# -*- coding: utf-8 -*-

from django.urls import path

from yagi_keiji_cup.views import cup_final_information

urlpatterns = [
    path(r"", cup_final_information, name="yagi_keiji_cup_details"),
]
