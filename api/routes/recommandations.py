# Pour executer les codes passer par le terminal avec la commande : 
# python -m api.route.recommandations

from fastapi import APIRouter, Query
from api.model.news_api import get_all_articles_by_theme

router = APIRouter()

@router.get("/news/themes")
async def get_articles_grouped_by_theme():
    data = await get_all_articles_by_theme()
    return data

# (Préparé pour l’avenir)
@router.get("/news/by-theme")
async def get_articles_for_one_theme(theme: str = Query(..., description="Nom du thème")):
    # Tu pourras connecter ça à une fonction qui récupère un seul thème
    return {"message": f"Articles pour le thème : {theme}"}
