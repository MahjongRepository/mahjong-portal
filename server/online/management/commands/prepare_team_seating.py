# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from online.team_seating import TeamSeating


class Command(BaseCommand):
    def handle(self, *args, **options):
        TeamSeating.prepare_team_sortition()
