import os
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'factguard_project.settings')
django.setup()

with open('recommendations_data.json', 'w', encoding='utf-8') as f:
    call_command('dumpdata', 'recommendations', stdout=f)

print("Dump terminé avec succès")
