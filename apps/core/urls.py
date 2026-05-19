from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("ar/", views.ar_view, name="ar_view"),
]
