import csv

from django.core.management.base import BaseCommand
from django.utils import timezone

from player.models import Player
from settings.models import City, Country


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def handle(self, *args, **options):
        file = 'players.csv'

        reader = csv.DictReader(open(file, 'r'))

        country = Country.objects.get(name_en='Russia')

        for row in reader:
            if row.get('id'):
                id = row['id']
                last_name_ru = row['last_name_ru']
                first_name_ru = row['first_name_ru']
                last_name_en = row['last_name_en']
                first_name_en = row['first_name_en']
                ema_id = row['ema']

                player = Player.objects.get(id=id)
                player.last_name_ru = last_name_ru
                player.first_name_ru = first_name_ru
                player.last_name_en = last_name_en
                player.first_name_en = first_name_en
                player.ema_id = ema_id
                player.slug = '{}-{}'.format(last_name_en.lower(), first_name_en.lower())
                player.save()
            else:
                city = row.get('city')
                city = City.objects.get(name_ru=city)

                last_name_ru = row['last_name_ru']
                first_name_ru = row['first_name_ru']
                last_name_en = row['last_name_en']
                first_name_en = row['first_name_en']
                ema_id = row['ema']

                slug = '{}-{}'.format(last_name_en.lower(), first_name_en.lower())

                Player.objects.create(
                    last_name_ru=last_name_ru,
                    first_name_ru=first_name_ru,
                    last_name_en=last_name_en,
                    first_name_en=first_name_en,
                    ema_id=ema_id,
                    city=city,
                    country=country,
                    slug=slug
                )
