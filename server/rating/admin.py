from django import forms
from django.contrib import admin

from rating.models import Rating


class RatingForm(forms.ModelForm):

    class Meta:
        model = Rating
        exclude = ['name', 'description']


class RatingAdmin(admin.ModelAdmin):
    form = RatingForm
    list_display = ['name', 'type', 'order']


admin.site.register(Rating, RatingAdmin)
