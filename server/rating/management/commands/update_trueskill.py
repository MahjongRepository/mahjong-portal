# -*- coding: utf-8 -*-
from datetime import datetime

import ujson
from django.core.management.base import BaseCommand
from django.utils import timezone

from rating.trueskill.utils import update_trueskill


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


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

        rating_date = datetime.strptime(trueskill_date, "%d%m%Y") if trueskill_date else timezone.now().date()
        update_trueskill(trueskill_map=trueskill_map, trueskill_type=trueskill_type, rating_date=rating_date)

        print("{0}: End trueskill rating update".format(get_date_string()))
