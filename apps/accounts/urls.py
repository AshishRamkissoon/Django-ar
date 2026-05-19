from django.urls import path
from . import views

urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path("local-login/", views.local_login, name="local_login"),
]
