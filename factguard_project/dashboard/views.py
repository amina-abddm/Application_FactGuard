from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from datetime import datetime, timedelta
# Create your views here.
from django.http import HttpResponse





#@login_required
def dashboard_view(request):
    # Calculer les statistiques (données simulées pour l'instant)
    total_analyses = 156
    avg_score = 87
    
    # Statistiques par type
    type_stats = {
        'text': 89,
        'link': 45,
        'image': 22
    }
    
    # Suggestions d'articles (données simulées)
    suggestions = [
        {
            'title': 'Nouvelle étude sur le climat',
            'description': 'Analyse des dernières données climatiques publiées',
            'category': 'science',
            'get_category_display': lambda: 'Science'
        },
        {
            'title': 'Élections locales 2025',
            'description': 'Vérification des promesses de campagne',
            'category': 'politique',
            'get_category_display': lambda: 'Politique'
        },
        {
            'title': 'Santé publique',
            'description': 'Nouvelles recommandations sanitaires',
            'category': 'sante',
            'get_category_display': lambda: 'Santé'
        }
    ]
    
    context = {
        'total_analyses': total_analyses,
        'avg_score': avg_score,
        'type_stats': type_stats,
        'suggestions': suggestions,
        'user': request.user if request.user.is_authenticated else None
    }
    
    return render(request, 'dashboard/coming_soon.html', context)


def analyzer_view(request):
    return render(request, 'dashboard/analyzer.html', {'page': 'Analyseur'})

def history_view(request):
    return render(request, 'dashboard/coming_soon.html', {'page': 'Historique'})

def statistics_view(request):
    return render(request, 'dashboard/coming_soon.html', {'page': 'Statistiques'})
