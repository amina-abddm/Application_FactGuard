"""
WSGI config for factguard_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# --- Azure Monitor ---
try:
    from .telemetry import setup_telemetry
    setup_telemetry()
except Exception as e:
    print(f"[telemetry] WSGI init error: {e}")
# --------------------- 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factguard_project.settings')

application = get_wsgi_application()
