# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.utils import timezone

from utils.new_pantheon import get_rating_table
from yagi_keiji_cup.models import YagiKeijiCupSettings


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):

    def handle(self, *args, **options):
        print("{0}: Start update Yagi Kaiji Cup results".format(get_date_string()))

        yagi_settings = None
        try:
            yagi_settings = YagiKeijiCupSettings.objects.get(is_main=True)
        except YagiKeijiCupSettings.DoesNotExist:
            yagi_settings = None

        if yagi_settings:
            tenhou_pantheon_tournament_id = yagi_settings.tenhou_tournament.new_pantheon_id
            majsoul_pantheon_tournament_id = yagi_settings.majsoul_tournament.new_pantheon_id

            #todo: prefetch player <-> team_name mapping

            tenhou_results = get_rating_table(tenhou_pantheon_tournament_id)

            #todo: wait fix from pantheon team
            #majsoul_results = get_rating_table(majsoul_pantheon_tournament_id)

            #todo: postsorting by player rating and place
            #todo: sorting by team scores

        print("{0}: Finish update Yagi Kaiji Cup results".format(get_date_string()))
