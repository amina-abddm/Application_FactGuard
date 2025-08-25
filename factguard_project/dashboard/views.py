from django.shortcuts import render, redirect, get_object_or_404
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

print("PYTHONPATH :", sys.path)

@login_required
def dashboard_view(request):
    """Redirection vers analyzer - point d'entrée principal FactGuard"""
    return redirect('analyzer')

@login_required
def analyzer_view(request):
    if request.method == 'POST':
        content_type = request.POST.get('content_type', 'text')
        print(f"Type sélectionné: {content_type}")
        
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
            if content_type == 'link':
                print("🔗 Analyse de lien...")
                prompt = f"Analysez la fiabilité et la crédibilité de ce lien/site web : {content}"
                result = call_gpt_analysis(prompt)
            elif content_type == 'image':
                print("🖼️ Analyse d'image...")
                result = f"Analyse d'image en développement pour : {content}"
            else:
                print("📝 Analyse de texte...")
                result = call_gpt_analysis(content)
            
            confidence = extract_confidence_score(result)
            
            print(f"🔄 Tentative de sauvegarde...")
            analysis = Analysis.objects.create(
                text=content,
                result=result,
                confidence_score=confidence,
                user=request.user,
                content_type=content_type
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
    """Vue pour afficher l'historique avec les 5 dernières et bouton Plus"""
    user = request.user
    all_analyses = Analysis.objects.filter(user=user).order_by('-created_at')
    total_count = all_analyses.count()
    
    print(f"📊 Total analyses pour {user}: {total_count}")
    
    # Gestion du cas vide
    if not all_analyses.exists():
        return render(request, 'dashboard/history.html', {
            'analyses_recent': [],
            'analyses_all': [],
            'total_count': 0,
        })
    
    # Les 5 dernières analyses (affichées par défaut)
    analyses_recent = all_analyses[:5]
    
    return render(request, 'dashboard/history.html', {
        'analyses_recent': analyses_recent,  # Les 5 dernières
        'analyses_all': all_analyses,        # Toutes (pour le bouton Plus)
        'total_count': total_count,
    })


@login_required
def statistics_view(request):
    """Page statistiques simplifiée - FactGuard Sprint 1"""
    avg_score_raw = Analysis.objects.filter(user=request.user).aggregate(
        avg_score=models.Avg('confidence_score')
    )['avg_score'] or 0
    
    # Conversion du score de 0-1 vers 0-100 avec arrondi à 1 décimale
    avg_score_percentage = round(avg_score_raw * 100, 1)
    
    context = { 
        'page': 'Statistiques',
        'total_analyses': Analysis.objects.filter(user=request.user).count(),
        'avg_score': avg_score_percentage,
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


@login_required
def delete_analysis_view(request, analysis_id):
    """Vue pour supprimer une analyse spécifique avec confirmation"""
    analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
    
    if request.method == 'POST':
        analysis.delete()
        messages.success(request, "✅ Analyse supprimée avec succès !")
        return redirect('dashboard:history')
    
    return render(request, 'dashboard/confirm_delete.html', {
        'analysis': analysis,
        'title': 'Supprimer une analyse'
    })

@login_required
def clear_all_history_view(request):
    """Vue pour supprimer tout l'historique avec confirmation"""
    user_analyses = Analysis.objects.filter(user=request.user)
    total_count = user_analyses.count()
    
    if request.method == 'POST':
        deleted_count = user_analyses.count()
        user_analyses.delete()
        messages.success(request, f"✅ {deleted_count} analyses supprimées avec succès !")
        return redirect('dashboard:history')
    
    return render(request, 'dashboard/confirm_delete.html', {
        'analyses_count': total_count,
        'title': 'Vider tout l\'historique'
    })