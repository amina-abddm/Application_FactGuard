from django.core.management.base import BaseCommand
from data_pipeline.pipeline import FactGuardDataPipeline

class Command(BaseCommand):
    help = 'Lance le pipeline d\'ingestion de données FactGuard'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(' Démarrage du pipeline d\'ingestion...'))
        
        pipeline = FactGuardDataPipeline()
        pipeline.run_ingestion_pipeline()
        
        self.stdout.write(self.style.SUCCESS(' Pipeline terminé avec succès !'))