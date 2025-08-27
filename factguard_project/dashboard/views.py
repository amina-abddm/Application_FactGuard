from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models
from django.utils import timezone
from django.db.models import Count, Avg
from django.contrib import messages
from .models import Analysis
from typing import Optional, Protocol, TYPE_CHECKING
import re
import sys

# ============================================================================
# IMPORTS ET CONFIGURATION DES SERVICES IA
# ============================================================================

# Import conditionnel du service RAG avec typage correct
RAGServiceType = None
RAG_AVAILABLE = False

try:
    from api.services.rag_service import RAGService
    RAGServiceType = RAGService
    RAG_AVAILABLE = True
    print(" Service RAG importé avec succès depuis api.services")
except ImportError as e:
    RAGServiceType = None
    RAG_AVAILABLE = False
    print(f" Service RAG non disponible: {e}")

# Import conditionnel Azure OpenAI
try:
    from api.services.azure_openai_service import AzureOpenAIService as AzureService
    print(" AzureService importé avec succès")
except ImportError as e:
    print(f" Erreur import AzureService: {e}")


# Définition d'un Protocol pour le typage
class RAGServiceProtocol(Protocol):
    def analyze_with_context(self, query: str) -> dict:
        ...
    def get_similar_analyses(self, query: str, limit: int = 5) -> list:
        ...

print("PYTHONPATH :", sys.path)

# ============================================================================
# VUES PRINCIPALES
# ============================================================================

@login_required
def dashboard_view(request):
    """Redirection vers analyzer - point d'entrée principal FactGuard"""
    return redirect('dashboard:analyzer')

@login_required
def analyzer_unified_view(request):
    """ Analyseur Unifié - Standard et RAG avec sélection de mode"""
    
    # Détecter le mode basé sur l'URL ou paramètre
    is_rag_mode = 'rag' in request.path or request.GET.get('mode') == 'rag'
    
    context = {
        'rag_mode': is_rag_mode,
        'rag_available': RAG_AVAILABLE,
        'page_title': 'Analyseur Intelligent RAG' if is_rag_mode else 'Analyseur Standard'
    }
    
    if request.method == 'POST':
        print(f" DEBUG: Mode détecté = {'RAG' if is_rag_mode else 'Standard'}")
        print(f" DEBUG: Données POST = {dict(request.POST)}")
        
        # Récupération intelligente du contenu selon le type
        content_type = request.POST.get('content_type', 'text')
        analysis_mode = request.POST.get('analysis_mode', 'rag' if is_rag_mode else 'standard')
        
        # Extraction du contenu selon le type sélectionné
        content = _extract_content_by_type(request, content_type)
        
        print(f" DEBUG: Type = {content_type}, Contenu = '{str(content)[:100]}...'")
        
        if not content or (isinstance(content, str) and len(content) < 5):
            messages.error(request, "Veuillez saisir du contenu à analyser (minimum 5 caractères).")
            return render(request, 'dashboard/analyzer_unified.html', context)
        
        try:
            # Choix du mode d'analyse
            if analysis_mode == 'rag' and RAG_AVAILABLE and RAGServiceType is not None:
                analysis_result, additional_context = _perform_rag_analysis(content)
                context.update(additional_context)
                context['analysis_mode'] = 'rag'
                
                sources_count = additional_context.get('sources_count', 0)
                messages.success(request, f" Analyse RAG terminée avec {sources_count} source(s) contextuelle(s)!")
                
            else:
                analysis_result = _perform_standard_analysis(content, content_type)
                context.update({
                    'analysis_result': analysis_result,
                    'analysis_mode': 'standard'
                })
                messages.success(request, " Analyse standard terminée !")
            
            # Extraction du score de confiance et sauvegarde
            confidence = extract_confidence_score(context['analysis_result'])
            
            analysis = Analysis.objects.create(
                text=str(content)[:1000],  # Limiter la taille pour la DB
                result=context['analysis_result'],
                confidence_score=confidence,
                user=request.user,
                content_type=content_type
            )
            
            context.update({
                'confidence': confidence * 100 if confidence < 1 else confidence,
                'query_analyzed': content,
                'analysis': analysis
            })
            
            print(f" DEBUG: Analyse sauvegardée ID: {analysis.pk}")
            
        except Exception as e:
            print(f" DEBUG: Erreur lors de l'analyse: {e}")
            messages.error(request, f" Erreur lors de l'analyse : {str(e)}")
            context['error_message'] = str(e)
    
    return render(request, 'dashboard/analyzer_unified.html', context)

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def _extract_content_by_type(request, content_type):
    """Extrait le contenu selon le type sélectionné"""
    if content_type == 'text':
        return request.POST.get('text_to_analyze', '').strip()
    elif content_type == 'link':
        return request.POST.get('content', '').strip()
    elif content_type == 'image':
        uploaded_file = request.FILES.get('image')
        return f"Image: {uploaded_file.name}" if uploaded_file else ""
    else:
        return request.POST.get('content', '').strip()

