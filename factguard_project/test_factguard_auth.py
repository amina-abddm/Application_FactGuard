import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
import pyodbc

# Charge les variables d'environnement du .env
load_dotenv()

def test_factguard_authentication():
    try:
        print(" Test authentification FactGuard avec Service Principal...")
        
        tenant_id = os.getenv('AZURE_TENANT_ID')
        client_id = os.getenv('AZURE_CLIENT_ID')
        client_secret = os.getenv('AZURE_CLIENT_SECRET')

        if not tenant_id or not client_id or not client_secret:
            raise ValueError("AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET must be set in the environment variables.")

        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        #  SCOPE avec /.default
        token = credential.get_token("https://database.windows.net//.default")
        print(" Authentification Azure réussie avec Service Principal !")
        
        # Test de connexion à Azure SQL Database
        server = 'factguard-sqlserver.database.windows.net'
        database = 'factguard-db'
        
        connection_string = (
            f"Driver={{ODBC Driver 17 for SQL Server}};"  # ← CHANGEMENT ICI
            f"Server=tcp:{server},1433;"
            f"Database={database};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=yes;"  # ← Ajouté pour compatibilité
        )
        
        conn = pyodbc.connect(connection_string, attrs_before={1256: token.token})
        
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version_row = cursor.fetchone()
        if version_row is not None:
            version = version_row[0]
            print(f" Connexion Azure SQL Database réussie !")
            print(f" Version SQL Server : {version[:80]}...")
        else:
            print(" Impossible de récupérer la version du serveur SQL.")
        
        # Test création table basique
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='factguard_test' AND xtype='U')
            CREATE TABLE factguard_test (
                id INT IDENTITY(1,1) PRIMARY KEY,
                message NVARCHAR(255),
                created_at DATETIME2 DEFAULT GETDATE()
            )
        """)
        
        cursor.execute("INSERT INTO factguard_test (message) VALUES (?)", 
                    ("Authentification FactGuard réussie !",))
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM factguard_test")
        count_row = cursor.fetchone()
        if count_row is not None:
            count = count_row[0]
            print(f" Table test : {count} enregistrement(s)")
        else:
            print(" Impossible de récupérer le nombre d'enregistrements dans la table test.")
        
        conn.close()
        print(" SUCCÈS COMPLET ! FactGuard est connecté à Azure SQL Database !")
        return True
        
    except Exception as e:
        print(f" Erreur : {e}")
        return False

if __name__ == "__main__":
    test_factguard_authentication()
