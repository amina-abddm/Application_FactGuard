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
        """Analyse enrichie avec contexte de sources fiables"""
        try:
            # Recherche de sources pertinentes avec diagnostic
            relevant_sources = self._search_relevant_sources(query, top_k=10)
            
            # Construction du contexte enrichi
            context = self._build_enhanced_context(relevant_sources, analysis_type)
            
            # Génération de l'analyse avec prompt spécialisé
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
            logger.error(f"Erreur RAG enrichi: {e}")
            return {
                'analysis_result': f"Erreur lors de l'analyse contextuelle: {str(e)}",
                'sources_count': 0,
                'context_used': '',
                'sources': [],
                'analysis_confidence': 0.0
            }
    
    def _search_relevant_sources(self, query: str, top_k: int = 10) -> List[Dict]:
        """Recherche de sources pertinentes avec diagnostic complet"""
        try:
            # DIAGNOSTIC DETAILLE
            logger.info(f"=== DIAGNOSTIC RECHERCHE RAG ===")
            logger.info(f"Query: {query}")
            logger.info(f"Top_k: {top_k}")
            
            # Vérification du client
            if not self.search_service or not hasattr(self.search_service, 'search_client') or not self.search_service.search_client:
                logger.error(" Azure Search client NON DISPONIBLE")
                return []
            
            logger.info(" Client Azure Search disponible")
            
            # Test de connexion basique
            try:
                test_results = self.search_service.search_client.search(
                    search_text="*", 
                    top=1,
                    include_total_count=True
                )
                total_docs = getattr(test_results, 'get_count', lambda: 'Unknown')()
                logger.info(f" Documents dans l'index: {total_docs}")
            except Exception as test_e:
                logger.error(f" Erreur test connexion: {test_e}")
            
            # Recherche SIMPLIFIEE et moins restrictive
            logger.info(f" Recherche pour: '{query}'")
            
            results = self.search_service.search_client.search(
                search_text=query,
                top=top_k,
                search_mode="any",  # CHANGEMENT: "any" au lieu de "all"
                include_total_count=True,
                select=["id", "title", "content", "url", "source", "reliability_score", "date_published"],
                # SUPPRESSION highlight_fields qui peut causer des erreurs
                # highlight_fields="content,title",
            )
            
            sources = []
            result_count = 0
            
            for result in results:
                result_count += 1
                source_dict = {
                    'id': result.get('id', ''),
                    'title': result.get('title', ''),
                    'content': result.get('content', '')[:1000],
                    'url': result.get('url', ''),
                    'source': result.get('source', ''),
                    'reliability_score': result.get('reliability_score', 0),
                    'date_published': result.get('date_published', ''),
                    '@search.score': result.get('@search.score', 0.0),
                }
                sources.append(source_dict)
                
                # LOG DETAILLE CHAQUE SOURCE
                logger.info(f"   Source {result_count}:")
                logger.info(f"   ID: {source_dict['id']}")
                logger.info(f"   Title: {source_dict['title'][:60]}...")
                logger.info(f"   Source: {source_dict['source']}")
                logger.info(f"   Score: {source_dict['@search.score']:.2f}")
            
            logger.info(f" TOTAL SOURCES TROUVEES: {len(sources)}")
            
            if len(sources) == 0:
                logger.warning(" AUCUNE SOURCE TROUVEE")
                logger.warning("   Testez avec query='*' pour voir tous les documents")
                
                # Test de secours avec requête générale
                try:
                    fallback_results = self.search_service.search_client.search(
                        search_text="*",
                        top=3,
                        select=["id", "title", "source"]
                    )
                    logger.info(" Exemples de documents dans l'index:")
                    for i, doc in enumerate(fallback_results, 1):
                        logger.info(f"   {i}. {doc.get('title', 'N/A')[:50]} - {doc.get('source', 'N/A')}")
                except Exception as fallback_e:
                    logger.error(f" Erreur test fallback: {fallback_e}")
            
            return sources
            
        except Exception as e:
            logger.error(f" ERREUR recherche sources: {e}")
            logger.error(f"Type erreur: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _build_enhanced_context(self, sources: List[Dict], analysis_type: str) -> str:
        """Construit un contexte enrichi selon le type d'analyse"""
        if not sources:
            logger.warning(" Aucune source pour construire le contexte")
            return "Aucune source contextuelle disponible."
        
        logger.info(f" Construction contexte avec {len(sources)} sources")
        
        context_parts = [
            f"=== CONTEXTE FACTGUARD - ANALYSE DE {analysis_type.upper()} ===",
            f" {len(sources)} sources analysées",
            ""
        ]
        
        for i, source in enumerate(sources, 1):
            reliability = source.get('reliability_score', 0)
            reliability_level = "ÉLEVÉE" if reliability > 0.8 else "MOYENNE" if reliability > 0.6 else "FAIBLE"
            
            context_parts.append(f"""
SOURCE {i} - Fiabilité: {reliability_level} ({reliability:.2f})
Titre: {source.get('title', 'N/A')}
Source: {source.get('source', 'N/A')}
Date: {source.get('date_published', 'N/A')[:10]}
Contenu: {source.get('content', '')[:400]}...
Score de pertinence: {source.get('@search.score', 0):.2f}
---""")
        
        context = "\n".join(context_parts)
        logger.info(f" Contexte construit: {len(context)} caractères")
        return context
    
    def _perform_contextual_analysis(self, query: str, context: str, 
                                analysis_type: str, sources: List[Dict]) -> str:
        """Effectue l'analyse avec le contexte enrichi"""
        
        logger.info(f" Analyse avec {len(sources)} sources contextuelles")
        
        # Prompts spécialisés
        specialized_prompts = {
            "reliability": """
Tu es un expert en vérification des faits pour FactGuard. Analyse la fiabilité de l'information fournie en utilisant le contexte de sources fiables disponibles.

INSTRUCTIONS SPÉCIFIQUES:
1. Compare l'information à analyser avec les sources contextuelles fournies
2. Identifie les concordances et divergences avec les sources fiables
3. Évalue la crédibilité basée sur la cohérence des sources
4. Détecte les signaux d'alarme (dates incohérentes, sources peu fiables, etc.)
5. Fournis un score de fiabilité justifié et des recommandations

FORMAT OBLIGATOIRE:
📈 Score de fiabilité: XX/100
📝 Analyse détaillée: [Explication avec preuves des sources]
🔗 Sources consultées: [Liste des sources utilisées]
✅/❌ VERDICT: [FIABLE/DOUTEUX/FAUX]
""",
            
            "fact_check": """
Tu es un fact-checker professionnel utilisant FactGuard. Vérifie les faits contenus dans l'information en t'appuyant sur les sources contextuelles.

FOCUS SUR:
1. Vérification factuelle point par point
2. Identification des éléments vérifiables vs opinions
3. Comparaison avec les données factuelles des sources
4. Signalement des informations non vérifiées
5. Classification: VRAI / PARTIELLEMENT VRAI / FAUX / NON VÉRIFIABLE
""",
        }
        
        system_prompt = specialized_prompts.get(analysis_type, specialized_prompts["reliability"])
        
        enhanced_prompt = f"""
{system_prompt}

CONTEXTE DE SOURCES FIABLES:
{context}

INFORMATION À ANALYSER:
{query}

CONSIGNE: Utilise OBLIGATOIREMENT le contexte fourni pour enrichir ton analyse. Cite les sources utilisées et justifie ton évaluation.
"""
        
        result = self.openai_service.analyze_information(enhanced_prompt, content_type='text')
        logger.info(f" Analyse terminée avec contexte de {len(sources)} sources")
        return result
    
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
        return min(confidence, 1.0)

    def get_similar_analyses(self, query: str, limit: int = 5) -> List[Dict]:
        """Recherche d'analyses similaires"""
        try:
            return self._search_relevant_sources(query, top_k=limit)
        except Exception as e:
            logger.error(f"Erreur recherche analyses similaires: {e}")
            return []
