from typing import List, Optional

from django.utils import timezone

from account.models import User
from player.models import Player
from player.tenhou.models import TenhouNickname
from settings.models import City


class PlayerHelper:
    @staticmethod
    def update_player_from_pantheon_feed(feed) -> List[str]:
        updated_fields = []
        if feed.updated_information is not None:
            feed_city = PlayerHelper.safe_strip(feed, "city")
            feed_title = PlayerHelper.safe_strip(feed, "title")
            feed_email = PlayerHelper.safe_strip(feed, "email")
            feed_tenhou_id = PlayerHelper.safe_strip(feed, "tenhou_id")

            city_object = None
            try:
                city_object = City.objects.get(name_ru=feed_city) if feed_city is not None else None
            except City.DoesNotExist:
                city_object = None
            current_player = PlayerHelper.find_player_smart(player_full_name=feed_title, city_object=city_object)

            is_need_update_user = False
            is_need_update_player = False
            current_user = None
            if feed.user_id is not None:
                current_user = User.objects.get(id=feed.user_id)
            else:
                if feed_email is not None:
                    current_user = User.objects.get(email=feed_email)

            if current_user is not None and feed.updated_information["person_id"] is not None:
                if current_user.new_pantheon_id != int(feed.updated_information["person_id"]):
                    current_user.new_pantheon_id = feed.updated_information["person_id"]
                    updated_fields.append("player's user pantheon_id updated")
                    is_need_update_user = True

            if current_user is not None and current_player is not None:
                if current_user.attached_player is None:
                    current_user.attached_player = current_player
                    updated_fields.append("user's attached player updated")
                    is_need_update_user = True

            if current_player is not None:
                if feed_tenhou_id is not None and len(feed_tenhou_id) <= 8:
                    if (
                        current_player.tenhou_object is not None
                        and current_player.tenhou_object.tenhou_username != feed_tenhou_id
                    ):
                        old_tenhou_objects = current_player.tenhou.all().exclude(id=current_player.tenhou_object.id)
                        updated_fields.append("old tenhou account updated")
                        PlayerHelper.update_player_tenhou_object(
                            current_player,
                            current_player.tenhou_object,
                            feed_tenhou_id,
                            old_tenhou_objects,
                            updated_fields,
                        )
                    else:
                        old_tenhou_objects = current_player.tenhou.all()
                        new_tenhou_object = TenhouNickname.objects.create(
                            username_created_at=timezone.now(), player_id=current_player.id
                        )
                        updated_fields.append("new tenhou account added")
                        PlayerHelper.update_player_tenhou_object(
                            current_player, new_tenhou_object, feed_tenhou_id, old_tenhou_objects, updated_fields
                        )

            if current_player is not None and current_player.pantheon_id != int(feed.updated_information["person_id"]):
                try:
                    dirty_player = Player.objects.get(pantheon_id=int(feed.updated_information["person_id"]))
                    if dirty_player is not None:
                        dirty_player.pantheon_id = None
                        dirty_player.save()
                        updated_fields.append("another player's pantheon id remove because with same person_id")
                except Player.DoesNotExist:
                    pass

                current_player.pantheon_id = feed.updated_information["person_id"]
                updated_fields.append("player's pantheon_id updated")
                is_need_update_player = True

            if is_need_update_user and current_user is not None:
                current_user.save()
            if is_need_update_player and current_player is not None:
                current_player.save()
        return updated_fields

    @staticmethod
    def safe_strip(feed, key) -> Optional[str]:
        if key in feed.updated_information:
            row = feed.updated_information[key]
            if row is not None:
                stripped = row.strip()
                if len(stripped) > 0:
                    return stripped
        return None

    @staticmethod
    def update_player_tenhou_object(player, tenhou_account, new_tenhou_id, old_tenhou_objects, updated_fields):
        tenhou_account.tenhou_username = new_tenhou_id
        tenhou_account.is_main = True
        tenhou_account.is_active = True
        tenhou_account.player = player
        tenhou_account.save()

        for old_tenhou_object in old_tenhou_objects:
            old_tenhou_object.is_main = False
            old_tenhou_object.is_active = False
            old_tenhou_object.save()
            updated_fields.append("old tenhou account disabled")

    @staticmethod
    def find_player_smart(player_full_name: str, city_object=None) -> Optional[Player]:
        arr = player_full_name.strip().split()
        if len(arr) != 2:
            return None
        last_names = PlayerHelper.__generate_name_variants(arr[0].strip())
        first_names = PlayerHelper.__generate_name_variants(arr[1].strip())

        found_players = PlayerHelper.__find_all_players(
            first_names=first_names, last_names=last_names, city_object=city_object
        )
        if len(found_players) == 1:
            return found_players[0]
        else:
            return None

    @staticmethod
    def __generate_name_variants(name: str) -> List[str]:
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
    def __find_all_players(first_names: List[str], last_names: List[str], city_object=None) -> List[Player]:
        players = []
        all_names = first_names + last_names
        players.extend(PlayerHelper.__get_players_by_ru_full_name(all_full_names=all_names, city_object=city_object))
        players.extend(PlayerHelper.__get_players_by_en_full_name(all_full_names=all_names, city_object=city_object))
        return list(set(players))

    @staticmethod
    def __get_players_by_ru_full_name(all_full_names: List[str], city_object=None) -> List[Player]:
        if city_object:
            return Player.objects.filter(
                first_name_ru__in=all_full_names,
                last_name_ru__in=all_full_names,
                city=city_object,
                is_exclude_from_rating=False,
            )
        else:
            return Player.objects.filter(
                first_name_ru__in=all_full_names, last_name_ru__in=all_full_names, is_exclude_from_rating=False
            )

    @staticmethod
    def __get_players_by_en_full_name(all_full_names: List[str], city_object=None) -> List[Player]:
        if city_object:
            return Player.objects.filter(
                first_name_en__in=all_full_names,
                last_name_en__in=all_full_names,
                city=city_object,
                is_exclude_from_rating=False,
            )
        else:
            return Player.objects.filter(
                first_name_en__in=all_full_names, last_name_en__in=all_full_names, is_exclude_from_rating=False
            )
