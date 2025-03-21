import logging
from monitoring import MonitoringUtils
from document_processor import DocumentProcessor
from document_creator import DocumentCreator

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialiser le monitoring
        monitor = MonitoringUtils.initialize_monitoring('monitoring/config.json')
        
        # Initialiser les composants principaux
        processor = DocumentProcessor()  # Au lieu de DocumentAnalyzer
        creator = DocumentCreator()
        
        # Boucle principale
        while True:
            try:
                # Vérifier la santé du système
                health_metrics = monitor.check_system_health(processor, creator)
                
                # Obtenir un rapport complet
                health_report = monitor.get_health_report()
                
                # Sauvegarder le rapport
                MonitoringUtils.save_report_to_file(
                    health_report,
                    'monitoring/reports/latest_health_report.txt'
                )
                
                # Analyser les tendances
                trends = MonitoringUtils.analyze_trends('monitoring/system_stats.json')
                
                # Vérifier s'il y a des problèmes critiques
                if health_report['status'] == 'CRITICAL':
                    logger.critical("État système critique détecté!")
                    # Implémenter ici la logique de gestion des situations critiques
                    
                # Si le cache est trop grand, le nettoyer
                if health_metrics['resources'].get('cache_size', 0) > 900:  # 90% du seuil
                    logger.warning("Nettoyage préventif du cache")
                    processor.clear_cache()
                    creator.clear_cache()
                
                # Pause avant la prochaine vérification
                import time
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Erreur dans la boucle de monitoring: {e}")
                time.sleep(60)  # Attendre 1 minute en cas d'erreur
    
    except Exception as e:
        logger.error(f"Erreur fatale dans le monitoring: {e}")
        raise

if __name__ == "__main__":
    main() 