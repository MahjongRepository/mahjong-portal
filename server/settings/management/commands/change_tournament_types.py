from django.core.management.base import BaseCommand
from django.utils import timezone

from tournament.models import Tournament


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        tournaments = Tournament.objects.all()
        for tournament in tournaments:
            tournament.tournament_type_new = tournament.tournament_type.slug
            tournament.save()

        print('{0}: End'.format(get_date_string()))
