import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from datetime import datetime, timedelta
import hashlib
import feedparser
from typing import List, Dict, Any, Optional

class FactGuardContentIndexer:
    """Service d'indexation pour FactGuard avec Azure AI Search"""
    
    def __init__(self):
        # Configuration Azure AI Search depuis les variables d'environnement
        self.service_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.admin_key = os.getenv('AZURE_SEARCH_ADMIN_KEY') 
        self.index_name = os.getenv('AZURE_SEARCH_INDEX_NAME', 'factguard-index')
        
        if not self.service_endpoint or not self.admin_key:
            raise ValueError("Variables d'environnement Azure Search manquantes")
        
        # Initialisation du client Azure Search
        credential = AzureKeyCredential(self.admin_key)
        
        # Client pour les opérations sur les documents
        self.search_client = SearchClient(
            endpoint=self.service_endpoint,
            index_name=self.index_name,
            credential=credential
        )
        
        # Client pour les opérations sur l'index
        self.index_client = SearchIndexClient(
            endpoint=self.service_endpoint,
            credential=credential
        )
        
        print(f"FactGuardContentIndexer initialisé - Index: {self.index_name}")
    
    def upload_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Upload de documents vers Azure AI Search"""
        try:
            result = self.search_client.upload_documents(documents=documents)
            
            success_count = sum(1 for r in result if r.succeeded)
            total_count = len(result)
            
            print(f"Upload terminé: {success_count}/{total_count} documents")
            return success_count == total_count
            
        except Exception as e:
            print(f"Erreur upload documents: {e}")
            return False
    
    def index_analysis(self, analysis_obj: Any) -> bool:
        """Indexe automatiquement une analyse FactGuard"""
        try:
            print(f"Indexation de l'analyse ID: {analysis_obj.id}")
            
            # Convertir l'analyse en document Azure Search
            document = analysis_obj.to_search_document()
            
            # Upload du document
            result = self.search_client.upload_documents([document])
            
            # Vérification sécurisée du résultat
            if len(result) > 0 and hasattr(result[0], 'succeeded'):
                if result[0].succeeded:
                    print(f"Analyse {analysis_obj.id} indexée avec succès")
                    return True
                else:
                    error_msg = getattr(result[0], 'error_message', 'Erreur inconnue')
                    print(f"Échec indexation analyse {analysis_obj.id}: {error_msg}")
                    return False
            else:
                print(f"Analyse {analysis_obj.id} indexée (succès présumé)")
                return True
                
        except Exception as e:
            print(f"Erreur indexation analyse {analysis_obj.id}: {e}")
            return False
    
    def search_similar_analyses(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Recherche d'analyses similaires pour le RAG"""
        try:
            print(f"Recherche similaire pour: {query[:50]}...")
            
            # Recherche avec Azure AI Search
            results = self.search_client.search(
                search_text=query,
                top=top_k,
                select=[
                    "id", "text", "result", "confidence_score", 
                    "content_type", "created_at", "reliability_level"
                ],
                search_fields=["text", "result"],
                filter="confidence_score ge 0.4",
                query_type="simple"
            )
            
            # Formatage des résultats
            formatted_results: List[Dict[str, Any]] = []
            for result in results:
                result_dict = dict(result)
                formatted_results.append({
                    'id': result_dict.get('id', ''),
                    'text': result_dict.get('text', ''),
                    'result': result_dict.get('result', ''),
                    'confidence_score': float(result_dict.get('confidence_score', 0)),
                    'content_type': result_dict.get('content_type', 'text'),
                    'created_at': result_dict.get('created_at', ''),
                    'reliability_level': result_dict.get('reliability_level', ''),
                    'search_score': result_dict.get('@search.score', 0)
                })
            
            print(f"{len(formatted_results)} analyses similaires trouvées")
            return formatted_results
            
        except Exception as e:
            print(f"Erreur recherche similaire: {e}")
            return []
    
    def search_documents(self, query: str, top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Recherche générique de documents"""
        try: 
            search_params: Dict[str, Any] = {
                "search_text": query,
                "top": top_k,
                "query_type": "simple"
            }
            
            # Ajout des filtres si fournis
            if filters:
                filter_conditions = []
                for field, condition in filters.items():
                    if isinstance(condition, dict):
                        for op, value in condition.items():
                            if op == "gte":
                                filter_conditions.append(f"{field} ge {value}")
                            elif op == "lte":
                                filter_conditions.append(f"{field} le {value}")
                            elif op == "eq":
                                filter_conditions.append(f"{field} eq '{value}'")
                
                if filter_conditions:
                    search_params["filter"] = " and ".join(filter_conditions)
            
            results = self.search_client.search(**search_params)
            
            return [dict(result) for result in results]
            
        except Exception as e:
            print(f"Erreur recherche documents: {e}")
            return []
    
    def index_from_rss(self, rss_url: str, source_name: str) -> int:
        """Indexe des articles depuis un flux RSS"""
        try:
            print(f"Traitement RSS: {source_name}")
            
            # Parser le flux RSS
            feed = feedparser.parse(rss_url)
            
            if not hasattr(feed, 'entries') or not feed.entries:
                print(f"Flux RSS invalide ou vide: {rss_url}")
                return 0
            
            documents: List[Dict[str, Any]] = []
            
            for entry in feed.entries[:10]:
                try:
                    # Gestion sécurisée du lien
                    link = entry.get('link', '')
                    if isinstance(link, list):
                        link_str = str(link[0]) if link else ''
                    else:
                        link_str = str(link) if link else ''
                    
                    if not link_str:
                        continue
                        
                    article_id = hashlib.md5(link_str.encode('utf-8')).hexdigest()
                    
                    # Extraire le contenu
                    content = entry.get('summary', '') or entry.get('description', '') or ''
                    if not isinstance(content, str):
                        content = str(content)
                    
                    if len(content) < 50:
                        continue
                    
                    # Gestion de la date
                    published_date = entry.get('published', '')
                    if not isinstance(published_date, str):
                        published_date = str(published_date) if published_date else ''
                    
                    # Préparer le document
                    document: Dict[str, Any] = {
                        "id": f"rss_{article_id}",
                        "text": entry.get('title', 'Sans titre'),
                        "result": content,
                        "confidence_score": 0.8,
                        "content_type": "news",
                        "created_at": self._parse_rss_date(published_date),
                        "reliability_level": "Source externe",
                        "url": link_str,
                        "source": source_name
                    }
                    
                    documents.append(document)
                    
                except Exception as e:
                    print(f"Erreur traitement article: {e}")
                    continue
            
            # Upload des documents
            if documents:
                success = self.upload_documents(documents)
                count = len(documents) if success else 0
                print(f"{count} articles indexés depuis {source_name}")
                return count
            
            return 0
            
        except Exception as e:
            print(f"Erreur indexation RSS {source_name}: {e}")
            return 0
    
    def _parse_rss_date(self, date_str: str) -> str:
        """Parse la date depuis RSS au format ISO"""
        if not isinstance(date_str, str) or not date_str.strip():
            return datetime.now().isoformat()
        
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            if dt:
                return dt.isoformat()
            else:
                return datetime.now().isoformat()
        except Exception:
            return datetime.now().isoformat()
    
    def cleanup_old_documents(self, days_old: int = 30) -> int:
        """Supprime les documents trop anciens"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            old_docs = self.search_client.search(
                search_text="*",
                filter=f"created_at lt {cutoff_date}",
                select=["id"],
                top=1000
            )
            
            delete_actions: List[Dict[str, Any]] = []
            for doc in old_docs:
                doc_dict = dict(doc)
                delete_actions.append({
                    "@search.action": "delete",
                    "id": doc_dict["id"]
                })
            
            if delete_actions:
                result = self.search_client.upload_documents(delete_actions)
                deleted_count = sum(1 for r in result if r.succeeded)
                print(f"{deleted_count} anciens documents supprimés")
                return deleted_count
            
            return 0
            
        except Exception as e:
            print(f"Erreur nettoyage: {e}")
            return 0
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Statistiques de l'index"""
        try:
            stats: Dict[str, Any] = {}
            
            try:
                all_docs = self.search_client.search(
                    search_text="*", 
                    top=1, 
                    include_total_count=True
                )
                stats['total_documents'] = all_docs.get_count() or 0
            except Exception:
                stats['total_documents'] = 0
            
            return stats
            
        except Exception as e:
            print(f"Erreur statistiques: {e}")
            return {'total_documents': 0}
