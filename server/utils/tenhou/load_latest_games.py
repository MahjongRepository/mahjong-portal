# -*- coding: utf-8 -*-
import hashlib


def parse_log_line(line):
    """
    Example of the line:
    23:59 | 20 | 四般東喰赤－ | 最終回(+61.0) manyaoba(+1.0) 可以打(-19.0) KENT6MG(-43.0)
    """

    game_time = line[0:5]
    game_length = line[8:10]
    game_type = line[13:19]
    players = line[22:len(line)]

    temp_players = players.split(' ')
    position = 1
    players = []
    for temp in temp_players:
        name = temp.split('(')[0]

        # iterate symbol by symbol from the end of string
        # and it it is open brace symbol
        # it means that everything before that brace
        # is player name
        for i in reversed(range(len(temp))):
            if temp[i] == '(':
                name = temp[0:i]
                break

        players.append({
            'name': name,
            'position': position,
        })

        position += 1

    return {
        'players': players,
        'game_type': game_type,
        'game_time': game_time
    }


def generate_game_hash(player_name, game_date, game_time_string):
    hash_string = 'player_{}_date_{}_time_{}'.format(
        player_name,
        game_date.strftime('%Y%m%d'),
        game_time_string
    )

    return hashlib.sha1(hash_string.encode()).hexdigest()
