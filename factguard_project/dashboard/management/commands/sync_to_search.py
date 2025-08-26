import requests
import json
from django.core.management.base import BaseCommand
from dashboard.models import Analysis
from dotenv import load_dotenv
import os

class Command(BaseCommand):
    help = 'Synchronise les analyses vers Azure AI Search'
    
    def handle(self, *args, **options):
        load_dotenv()
        
        endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        api_key = os.getenv('AZURE_SEARCH_API_KEY')
        index_name = 'factguard-analyses'
        
        # Récupérer toutes les analyses
        analyses = Analysis.objects.all()
        documents = []
        
        for analysis in analyses:
            # Utiliser la méthode to_search_document() de votre modèle
            doc = {
                "id": str(analysis.pk),
                "content": analysis.text,
                "analysis_result": analysis.result,
                "confidence_score": analysis.confidence_score,
                "user_id": str(analysis.user.pk),
                "username": analysis.user.username,
                "created_at": analysis.created_at.isoformat(),
                "summary": analysis.result[:200] + "..." if len(analysis.result) > 200 else analysis.result
            }
            documents.append(doc)
        
        # Indexer par batch dans Azure Search
        if documents:
            upload_url = f"{endpoint}/indexes/{index_name}/docs/index?api-version=2024-07-01"
            headers = {
                'api-key': api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                "value": [{"@search.action": "upload", **doc} for doc in documents]
            }
            
            response = requests.post(upload_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS(f' {len(documents)} analyses indexées avec succès!'))
            else:
                self.stdout.write(self.style.ERROR(f' Erreur indexation: {response.text}'))