def _perform_rag_analysis(content):
    """Effectue une analyse RAG"""
    print(" DEBUG: Utilisation du mode RAG")
    
    if RAGServiceType is None:
        raise RuntimeError("Le service RAG n'est pas disponible.")
    rag_service: RAGServiceProtocol = RAGServiceType()
    rag_result = rag_service.analyze_with_context(str(content))
    
    analysis_result = rag_result.get('analysis_result', 'Pas de résultat')
    additional_context = {
        'analysis_result': analysis_result,
        'sources_count': rag_result.get('sources_count', 0),
        'context_used': rag_result.get('context_used', '')
    }
    
    return analysis_result, additional_context

def _perform_standard_analysis(content, content_type):
    """Effectue une analyse standard GPT-4o"""
    print("⚡ DEBUG: Utilisation du mode standard")
    
    if content_type == 'link':
        prompt = f"Analysez la fiabilité et la crédibilité de ce lien/site web : {content}"
        return call_gpt_analysis(prompt)
    elif content_type == 'image':
        return f"Analyse d'image en développement pour : {content}"
    else:
        return call_gpt_analysis(str(content))

def extract_confidence_score(result):
    """Extrait le score de confiance du résultat GPT"""
    try:
        patterns = [
            r'(?:score|fiabilité)[:\s]*(\d+(?:\.\d+)?)\s*[/%]',
            r'(\d+(?:\.\d+)?)\s*[/%]',
            r'confiance[:\s]*(\d+(?:\.\d+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, str(result).lower())
            if match:
                score = float(match.group(1))
                return score / 100 if score > 1 else score
    except Exception as e:
        print(f"Erreur extraction score: {e}")
    
    return 0.0

# ============================================================================
# VUES EXISTANTES (inchangées)
# ============================================================================

@login_required
def analyzer_view(request):
    """Vue analyzer standard - redirige vers la vue unifiée"""
    return analyzer_unified_view(request)

@login_required
def rag_analyzer_view(request):
    """Vue RAG analyzer - redirige vers la vue unifiée"""
    return analyzer_unified_view(request)

@login_required
def history_view(request):
    """Vue pour afficher l'historique avec les 5 dernières et bouton Plus"""
    user = request.user
    all_analyses = Analysis.objects.filter(user=user).order_by('-created_at')
    total_count = all_analyses.count()
    
    print(f"📊 Total analyses pour {user}: {total_count}")
    
    if not all_analyses.exists():
        return render(request, 'dashboard/history.html', {
            'analyses_recent': [],
            'analyses_all': [],
            'total_count': 0,
        })
    
    analyses_recent = all_analyses[:5]
    
    return render(request, 'dashboard/history.html', {
        'analyses_recent': analyses_recent,
        'analyses_all': all_analyses,
        'total_count': total_count,
    })

@login_required
def statistics_view(request):
    """Page statistiques complète - FactGuard"""
    
    user_analyses = Analysis.objects.filter(user=request.user)
    total_analyses = user_analyses.count()
    
    avg_score_raw = user_analyses.aggregate(
        avg_score=models.Avg('confidence_score')
    )['avg_score'] or 0
    avg_score_percentage = round(avg_score_raw * 100, 1)
    
    reliable_count = user_analyses.filter(confidence_score__gte=0.75).count()
    reliable_content = round((reliable_count / total_analyses) * 100, 1) if total_analyses > 0 else 0
    
    today = timezone.now().date()
    analyses_today = user_analyses.filter(created_at__date=today).count()
    
    type_counts = user_analyses.values('content_type').annotate(count=Count('id'))
    type_stats = {'text': 0, 'link': 0, 'image': 0}
    for item in type_counts:
        content_type = item['content_type']
        if content_type in type_stats:
            type_stats[content_type] = item['count']
    
    total_content = sum(type_stats.values())
    type_percentages = {
        'text_percent': round((type_stats['text'] / total_content) * 100, 1) if total_content > 0 else 0,
        'link_percent': round((type_stats['link'] / total_content) * 100, 1) if total_content > 0 else 0,
        'image_percent': round((type_stats['image'] / total_content) * 100, 1) if total_content > 0 else 0,
    }
    
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

@login_required
def delete_analysis_view(request, analysis_id):
    """Vue pour supprimer une analyse spécifique avec confirmation"""
    analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
    
    if request.method == 'POST':
        analysis.delete()
        messages.success(request, " Analyse supprimée avec succès !")
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
        messages.success(request, f" {deleted_count} analyses supprimées avec succès !")
        return redirect('dashboard:history')
    
    return render(request, 'dashboard/confirm_delete.html', {
        'analyses_count': total_count,
        'title': 'Vider tout l\'historique'
    })
