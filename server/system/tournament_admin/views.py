from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404

from player.models import Player
from system.tournament_admin.forms import UploadResultsForm
from tournament.models import Tournament, TournamentResult


@login_required
@user_passes_test(lambda u: u.is_superuser)
def new_tournaments(request):
    tournaments = Tournament.objects.filter(is_upcoming=True)
    return render(request, 'tournament_admin/new_tournaments.html', {
        'tournaments': tournaments
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def upload_results(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    form = UploadResultsForm()

    not_found_users = []
    file_was_uploaded = False
    success = False

    if request.POST:
        form = UploadResultsForm(request.POST, request.FILES)
        if form.is_valid():
            file_was_uploaded = True

            csv_file = form.cleaned_data['csv_file']
            file_data = csv_file.read().decode("utf-8")

            # csv.DictReader didn't want to work with InMemoryFile
            # so, let's go with a straight way
            lines = file_data.split('\n')
            filtered_results = []
            for line in lines:
                fields = line.split(';')

                # first row
                if fields[0] == 'place':
                    continue

                place = fields[0].strip().lower()
                name = fields[1].strip().lower()
                scores = fields[2].strip().lower()

                temp = name.split(' ')
                first_name = temp[1].title()
                last_name = temp[0].title()

                if first_name == 'Замены':
                    first_name = 'замены'

                filtered_results.append([place, first_name, last_name, scores])

                try:
                    player = Player.all_objects.get(first_name_ru=first_name, last_name_ru=last_name)
                except Player.DoesNotExist:
                    not_found_users.append(
                        '{} {}'.format(last_name, first_name)
                    )

            # everything is fine
            if not not_found_users:
                for result in filtered_results:
                    place = result[0]
                    first_name = result[1]
                    last_name = result[2]
                    scores = result[3]

                    player = Player.all_objects.get(first_name_ru=first_name, last_name_ru=last_name)

                    TournamentResult.objects.create(
                        player=player,
                        tournament=tournament,
                        place=place,
                        scores=scores,
                    )

                tournament.is_upcoming = False
                tournament.save()

                success = True

    return render(request, 'tournament_admin/upload_results.html', {
        'tournament': tournament,
        'form': form,
        'not_found_users': not_found_users,
        'file_was_uploaded': file_was_uploaded,
        'success': success
    })
