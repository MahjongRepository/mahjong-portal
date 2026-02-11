# -*- coding: utf-8 -*-
from datetime import datetime

import ujson
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from player.player_helper import PlayerHelper
from rating.models import ExternalRating, ExternalRatingDate, ExternalRatingDelta, ExternalRatingTournament
from tournament.models import Tournament
from website.views import NEW_PANTHEON_TYPE, OLD_PANTHEON_TYPE


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


def get_tournament(pantheon_type, tournament_id):
    try:
        if NEW_PANTHEON_TYPE == pantheon_type:
            return Tournament.objects.get(new_pantheon_id=str(tournament_id))
        if OLD_PANTHEON_TYPE == pantheon_type:
            return Tournament.objects.get(old_pantheon_id=str(tournament_id))
    except Tournament.DoesNotExist as e:
        print(f"Tournament [type={pantheon_type} id={tournament_id}] not found")
        raise e
    except Tournament.MultipleObjectsReturned as e:
        print(f"found not unique Tournament [type={pantheon_type} id={tournament_id}]")
        raise e


def get_rating_by_type(type):
    if ExternalRating.TYPES[ExternalRating.TRUESKILL][1] == type.upper():
        return ExternalRating.objects.get_or_create(
            name="Trueskill",
            name_en="Trueskill rating (beta version)",
            name_ru="Trueskill рейтинг (бета версия)",
            slug="trueskill",
            description="Trueskill rating",
            description_en="Trueskill rating system for players developed by "
            "Microsoft Research. Link for more information https://trueskill.org/",
            description_ru="Trueskill рейтинг, разработанный Microsoft Research. "
            "Ссылка на подробное описание https://trueskill.org/",
            type=ExternalRating.TRUESKILL,
            order=0,
        )[0]
    if ExternalRating.TYPES[ExternalRating.ONLINE_TRUESKILL][1] == type.upper():
        return ExternalRating.objects.get_or_create(
            name="Online Trueskill",
            name_en="Online Trueskill rating (beta version)",
            name_ru="Online Trueskill рейтинг (бета версия)",
            slug="online-trueskill",
            description="Online Trueskill rating",
            description_en="Trueskill online rating system for players developed by "
            "Microsoft Research. Link for more information https://trueskill.org/",
            description_ru="Trueskill рейтинг, разработанный Microsoft Research. "
            "Ссылка на подробное описание https://trueskill.org/",
            type=ExternalRating.ONLINE_TRUESKILL,
            order=1,
        )[0]
    raise AssertionError("Passed type not allowed!")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("trueskill_file", type=str)
        parser.add_argument("type", type=str)
        parser.add_argument("--date", default=None, type=str)

    def handle(self, *args, **options):
        print("{0}: Start trueskill rating update".format(get_date_string()))

        trueskill_file = options["trueskill_file"]
        trueskill_type = options["type"]
        trueskill_date = options["date"]
        with open(trueskill_file, "r") as f:
            trueskill_map = ujson.loads(f.read())

        try:
            with transaction.atomic():
                rating_date = datetime.strptime(trueskill_date, "%d%m%Y") if trueskill_date else timezone.now().date()
                rating_date_str = rating_date.strftime("%d-%m-%Y")
                rating = get_rating_by_type(trueskill_type)
                print(f"Erasing dates {rating_date_str}...")
                ExternalRatingDelta.objects.filter(rating=rating, date=rating_date).delete()
                ExternalRatingDate.objects.filter(rating=rating, date=rating_date).delete()
                ExternalRatingTournament.objects.filter(rating=rating).delete()

                deltas = []
                sorted_rating = sorted(trueskill_map["trueskill"], key=lambda d: d["rating"], reverse=True)
                place = 1
                for ts_player in sorted_rating:
                    player_full_name = ts_player["player"]
                    player = PlayerHelper.find_player_smart(player_full_name=player_full_name)
                    if player:
                        deltas.append(
                            ExternalRatingDelta(
                                rating=rating,
                                player=player,
                                date=rating_date,
                                base_rank=ts_player["rating"],
                                is_active=True,
                                place=place,
                                game_numbers=ts_player["game_count"],
                                last_game_date=ts_player["last_game_date"],
                            )
                        )
                        place = place + 1
                    else:
                        if "old_ids" in ts_player and "new_ids" in ts_player:
                            print(
                                "find_player_smart(): found 0 players with name '{0}', old_ids={1}, new_ids={2}".format(
                                    player_full_name, ts_player["old_ids"], ts_player["new_ids"]
                                )
                            )
                        elif "old_ids" in ts_player:
                            print(
                                "find_player_smart(): found 0 players with name '{0}', old_ids={1}".format(
                                    player_full_name, ts_player["old_ids"]
                                )
                            )
                        else:
                            print("find_player_smart(): found 0 players with name '{0}'".format(player_full_name))

                if deltas:
                    ExternalRatingDelta.objects.bulk_create(deltas)
                print(f"Trueskill players updated on date {rating_date_str}!")

                tournaments = []
                ts_tournaments_count = len(trueskill_map["tournament_ids"])
                tournaments_count = 0
                for tournament_id_map in trueskill_map["tournament_ids"]:
                    try:
                        tournament_id = tournament_id_map["pantheon_id"]
                        tournament_pantheon_type = tournament_id_map["pantheon_type"]
                        tournament = get_tournament(tournament_pantheon_type, tournament_id)
                        tournaments.append(ExternalRatingTournament(rating=rating, tournament=tournament))
                        tournaments_count += 1
                    except (Tournament.DoesNotExist, Tournament.MultipleObjectsReturned) as e:
                        raise e

                if tournaments_count != ts_tournaments_count:
                    raise AssertionError("Not all tournaments found!")

                if tournaments:
                    ExternalRatingTournament.objects.bulk_create(tournaments)
                print(f"Trueskill tournaments updated on date {rating_date_str}!")

                ExternalRatingDate.objects.create(rating=rating, date=rating_date)

        except Exception as e:
            print(e)
            raise e

        print("{0}: End trueskill rating update".format(get_date_string()))
