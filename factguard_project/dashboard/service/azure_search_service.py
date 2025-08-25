# dashboard/services/azure_search_service.py
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential
from django.conf import settings

class AzureSearchService:
    def __init__(self):
        # Configuration depuis settings.py
        self.service_endpoint = settings.AZURE_SEARCH_SERVICE_ENDPOINT
        self.admin_key = settings.AZURE_SEARCH_ADMIN_KEY
        self.index_name = settings.AZURE_SEARCH_INDEX_NAME
        
        # Credential réutilisable
        self.credential = AzureKeyCredential(self.admin_key)
    
    def get_search_client(self):
        """Retourne un client de recherche configuré"""
        return SearchClient(
            endpoint=self.service_endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
    
    def get_index_client(self):
        """Retourne un client d'index configuré"""
        return SearchIndexClient(
            endpoint=self.service_endpoint,
            credential=self.credential
        )

# Instance globale
azure_search_service = AzureSearchService()
