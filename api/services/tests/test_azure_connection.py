import os
from pathlib import Path
from dotenv import load_dotenv

# Chemin explicite vers le .env
current_dir = Path(__file__).parent
env_file = current_dir / '.env'

print(f"📁 Dossier courant: {current_dir}")
print(f"📄 Fichier .env: {env_file}")
print(f"✅ Fichier existe: {env_file.exists()}")

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


