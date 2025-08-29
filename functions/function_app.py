# test_azure_connection_interactive.py
from azure.identity import InteractiveBrowserCredential
import pyodbc

def test_with_browser_auth():
    """Authentification via navigateur - sans Azure CLI"""
    try:
        print(" Authentification via navigateur...")
        
        # Authentification interactive
        credential = InteractiveBrowserCredential()
        token = credential.get_token("https://database.windows.net/")
        
        print(" Authentification réussie !")
        
        # Test connexion SQL
        server = 'factguard-sqlserver.database.windows.net'
        database = 'factguard-db'
        
        connection_string = (
            f"Driver={{ODBC Driver 18 for SQL Server}};"
            f"Server=tcp:{server},1433;"
            f"Database={database};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
        )
        
        conn = pyodbc.connect(connection_string, attrs_before={
            1256: token.token
        })
        
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        if row is not None:
            version = row[0]
            print(f" Connexion SQL réussie !")
            print(f" Version : {version[:50]}...")
        else:
            print(" Aucun résultat retourné par la requête SQL.")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f" Erreur : {e}")
        return False

if __name__ == "__main__":
    test_with_browser_auth()
