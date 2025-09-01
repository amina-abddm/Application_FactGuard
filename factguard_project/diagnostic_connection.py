# diagnostic_connection.py
import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
import pyodbc

load_dotenv()

def test_different_configs():
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')

    if tenant_id is None or client_id is None or client_secret is None:
        raise ValueError("One or more Azure credentials are missing in environment variables.")

    credential = ClientSecretCredential(
        tenant_id=str(tenant_id),
        client_id=str(client_id),
        client_secret=str(client_secret)
    )
    
    token = credential.get_token("https://database.windows.net//.default")
    print(" Token obtenu avec succès")
    
    server = 'factguard-sqlserver.database.windows.net'
    database = 'factguard-db'
    
    # Test 1 : Version simplifiée
    print("\n🧪 Test 1 : Configuration simplifiée...")
    try:
        conn_str = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server},1433;Database={database};"
        conn = pyodbc.connect(conn_str, attrs_before={1256: token.token})
        print(" Test 1 réussi - Configuration simplifiée OK")
        conn.close()
        return True
    except Exception as e:
        print(f" Test 1 échoué : {e}")
    
    # Test 2 : Avec TrustServerCertificate
    print("\n Test 2 : Avec TrustServerCertificate...")
    try:
        conn_str = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server},1433;Database={database};TrustServerCertificate=yes;"
        conn = pyodbc.connect(conn_str, attrs_before={1256: token.token})
        print(" Test 2 réussi - TrustServerCertificate OK")
        conn.close()
        return True
    except Exception as e:
        print(f" Test 2 échoué : {e}")
    
    # Test 3 : Format tcp explicite
    print("\n🧪 Test 3 : Format tcp explicite...")
    try:
        conn_str = f"Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:{server},1433;Database={database};TrustServerCertificate=yes;"
        conn = pyodbc.connect(conn_str, attrs_before={1256: token.token})
        print(" Test 3 réussi - Format tcp OK")
        conn.close()
        return True
    except Exception as e:
        print(f" Test 3 échoué : {e}")
    
    print("\n Tous les tests ont échoué")
    print(" Vérifiez les permissions de votre Service Principal dans Azure Portal")
    return False

if __name__ == "__main__":
    test_different_configs()
