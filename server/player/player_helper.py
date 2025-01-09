from typing import List, Optional

from player.models import Player


class PlayerHelper:
    @staticmethod
    def find_player_smart(player_full_name: str) -> Optional[Player]:
        arr = player_full_name.strip().split()
        if len(arr) != 2:
            return None
        last_names = PlayerHelper.generate_name_variants(arr[0].strip())
        first_names = PlayerHelper.generate_name_variants(arr[1].strip())

        found_players = PlayerHelper.find_all_players(first_names=first_names, last_names=last_names)
        if len(found_players) == 1:
            return found_players[0]
        else:
            return None

    @staticmethod
    def generate_name_variants(name: str) -> List[str]:
        res = [name]
        if "ё" in name:
            res.append(name.replace("ё", "е"))
            return res
        if "е" not in name:
            return res
        for i in range(len(name)):
            if name[i] == "е":
                res.append(name[:i] + "ё" + name[i + 1 :])
        return res

    @staticmethod
    def find_all_players(first_names: List[str], last_names: List[str]) -> List[Player]:
        players = []
        all_names = first_names + last_names
        players.extend(
            Player.objects.filter(first_name_ru__in=all_names, last_name_ru__in=all_names, is_exclude_from_rating=False)
        )
        players.extend(
            Player.objects.filter(first_name_en__in=all_names, last_name_en__in=all_names, is_exclude_from_rating=False)
        )
        return players
