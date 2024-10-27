# -*- coding: utf-8 -*-
import logging
import os
import random
import threading
from copy import copy
from datetime import datetime, timedelta
from random import randint
from time import sleep
from typing import Dict, List, Optional
from urllib.parse import parse_qs, unquote, urlparse

import numpy as np
import pytz
import requests
import ujson as json
from django.conf import settings
from django.db import transaction
from django.db.transaction import get_connection
from django.utils import timezone, translation
from django.utils.translation import activate
from django.utils.translation import gettext as _
from google.protobuf.json_format import MessageToJson
from numpy.random import PCG64, SeedSequence

from online.models import (
    TournamentGame,
    TournamentGamePlayer,
    TournamentNotification,
    TournamentPlayers,
    TournamentStatus,
)
from online.parser import TenhouParser
from tournament.models import MsOnlineTournamentRegistration, OnlineTournamentRegistration
from utils.general import format_text
from utils.new_pantheon import (
    add_online_replay_through_pantheon,
    add_penalty_game,
    add_user_to_new_pantheon,
    get_new_pantheon_swiss_sortition,
    send_team_names_to_pantheon,
    upload_replay_through_pantheon,
)
from utils.tenhou.helper import parse_names_from_tenhou_chat_message

logger = logging.getLogger("tournament_bot")


