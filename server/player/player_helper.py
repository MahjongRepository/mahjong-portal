# -*- coding: utf-8 -*-
import math
import operator
from dataclasses import dataclass
from functools import reduce
from typing import List, Optional

from django.db.models import Q
from django.utils import timezone

from account.models import User
from online.parser import TenhouParser
from player.models import Player
from player.tenhou.models import TenhouNickname
from settings.models import City, Country
from tournament.models import OnlineTournamentRegistration
from utils.general import is_date_before_or_equals


class PlayerHelper:

    @dataclass
    class AccountUpdates:
        code: int
        msg: str

    userPantheonIdUpdate = AccountUpdates(1, "player's user pantheon_id updated")
    userAttachedPlayerUpdate = AccountUpdates(2, "user's attached player updated")
    playerCountryUpdate = AccountUpdates(3, "player's country updated")
    playerCityUpdate = AccountUpdates(4, "player's city updated")
    oldTenhouAccountUpdate = AccountUpdates(5, "old tenhou account updated")
    newTenhouAccountUpdate = AccountUpdates(6, "new tenhou account added")
    removeConflictPantheonIdUpdate = AccountUpdates(
        7, "another player's pantheon id remove because with same person_id"
    )
    playerPantheonIdUpdate = AccountUpdates(8, "player's pantheon_id updated")
    oldTenhouAccountDisableUpdate = AccountUpdates(9, "old tenhou account disabled")

    class TenhouNicknameSearchContext:
        is_tenhou_account_exist: bool
        is_tenhou_account_relate_to_player: bool
        old_tenhou_account: TenhouNickname

        def __init__(self, is_tenhou_account_exist: bool, is_tenhou_account_relate_to_player: bool, old_tenhou_account):
            self.is_tenhou_account_exist = is_tenhou_account_exist
            self.is_tenhou_account_relate_to_player = is_tenhou_account_relate_to_player
            self.old_tenhou_account = old_tenhou_account

    @staticmethod
    def calculate_rating(log_hash, current_tenhou_nickname, games_count):
        parser = TenhouParser()
        players_with_results = parser.get_ratings(log_hash)

        uma_map = {1: 30, 2: 10, 3: -10, 4: -30}

        current_place = -1
        current_rate = -1
        avg_rate = 0

        is_tenhou_account_found = False
        for _, result_map in players_with_results.items():
            if result_map["nickname"] == current_tenhou_nickname:
                current_place = result_map["place"]
                current_rate = result_map["rate"]
                is_tenhou_account_found = True
            avg_rate += int(result_map["rate"])
        if is_tenhou_account_found:
            avg_rate = avg_rate / 4
            place_base = uma_map[current_place]
            adjustment = 1 - (games_count * 0.002) if games_count < 400 else 0.2
            raw_rating_change = adjustment * (place_base + (avg_rate - current_rate) / 40)
            rating_change = float(format(raw_rating_change, ".3g"))
            return math.floor(current_rate + rating_change)
        return None

    @staticmethod
    def __resolve_tenhou_nickname(feed_tenhou_id: str, player) -> TenhouNicknameSearchContext:
        all_tenhou_nicknames = TenhouNickname.objects.filter(tenhou_username=feed_tenhou_id)
        existed_player_tenhou_nickname = all_tenhou_nicknames.filter(player=player)
        is_tenhou_account_relate_to_player = existed_player_tenhou_nickname.exists()
        old_tenhou_account = None
        if is_tenhou_account_relate_to_player:
            old_tenhou_account = existed_player_tenhou_nickname.first()
        return PlayerHelper.TenhouNicknameSearchContext(
            all_tenhou_nicknames.exists(), is_tenhou_account_relate_to_player, old_tenhou_account
        )

    @staticmethod
    def __update_old_tenhou_account(current_player, tenhou_nickname_search_context, feed_tenhou_id, updated_fields):
        old_tenhou_objects = current_player.tenhou.all().exclude(
            id=tenhou_nickname_search_context.old_tenhou_account.id
        )
        updated_fields.append(PlayerHelper.oldTenhouAccountUpdate)
        updated_fields.append(PlayerHelper.newTenhouAccountUpdate)
        PlayerHelper.update_player_tenhou_object(
            current_player,
            tenhou_nickname_search_context.old_tenhou_account,
            feed_tenhou_id,
            old_tenhou_objects,
            updated_fields,
        )

    @staticmethod
    def update_player_from_pantheon_feed(feed) -> List[AccountUpdates]:
        updated_fields = []
        if feed.updated_information is not None:
            feed_city = PlayerHelper.safe_strip(feed, "city")
            feed_title = PlayerHelper.safe_strip(feed, "title")
            feed_email = PlayerHelper.safe_strip(feed, "email")
            feed_tenhou_id = PlayerHelper.safe_strip(feed, "tenhou_id")
            feed_country_code = PlayerHelper.safe_strip(feed, "country")
            feed_person_id = feed.updated_information["person_id"]

            current_user = None
            current_player = None
            if feed.user_id is not None:
                current_user = User.objects.get(id=feed.user_id)
            else:
                if feed_email is not None:
                    current_user = User.objects.get(email=feed_email)

            if current_user is not None and feed_person_id is not None:
                if current_user.attached_player is not None and current_user.attached_player.pantheon_id == int(
                    feed_person_id
                ):
                    current_player = Player.objects.get(pantheon_id=int(feed_person_id))

            city_object = None
            if current_player is None:
                try:
                    city_object = City.objects.get(name_ru=feed_city) if feed_city is not None else None
                except City.DoesNotExist:
                    city_object = None
                if city_object is not None:
                    current_player = PlayerHelper.find_player_smart(
                        player_full_name=feed_title, city_object=city_object
                    )
                else:
                    current_player = None

            if current_player is None:
                current_player = PlayerHelper.find_player_smart(player_full_name=feed_title)

            is_need_update_user = False
            is_need_update_player = False
            if current_user is not None and feed_person_id is not None:
                if current_user.new_pantheon_id != int(feed_person_id):
                    current_user.new_pantheon_id = int(feed_person_id)
                    updated_fields.append(PlayerHelper.userPantheonIdUpdate)
                    is_need_update_user = True

            if current_user is not None and current_player is not None:
                if current_user.attached_player is None:
                    current_user.attached_player = current_player
                    updated_fields.append(PlayerHelper.userAttachedPlayerUpdate)
                    is_need_update_user = True
                else:
                    if current_user.attached_player.id != current_player.id:
                        current_user.attached_player = current_player
                        updated_fields.append(PlayerHelper.userAttachedPlayerUpdate)
                        is_need_update_user = True

            if current_player is not None:
                country_object = None
                try:
                    country_object = (
                        Country.objects.get(code=feed_country_code) if feed_country_code is not None else None
                    )
                except Country.DoesNotExist:
                    country_object = None

                if country_object is not None:
                    current_player.country = country_object
                    updated_fields.append(PlayerHelper.playerCountryUpdate)
                    is_need_update_player = True

                if city_object is not None:
                    current_player.city = city_object
                    updated_fields.append(PlayerHelper.playerCityUpdate)
                    is_need_update_player = True

                if feed_tenhou_id is not None and len(feed_tenhou_id) <= 8:
                    if (
                        current_player.tenhou_object is not None
                        and current_player.tenhou_object.tenhou_username != feed_tenhou_id
                    ):
                        tenhou_nickname_search_context = PlayerHelper.__resolve_tenhou_nickname(
                            feed_tenhou_id, current_player
                        )
                        if not tenhou_nickname_search_context.is_tenhou_account_exist:
                            new_tenhou_object = TenhouNickname.objects.create(
                                username_created_at=timezone.now(),
                                player_id=current_player.id,
                                tenhou_username=feed_tenhou_id,
                            )
                            old_tenhou_objects = current_player.tenhou.all().exclude(id=new_tenhou_object.id)
                            updated_fields.append(PlayerHelper.oldTenhouAccountUpdate)
                            updated_fields.append(PlayerHelper.newTenhouAccountUpdate)
                            PlayerHelper.update_player_tenhou_object(
                                current_player,
                                new_tenhou_object,
                                feed_tenhou_id,
                                old_tenhou_objects,
                                updated_fields,
                            )
                        else:
                            if tenhou_nickname_search_context.is_tenhou_account_relate_to_player:
                                PlayerHelper.__update_old_tenhou_account(
                                    current_player, tenhou_nickname_search_context, feed_tenhou_id, updated_fields
                                )
                    elif current_player.tenhou_object is None:
                        tenhou_nickname_search_context = PlayerHelper.__resolve_tenhou_nickname(
                            feed_tenhou_id, current_player
                        )
                        if not tenhou_nickname_search_context.is_tenhou_account_exist:
                            new_tenhou_object = TenhouNickname.objects.create(
                                username_created_at=timezone.now(),
                                player_id=current_player.id,
                                tenhou_username=feed_tenhou_id,
                            )
                            old_tenhou_objects = []
                            updated_fields.append(PlayerHelper.newTenhouAccountUpdate)
                            PlayerHelper.update_player_tenhou_object(
                                current_player,
                                new_tenhou_object,
                                feed_tenhou_id,
                                old_tenhou_objects,
                                updated_fields,
                            )
                        else:
                            if tenhou_nickname_search_context.is_tenhou_account_relate_to_player:
                                PlayerHelper.__update_old_tenhou_account(
                                    current_player, tenhou_nickname_search_context, feed_tenhou_id, updated_fields
                                )
                    else:
                        old_tenhou_objects = current_player.tenhou.all().exclude(id=current_player.tenhou_object.id)
                        updated_fields.append(PlayerHelper.oldTenhouAccountUpdate)
                        PlayerHelper.update_player_tenhou_object(
                            current_player,
                            current_player.tenhou_object,
                            feed_tenhou_id,
                            old_tenhou_objects,
                            updated_fields,
                        )
            if current_player is not None and feed_person_id is not None:
                try:
                    dirty_player = (
                        Player.objects.filter(pantheon_id=int(feed_person_id)).exclude(id=current_player.id).first()
                    )
                    if dirty_player is not None:
                        dirty_player.pantheon_id = None
                        dirty_player.save()
                        updated_fields.append(PlayerHelper.removeConflictPantheonIdUpdate)
                except Player.DoesNotExist:
                    pass

            if (
                current_player is not None
                and feed_person_id is not None
                and current_player.pantheon_id != int(feed_person_id)
            ):
                try:
                    dirty_player = Player.objects.get(pantheon_id=int(feed_person_id))
                    if dirty_player is not None:
                        dirty_player.pantheon_id = None
                        dirty_player.save()
                        updated_fields.append(PlayerHelper.removeConflictPantheonIdUpdate)
                except Player.DoesNotExist:
                    pass

                current_player.pantheon_id = int(feed_person_id)
                updated_fields.append(PlayerHelper.playerPantheonIdUpdate)
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
        previous_active_state = tenhou_account.is_active
        tenhou_account_is_active = player is not None and not player.is_hide_tenhou_activity
        if tenhou_account_is_active:
            now = timezone.now().date()
            if tenhou_account.last_played_date is not None:
                delta = now - tenhou_account.last_played_date
                if delta.days >= 140:
                    tenhou_account_is_active = previous_active_state

        tenhou_account.tenhou_username = new_tenhou_id
        tenhou_account.is_main = True
        tenhou_account.is_active = tenhou_account_is_active
        tenhou_account.player = player
        tenhou_account.save()

        for old_tenhou_object in old_tenhou_objects:
            old_tenhou_object.is_main = False
            old_tenhou_object.is_active = False
            old_tenhou_object.save()
            updated_fields.append(PlayerHelper.oldTenhouAccountDisableUpdate)

        if player is not None:
            current_registrations = (
                OnlineTournamentRegistration.objects.filter(player=player)
                .filter(tournament__is_upcoming=True)
                .filter(tournament__is_hidden=False)
                .filter(tournament__is_event=False)
                .filter(tournament__is_majsoul_tournament=False)
                .prefetch_related("tournament")
            )
            now = timezone.now()
            for registration in current_registrations:
                tournament = registration.tournament
                if is_date_before_or_equals(now, tournament.start_date):
                    registration.tenhou_nickname = new_tenhou_id
                    registration.save()

    @staticmethod
    def __generate_search_variants_tuples(raw_parts):
        variants = []
        for i in range(len(raw_parts) - 1):
            variants.append((" ".join(raw_parts[: i + 1]), " ".join(raw_parts[i + 1 : len(raw_parts)])))
        return variants

    @staticmethod
    def find_player_smart(player_full_name: str, city_object=None) -> Optional[Player]:
        arr = player_full_name.strip().split()
        if len(arr) > 4:
            return None
        variants = PlayerHelper.__generate_search_variants_tuples(arr)
        founded_player = None
        for variant in variants:
            last_names = PlayerHelper.__generate_name_variants(variant[0].strip())
            first_names = PlayerHelper.__generate_name_variants(variant[1].strip())

            found_players = PlayerHelper.__find_all_players(
                first_names=first_names, last_names=last_names, city_object=city_object
            )
            if len(found_players) == 1:
                founded_player = found_players[0]
                break
        return founded_player

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
        first_name_conditions = reduce(operator.or_, (Q(first_name_ru__iexact=x) for x in all_full_names))
        last_name_conditions = reduce(operator.or_, (Q(last_name_ru__iexact=x) for x in all_full_names))
        if city_object:
            query = first_name_conditions & last_name_conditions & Q(city=city_object) & Q(is_exclude_from_rating=False)
            return Player.objects.filter(query)
        else:
            query = first_name_conditions & last_name_conditions & Q(is_exclude_from_rating=False)
            return Player.objects.filter(query)

    @staticmethod
    def __get_players_by_en_full_name(all_full_names: List[str], city_object=None) -> List[Player]:
        first_name_conditions = reduce(operator.or_, (Q(first_name_en__iexact=x) for x in all_full_names))
        last_name_conditions = reduce(operator.or_, (Q(last_name_en__iexact=x) for x in all_full_names))
        if city_object:
            query = first_name_conditions & last_name_conditions & Q(city=city_object) & Q(is_exclude_from_rating=False)
            return Player.objects.filter(query)
        else:
            query = first_name_conditions & last_name_conditions & Q(is_exclude_from_rating=False)
            return Player.objects.filter(query)
