from django.db.models import Q

from player.models import Player
from tournament.models import Tournament, TournamentResult


def _add_to_map(mp: dict[tuple[str, int], TournamentResult], key: tuple[str, int], tournament_result: TournamentResult):
    existing_result = mp.get(key)
    if existing_result is None:
        mp[key] = tournament_result
        return

    # validate that there is only one player in tournament results for each pantheon id
    existing_player: Player = existing_result.player
    player: Player = tournament_result.player
    if existing_player.id != player.id:
        raise Exception(
            f"Tournament results have different players for pantheon (type, id) {key}: "
            f"({existing_player.id, existing_player.slug, existing_player.full_name}) and "
            f"({player.id, player.slug, player.full_name})"
        )

    # last tournament by date
    existing_tournament: Tournament = existing_result.tournament
    tournament: Tournament = tournament_result.tournament
    if existing_tournament.end_date < tournament.end_date:
        mp[key] = tournament_result


def load_last_player_pantheon_results() -> dict[tuple[str, int], TournamentResult]:
    qs = TournamentResult.objects.select_related("tournament", "player").filter(
        Q(tournament__old_pantheon_id__isnull=False) | Q(tournament__new_pantheon_id__isnull=False),
        tournament__is_hidden=False,
    )
    result: dict[tuple[str, int], TournamentResult] = {}
    for tournament_result in qs:
        if tournament_result.player_pantheon_id is None:
            continue
        if tournament_result.player is None:
            continue
        pantheon_type: str | None = tournament_result.tournament.get_pantheon_type()
        if pantheon_type is None:
            continue
        key = (pantheon_type, tournament_result.player_pantheon_id)
        _add_to_map(result, key, tournament_result)
    return result
