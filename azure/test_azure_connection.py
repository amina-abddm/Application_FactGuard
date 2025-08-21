import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# 1️⃣ Charge explicitement le .env situé dans /azure
# Exemple : /Users/ryadmohamedi/Desktop/Application_FactGuard/azure/.env
dotenv_path = "/Users/ryadmohamedi/Desktop/Application_FactGuard/azure/.env"
load_dotenv(dotenv_path=dotenv_path)

# 2️⃣ Récupère les variables – soulève une erreur si l'une manque
api_key   = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("OPEN_API_KEY")
endpoint  = os.getenv("AZURE_OPENAI_ENDPOINT")
api_ver   = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01")  # valeur par défaut

if not api_key:
    raise EnvironmentError("AZURE_OPENAI_API_KEY (ou OPEN_API_KEY) est introuvable dans .env")
if not endpoint:
    raise EnvironmentError("AZURE_OPENAI_ENDPOINT est introuvable dans .env")

print("DEBUG – clé chargée :", api_key[:6] + "…")     # voir les 6 premiers caractères
print("DEBUG – endpoint    :", endpoint)
print("DEBUG – api version :", api_ver)

# 3️⃣ Instancie le client seulement si tout est présent
client = AzureOpenAI(
    api_key        = api_key,
    azure_endpoint = endpoint,  # Utilise azure_endpoint pour le SDK ≥1.0
    api_version    = api_ver
)

def test_connection():
    resp = client.chat.completions.create(
        model="gpt-4o",  # nom exact du déploiement
        messages=[{"role": "user", "content": "Ping"}],
        max_tokens=10
    )
    print("Connexion réussie :", resp.choices[0].message.content)

if __name__ == "__main__":
    test_connection()
