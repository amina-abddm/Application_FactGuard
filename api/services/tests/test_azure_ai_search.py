import requests
import os
from pathlib import Path
from dotenv import load_dotenv


env_path = Path(__file__).parent.parent.parent.parent / 'factguard_project' / '.env'

print(f" Chemin calculé: {env_path}")
print(f" Fichier existe: {env_path.exists()}")

# Charger le .env
result = load_dotenv(env_path)
print(f" Chargement: {'✅' if result else '❌'}")

# Configuration
endpoint = "https://ai-search-factguard.search.windows.net"
indexer_name = "factguard-indexer"
api_key = os.getenv('AZURE_SEARCH_API_KEY')

print(f" Clé chargée: {'✅' if api_key else '❌'}")
if api_key:
    print(f" Clé (15 premiers chars): {api_key[:15]}...")

headers = {
    'api-key': api_key,
    'Content-Type': 'application/json'
}

url = f"{endpoint}/indexers/{indexer_name}/status?api-version=2024-07-01"

# Test de santé
try:
    if not api_key:
        print(" Pas de clé API - impossible de continuer")
        exit(1)
        
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f" Indexer Status: {data['status']}")
        print(f" Documents traités: {data['lastResult']['itemsProcessed']}")
        print(f" Documents en erreur: {data['lastResult']['itemsFailed']}")
    elif response.status_code == 404:
        print(f" Indexer '{indexer_name}' n'existe pas encore")
        print(" Service accessible - créez l'indexer dans Azure Portal")
    else:
        print(f" Erreur: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f" Erreur: {e}")

