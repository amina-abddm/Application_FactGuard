from django.shortcuts import render, redirect  # ← Import complet
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from datetime import datetime, timedelta
from django.http import HttpResponse


def dashboard_view(request):
    """
    Redirection vers analyzer - point d'entrée principal FactGuard
    """
    return redirect('analyzer')  # ← Maintenant défini


def analyzer_view(request):
    """
    Page analyzer - Cœur de FactGuard avec Azure OpenAI GPT-4
    """
    return render(request, 'dashboard/analyzer.html', {'page': 'Analyseur'})


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

