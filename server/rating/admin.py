from django.contrib import admin

from rating.models import Rating


class RatingAdmin(admin.ModelAdmin):
    list_display = ['name', 'type']


admin.site.register(Rating, RatingAdmin)
