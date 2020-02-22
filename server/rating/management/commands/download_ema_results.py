import csv

import requests
from bs4 import BeautifulSoup
from django.core.management import BaseCommand
from django.utils import timezone


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("tournament_id", type=str)

    def handle(self, *args, **options):
        print("{0}: Start".format(get_date_string()))

        file_name = "data.csv"
        writer = csv.writer(open(file_name, "w+"))
        writer.writerow(["place", "first_name", "last_name", "scores", "load_player"])

        tournament_id = options.get("tournament_id")

        url = "http://mahjong-europe.org/ranking/Tournament/TR_RCR_{}.html".format(tournament_id)
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        table = soup.findAll("div", {"class": "TCTT_lignes"})[0]
        # skip first row because it is a header
        results = table.findAll("div")[1:]
        for result in results:
            data = result.findAll("p")

            place = data[0].text.strip()
            last_name = data[2].text.strip().title()
            first_name = data[3].text.strip().title()
            scores = data[6].text.strip().title()

            if scores == "1" or scores == "N/A" or scores == "0":
                scores = ""

            writer.writerow([place, first_name, last_name, scores, ""])

        print("{0}: End".format(get_date_string()))
