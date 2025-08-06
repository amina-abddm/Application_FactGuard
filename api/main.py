# Pour exécuter le main : 
# ouvrir terminal puis python -m api.main  
# Pour lancer l'application : 
# ouvrir terminal puis uvicorn api.main:api --reload

from fastapi import APIRouter
from api.routes.recommandations import router as recommandations_router

api = FastAPI()

# Enregistrement du routeur
api.include_router(recommandations_router)