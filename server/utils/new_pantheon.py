import logging

from django.conf import settings
from twirp.context import Context

import pantheon_api.atoms_pb2
from pantheon_api.mimir_twirp import MimirClient

logger = logging.getLogger()
# todo move to settings
PRODUCTION_PANTHEON_GAME_MANAGMENT_API = "https://gameapi.riichimahjong.org/"


def get_new_pantheon_swiss_sortition(eventId, adminPersonId):
    client = MimirClient(PRODUCTION_PANTHEON_GAME_MANAGMENT_API)

    context = Context()
    # todo pass pantheon event's owner token
    context.set_header("X-Auth-Token", settings.PANTHEON_ADMIN_TOKEN)
    context.set_header("X-Current-Event-Id", str(eventId))
    context.set_header("X-Current-Person-Id", str(adminPersonId))

    return client.GenerateSwissSeating(
        ctx=context,
        request=pantheon_api.atoms_pb2.GenericEventPayload(event_id=eventId),
        server_path_prefix="/v2",
    )
