from .models import Article
import requests
from decouple import config

API_KEY = config('NEWS_API_KEY')
BASE_URL = "https://newsapi.org/v2/everything"

# Récupère des articles depuis l'API News par thème
def get_articles_from_api(theme_name, limit=6):
    """Récupère des articles depuis l'API News par thème."""
    params = {
        'q': theme_name,
        'pageSize': limit,
        'apiKey': API_KEY,
        'language': 'fr',
        'sortBy': 'publishedAt'
    }
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code != 200:
        return []
    
    data = response.json()
    articles = []
    for item in data.get('articles', []):
        article_data = {
            'title': item.get('title'),
            'summary': item.get('description') or "",
            'theme': theme_name,
            'read_time': "5 min",
            'url': item.get('url')
        }
        articles.append(article_data)
    return articles

# Récupère les articles actifs d'un thème, ou crée-les via l'API si nécessaire
def articles_by_theme(theme_name, limit=6):
    """
    Récupère les articles actifs d'un thème.  
    S'il n'y en a pas en base, crée des articles via l'API News.
    """
    # Vérifie les articles existants
    existing_articles = Article.objects.filter(theme=theme_name, is_active=True)[:limit]
    
    if existing_articles.exists():
        return existing_articles
    
    # Sinon, récupère depuis l'API
    api_articles = get_articles_from_api(theme_name, limit)
    
    created_articles = []
    for a in api_articles:
        article, created = Article.objects.get_or_create(
            title=a['title'],
            defaults=a
        )
        created_articles.append(article)
    
    return created_articles