# -*- coding: utf-8 -*-

import logging

from django.conf import settings
from django.utils.translation import gettext as _
from twirp.context import Context

import pantheon_api.atoms_pb2
import pantheon_api.frey_pb2
import pantheon_api.mimir_pb2
from online.models import TournamentPlayers
from pantheon_api.frey_twirp import FreyClient
from pantheon_api.mimir_twirp import MimirClient

logger = logging.getLogger()
# todo move to settings
PRODUCTION_PANTHEON_GAME_MANAGMENT_API = "https://gameapi.riichimahjong.org/"
PRODUCTION_PANTHEON_USER_MANAGMENT_API = "https://userapi.riichimahjong.org/"


def get_new_pantheon_swiss_sortition(pantheonEventId, adminPersonId):
    client = MimirClient(PRODUCTION_PANTHEON_GAME_MANAGMENT_API)

    context = Context()
    # todo pass pantheon event's owner token
    context.set_header("X-Auth-Token", settings.PANTHEON_ADMIN_COOKIE)
    context.set_header("X-Current-Event-Id", str(pantheonEventId))
    context.set_header("X-Current-Person-Id", str(adminPersonId))

    return client.GenerateSwissSeating(
        ctx=context,
        request=pantheon_api.mimir_pb2.SeatingGenerateSwissSeatingPayload(
            event_id=int(pantheonEventId), substitute_replacement_players=True
        ),
        server_path_prefix="/v2",
    )


def get_pantheon_public_person_information(personId, email):
    client = FreyClient(PRODUCTION_PANTHEON_USER_MANAGMENT_API)

    response = client.GetPersonalInfo(
        ctx=Context(),
        request=pantheon_api.frey_pb2.PersonsGetPersonalInfoPayload(ids=[personId]),
        server_path_prefix="/v2",
    )
    person = response.people[0]

    return {
        "person_id": person.id,
        "country": person.country,
        "city": person.city,
        "tenhou_id": person.tenhou_id,
        "title": person.title,
        "has_avatar": person.has_avatar,
        "ms_nickname": person.ms_nickname,
        "ms_account_id": person.ms_account_id,
        "email": email,
    }


def update_personal_info(person_info, adminPersonId, pantheonEventId):
    client = FreyClient(PRODUCTION_PANTHEON_USER_MANAGMENT_API)
    context = Context()
    # todo pass pantheon event's owner token
    context.set_header("X-Auth-Token", settings.PANTHEON_ADMIN_COOKIE)
    context.set_header("X-Current-Event-Id", str(pantheonEventId))
    context.set_header("X-Current-Person-Id", str(adminPersonId))

    return client.UpdatePersonalInfo(
        ctx=context,
        request=pantheon_api.frey_pb2.PersonsUpdatePersonalInfoPayload(
            id=int(person_info["person_id"]),
            tenhou_id=str(person_info["tenhou_id"]),
            ms_nickname=str(person_info["ms_nickname"]),
            ms_friend_id=int(person_info["ms_friend_id"]),
            ms_account_id=int(person_info["ms_account_id"]),
            title=str(person_info["title"]),
            city=str(person_info["city"]),
            country=str(person_info["country"]),
            has_avatar=bool(person_info["has_avatar"], email=str(person_info["email"])),
        ),
        server_path_prefix="/v2",
    )


def register_player(adminPersonId, pantheonEventId, pantheonId):
    client = MimirClient(PRODUCTION_PANTHEON_GAME_MANAGMENT_API)

    context = Context()
    # todo pass pantheon event's owner token
    context.set_header("X-Auth-Token", settings.PANTHEON_ADMIN_COOKIE)
    context.set_header("X-Current-Event-Id", str(pantheonEventId))
    context.set_header("X-Current-Person-Id", str(adminPersonId))

    return client.RegisterPlayer(
        ctx=context,
        request=pantheon_api.mimir_pb2.EventsRegisterPlayerPayload(
            event_id=int(pantheonEventId), player_id=int(pantheonId)
        ),
        server_path_prefix="/v2",
    )


