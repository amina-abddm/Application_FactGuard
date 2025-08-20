from .models import Article
import requests
from decouple import config

API_KEY = config('NEWS_API_KEY')
BASE_URL = "https://newsapi.org/v2/everything"


# 🔹 Récupère des articles depuis l'API News par thème
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
        title = item.get('title')
        if not title:  # ⚠️ On ignore les articles sans titre
            continue

        article_data = {
            'title': title,
            'summary': item.get('description') or "",
            'theme': theme_name,
            'read_time': "5 min",
            'url': item.get('url') or ""
        }
        articles.append(article_data)
    return articles


# 🔹 Récupère et enregistre les articles pour un thème donné
def articles_by_theme(theme_name, limit=6):
    """
    Récupère systématiquement les articles d’un thème via l’API News.
    Les articles sont créés/MAJ en base à chaque appel.
    """

    # (Optionnel) Désactiver les anciens articles de ce thème
    Article.objects.filter(theme=theme_name).update(is_active=False)

    # Récupère depuis l'API News
    api_articles = get_articles_from_api(theme_name, limit)

    created_articles = []
    for a in api_articles:
        article, _ = Article.objects.update_or_create(
            title=a['title'],  # clé d’unicité
            defaults={
                'summary': a['summary'],
                'theme': theme_name,
                'read_time': a['read_time'],
                'url': a['url'],
                'is_active': True
            }
        )
        created_articles.append(article)

    return created_articles
