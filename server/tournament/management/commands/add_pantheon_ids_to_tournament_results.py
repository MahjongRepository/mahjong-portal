# -*- coding: utf-8 -*-
import argparse
import dataclasses
import json
from collections import defaultdict
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db.models import Q

from tournament.models import Tournament, TournamentResult


@dataclasses.dataclass
class ParsedRatingTableRecord:
    player_pantheon_id: int
    player_name: str
    place: int
    score: float


def fix_shared_places(parsed_records: list[ParsedRatingTableRecord]) -> Dict[int, List[ParsedRatingTableRecord]]:
    prev_place = 0
    prev_score = None
    for record in parsed_records:
        if record.score == prev_score:
            record.place = prev_place
        else:
            prev_place = record.place
            prev_score = record.score

    place_to_ids: Dict[int, List[ParsedRatingTableRecord]] = defaultdict(list)
    for record in parsed_records:
        place_to_ids[record.place].append(record)

    print("Parsed records with fixed shared places:")
    for place in sorted(place_to_ids.keys()):
        print(f"Place: {place}, ids and names: {place_to_ids[place]}")

    return place_to_ids


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

    response = requests.get(f"https://rating.riichimahjong.org/event/{new_pantheon_id}/order/rating")
    if response.status_code != 200:
        print(f"Http request returned status code {response.status_code}, message: {response.text}")
        return []

    text = response.text
    start_index = text.find("<script>window.initialData = ")
    if start_index == -1:
        print("Can't parse HTML: start_index == -1")
        return []
    end_index = text.find(";</script>", start_index)
    if end_index == -1:
        print("Can't parse HTML: end_index == -1")
        return []

    initial_data_str = text[start_index + len("<script>window.initialData = ") : end_index]
    initial_data = json.loads(initial_data_str)
    rating_table = None
    for key, value in initial_data.items():
        if "RatingTable" in key and str(new_pantheon_id) in key:
            rating_table = value
            break
    if rating_table is None:
        print("Rating table not found in HTML")
        return []

    rating_table: List
    print(f"Found {len(rating_table)} records in HTML")
    parsed_records: List[ParsedRatingTableRecord] = []
    for i, record in enumerate(rating_table):
        parsed_records.append(
            ParsedRatingTableRecord(
                player_pantheon_id=record["id"],
                player_name=record["title"],
                place=i + 1,
                score=record["rating"],
            )
        )

    return parsed_records


def update_db(tournament: Tournament, dry_run: bool, place_to_ids: Dict[int, List[ParsedRatingTableRecord]]):
    tournament_results = list(TournamentResult.objects.filter(tournament=tournament))
    print(f"Found {len(tournament_results)} tournament results in DB")
    objects_to_update: List[TournamentResult] = []
    already_set_count = 0
    manual_count = 0
    for tournament_result in tournament_results:
        if tournament_result.player_pantheon_id is not None:
            print(
                f"Place {tournament_result.place} already has player pantheon id {tournament_result.player_pantheon_id}"
            )
            already_set_count += 1
            continue
        updates = place_to_ids[tournament_result.place]
        if len(updates) == 1:
            player_pantheon_id = updates[0].player_pantheon_id
            print(f"Processing place {tournament_result.place}, will set player pantheon id to {player_pantheon_id}")
            tournament_result.player_pantheon_id = player_pantheon_id
            objects_to_update.append(tournament_result)
        else:
            print(f"There are {len(updates)} players sharing place {tournament_result.place}, update them manually")
            manual_count += len(updates)

    print(f"To update: {len(objects_to_update)}, already set: {already_set_count}, manual: {manual_count}")

    if not dry_run:
        TournamentResult.objects.bulk_update(objects_to_update, fields=["player_pantheon_id"])
        print(f"Updated {len(objects_to_update)} objects in DB")


def load_tournaments(slug: Optional[str], year: Optional[int]) -> List[Tournament]:
    if slug is None and year is None:
        print("No slug or year provided, returning empty list from load_tournaments()")
        return []

    if slug is not None and year is not None:
        print("Both slug and year provided, returning empty list from load_tournaments()")
        return []

    qs = Tournament.objects.filter(Q(old_pantheon_id__isnull=False) | Q(new_pantheon_id__isnull=False))
    if slug is not None:
        qs = qs.filter(slug=slug)
    else:
        qs = qs.filter(end_date__year=year)
    return list(qs.order_by("end_date"))


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--slug", type=str)
        parser.add_argument("--year", type=int)
        parser.add_argument("--dry-run", default=False, action=argparse.BooleanOptionalAction)

    def handle(self, *args, **options):
        # parsed_records = parse_new_pantheon_ids(new_pantheon_id=888)
        # parsed_records = parse_old_pantheon_ids(old_pantheon_id=349)
        # place_to_ids = fix_shared_places(parsed_records=parsed_records)
        # return

        year = options.get("year")
        slug = options.get("slug")
        dry_run: bool = options.get("dry_run", False)
        print(f"Slug: {slug}, year: {year}, dry_run: {dry_run}")

        tournaments: list[Tournament] = load_tournaments(slug=slug, year=year)
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

            place_to_ids = fix_shared_places(parsed_records=parsed_records)
            update_db(tournament=tournament, dry_run=dry_run, place_to_ids=place_to_ids)
            print(f"Finished processing tournament {tournament.slug}")

        print("End of command")
