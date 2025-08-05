import pandas as pd
import requests

# Récupération des articles de presse par thème

themes = ["politique", "sport", "finance", "technologie", "culture", "écologie", "science"]
articles_by_theme = {}

# Remplacer par votre clé API NewsAPI
api_key = "e9baebaeb14c471881db9f362e4a4885"  # clé API 
url = "https://newsapi.org/v2/everything"     # URL de l'API NewsAPI

# Boucle pour récupérer les articles pour chaque thème

for theme in themes:
    params = {
        "q": theme,
        "language": "fr",
        "sortBy": "publishedAt",
        "apiKey": api_key
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Extraire jusqu'à 11 titres pour ce thème et leur dates de publication
  
    titles = [article["title"] for article in data.get("articles", [])[:11]]
    date = articles_by_theme.get("publishedAt", "")[:10]  # Format YYYY-MM-DD
    articles_by_theme[theme] = titles if titles else ["Aucun article trouvé"]

# Créer le DataFrame à partir d’un dictionnaire
if not articles_by_theme:
    print("Aucun article trouvé pour les thèmes spécifiés !")
else:
    df = pd.DataFrame.from_dict(articles_by_theme, orient='index').transpose()

# Afficher le tableau
print(df)