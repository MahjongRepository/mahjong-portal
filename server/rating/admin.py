# -*- coding: utf-8 -*-

from django import forms
from django.contrib import admin

from rating.models import ExternalRating, Rating, RatingDate


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        exclude = ["name", "description"]


class ExternalRatingForm(forms.ModelForm):
    class Meta:
        model = ExternalRating
        exclude = ["name", "description"]


class RatingAdmin(admin.ModelAdmin):
    form = RatingForm
    list_display = ["name", "type", "order"]


class RatingDateAdmin(admin.ModelAdmin):
    list_display = ["date", "rating"]
    list_filter = ["rating"]


class ExternalRatingAdmin(admin.ModelAdmin):
    form = ExternalRatingForm
    list_display = ["name", "order"]


admin.site.register(Rating, RatingAdmin)
admin.site.register(RatingDate, RatingDateAdmin)
admin.site.register(ExternalRating, ExternalRatingAdmin)
