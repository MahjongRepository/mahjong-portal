# -*- coding: utf-8 -*-

from time import sleep

from django.core.management.base import BaseCommand
from django.utils import timezone

from player.tenhou.models import TenhouNickname
from utils.tenhou.helper import download_all_games_from_nodochi


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("{0}: Start".format(get_date_string()))

        tenhou_objects = TenhouNickname.active_objects
        now = timezone.now().date()
        for tenhou_object in tenhou_objects:
            delta = now - tenhou_object.last_played_date
            # let's check account deactivation in advance
            if delta.days >= 140:
                print()
                print(f"{tenhou_object.tenhou_username} didn't play ranking games in {delta.days} days.")
                print("Checking not ranking games...")

                player_games, _, _ = download_all_games_from_nodochi(
                    tenhou_object.tenhou_username, only_ranking_games=False
                )
                latest_game = player_games[-1]

                delta = now - latest_game["game_date"].date()
                # player didn't play ranking and custom lobby games
                # it means that account was deleted
                if delta.days >= 181:
                    print("Deactivating account...")
                    tenhou_object.is_active = False
                    tenhou_object.save()

                    # we disabled main account for the player
                    # maybe there is another account to be main one
                    if tenhou_object.is_main:
                        other_objects = TenhouNickname.active_objects.filter(player=tenhou_object.player).first()

                        if other_objects:
                            other_objects.is_main = True
                            other_objects.save()
                else:
                    print("Found some custom lobby games, account is active")
                    tenhou_object.last_played_date = latest_game["game_date"]
                    tenhou_object.save()

                # let's be gentle and don't ddos nodochi
                sleep(10)

        print("{0}: End".format(get_date_string()))
