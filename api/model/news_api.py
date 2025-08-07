# Pour executer les codes passer par le terminal avec la commande : 
# python -m api.model.news_api

import httpx
from typing import List, Dict, Any
from datetime import timezone, datetime, timedelta
from api.security import NEWS_API_KEY

# Récupération des articles de presse par thème de manière asynchrone
themes = ["politique", "sport", "finance", "technologie", "culture", "écologie", "science"]
articles_by_theme: Dict[str, List[Dict[str, Any]]] = {}

# Calculer la date 3 jours avant aujourd’hui au format YYYY-MM-DD
start_date = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d")


# Remplacer par votre clé API NewsAPI
async def fetch_articles(theme: str, start_date: str = "2025-08-01") -> List[Dict]:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": theme,
        "language": "fr",
        "from": start_date, 
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY
    }
    # Effectuer la requête asynchrone
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        # Traiter la réponse JSON
        data = response.json()
        # Vérifier si la clé "articles" est présente
        articles = data.get("articles", [])
        if not articles:
            return []

        # Limiter à 4 articles et extraire les infos utiles
        formatted_articles = [
            {
                "title": article.get("title"),
                "published_at": article.get("publishedAt"),
                "summary": article.get("description"),
                "url": article.get("url")
            }
            for article in articles[:4]
        ]

        return formatted_articles   
      
# Fonction pour récupérer tous les articles par thème
async def get_all_articles_by_theme() -> Dict[str, List[Dict[str, Any]]]:
    results = {}
    for theme in themes:
        articles = await fetch_articles(theme)
        results[theme] = articles
    return results


# Fonction pour récupérer les articles de presse par thème
import asyncio

if __name__ == "__main__":
    from pprint import pprint
    articles = asyncio.run(fetch_articles("technologie"))
    pprint(articles)
    

