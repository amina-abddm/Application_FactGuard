# test_managed_identity.py
from azure.identity import InteractiveBrowserCredential
import pyodbc

def test_with_managed_identity_simulation():
    """Test avec authentification interactive - simule Managed Identity"""
    try:
        print("🔐 Authentification interactive (comme Managed Identity)...")
        
        credential = InteractiveBrowserCredential()
        token = credential.get_token("https://database.windows.net/")
        
        print("✅ Token obtenu - simulation Managed Identity réussie !")
        
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
        version = cursor.fetchone()
        
        print(f"✅ Connexion réussie avec Managed Identity !")
        if version is not None and len(version) > 0 and version[0] is not None:
            print(f"📊 Version : {version[0][:50]}...")
        else:
            print("📊 Version : Aucune version retournée.")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return False

if __name__ == "__main__":
    test_with_managed_identity_simulation()
