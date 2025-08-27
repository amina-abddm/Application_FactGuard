from django.urls import path, include
from . import views
from recommendations import urls as recommendations_urls

app_name = "dashboard"

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('analyzer/', views.analyzer_view, name='analyzer'),
    path('history/', views.history_view, name='history'),         
    path('statistics/', views.statistics_view, name='statistics'),
    path('recommendations/', include('recommendations.urls')),
    path('delete-analysis/<int:analysis_id>/', views.delete_analysis_view, name='delete_analysis'),
    path('clear-history/', views.clear_all_history_view, name='clear_history'),
    path('rag-analyzer/', views.analyzer_unified_view, name='rag_analyzer'),

]
