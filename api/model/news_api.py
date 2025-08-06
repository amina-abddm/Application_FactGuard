import httpx
from typing import List, Dict
from datetime import datetime, timedelta
from security import NEWS_API_KEY

# Récupération des articles de presse par thème de manière asynchrone
themes = ["politique", "sport", "finance", "technologie", "culture", "écologie", "science"]
articles_by_theme: Dict[str, List[str]] = {}

# Calculer la date 3 jours avant aujourd’hui au format YYYY-MM-DD
start_date = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")

# Remplacer par votre clé API NewsAPI
async def fetch_articles(theme: str) -> List[str]:
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
        data = response.json()
        articles = data.get("articles", [])
        
        # Limiter à 4 articles et extraire les titres
        titles = [article.get("title") for article in articles[:4]]
        return titles if titles else ["Aucun article trouvé"]
    
# Fonction pour récupérer tous les articles par thème
async def get_all_articles_by_theme() -> Dict[str, List[str]]:
    results = {}
    for theme in themes:
        titles = await fetch_articles(theme)
        results[theme] = titles
    return results
