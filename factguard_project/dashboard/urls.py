from django.urls import path, include
from . import views
from django.views.generic import RedirectView
from recommendations import urls as recommendations_urls

app_name = "dashboard"

urlpatterns = [
    
    path('', RedirectView.as_view(url='/dashboard/', permanent=True)),  #  REDIRECTION RACINE VERS DASHBOARD
    path('analyzer/', views.analyzer_view, name='analyzer'),            # type: ignore
    path('history/', views.history_view, name='history'),               # URL temporaires pour les liens de navigation
    path('statistics/', views.statistics_view, name='statistics'),      # URL temporaires pour les liens de navigation
    path('recommendations/', include('recommendations.urls')),
    path('delete-analysis/<int:analysis_id>/', views.delete_analysis_view, name='delete_analysis'),
     path('analysis/<int:analysis_id>/', views.analysis_detail_view, name='analysis_detail'),
    path('clear-history/', views.clear_all_history_view, name='clear_history'),
    path('rag-analyzer/', views.analyzer_unified_view, name='rag_analyzer'),  # type: ignore

]
