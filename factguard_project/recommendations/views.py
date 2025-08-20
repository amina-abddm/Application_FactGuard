# recommandations/views.py
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import Article, Theme


"""Créer les thèmes par défaut"""
themes = [
        {
            'name': 'politique',
            'display_name': 'Politique',
            'emoji': '🏛️',
            'gradient': 'from-blue-500 to-indigo-600',
            'bg_color': 'bg-blue-50',
            'text_color': 'text-blue-700',
            'icon_name': 'university'
        },
        {
            'name': 'finance',
            'display_name': 'Finance',
            'emoji': '💰',
            'gradient': 'from-green-500 to-emerald-600',
            'bg_color': 'bg-green-50',
            'text_color': 'text-green-700',
            'icon_name': 'dollar-sign'
        },
        {
            'name': 'sport',
            'display_name': 'Sport',
            'emoji': '⚽',
            'gradient': 'from-orange-500 to-red-600',
            'bg_color': 'bg-orange-50',
            'text_color': 'text-orange-700',
            'icon_name': 'trophy'
        },
        {
            'name': 'technologie',
            'display_name': 'Technologie',
            'emoji': '💻',
            'gradient': 'from-purple-500 to-violet-600',
            'bg_color': 'bg-purple-50',
            'text_color': 'text-purple-700',
            'icon_name': 'laptop'
        },
        {
            'name': 'science',
            'display_name': 'Science',
            'emoji': '🔬',
            'gradient': 'from-cyan-500 to-blue-600',
            'bg_color': 'bg-cyan-50',
            'text_color': 'text-cyan-700',
            'icon_name': 'microscope'
        },
        {
            'name': 'culture',
            'display_name': 'Culture',
            'emoji': '🎭',
            'gradient': 'from-pink-500 to-rose-600',
            'bg_color': 'bg-pink-50',
            'text_color': 'text-pink-700',
            'icon_name': 'palette'
        },
        {
            'name': 'international',
            'display_name': 'International',
            'emoji': '🌍',
            'gradient': 'from-teal-500 to-cyan-600',
            'bg_color': 'bg-teal-50',
            'text_color': 'text-teal-700',
            'icon_name': 'globe'
        },
        {
            'name': 'sante',
            'display_name': 'Santé',
            'emoji': '🏥',
            'gradient': 'from-red-500 to-pink-600',
            'bg_color': 'bg-red-50',
            'text_color': 'text-red-700',
            'icon_name': 'heart'
        }
    ]
            
def recommendations(request):
    context = {
        "themes": themes,
    }
    return render(request, "recommendations/recommendations.html", context)



def theme_articles(request, theme_name):
    """Articles d'un thème spécifique"""
    theme = get_object_or_404(Theme, name=theme_name, is_active=True)
    articles = Article.objects.filter(theme=theme_name, is_active=True)[:6]
    
    context = {
        'theme': theme,
        'articles': articles,
    }
    return render(request, 'recommendations/theme_articles.html', context)

