import ms.protocol_pb2 as pb
from google.protobuf.json_format import MessageToDict

from player.mahjong_soul.management.commands.ms_base import MSBaseCommand
from player.mahjong_soul.models import MSAccount, MSAccountStatistic, MSPointsHistory


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

            self.calculate_and_save_places_statistic(
                response, four_people_stat, three_people_stat
            )

            four_people_stat.save()
            three_people_stat.save()

            self.calculate_and_save_points_diff(four_people_stat)
            self.calculate_and_save_points_diff(three_people_stat)

    def calculate_and_save_points_diff(self, stat_object):
        latest_history = MSPointsHistory.objects.filter(stat_object=stat_object).order_by('-created_on').first()
        if not latest_history:
            MSPointsHistory.objects.create(
                rank_index=0,
                stat_object=stat_object,
                rank=stat_object.rank,
                points=stat_object.points,
            )
            return

        # user stat wasn't changed from latest update
        if latest_history.rank == stat_object.rank and latest_history.points == stat_object.points:
            return

        # only points were changed
        if latest_history.rank == stat_object.rank:
            MSPointsHistory.objects.create(
                rank_index=latest_history.rank_index,
                stat_object=stat_object,
                rank=stat_object.rank,
                points=stat_object.points,
            )
            return

        # points and rank were changed
        MSPointsHistory.objects.create(
            rank_index=latest_history.rank_index + 1,
            stat_object=stat_object,
            rank=stat_object.rank,
            points=stat_object.points,
        )

    def calculate_and_save_places_statistic(self, response, four_people_stat, three_people_stat):
        four_tonpusen_type = 1
        four_hanchan_type = 2
        three_tonpusen_type = 11
        three_hanchan_type = 12
        games_statistics = response['detailData']['rankStatistic']['totalStatistic']['allLevelStatistic']['gameMode']

        four_tonpusen_data = [x for x in games_statistics if x['mode'] == four_tonpusen_type]
        if four_tonpusen_data:
            result = self.calculate_places_from_raw_data(four_tonpusen_data)
            first_place, second_place, third_place, fourth_place, games_count, average_place = result

            four_people_stat.tonpusen_games = games_count
            four_people_stat.tonpusen_average_place = average_place
            four_people_stat.tonpusen_first_place = first_place
            four_people_stat.tonpusen_second_place = second_place
            four_people_stat.tonpusen_third_place = third_place
            four_people_stat.tonpusen_fourth_place = fourth_place

        four_hanchan_data = [x for x in games_statistics if x['mode'] == four_hanchan_type]
        if four_hanchan_data:
            result = self.calculate_places_from_raw_data(four_hanchan_data)
            first_place, second_place, third_place, fourth_place, games_count, average_place = result

            four_people_stat.hanchan_games = games_count
            four_people_stat.hanchan_average_place = average_place
            four_people_stat.hanchan_first_place = first_place
            four_people_stat.hanchan_second_place = second_place
            four_people_stat.hanchan_third_place = third_place
            four_people_stat.hanchan_fourth_place = fourth_place

        three_tonpusen_data = [x for x in games_statistics if x['mode'] == three_tonpusen_type]
        if three_tonpusen_data:
            first_place, second_place, third_place, _, games_count, average_place = self.calculate_places_from_raw_data(
                three_tonpusen_data
            )

            three_people_stat.tonpusen_games = games_count
            three_people_stat.tonpusen_average_place = average_place
            three_people_stat.tonpusen_first_place = first_place
            three_people_stat.tonpusen_second_place = second_place
            three_people_stat.tonpusen_third_place = third_place

        three_hanchan_data = [x for x in games_statistics if x['mode'] == three_hanchan_type]
        if three_hanchan_data:
            first_place, second_place, third_place, _, games_count, average_place = self.calculate_places_from_raw_data(
                three_hanchan_data
            )

            three_people_stat.hanchan_games = games_count
            three_people_stat.hanchan_average_place = average_place
            three_people_stat.hanchan_first_place = first_place
            three_people_stat.hanchan_second_place = second_place
            three_people_stat.hanchan_third_place = third_place

    def calculate_places_from_raw_data(self, data):
        first_place = data[0]['gameFinalPosition'][0]
        second_place = data[0]['gameFinalPosition'][1]
        third_place = data[0]['gameFinalPosition'][2]
        fourth_place = data[0]['gameFinalPosition'][3]

        games_count = first_place + second_place + third_place + fourth_place
        average_place = (first_place + second_place * 2 + third_place * 3 + fourth_place * 4) / games_count

        return first_place, second_place, third_place, fourth_place, games_count, average_place
