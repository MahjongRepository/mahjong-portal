from django.contrib import admin

from settings.models import Country, City, TournamentType


class CountryAdmin(admin.ModelAdmin):
    list_display = ['name']


class CityAdmin(admin.ModelAdmin):
    list_display = ['name']


class TournamentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']


admin.site.register(Country, CountryAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(TournamentType, TournamentTypeAdmin)
