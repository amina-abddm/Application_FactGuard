from services.search.azure_search import AzureSearchService
from api.services.azure_openai_service import AzureOpenAIService 
class EnhancedRAGService:
    def __init__(self):
        self.search_service = AzureSearchService()
        self.openai_service = AzureOpenAIService()  #  Utiliser le service

    def analyze_with_context(self, user_query):
        """Analyse RAG avec prompt optimisé pour une meilleure intégration du contexte"""
        
        try:
            # 1. Recherche contextuelle dans Azure AI Search
            search_results = self.search_service.search_analyses(user_query, top=5)
            
            # 2. Vérifier si on a du contexte pertinent
            if not search_results:
                fallback_prompt = f"""
Tu es FactGuard, un expert en vérification d'informations.

INFORMATION À ANALYSER :
{user_query}

INSTRUCTION :
Effectue une analyse de fact-checking standard car aucune analyse similaire n'a été trouvée dans l'historique.

Fournis ton analyse sous ce format :
- **Évaluation** : [Vraie/Fausse/Partiellement vraie/Impossible à vérifier]
- **Explication** : [Explication détaillée]
- **Score de confiance** : [0-100]%
- **Sources recommandées** : [Types de sources à consulter]
- **Note** : Analyse effectuée sans contexte historique
                """
                
                
                result = self.openai_service.analyze_information(fallback_prompt)
                
                return {
                    'analysis_result': result,
                    'context_used': "Aucun contexte historique trouvé - Analyse standard effectuée",
                    'sources_count': 0,
                    'search_query': user_query,
                    'mode': 'standard'
                }
            
            # 3. Construire un contexte riche et structuré
            context_sections = []
            for i, result in enumerate(search_results, 1):
                context_section = f"""
ANALYSE #{i} (Score: {result.get('confidence_score', 'N/A')}) :
• Contenu analysé : {result['content'][:400]}
• Verdict précédent : {result['analysis_result'][:300]}
• Analysé par : {result.get('username', 'Utilisateur')}
• Date : {result.get('created_at', 'Date inconnue')}
---"""
                context_sections.append(context_section)
            
            rich_context = "\n".join(context_sections)
            
            # 4. Prompt optimisé avec instructions spécifiques
            enhanced_prompt = f"""
Tu es FactGuard Pro, système expert de fact-checking avec accès à une base d'analyses historiques.

=== CONTEXTE HISTORIQUE PERTINENT ===
{rich_context}

=== NOUVELLE INFORMATION À ANALYSER ===
{user_query}

=== INSTRUCTIONS SPÉCIFIQUES ===
1. COMPARE cette nouvelle information avec les analyses historiques ci-dessus
2. IDENTIFIE les similitudes, contradictions ou patterns récurrents
3. UTILISE l'expertise accumulée pour enrichir ton évaluation
4. CITE les analyses précédentes pertinentes (ex: "Comme observé dans l'Analyse #2...")
5. JUSTIFIE ton verdict en t'appuyant sur le contexte historique

=== FORMAT DE RÉPONSE OBLIGATOIRE ===
**🔍 ANALYSE COMPARATIVE :**
[Comparaison avec les analyses historiques similaires]

**📊 VERDICT ENRICHI :**
[Évaluation basée sur l'expertise accumulée]

**🎯 SCORE DE CONFIANCE :**
[0-100]% (justifié par l'historique)

**📚 SOURCES CONTEXTUELLES :**
[Références aux analyses précédentes utilisées]

**💡 INSIGHTS SUPPLÉMENTAIRES :**
[Patterns détectés ou recommandations basées sur l'historique]

IMPORTANT : Tu DOIS utiliser et citer le contexte historique dans ta réponse.
            """
            
            # 5. Appel GPT-4o avec le prompt optimisé
            result = self.openai_service.analyze_information(enhanced_prompt)
            
            return {
                'analysis_result': result,
                'context_used': rich_context,
                'sources_count': len(search_results),
                'search_query': user_query,
                'enhanced_prompt': enhanced_prompt,
                'mode': 'rag_enhanced'
            }
            
        except Exception as e:
            # Fallback en cas d'erreur
            return {
                'analysis_result': f"Erreur lors de l'analyse RAG. Analyse standard pour: {user_query}",
                'context_used': f"Erreur: {str(e)}",
                'sources_count': 0,
                'error': str(e),
                'mode': 'error_fallback'
            }

       # ✅ AJOUT : Méthode manquante pour respecter le protocole
    def get_similar_analyses(self, query: str, limit: int = 5) -> List[Dict]:
        """Recherche d'analyses similaires dans l'historique"""
        try:
            # Utiliser Azure AI Search pour trouver des analyses similaires
            similar_sources = self._search_relevant_sources(query, top_k=limit)
            
            # Formatter les résultats pour correspondre au protocole
            similar_analyses = []
            for source in similar_sources:
                similar_analyses.append({
                    'content': source.get('content', ''),
                    'confidence_score': source.get('reliability_score', 0),
                    'title': source.get('title', ''),
                    'url': source.get('url', ''),
                    'relevance_score': source.get('@search.score', 0)
                })
            
            return similar_analyses
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche analyses similaires: {e}")
            return []

# Alias pour compatibilité (si utilisé)
RAGService = EnhancedRAGService