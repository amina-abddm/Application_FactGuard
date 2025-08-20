import os
from dotenv import load_dotenv
from openai import AzureOpenAI

class AzureOpenAIService:
    def __init__(self):
        # Charge les variables d'environnement
        load_dotenv(dotenv_path=r"C:\Users\Utilisateur\Desktop\Application_FactGuard\azure\.env")

        # Récupère les vars avec vérification
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

        if not api_key or not endpoint:
            raise EnvironmentError("Variables d'environnement manquantes pour Azure OpenAI.")

        # Initialisation du client
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )

    def analyze_content(self, content, model="gpt-4o", max_tokens=500 , content_type: str = "text"):
        """Effectue une analyse avec le prompt spécifique pour FactGuard."""
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
            "📶 **Niveau de confiance** :  🟥 Faible / 🟨 Moyen / 🟩 Élevé\n\n"
            "🔗 **Source(s) fiable(s) identifiée(s)** :\n"
            "{insère ici une ou deux sources crédibles si disponibles, ou écris “Aucune source pertinente trouvée”}\n\n"
            "Réponds uniquement dans ce format, quel que soit l’input (texte, lien ou image), sans en sortir."
        )

        messages = [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": content}
        ]

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
