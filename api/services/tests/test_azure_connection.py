import os
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, ClientSecretCredential  # Ajout de l'import
# En haut du fichier, ajoutez :
from dotenv import load_dotenv
load_dotenv()

# Remplacez la ligne DefaultAzureCredential() par :
if os.getenv('AZURE_CLIENT_SECRET'):
    credential = ClientSecretCredential(
        tenant_id=os.getenv('AZURE_TENANT_ID'),
        client_id=os.getenv('AZURE_CLIENT_ID'),
        client_secret=os.getenv('AZURE_CLIENT_SECRET')
    )
else:
    credential = DefaultAzureCredential()

# Définir le chemin du fichier .env
env_file = Path('.') / '.env'

if env_file.exists():
    # Chargement avec chemin explicite
    result = load_dotenv(dotenv_path=env_file, override=True)
    print(f"🔄 Chargement réussi: {result}")
    
    # Test des variables
    print("\n🔍 Variables après chargement:")
    vars_to_test = [
        'AZURE_SEARCH_ENDPOINT',
        'AZURE_SEARCH_API_KEY', 
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY'
    ]
    
    for var in vars_to_test:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:10]}...{value[-4:]}")
        else:
            print(f"❌ {var}: None")
else:
    print("❌ Fichier .env introuvable !")


