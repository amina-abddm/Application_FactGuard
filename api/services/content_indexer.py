import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from datetime import datetime, timedelta
import hashlib
import feedparser
from typing import List, Dict, Any, Optional , Union


class FactGuardContentIndexer:
    """Service d'indexation pour FactGuard avec Azure AI Search"""
    
    def __init__(self):
        # Configuration Azure AI Search depuis les variables d'environnement
        self.service_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.admin_key = os.getenv('AZURE_SEARCH_ADMIN_KEY') 
        self.index_name = os.getenv('AZURE_SEARCH_INDEX_NAME', 'factguard-articles-index')
        
        if not self.service_endpoint or not self.admin_key:
            raise ValueError("Variables d'environnement Azure Search manquantes")
        
        credential = AzureKeyCredential(self.admin_key)
        
        # Client unique pour tous les types de documents
        self.search_client = SearchClient(
            endpoint=self.service_endpoint,
            index_name=self.index_name,
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
        """Indexe une analyse dans factguard-articles-index"""
        try:
            print(f"Indexation de l'analyse ID: {analysis_obj.id}")
            
            document = {
                "id": f"analysis_{analysis_obj.id}",
                "title": f"Analyse: {analysis_obj.text[:50]}...",
                "content": analysis_obj.text,
                "url": f"/analysis/{analysis_obj.id}",
                "date_published": analysis_obj.created_at.isoformat(),
                "source": "FactGuard Analyzer",
                "reliability_score": float(analysis_obj.confidence_score),
                "category": "analysis",
                "tags": f"analysis,fact-check,user-generated,confidence-{int(analysis_obj.confidence_score*100)}"
            }
            
            result = self.search_client.upload_documents([document])
            
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
        """Recherche d'analyses similaires dans l'index unique"""
        try:
            print(f"Recherche similaire pour: {query[:50]}...")
            
            results = self.search_client.search(
                search_text=query,
                top=top_k,
                select=[
                    "id", "title", "content", "reliability_score", 
                    "category", "date_published", "source", "tags"
                ],
                search_fields=["title", "content", "tags"],
                #filter="category eq 'analysis' and reliability_score ge 0.4",
                query_type="simple"
            )
            
            formatted_results: List[Dict[str, Any]] = []
            for result in results:
                result_dict = dict(result)
                formatted_results.append({
                    'id': result_dict.get('id', ''),
                    'title': result_dict.get('title', ''),
                    'content': result_dict.get('content', ''),
                    'reliability_score': float(result_dict.get('reliability_score', 0)),
                    'category': result_dict.get('category', 'analysis'),
                    'date_published': result_dict.get('date_published', ''),
                    'source': result_dict.get('source', ''),
                    'search_score': result_dict.get('@search.score', 0)
                })
            
            print(f"{len(formatted_results)} analyses similaires trouvées")
            return formatted_results
            
        except Exception as e:
            print(f"Erreur recherche similaire: {e}")
            return []

    def index_from_rss(self, rss_url: str, source_name: str) -> int:
        """Indexe des articles RSS dans l'index unique"""
        try:
            print(f"Traitement RSS: {source_name}")
            
            feed = feedparser.parse(rss_url)
            if not hasattr(feed, 'entries') or not feed.entries:
                return 0
            
            documents: List[Dict[str, Any]] = []
            
            for entry in feed.entries[:10]:
                try:
                    link = entry.get('link', '')
                    if isinstance(link, list):
                        link_str = str(link[0]) if link else ''
                    else:
                        link_str = str(link) if link else ''
                    
                    if not link_str:
                        continue
                    
                    article_id = hashlib.md5(link_str.encode('utf-8')).hexdigest()
                    content = entry.get('summary', '') or entry.get('description', '') or ''
                    
                    if len(content) < 50:
                        continue
                    
                    document: Dict[str, Any] = {
                        "id": f"article_{article_id}",
                        "title": entry.get('title', 'Sans titre'),
                        "content": content,
                        "url": link_str,
                        "date_published": self._parse_rss_date(entry.get('published', '')),
                        "source": source_name,
                        "reliability_score": 0.8,
                        "category": "news",
                        "tags": f"news,rss,{source_name},fact-checking"
                    }
                    
                    documents.append(document)
                    
                except Exception as e:
                    print(f"Erreur traitement article: {e}")
                    continue
            
            if documents:
                result = self.search_client.upload_documents(documents=documents)
                success_count = sum(1 for r in result if r.succeeded)
                print(f"{success_count} articles indexés depuis {source_name}")
                return success_count
            
            return 0
            
        except Exception as e:
            print(f"Erreur indexation RSS {source_name}: {e}")
            return 0
        

    def _parse_rss_date(self, date_str: Union[str, list, None, Any]) -> str:
        """Parse la date depuis RSS au format ISO, en gérant plusieurs types possibles"""
        if date_str is None:
            return datetime.now().isoformat()
        
        if isinstance(date_str, list):
            # Prendre le premier élément s'il existe
            if not date_str:
                return datetime.now().isoformat()
            date_str_value = date_str[0]
            if not isinstance(date_str_value, str):
                date_str_value = str(date_str_value)
        else:
            # Convertir tout autre type en string
            date_str_value = str(date_str)

        if not date_str_value.strip():
            return datetime.now().isoformat()

        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str_value)
            if dt:
                return dt.isoformat()
            else:
                return datetime.now().isoformat()
        except Exception:
            return datetime.now().isoformat()



    def search_articles_and_analyses(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Recherche combinée articles + analyses"""
        try:
            results = self.search_client.search(
                search_text=query,
                top=top_k,
                select=["id", "title", "content", "category", "source", "date_published", "reliability_score"],
                search_fields=["title", "content", "tags"],
                query_type="simple"
            )
            
            return [dict(result) for result in results]
            
        except Exception as e:
            print(f"Erreur recherche combinée: {e}")
            return []
