
from django.core.management.base import BaseCommand
from django.utils import timezone

from player.tenhou.models import TenhouNickname


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        tenhou_objects = TenhouNickname.objects.all()
        now = timezone.now().date()
        for tenhou_object in tenhou_objects:
            delta = now - tenhou_object.last_played_date
            if delta.days > 181:
                print('{} days {}'.format(tenhou_object.tenhou_username, delta.days))

                tenhou_object.is_active = False
                tenhou_object.save()

                # we disabled main account for the player
                # maybe there is another account to be main one
                if tenhou_object.is_main:
                    other_objects = TenhouNickname.objects.filter(
                        player=tenhou_object.player,
                        is_active=True
                    ).first()

                    if other_objects:
                        other_objects.is_main = True
                        other_objects.save()

        print('{0}: End'.format(get_date_string()))
