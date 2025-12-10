# recommendations/urls.py
from django.urls import path
from .views import recommendations, theme_articles

app_name = "recommendations"

urlpatterns = [
    path("", recommendations, name="recommendations"),
    path('<str:theme_name>/', theme_articles, name='theme_articles'),  
]
