import ms.protocol_pb2 as pb
from google.protobuf.json_format import MessageToJson, MessageToDict

from player.mahjong_soul.management.commands.ms_base import MSBaseCommand
from player.mahjong_soul.models import MSAccount, MSAccountStatistic


class Command(MSBaseCommand):

    async def run_code(self, lobby, *args, **options):
        ms_accounts = MSAccount.objects.all()

        for ms_account in ms_accounts:
            request = pb.ReqAccountInfo()
            request.account_id = ms_account.account_id
            response = await lobby.fetch_account_info(request)

            ms_account.account_name = response.account.nickname
            ms_account.save()

            four_people_stat, _ = MSAccountStatistic.objects.get_or_create(
                game_type=MSAccountStatistic.FOUR_PLAYERS,
                account=ms_account
            )
            four_people_stat.rank = response.account.level.id
            four_people_stat.points = response.account.level.score

            three_people_stat, _ = MSAccountStatistic.objects.get_or_create(
                game_type=MSAccountStatistic.THREE_PLAYERS,
                account=ms_account
            )
            three_people_stat.rank = response.account.level3.id
            three_people_stat.points = response.account.level3.score

            request = pb.ReqAccountStatisticInfo()
            request.account_id = ms_account.account_id
            response = await lobby.fetch_account_statistic_info(request)
            response = MessageToDict(response)

            # statistic_data[]
            # mahjongCategory
            # 1 - 4 players
            # 2 - 3 players
            # gameCategory
            # 1 - friendly match
            # 2 - rating match

            # detailData.rankStatistic.totalStatistic.allLevelStatistic.gameMode[]
            # mode
            # 1 - 4p tonpusen
            # 2 - 4p hanchan
            # 11 - 3p tonpusen
            # 12 - 3p hanchan
            #
            # gameFinalPosition[]

            FOUR_TONPUSEN = 1
            FOUR_HANCHAN = 2
            THREE_TONPUSEN = 11
            THREE_HANCHAN = 12
            games_statistics = response['detailData']['rankStatistic']['totalStatistic']['allLevelStatistic']['gameMode']

            four_tonpusen_data = [x for x in games_statistics if x['mode'] == FOUR_TONPUSEN]
            if four_tonpusen_data:
                first_place, second_place, third_place, fourth_place, games_count, average_place = self.calculate_stat(
                    four_tonpusen_data
                )

                four_people_stat.tonpusen_games = games_count
                four_people_stat.tonpusen_average_place = average_place
                four_people_stat.tonpusen_first_place = first_place
                four_people_stat.tonpusen_second_place = second_place
                four_people_stat.tonpusen_third_place_place = third_place
                four_people_stat.tonpusen_fourth_place = fourth_place

            four_hanchan_data = [x for x in games_statistics if x['mode'] == FOUR_HANCHAN]
            if four_hanchan_data:
                first_place, second_place, third_place, fourth_place, games_count, average_place = self.calculate_stat(
                    four_hanchan_data
                )

                four_people_stat.hanchan_games = games_count
                four_people_stat.hanchan_average_place = average_place
                four_people_stat.hanchan_first_place = first_place
                four_people_stat.hanchan_second_place = second_place
                four_people_stat.hanchan_third_place_place = third_place
                four_people_stat.hanchan_fourth_place = fourth_place

            three_tonpusen_data = [x for x in games_statistics if x['mode'] == THREE_TONPUSEN]
            if three_tonpusen_data:
                first_place, second_place, third_place, _, games_count, average_place = self.calculate_stat(
                    three_tonpusen_data
                )

                three_people_stat.tonpusen_games = games_count
                three_people_stat.tonpusen_average_place = average_place
                three_people_stat.tonpusen_first_place = first_place
                three_people_stat.tonpusen_second_place = second_place
                three_people_stat.tonpusen_third_place_place = third_place

            three_hanchan_data = [x for x in games_statistics if x['mode'] == THREE_HANCHAN]
            if three_hanchan_data:
                first_place, second_place, third_place, _, games_count, average_place = self.calculate_stat(
                    three_hanchan_data
                )

                three_people_stat.hanchan_games = games_count
                three_people_stat.hanchan_average_place = average_place
                three_people_stat.hanchan_first_place = first_place
                three_people_stat.hanchan_second_place = second_place
                three_people_stat.hanchan_third_place_place = third_place

            four_people_stat.save()
            three_people_stat.save()

    def calculate_stat(self, data):
        first_place = data[0]['gameFinalPosition'][0]
        second_place = data[0]['gameFinalPosition'][1]
        third_place = data[0]['gameFinalPosition'][2]
        fourth_place = data[0]['gameFinalPosition'][3]

        games_count = first_place + second_place + third_place + fourth_place
        average_place = (first_place + second_place * 2 + third_place * 3 + fourth_place * 4) / games_count

        return first_place, second_place, third_place, fourth_place, games_count, average_place


