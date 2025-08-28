import azure.functions as func
import logging
import os
from datetime import datetime
from content_indexer import FactGuardContentIndexer

# Configuration de l'application Azure Functions
app = func.FunctionApp()

@app.timer_trigger(
    schedule="0 0 8 * * *",  # Tous les jours à 8h00 UTC
    arg_name="mytimer", 
    run_on_startup=False
)
def daily_factguard_indexer(mytimer: func.TimerRequest) -> None:
    """
    Fonction de collecte quotidienne de données pour FactGuard
    Déclenchée automatiquement chaque jour à 8h
    """
    utc_timestamp = datetime.utcnow().isoformat()
    
    if mytimer.past_due:
        logging.warning('⚠️ Le déclencheur est en retard!')
    
    logging.info(f'🚀 Début de la collecte FactGuard à {utc_timestamp}')
    
    try:
        # Initialiser l'indexeur
        indexer = FactGuardContentIndexer()
        
        # Statistiques de collecte
        total_indexed = 0
        
        # 1. Indexer les données d'exemple/test
        logging.info('📋 Indexation des données d\'exemple...')
        sample_count = indexer.index_sample_data()
        total_indexed += sample_count
        logging.info(f'✅ {sample_count} documents d\'exemple indexés')
        
        # 2. Indexer les actualités récentes
        logging.info('📰 Collecte d\'actualités récentes...')
        try:
            news_count = indexer.index_news_articles([
                "https://www.lemonde.fr/rss/une.xml",
                "https://feeds.reuters.com/reuters/topNews",
                "https://rss.cnn.com/rss/edition.rss"
            ])
            total_indexed += news_count
            logging.info(f'✅ {news_count} articles d\'actualité indexés')
        except Exception as e:
            logging.error(f'❌ Erreur indexation actualités: {e}')
        
        # 3. Indexer les données gouvernementales
        logging.info('🏛️ Collecte de données gouvernementales...')
        try:
            gov_count = indexer.index_government_data()
            total_indexed += gov_count
            logging.info(f'✅ {gov_count} documents gouvernementaux indexés')
        except Exception as e:
            logging.error(f'❌ Erreur indexation données gouv: {e}')
        
        # Résumé final
        logging.info(f'🎉 Collecte terminée: {total_indexed} documents au total indexés')
        
        # Optionnel : Envoyer une notification de succès
        if total_indexed > 0:
            logging.info('✅ Votre système FactGuard a été mis à jour avec des données récentes!')
        else:
            logging.warning('⚠️ Aucun nouveau document indexé - vérifiez la configuration')
            
    except Exception as e:
        logging.error(f'❌ Erreur critique lors de la collecte: {str(e)}')
        # Optionnel : Envoyer une alerte par email ou Teams
        raise

@app.timer_trigger(
    schedule="0 0 */6 * * *",  # Toutes les 6 heures
    arg_name="timer_6h", 
    run_on_startup=False
)
def frequent_factguard_indexer(timer_6h: func.TimerRequest) -> None:
    """
    Collecte fréquente (toutes les 6h) pour les sources à haute fréquence
    """
    logging.info('🔄 Collecte fréquente FactGuard démarrée')
    
    try:
        indexer = FactGuardContentIndexer()
        
        # Collecte uniquement les sources les plus récentes
        recent_count = indexer.index_news_articles([
            "https://feeds.reuters.com/reuters/topNews",
            "https://rss.cnn.com/rss/edition.rss"
        ])
        
        logging.info(f'🔄 Collecte fréquente terminée: {recent_count} nouveaux articles')
        
    except Exception as e:
        logging.error(f'❌ Erreur collecte fréquente: {str(e)}')

# Fonction de test/debug manuelle
@app.http_trigger(route="test-indexer", auth_level=func.AuthLevel.FUNCTION)
def test_indexer(req: func.HttpRequest) -> func.HttpResponse:
    """
    Point d'entrée HTTP pour tester manuellement l'indexeur
    Usage: POST https://your-function.azurewebsites.net/api/test-indexer
    """
    logging.info('🧪 Test manuel de l\'indexeur déclenché')
    
    try:
        indexer = FactGuardContentIndexer()
        count = indexer.index_sample_data()
        
        return func.HttpResponse(
            f"✅ Test réussi: {count} documents indexés",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            f"❌ Test échoué: {str(e)}",
            status_code=500
        )
