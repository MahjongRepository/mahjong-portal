from django import forms
from django.contrib import admin

from rating.models import Rating, RatingDate


class RatingForm(forms.ModelForm):

    class Meta:
        model = Rating
        exclude = ['name', 'description']


class RatingAdmin(admin.ModelAdmin):
    form = RatingForm
    list_display = ['name', 'type', 'order']


class RatingDateAdmin(admin.ModelAdmin):
    list_display = ['date', 'rating']
    list_filter = ['rating']


admin.site.register(Rating, RatingAdmin)
admin.site.register(RatingDate, RatingDateAdmin)
