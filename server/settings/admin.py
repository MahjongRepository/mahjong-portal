from django.contrib import admin

from settings.models import Country


class CountryAdmin(admin.ModelAdmin):
    list_display = ['name']


admin.site.register(Country, CountryAdmin)
