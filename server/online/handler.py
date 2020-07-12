# -*- coding: utf-8 -*-
import logging
import random
from copy import copy
from datetime import timedelta
from random import randint
from typing import Dict, Optional
from urllib.parse import parse_qs, unquote, urlparse

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone, translation
from django.utils.translation import activate
from django.utils.translation import gettext as _

from online.models import (
    TournamentGame,
    TournamentGamePlayer,
    TournamentNotification,
    TournamentPlayers,
    TournamentStatus,
)
from online.parser import TenhouParser
from player.models import Player
from player.tenhou.management.commands.add_tenhou_account import get_started_date_for_account
from tournament.models import OnlineTournamentRegistration
from utils.general import make_random_letters_and_digit_string
from utils.pantheon import add_tenhou_game_to_pantheon, add_user_to_pantheon, get_pantheon_swiss_sortition

logger = logging.getLogger()


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
                return _("Games will start soon. Confirmed players: %(confirmed_players)s.") % {
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

        self.create_notification(
            TournamentNotification.CONFIRMATION_STARTED,
            kwargs={"lobby_link": self.get_lobby_link(), "rating_link": self.get_rating_link()},
        )

    def close_registration(self):
        status = self.get_status()
        status.registration_closed = True
        status.save()

        confirmed_players = TournamentPlayers.objects.filter(tournament=self.tournament).count()
        self.create_notification(
            TournamentNotification.CONFIRMATION_ENDED,
            {"lobby_link": self.get_lobby_link(), "confirmed_players": confirmed_players},
        )

    def send_team_names_to_pantheon(self):
        registrations = TournamentPlayers.objects.filter(tournament=self.tournament)

        team_names = {}
        for registration in registrations:
            team_names[registration.pantheon_id] = registration.team_name

        data = {
            "jsonrpc": "2.0",
            "method": "updatePlayersTeams",
            "params": {"eventId": settings.PANTHEON_EVENT_ID, "teamNameMap": team_names},
            "id": make_random_letters_and_digit_string(),
        }

        headers = {"X-Auth-Token": settings.PANTHEON_ADMIN_TOKEN}

        response = requests.post(settings.PANTHEON_URL, json=data, headers=headers)
        if response.status_code == 500:
            logger.error("Log add. Pantheon 500.")
            return "Pantheon 500 error"

        content = response.json()
        if content.get("error"):
            logger.error("Log add. Pantheon error. {}".format(content.get("error")))
            return "Pantheon {} error".format(content.get("error"))

        return "Готово"

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

        try:
            parser = TenhouParser()
            players = parser.get_player_names(log_id)
        except Exception:
            return (
                _("Fail to add this game. Try again in a moment or you havn't copied the entire link of the game log."),
                False,
            )

        if TournamentGame.objects.filter(log_id=log_id).exists():
            return _("The game has been added. Thank you."), True

        games = (
            TournamentGame.objects.filter(tournament=self.tournament)
            .filter(game_players__player__tenhou_username__in=players)
            .filter(tournament_round=status.current_round)
            .distinct()
        )
        error_message = _("Fail to add game log. Contact the administrator %(admin_username)s.") % {
            "admin_username": self.get_admin_username()
        }
        if games.count() >= 2:
            logger.error("Log add. Too much games.")
            return error_message, False

        game = games.first()
        response = add_tenhou_game_to_pantheon(log_link)
        if response.status_code == 500:
            logger.error("Log add. Pantheon 500.")
            return error_message, False

        content = response.json()
        if content.get("error"):
            logger.error("Log add. Pantheon error. {}".format(content.get("error")))
            return error_message, False

        game_info = content["result"]["games"][0]
        pantheon_url = f"https://gui.mjtop.net/eid{settings.PANTHEON_EVENT_ID}/game/{game_info['hash']}"

        pantheon_players = {}
        for pantheon_player_id in content["result"]["players"].keys():
            pantheon_players[pantheon_player_id] = {
                "id": pantheon_player_id,
                "tenhou_nickname": content["result"]["players"][pantheon_player_id]["tenhou_id"],
                "pantheon_name": content["result"]["players"][pantheon_player_id]["display_name"],
                "score": 0,
                "place": 0,
                "rating_delta": 0,
            }

        for pantheon_player_id in game_info["final_results"].keys():
            pantheon_players[pantheon_player_id]["score"] = game_info["final_results"][pantheon_player_id]["score"]
            pantheon_players[pantheon_player_id]["place"] = game_info["final_results"][pantheon_player_id]["place"]
            pantheon_players[pantheon_player_id]["rating_delta"] = game_info["final_results"][pantheon_player_id][
                "rating_delta"
            ]

        formatted_players = []
        players_info = sorted(pantheon_players.values(), key=lambda x: x["place"])
        # align strings and format scores
        max_nick_length = max([len(x["tenhou_nickname"]) for x in players_info])
        max_scores_length = max([len(str(x["score"])) for x in players_info])
        for player_info in players_info:
            try:
                player_record = Player.objects.get(pantheon_id=player_info["id"])
                display_name = f"{player_record.last_name_ru} ({player_record.last_name_en})"
            except Player.DoesNotExist:
                display_name = player_info["pantheon_name"]

            tenhou_nickname = player_info["tenhou_nickname"].ljust(max_nick_length, " ")

            scores = str(player_info["score"]).rjust(max_scores_length, " ")
            rating_delta = player_info["rating_delta"]
            if rating_delta > 0:
                rating_delta = f"+{rating_delta}"

            formatted_players.append(
                f"{player_info['place']}. {display_name}\n{tenhou_nickname} {scores} ({rating_delta})"
            )

        game.log_id = log_id
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
            kwargs={
                "finished": finished_games.count(),
                "total": total_games,
                "pantheon_link": pantheon_url,
                "tenhou_link": f"http://tenhou.net/0/?log={log_id}",
                "player_one": formatted_players[0],
                "player_two": formatted_players[1],
                "player_three": formatted_players[2],
                "player_four": formatted_players[3],
            },
        )

        self.check_round_was_finished()

        return _("The game has been added. Thank you."), True

    def confirm_participation_in_tournament(self, tenhou_nickname, telegram_username=None, discord_username=None):
        status = self.get_status()

        if status.registration_closed:
            return _("The confirmation phase has already ended. Visit our next tournaments.")

        if len(tenhou_nickname) > 8:
            return _("The tenhou.net nickname must not be longer than eight characters.")

        try:
            registration = OnlineTournamentRegistration.objects.get(
                tenhou_nickname=tenhou_nickname, tournament=self.tournament
            )
        except OnlineTournamentRegistration.DoesNotExist:
            return _(
                "Your tenhou.net username is out of tournament registration list. Contact the administrator %(admin_username)s."
            ) % {"admin_username": self.get_admin_username()}

        if TournamentPlayers.objects.filter(tenhou_username=tenhou_nickname, tournament=self.tournament).exists():
            return _('Nickname "%(tenhou_nickname)s" was already confirmed for this tournament.') % {
                "tenhou_nickname": tenhou_nickname
            }

        account_started_date = get_started_date_for_account(tenhou_nickname)
        if not account_started_date and telegram_username != settings.TELEGRAM_ADMIN_USERNAME[1:]:
            return _(
                'Nickname "%(tenhou_nickname)s" doesn\'t have game records. '
                "Are you sure it is spelled correctly? Case of letters is important! Contact admin %(admin_username)s."
            ) % {"tenhou_nickname": tenhou_nickname, "admin_username": self.get_admin_username()}

        pantheon_id = registration.player and registration.player.pantheon_id or None
        team_name = registration.notes

        record = TournamentPlayers.objects.create(
            telegram_username=telegram_username,
            discord_username=discord_username,
            tenhou_username=tenhou_nickname,
            tournament=self.tournament,
            pantheon_id=pantheon_id,
            team_name=team_name,
        )

        try:
            add_user_to_pantheon(record)
        except Exception as e:
            logger.error(e, exc_info=e)

        return _("Your participation in the tournament has been confirmed!")

    def prepare_next_round(self):
        status = self.get_status()

        if not status.current_round:
            status.current_round = 0

        if status.current_round >= self.tournament.number_of_sessions:
            return "Невозможно запустить новые игры. У турнира закончились туры."

        current_games = TournamentGame.objects.filter(tournament=self.tournament).exclude(
            status=TournamentGame.FINISHED
        )

        if current_games.exists():
            return "Невозможно запустить новые игры. Старые игры ещё не завершились."

        confirmed_players = TournamentPlayers.objects.filter(tournament=self.tournament)

        missed_id = confirmed_players.filter(pantheon_id=None)
        if missed_id.exists():
            return "Невозможно запустить новые игры. Не у всех игроков стоит pantheon id."

        with transaction.atomic():
            status.current_round += 1
            status.end_break_time = None

            pantheon_ids = {}
            for confirmed_player in confirmed_players:
                pantheon_ids[confirmed_player.pantheon_id] = confirmed_player

            sortition = self.make_sortition(list(pantheon_ids.keys()), status.current_round)
            # sortition = TeamSeating.get_seating_for_round(status.current_round)

            games = []
            for item in sortition:
                logger.info(item)
                # shuffle player winds
                random.shuffle(item)

                try:
                    game = TournamentGame.objects.create(
                        status=TournamentGame.NEW, tournament=self.tournament, tournament_round=status.current_round
                    )

                    for wind in range(0, len(item)):
                        player_id = pantheon_ids[item[wind]].id

                        TournamentGamePlayer.objects.create(game=game, player_id=player_id, wind=wind)
                    games.append(game)
                except Exception as e:
                    logger.error("Failed to prepare a game. Pantheon ids={}".format(item), exc_info=e)

            # we was able to generate games
            if games:
                status.save()

                # for users
                self.create_notification(
                    TournamentNotification.GAMES_PREPARED,
                    {"current_round": status.current_round, "total_rounds": self.tournament.number_of_sessions},
                )

                # for admin
                message = "Тур {}. Игры сформированы.".format(status.current_round)
            else:
                message = "Игры не запустились. Требуется вмешательство администратора."

        return message

    def make_sortition(self, pantheon_ids, current_round):
        if current_round == 1:
            return self._random_sortition(pantheon_ids)
        else:
            return get_pantheon_swiss_sortition()

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

        url = "http://tenhou.net/cs/edit/start.cgi"
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
            location = unquote(response.headers["location"])
            result = location.split("{}&".format(self.lobby))[1]

            if result.startswith("FAILED"):
                logger.error(result)
                game.status = TournamentGame.FAILED_TO_START
                self.create_notification(
                    TournamentNotification.GAME_FAILED, kwargs={"players": ", ".join(escaped_player_names)}
                )
            elif result.startswith("MEMBER NOT FOUND"):
                missed_player_ids = [x for x in result.split("\r\n")[1:] if x]
                missed_player_objects = TournamentPlayers.objects.filter(tenhou_username__in=missed_player_ids).filter(
                    tournament=self.tournament
                )

                missed_player_nicknames = []
                for missed_player in missed_player_objects:
                    if missed_player.telegram_username:
                        missed_player_nicknames.append(
                            f"@{missed_player.telegram_username} ({self.TELEGRAM_DESTINATION})"
                        )
                    if missed_player.discord_username:
                        missed_player_nicknames.append(
                            f"@{missed_player.discord_username} ({self.DISCORD_DESTINATION})"
                        )

                game.status = TournamentGame.FAILED_TO_START
                self.create_notification(
                    TournamentNotification.GAME_FAILED_NO_MEMBERS,
                    kwargs={
                        "players": ", ".join(escaped_player_names),
                        "missed_players": ", ".join(missed_player_nicknames),
                    },
                )
            else:
                game.status = TournamentGame.STARTED
                self.create_notification(
                    TournamentNotification.GAME_STARTED, kwargs={"players": ", ".join(escaped_player_names)}
                )
        except Exception as e:
            logger.error(e, exc_info=e)

            game.status = TournamentGame.FAILED_TO_START
            self.create_notification(
                TournamentNotification.GAME_FAILED, kwargs={"players": ", ".join(escaped_player_names)}
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
                pass
                # self.create_notification(TournamentNotification.TOURNAMENT_FINISHED)
            else:
                index = status.current_round - 1
                break_minutes = self.TOURNAMENT_BREAKS_TIME[index]
                status.end_break_time = timezone.now() + timedelta(minutes=break_minutes)
                status.save()
                self.create_notification(
                    TournamentNotification.ROUND_FINISHED,
                    {"break_minutes": break_minutes, "lobby_link": self.get_lobby_link()},
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

    def create_notification(self, notification_type: int, kwargs: Optional[Dict] = None):
        if not kwargs:
            kwargs = {}

        with transaction.atomic():
            TournamentNotification.objects.create(
                tournament=self.tournament,
                notification_type=notification_type,
                message_kwargs=kwargs,
                destination=TournamentNotification.DISCORD,
            )

            TournamentNotification.objects.create(
                tournament=self.tournament,
                notification_type=notification_type,
                message_kwargs=kwargs,
                destination=TournamentNotification.TELEGRAM,
            )

    def get_notification_text(
        self, lang: str, notification: TournamentNotification, extra_kwargs: Optional[dict] = None
    ):
        activate(lang)

        kwargs = copy(notification.message_kwargs)
        if extra_kwargs:
            kwargs.update(extra_kwargs)

        if self.destination == self.DISCORD_DESTINATION:
            # this will disable links preview for discord messages
            for key, value in kwargs.items():
                if type(value) == str and value.startswith("http"):
                    kwargs[key] = f"<{value}>"

        if notification.notification_type == TournamentNotification.CONFIRMATION_STARTED:
            if self.destination == self.TELEGRAM_DESTINATION:
                return (
                    "Начался этап подтверждения участия! "
                    'Для подтверждения своего участия отправьте команду "`/me ваш ник на тенхе`" (регистр важен!). '
                    "Этап завершится в 10-20 (МСК).\n\n"
                    "Полезные ссылки:\n"
                    "- турнирное лобби: %(lobby_link)s\n"
                    "- турнирный рейтинг: %(rating_link)s\n"
                ) % kwargs

            if self.destination == self.DISCORD_DESTINATION:
                return (
                    _(
                        "Confirmation stage has begun! "
                        "To confirm your tournament participation go to %(confirmation_channel)s "
                        "and send your tenhou.net nickname. "
                        "Confirmation stage will be ended at 7-20 UTC time.\n\n"
                        "Useful links:\n"
                        "- tournament lobby: %(lobby_link)s\n"
                        "- tournament rating table: %(rating_link)s"
                    )
                    % kwargs
                )

        messages = {
            TournamentNotification.GAME_ENDED: _(
                "New game was added.\n\n"
                "Results:\n"
                "```\n"
                "%(player_one)s\n"
                "%(player_two)s\n"
                "%(player_three)s\n"
                "%(player_four)s\n"
                "```\n"
                "Game link: %(pantheon_link)s\n\n"
                "Tenhou link: %(tenhou_link)s\n\n"
                "Finished games: %(finished)s/%(total)s."
            ),
            TournamentNotification.CONFIRMATION_ENDED: _(
                "Confirmation stage has ended, there are %(confirmed_players)s players. "
                "Games starts **in 10 minutes**. "
                "Please, follow this link %(lobby_link)s to enter the tournament lobby. "
                "Games will start automatically."
            ),
            TournamentNotification.GAMES_PREPARED: _(
                "Round %(current_round)s of %(total_rounds)s starts. "
                "Tournament seating is ready.\n\n"
                "Starting games...\n\n"
                "After the game please send a link to the game log, "
                "it will save some time for the tournament admin "
                "(without all collected logs we can't finish the tournament round)."
            ),
            TournamentNotification.GAME_FAILED: _(
                "Game: %(players)s is not started. The table was moved to the end of the queue."
            ),
            TournamentNotification.GAME_FAILED_NO_MEMBERS: _(
                "Game: %(players)s is not started. "
                "Missed players %(missed_players)s. The table was moved to the end of the queue."
            ),
            TournamentNotification.GAME_STARTED: _("Game: %(players)s started."),
            TournamentNotification.ROUND_FINISHED: _(
                "All games finished. Next round starts in %(break_minutes)s minutes.\n\n"
                "Tournament lobby: %(lobby_link)s"
            ),
            TournamentNotification.TOURNAMENT_FINISHED: _("The tournament is over. Thank you for participating!"),
        }
        return messages.get(notification.notification_type) % kwargs

    def get_lobby_link(self):
        return f"http://tenhou.net/0/?{settings.TOURNAMENT_PUBLIC_LOBBY}"

    def get_rating_link(self):
        return f"https://gui.mjtop.net/eid{settings.PANTHEON_EVENT_ID}/stat"

    def get_admin_username(self):
        if self.destination == self.TELEGRAM_DESTINATION:
            return settings.TELEGRAM_ADMIN_USERNAME
        if self.destination == self.DISCORD_DESTINATION:
            return f"<@{settings.DISCORD_ADMIN_ID}>"

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
