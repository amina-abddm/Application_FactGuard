import os
from dotenv import load_dotenv

# Chargement explicite du fichier .env
load_dotenv()

print("🔍 Variables chargées :")
print(f"AZURE_SEARCH_ENDPOINT: {os.getenv('AZURE_SEARCH_ENDPOINT')}")
print(f"AZURE_SEARCH_API_KEY: {'***' + str(os.getenv('AZURE_SEARCH_API_KEY', ''))[-4:] if os.getenv('AZURE_SEARCH_API_KEY') else 'None'}")
print(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"AZURE_OPENAI_API_KEY: {'***' + str(os.getenv('AZURE_OPENAI_API_KEY', ''))[-4:] if os.getenv('AZURE_OPENAI_API_KEY') else 'None'}")

if os.getenv('AZURE_SEARCH_ENDPOINT') and os.getenv('AZURE_SEARCH_API_KEY'):
    print(" Variables Azure Search correctement chargées!")
else:
    print(" Variables Azure Search manquantes")

if os.getenv('AZURE_OPENAI_ENDPOINT') and os.getenv('AZURE_OPENAI_API_KEY'):
    print(" Variables Azure OpenAI correctement chargées!")
else:
    print(" Variables Azure OpenAI manquantes")


