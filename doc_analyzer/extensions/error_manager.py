"""
Gestionnaire d'erreurs spécifiques à l'application
"""

import logging
import traceback
from typing import Dict, Any, List, Optional, Type, Union
from datetime import datetime
import json
import os

logger = logging.getLogger("VynalDocsAutomator.Extensions.ErrorManager")

class DocumentError(Exception):
    """Erreur de base pour les documents"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.details = details or {}
        self.timestamp = datetime.now()

class ValidationError(DocumentError):
    """Erreur de validation de document"""
    pass

class ExtractionError(DocumentError):
    """Erreur d'extraction de données"""
    pass

class FormatError(DocumentError):
    """Erreur de format de document"""
    pass

class ProcessingError(DocumentError):
    """Erreur de traitement de document"""
    pass

class ErrorManager:
    """
    Gestionnaire pour la gestion des erreurs spécifiques
    """
    
    def __init__(self, error_log_dir: str = "error_logs"):
        self.error_log_dir = error_log_dir
        
        # Historique des erreurs
        self._error_history: List[Dict[str, Any]] = []
        
        # Callbacks d'erreurs enregistrés
        self._error_handlers: Dict[Type[Exception],
                                 List[callable]] = {}
        
        # Configuration de la gestion d'erreurs
        self._error_config = {
            "max_history_size": 1000,
            "log_to_file": True,
            "notify_on_error": True,
            "auto_retry": {
                "enabled": True,
                "max_retries": 3,
                "delay_seconds": 5
            }
        }
        
        self._ensure_error_log_dir()
        logger.info("Gestionnaire d'erreurs initialisé")
    
    def _ensure_error_log_dir(self):
        """Crée le répertoire des logs d'erreurs s'il n'existe pas"""
        if not os.path.exists(self.error_log_dir):
            os.makedirs(self.error_log_dir)
            logger.info(f"Répertoire des logs d'erreurs créé: {self.error_log_dir}")
    
    def handle_error(self, error: Exception,
                    context: Dict[str, Any] = None) -> bool:
        """
        Gère une erreur
        
        Args:
            error: L'erreur à gérer
            context: Contexte de l'erreur
            
        Returns:
            bool: True si l'erreur a été gérée
        """
        try:
            # Préparer les informations d'erreur
            error_info = {
                "type": error.__class__.__name__,
                "message": str(error),
                "timestamp": datetime.now().isoformat(),
                "traceback": traceback.format_exc(),
                "context": context or {}
            }
            
            # Ajouter les détails si c'est une DocumentError
            if isinstance(error, DocumentError):
                error_info.update({
                    "details": error.details,
                    "error_timestamp": error.timestamp.isoformat()
                })
            
            # Ajouter à l'historique
            self._add_to_history(error_info)
            
            # Logger l'erreur
            if self._error_config["log_to_file"]:
                self._log_error(error_info)
            
            # Appeler les handlers spécifiques
            handled = False
            for error_type, handlers in self._error_handlers.items():
                if isinstance(error, error_type):
                    for handler in handlers:
                        try:
                            handler(error, context)
                            handled = True
                        except Exception as e:
                            logger.error(f"Erreur dans le handler: {e}")
            
            # Notification si configurée
            if self._error_config["notify_on_error"]:
                self._notify_error(error_info)
            
            return handled
            
        except Exception as e:
            logger.error(f"Erreur lors de la gestion d'erreur: {e}")
            return False
    
    def _add_to_history(self, error_info: Dict[str, Any]):
        """Ajoute une erreur à l'historique"""
        self._error_history.append(error_info)
        
        # Limiter la taille de l'historique
        while (len(self._error_history) >
               self._error_config["max_history_size"]):
            self._error_history.pop(0)
    
    def _log_error(self, error_info: Dict[str, Any]):
        """Enregistre une erreur dans un fichier"""
        try:
            timestamp = datetime.fromisoformat(error_info["timestamp"])
            filename = f"error_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.error_log_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Erreur enregistrée dans: {filepath}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du log: {e}")
    
    def _notify_error(self, error_info: Dict[str, Any]):
        """Notifie une erreur (à implémenter selon les besoins)"""
        # TODO: Implémenter la notification (email, Slack, etc.)
        pass
    
    def register_error_handler(self, error_type: Type[Exception],
                             handler: callable):
        """
        Enregistre un handler pour un type d'erreur
        
        Args:
            error_type: Type d'erreur
            handler: Fonction de gestion
        """
        if error_type not in self._error_handlers:
            self._error_handlers[error_type] = []
        self._error_handlers[error_type].append(handler)
        logger.debug(f"Handler enregistré pour {error_type.__name__}")
    
    def unregister_error_handler(self, error_type: Type[Exception],
                               handler: callable):
        """
        Supprime un handler
        
        Args:
            error_type: Type d'erreur
            handler: Fonction de gestion
        """
        if error_type in self._error_handlers:
            self._error_handlers[error_type] = [
                h for h in self._error_handlers[error_type]
                if h != handler
            ]
            logger.debug(f"Handler supprimé pour {error_type.__name__}")
    
    def get_error_history(self, error_type: Type[Exception] = None,
                         start_date: datetime = None,
                         end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des erreurs avec filtres
        
        Args:
            error_type: Type d'erreur à filtrer
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            List[Dict[str, Any]]: Liste des erreurs filtrées
        """
        filtered_history = self._error_history.copy()
        
        if error_type:
            filtered_history = [
                e for e in filtered_history
                if e["type"] == error_type.__name__
            ]
        
        if start_date:
            filtered_history = [
                e for e in filtered_history
                if datetime.fromisoformat(e["timestamp"]) >= start_date
            ]
        
        if end_date:
            filtered_history = [
                e for e in filtered_history
                if datetime.fromisoformat(e["timestamp"]) <= end_date
            ]
        
        return filtered_history
    
    def clear_error_history(self):
        """Vide l'historique des erreurs"""
        self._error_history.clear()
        logger.info("Historique des erreurs vidé")
    
    def update_error_config(self, config: Dict[str, Any]) -> bool:
        """
        Met à jour la configuration
        
        Args:
            config: Nouvelle configuration
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        try:
            self._error_config.update(config)
            logger.info("Configuration mise à jour")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la configuration: {e}")
            return False
    
    def get_error_config(self) -> Dict[str, Any]:
        """
        Récupère la configuration actuelle
        
        Returns:
            Dict[str, Any]: Configuration
        """
        return self._error_config.copy()
    
    def analyze_errors(self, error_type: Type[Exception] = None,
                      time_period: str = "24h") -> Dict[str, Any]:
        """
        Analyse les erreurs pour identifier les tendances
        
        Args:
            error_type: Type d'erreur à analyser
            time_period: Période d'analyse (24h, 7d, 30d)
            
        Returns:
            Dict[str, Any]: Statistiques d'erreurs
        """
        try:
            # Calculer la date de début selon la période
            now = datetime.now()
            if time_period == "24h":
                start_date = now.replace(hour=0, minute=0, second=0)
            elif time_period == "7d":
                start_date = now.replace(hour=0, minute=0, second=0)
                start_date = start_date.replace(
                    day=start_date.day - 7)
            elif time_period == "30d":
                start_date = now.replace(hour=0, minute=0, second=0)
                start_date = start_date.replace(
                    day=start_date.day - 30)
            else:
                raise ValueError(f"Période invalide: {time_period}")
            
            # Filtrer les erreurs
            errors = self.get_error_history(
                error_type=error_type,
                start_date=start_date,
                end_date=now
            )
            
            # Analyser les erreurs
            stats = {
                "total_errors": len(errors),
                "error_types": {},
                "time_distribution": {},
                "common_contexts": {}
            }
            
            for error in errors:
                # Compter par type
                error_type = error["type"]
                stats["error_types"][error_type] = (
                    stats["error_types"].get(error_type, 0) + 1
                )
                
                # Distribution temporelle
                timestamp = datetime.fromisoformat(
                    error["timestamp"]).strftime("%Y-%m-%d")
                stats["time_distribution"][timestamp] = (
                    stats["time_distribution"].get(timestamp, 0) + 1
                )
                
                # Contextes communs
                if "context" in error:
                    for key, value in error["context"].items():
                        if isinstance(value, (str, int, float, bool)):
                            context_key = f"{key}:{value}"
                            stats["common_contexts"][context_key] = (
                                stats["common_contexts"].get(context_key, 0) + 1
                            )
            
            # Trier les résultats
            stats["error_types"] = dict(sorted(
                stats["error_types"].items(),
                key=lambda x: x[1],
                reverse=True
            ))
            stats["time_distribution"] = dict(sorted(
                stats["time_distribution"].items()
            ))
            stats["common_contexts"] = dict(sorted(
                stats["common_contexts"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10])  # Top 10 contextes
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}")
            return {} 