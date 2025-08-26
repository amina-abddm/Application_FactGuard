import requests
import os
from dotenv import load_dotenv

class AzureSearchService:
    def __init__(self):
        load_dotenv()
        self.endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        self.api_key = os.getenv('AZURE_SEARCH_API_KEY')
        self.index_name = 'factguard-analyses'
        
    def search_analyses(self, query, top=5):
        """Recherche dans l'index Azure AI Search"""
        search_url = f"{self.endpoint}/indexes/{self.index_name}/docs?api-version=2024-07-01"
        
        headers = {
            'api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        params = {
            'search': query,
            'top': top,
            'select': 'content,analysis_result,confidence_score,username,created_at',
            'orderby': 'search.score() desc'
        }
        
        response = requests.get(search_url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json().get('value', [])
        else:
            return []
    
    def get_context_for_rag(self, query, max_context_length=2000):
        """Récupère le contexte pour RAG"""
        results = self.search_analyses(query, top=3)
        
        context_parts = []
        current_length = 0
        
        for result in results:
            snippet = f"Analyse précédente: {result['content'][:300]}... Résultat: {result['analysis_result'][:300]}..."
            
            if current_length + len(snippet) > max_context_length:
                break
                
            context_parts.append(snippet)
            current_length += len(snippet)
        
        return "\n\n".join(context_parts)


