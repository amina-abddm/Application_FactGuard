from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import models
from django.contrib import messages
from .models import Analysis
import re
import sys

# Imports avec gestion d'erreur
try:
    from api.services.azure_openai_service import AzureOpenAIService as AzureService
    print("✅ AzureService importé avec succès")
except ImportError as e:
    print(f"❌ Erreur import AzureService: {e}")

try:
    from azure.azure_openai import analyse_information as call_gpt_analysis
    print("✅ call_gpt_analysis importé avec succès")
except ImportError as e:
    print(f"❌ Erreur import call_gpt_analysis: {e}")

import re
import sys

print("PYTHONPATH :", sys.path)

@login_required
def dashboard_view(request):
    """Redirection vers analyzer - point d'entrée principal FactGuard"""
    return redirect('analyzer')

@login_required
def analyzer_view(request):
    print(f"=== analyzer_view - Méthode: {request.method} ===")
    
    if request.method == 'POST':
        text = request.POST.get('text_to_analyze', '').strip()  
        print(f"Texte reçu: '{text}' (longueur: {len(text)})")
        print(f"Données POST: {dict(request.POST)}")
        
        if not text or len(text) < 10:
            messages.error(request, "Le texte doit contenir au moins 10 caractères.")
            return render(request, 'dashboard/analyzer.html')
        
        try:
            print("🔄 Appel call_gpt_analysis...")
            result = call_gpt_analysis(text)
            print(f"✅ Résultat: {result}")
            
            confidence = extract_confidence_score(result)
            print(f"📊 Confiance: {confidence}")
            
            # Enregistrement en base
            analysis = Analysis.objects.create(
                text=text,
                result=result,
                confidence_score=confidence,
                user=request.user
            )
            print(f"💾 Analyse sauvegardée ID: {analysis.pk}")
            
            messages.success(request, f"✅ Analyse #{analysis.pk} enregistrée !")
            
            # ✅ CORRECTION : Passer les bonnes variables au template
            return render(request, 'dashboard/analyzer.html', {
                'analysis_result': result,  # ← Variable utilisée dans le template
                'analysis': analysis,
                'confidence': confidence
            })
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            messages.error(request, f"❌ Erreur : {str(e)}")
            return render(request, 'dashboard/analyzer.html', {
                'error_message': str(e)  # ← Variable utilisée dans le template
            })
    
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
