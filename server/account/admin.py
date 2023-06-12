from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from django.utils.translation import gettext_lazy as _

from account.models import AttachingPlayerRequest, User


class CustomUserAdmin(UserAdmin):
    ordering = ["-date_joined"]
    search_fields = ("username", "first_name", "last_name", "email", "new_pantheon_id")
    list_display = ("username", "email", "attached_player", "date_joined")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("email", "attached_player", "new_pantheon_id")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_tournament_manager",
                    "is_league_manager",
                    "is_ema_players_manager",
                    "user_permissions",
                    "managed_tournaments",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    filter_horizontal = ["user_permissions", "managed_tournaments"]
    raw_id_fields = ["attached_player"]


class AttachingPlayerRequestAdmin(admin.ModelAdmin):
    list_display = ["created_on", "user", "player", "contacts", "is_processed"]
    raw_id_fields = ["player"]


class PermissionAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("content_type")


admin.site.register(Permission, PermissionAdmin)
admin.site.register(User, CustomUserAdmin)
admin.site.register(AttachingPlayerRequest, AttachingPlayerRequestAdmin)
