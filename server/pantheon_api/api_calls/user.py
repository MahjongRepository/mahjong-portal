from django.conf import settings
from twirp.context import Context

from pantheon_api import frey_pb2
from pantheon_api.frey_twirp import FreyClient


def login_through_pantheon(email, password):
    client = FreyClient(settings.PANTHEON_AUTH_API_URL)

    return client.Authorize(
        ctx=Context(),
        request=frey_pb2.AuthAuthorizePayload(email=email, password=password),
        server_path_prefix="/v2",
    )


def get_current_pantheon_user_data(person_id, auth_token):
    client = FreyClient(settings.PANTHEON_AUTH_API_URL)

    response = client.Me(
        ctx=Context(),
        request=frey_pb2.AuthMePayload(person_id=person_id, auth_token=auth_token),
        server_path_prefix="/v2",
    )

    return {
        "person_id": response.person_id,
        "country": response.country,
        "city": response.city,
        "email": response.email,
        "phone": response.phone,
        "tenhou_id": response.tenhou_id,
        "title": response.title,
    }


def get_pantheon_public_person_information(person_id):
    client = FreyClient(settings.PANTHEON_AUTH_API_URL)

    response = client.GetPersonalInfo(
        ctx=Context(),
        request=frey_pb2.PersonsGetPersonalInfoPayload(ids=[person_id]),
        server_path_prefix="/v2",
    )
    person = response.people[0]

    return {
        "person_id": person.id,
        "country": person.country,
        "city": person.city,
        "tenhou_id": person.tenhou_id,
        "title": person.title,
    }
