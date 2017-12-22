from django.contrib import admin

from settings.models import Country, City


class CountryAdmin(admin.ModelAdmin):
    list_display = ['name']


class CityAdmin(admin.ModelAdmin):
    list_display = ['name']


admin.site.register(Country, CountryAdmin)
admin.site.register(City, CityAdmin)
