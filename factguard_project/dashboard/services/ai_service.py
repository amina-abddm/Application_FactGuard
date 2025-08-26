import os
import re
from openai import AzureOpenAI
from django.conf import settings

def call_gpt_analysis(text):
    """
    Analyse le texte avec Azure OpenAI GPT-4o pour détecter les fake news
    """
    try:
        client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        
        prompt = f"""
        Analysez ce texte pour détecter s'il s'agit de fausses informations (fake news).
        Fournissez une analyse détaillée avec un score de fiabilité de 0 à 100.

        Format de réponse souhaité:
        - Fiabilité: [score/100]
        - Analyse: [explication détaillée]
        - Recommandations: [conseils pour l'utilisateur]

        Texte à analyser:
        {text}
        """
        
        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "Tu es un expert en détection de fake news et fact-checking."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Erreur lors de l'analyse: {str(e)}"

def extract_confidence_score(result):
    """
    Extrait le score de confiance du résultat GPT
    """
    try:
        # Recherche pattern "Fiabilité: XX/100" ou "Score: XX"
        score_match = re.search(r'(?:fiabilité|score).*?(\d+)(?:/100|%)', result.lower())
        if score_match:
            score = float(score_match.group(1))
            return score / 100 if score > 1 else score
    except:
        pass
    return 0.0
