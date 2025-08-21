from django.urls import path, include
from . import views
from recommendations import urls as recommendations_urls

app_name = "dashboard"

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('analyzer/', views.analyzer_view, name='analyzer'),
    path('history/', views.history_view, name='history'),         # URL temporaires pour les liens de navigation
    path('statistics/', views.statistics_view, name='statistics'),# URL temporaires pour les liens de navigation
    path('recommendations/', include('recommendations.urls')),
]