class TournamentHandler:
    # in minutes
    TOURNAMENT_BREAKS_TIME = [5, 5, 30, 5, 5, 5]

    TELEGRAM_DESTINATION = "tg"
    DISCORD_DESTINATION = "ds"

    tournament = None
    lobby = None
    game_type = None
    total_games = None
    destination = None

    def init(self, tournament, lobby, game_type, destination):
        self.tournament = tournament
        self.lobby = lobby
        self.game_type = game_type
        self.destination = destination

        TournamentStatus.objects.get_or_create(tournament=self.tournament)

    def get_status(self):
        return TournamentStatus.objects.get(tournament_id=self.tournament.id)

    def get_tournament_status(self):
        status = self.get_status()

        if not status.current_round:
            confirmed_players = TournamentPlayers.objects.filter(tournament=self.tournament).count()
            if status.registration_closed:
                return _("Games will start at 7-30 AM UTC. Confirmed players: %(confirmed_players)s.") % {
                    "confirmed_players": confirmed_players
                }
            else:
                return _("Confirmation phase is in progress. Confirmed players: %(confirmed_players)s.") % {
                    "confirmed_players": confirmed_players
                }

        # if status.current_round == self.tournament.number_of_sessions:
        #     return _("The tournament is over. Thank you for participating!")

        if status.end_break_time:
            now = timezone.now()

            if now > status.end_break_time:
                return _("Games will start soon.")

            minutes_dict = {
                1: "минуту",
                2: "минуты",
                3: "минуты",
                4: "минуты",
                21: "минуту",
                22: "минуты",
                23: "минуты",
                24: "минуты",
            }

            seconds_dict = {
                1: "секунду",
                2: "секунды",
                3: "секунды",
                4: "секунды",
                21: "секунду",
                22: "секунды",
                23: "секунды",
                24: "секунды",
                31: "секунду",
                32: "секунды",
                33: "секунды",
                34: "секунды",
                41: "секунду",
                42: "секунды",
                43: "секунды",
                44: "секунды",
                51: "секунду",
                52: "секунды",
                53: "секунды",
                54: "секунды",
            }

            delta = status.end_break_time - now
            language = translation.get_language()

            if delta.seconds > 60:
                minutes = round(delta.seconds // 60 % 60, 2)
                seconds = delta.seconds - minutes * 60
            else:
                minutes = None
                seconds = delta.seconds

            if language == "en":
                if minutes:
                    date = "{} minutes {} seconds".format(minutes, seconds)
                else:
                    date = "{} seconds".format(seconds)
            else:
                if minutes:
                    date = "{} {} и {} {}".format(
                        minutes, minutes_dict.get(minutes, "минут"), seconds, seconds_dict.get(seconds, "секунд")
                    )
                else:
                    date = "{} {}".format(delta.seconds, seconds_dict.get(delta.seconds, "секунд"))

            return _("Break. The next tour will start in %(date)s.") % {"date": date}

        finished_games_count = (
            TournamentGame.objects.filter(tournament=self.tournament)
            .filter(tournament_round=status.current_round)
            .filter(status=TournamentGame.FINISHED)
            .count()
        )

        failed_games_count = (
            TournamentGame.objects.filter(tournament=self.tournament)
            .filter(tournament_round=status.current_round)
            .filter(status=TournamentGame.FAILED_TO_START)
            .count()
        )

        total_games = (
            TournamentGame.objects.filter(tournament=self.tournament)
            .filter(tournament_round=status.current_round)
            .count()
        )

        message = _("Stage %(current_round)s of %(total_rounds)s.") % {
            "current_round": status.current_round,
            "total_rounds": self.tournament.number_of_sessions,
        }

        message += " "
        message += _("Finished games: %(finished)s/%(total)s.") % {
            "finished": finished_games_count,
            "total": total_games,
        }

        if failed_games_count:
            message += " "
            message += _("Several games could not start. The administrator will fix this soon.")

        return message

    def open_registration(self):
        status = self.get_status()
        status.registration_closed = False
        status.save()

        current_config = self.tournament.online_config.get_config()
        # todo: handle is_validated
        if current_config.is_validated:
            self.create_notification(
                TournamentNotification.CONFIRMATION_STARTED,
                tg_ru_kwargs={
                    "confirmation_end_time": current_config.ru_confirmation_end_time,
                    "timezone": current_config.ru_tournament_timezone,
                    "lobby_link": self.get_lobby_link(current_config.public_lobby),
                    "rating_link": self.get_rating_link(),
                },
                discord_ru_kwargs={
                    "confirmation_channel": current_config.ru_discord_confirmation_channel,
                    "confirmation_end_time": current_config.ru_confirmation_end_time,
                    "timezone": current_config.ru_tournament_timezone,
                    "lobby_link": self.get_lobby_link(current_config.public_lobby),
                    "rating_link": self.get_rating_link(),
                },
                discord_en_kwargs={
                    "confirmation_channel": current_config.en_discord_confirmation_channel,
                    "confirmation_end_time": current_config.en_confirmation_end_time,
                    "timezone": current_config.en_tournament_timezone,
                    "lobby_link": self.get_lobby_link(current_config.public_lobby),
                    "rating_link": self.get_rating_link(),
                },
            )

    def close_registration(self):
        status = self.get_status()
        status.registration_closed = True
        status.save()

        confirmed_players = TournamentPlayers.objects.filter(tournament=self.tournament).count()
        current_config = self.tournament.online_config.get_config()
        self.create_notification(
            TournamentNotification.CONFIRMATION_ENDED,
            tg_ru_kwargs={
                "lobby_link": self.get_lobby_link(current_config.public_lobby),
                "confirmed_players": confirmed_players,
            },
            discord_ru_kwargs={
                "lobby_link": self.get_lobby_link(current_config.public_lobby),
                "confirmed_players": confirmed_players,
            },
            discord_en_kwargs={
                "lobby_link": self.get_lobby_link(current_config.public_lobby),
                "confirmed_players": confirmed_players,
            },
        )

    def send_team_names_to_pantheon(self):
        try:
            registrations = TournamentPlayers.objects.filter(tournament=self.tournament, is_disable=False)
            self._send_team_names_to_pantheon(registrations=registrations)
        except Exception as e:
            logger.error(e, exc_info=e)
            return _("Fatal error. Ask for administrator.")

    def send_player_team_names_to_pantheon(self, player):
        try:
            self._send_team_names_to_pantheon(registrations=[player])
        except Exception as e:
            logger.error(e, exc_info=e)
            return _("Fatal error. Ask for administrator.")

    def _send_team_names_to_pantheon(self, registrations):
        try:
            team_names = []
            for registration in registrations:
                team_names.append({"player_id": registration.pantheon_id, "team_name": registration.team_name})

            pantheon_response = send_team_names_to_pantheon(
                self.tournament.new_pantheon_id, settings.PANTHEON_ADMIN_ID, team_names
            )

            if not pantheon_response.success:
                return _("Error adding teams names to pantheon.")
        except Exception as e:
            logger.error(e, exc_info=e)
            return _("Fatal error. Ask for administrator.")

        return _("Teams names successfully added to pantheon.")

    def add_game_log(self, log_link):
        status = self.get_status()
        error_message = _("This is not looks like a link to the game log.")

        log_link = log_link.replace("https://", "http://")

        log_link = log_link.strip()
        if not log_link.startswith("http://tenhou.net/"):
            return error_message, False

        attributes = parse_qs(urlparse(log_link).query)

        if "log" not in attributes:
            return error_message, False

        log_id = attributes["log"][0]

        if TournamentGame.objects.filter(log_id=log_id).exists():
            return _("The game has been added. Thank you."), True

        try:
            parser = TenhouParser()
            players = parser.get_player_names(log_id)
        except Exception:
            return (
                _("Fail to add this game. Try again in a moment or you havn't copied the entire link of the game log."),
                False,
            )

        with transaction.atomic():
            # todo: extract admin name from online config
            error_message = _("Fail to add game log. Contact the administrator %(admin_username)s.") % {
                "admin_username": self.get_admin_username()
            }

            cursor = get_connection().cursor()
            cursor.execute(f"LOCK TABLE {TournamentGame._meta.db_table}")

            try:
                games = (
                    TournamentGame.objects.filter(tournament=self.tournament)
                    .filter(game_players__player__tenhou_username__in=players)
                    .filter(tournament_round=status.current_round)
                    .distinct()
                )

                if games.count() >= 2:
                    logger.error("Log add. Too much games.")
                    return error_message, False

                game = games.first()
                game.log_id = log_id
                game.save()

                self.process_add_game_log(status=status, log_link=log_link, log_id=log_id, game=game)
                self.check_round_was_finished()
            except Exception as err:
                logger.error(err)
                return error_message, False
            finally:
                cursor.close()

        return _("The game has been added. Thank you."), True

    def process_add_game_log(self, status, log_link, log_id, game):
        response = add_online_replay_through_pantheon(self.tournament.new_pantheon_id, log_link)

        if not response.game or not response.game.session_hash:
            raise Exception(f"Log {log_link} not successfully added to pantheon")

        game_info = response.game
        pantheon_url = (
            f"https://rating.riichimahjong.org/event/{self.tournament.new_pantheon_id}"
            f"/game/{game_info.session_hash}"
        )

        pantheon_players = {}
        for pantheon_player in response.players:
            pantheon_player_id = pantheon_player.id
            pantheon_players[pantheon_player_id] = {
                "id": pantheon_player_id,
                "tenhou_nickname": pantheon_player.tenhou_id,
                "pantheon_name": pantheon_player.title,
                "score": 0,
                "place": 0,
                "rating_delta": 0,
            }

        for pantheon_player_result in game_info.final_results:
            pantheon_player_id = pantheon_player_result.player_id
            pantheon_players[pantheon_player_id]["score"] = pantheon_player_result.score
            pantheon_players[pantheon_player_id]["place"] = pantheon_player_result.place
            pantheon_players[pantheon_player_id]["rating_delta"] = pantheon_player_result.rating_delta

        formatted_players = []
        players_info = sorted(pantheon_players.values(), key=lambda x: x["place"])
        # align strings and format scores
        max_nick_length = max([len(x["tenhou_nickname"]) for x in players_info])
        max_scores_length = max([len(str(x["score"])) for x in players_info])
        for player_info in players_info:
            try:
                current_tournament_player = TournamentPlayers.objects.get(
                    tournament=self.tournament, pantheon_id=player_info["id"]
                )
                try:
                    current_registrant = OnlineTournamentRegistration.objects.get(
                        tournament=self.tournament, tenhou_nickname=current_tournament_player.tenhou_username
                    )
                    display_name = f"{current_registrant.first_name} ({current_registrant.last_name})"
                except OnlineTournamentRegistration.DoesNotExist:
                    display_name = player_info["pantheon_name"]
            except TournamentPlayers.DoesNotExist:
                display_name = player_info["pantheon_name"]

            tenhou_nickname = player_info["tenhou_nickname"].ljust(max_nick_length, " ")

            scores = str(player_info["score"]).rjust(max_scores_length, " ")
            rating_delta = player_info["rating_delta"]
            if rating_delta > 0:
                rating_delta = f"+{rating_delta}"

            formatted_players.append(
                f"{player_info['place']}. {display_name}\n{tenhou_nickname} {scores} ({rating_delta})"
            )

        game.status = TournamentGame.FINISHED
        game.save()

        finished_games = (
            TournamentGame.objects.filter(tournament=self.tournament)
            .filter(status=TournamentGame.FINISHED)
            .filter(tournament_round=status.current_round)
        )

        total_games = (
            TournamentGame.objects.filter(tournament=self.tournament)
            .filter(tournament_round=status.current_round)
            .count()
        )

        self.create_notification(
            TournamentNotification.GAME_ENDED,
            tg_ru_kwargs={
                "finished": finished_games.count(),
                "total": total_games,
                "pantheon_link": pantheon_url,
                "game_replay_link": f"http://tenhou.net/0/?log={log_id}",
                "player_one": formatted_players[0],
                "player_two": formatted_players[1],
                "player_three": formatted_players[2],
                "player_four": formatted_players[3],
                "platform_name": "Tenhou",
            },
            discord_ru_kwargs={
                "finished": finished_games.count(),
                "total": total_games,
                "pantheon_link": pantheon_url,
                "game_replay_link": f"http://tenhou.net/0/?log={log_id}",
                "player_one": formatted_players[0],
                "player_two": formatted_players[1],
                "player_three": formatted_players[2],
                "player_four": formatted_players[3],
                "platform_name": "Tenhou",
            },
            discord_en_kwargs={
                "finished": finished_games.count(),
                "total": total_games,
                "pantheon_link": pantheon_url,
                "game_replay_link": f"http://tenhou.net/0/?log={log_id}",
                "player_one": formatted_players[0],
                "player_two": formatted_players[1],
                "player_three": formatted_players[2],
                "player_four": formatted_players[3],
                "platform_name": "Tenhou",
            },
        )

    def game_finish(self, log_id, players, log_content, log_time):
        if not self.tournament.is_majsoul_tournament:
            platform_id = 1
        else:
            platform_id = 2

        status = self.get_status()

        if TournamentGame.objects.filter(log_id=log_id).exists():
            return _("The game has been added. Thank you."), True

        # todo add flag for disable upload to pantheon
        try:
            pantheon_response = upload_replay_through_pantheon(
                self.tournament.new_pantheon_id, platform_id, 2, log_id, log_time, log_content
            )
            if not pantheon_response.game or not pantheon_response.game.session_hash:
                return _("Error adding a game to pantheon."), True
        except Exception:
            return _("Error adding a game to pantheon."), True

        pantheon_response_dict = json.loads(MessageToJson(pantheon_response))

        formatted_players_results = {}
        for player_result in pantheon_response_dict["game"]["finalResults"]:
            formatted_players_results[int(player_result["playerId"])] = player_result

        formatted_players = {}
        for current_player in pantheon_response_dict["players"]:
            matched_player = formatted_players_results[int(current_player["id"])]
            formatted_players[matched_player["place"]] = f"{current_player['tenhouId']} [{matched_player['score']}]"

        with transaction.atomic():
            error_message = _("Fail to add game log. Contact the administrator %(admin_username)s.") % {
                "admin_username": self.get_admin_username()
            }

            cursor = get_connection().cursor()
            cursor.execute(f"LOCK TABLE {TournamentGame._meta.db_table}")

            try:
                if not self.tournament.is_majsoul_tournament:
                    games = (
                        TournamentGame.objects.filter(tournament=self.tournament)
                        .filter(game_players__player__tenhou_username__in=players)
                        .filter(tournament_round=status.current_round)
                        .distinct()
                    )
                else:
                    games = (
                        TournamentGame.objects.filter(tournament=self.tournament)
                        .filter(game_players__player__ms_username__in=players)
                        .filter(tournament_round=status.current_round)
                        .distinct()
                    )

                if games.count() >= 2:
                    logger.error("Log add. Too much games.")
                    return error_message, False

                game = games.first()

                if not game:
                    logger.error("Games not found for this players!")
                    return error_message, False

                game.log_id = log_id
                game.save()

                self.process_game_finish(
                    status=status,
                    game=game,
                    players=players,
                    log_id=log_id,
                    pantheon_response_dict=pantheon_response_dict,
                    formatted_players=formatted_players,
                )
                self.check_round_was_finished()
            except Exception as err:
                logger.error(err)
                return error_message, False
            finally:
                cursor.close()

        return _("The game has been added. Thank you."), True

    def process_game_finish(self, status, game, players, log_id, pantheon_response_dict, formatted_players):
        game.status = TournamentGame.FINISHED
        game.save()

        finished_games = (
            TournamentGame.objects.filter(tournament=self.tournament)
            .filter(status=TournamentGame.FINISHED)
            .filter(tournament_round=status.current_round)
        )

        total_games = (
            TournamentGame.objects.filter(tournament=self.tournament)
            .filter(tournament_round=status.current_round)
            .count()
        )

        if not self.tournament.is_majsoul_tournament:
            self.create_notification(
                TournamentNotification.GAME_ENDED,
                tg_ru_kwargs={
                    "finished": finished_games.count(),
                    "total": total_games,
                    "pantheon_link": "pantheon_link",
                    "game_replay_link": f"http://tenhou.net/0/?log={log_id}",
                    "player_one": players[0],
                    "player_two": players[1],
                    "player_three": players[2],
                    "player_four": players[3],
                    "platform_name": "Tenhou",
                },
                discord_ru_kwargs={
                    "finished": finished_games.count(),
                    "total": total_games,
                    "pantheon_link": "pantheon_link",
                    "game_replay_link": f"http://tenhou.net/0/?log={log_id}",
                    "player_one": players[0],
                    "player_two": players[1],
                    "player_three": players[2],
                    "player_four": players[3],
                    "platform_name": "Tenhou",
                },
                discord_en_kwargs={
                    "finished": finished_games.count(),
                    "total": total_games,
                    "pantheon_link": "pantheon_link",
                    "game_replay_link": f"http://tenhou.net/0/?log={log_id}",
                    "player_one": players[0],
                    "player_two": players[1],
                    "player_three": players[2],
                    "player_four": players[3],
                    "platform_name": "Tenhou",
                },
            )
        else:
            self.create_notification(
                TournamentNotification.GAME_ENDED,
                tg_ru_kwargs={
                    "finished": finished_games.count(),
                    "total": total_games,
                    "pantheon_link": self.get_pantheon_game_link(pantheon_response_dict["game"]["sessionHash"]),
                    "game_replay_link": f"https://mahjongsoul.game.yo-star.com/?paipu={log_id}",
                    "player_one": formatted_players[1],
                    "player_two": formatted_players[2],
                    "player_three": formatted_players[3],
                    "player_four": formatted_players[4],
                    "platform_name": "mahjongsoul",
                },
                discord_ru_kwargs={
                    "finished": finished_games.count(),
                    "total": total_games,
                    "pantheon_link": self.get_pantheon_game_link(pantheon_response_dict["game"]["sessionHash"]),
                    "game_replay_link": f"https://mahjongsoul.game.yo-star.com/?paipu={log_id}",
                    "player_one": formatted_players[1],
                    "player_two": formatted_players[2],
                    "player_three": formatted_players[3],
                    "player_four": formatted_players[4],
                    "platform_name": "mahjongsoul",
                },
                discord_en_kwargs={
                    "finished": finished_games.count(),
                    "total": total_games,
                    "pantheon_link": self.get_pantheon_game_link(pantheon_response_dict["game"]["sessionHash"]),
                    "game_replay_link": f"https://mahjongsoul.game.yo-star.com/?paipu={log_id}",
                    "player_one": formatted_players[1],
                    "player_two": formatted_players[2],
                    "player_three": formatted_players[3],
                    "player_four": formatted_players[4],
                    "platform_name": "mahjongsoul",
                },
            )

    def confirm_participation_in_tournament(
        self, nickname, telegram_username=None, discord_username=None, friend_id=None, is_admin=False
    ):
        status = self.get_status()

        if not is_admin and status.registration_closed:
            return _("The confirmation phase has already ended. Visit our next tournaments.")

        if not self.tournament.is_majsoul_tournament and len(nickname) > 8:
            return _("The tenhou.net nickname must not be longer than eight characters.")

        if not self.tournament.is_majsoul_tournament:
            try:
                registration = OnlineTournamentRegistration.objects.get(
                    tenhou_nickname__iexact=nickname, tournament=self.tournament
                )
            except OnlineTournamentRegistration.DoesNotExist:
                return _("You need to register for the tournament on mahjong.click first.")
        else:
            if not friend_id:
                registration = MsOnlineTournamentRegistration.objects.filter(
                    ms_nickname__iexact=nickname, tournament=self.tournament
                )
            else:
                registration = MsOnlineTournamentRegistration.objects.filter(
                    ms_nickname__iexact=nickname, tournament=self.tournament, ms_friend_id=friend_id
                )

            if len(registration) <= 0:
                return _("You need to register for the tournament on mahjong.click first.")
            if len(registration) > 1:
                return _("Found multiple majsoul accounts for the tournament on mahjong.click. Ask for administrator.")
            registration = registration[0]

        if self.tournament.is_majsoul_tournament and not registration.is_validated:
            return _("Majsoul account not validated. Ask for administrator.")

        if not registration.is_approved:
            return _("You are not approved for this tournament by administrator.")

        if not self.tournament.is_majsoul_tournament:
            if TournamentPlayers.objects.filter(tenhou_username__iexact=nickname, tournament=self.tournament).exists():
                return _('Nickname "%(nickname)s" was already confirmed for this tournament.') % {"nickname": nickname}
        else:
            if TournamentPlayers.objects.filter(
                ms_username__iexact=nickname, tournament=self.tournament, pantheon_id=registration.user.new_pantheon_id
            ).exists():
                return _('Nickname "%(nickname)s" was already confirmed for this tournament.') % {"nickname": nickname}

        pantheon_id = registration.user and registration.user.new_pantheon_id or None
        # todo: deprecate non pantheon_registration for online tournament
        if not pantheon_id:
            pantheon_id = registration.player and registration.player.pantheon_id or None
        team_name = registration.notes

        tenhou_nickname = ""
        ms_nickname = None
        ms_account_id = None
        if not self.tournament.is_majsoul_tournament:
            tenhou_nickname = nickname
        else:
            ms_nickname = nickname
            ms_account_id = registration.ms_account_id

        with transaction.atomic():
            record = TournamentPlayers.objects.create(
                telegram_username=telegram_username,
                discord_username=discord_username,
                tenhou_username=tenhou_nickname,
                tournament=self.tournament,
                pantheon_id=pantheon_id,
                team_name=team_name,
                ms_username=ms_nickname,
                ms_account_id=ms_account_id,
            )

            try:
                # todo: deprecate non pantheon_registration for online tournament
                if self.tournament.is_online():
                    add_user_to_new_pantheon(
                        record,
                        registration,
                        self.tournament.new_pantheon_id,
                        settings.PANTHEON_ADMIN_ID,
                        self.tournament.is_majsoul_tournament,
                    )
                    if self.tournament.is_command:
                        self.send_player_team_names_to_pantheon(record)
            except Exception as e:
                logger.error(e, exc_info=e)
                transaction.set_rollback(True)
                return _("Fatal error. Ask for administrator.")

        return _("Your participation in the tournament has been confirmed!")

    def add_penalty_game(self, game_id):
        try:
            game = TournamentGame.objects.get(id=game_id, tournament_id=self.tournament.id)
            if not game:
                return _("Game does not exist.")

            player_ids = [x.player.pantheon_id for x in game.game_players.all()]
            pantheon_response = add_penalty_game(
                self.tournament.new_pantheon_id, settings.PANTHEON_ADMIN_ID, player_ids
            )
            if not pantheon_response.hash:
                return _("Error adding penalty to pantheon.")

            player_names = self.get_players_message_string([x.player for x in game.game_players.all()])
            self.create_notification(
                TournamentNotification.GAME_PENALTY,
                tg_ru_kwargs={"player_names": player_names},
                discord_ru_kwargs={"player_names": player_names},
                discord_en_kwargs={"player_names": player_names},
            )
            self.check_round_was_finished()
        except Exception as e:
            logger.error(e, exc_info=e)
            return _("Fatal error. Ask for administrator.")
        return _("Game penalty added successfully.")

    def prepare_next_round(self, reshuffleInPortal=True):
        status = self.get_status()

        if not status.current_round:
            status.current_round = 0

        if status.current_round >= self.tournament.number_of_sessions:
            message = "Невозможно запустить новые игры. У турнира закончились туры."
            return {"message": message, "tables": [], "round": -1}

        current_games = TournamentGame.objects.filter(tournament=self.tournament).exclude(
            status=TournamentGame.FINISHED
        )

        if current_games.exists():
            message = "Невозможно запустить новые игры. Старые игры ещё не завершились."
            return {"message": message, "tables": [], "round": -1}

        confirmed_players = TournamentPlayers.objects.filter(tournament=self.tournament, is_disable=False)

        if len(confirmed_players) == 0:
            logger.error("Not found confirmed player for tournament {}".format(self.tournament.id))

        missed_id = confirmed_players.filter(pantheon_id=None)
        if missed_id.exists():
            message = "Невозможно запустить новые игры. Не у всех игроков стоит pantheon id."
            return {"message": message, "tables": [], "round": -1}

        is_majsoul_tournament = self.tournament.is_majsoul_tournament

        with transaction.atomic():
            status.current_round += 1
            status.end_break_time = None

            pantheon_ids = {}
            for confirmed_player in confirmed_players:
                pantheon_ids[int(confirmed_player.pantheon_id)] = confirmed_player

            sortition = self.make_sortition(pantheon_ids, status.current_round)
            # from online.team_seating import TeamSeating
            # sortition = TeamSeating.get_seating_for_round(status.current_round)

            games = []
            final_sortition = []
            for game_index, item in enumerate(sortition):
                logger.info(f"Preparing table with player_ids={item}")

                # shuffle player winds
                if reshuffleInPortal:
                    random.shuffle(item)

                try:
                    game = TournamentGame.objects.create(
                        status=TournamentGame.NEW,
                        tournament=self.tournament,
                        tournament_round=status.current_round,
                        game_index=game_index + 1,
                    )

                    table_players = []
                    for wind in range(0, len(item)):
                        player_id = pantheon_ids[item[wind]].id
                        TournamentGamePlayer.objects.create(game=game, player_id=player_id, wind=wind)
                        if not is_majsoul_tournament:
                            table_players.append({"tenhou_id": pantheon_ids[item[wind]].tenhou_username})
                        else:
                            table_players.append({"ms_account_id": pantheon_ids[item[wind]].ms_account_id})
                    final_sortition.append({"players": table_players})

                    games.append(game)
                except Exception as e:
                    logger.error("Failed to prepare a game. Pantheon ids={}".format(item), exc_info=e)

            # we was able to generate games
            if games:
                status.save()

                # for users
                self.create_notification(
                    TournamentNotification.GAMES_PREPARED,
                    tg_ru_kwargs={
                        "current_round": status.current_round,
                        "total_rounds": self.tournament.number_of_sessions,
                    },
                    discord_ru_kwargs={
                        "current_round": status.current_round,
                        "total_rounds": self.tournament.number_of_sessions,
                    },
                    discord_en_kwargs={
                        "current_round": status.current_round,
                        "total_rounds": self.tournament.number_of_sessions,
                    },
                )

                # for admin
                message = "Тур {}. Игры сформированы.".format(status.current_round)
                return {"message": message, "tables": final_sortition, "round": status.current_round}
            else:
                message = "Игры не запустились. Требуется вмешательство администратора."
                return {"message": message, "tables": [], "round": -1}

    # return [[1,2,3,4],[5,6,7,8]...]
    def make_sortition(self, pantheon_ids, current_round):
        if current_round == 1:
            pantheon_ids_list = list(pantheon_ids.keys())
            if len(pantheon_ids_list) % 4 == 0:
                return self._numpy_random_sortition(pantheon_ids_list)
            else:
                return []
        else:
            make_failback_sortition = False
            pantheon_sortition = get_new_pantheon_swiss_sortition(
                self.tournament.new_pantheon_id, settings.PANTHEON_ADMIN_ID
            )
            pantheon_sortition = json.loads(MessageToJson(pantheon_sortition))
            tables = pantheon_sortition["tables"]
            pantheon_sortition = []
            if tables:
                pantheon_players_count = 0
                for table in tables:
                    players = []
                    for player in table["players"]:
                        player_id = int(player["playerId"])
                        pantheon_players_count = pantheon_players_count + 1
                        if player_id not in pantheon_ids:
                            make_failback_sortition = True
                            break
                        players.append(player_id)
                    if not make_failback_sortition:
                        pantheon_sortition.append(players)
                if not make_failback_sortition and pantheon_players_count < len(pantheon_ids):
                    make_failback_sortition = True
                if pantheon_players_count % 4 != 0:
                    make_failback_sortition = True
            else:
                make_failback_sortition = True

            if not make_failback_sortition:
                return pantheon_sortition
            else:
                marked_pantheon_ids = {}
                pantheon_ids_list = list(pantheon_ids.keys())
                if len(pantheon_ids_list) % 4 != 0:
                    return []
                pantheon_ids_list.sort()
                player_index = 1
                for id in pantheon_ids_list:
                    marked_pantheon_ids[player_index] = id
                    player_index = player_index + 1
                golf_sortition = self.resolve_golf_sortition(
                    self.tournament.number_of_sessions, len(pantheon_ids), current_round, marked_pantheon_ids
                )
                if not golf_sortition:
                    return self._numpy_random_sortition(pantheon_ids_list)

    # marked_pantheon_ids[index] = pantheon_id
    def resolve_golf_sortition(self, tours_count, players_count, current_tour, marked_pantheon_ids):
        golf_sortition = []
        folder = settings.GOLF_SORTITION_DIR
        golf_sortition_file = os.path.join(
            settings.BASE_DIR, folder, f"{tours_count}_tours_{players_count}_players.json"
        )
        # check exist file
        if os.path.isfile(golf_sortition_file):
            with open(golf_sortition_file) as f:
                data = json.loads(f.read())
            for tours in data:
                if tours["tour_number"] == current_tour:
                    tables = tours["tables"]
                    for table in tables:
                        current_table = []
                        seating = table["seating"]
                        for seat in seating:
                            player_index = int(seat["player_index"])
                            if player_index in marked_pantheon_ids:
                                current_table.append(marked_pantheon_ids[player_index])
                        golf_sortition.append(current_table)

        return golf_sortition

    def start_games(self):
        status = self.get_status()

        games = TournamentGame.objects.filter(tournament=self.tournament).filter(tournament_round=status.current_round)

        for game in games:
            self.start_game(game)

    def start_game(self, game):
        """
        Send request to tenhou.net to start a new game in the tournament lobby
        """

        players = game.game_players.all().order_by("wind")

        player_names = [x.player.tenhou_username for x in players]
        escaped_player_names = [f"`{x.player.tenhou_username}`" for x in players]

        url = "https://tenhou.net/cs/edit/cmd_start.cgi"
        data = {
            "L": self.lobby,
            "R2": self.game_type,
            "RND": "default",
            "WG": 1,
            "M": "\r\n".join([x for x in player_names]),
        }

        headers = {
            "Origin": "http://tenhou.net",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "http://tenhou.net/cs/edit/?{}".format(self.lobby),
        }

        try:
            response = requests.post(url, data=data, headers=headers, allow_redirects=False)
            result = unquote(response.content.decode("utf-8"))

            if result.startswith("FAILED"):
                logger.error(result)
                game.status = TournamentGame.FAILED_TO_START
                self.create_notification(
                    TournamentNotification.GAME_FAILED,
                    tg_ru_kwargs={"players": ", ".join(escaped_player_names), "game_index": game.game_index},
                )
            elif result.startswith("MEMBER NOT FOUND"):
                missed_player_ids = [x for x in result.split("\r\n")[1:] if x]
                missed_player_objects = TournamentPlayers.objects.filter(tenhou_username__in=missed_player_ids).filter(
                    tournament=self.tournament
                )

                missed_players_str = self.get_players_message_string(missed_player_objects)
                game.status = TournamentGame.FAILED_TO_START
                self.create_notification(
                    TournamentNotification.GAME_FAILED_NO_MEMBERS,
                    tg_ru_kwargs={
                        "players": ", ".join(escaped_player_names),
                        "missed_players": missed_players_str,
                        "lobby_link": self.get_lobby_link(),
                        "game_index": game.game_index,
                        "missed_players_str": "",
                    },
                )
            else:
                game.status = TournamentGame.STARTED
                self.create_notification(
                    TournamentNotification.GAME_STARTED,
                    tg_ru_kwargs={"players": ", ".join(escaped_player_names), "game_index": game.game_index},
                )
        except Exception as e:
            logger.error(e, exc_info=e)

            game.status = TournamentGame.FAILED_TO_START
            self.create_notification(
                TournamentNotification.GAME_FAILED, tg_ru_kwargs={"players": ", ".join(escaped_player_names)}
            )

        game.save()

    def create_start_game_notification(self, tour, table_number, notification_type, missed_players=None):
        if missed_players is None:
            missed_players = []
        status = self.get_status()
        if tour == status.current_round:
            if notification_type == 1:
                games = (
                    TournamentGame.objects.filter(tournament=self.tournament)
                    .filter(tournament_round=status.current_round)
                    .filter(game_index=table_number)
                )
                for game in games:
                    self._create_start_game_notification(game)
            if notification_type == 2:
                games = (
                    TournamentGame.objects.filter(tournament=self.tournament)
                    .filter(tournament_round=status.current_round)
                    .filter(game_index=table_number)
                )
                for game in games:
                    game.status = TournamentGame.FAILED_TO_START
                    players = game.game_players.all().order_by("wind")
                    if not self.tournament.is_majsoul_tournament:
                        escaped_player_names = [f"`{x.player.tenhou_username}`" for x in players]
                    else:
                        escaped_player_names = [f"`{x.player.ms_username}`" for x in players]
                    self.create_notification(
                        TournamentNotification.GAME_FAILED,
                        tg_ru_kwargs={"players": ", ".join(escaped_player_names), "game_index": game.game_index},
                        discord_ru_kwargs={"players": ", ".join(escaped_player_names), "game_index": game.game_index},
                        discord_en_kwargs={"players": ", ".join(escaped_player_names), "game_index": game.game_index},
                    )
                    game.save()
            if notification_type == 3:
                games = (
                    TournamentGame.objects.filter(tournament=self.tournament)
                    .filter(tournament_round=status.current_round)
                    .filter(game_index=table_number)
                )
                for game in games:
                    game.status = TournamentGame.FAILED_TO_START
                    players = game.game_players.all().order_by("wind")
                    if not self.tournament.is_majsoul_tournament:
                        escaped_player_names = [f"`{x.player.tenhou_username}`" for x in players]
                    else:
                        escaped_player_names = [f"`{x.player.ms_username}`" for x in players]

                    if not self.tournament.is_majsoul_tournament:
                        missed_round_players = (
                            TournamentPlayers.objects.filter(tournament=self.tournament)
                            .filter(tenhou_username__in=missed_players)
                            .all()
                        )
                    else:
                        missed_round_players = (
                            TournamentPlayers.objects.filter(tournament=self.tournament)
                            .filter(ms_account_id__in=missed_players)
                            .all()
                        )

                    current_missed_players = []
                    current_missed_tg_usernames = []
                    current_missed_discord_usernames = []
                    for round_player in missed_round_players:
                        if not self.tournament.is_majsoul_tournament:
                            current_missed_players.append(round_player.tenhou_username)
                        else:
                            current_missed_players.append(round_player.ms_username)
                        current_missed_tg_usernames.append(round_player.telegram_username)
                        current_missed_discord_usernames.append(round_player.discord_username)

                    tg_formatted_missed_players = ", ".join(["@{}".format(x) for x in current_missed_tg_usernames])
                    discord_formatted_missed_players = ", ".join(
                        ["{}".format(x) for x in current_missed_discord_usernames]
                    )
                    current_config = self.tournament.online_config.get_config()

                    self.create_notification(
                        TournamentNotification.GAME_FAILED_NO_MEMBERS,
                        tg_ru_kwargs={
                            "players": ", ".join(escaped_player_names),
                            "game_index": game.game_index,
                            "missed_players": current_missed_players,
                            "lobby_link": self.get_lobby_link(current_config.public_lobby),
                            "missed_players_str": tg_formatted_missed_players,
                        },
                        discord_ru_kwargs={
                            "players": ", ".join(escaped_player_names),
                            "game_index": game.game_index,
                            "missed_players": current_missed_players,
                            "lobby_link": self.get_lobby_link(current_config.public_lobby),
                            "missed_players_str": discord_formatted_missed_players,
                        },
                        discord_en_kwargs={
                            "players": ", ".join(escaped_player_names),
                            "game_index": game.game_index,
                            "missed_players": current_missed_players,
                            "lobby_link": self.get_lobby_link(current_config.public_lobby),
                            "missed_players_str": discord_formatted_missed_players,
                        },
                    )
                    game.save()

    def _create_start_game_notification(self, game):
        try:
            players = game.game_players.all().order_by("wind")

            if not self.tournament.is_majsoul_tournament:
                escaped_player_names = [f"`{x.player.tenhou_username}`" for x in players]
            else:
                escaped_player_names = [f"`{x.player.ms_username}`" for x in players]

            game.status = TournamentGame.STARTED
            self.create_notification(
                TournamentNotification.GAME_STARTED,
                tg_ru_kwargs={"players": ", ".join(escaped_player_names), "game_index": game.game_index},
                discord_ru_kwargs={"players": ", ".join(escaped_player_names), "game_index": game.game_index},
                discord_en_kwargs={"players": ", ".join(escaped_player_names), "game_index": game.game_index},
            )
            game.save()
        except Exception:
            game.status = TournamentGame.FAILED_TO_START
            self.create_notification(
                TournamentNotification.GAME_FAILED,
                tg_ru_kwargs={"players": ", ".join(escaped_player_names), "game_index": game.game_index},
                discord_ru_kwargs={"players": ", ".join(escaped_player_names), "game_index": game.game_index},
                discord_en_kwargs={"players": ", ".join(escaped_player_names), "game_index": game.game_index},
            )
            game.save()

    def check_round_was_finished(self):
        status = self.get_status()

        finished_games = (
            TournamentGame.objects.filter(tournament=self.tournament)
            .filter(status=TournamentGame.FINISHED)
            .filter(tournament_round=status.current_round)
        )
        games = TournamentGame.objects.filter(tournament=self.tournament).filter(tournament_round=status.current_round)

        if finished_games.count() == games.count() and not status.end_break_time:
            if status.current_round == self.tournament.number_of_sessions:
                self.create_notification(TournamentNotification.TOURNAMENT_FINISHED)
            else:
                index = status.current_round - 1
                break_minutes = self.TOURNAMENT_BREAKS_TIME[index]
                status.end_break_time = timezone.now() + timedelta(minutes=break_minutes)
                status.save()

                current_config = self.tournament.online_config.get_config()

                self.create_notification(
                    TournamentNotification.ROUND_FINISHED,
                    tg_ru_kwargs={
                        "break_minutes": break_minutes,
                        "lobby_link": self.get_lobby_link(current_config.public_lobby),
                        "current_round": status.current_round + 1,
                        "total_rounds": self.tournament.number_of_sessions,
                    },
                    discord_ru_kwargs={
                        "break_minutes": break_minutes,
                        "lobby_link": self.get_lobby_link(current_config.public_lobby),
                        "current_round": status.current_round + 1,
                        "total_rounds": self.tournament.number_of_sessions,
                    },
                    discord_en_kwargs={
                        "break_minutes": break_minutes,
                        "lobby_link": self.get_lobby_link(current_config.public_lobby),
                        "current_round": status.current_round + 1,
                        "total_rounds": self.tournament.number_of_sessions,
                    },
                )
        else:
            return None

    def new_tg_chat_member(self, username: str):
        status = self.get_status()

        if not status.current_round:
            message = "Добро пожаловать в чат онлайн турнира! \n"
            if not username:
                message += (
                    "Для начала установите username в настройках телеграма (Settings -> Username). "
                    "Инструкция: http://telegramzy.ru/nik-v-telegramm/ \n"
                )
                message += 'После этого отправьте команду "`/me ваш ник на тенхе`" для подтверждения участия.'
            else:
                message += 'Для подтверждения участия отправьте команду "`/me ваш ник на тенхе`" (регистр важен!)'
            return message
        else:
            message = "Добро пожаловать в чат онлайн турнира! \n\n"
            message += "Статистику турнира можно посмотреть вот тут: {} \n".format(self.get_rating_link())
            return message

    def create_notification(
        self,
        notification_type: int,
        tg_ru_kwargs: Optional[Dict] = None,
        discord_ru_kwargs: Optional[Dict] = None,
        discord_en_kwargs: Optional[Dict] = None,
    ):
        if not tg_ru_kwargs:
            tg_ru_kwargs = {}
        if not discord_ru_kwargs:
            discord_ru_kwargs = {}
        if not discord_en_kwargs:
            discord_en_kwargs = {}

        with transaction.atomic():
            TournamentNotification.objects.create(
                tournament=self.tournament,
                notification_type=notification_type,
                message_kwargs=discord_ru_kwargs,
                destination=TournamentNotification.DISCORD,
                lang=TournamentNotification.RU,
            )

            TournamentNotification.objects.create(
                tournament=self.tournament,
                notification_type=notification_type,
                message_kwargs=discord_en_kwargs,
                destination=TournamentNotification.DISCORD,
                lang=TournamentNotification.EN,
            )

            TournamentNotification.objects.create(
                tournament=self.tournament,
                notification_type=notification_type,
                message_kwargs=tg_ru_kwargs,
                destination=TournamentNotification.TELEGRAM,
                lang=TournamentNotification.RU,
            )

    def get_allowed_players(self):
        confirmed_players = TournamentPlayers.objects.filter(tournament=self.tournament)
        allowed_players = []
        for player in confirmed_players:
            allowed_players.append(
                {
                    "pantheon_id": player.pantheon_id,
                    "tenhou_id": player.tenhou_username,
                    "is_replacement": player.is_replacement,
                    "ms_username": player.ms_username,
                    "ms_account_id": player.ms_account_id,
                    "telegram_username": player.telegram_username,
                }
            )
        return allowed_players

    def get_notification_text(
        self, lang: str, notification: TournamentNotification, destination: str, extra_kwargs: Optional[dict] = None
    ):
        activate(lang)

        status = self.get_status()

        kwargs = copy(notification.message_kwargs)
        if extra_kwargs:
            kwargs.update(extra_kwargs)

        if destination == self.DISCORD_DESTINATION:
            # this will disable links preview for discord messages
            for key, value in kwargs.items():
                if type(value) == str and value.startswith("http"):
                    kwargs[key] = f"<{value}>"

        if notification.notification_type == TournamentNotification.CONFIRMATION_STARTED:
            if destination == self.TELEGRAM_DESTINATION:
                if not self.tournament.is_majsoul_tournament:
                    return (
                        _(
                            "Confirmation stage has begun! "
                            'To confirm your tournament participation send command "/me your tenhou nickname" '
                            "(registry important!). "
                            "Confirmation stage will be ended at %(confirmation_end_time)s (%(timezone)s).\n\n"
                            "Useful links:\n"
                            "- tournament lobby: %(lobby_link)s\n"
                            "- tournament rating table: %(rating_link)s\n"
                        )
                        % kwargs
                    )
                else:
                    return (
                        _(
                            "Confirmation stage has begun! "
                            'To confirm your tournament participation send command "/me your mahjongsoul nickname" '
                            "(registry important!). "
                            "Confirmation stage will be ended at %(confirmation_end_time)s (%(timezone)s).\n\n"
                            "Useful links:\n"
                            "- tournament lobby: %(lobby_link)s\n"
                            "- tournament rating table: %(rating_link)s\n"
                        )
                        % kwargs
                    )

            if destination == self.DISCORD_DESTINATION:
                return (
                    _(
                        "Confirmation stage has begun! "
                        "To confirm your tournament participation go to channel %(confirmation_channel)s "
                        "and send your tenhou.net nickname. \n"
                        "Confirmation stage will be ended at %(confirmation_end_time)s %(timezone)s time.\n\n"
                        "Useful links:\n"
                        "- tournament lobby: %(lobby_link)s\n"
                        "- tournament rating table: %(rating_link)s"
                    )
                    % kwargs
                )

        if notification.notification_type == TournamentNotification.ROUND_FINISHED:
            if destination == TournamentHandler.DISCORD_DESTINATION:
                kwargs["break_end"] = status.end_break_time.replace(tzinfo=pytz.UTC).strftime("%H-%M")

            if destination == TournamentHandler.TELEGRAM_DESTINATION:
                kwargs["break_end"] = status.end_break_time.astimezone(pytz.timezone("Europe/Moscow")).strftime("%H-%M")

            return (
                _(
                    "All games finished. Next round %(current_round)s (of %(total_rounds)s) "
                    "starts in %(break_minutes)s minutes at %(break_end)s UTC.\n\n"
                    "Tournament lobby: %(lobby_link)s"
                )
                % kwargs
            )

        games_prepared_message = _(
            "Round %(current_round)s of %(total_rounds)s starts. "
            "Tournament seating is ready.\n\n"
            "Starting games...\n\n"
            "After the game please send the game log link to the #game_logs channel. "
            "The game log should be sent before the new round starts. "
            "If there is no log when next round start, all players from this game "
            "will get -30000 scores as a round result (their real scores will not be counted)."
        )
        if self.tournament.is_majsoul_tournament:
            games_prepared_message = _(
                "Round %(current_round)s of %(total_rounds)s starts. "
                "Tournament seating is ready.\n\n"
                "Starting games...\n\n"
                "After the game the log will be saved automatically.\n"
                "If this does not happen, please contact the administrator."
            )

        messages = {
            TournamentNotification.GAME_ENDED: _(
                "New game was added.\n\n"
                "Results:\n"
                "```\n"
                "%(player_one)\n"
                "%(player_two)\n"
                "%(player_three)\n"
                "%(player_four)\n"
                "```\n"
                "Game link: %(pantheon_link)\n\n"
                "%(platform_name) link: %(game_replay_link)\n\n"
                "Finished games: %(finished)s/%(total)s."
            ),
            TournamentNotification.CONFIRMATION_ENDED: _(
                "Confirmation stage has ended, there are %(confirmed_players)s players. "
                "Games starts in 10 minutes at 7-30 AM UTC. "
                "Please, follow this link %(lobby_link)s to enter the tournament lobby. "
                "Games will start automatically."
            ),
            TournamentNotification.GAMES_PREPARED: games_prepared_message,
            TournamentNotification.GAME_FAILED: _(
                "Game №%(game_index)s: %(players)s. Is not started. The table was moved to the end of the queue."
            ),
            TournamentNotification.GAME_FAILED_NO_MEMBERS: _(
                "Game №%(game_index)s: %(players)s. Is not started. Missed players %(missed_players)s. "
                "The table was moved to the end of the queue. \n\n"
                "%(missed_players_str) Missed players please enter the tournament lobby: %(lobby_link)."
            ),
            TournamentNotification.GAME_STARTED: _("Game №%(game_index)s: %(players)s. Started."),
            TournamentNotification.TOURNAMENT_FINISHED: _("The tournament is over. Thank you for participating!"),
            TournamentNotification.GAME_PRE_ENDED: _("%(message)s\n\n"),
            TournamentNotification.GAME_LOG_REMINDER: _(
                "Players: %(player_names)s please send link to game log.\n\n"
                "If there is no log when next round start, all players from this game "
                "will get -30000 scores as a round result (their real scores will not be counted)."
            ),
            TournamentNotification.GAME_PENALTY: _(
                "Players: %(player_names)s you got -30000 penalty because of not sent link to game log."
            ),
        }

        return format_text(messages.get(notification.notification_type), kwargs)

    def get_lobby_link(self, lobby=None):
        current_lobby = lobby
        if not current_lobby:
            if not self.tournament.is_majsoul_tournament:
                current_lobby = settings.TOURNAMENT_PUBLIC_LOBBY
            else:
                current_lobby = self.lobby

        if self.tournament:
            if not self.tournament.is_majsoul_tournament:
                return f"http://tenhou.net/0/?{current_lobby}"
            else:
                return f"{current_lobby}"

    def get_rating_link(self):
        return f"https://rating.riichimahjong.org/event/{self.tournament.new_pantheon_id}/order/rating"

    def get_pantheon_game_link(self, hash):
        return f"https://rating.riichimahjong.org/event/{self.tournament.new_pantheon_id}/game/{hash}"

    def get_admin_username(self):
        if self.destination == self.TELEGRAM_DESTINATION:
            return settings.TELEGRAM_ADMIN_USERNAME
        if self.destination == self.DISCORD_DESTINATION:
            return f"<@{settings.DISCORD_ADMIN_ID}>"

    def game_pre_end(self, end_game_message: str):
        status = self.get_status()

        tenhou_nicknames = parse_names_from_tenhou_chat_message(end_game_message)
        game = (
            TournamentGame.objects.filter(tournament=self.tournament)
            .filter(game_players__player__tenhou_username__in=tenhou_nicknames)
            .filter(tournament_round=status.current_round)
            .distinct()
            .first()
        )

        if not game:
            logger.error(f"Can't find game to finish. {tenhou_nicknames}")
            return

        game.status = TournamentGame.FINISHED
        game.save()

        self.create_notification(
            TournamentNotification.GAME_PRE_ENDED,
            tg_ru_kwargs={"message": unquote(end_game_message)},
            discord_ru_kwargs={"message": unquote(end_game_message)},
            discord_en_kwargs={"message": unquote(end_game_message)},
        )

        # postpone reminder
        thread = threading.Thread(target=self.send_log_reminder_message, args=(end_game_message,))
        thread.daemon = True
        thread.start()

        self.check_round_was_finished()

    def send_log_reminder_message(self, end_game_message: str):
        # lets give some time for players before spamming with message
        sleep(120)

        tenhou_nicknames = parse_names_from_tenhou_chat_message(end_game_message)
        players = TournamentPlayers.objects.filter(tenhou_username__in=tenhou_nicknames).filter(
            tournament=self.tournament
        )

        status = self.get_status()
        game = (
            TournamentGame.objects.filter(tournament=self.tournament)
            .filter(game_players__player__tenhou_username__in=tenhou_nicknames)
            .filter(tournament_round=status.current_round)
            .filter(log_id__isnull=True)
            .first()
        )

        # players already submitted game log
        if not game:
            return

        self.create_notification(
            TournamentNotification.GAME_LOG_REMINDER,
            tg_ru_kwargs={"player_names": self.get_players_message_string(players)},
        )

    def get_players_message_string(self, players: List[TournamentPlayers]):
        player_names = []
        for player in players:
            if player.telegram_username:
                player_names.append(f"@{player.telegram_username} ({TournamentHandler.TELEGRAM_DESTINATION})")
            if player.discord_username:
                player_names.append(f"@{player.discord_username} ({TournamentHandler.DISCORD_DESTINATION})")
        return ", ".join(player_names)

    def _numpy_random_sortition(self, pantheon_ids):
        seed = datetime.now().microsecond
        rg = np.random.Generator(PCG64(SeedSequence(seed)))
        # pre shuffle players sequense for legacy sorting
        rg.shuffle(pantheon_ids)
        return self._random_sortition(pantheon_ids)

    def _random_sortition(self, pantheon_ids):
        # default random.shuffle function doesn't produce good results
        # so, let's use our own shuffle implementation
        for i in range(len(pantheon_ids)):
            swap = randint(0, len(pantheon_ids) - 1)
            temp = pantheon_ids[swap]
            pantheon_ids[swap] = pantheon_ids[i]
            pantheon_ids[i] = temp
        return list(self._split_to_chunks(pantheon_ids))

    def _split_to_chunks(self, items):
        n = 4
        for i in range(0, len(items), n):
            yield items[i : i + n]
