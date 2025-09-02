import os
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, ClientSecretCredential

def load_azure_credentials():
    """Charge les variables d'environnement et configure l'authentification Azure"""
    
    # Charger le .env
    env_path = Path(__file__).parent.parent.parent.parent / 'factguard_project' / '.env'
    result = load_dotenv(env_path)
    
    print(f"📥 Chargement .env: {'✅' if result else '❌'}")
    
    # ✅ SOLUTION : Vérification explicite des variables
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    
    # Vérifier que toutes les variables sont présentes
    if tenant_id and client_id and client_secret:
        credential = ClientSecretCredential(
            tenant_id=tenant_id,           # str garanti
            client_id=client_id,           # str garanti
            client_secret=client_secret    # str garanti
        )
        print("🔐 Authentification: Service Principal")
        return credential
    else:
        # Afficher quelles variables manquent
        missing = []
        if not tenant_id: missing.append('AZURE_TENANT_ID')
        if not client_id: missing.append('AZURE_CLIENT_ID')  
        if not client_secret: missing.append('AZURE_CLIENT_SECRET')
        
        print(f"⚠️  Variables manquantes: {', '.join(missing)}")
        print("🔐 Fallback: DefaultAzureCredential")
        
        credential = DefaultAzureCredential()
        return credential

# Test avec gestion d'erreur complète
def test_azure_connection():
    """Test complet de la connexion Azure"""
    try:
        credential = load_azure_credentials()
        
        # Test des variables critiques
        vars_status = {
            'AZURE_TENANT_ID': os.getenv('AZURE_TENANT_ID'),
            'AZURE_CLIENT_ID': os.getenv('AZURE_CLIENT_ID'),
            'AZURE_CLIENT_SECRET': os.getenv('AZURE_CLIENT_SECRET'),
            'AZURE_SEARCH_ENDPOINT': os.getenv('AZURE_SEARCH_ENDPOINT'),
            'AZURE_SEARCH_API_KEY': os.getenv('AZURE_SEARCH_API_KEY'),
        }
        
        print("\n🔍 Status des variables:")
        for var, value in vars_status.items():
            if value:
                display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else value[:12]
                print(f"✅ {var}: {display_value}")
            else:
                print(f"❌ {var}: None")
        
        print(f"\n✅ Credential configuré: {type(credential).__name__}")
        return credential
        
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        return None

if __name__ == "__main__":
    credential = test_azure_connection()

