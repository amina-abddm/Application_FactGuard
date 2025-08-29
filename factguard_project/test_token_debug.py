# test_token_debug.py
import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
import pyodbc
import struct

load_dotenv()

def test_token_formats():
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')

    if not tenant_id or not client_id or not client_secret:
        raise ValueError("AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET must be set in environment variables.")

    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    
    token = credential.get_token("https://database.windows.net//.default")
    print(f"✅ Token obtenu, longueur: {len(token.token)} caractères")
    
    server = 'factguard-sqlserver.database.windows.net'
    database = 'factguard-db'
    
    # Test 1 : Format token direct (votre méthode actuelle)
    print("\n🧪 Test 1 : Token direct...")
    try:
        conn_str = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server},1433;Database={database};TrustServerCertificate=yes;"
        conn = pyodbc.connect(conn_str, attrs_before={1256: token.token})
        print("✅ Test 1 réussi - Token direct OK")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Test 1 échoué : {e}")
    
    # Test 2 : Format token avec struct (recommandé par Microsoft)
    print("\n🧪 Test 2 : Token avec struct...")
    try:
        SQL_COPT_SS_ACCESS_TOKEN = 1256
        token_bytes = token.token.encode('utf-16-le')
        token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        
        conn_str = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server},1433;Database={database};TrustServerCertificate=yes;"
        conn = pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
        print("✅ Test 2 réussi - Token struct OK")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Test 2 échoué : {e}")
    
    # Test 3 : Sans TrustServerCertificate
    print("\n🧪 Test 3 : Sans TrustServerCertificate...")
    try:
        conn_str = f"Driver={{ODBC Driver 17 for SQL Server}};Server={server},1433;Database={database};"
        conn = pyodbc.connect(conn_str, attrs_before={1256: token.token})
        print("✅ Test 3 réussi - Sans TrustServerCertificate OK")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Test 3 échoué : {e}")
    
    print("\n❌ Tous les tests ont échoué")
    return False

if __name__ == "__main__":
    test_token_formats()
