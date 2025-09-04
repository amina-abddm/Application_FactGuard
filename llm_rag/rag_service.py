# api/services/rag_service.py
from typing import Dict, List, Any
from .azure_ai_search_service import FactGuardSearchService
from .azure_openai_service import AzureOpenAIService
import logging

logger = logging.getLogger(__name__)

class RAGService:
    """Service RAG amélioré pour FactGuard avec Azure AI Search"""
    
    def __init__(self):
        self.search_service = FactGuardSearchService()
        self.openai_service = AzureOpenAIService()
    
    def analyze_with_context(self, query: str, analysis_type: str = "reliability") -> Dict[str, Any]:
        """
        Analyse enrichie avec contexte de sources fiables
        
        Args:
            query: Information à analyser
            analysis_type: Type d'analyse (reliability, fact_check, bias_detection)
        """
        try:
            # 1. Recherche hybride de sources pertinentes
            relevant_sources = self._search_relevant_sources(query, top_k=5)
            
            # 2. Construction du contexte enrichi
            context = self._build_enhanced_context(relevant_sources, analysis_type)
            
            # 3. Génération de l'analyse avec prompt spécialisé
            analysis_result = self._perform_contextual_analysis(
                query, context, analysis_type, relevant_sources
            )
            
            return {
                'analysis_result': analysis_result,
                'sources_count': len(relevant_sources),
                'context_used': context[:500],
                'sources': [
                    {
                        'title': source.get('title', 'Source inconnue'),
                        'url': source.get('url', ''),
                        'reliability_score': source.get('reliability_score', 0),
                        'relevance_score': source.get('@search.score', 0)
                    }
                    for source in relevant_sources
                ],
                'analysis_confidence': self._calculate_confidence(relevant_sources)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur RAG enrichi: {e}")
            return {
                'analysis_result': f"Erreur lors de l'analyse contextuelle: {str(e)}",
                'sources_count': 0,
                'context_used': '',
                'sources': [],
                'analysis_confidence': 0.0
            }
    
    def _search_relevant_sources(self, query: str, top_k: int = 5) -> List[Dict]:
        """Recherche hybride de sources pertinentes"""
        try:
            # ✅ CORRECTION : Vérification de sécurité
            if not self.search_service or not hasattr(self.search_service, 'search_client') or not self.search_service.search_client:
                logger.warning("❌ Azure Search client non disponible")
                return []
            
            # Recherche hybride (texte + vecteur sémantique)
            results = self.search_service.search_client.search(
                search_text=query,
                top=top_k,
                search_mode="all",
                include_total_count=True,
                select=["title", "content", "url", "source", "reliability_score", "category", "date_published"],
                highlight_fields="content,title",  # ✅ CORRECTION : String au lieu de liste
                # semantic_configuration_name="default",  # ✅ Commenté temporairement
                # query_type="semantic"  # ✅ Commenté temporairement
            )
            
            sources = []
            for result in results:
                sources.append({
                    'title': result.get('title', ''),
                    'content': result.get('content', '')[:1000],
                    'url': result.get('url', ''),
                    'source': result.get('source', ''),
                    'reliability_score': result.get('reliability_score', 0),
                    'category': result.get('category', ''),
                    'date_published': result.get('date_published', ''),
                    '@search.score': result.get('@search.score', 0.0),
                    '@search.highlights': result.get('@search.highlights', {})
                })
            
            logger.info(f"🔍 Trouvé {len(sources)} sources pertinentes")
            return sources
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche sources: {e}")
            return []
    
    def _build_enhanced_context(self, sources: List[Dict], analysis_type: str) -> str:
        """Construit un contexte enrichi selon le type d'analyse"""
        if not sources:
            return "Aucune source contextuelle disponible."
        
        context_parts = [
            f"=== CONTEXTE FACTGUARD - ANALYSE DE {analysis_type.upper()} ===\n"
        ]
        
        for i, source in enumerate(sources, 1):
            reliability = source.get('reliability_score', 0)
            reliability_level = "ÉLEVÉE" if reliability > 0.8 else "MOYENNE" if reliability > 0.6 else "FAIBLE"
            
            context_parts.append(f"""
SOURCE {i} - Fiabilité: {reliability_level} ({reliability:.2f})
Titre: {source.get('title', 'N/A')}
Source: {source.get('source', 'N/A')}
Catégorie: {source.get('category', 'N/A')}
Date: {source.get('date_published', 'N/A')[:10]}
Contenu: {source.get('content', '')[:400]}...
Score de pertinence: {source.get('@search.score', 0):.2f}
---""")
        
        return "\n".join(context_parts)
    
    def _perform_contextual_analysis(self, query: str, context: str, 
                                   analysis_type: str, sources: List[Dict]) -> str:
        """Effectue l'analyse avec le contexte enrichi"""
        
        # Prompts spécialisés selon le type d'analyse
        specialized_prompts = {
            "reliability": """
Tu es un expert en vérification des faits pour FactGuard. Analyse la fiabilité de l'information fournie en utilisant le contexte de sources fiables disponibles.

INSTRUCTIONS SPÉCIFIQUES:
1. Compare l'information à analyser avec les sources contextuelles fournies
2. Identifie les concordances et divergences avec les sources fiables
3. Évalue la crédibilité basée sur la cohérence des sources
4. Détecte les signaux d'alarme (dates incohérentes, sources peu fiables, etc.)
5. Fournis un score de fiabilité justifié et des recommandations""",
            
            "fact_check": """
Tu es un fact-checker professionnel utilisant FactGuard. Vérifie les faits contenus dans l'information en t'appuyant sur les sources contextuelles.

FOCUS SUR:
1. Vérification factuelle point par point
2. Identification des éléments vérifiables vs opinions
3. Comparaison avec les données factuelles des sources
4. Signalement des informations non vérifiées
5. Classification: VRAI / PARTIELLEMENT VRAI / FAUX / NON VÉRIFIABLE""",
            
            "bias_detection": """
Tu es un analyste de biais informationnels pour FactGuard. Détecte les biais potentiels dans l'information en utilisant le contexte de sources diversifiées.

ANALYSE DES BIAIS:
1. Biais de confirmation dans la présentation
2. Sélectivité des faits présentés
3. Langage orienté ou émotionnel
4. Omissions significatives
5. Perspective unique vs multiple points de vue"""
        }
        
        system_prompt = specialized_prompts.get(analysis_type, specialized_prompts["reliability"])
        
        enhanced_prompt = f"""
{system_prompt}

CONTEXTE DE SOURCES FIABLES:
{context}

INFORMATION À ANALYSER:
{query}

CONSIGNE: Utilise OBLIGATOIREMENT le contexte fourni pour enrichir ton analyse. Cite les sources utilisées et justifie ton évaluation.

Réponds selon le format FactGuard habituel avec emojis et structure claire.
"""
        
        return self.openai_service.analyze_information(enhanced_prompt, content_type='text')
    
    def _calculate_confidence(self, sources: List[Dict]) -> float:
        """Calcule le niveau de confiance basé sur les sources"""
        if not sources:
            return 0.0
        
        # Facteurs de confiance
        avg_reliability = sum(s.get('reliability_score', 0) for s in sources) / len(sources)
        source_diversity = len(set(s.get('source', '') for s in sources)) / len(sources)
        avg_relevance = sum(s.get('@search.score', 0) for s in sources) / len(sources)
        
        # Score de confiance pondéré
        confidence = (avg_reliability * 0.5 + source_diversity * 0.3 + (avg_relevance/100) * 0.2)
        return min(confidence, 1.0)  # Plafonner à 1.0

    def get_similar_analyses(self, query: str, limit: int = 5) -> List[Dict]:
        """Recherche d'analyses similaires (implémentation pour le protocole)"""
        try:
            return self._search_relevant_sources(query, top_k=limit)
        except Exception as e:
            logger.error(f"❌ Erreur recherche analyses similaires: {e}")
            return []
