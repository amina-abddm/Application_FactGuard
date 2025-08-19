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
    return redirect('analyzer')  #


def analyzer_view(request):
    analysis_result = None
    error_message = None

    if request.method == 'POST':
        content = request.POST.get('text_to_analyze', '')
        if content:
            try:
                service = AzureOpenAIService()  # Initialisation ici
                messages = [
                    {"role": "system", "content": "Analyse d'information pour FactGuard."},
                    {"role": "user", "content": content}
                ]
                response = service.chat_completion(messages)
                analysis_result = response.choices[0].message.content
            except Exception as e:
                error_message = str(e)

    return render(request, 'dashboard/analyzer.html', {
        'analysis_result': analysis_result,
        'error_message': error_message
    })


def history_view(request):
    """
    Page historique - En développement
    """
    return render(request, 'dashboard/coming_soon.html', {'page': 'Historique'})


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

