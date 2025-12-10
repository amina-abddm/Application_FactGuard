from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models
import logging
from django.http import HttpResponse
from opentelemetry import trace
from django.utils import timezone
from django.db.models import Count, Avg
from django.contrib import messages
from .models import Analysis
from typing import Optional, Protocol, TYPE_CHECKING
import re
import sys
from datetime import date


# ============================================================================
# IMPORTS ET CONFIGURATION DES SERVICES IA
# ============================================================================
# Import conditionnel du service RAG avec typage correct
RAGServiceType = None
RAG_AVAILABLE = False


try:
    # Import du service RAG complet
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'api'))
    
    from llm_rag.rag_service import RAGService
    from llm_rag.content_indexer import FactGuardContentIndexer
    
    RAGServiceType = RAGService
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"RAG service non disponible: {e}")
    RAGServiceType = None
    RAG_AVAILABLE = False



# Import conditionnel Azure OpenAI SDK 
try:
    from llm_rag.azure_openai_service import AzureOpenAIService
    AZURE_SDK_AVAILABLE = True
except ImportError as e:
    AzureOpenAIService = None
    AZURE_SDK_AVAILABLE = False


call_gpt_analysis = None

# Définition d'un Protocol pour le typage
class RAGServiceProtocol(Protocol):
    def analyze_with_context(self, query: str) -> dict:
        ...
    def get_similar_analyses(self, query: str, limit: int = 5) -> list:
        ...


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
        'azure_sdk_available': AZURE_SDK_AVAILABLE,
        'page_title': 'Analyseur Intelligent RAG' if is_rag_mode else 'Analyseur Standard'
    }
    
    if request.method == 'POST':
        # Récupération intelligente du contenu selon le type
        content_type = request.POST.get('content_type', 'text')
        analysis_mode = request.POST.get('analysis_mode', 'rag' if is_rag_mode else 'standard')
        
        # Extraction du contenu selon le type sélectionné
        content = _extract_content_by_type(request, content_type)
        
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
                messages.success(request, f"Analyse RAG terminée avec {sources_count} source(s) contextuelle(s)!")
                
            else:
                analysis_result = _perform_standard_analysis(content, content_type)
                context.update({
                    'analysis_result': analysis_result,
                    'analysis_mode': 'standard'
                })
                messages.success(request, "Analyse standard terminée !")
                
            # Extraction du score de confiance et sauvegarde
            confidence = extract_confidence_score(context.get('analysis_result', ''))
            
            analysis = Analysis.objects.create(
                text=str(content)[:1000],
                result=context.get('analysis_result', ''),
                confidence_score=confidence,
                user=request.user,
                content_type=content_type
            )

            # AUTO-INDEXATION pour enrichir la base RAG
            if analysis_mode == 'rag':
                try:
                    _auto_index_analysis(analysis)
                    print(f"Analyse {analysis.pk} ajoutée à la base de connaissances RAG")
                except Exception as e:
                    print(f"Erreur auto-indexation: {e}")
            
            context.update({
                'confidence': confidence * 100 if confidence < 1 else confidence,
                'query_analyzed': content,
                'analysis': analysis
            })

            
            context.update({
                'confidence': confidence * 100 if confidence < 1 else confidence,
                'query_analyzed': content,
                'analysis': analysis
            })
            
        except Exception as e:
            messages.error(request, f"Erreur lors de l'analyse : {str(e)}")
            context['error_message'] = str(e)
    
    return render(request, 'dashboard/analyzer_unified.html', context)


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================


def _get_azure_service():
    """Retourne une instance du service Azure ou None si indisponible"""
    if not AZURE_SDK_AVAILABLE or AzureOpenAIService is None:
        return None
    
    try:
        service = AzureOpenAIService()
        if service.is_available():
            return service
    except Exception as e:
        pass
    
    return None


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


logger = logging.getLogger(__name__)

def _perform_rag_analysis(content):
    """Effectue une analyse RAG enrichie avec Azure AI Search"""
    
    if RAGServiceType is None:
        raise RuntimeError("Le service RAG n'est pas disponible.")
    
    try:
        print(f"Démarrage analyse RAG pour: {content[:50]}...")
        
        # Initialiser le service RAG
        rag_service = RAGServiceType()
        
        # Analyse avec contexte historique - ADAPTATION pour votre service existant
        rag_result = rag_service.analyze_with_context(str(content), analysis_type="reliability")
        
        # Récupération des données selon votre structure existante
        analysis_result = rag_result.get('analysis_result', 'Pas de résultat')
        sources_count = rag_result.get('sources_count', 0)
        context_used = rag_result.get('context_used', '')
        confidence_raw = rag_result.get('analysis_confidence', 0.7)
        
        # Conversion confidence en pourcentage
        confidence = int(confidence_raw * 100) if confidence_raw <= 1 else int(confidence_raw)
        
        print(f"Analyse RAG terminée - {sources_count} sources utilisées")
        
        additional_context = {
            'analysis_result': analysis_result,
            'sources_count': sources_count,
            'context_used': context_used,
            'confidence': confidence,
            'sources': rag_result.get('sources', []),
            'analysis_confidence': confidence / 100
        }
        
        return analysis_result, additional_context
        
    except Exception as e:
        logger.error(f"Erreur analyse RAG: {e}")
        
        # Fallback vers analyse standard
        try:
            azure_service = _get_azure_service()
            if azure_service:
                fallback_result = azure_service.analyze_information(str(content), content_type='text')
                return fallback_result, {
                    'analysis_result': fallback_result,
                    'sources_count': 0,
                    'context_used': 'Fallback - Aucun contexte historique',
                    'confidence': 60
                }
            else:
                raise RuntimeError(f"Service RAG et fallback Azure indisponibles: {str(e)}")
                
        except Exception as fallback_error:
            logger.error(f"Erreur fallback: {fallback_error}")
            raise RuntimeError(f"Échec RAG et fallback: {str(e)}")


