# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from account.models import PantheonInfoUpdateLog
from player.player_helper import PlayerHelper


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):

    def handle(self, *args, **options):
        print("{0}: Start players update from pantheon feeds".format(get_date_string()))
        feeds = PantheonInfoUpdateLog.objects.filter(is_applied=False)
        feed_count = len(feeds)
        feed_update_index = 1
        for feed in feeds:
            with transaction.atomic():
                try:
                    updates = PlayerHelper.update_player_from_pantheon_feed(feed)
                    feed.is_applied = True
                    feed.save()
                    print("{0}/{1}: player update:{2}".format(feed_update_index, feed_count, updates))
                    feed_update_index = feed_update_index + 1
                except Exception as err:
                    transaction.set_rollback(True)
                    raise err
        print("{0}: Finish players update from pantheon feeds".format(get_date_string()))
