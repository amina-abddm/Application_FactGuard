# test_azure_connection.py
import sys
import os
from azure.identity import DefaultAzureCredential
import pyodbc

def test_authentication():
    """Test de l'authentification Azure"""
    try:
        print(" Test d'authentification Azure...")
        credential = DefaultAzureCredential()
        token = credential.get_token("https://database.windows.net/")
        print(" Authentification Azure réussie !")
        return True
    except Exception as e:
        print(f" Erreur d'authentification : {e}")
        return False

def test_sql_connection():
    """Test de connexion complète à Azure SQL"""
    try:
        print("🔗 Test de connexion Azure SQL...")
        
        # Configuration (adaptez avec vos vraies valeurs)
        server = 'factguard-sqlserver.database.windows.net'
        database = 'factguard-db'
        
        # Obtenir le token
        credential = DefaultAzureCredential()
        token = credential.get_token("https://database.windows.net/")
        
        # Connection string
        connection_string = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server=tcp:{server},1433;"
            f"Database={database};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        
        # Connexion avec token
        conn = pyodbc.connect(connection_string, attrs_before={
            1256: token.token  # SQL_COPT_SS_ACCESS_TOKEN
        })
        
        # Test simple
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        if row is not None:
            version = row[0]
            print(f" Connexion SQL réussie !")
            print(f" Version SQL Server : {version[:50]}...")
        else:
            print(" La requête SQL n'a retourné aucun résultat.")
                    
        conn.close()
        return True
        
    except Exception as e:
        print(f" Erreur de connexion SQL : {e}")
        return False

if __name__ == "__main__":
    print(" Test de connexion Azure SQL Database pour FactGuard")
    print("=" * 55)
    
    # Test 1 : Authentification
    auth_ok = test_authentication()
    
    if auth_ok:
        # Test 2 : Connexion SQL complète
        sql_ok = test_sql_connection()
        
        if sql_ok:
            print("\n Tous les tests réussis ! Votre configuration Azure SQL est prête.")
        else:
            print("\n Authentification OK mais connexion SQL échouée.")
            print("Vérifiez le pare-feu et les paramètres réseau.")
    else:
        print("\nProblème d'authentification Azure.")
        print("Vérifiez votre connexion et vos permissions.")
