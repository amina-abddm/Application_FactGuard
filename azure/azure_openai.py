import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Charger les variables du fichier .env
load_dotenv()
# Lire la clé API depuis .env
API_KEY = os.getenv("OPEN_API_KEY")

# Autres configs
ENDPOINT = "https://factguard-model.openai.azure.com/"
API_VERSION = "2024-12-01-preview"
DEPLOYMENT_NAME = "gpt-4o"

client = AzureOpenAI(
    api_key=API_KEY,
    api_version=API_VERSION,
    azure_endpoint=ENDPOINT,
)

PROMPT = (
    "Tu es un assistant d’analyse d’information expert en détection de désinformation.\n\n"
    "Selon le type de contenu fourni (texte, lien ou image), tu dois :\n"
    "1. **Analyser l'information transmise**.\n"
    "2. **Comparer avec des faits actuels ou des connaissances fiables**.\n"
    "3. **Évaluer la fiabilité de l'information**.\n\n"
    "Réponds toujours en suivant **le format ci-dessous**, avec des **emojis pour plus de lisibilité**, "
    "et en conservant **la même structure** dans tous les cas :\n\n"
    "✅ **Analyse terminée ! Voici les résultats :**\n\n"
    "📊 **Score de fiabilité** :`XX %`\n\n"
    "📝 **Explication** : {analyse synthétique en 1 phrases très courte max, expliquant la base de l’évaluation}\n\n"
    "📶 **Niveau de confiance** :  🟥 Faible / 🟨 Moyen / 🟩 Élevé\n\n"
    "🔗 **Source(s) fiable(s) identifiée(s)** :\n"
    "{insère ici une ou deux sources crédibles si disponibles, ou écris “Aucune source pertinente trouvée”}\n\n"
    "Réponds uniquement dans ce format, quel que soit l’input (texte, lien ou image), sans en sortir."
)

def analyse_information(contenu: str) -> str:
    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": contenu}
    ]
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=messages,
        max_tokens=1024,
        temperature=0,
        top_p=1.0,
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    test_input = "Macron annonce la fin de la pandémie de COVID-19 en France."
    resultat = analyse_information(test_input)
    print(resultat)