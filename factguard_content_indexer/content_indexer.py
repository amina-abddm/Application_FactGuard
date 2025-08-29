import openai
from azure_ai_search_service import FactGuardSearchService
from .azure_openai_service import AzureOpenAIService
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FactGuardContentIndexer:
    """Service d'indexation de contenu pour FactGuard"""
    
    def __init__(self):
        self.search_service = FactGuardSearchService()
        if not hasattr(self.search_service, "search_client") or self.search_service.search_client is None:
            raise ValueError("FactGuardSearchService.search_client is not initialized. Please check your FactGuardSearchService implementation.")
        self.openai_service = AzureOpenAIService()
    
    def generate_embedding(self, text: str) -> List[float]:
        """Génère un embedding pour le texte donné"""
        try:
            response = self.openai_service.client.embeddings.create(
                model="text-embedding-ada-002",  #   modèle d'embedding déployé
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Erreur génération embedding: {e}")
            return []
    
    def index_article(self, title: str, content: str, url: str = "", 
                    source: str = "", category: str = "", tags: Optional[List[str]] = None):
        """Indexe un article dans Azure AI Search"""
        try:
            # Génération de l'embedding
            full_text = f"{title} {content}"
            content_vector = self.generate_embedding(full_text)
            
            if not content_vector:
                logger.error("Impossible de générer l'embedding")
                return False
            
            # Création du document
            document = {
                "id": hashlib.md5(f"{url}{title}".encode()).hexdigest(),
                "title": title,
                "content": content,
                "url": url,
                "date_published": datetime.now().isoformat(),
                "source": source,
                "reliability_score": 0.8,  # Score par défaut
                "category": category,
                "tags": tags if tags is not None else [],
                "content_vector": content_vector
            }
            
            # Vérification de l'initialisation du search_client
            if not hasattr(self.search_service, "search_client") or self.search_service.search_client is None:
                logger.error("search_client non initialisé")
                return False

            # Indexation
            result = self.search_service.search_client.upload_documents([document])
            
            if result[0].succeeded:
                logger.info(f" Article indexé: {title[:50]}...")
                return True
            else:
                logger.error(f" Échec indexation: {result[0].error_message}")
                return False
                
        except Exception as e:
            logger.error(f" Erreur indexation article: {e}")
            return False
    
    def batch_index_articles(self, articles: List[Dict]):
        """Indexe plusieurs articles en lot"""
        success_count = 0
        for article in articles:
            if self.index_article(**article):
                success_count += 1
        
        logger.info(f" {success_count}/{len(articles)} articles indexés")
        return success_count
