from online.models import TournamentPlayers

players = TournamentPlayers.objects.all()
ids = [x.pantheon_id for x in players]

for player in players:
    print("update player set tenhou_id = '{}' where id = {};".format(player.tenhou_username, player.pantheon_id))
