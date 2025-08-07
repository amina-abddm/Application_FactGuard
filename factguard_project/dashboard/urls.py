from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
        # URLs temporaires pour les liens de navigation
    path('analyzer/', views.analyzer_view, name='analyzer'),
    path('history/', views.history_view, name='history'),
    path('statistics/', views.statistics_view, name='statistics'),
]
