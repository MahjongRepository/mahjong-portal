# -*- coding: utf-8 -*-
import argparse
import dataclasses
from collections import defaultdict
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db.models import Q

from tournament.models import Tournament, TournamentResult
from utils.new_pantheon import get_rating_table


@dataclasses.dataclass
class ParsedRatingTableRecord:
    player_pantheon_id: int
    player_name: str
    place: int
    score: float


def fix_shared_places(parsed_records: list[ParsedRatingTableRecord]):
    prev_place = 0
    prev_score = None
    for record in parsed_records:
        if record.score == prev_score:
            record.place = prev_place
        else:
            prev_place = record.place
            prev_score = record.score


def parse_old_pantheon_ids(old_pantheon_id: int) -> List[ParsedRatingTableRecord]:
    print(f"Old pantheon id: {old_pantheon_id}")

    response = requests.get(f"https://mahjongpantheon.github.io/pantheon-v1-archive/eid{old_pantheon_id}/stat.html")
    if response.status_code != 200:
        print(f"Http request returned status code {response.status_code}, message: {response.text}")
        return []

    bs = BeautifulSoup(response.text, features="html.parser")
    tables = bs.find_all("table")
    if len(tables) != 1:
        print("Can't parse HTML: len(tables) != 1")
        return []

    parsed_records: List[ParsedRatingTableRecord] = []
    tr_list = tables[0].find_all("tr")
    player_link_column = None
    score_column = None
    for row_index, tr in enumerate(tr_list):
        if row_index == 0:
            th_list = tr.find_all("th")
            for column_index, th in enumerate(th_list):
                th_text = th.text
                if "Игрок" in th_text:
                    player_link_column = column_index
                elif "Рейтинговые очки" in th_text:
                    score_column = column_index
        else:
            assert player_link_column is not None
            assert score_column is not None
            td_list = tr.find_all("td")

            player_column_value = str(td_list[player_link_column])
            i1 = player_column_value.find('<a href="user/')
            if i1 == -1:
                print("Can't parse HTML: i1 == -1")
                return []
            i2 = player_column_value.find('.html">', i1)
            if i2 == -1:
                print("Can't parse HTML: i2 == -1")
                return []
            player_id = int(player_column_value[i1 + len('<a href="user/') : i2])
            i3 = player_column_value.find("</a>", i2)
            if i3 == -1:
                print("Can't parse HTML: i3 == -1")
                return []
            player_name = str(player_column_value[i2 + len('.html">') : i3])

            score = float(td_list[score_column].text)

            parsed_records.append(
                ParsedRatingTableRecord(
                    player_pantheon_id=player_id,
                    player_name=player_name,
                    place=row_index,
                    score=score,
                )
            )

    return parsed_records


def parse_new_pantheon_ids(new_pantheon_id: int) -> List[ParsedRatingTableRecord]:
    print(f"New pantheon id: {new_pantheon_id}")

    rating_table = list(get_rating_table(eventId=new_pantheon_id).list)  # list[atoms_pb2.PlayerInRating]
    print(f"Got {len(rating_table)} records from Pantheon api")
    parsed_records: List[ParsedRatingTableRecord] = []
    for i, player in enumerate(rating_table):
        parsed_records.append(
            ParsedRatingTableRecord(
                player_pantheon_id=player.id,
                player_name=player.title,
                place=i + 1,
                score=player.rating,
            )
        )

    return parsed_records


def filter_null_scores(tournament_results: List[TournamentResult]) -> List[TournamentResult]:
    results_with_not_null_scores = []
    null_score_count = 0
    for tournament_result in tournament_results:
        if tournament_result.scores is None:
            print(
                f"Place {tournament_result.place} has null score, can't process it "
                f"(portal name {tournament_result.player.full_name if tournament_result.player else None}) "
                f"(portal player_string {tournament_result.player_string})"
            )
            null_score_count += 1
            continue
        results_with_not_null_scores.append(tournament_result)

    print(f"Null scores: {null_score_count}")
    return results_with_not_null_scores


