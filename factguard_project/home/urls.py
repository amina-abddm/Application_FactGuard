# home/urls.py
from django.urls import path
from . import views
from .views import home_view, SignUpView

app_name = "home"

urlpatterns = [
    path("", home_view, name="index"),
    path("accounts/signup/", SignUpView.as_view(), name="signup"),
]
