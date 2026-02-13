# -*- coding: utf-8 -*-
import ms.protocol_pb2 as pb
from django.conf import settings

from player.mahjong_soul.management.commands.ms_servers_base import MSServerBaseCommand
from tournament.models import MsOnlineTournamentRegistration


class Command(MSServerBaseCommand):
    async def process_validate(self, lobby, tournament_id, force=False):
        if not force:
            registrations = MsOnlineTournamentRegistration.objects.filter(
                tournament_id=tournament_id, is_validated=False
            )
        else:
            registrations = MsOnlineTournamentRegistration.objects.filter(tournament_id=tournament_id)

        print(f"found {len(registrations)} not validated registrations")

        account_ids = []
        registration_mapping = {}
        not_found_on_server = 0
        for registration in registrations:
            req = pb.ReqSearchAccountByPattern()
            req.search_next = False
            req.pattern = str(registration.ms_friend_id)

            res = await lobby.search_account_by_pattern(req)

            if res.error.code:
                print("SearchAccount Error:")
                print(res)
                not_found_on_server = not_found_on_server + 1

            account_id = res.decode_id
            account_ids.append(int(account_id))
            registration_mapping[account_id] = registration

        updated_players = 0
        failed_updated_players = 0
        for current_account_id in account_ids:
            req = pb.ReqMultiAccountId()
            req.account_id_list.extend([current_account_id])
            res = await lobby.fetch_multi_account_brief(req)

            if res.error.code:
                print("friend_id=%d SearchMultiAccount Error:" % registration_mapping[current_account_id].ms_friend_id)
                print(res)
                not_found_on_server = not_found_on_server + 1

            for player in res.players:
                registrant = registration_mapping[player.account_id]
                if registrant.ms_nickname == player.nickname:
                    registrant.ms_account_id = player.account_id
                    registrant.is_validated = True
                    registrant.save()
                    print("found player : %s with account_id=%s, updated" % (registrant.ms_nickname, player.account_id))
                    updated_players = updated_players + 1
                else:
                    print(
                        "player data not valid : %s with friend_id=%s, actual nickname=%s"
                        % (registrant.ms_nickname, registrant.ms_friend_id, player.nickname)
                    )
                    failed_updated_players = failed_updated_players + 1
        print(
            f"not found on server={not_found_on_server}, updated players={updated_players}, "
            f"failed updated players={failed_updated_players}"
        )

    async def run_code_with_channel(self, lobby, channel, version_to_force, *args, **options):
        tournament_id = options.get("tournament_id")
        server_type = options.get("server_type")
        access_token = options.get("access_token")
        force = options.get("force")

        if server_type.lower() == "cn":
            result = await self.login(lobby, settings.MS_USERNAME, settings.MS_PASSWORD, version_to_force)
        else:
            result = await self.login_with_token(lobby, access_token, version_to_force)
        if not result:
            print("Exit")
            await channel.close()
            return

        await self.process_validate(lobby, tournament_id, force)
