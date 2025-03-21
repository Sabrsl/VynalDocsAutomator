import os
import logging
import psutil
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger("VynalDocsAutomator.Monitor")

class SystemMonitor:
    """
    Moniteur système pour VynalDocsAutomator
    Surveille les performances, les ressources et la santé du système
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise le moniteur système
        
        Args:
            config_path: Chemin vers le fichier de configuration (optionnel)
        """
        self.metrics = {
            'performance': {},
            'resources': {},
            'quality': {},
            'errors': {}
        }
        self.alerts = []
        self.last_check = None
        self.config = self._load_config(config_path)
        self.stats_file = self.config.get('stats_file', 'monitoring/system_stats.json')
        
        # Créer le dossier de monitoring s'il n'existe pas
        os.makedirs('monitoring', exist_ok=True)
        
        # Configurer le logging
        self._setup_logging()
        
        logger.info("SystemMonitor initialisé")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Charge la configuration du moniteur"""
        default_config = {
            'thresholds': {
                'performance': {
                    'avg_processing_time': 10,  # secondes
                    'success_rate': 0.9,        # 90%
                    'timeout_rate': 0.1         # 10%
                },
                'resources': {
                    'cache_size': 1000,         # items
                    'memory_usage': 0.8,        # 80% de la RAM
                    'cpu_usage': 0.7            # 70% du CPU
                },
                'quality': {
                    'variable_detection_rate': 0.8,  # 80%
                    'false_positive_rate': 0.05      # 5%
                }
            },
            'monitoring': {
                'check_interval': 300,          # 5 minutes
                'stats_retention': 7,           # 7 jours
                'alert_cooldown': 1800          # 30 minutes
            },
            'logging': {
                'level': 'INFO',
                'file': 'monitoring/system.log',
                'max_size': 10485760,           # 10 MB
                'backup_count': 5
            },
            'stats_file': 'monitoring/system_stats.json'
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    custom_config = json.load(f)
                    # Fusion intelligente des configurations
                    self._deep_update(default_config, custom_config)
            except Exception as e:
                logger.error(f"Erreur lors du chargement de la configuration: {e}")
        
        return default_config
    
    def _deep_update(self, d: Dict, u: Dict) -> None:
        """Met à jour récursivement un dictionnaire"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d:
                self._deep_update(d[k], v)
            else:
                d[k] = v
    
    def _setup_logging(self) -> None:
        """Configure le système de logging"""
        log_config = self.config['logging']
        
        # Créer le dossier de logs si nécessaire
        os.makedirs(os.path.dirname(log_config['file']), exist_ok=True)
        
        # Configurer le handler de fichier avec rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_config['file'],
            maxBytes=log_config['max_size'],
            backupCount=log_config['backup_count']
        )
        
        # Configurer le format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Ajouter le handler au logger
        logger.addHandler(file_handler)
        logger.setLevel(getattr(logging, log_config['level']))
    
    def check_system_health(self, analyzer: Any, creator: Any) -> Dict[str, Any]:
        """
        Vérifie la santé globale du système
        
        Args:
            analyzer: Instance de DocumentAnalyzer
            creator: Instance de DocumentCreator
            
        Returns:
            Dict contenant les métriques et alertes
        """
        current_time = datetime.now()
        
        # Éviter les vérifications trop fréquentes
        if (self.last_check and 
            (current_time - self.last_check).total_seconds() < 
            self.config['monitoring']['check_interval']):
            return self.metrics
        
        self.last_check = current_time
        
        try:
            # Vérifier les performances
            self._check_performance(analyzer)
            
            # Vérifier les ressources
            self._check_resources(analyzer, creator)
            
            # Vérifier la qualité
            self._check_quality(analyzer)
            
            # Sauvegarder les statistiques
            self._save_stats()
            
            # Nettoyer les anciennes données
            self._cleanup_old_data()
            
            return self.metrics
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du système: {e}")
            self.metrics['errors']['last_check_error'] = str(e)
            return self.metrics
    
    def _check_performance(self, analyzer: Any) -> None:
        """Vérifie les métriques de performance"""
        stats = analyzer.get_stats()
        thresholds = self.config['thresholds']['performance']
        
        # Temps de traitement moyen
        avg_time = stats.get('avg_processing_time', 0)
        if avg_time > thresholds['avg_processing_time']:
            self._add_alert(
                'performance',
                f"Temps de traitement moyen élevé: {avg_time:.2f}s"
            )
        
        # Taux de succès
        total_docs = stats.get('analyzed_docs', 0)
        if total_docs > 0:
            success_rate = stats.get('successful_analyses', 0) / total_docs
            if success_rate < thresholds['success_rate']:
                self._add_alert(
                    'performance',
                    f"Taux de succès faible: {success_rate:.2%}"
                )
        
        # Mettre à jour les métriques
        self.metrics['performance'].update({
            'avg_processing_time': avg_time,
            'success_rate': success_rate if total_docs > 0 else 1.0,
            'total_docs': total_docs,
            'timestamp': datetime.now().isoformat()
        })
    
    def _check_resources(self, analyzer: Any, creator: Any) -> None:
        """Vérifie l'utilisation des ressources"""
        thresholds = self.config['thresholds']['resources']
        
        # Taille du cache
        analyzer_cache_size = len(getattr(analyzer, 'cache', {}))
        creator_cache_size = len(getattr(creator, 'cache', {}))
        total_cache_size = analyzer_cache_size + creator_cache_size
        
        if total_cache_size > thresholds['cache_size']:
            self._add_alert(
                'resources',
                f"Taille du cache excessive: {total_cache_size} items"
            )
        
        # Utilisation mémoire
        process = psutil.Process()
        memory_usage = process.memory_percent() / 100
        if memory_usage > thresholds['memory_usage']:
            self._add_alert(
                'resources',
                f"Utilisation mémoire élevée: {memory_usage:.2%}"
            )
        
        # Utilisation CPU
        cpu_usage = psutil.cpu_percent() / 100
        if cpu_usage > thresholds['cpu_usage']:
            self._add_alert(
                'resources',
                f"Utilisation CPU élevée: {cpu_usage:.2%}"
            )
        
        # Mettre à jour les métriques
        self.metrics['resources'].update({
            'cache_size': total_cache_size,
            'memory_usage': memory_usage,
            'cpu_usage': cpu_usage,
            'timestamp': datetime.now().isoformat()
        })
    
    def _check_quality(self, analyzer: Any) -> None:
        """Vérifie les métriques de qualité"""
        thresholds = self.config['thresholds']['quality']
        
        # Ces métriques devraient être calculées sur la base des résultats d'analyse
        stats = analyzer.get_stats()
        total_docs = stats.get('analyzed_docs', 0)
        
        if total_docs > 0:
            # Taux de détection des variables (à implémenter selon les besoins)
            detection_rate = 0.9  # exemple
            if detection_rate < thresholds['variable_detection_rate']:
                self._add_alert(
                    'quality',
                    f"Taux de détection des variables faible: {detection_rate:.2%}"
                )
            
            # Taux de faux positifs (à implémenter selon les besoins)
            false_positive_rate = 0.03  # exemple
            if false_positive_rate > thresholds['false_positive_rate']:
                self._add_alert(
                    'quality',
                    f"Taux de faux positifs élevé: {false_positive_rate:.2%}"
                )
            
            # Mettre à jour les métriques
            self.metrics['quality'].update({
                'variable_detection_rate': detection_rate,
                'false_positive_rate': false_positive_rate,
                'timestamp': datetime.now().isoformat()
            })
    
    def _add_alert(self, category: str, message: str) -> None:
        """Ajoute une alerte avec gestion du cooldown"""
        current_time = datetime.now()
        cooldown = self.config['monitoring']['alert_cooldown']
        
        # Vérifier si une alerte similaire existe dans le cooldown
        for alert in self.alerts:
            if (alert['category'] == category and 
                alert['message'] == message and
                (current_time - datetime.fromisoformat(alert['timestamp'])).total_seconds() < cooldown):
                return
        
        # Ajouter la nouvelle alerte
        alert = {
            'category': category,
            'message': message,
            'timestamp': current_time.isoformat()
        }
        self.alerts.append(alert)
        logger.warning(f"Alerte {category}: {message}")
    
    def _save_stats(self) -> None:
        """Sauvegarde les statistiques"""
        try:
            stats = {
                'metrics': self.metrics,
                'alerts': self.alerts,
                'last_update': datetime.now().isoformat()
            }
            
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des statistiques: {e}")
    
    def _cleanup_old_data(self) -> None:
        """Nettoie les anciennes données"""
        retention_days = self.config['monitoring']['stats_retention']
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Nettoyer les anciennes alertes
        self.alerts = [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert['timestamp']) > cutoff_date
        ]
        
        # Nettoyer les anciens fichiers de log
        log_dir = os.path.dirname(self.config['logging']['file'])
        for file in os.listdir(log_dir):
            if file.startswith('system') and file.endswith('.log'):
                file_path = os.path.join(log_dir, file)
                if os.path.getmtime(file_path) < cutoff_date.timestamp():
                    try:
                        os.remove(file_path)
                        logger.info(f"Ancien fichier de log supprimé: {file}")
                    except Exception as e:
                        logger.error(f"Erreur lors de la suppression du fichier {file}: {e}")
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Génère un rapport de santé complet
        
        Returns:
            Dict contenant le rapport de santé
        """
        return {
            'metrics': self.metrics,
            'alerts': self.alerts,
            'status': self._calculate_overall_status(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_overall_status(self) -> str:
        """Calcule le statut global du système"""
        if not self.metrics or not self.last_check:
            return 'UNKNOWN'
        
        # Compter les alertes par catégorie
        alert_counts = {'performance': 0, 'resources': 0, 'quality': 0}
        recent_alerts = [
            alert for alert in self.alerts
            if (datetime.now() - datetime.fromisoformat(alert['timestamp'])).total_seconds() < 3600
        ]
        
        for alert in recent_alerts:
            if alert['category'] in alert_counts:
                alert_counts[alert['category']] += 1
        
        # Définir le statut en fonction des alertes
        if sum(alert_counts.values()) == 0:
            return 'HEALTHY'
        elif any(count > 2 for count in alert_counts.values()):
            return 'CRITICAL'
        elif sum(alert_counts.values()) > 3:
            return 'WARNING'
        else:
            return 'DEGRADED' 