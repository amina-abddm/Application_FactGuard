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
    if request.method == 'POST':
        #  Récupérer le type sélectionné (nom correct du template)
        content_type = request.POST.get('content_type', 'text')
        print(f"Type sélectionné: {content_type}")
        
        #  Récupérer le contenu selon le type (noms corrects du template)
        if content_type == 'text':
            content = request.POST.get('text_to_analyze', '').strip()
        elif content_type == 'link':
            content = request.POST.get('content', '').strip()          
        elif content_type == 'image':
            uploaded_file = request.FILES.get('image')                
            content = f"Image: {uploaded_file.name}" if uploaded_file else ""
        else:
            content = ""
            
        print(f"Contenu reçu pour {content_type}: '{content}'")
        
        if not content or len(content) < 5:
            messages.error(request, "Veuillez saisir du contenu à analyser.")
            return render(request, 'dashboard/analyzer.html')
        
        try:
            #  Adapter l'analyse selon le type
            if content_type == 'link':
                print("🔗 Analyse de lien...")
                # Instruction spécifique pour les liens
                prompt = f"Analysez la fiabilité et la crédibilité de ce lien/site web : {content}"
                result = call_gpt_analysis(prompt)
            elif content_type == 'image':
                print("🖼️ Analyse d'image...")
                result = f"Analyse d'image en développement pour : {content}"
            else:
                print("📝 Analyse de texte...")
                result = call_gpt_analysis(content)
            
            confidence = extract_confidence_score(result)
            
            # Sauvegarde
            analysis = Analysis.objects.create(
                text=content,
                result=result,
                confidence_score=confidence,
                user=request.user
            )
            
            print(f"✅ Analyse {content_type} sauvegardée ID: {analysis.pk}")
            messages.success(request, f"✅ Analyse enregistrée avec succès !")
            
            return render(request, 'dashboard/analyzer.html', {
                'analysis_result': result,
                'analysis': analysis,
                'confidence': confidence * 100 if confidence < 1 else confidence,
            })
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
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
