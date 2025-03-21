import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from .system_monitor import SystemMonitor

logger = logging.getLogger("VynalDocsAutomator.MonitorUtils")

class MonitoringUtils:
    """Utilitaires pour le monitoring du système"""
    
    @staticmethod
    def initialize_monitoring(config_path: Optional[str] = None) -> SystemMonitor:
        """
        Initialise le système de monitoring
        
        Args:
            config_path: Chemin vers le fichier de configuration (optionnel)
            
        Returns:
            SystemMonitor: Instance du moniteur système
        """
        try:
            monitor = SystemMonitor(config_path)
            logger.info("Système de monitoring initialisé avec succès")
            return monitor
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du monitoring: {e}")
            raise
    
    @staticmethod
    def format_health_report(report: Dict[str, Any]) -> str:
        """
        Formate un rapport de santé en texte lisible
        
        Args:
            report: Rapport de santé du système
            
        Returns:
            str: Rapport formaté
        """
        lines = [
            "=== Rapport de Santé du Système ===",
            f"Status: {report['status']}",
            f"Date: {report['timestamp']}",
            "",
            "--- Performances ---"
        ]
        
        # Ajouter les métriques de performance
        perf = report['metrics'].get('performance', {})
        if perf:
            lines.extend([
                f"Temps moyen de traitement: {perf.get('avg_processing_time', 0):.2f}s",
                f"Taux de succès: {perf.get('success_rate', 0):.2%}",
                f"Documents traités: {perf.get('total_docs', 0)}"
            ])
        
        lines.extend(["", "--- Ressources ---"])
        
        # Ajouter les métriques de ressources
        res = report['metrics'].get('resources', {})
        if res:
            lines.extend([
                f"Taille du cache: {res.get('cache_size', 0)} items",
                f"Utilisation mémoire: {res.get('memory_usage', 0):.2%}",
                f"Utilisation CPU: {res.get('cpu_usage', 0):.2%}"
            ])
        
        lines.extend(["", "--- Qualité ---"])
        
        # Ajouter les métriques de qualité
        qual = report['metrics'].get('quality', {})
        if qual:
            lines.extend([
                f"Taux de détection: {qual.get('variable_detection_rate', 0):.2%}",
                f"Taux de faux positifs: {qual.get('false_positive_rate', 0):.2%}"
            ])
        
        # Ajouter les alertes récentes
        if report['alerts']:
            lines.extend(["", "--- Alertes Récentes ---"])
            for alert in report['alerts'][-5:]:  # Afficher les 5 dernières alertes
                lines.append(
                    f"[{alert['category']}] {alert['message']} "
                    f"({alert['timestamp']})"
                )
        
        return "\n".join(lines)
    
    @staticmethod
    def save_report_to_file(report: Dict[str, Any], output_path: str) -> None:
        """
        Sauvegarde un rapport dans un fichier
        
        Args:
            report: Rapport de santé
            output_path: Chemin du fichier de sortie
        """
        try:
            # Créer le dossier si nécessaire
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Sauvegarder le rapport formaté
            formatted_report = MonitoringUtils.format_health_report(report)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_report)
            
            logger.info(f"Rapport sauvegardé dans {output_path}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du rapport: {e}")
            raise
    
    @staticmethod
    def analyze_trends(stats_file: str) -> Dict[str, Any]:
        """
        Analyse les tendances à partir des statistiques sauvegardées
        
        Args:
            stats_file: Chemin vers le fichier de statistiques
            
        Returns:
            Dict: Analyse des tendances
        """
        try:
            if not os.path.exists(stats_file):
                return {'error': 'Fichier de statistiques non trouvé'}
            
            with open(stats_file, 'r') as f:
                stats = json.load(f)
            
            # Analyser les tendances
            trends = {
                'performance': MonitoringUtils._analyze_performance_trends(stats),
                'resources': MonitoringUtils._analyze_resource_trends(stats),
                'quality': MonitoringUtils._analyze_quality_trends(stats),
                'alerts': MonitoringUtils._analyze_alert_trends(stats)
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des tendances: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def _analyze_performance_trends(stats: Dict) -> Dict[str, Any]:
        """Analyse les tendances de performance"""
        metrics = stats.get('metrics', {}).get('performance', {})
        return {
            'avg_processing_time': {
                'current': metrics.get('avg_processing_time', 0),
                'trend': 'stable'  # À implémenter: calcul de tendance
            },
            'success_rate': {
                'current': metrics.get('success_rate', 0),
                'trend': 'stable'
            }
        }
    
    @staticmethod
    def _analyze_resource_trends(stats: Dict) -> Dict[str, Any]:
        """Analyse les tendances d'utilisation des ressources"""
        metrics = stats.get('metrics', {}).get('resources', {})
        return {
            'cache_size': {
                'current': metrics.get('cache_size', 0),
                'trend': 'stable'
            },
            'memory_usage': {
                'current': metrics.get('memory_usage', 0),
                'trend': 'stable'
            },
            'cpu_usage': {
                'current': metrics.get('cpu_usage', 0),
                'trend': 'stable'
            }
        }
    
    @staticmethod
    def _analyze_quality_trends(stats: Dict) -> Dict[str, Any]:
        """Analyse les tendances de qualité"""
        metrics = stats.get('metrics', {}).get('quality', {})
        return {
            'variable_detection_rate': {
                'current': metrics.get('variable_detection_rate', 0),
                'trend': 'stable'
            },
            'false_positive_rate': {
                'current': metrics.get('false_positive_rate', 0),
                'trend': 'stable'
            }
        }
    
    @staticmethod
    def _analyze_alert_trends(stats: Dict) -> Dict[str, Any]:
        """Analyse les tendances des alertes"""
        alerts = stats.get('alerts', [])
        categories = {}
        
        # Compter les alertes par catégorie
        for alert in alerts:
            category = alert['category']
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        return {
            'total_alerts': len(alerts),
            'categories': categories,
            'trend': 'stable'  # À implémenter: calcul de tendance
        } 