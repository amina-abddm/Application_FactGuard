import os
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

class AzureSearchService:
    def __init__(self):
        self.endpoint = os.getenv('AZURE_SEARCH_SERVICE_ENDPOINT')
        self.key = os.getenv('AZURE_SEARCH_ADMIN_KEY')
        self.index_name = os.getenv('AZURE_SEARCH_INDEX_NAME')
        
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.key)
        )
    
    def search_similar_content(self, query, top=5):
        """Recherche de contenu similaire"""
        try:
            results = self.search_client.search(
                search_text=query,
                top=top,
                select=["id", "content", "source", "credibility_score"]
            )
            return list(results)
        except Exception as e:
            print(f"Erreur de recherche: {e}")
            return []
    
    def index_analysis(self, analysis_data):
        """Indexer une nouvelle analyse"""
        try:
            result = self.search_client.upload_documents([analysis_data])
            return result
        except Exception as e:
            print(f"Erreur d'indexation: {e}")
            return None