def add_user_to_new_pantheon(
    record: TournamentPlayers, registration, pantheonEventId, adminPersonId, isMajsoulTournament
):
    if not registration.user or not registration.user.email:
        return _("There is no user email in the registration."), False

    person_info = get_pantheon_public_person_information(record.pantheon_id, registration.user.email)

    if isMajsoulTournament:
        person_info["ms_nickname"] = registration.ms_nickname
        person_info["ms_account_id"] = registration.ms_account_id
        person_info["ms_friend_id"] = registration.ms_friend_id
    else:
        person_info["tenhou_id"] = registration.tenhou_nickname
        person_info["ms_friend_id"] = -1

    # todo: check update person errors
    update_personal_info(person_info, adminPersonId, pantheonEventId)
    # todo: check register player error
    register_player(adminPersonId, pantheonEventId, record.pantheon_id)
    return "Success", True


def upload_replay_through_pantheon(eventId, platformId, contentType, replayHash, logTime, content):
    client = MimirClient(PRODUCTION_PANTHEON_GAME_MANAGMENT_API)

    context = Context()
    context.set_header("HTTP-X-EXTERNAL-QUERY-SECRET", settings.EXTERNAL_QUERY_SECRET)

    return client.AddTypedOnlineReplay(
        ctx=context,
        request=pantheon_api.mimir_pb2.TypedGamesAddOnlineReplayPayload(
            event_id=int(eventId),
            platform_id=int(platformId),
            content_type=int(contentType),
            log_timestamp=int(logTime),
            replay_hash=str(replayHash),
            content=content,
        ),
        server_path_prefix="/v2",
    )


def add_online_replay_through_pantheon(eventId, tenhouGameLink):
    client = MimirClient(PRODUCTION_PANTHEON_GAME_MANAGMENT_API)

    context = Context()
    context.set_header("HTTP-X-EXTERNAL-QUERY-SECRET", settings.EXTERNAL_QUERY_SECRET)

    return client.AddOnlineReplay(
        ctx=context,
        request=pantheon_api.mimir_pb2.GamesAddOnlineReplayPayload(
            event_id=int(eventId),
            link=str(tenhouGameLink),
        ),
        server_path_prefix="/v2",
    )


def add_penalty_game(pantheonEventId, adminPersonId, playerIds):
    client = MimirClient(PRODUCTION_PANTHEON_GAME_MANAGMENT_API)

    context = Context()
    # todo pass pantheon event's owner token
    context.set_header("X-Auth-Token", settings.PANTHEON_ADMIN_COOKIE)
    context.set_header("X-Current-Event-Id", str(pantheonEventId))
    context.set_header("X-Current-Person-Id", str(adminPersonId))

    return client.AddPenaltyGame(
        ctx=context,
        request=pantheon_api.mimir_pb2.GamesAddPenaltyGamePayload(event_id=int(pantheonEventId), players=playerIds),
        server_path_prefix="/v2",
    )


def send_team_names_to_pantheon(pantheonEventId, adminPersonId, teamMapping):
    client = MimirClient(PRODUCTION_PANTHEON_GAME_MANAGMENT_API)

    context = Context()
    # todo pass pantheon event's owner token
    context.set_header("X-Auth-Token", settings.PANTHEON_ADMIN_COOKIE)
    context.set_header("X-Current-Event-Id", str(pantheonEventId))
    context.set_header("X-Current-Person-Id", str(adminPersonId))

    teams = []
    for team in teamMapping:
        teams.append(
            pantheon_api.atoms_pb2.TeamMapping(player_id=int(team["player_id"]), team_name=str(team["team_name"]))
        )

    return client.UpdatePlayersTeams(
        ctx=context,
        request=pantheon_api.mimir_pb2.EventsUpdatePlayersTeamsPayload(
            event_id=int(pantheonEventId), ids_to_team_names=teams
        ),
        server_path_prefix="/v2",
    )