def _perform_standard_analysis(content, content_type):
    """Effectue une analyse standard GPT-4o avec Azure SDK"""
    
    # Essai avec le  SDK Azure
    azure_service = _get_azure_service()
    
    if azure_service:
        try:
            if content_type == 'link':
                return azure_service.analyze_information(
                    f"Analysez la fiabilité et la crédibilité de ce lien/site web : {content}",
                    content_type='link'
                )
            elif content_type == 'image':
                return f"Analyse d'image en développement pour : {content}"
            else:
                return azure_service.analyze_information(str(content), content_type='text')
                
        except Exception as e:
            pass
    
    # Fallback vers l'ancien système
    if call_gpt_analysis:
        try:
            if content_type == 'link':
                prompt = f"Analysez la fiabilité et la crédibilité de ce lien/site web : {content}"
                return call_gpt_analysis(prompt)
            elif content_type == 'image':
                return f"Analyse d'image en développement pour : {content}"
            else:
                return call_gpt_analysis(str(content))
        except Exception as e:
            return f"Erreur lors de l'analyse : {str(e)}"
    else:
        return "Aucun service d'analyse disponible. Veuillez vérifier la configuration Azure OpenAI."


def extract_confidence_score(result):
    """Version robuste avec debug pour extraction du score"""
    try:
        if not result:
            print("DEBUG: Résultat vide pour extraction score")
            return 0.7  # Score par défaut plus élevé
            
        result_str = str(result).lower()
        print(f"DEBUG: Extraction score depuis: {result_str[:100]}...")
        
        # Patterns améliorés
        patterns = [
            (r'score.*?(?:de\s+)?fiabilité.*?(\d+)%', "Score de fiabilité X%"),
            (r'fiabilité.*?(\d+)%', "Fiabilité: X%"), 
            (r'score.*?(\d+)%', "Score: X%"),
            (r'(\d+)%', "X%"),
            (r'score.*?(\d+(?:\.\d+)?)', "Score: 0.X"),
            (r'confiance.*?(\d+(?:\.\d+)?)', "Confiance: 0.X"),
        ]
        
        for pattern, description in patterns:
            matches = re.findall(pattern, result_str)
            if matches:
                try:
                    score = float(matches[0])
                    if score > 1:
                        score = score / 100
                    score = min(max(score, 0.0), 1.0)
                    print(f"DEBUG: Score extrait via '{description}': {score}")
                    return score
                except (ValueError, IndexError):
                    continue
                    
        print("DEBUG: Aucun score trouvé, utilisation score par défaut")
        return 0.7  # 70% par défaut
        
    except Exception as e:
        print(f"DEBUG: Erreur extraction score: {e}")
        return 0.7

@login_required
def analysis_detail_view(request, analysis_id):
    """Vue détail d'une analyse spécifique"""
    analysis = get_object_or_404(Analysis, pk=analysis_id, user=request.user)
    
    # Métadonnées pour affichage
    context = {
        'analysis': analysis,
        'confidence_percentage': round(analysis.confidence_score * 100, 1),
        'page_title': f'Analyse #{analysis.pk}',
        'created_date': analysis.created_at.strftime('%d/%m/%Y à %H:%M'),
        'word_count': len(analysis.text.split()),
        'result_word_count': len(analysis.result.split()),
    }
    
    return render(request, 'dashboard/analysis_detail.html', context)



