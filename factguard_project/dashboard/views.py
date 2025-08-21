from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from azure.azure_openai import analyse_information as call_gpt_analysis
from django.db import models
from django.contrib import messages
from .models import Analysis
import re
import sys

print("PYTHONPATH :", sys.path)

@login_required
def dashboard_view(request):
    """Redirection vers analyzer - point d'entrée principal FactGuard"""
    return redirect('analyzer')

@login_required
def analyzer_view(request):
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        
        if not text or len(text) < 10:
            messages.error(request, "Le texte doit contenir au moins 10 caractères.")
            return render(request, 'dashboard/analyzer.html')
        
        try:
            # Appel à Azure OpenAI GPT-4o
            result = call_gpt_analysis(text)
            
            # Extraire le score de confiance
            confidence = extract_confidence_score(result)
            
            # Enregistrer l'analyse en base
            analysis = Analysis.objects.create(
                text=text,
                result=result,
                confidence_score=confidence,
                user=request.user
            )
            
            messages.success(request, f"✅ Analyse #{analysis.pk} enregistrée avec succès !")
            
            return render(request, 'dashboard/analyzer.html', {
                'result': result,
                'analysis': analysis,
                'confidence': confidence
            })
            
        except Exception as e:
            messages.error(request, f"❌ Erreur lors de l'analyse : {str(e)}")
            return render(request, 'dashboard/analyzer.html')
    
    return render(request, 'dashboard/analyzer.html')

@login_required
def history_view(request):
    """Vue pour afficher l'historique des analyses"""
    analyses = Analysis.objects.filter(user=request.user).order_by('-created_at')[:20]
    return render(request, 'dashboard/history.html', {
        'analyses': analyses,
        'total_count': Analysis.objects.filter(user=request.user).count()
    })

@login_required
def statistics_view(request):
    """Page statistiques simplifiée - FactGuard Sprint 1"""
    context = { 
        'page': 'Statistiques',
        'total_analyses': Analysis.objects.filter(user=request.user).count(),
        'avg_score': Analysis.objects.filter(user=request.user).aggregate(
            avg_score=models.Avg('confidence_score')
        )['avg_score'] or 0,
        'user': request.user,
    }
    
    return render(request, 'dashboard/statistics.html', context)

def extract_confidence_score(result):
    """Extrait le score de confiance du résultat GPT"""
    try:
        patterns = [
            r'(?:score|fiabilité)[:\s]*(\d+(?:\.\d+)?)\s*[/%]',
            r'(\d+(?:\.\d+)?)\s*[/%]',
            r'confiance[:\s]*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, result.lower())
            if match:
                score = float(match.group(1))
                return score / 100 if score > 1 else score
    except Exception as e:
        print(f"Erreur extraction score: {e}")
    
    return 0.0
