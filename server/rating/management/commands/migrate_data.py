import datetime

from django.core.management.base import BaseCommand

from player.models import PlayerERMC, PlayerQuotaEvent, PlayerWRC
from rating.models import Rating, RatingResult


class Command(BaseCommand):
    def handle(self, *args, **options):
        PlayerQuotaEvent.objects.all().delete()
        rating = Rating.objects.get(type=Rating.RR)

        rating_date = datetime.date(2019, 1, 1)
        rating_results = (
            RatingResult.objects.filter(rating=rating)
            .filter(date=rating_date)
            .prefetch_related("player")
            .prefetch_related("player__city")
            .prefetch_related("player__ermc")
            .order_by("place")
        )[:100]

        for x in rating_results:
            try:
                ermc = x.player.ermc
            except PlayerERMC.DoesNotExist:
                ermc = None

            state = PlayerQuotaEvent.NEW
            federation_member = None
            if ermc:
                state = ermc.state
                federation_member = ermc.federation_member
            PlayerQuotaEvent.objects.create(
                player=x.player,
                place=x.place,
                score=x.score,
                state=state,
                federation_member=federation_member,
                type=PlayerQuotaEvent.ERMC_2019,
            )

        rating_date = datetime.date(2020, 2, 1)
        rating_results = (
            RatingResult.objects.filter(rating=rating)
            .filter(date=rating_date)
            .prefetch_related("player")
            .prefetch_related("player__city")
            .prefetch_related("player__ermc")
            .order_by("place")
        )[:100]

        for x in rating_results:
            try:
                wrc = x.player.wrc
            except PlayerWRC.DoesNotExist:
                wrc = None

            state = PlayerQuotaEvent.NEW
            federation_member = None
            if wrc:
                state = wrc.state
                federation_member = wrc.federation_member
            PlayerQuotaEvent.objects.create(
                player=x.player,
                place=x.place,
                score=x.score,
                state=state,
                federation_member=federation_member,
                type=PlayerQuotaEvent.WRC_2020,
            )
