import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Charger les variables d'environnement
load_dotenv()

def test_azure_connection():
    try:
        client = AzureOpenAI(
            api_key=os.getenv("OPEN_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello Azure OpenAI!"}],
            max_tokens=50
        )
        
        print("✅ Connexion Azure OpenAI réussie !")
        print(f"Réponse: {response.choices[0].message.content}")
        print(f"Tokens utilisés: {response.usage.total_tokens}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

if __name__ == "__main__":
    test_azure_connection()
