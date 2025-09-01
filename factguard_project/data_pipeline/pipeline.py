import os
from dotenv import load_dotenv
import feedparser
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import psycopg2
from psycopg2.extensions import connection
import logging

# Chargement des variables d'environnement
load_dotenv()

class FactGuardDataPipeline:
    """Pipeline d'ingestion de données pour FactGuard"""
    
    def __init__(self):
        self.db_connection: Optional[connection] = None
        self.search_client: Optional[SearchClient] = None
        
    def setup_connections(self):
        """Initialise les connexions aux services Azure"""
        try:
            # Récupération sécurisée des credentials PostgreSQL
            db_host = os.getenv('DBHOST')
            db_name = os.getenv('DBNAME')
            db_user = os.getenv('DBUSER')
            db_pass = os.getenv('DBPASS')
            
            if not all([db_host, db_name, db_user, db_pass]):
                missing_vars = [
                    var for var, val in [
                        ('DBHOST', db_host),
                        ('DBNAME', db_name), 
                        ('DBUSER', db_user),
                        ('DBPASS', db_pass)
                    ] if not val
                ]
                raise ValueError(f"Credentials PostgreSQL manquants dans .env: {', '.join(missing_vars)}")
            
            # Connexion PostgreSQL avec variables d'environnement
            self.db_connection = psycopg2.connect(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_pass,
                port=5432,
                sslmode='require'
            )
            
            # Azure AI Search - Récupération des variables
            endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
            index_name = os.getenv('AZURE_SEARCH_INDEX_NAME')
            api_key = os.getenv('AZURE_SEARCH_API_KEY')
            
            # Vérification explicite - élimine l'erreur Pylance
            if not endpoint:
                raise ValueError("AZURE_SEARCH_ENDPOINT manquante dans .env")
            if not index_name:
                raise ValueError("AZURE_SEARCH_INDEX_NAME manquante dans .env")
            if not api_key:
                raise ValueError("AZURE_SEARCH_API_KEY manquante dans .env")
            
            # Maintenant Pylance sait que ces variables sont des str
            self.search_client = SearchClient(
                endpoint=endpoint,
                index_name=index_name,
                credential=AzureKeyCredential(api_key)
            )
            
        except Exception as e:
            logging.error(f"Erreur lors de la configuration des connexions: {e}")
            raise
    
    def fetch_news_sources(self) -> List[Dict[str, Any]]:
        """Récupère les actualités de sources fiables"""
        sources = [
            "https://rss.cnn.com/rss/edition.rss",
            "https://feeds.reuters.com/reuters/topNews", 
            "https://www.lemonde.fr/rss/une.xml",
            "https://feeds.bbci.co.uk/news/rss.xml"
        ]
        
        all_articles = []
        for source_url in sources:
            try:
                logging.info(f"Récupération depuis: {source_url}")
                feed = feedparser.parse(source_url)
                
                if not hasattr(feed, 'entries') or not feed.entries:
                    logging.warning(f"Aucun article trouvé pour {source_url}")
                    continue
                
                for entry in feed.entries[:5]:  # 5 articles récents par source
                    # Gestion sécurisée de la date de publication
                    published_parsed = getattr(entry, 'published_parsed', None)
                    if published_parsed is not None:
                        try:
                            pub_date = datetime(*published_parsed[:6])
                        except (TypeError, ValueError, IndexError):
                            pub_date = datetime.now()
                    else:
                        pub_date = datetime.now()
                    
                    # Validation des données essentielles
                    title = getattr(entry, 'title', 'Sans titre')
                    url = getattr(entry, 'link', '')
                    
                    if not url:  # Skip articles without URL
                        continue
                    
                    article = {
                        'title': title,
                        'content': getattr(entry, 'summary', 'Sans contenu'),
                        'url': url,
                        'date_published': pub_date,
                        'source': getattr(feed.feed, 'title', 'Source inconnue')
                    }
                    all_articles.append(article)
                    
            except Exception as e:
                logging.error(f"Erreur lors de la récupération de {source_url}: {e}")
                
        logging.info(f"Total articles récupérés: {len(all_articles)}")
        return all_articles
    
    def search_recent_claims(self, query: str) -> List[Dict[str, Any]]:
        """Recherche d'informations récentes via Bing Search API"""
        subscription_key = os.getenv('BING_SEARCH_API_KEY')
        if not subscription_key:
            logging.warning("Clé API Bing Search manquante - fonctionnalité désactivée")
            return []
            
        search_url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": subscription_key}
        params = {
            "q": f"{query} site:reuters.com OR site:bbc.com OR site:lemonde.fr",
            "count": 10,
            "sortBy": "Date",
            "freshness": "Week"  # Dernière semaine
        }
        
        try:
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            results = response.json()
            return results.get('webPages', {}).get('value', [])
        except requests.exceptions.RequestException as e:
            logging.error(f"Erreur requête Bing Search: {e}")
            return []
        except Exception as e:
            logging.error(f"Erreur Bing Search: {e}")
            return []
    
    def store_in_database(self, articles: List[Dict[str, Any]]):
        """Stocke les articles dans PostgreSQL avec gestion d'erreurs robuste"""
        if not self.db_connection:
            raise ValueError("Connexion à la base de données non établie")
        
        successful_inserts = 0
        
        for article in articles:
            try:
                cursor = self.db_connection.cursor()
                
                cursor.execute("""
                    INSERT INTO knowledge_base_articles 
                    (title, content, url, published_date, source, ingestion_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                """, (
                    article['title'][:500],
                    article['content'][:5000],
                    article['url'][:1000],
                    article['date_published'],  # Utilise la date du feed
                    article['source'][:200],
                    datetime.now()
                ))
                
                self.db_connection.commit()
                cursor.close()
                
                if cursor.rowcount > 0:
                    successful_inserts += 1
                    
            except Exception as e:
                logging.error(f"Erreur insertion DB pour {article.get('url', 'URL inconnue')}: {e}")
                self.db_connection.rollback()
        
        logging.info(f"{successful_inserts} nouveaux articles insérés en base")
    
    def index_in_azure_search(self, articles: List[Dict[str, Any]]):
        """Indexe les articles dans Azure AI Search"""
        if not self.search_client:
            raise ValueError("Client Azure Search non configuré")
        
        documents = []
        for article in articles:
            # Conversion correcte du datetime pour Azure Search
            date_published = article['date_published']
            if hasattr(date_published, 'replace'):
                # Ajouter timezone UTC si manquant
                from datetime import timezone
                date_str = date_published.replace(tzinfo=timezone.utc).isoformat()
            else:
                # Si c'est déjà une string, ajouter Z pour UTC
                date_str = f"{date_published.isoformat()}Z" if hasattr(date_published, 'isoformat') else f"{date_published}Z"
        
            doc = {
                "id": f"article_{abs(hash(article['url']))}", 
                "title": article['title'],
                "content": article['content'],
                "url": article['url'],
                "date_published": date_str,  # Format correct pour Azure Search
                "source": article['source'],
                #"document_type": "news_article"
        }
        documents.append(doc)
        
        if documents:
            try:
                result = self.search_client.upload_documents(documents)
                successful_uploads = len([r for r in result if r.succeeded])
                print(f"{successful_uploads}/{len(documents)} articles indexés dans Azure AI Search")
                return result
            except Exception as e:
                logging.error(f"Erreur indexation Azure Search: {e}")
                return None
        else:
            print("Aucun document à indexer")
            return None
    
    def run_ingestion_pipeline(self):
        """Exécute le pipeline complet d'ingestion"""
        start_time = datetime.now()
        
        try:
            print("Démarrage du pipeline d'ingestion FactGuard...")
            
            # 1. Connexions
            self.setup_connections()
            print("Connexions établies")
            
            # 2. Récupération des actualités
            articles = self.fetch_news_sources()
            print(f"{len(articles)} articles récupérés")
            
            if not articles:
                print("Aucun article récupéré, arrêt du pipeline")
                return
            
            # 3. Stockage en base
            self.store_in_database(articles)
            print("Articles stockés en base PostgreSQL")
            
            # 4. Indexation pour RAG
            self.index_in_azure_search(articles)
            print("Articles indexés pour le RAG")
            
            duration = (datetime.now() - start_time).total_seconds()
            print(f"Pipeline d'ingestion terminé avec succès en {duration:.1f}s !")
            
        except Exception as e:
            logging.error(f"Erreur pipeline: {e}")
            raise
        finally:
            # 5. Nettoyage
            if self.db_connection:
                self.db_connection.close()
                print("Connexion base de données fermée")

# Script principal
if __name__ == "__main__":
    # Configuration des logs
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('ingestion_pipeline.log')
        ]
    )
    
    try:
        pipeline = FactGuardDataPipeline()
        pipeline.run_ingestion_pipeline()
    except Exception as e:
        logging.error(f"Échec du pipeline: {e}")
        exit(1)
