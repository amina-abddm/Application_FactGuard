import os
import sys
import logging  
import azure.functions as func
from azure.identity import InteractiveBrowserCredential, DefaultAzureCredential
import psycopg2
from dotenv import load_dotenv
load_dotenv()

# Configuration des logs
logging.basicConfig(level=logging.INFO)

current_dir = os.path.dirname(os.path.abspath(__file__))  # functions/
parent_dir = os.path.dirname(current_dir)                # Application_FactGuard/
factguard_path = os.path.join(parent_dir, 'factguard_project')
sys.path.insert(0, factguard_path)

from data_pipeline.pipeline import FactGuardDataPipeline # type: ignore

app = func.FunctionApp()

def connect_postgres_with_azure_identity():
    """Connexion PostgreSQL avec variables d'environnement"""
    try:
        print("Connexion PostgreSQL avec variables d'environnement...")
        
        # connection avec mot de pass
        connection_params = {
            'host': os.getenv('DBHOST', 'factguard-sqlserver.postgres.database.azure.com'),
            'database': os.getenv('DBNAME', 'factguard-db'), 
            'user': os.getenv('DBUSER', 'django'),
            'password': os.getenv('DBPASS'),  #  Utiliser le mot de passe du .env
            'port': 5432,
            'sslmode': 'require'
        }
        
        # Vérifier que le mot de passe est défini
        if not connection_params['password']:
            raise ValueError("DBPASS environment variable is not set")
        
        #  Connexion directe sans token Azure
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"Connexion PostgreSQL réussie !")
        print(f"Version: {version[:60]}...")
        
        return conn
        
    except Exception as e:
        print(f"Erreur: {e}")
        return None


def test_connection():
    """Test simple de la connexion"""
    conn = connect_postgres_with_azure_identity()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM knowledge_base_articles;")
        count = cursor.fetchone()[0]
        print(f"Nombre d'enregistrements: {count}")
        conn.close()

# Azure Function avec Timer Trigger
@app.timer_trigger(schedule="0 0 * * * *",  # Toutes les heures
                   arg_name="myTimer", 
                   run_on_startup=False,
                   use_monitor=False) 
def factguard_ingestion_timer(myTimer: func.TimerRequest) -> None:
    """Azure Function pour exécuter le pipeline FactGuard toutes les heures"""
    
    if myTimer.past_due:
        logging.info('Le timer était en retard!')  
    
    try:
        logging.info('Démarrage du pipeline FactGuard...')  
        
        # Utiliser votre pipeline avec Azure Identity
        pipeline = FactGuardDataPipeline()
        pipeline.run_ingestion_pipeline()
        
        logging.info('Pipeline FactGuard terminé avec succès!') 
        
    except Exception as e:
        logging.error(f'Erreur pipeline FactGuard: {str(e)}') 
        raise

# Pour les tests locaux
if __name__ == "__main__":
    test_connection()

