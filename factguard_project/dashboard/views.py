from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models
from django.utils import timezone
from django.db.models import Count, Avg
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
    """Page statistiques complète - FactGuard"""
    
    # Données de base
    user_analyses = Analysis.objects.filter(user=request.user)
    total_analyses = user_analyses.count()
    
    # Score moyen (0-1 vers 0-100)
    avg_score_raw = user_analyses.aggregate(
        avg_score=models.Avg('confidence_score')
    )['avg_score'] or 0
    avg_score_percentage = round(avg_score_raw * 100, 1)
    
    # Contenu fiable (seuil : confidence_score >= 0.75)
    reliable_count = user_analyses.filter(confidence_score__gte=0.75).count()
    reliable_content = round((reliable_count / total_analyses) * 100, 1) if total_analyses > 0 else 0
    
    # Analyses d'aujourd'hui
    today = timezone.now().date()
    analyses_today = user_analyses.filter(created_at__date=today).count()
    
    # Répartition par type
    type_counts = user_analyses.values('content_type').annotate(count=Count('id'))
    type_stats = {'text': 0, 'link': 0, 'image': 0}
    for item in type_counts:
        content_type = item['content_type']
        if content_type in type_stats:
            type_stats[content_type] = item['count']
    
    # Pourcentages pour les jauges
    total_content = sum(type_stats.values())
    type_percentages = {
        'text_percent': round((type_stats['text'] / total_content) * 100, 1) if total_content > 0 else 0,
        'link_percent': round((type_stats['link'] / total_content) * 100, 1) if total_content > 0 else 0,
        'image_percent': round((type_stats['image'] / total_content) * 100, 1) if total_content > 0 else 0,
    }
    
    # Dernière analyse
    last_analysis = user_analyses.order_by('-created_at').first()
    last_analysis_text = "Pas encore d'analyse"
    if last_analysis:
        time_diff = timezone.now() - last_analysis.created_at
        if time_diff.days > 0:
            last_analysis_text = f"Il y a {time_diff.days} jour(s)"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            last_analysis_text = f"Il y a {hours} heure(s)"
        else:
            minutes = time_diff.seconds // 60
            last_analysis_text = f"Il y a {minutes} minute(s)"
    
    # Context complet
    context = {
        'page': 'Statistiques',
        'total_analyses': total_analyses,
        'avg_score': avg_score_percentage,
        'type_stats': type_stats,
        'type_percentages': type_percentages,
        'simple_stats': {
            'reliable_content': reliable_content,
            'analyses_today': analyses_today,
            'ai_model': 'GPT-4o',
            'last_analysis': last_analysis_text,
        },
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