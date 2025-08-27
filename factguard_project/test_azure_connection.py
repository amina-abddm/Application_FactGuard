import os
from pathlib import Path
from dotenv import load_dotenv

# Charger le .env depuis le dossier courant
env_file = Path(__file__).parent / '.env'

print(f"📄 Fichier .env: {env_file}")
print(f"✅ Fichier existe: {env_file.exists()}")

if env_file.exists():
    result = load_dotenv(dotenv_path=env_file, override=True)
    print(f"🔄 Chargement réussi: {result}")
    
    # Test des variables Azure
    print("\n🔍 Variables après chargement:")
    azure_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
    azure_key = os.getenv('AZURE_SEARCH_API_KEY')
    openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    openai_key = os.getenv('AZURE_OPENAI_API_KEY')
    
    print(f"✅ AZURE_SEARCH_ENDPOINT: {azure_endpoint}")
    print(f"✅ AZURE_SEARCH_API_KEY: {azure_key[:10] if azure_key else 'None'}...")
    print(f"✅ AZURE_OPENAI_ENDPOINT: {openai_endpoint}")
    print(f"✅ AZURE_OPENAI_API_KEY: {openai_key[:10] if openai_key else 'None'}...")
    
    if azure_endpoint and azure_key and openai_endpoint and openai_key:
        print("\n🎉 Toutes les variables Azure sont chargées correctement !")
    else:
        print("\n❌ Certaines variables Azure sont manquantes")
else:
    print("❌ Fichier .env introuvable !")
