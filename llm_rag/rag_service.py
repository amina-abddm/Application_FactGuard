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
            relevant_sources = self._search_relevant_sources(query, top_k=10)

            context = self._build_enhanced_context(relevant_sources, analysis_type)

            analysis_result = self._perform_contextual_analysis(
                query, context, analysis_type, relevant_sources
            )

            return {
                "analysis_result": analysis_result,
                "sources_count": len(relevant_sources),
                "context_used": context[:500],
                "sources": [
                    {
                        "title": src.get("title") or "Source inconnue",
                        "url": src.get("url") or "",
                        "reliability_score": src.get("reliability_score") or 0,
                        "relevance_score": src.get("@search.score") or 0.0,
                    }
                    for src in relevant_sources
                ],
                "analysis_confidence": self._calculate_confidence(relevant_sources),
            }

        except Exception as e:
            logger.error(f"Erreur RAG enrichi: {e}")
            return {
                "analysis_result": f"Erreur lors de l'analyse contextuelle: {str(e)}",
                "sources_count": 0,
                "context_used": "",
                "sources": [],
                "analysis_confidence": 0.0,
            }

    # ============================================================
    # 🔎 1. RECHERCHE DES SOURCES AZURE SEARCH
    # ============================================================
    
    def _search_relevant_sources(self, query: str, top_k: int = 10) -> List[Dict]:
        try:
            logger.info(f"[RAG] Recherche de sources pour: {query}")

            if not self.search_service or not self.search_service.search_client:
                logger.error("Client Azure Search indisponible")
                return []

            # Recherche simple pour éviter les erreurs
            results = self.search_service.search_client.search(
                search_text=query,
                top=top_k,
                search_mode="any",
                include_total_count=True,
                select=[
                    "id", "title", "content", "url",
                    "source", "reliability_score",
                    "date_published"
                ]
            )

            sources = []
            for item in results:
                sources.append({
                    "id": item.get("id") or "",
                    "title": item.get("title") or "",
                    "content": (item.get("content") or "")[:1000],
                    "url": item.get("url") or "",
                    "source": item.get("source") or "",
                    "reliability_score": item.get("reliability_score") or 0,
                    "date_published": item.get("date_published") or "",
                    "@search.score": item.get("@search.score") or 0.0,
                })

            logger.info(f"[RAG] {len(sources)} sources trouvées")
            return sources

        except Exception as e:
            logger.error(f"Erreur dans la recherche Azure Search: {e}")
            return []

    # ============================================================
    # 🧠 2. CONSTRUCTION CONTEXTE – VERSION 100% FIXED
    # ============================================================

    def _build_enhanced_context(self, sources: List[Dict], analysis_type: str) -> str:
        """Construit un contexte enrichi et SANS ERREURS NoneType"""

        if not sources:
            return "Aucune source contextuelle disponible."

        context_parts = [
            f"=== CONTEXTE FACTGUARD - ANALYSE {analysis_type.upper()} ===",
            f"{len(sources)} sources trouvées.",
            ""
        ]

        for i, src in enumerate(sources, 1):

            reliability = src.get("reliability_score") or 0.0
            score = src.get("@search.score") or 0.0

            # Niveau de fiabilité
            if reliability > 0.8:
                level = "ÉLEVÉE"
            elif reliability > 0.6:
                level = "MOYENNE"
            else:
                level = "FAIBLE"

            context_parts.append(
                f"""
SOURCE {i}
Fiabilité: {level} ({reliability:.2f})
Titre: {src.get("title") or "N/A"}
Source: {src.get("source") or "N/A"}
Date: {(src.get("date_published") or "")[:10]}
Contenu: {(src.get("content") or "")[:400]}...
Pertinence: {score:.2f}
--------------------
"""
            )

        return "\n".join(context_parts)

    # ============================================================
    # 🧠 3. ANALYSE PAR AZURE OPENAI
    # ============================================================

    def _perform_contextual_analysis(self, query: str, context: str,
                                     analysis_type: str, sources: List[Dict]) -> str:
        logger.info(f"[RAG] Analyse avec {len(sources)} sources…")

        prompt = f"""
Tu es un expert FactGuard. Analyse le contenu en te basant STRICTEMENT sur les sources ci-dessous.

=== CONTEXTE SOURCES ===
{context}

=== INFORMATION À ANALYSER ===
{query}

Réponds en citant les sources utilisées et en évaluant la fiabilité de l'information.
"""

        return self.openai_service.analyze_information(prompt)

    # ============================================================
    # 📊 4. CALCUL DU SCORE DE CONFIANCE – VERSION FIXED
    # ============================================================

    def _calculate_confidence(self, sources: List[Dict]) -> float:
        if not sources:
            return 0.0

        reliability_values = [(s.get("reliability_score") or 0.0) for s in sources]
        relevance_values = [(s.get("@search.score") or 0.0) for s in sources]
        diversity = len(set(s.get("source") or "" for s in sources))

        avg_reliability = sum(reliability_values) / len(sources)
        avg_relevance = sum(relevance_values) / len(sources)

        confidence = (
            avg_reliability * 0.5 +
            (diversity / len(sources)) * 0.3 +
            (avg_relevance / 100) * 0.2
        )

        return min(confidence, 1.0)

    # ============================================================
    # 🔁 5. ANALYSES SIMILAIRES
    # ============================================================

    def get_similar_analyses(self, query: str, limit: int = 5) -> List[Dict]:
        try:
            return self._search_relevant_sources(query, top_k=limit)
        except Exception as e:
            logger.error(f"Erreur recherche analyses similaires: {e}")
            return []
