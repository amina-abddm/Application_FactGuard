from django.shortcuts import render, redirect  #
from django.contrib.auth.decorators import login_required
from api.services.azure_openai_service import AzureOpenAIService 
from django.db.models import Count, Avg
from datetime import datetime, timedelta
from django.http import HttpResponse

import sys
print("PYTHONPATH :", sys.path)  # Affiche les chemins recherchés



def dashboard_view(request):
        """
    Redirection vers analyzer - point d'entrée principal FactGuard
    """
        return redirect('analyzer')


def analyzer_view(request):
    analysis_result = None
    error_message = None

    if request.method == 'POST':
        content_type = request.POST.get('content_type', 'text')  # text ou link
        if content_type == 'text':
            content = request.POST.get('text_to_analyze', '')
        elif content_type == 'link':
            content = request.POST.get('content', '')
        else:                     # image ignorée pour le moment
            content = ''

        if content:
            try:
                service = AzureOpenAIService()
                analysis_result = service.analyze_content(content, content_type=content_type)
            except Exception as e:
                error_message = f"Erreur lors de l'analyse : {e}"

    return render(
        request,
        'dashboard/analyzer.html',
        {'analysis_result': analysis_result, 'error_message': error_message}
    )


def history_view(request):
    """
    Page historique - En développement
    """
    return render(request, 'dashboard/historical.html', {'page': 'Historique'})


def statistics_view(request):
    """
    Page statistiques simplifiée - FactGuard Sprint 1
    """
    # Context : dictionnaire Python standard
    context = { 
        'page': 'Statistiques',
        'total_analyses': 156,
        'avg_score': 87,
        'type_stats': {
            'text': 89,
            'link': 45,
            'image': 22
        },
        'user': request.user,
    }
    
    return render(request, 'dashboard/statistics.html', context)

