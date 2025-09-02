# factguard_project/telemetry.py
from azure.monitor.opentelemetry import configure_azure_monitor

_is_configured = False

def setup_telemetry():
    global _is_configured
    if _is_configured:
        return
    # Lit APPLICATIONINSIGHTS_CONNECTION_STRING depuis l’environnement
    configure_azure_monitor()
    _is_configured = True
