# api/services/azure_search_service.py
import os
import logging
from typing import List, Dict, Any
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes.models import (
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    SearchIndex
)
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class FactGuardSearchService:
    """Service Azure AI Search spécialisé pour FactGuard"""
    
    def __init__(self):
        self.search_client = None
        self.index_client = None
        self.index_name = "factguard-articles-index"
        self._initialize_clients()
        self._ensure_index_exists()
    
    def _initialize_clients(self):
        """Initialise les clients Azure Search"""
        try:
            endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
            api_key = os.getenv('AZURE_SEARCH_API_KEY')
            
            if not endpoint:
                raise ValueError("Variable d'environnement AZURE_SEARCH_ENDPOINT manquante")
            if not api_key:
                raise ValueError("Variable d'environnement AZURE_SEARCH_API_KEY manquante")
            
            credential = AzureKeyCredential(api_key)
            
            self.search_client = SearchClient(
                endpoint=endpoint,
                index_name=self.index_name,
                credential=credential
            )
            
            self.index_client = SearchIndexClient(
                endpoint=endpoint,
                credential=credential
            )
            
            logger.info(" Azure AI Search initialisé pour FactGuard")
            
        except Exception as e:
            logger.error(f" Erreur initialisation Azure Search: {e}")
    
    def _ensure_index_exists(self):
        """Crée l'index FactGuard s'il n'existe pas"""
        if self.index_client is None:
            logger.error(" index_client n'est pas initialisé, impossible de créer ou mettre à jour l'index.")
            return
        try:
            # Définition des champs de l'index FactGuard
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="title", type=SearchFieldDataType.String),
                SearchableField(name="content", type=SearchFieldDataType.String),
                SearchableField(name="url", type=SearchFieldDataType.String),
                SimpleField(name="date_published", type=SearchFieldDataType.DateTimeOffset),
                SimpleField(name="source", type=SearchFieldDataType.String),
                SimpleField(name="reliability_score", type=SearchFieldDataType.Double),
                SearchableField(name="category", type=SearchFieldDataType.String),
                SearchableField(name="tags", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
                # Champ vectoriel pour la recherche sémantique
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536,  # Pour text-embedding-ada-002
                    vector_search_profile_name="factguard-vector-profile"
                )
            ]
            
            # Configuration de la recherche vectorielle
            vector_search = VectorSearch(
                profiles=[
                    VectorSearchProfile(
                        name="factguard-vector-profile",
                        algorithm_configuration_name="factguard-vector-config"
                    )
                ],
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="factguard-vector-config"
                    )
                ]
            )
            
            # Création de l'index
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search
            )
            
            self.index_client.create_or_update_index(index)
            logger.info(f" Index '{self.index_name}' créé/mis à jour")
            
        except Exception as e:
            logger.error(f" Erreur création index: {e}")
