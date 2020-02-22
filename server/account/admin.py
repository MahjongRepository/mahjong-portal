from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from account.models import User


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_tournament_manager",
                    "is_ema_players_manager",
                    "groups",
                    "user_permissions",
                    "managed_tournaments",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    filter_horizontal = ["groups", "user_permissions", "managed_tournaments"]


admin.site.register(User, CustomUserAdmin)
