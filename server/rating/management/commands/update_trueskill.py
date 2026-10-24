# -*- coding: utf-8 -*-
import ujson
from django.core.management.base import BaseCommand
from django.utils import timezone

from rating.trueskill.utils import update_trueskill


def get_current_time():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("trueskill_file", type=str)

    def handle(self, *args, **options):
        print(f"{get_current_time()}: Start trueskill rating update")

        trueskill_file = options["trueskill_file"]
        with open(trueskill_file, "r") as f:
            trueskill_data = ujson.loads(f.read())

        deltas, errors = update_trueskill(trueskill_data=trueskill_data)

        print(f"{get_current_time()}: End trueskill rating update, created {len(deltas)} records, {len(errors)} errors")
