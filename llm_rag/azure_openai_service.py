import os
import logging
from typing import Optional
from dotenv import load_dotenv
from openai import AzureOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

logger = logging.getLogger(__name__)

class AzureOpenAIService:
    def __init__(self):
        # Charge les variables d'environnement depuis la racine du projet
        load_dotenv()  # Recherche automatiquement .env dans le projet
        
        # Récupère les vars avec vérification
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        
        if not api_key or not endpoint:
            logger.error(" Variables d'environnement Azure OpenAI manquantes")
            raise EnvironmentError("Variables d'environnement manquantes pour Azure OpenAI.")
        
        # Initialisation du client
        try:
            self.client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=endpoint,
                api_version=api_version
            )
            logger.info(" Client Azure OpenAI SDK initialisé avec succès")
        except Exception as e:
            logger.error(f" Erreur initialisation Azure OpenAI: {e}")
            raise
    
    def is_available(self) -> bool:
        """Vérifie si le service est disponible"""
        return hasattr(self, 'client') and self.client is not None
    
    def analyze_content(self, content: str, model: Optional[str] = None, max_tokens: int = 500, content_type: str = "text") -> str:
        """Effectue une analyse avec le prompt spécifique pour FactGuard."""
        
        if not self.is_available():
            return " Service Azure OpenAI non disponible"
        
        # Utilise le modèle de déploiement configuré ou celui passé en paramètre
        model_to_use = model or self.deployment_name
        
        PROMPT = (
            "Tu es un assistant d'analyse d'information expert en détection de désinformation.\n\n"
            "Selon le type de contenu fourni (texte, lien ou image), tu dois :\n"
            "1. **Analyser l'information transmise**.\n"
            "2. **Comparer avec des faits actuels ou des connaissances fiables**.\n"
            "3. **Évaluer la fiabilité de l'information**.\n\n"
            "Réponds toujours en suivant **le format ci-dessous**, avec des **emojis pour plus de lisibilité**, "
            "et en conservant **la même structure** dans tous les cas :\n\n"
            "✅ Analyse terminée ! Voici les résultats :\n\n"
            "📊 Score de fiabilité :XX %\n\n"
            "📝 Explication : {analyse synthétique en 1 phrases très courte max, expliquant la base de l'évaluation}\n\n"
            "📶 Niveau de confiance :  🟥 Faible / 🟨 Moyen / 🟩 Élevé\n\n"
            "🔗 Source(s) fiable(s) identifiée(s) :\n"
            "{insère ici une ou deux sources crédibles si disponibles, ou écris \"Aucune source pertinente trouvée\"}\n\n"
            "Réponds uniquement dans ce format, quel que soit l'input (texte, lien ou image), sans en sortir."
        )
        

        messages = [
            ChatCompletionSystemMessageParam(role="system", content=PROMPT),
            ChatCompletionUserMessageParam(role="user", content=content)
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
                top_p=0.95
            )
            
            result = response.choices[0].message.content or ""
            logger.info(f" Analyse terminée pour contenu de type: {content_type}")
            return result
            
        except Exception as e:
            logger.error(f" Erreur lors de l'analyse: {e}")
            return f" Erreur lors de l'analyse : {str(e)}"
    
    # Alias pour compatibilité avec votre code existant
    def analyze_information(self, content: str, content_type: str = 'text') -> str:
        """Alias pour analyze_content - compatibilité avec views.py"""
        return self.analyze_content(content, content_type=content_type)