def update_db(tournament: Tournament, clean_old: bool, update: bool, parsed_records: List[ParsedRatingTableRecord]):
    tournament_results_all = list(TournamentResult.objects.filter(tournament=tournament).prefetch_related("player"))
    print(f"Found {len(tournament_results_all)} tournament results in DB")

    if clean_old:
        print("Option --clean-old enabled, delete all old player pantheon ids")
        for tournament_result in tournament_results_all:
            tournament_result.player_pantheon_id = None
        TournamentResult.objects.bulk_update(tournament_results_all, fields=["player_pantheon_id"])
        print(f"Deleted all old player pantheon ids from {len(tournament_results_all)} objects in DB")

    tournament_results_to_process = filter_null_scores(tournament_results=tournament_results_all)
    print(f"Results to process: {len(tournament_results_to_process)}, parsed records: {len(parsed_records)}")

    tournament_results_by_score: Dict[float, list[TournamentResult]] = defaultdict(list)
    parsed_records_by_score: Dict[float, list[ParsedRatingTableRecord]] = defaultdict(list)
    # DB stores scores in Decimal, round keys to prevent precision errors
    for tournament_result in tournament_results_to_process:
        tournament_results_by_score[round(float(tournament_result.scores), ndigits=2)].append(tournament_result)
    for parsed_record in parsed_records:
        parsed_records_by_score[round(parsed_record.score, ndigits=2)].append(parsed_record)
    unique_scores = sorted(set(tournament_results_by_score.keys()) | set(parsed_records_by_score.keys()), reverse=True)
    print(
        f"Found {len(unique_scores)} unique scores total, "
        f"{len(tournament_results_by_score)} in portal results, "
        f"{len(parsed_records_by_score)} in parsed records"
    )

    objects_to_update: List[TournamentResult] = []
    null_player_count = 0
    already_set_count = 0
    manual_count = 0
    for score in unique_scores:
        tournament_results_for_score: List[TournamentResult] = tournament_results_by_score[score]
        parsed_records_for_score: List[ParsedRatingTableRecord] = parsed_records_by_score[score]

        if len(tournament_results_for_score) == len(parsed_records_for_score) == 1:
            tournament_result = tournament_results_for_score[0]
            parsed_record = parsed_records_for_score[0]

            if tournament_result.player is None:
                print(
                    f"Place {tournament_result.place} (score {score}) "
                    f"has null player, can't process it (portal player_string {tournament_result.player_string})"
                )
                null_player_count += 1
                continue

            if tournament_result.player_pantheon_id is not None:
                print(
                    f"Place {tournament_result.place} (score {score}) "
                    f"(portal name {tournament_result.player.full_name}) "
                    f"already has player pantheon id {tournament_result.player_pantheon_id}"
                )
                already_set_count += 1
                continue

            player_pantheon_id = parsed_record.player_pantheon_id
            print(
                f"Processing place {tournament_result.place} (score {score}) "
                f"(portal name {tournament_result.player.full_name}), "
                f"will set player pantheon id to {player_pantheon_id} (parsed name {parsed_record.player_name})"
            )
            tournament_result.player_pantheon_id = player_pantheon_id
            objects_to_update.append(tournament_result)
        else:
            equal_sizes: bool = len(tournament_results_for_score) == len(parsed_records_for_score)
            print(
                f"{'Unsupported' if equal_sizes else 'Wrong'} number of players for score {score}. "
                f"Portal has {len(tournament_results_for_score)} tournament results. "
                f"Pantheon has {len(parsed_records_for_score)} parsed records"
            )
            if len(tournament_results_for_score) > 0:
                print(f"  Portal tournament results for score {score}:")
                for tournament_result in tournament_results_for_score:
                    if tournament_result.player_pantheon_id is not None:
                        already_set_count += 1
                    else:
                        manual_count += 1
                    print(
                        f"    Place {tournament_result.place}, "
                        f"portal name {tournament_result.player.full_name if tournament_result.player else None}, "
                        f"portal player_string {tournament_result.player_string}, "
                        f"portal pantheon id {tournament_result.player_pantheon_id}"
                    )
            if len(parsed_records_for_score) > 0:
                print(f"  Pantheon parsed records for score {score}:")
                for parsed_record in parsed_records_for_score:
                    print(
                        f"    Place {parsed_record.place}, "
                        f"name {parsed_record.player_name}, "
                        f"pantheon id {parsed_record.player_pantheon_id}"
                    )

    print(
        f"To update: {len(objects_to_update)}, null players: {null_player_count}, "
        f"already set: {already_set_count}, manual: {manual_count}"
    )

    if update:
        TournamentResult.objects.bulk_update(objects_to_update, fields=["player_pantheon_id"])
        print(f"Updated {len(objects_to_update)} objects in DB")


def load_tournaments(slug: Optional[str], year: Optional[int]) -> List[Tournament]:
    if slug is None and year is None:
        print("No slug or year provided, returning empty list from load_tournaments()")
        return []

    if slug is not None and year is not None:
        print("Both slug and year provided, returning empty list from load_tournaments()")
        return []

    qs = Tournament.objects.filter(Q(old_pantheon_id__isnull=False) | Q(new_pantheon_id__isnull=False), is_hidden=False)
    if slug is not None:
        qs = qs.filter(slug=slug)
    else:
        qs = qs.filter(end_date__year=year)
    return list(qs.order_by("end_date"))


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str)
        parser.add_argument("--year", type=int)
        parser.add_argument("--clean-old", default=False, action=argparse.BooleanOptionalAction)
        parser.add_argument("--update", default=False, action=argparse.BooleanOptionalAction)

    def handle(self, *args, **options):
        # parsed_records = parse_new_pantheon_ids(new_pantheon_id=888)
        # parsed_records = parse_old_pantheon_ids(old_pantheon_id=349)
        # return

        year = options.get("year")
        slug = options.get("slug")
        clean_old: bool = options.get("clean_old", False)
        update: bool = options.get("update", False)
        print(f"Slug: {slug}, year: {year}, clean_old: {clean_old}, update: {update}")

        tournaments: List[Tournament] = load_tournaments(slug=slug, year=year)
        if not tournaments:
            print("No tournaments found, exit command")
            return

        print(f"Found {len(tournaments)} tournaments:")
        for i, tournament in enumerate(tournaments):
            print(f"{i + 1}: {tournament.slug} | {tournament.name}")

        print("Start adding pantheon ids to tournament results")

        for tournament in tournaments:
            print("============================================================")
            print(f"Start processing tournament {tournament.slug}")
            if tournament.old_pantheon_id:
                parsed_records = parse_old_pantheon_ids(old_pantheon_id=tournament.old_pantheon_id)
            elif tournament.new_pantheon_id:
                parsed_records = parse_new_pantheon_ids(new_pantheon_id=tournament.new_pantheon_id)
            else:
                print("This tournament doesn't have pantheon id linked (what?), skip")
                continue

            fix_shared_places(parsed_records=parsed_records)
            update_db(tournament=tournament, clean_old=clean_old, update=update, parsed_records=parsed_records)
            print(f"Finished processing tournament {tournament.slug}")

        print("End of command")
