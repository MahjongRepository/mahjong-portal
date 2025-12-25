# -*- coding: utf-8 -*-

import logging

from django.utils.translation import activate

from online.handler import TournamentHandler
from online.models import TournamentNotification
from tournament.models import Tournament

logger = logging.getLogger("tournament_bot")

# todo: move into self
tournament_handler = TournamentHandler()


class PortalAutoBot:
    def init(self, tournamentId, lobbyId):
        tournament = Tournament.objects.get(id=tournamentId)
        tournament_handler.init(tournament, lobbyId, None, TournamentHandler.TELEGRAM_DESTINATION)

    @staticmethod
    def open_registration(chatId):
        logger.info("Open confirmation stage")
        logger.info(f"Chat ID {chatId}")
        tournament_handler.open_registration()

    @staticmethod
    def close_registration(chatId):
        logger.info("Close registration")
        logger.info(f"Chat ID {chatId}")
        tournament_handler.close_registration()

    @staticmethod
    def check_new_notifications(tournamentId):
        tg_ru_notification = TournamentNotification.objects.filter(
            is_processed=False,
            destination=TournamentNotification.TELEGRAM,
            failed=False,
            tournament_id=tournamentId,
            lang=TournamentNotification.RU,
        ).last()

        discord_en_notification = TournamentNotification.objects.filter(
            is_processed=False,
            destination=TournamentNotification.DISCORD,
            failed=False,
            tournament_id=tournamentId,
            lang=TournamentNotification.EN,
        ).last()

        discord_ru_notification = TournamentNotification.objects.filter(
            is_processed=False,
            destination=TournamentNotification.DISCORD,
            failed=False,
            tournament_id=tournamentId,
            lang=TournamentNotification.RU,
        ).last()

        if not tg_ru_notification and not discord_en_notification and not discord_ru_notification:
            return []

        notifications = []
        if tg_ru_notification:
            notifications.append(
                PortalAutoBot.prepare_notification_message(tg_ru_notification, TournamentNotification.TELEGRAM, "ru")
            )
        if discord_en_notification:
            notifications.append(
                PortalAutoBot.prepare_notification_message(
                    discord_en_notification, TournamentNotification.DISCORD, "en"
                )
            )
        if discord_ru_notification:
            notifications.append(
                PortalAutoBot.prepare_notification_message(
                    discord_ru_notification, TournamentNotification.DISCORD, "ru"
                )
            )

        return notifications

    @staticmethod
    def prepare_notification_message(notification, destination, lang):
        try:
            logger.info(f"Notification id={notification.id} found")
            current_destination = tournament_handler.TELEGRAM_DESTINATION
            if destination == TournamentNotification.DISCORD:
                current_destination = tournament_handler.DISCORD_DESTINATION
            message = tournament_handler.get_notification_text(lang, notification, current_destination)
            return {
                "message": message,
                "notification_id": notification.id,
                "destination": notification.destination,
                "type": notification.notification_type,
                "lang": notification.lang,
            }
        except Exception as e:
            notification.failed = True
            notification.save()
            logger.error(e, exc_info=e)

    @staticmethod
    def process_notification(notificationId, tournamentId):
        notification = TournamentNotification.objects.get(
            id=notificationId, tournament_id=tournamentId, is_processed=False
        )

        if not notification:
            return None

        try:
            notification.is_processed = True
            notification.failed = False
            notification.save()
            logger.info(f"Notification id={notification.id} update to processed")
        except Exception as e:
            notification.failed = True
            notification.save()
            logger.error(e, exc_info=e)

    @staticmethod
    def prepare_next_round():
        logger.info("Prepare next round")

        return tournament_handler.prepare_next_round(reshuffleInPortal=False)

    @staticmethod
    def confirm_player(nickname, telegram_username, discord_username, requested_lang):
        activate(requested_lang)

        return tournament_handler.confirm_participation_in_tournament(
            nickname, telegram_username=telegram_username, discord_username=discord_username
        )

    @staticmethod
    def admin_confirm_player(friend_id, nickname, telegram_username):
        activate("ru")

        return tournament_handler.confirm_participation_in_tournament(
            nickname, telegram_username=telegram_username, friend_id=friend_id, is_admin=True
        )

    @staticmethod
    def create_start_game_notification(tour, table_number, notification_type, missed_players):
        tournament_handler.create_start_game_notification(
            int(tour), int(table_number), int(notification_type), missed_players
        )

    @staticmethod
    def game_finish(log_id, players, log_content, log_time, requested_lang):
        activate(requested_lang)

        return tournament_handler.game_finish(log_id, players, log_content, log_time)

    @staticmethod
    def get_tournament_status(requested_lang):
        logger.info("Get tournament status command")
        activate(requested_lang)
        return tournament_handler.get_tournament_status()

    @staticmethod
    def get_allowed_players():
        return tournament_handler.get_allowed_players()

    @staticmethod
    def add_game_log(log_link, requested_lang):
        activate(requested_lang)

        return tournament_handler.add_game_log(log_link)

    @staticmethod
    def add_penalty_game(requested_lang, game_id):
        activate(requested_lang)
        return tournament_handler.add_penalty_game(game_id)

    @staticmethod
    def send_team_names_to_pantheon(requested_lang):
        activate(requested_lang)
        return tournament_handler.send_team_names_to_pantheon()

    @staticmethod
    def check_player(nickname, confirm_code, requested_lang):
        activate(requested_lang)
        return tournament_handler.check_player(nickname, confirm_code)
