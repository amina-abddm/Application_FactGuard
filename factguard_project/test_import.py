import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

try:
    from config.secrets import secrets_manager
    print(" Import réussi !")
    
    # Test de récupération d'un secret
    test_secret = secrets_manager.get_secret('AZURE-SEARCH-ENDPOINT')
    if test_secret:
        print(f" Secret récupéré : {test_secret[:20]}...")
    else:
        print(" Impossible de récupérer le secret")
        
except ImportError as e:
    print(f" Erreur d'import : {e}")
except Exception as e:
    print(f" Erreur : {e}")
