# Pour executer les codes passer par le terminal avec la commande : 
# python -m api.route.recommandations

from fastapi import APIRouter, Query
from api.model.news_api import fetch_articles, get_all_articles_by_theme

router = APIRouter()

@router.get("/news/by-theme")
async def get_articles_by_theme(
    theme: str = Query(..., description="Nom du thème à rechercher")
):
    try:
        articles = await fetch_articles(theme)

        response = {
            "status": "success",
            "theme": theme,
            "articles": [
                {
                    "title": article["title"],
                    "published_at": article["published_at"],
                    "summary": article.get("summary", ""),
                    "url": article["url"]
                }
                for article in articles
            ]
        }

        return response

    except Exception as e:
        return {
            "status": "error",
            "theme": theme,
            "articles": [],
            "message": f"Une erreur est survenue : {str(e)}"
        }
        
        
# (Préparé pour l’avenir)
@router.get("/news/by-theme")
async def get_articles_for_one_theme(theme: str = Query(..., description="Nom du thème")):
    # Tu pourras connecter ça à une fonction qui récupère un seul thème
    return {"message": f"Articles pour le thème : {theme}"}
