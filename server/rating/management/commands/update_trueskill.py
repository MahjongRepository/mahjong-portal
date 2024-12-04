# -*- coding: utf-8 -*-
import ujson
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from player.models import Player
from rating.models import ExternalRating, ExternalRatingDate, ExternalRatingDelta, ExternalRatingTournament
from tournament.models import Tournament


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("trueskill_file", type=str)

    def handle(self, *args, **options):
        print("{0}: Start trueskill rating update".format(get_date_string()))

        trueskill_file = options["trueskill_file"]
        with open(trueskill_file, "r") as f:
            trueskill_map = ujson.loads(f.read())

        try:
            with transaction.atomic():
                now = timezone.now().date()
                rating = ExternalRating.objects.get_or_create(
                    name="Trueskill",
                    name_en="Trueskill rating (beta version)",
                    name_ru="Trueskill рейтинг (бета версия)",
                    slug="trueskill",
                    description="Trueskill rating",
                    description_en="Trueskill rating system for players developed by "
                    "Microsoft Research. Link for more information https://trueskill.org/",
                    description_ru="Trueskill рейтинг, разработанный Microsoft Research. "
                    "Ссылка на подробное описание https://trueskill.org/",
                )[0]
                print("Erasing dates...")
                ExternalRatingDelta.objects.filter(rating=rating, date=now).delete()
                ExternalRatingDate.objects.filter(rating=rating, date=now).delete()
                ExternalRatingTournament.objects.filter(rating=rating).delete()

                deltas = []
                sorted_rating = sorted(trueskill_map["trueskill"], key=lambda d: d["rating"], reverse=True)
                place = 1
                for ts_player in sorted_rating:
                    try:
                        full_name = ts_player["player"].split(" ")
                        if len(full_name) == 2:
                            player = Player.objects.get(
                                first_name_ru=full_name[1], last_name_ru=full_name[0], is_exclude_from_rating=False
                            )
                            deltas.append(
                                ExternalRatingDelta(
                                    rating=rating,
                                    player=player,
                                    date=now,
                                    base_rank=ts_player["rating"],
                                    is_active=True,
                                    place=place,
                                )
                            )
                            place = place + 1
                    except (Player.DoesNotExist, Player.MultipleObjectsReturned):
                        pass

                if deltas:
                    ExternalRatingDelta.objects.bulk_create(deltas)
                print("Trueskill players updated!")

                tournaments = []
                for tournament_id in trueskill_map["tournament_ids"]:
                    try:
                        tournament = Tournament.objects.get(
                            Q(old_pantheon_id=tournament_id) | Q(new_pantheon_id=tournament_id)
                        )
                        tournaments.append(ExternalRatingTournament(rating=rating, tournament=tournament))

                    except (Tournament.DoesNotExist, Tournament.MultipleObjectsReturned):
                        pass
                if tournaments:
                    ExternalRatingTournament.objects.bulk_create(tournaments)
                print("Trueskill tournaments updated!")

                ExternalRatingDate.objects.create(rating=rating, date=now)

        except Exception as e:
            print(e)

        print("{0}: End trueskill rating update".format(get_date_string()))
