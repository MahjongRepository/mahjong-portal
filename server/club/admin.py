from django.contrib import admin

from club.models import Club


class ClubAdmin(admin.ModelAdmin):
    list_display = ['name', 'city']
    search_fields = ['name']


admin.site.register(Club, ClubAdmin)