def _auto_index_analysis(analysis_obj):
    """Auto-indexation de l'analyse dans Azure AI Search pour enrichir la base RAG"""
    try:
        if not RAG_AVAILABLE:
            return False
            
        analysis_id = getattr(analysis_obj, 'id', 'ID inconnu')
        print(f"Auto-indexation de l'analyse ID: {analysis_id}")
        
        # Initialiser l'indexeur
        indexer = FactGuardContentIndexer()
        
        # Indexer l'analyse
        success = indexer.index_analysis(analysis_obj)
        
        if success:
            print(f"Analyse {analysis_id} indexée avec succès")
        else:
            print(f"Échec indexation analyse {analysis_id}")
            
        return success
        
    except Exception as e:
        print(f"Erreur auto-indexation: {e}")
        return False


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
    """Vue historique avec diagnostic et calculs robustes"""
    
    user = request.user
    
    # Récupération complète avec debug
    all_analyses = Analysis.objects.filter(user=user).order_by('-created_at')
    total_count = all_analyses.count()
    
    print(f"DEBUG HISTORY: User {user.username} - {total_count} analyses trouvées")
    
    if not all_analyses.exists():
        print("DEBUG HISTORY: Aucune analyse trouvée")
        return render(request, 'dashboard/history.html', {
            'analyses_recent': [],
            'analyses_all': [],
            'total_count': 0,
        })
    
    # Vérification des scores pour diagnostic
    scores = [a.confidence_score for a in all_analyses[:5]]
    print(f"DEBUG HISTORY: Scores des 5 dernières analyses: {scores}")
    
    # Test des propriétés du modèle
    first_analysis = all_analyses.first()
    if first_analysis:
        print(f"DEBUG HISTORY: Première analyse - Score: {first_analysis.confidence_score}, "
                f"Niveau: {first_analysis.reliability_level}, "
                f"Type: {first_analysis.type_display}")
    
    # Analyses récentes (5 dernières)
    analyses_recent = all_analyses[:5]
    
    # Statistiques pour debug
    avg_score = sum(a.confidence_score for a in all_analyses) / total_count if total_count > 0 else 0
    reliable_count = sum(1 for a in all_analyses if a.confidence_score >= 0.6)
    
    print(f"DEBUG HISTORY: Score moyen: {avg_score:.3f}, Analyses fiables: {reliable_count}/{total_count}")
    
    context = {
        'analyses_recent': analyses_recent,
        'analyses_all': all_analyses,
        'total_count': total_count,
        # Ajout de statistiques pour le template
        'avg_confidence': round(avg_score * 100, 1) if avg_score else 0,
        'reliable_percentage': round((reliable_count / total_count * 100), 1) if total_count > 0 else 0,
    }
    
    return render(request, 'dashboard/history.html', context)

@login_required
def statistics_view(request):
    """Vue statistiques avec calculs c"""
    
    # Analyses totales
    total_analyses = Analysis.objects.count()
    
    # Score moyen (conversion 0-1 vers 0-100%)
    avg_score_raw = Analysis.objects.aggregate(Avg('confidence_score'))['confidence_score__avg']
    avg_score = round(avg_score_raw * 100, 1) if avg_score_raw else 0
    
    # Contenu fiable (score >= 0.6 = 60%)
    reliable_analyses = Analysis.objects.filter(confidence_score__gte=0.6).count()
    reliable_content = round((reliable_analyses / total_analyses * 100), 1) if total_analyses > 0 else 0
    
    # Analyses par type
    type_stats = {
        'text': Analysis.objects.filter(content_type='text').count(),
        'link': Analysis.objects.filter(content_type='link').count(),
        'image': Analysis.objects.filter(content_type='image').count(),
    }
    
    # Pourcentages par type
    type_percentages = {}
    if total_analyses > 0:
        type_percentages = {
            'text_percent': round((type_stats['text'] / total_analyses * 100), 1),
            'link_percent': round((type_stats['link'] / total_analyses * 100), 1),
            'image_percent': round((type_stats['image'] / total_analyses * 100), 1),
        }
    else:
        type_percentages = {'text_percent': 0, 'link_percent': 0, 'image_percent': 0}
    
    # Statistiques supplémentaires
    analyses_today = Analysis.objects.filter(created_at__date=date.today()).count()
    last_analysis = Analysis.objects.first()  # Plus récente grâce à ordering
    
    simple_stats = {
        'reliable_content': reliable_content,
        'analyses_today': analyses_today,
        'ai_model': 'Azure OpenAI',
        'last_analysis': last_analysis.created_at.strftime('%d/%m/%Y %H:%M') if last_analysis else 'Aucune analyse'
    }
    
    context = {
        'total_analyses': total_analyses,
        'avg_score': avg_score,  # Maintenant en pourcentage
        'simple_stats': simple_stats,
        'type_stats': type_stats,
        'type_percentages': type_percentages,
    }
    
    return render(request, 'dashboard/statistics.html', context)


@login_required
def delete_analysis_view(request, analysis_id):
    """Vue pour supprimer une analyse spécifique avec confirmation"""
    analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
    
    if request.method == 'POST':
        analysis.delete()
        messages.success(request, "Analyse supprimée avec succès !")
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
        messages.success(request, f"{deleted_count} analyses supprimées avec succès !")
        return redirect('dashboard:history')
    
    return render(request, 'dashboard/confirm_delete.html', {
        'analyses_count': total_count,
        'title': "Vider tout l'historique"
    })



logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

def health(request):
    logger.info(" Health endpoint called")
    with tracer.start_as_current_span("factguard.health") as span:
        span.set_attribute("feature", "health_check")
    return HttpResponse("OK", content_type="text/plain")