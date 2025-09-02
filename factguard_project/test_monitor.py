import os
import logging
import time
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

# On charge la connexion depuis l'environnement
os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"] = "InstrumentationKey=d6038bca-22da-4e4c-8ece-298e4eabb29b;IngestionEndpoint=https://francecentral-1.in.applicationinsights.azure.com/;LiveEndpoint=https://francecentral.livediagnostics.monitor.azure.com/;ApplicationId=2fd6a4dc-684f-49c6-b7a3-f102143d97b9"

# Initialisation Azure Monitor
configure_azure_monitor()

# Logger et tracer
logger = logging.getLogger("factguard.test")
tracer = trace.get_tracer("factguard.test")

logger.warning("⚡ Test de log envoyé depuis script terminal")

with tracer.start_as_current_span("span_test_terminal") as span:
    span.set_attribute("feature", "test_span")
    time.sleep(0.3)
    logger.info("✅ Span terminé")
