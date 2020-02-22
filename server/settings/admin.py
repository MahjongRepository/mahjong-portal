from django import forms
from django.contrib import admin

from settings.models import Country, City


class CountryAdmin(admin.ModelAdmin):
    list_display = ["name"]


class CityForm(forms.ModelForm):
    class Meta:
        model = City
        exclude = ["name"]


class CityAdmin(admin.ModelAdmin):
    form = CityForm
    list_display = ["name"]
    search_fields = ["name_ru", "name_en"]

    prepopulated_fields = {"slug": ["name_en"]}


admin.site.register(Country, CountryAdmin)
admin.site.register(City, CityAdmin)
