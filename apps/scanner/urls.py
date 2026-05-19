from django.urls import path
from . import views

urlpatterns = [
    path("scan/", views.scan_view, name="scan"),
    path("history/", views.history_view, name="history"),
]
