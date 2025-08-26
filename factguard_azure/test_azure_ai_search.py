import requests
import os

# Configuration
endpoint = "https://factguard-search.search.windows.net"
indexer_name = "factguard-indexer"
api_key = os.getenv('AZURE_SEARCH_ADMIN_KEY')

headers = {
    'api-key': api_key,
    'Content-Type': 'application/json'
}

url = f"{endpoint}/indexers/{indexer_name}/status?api-version=2024-07-01"

# Test de santé
response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    print(f" Indexer Status: {data['status']}")
    print(f" Documents traités: {data['lastResult']['itemsProcessed']}")
    print(f" Documents en erreur: {data['lastResult']['itemsFailed']}")
else:
    print(f" Erreur: {response.status_code} - {response.text}")
