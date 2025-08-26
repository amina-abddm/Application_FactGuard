import os
import json
import requests
from django.core.management.base import BaseCommand
from dotenv import load_dotenv

class Command(BaseCommand):
    help = 'Crée l\'index Azure AI Search via API REST'
    
    def handle(self, *args, **options):
        load_dotenv()
        
        # Configuration
        endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        api_key = os.getenv('AZURE_SEARCH_API_KEY')
        
        self.stdout.write(f" Endpoint: {endpoint}")
        self.stdout.write(f" API Key: {'***' + api_key[-4:] if api_key else 'Non définie'}")
        
        if not endpoint or not api_key:
            self.stdout.write(
                self.style.ERROR(' Variables Azure Search manquantes')
            )
            return
        
        #  CHEMIN ABSOLU ROBUSTE
        # Structure : Application_FactGuard/factguard_project/dashboard/management/commands/
        # Objectif : Application_FactGuard/azure/search_index_schema.json
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.stdout.write(f" Répertoire actuel: {current_dir}")
        
        # Remonter jusqu'au dossier Application_FactGuard
        app_root = current_dir
        while not os.path.basename(app_root) == 'Application_FactGuard':
            parent = os.path.dirname(app_root)
            if parent == app_root:  # Protection contre boucle infinie
                break
            app_root = parent
        
        json_path = os.path.join(app_root, 'azure', 'search_index_schema.json')
        
        self.stdout.write(f" Racine Application_FactGuard: {app_root}")
        self.stdout.write(f" Chemin JSON calculé: {json_path}")
        self.stdout.write(f" Fichier existe: {'OUI' if os.path.exists(json_path) else 'NON'}")
        
        # Debug : Lister le contenu du dossier azure si il existe
        azure_dir = os.path.join(app_root, 'azure')
        if os.path.exists(azure_dir):
            files = os.listdir(azure_dir)
            self.stdout.write(f" Fichiers dans azure/: {files}")
        
        if not os.path.exists(json_path):
            self.stdout.write(
                self.style.ERROR(f' Fichier JSON introuvable: {json_path}')
            )
            return
        
        try:
            # Charger la définition d'index
            with open(json_path, 'r', encoding='utf-8') as f:
                index_definition = json.load(f)
            
            self.stdout.write(f" Index à créer: {index_definition.get('name', 'Non défini')}")
            
            # Headers pour les appels API
            headers = {
                'api-key': api_key,
                'Content-Type': 'application/json'
            }
            
            # Test de connexion - Liste des index existants
            list_url = f"{endpoint}/indexes?api-version=2024-07-01"
            response = requests.get(list_url, headers=headers)
            
            if response.status_code == 200:
                indexes = response.json().get('value', [])
                index_names = [idx['name'] for idx in indexes]
                self.stdout.write(f" Index existants: {index_names}")
                
                # Vérifier si l'index existe déjà
                target_index = index_definition['name']
                if target_index in index_names:
                    self.stdout.write(f" Index '{target_index}' existe déjà, mise à jour...")
                    # Mise à jour de l'index existant
                    update_url = f"{endpoint}/indexes('{target_index}')?api-version=2024-07-01"
                    response = requests.put(update_url, headers=headers, json=index_definition)
                    
                    if response.status_code == 200:
                        self.stdout.write(
                            self.style.SUCCESS(f' Index "{target_index}" mis à jour avec succès!')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f' Erreur mise à jour: {response.status_code} - {response.text}')
                        )
                else:
                    # Création d'un nouvel index
                    create_url = f"{endpoint}/indexes?api-version=2024-07-01"
                    response = requests.post(create_url, headers=headers, json=index_definition)
                    
                    if response.status_code in [200, 201]:
                        result = response.json()
                        self.stdout.write(
                            self.style.SUCCESS(f' Index "{result.get("name", target_index)}" créé avec succès!')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f' Erreur création: {response.status_code} - {response.text}')
                        )
            else:
                self.stdout.write(
                    self.style.ERROR(f' Impossible de se connecter à Azure Search: {response.status_code}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f' Erreur générale: {e}')
            )

