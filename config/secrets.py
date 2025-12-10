from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import os

class FactGuardSecrets:
    def __init__(self):
        self.vault_url = "https://factguard-keyvault.vault.azure.net/"
        self.credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=self.vault_url, credential=self.credential)
        
    def get_secret(self, secret_name, fallback_env=None):
        """Récupère un secret depuis Azure Key Vault avec fallback"""
        try:
            secret = self.client.get_secret(secret_name)
            print(f" Secret {secret_name} récupéré depuis Key Vault")
            return secret.value
        except Exception as e:
            print(f" Fallback pour {secret_name}: {e}")
            return os.getenv(fallback_env or secret_name)

# Instance globale
secrets_manager = FactGuardSecrets()
