"""
Gestionnaire de performance pour optimiser l'analyse des documents
"""

import logging
from typing import Dict, Any, Optional
from ..config import Config
import time

logger = logging.getLogger("VynalDocsAutomator.Extensions.Performance")

class PerformanceManager:
    """
    Gère les paramètres de performance pour l'analyse des documents
    S'intègre avec la configuration existante sans la modifier
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialise le gestionnaire de performance
        
        Args:
            config: Configuration existante (optionnelle)
        """
        self.config = config
        self._current_mode = "balanced"
        self._memory_threshold = 0.8  # 80% memory usage threshold
        self._cpu_threshold = 0.9  # 90% CPU usage threshold
        self._last_performance_check = 0
        self._check_interval = 60  # Check system resources every 60 seconds
        
        # Configurations de performance par mode
        self._performance_configs = {
            "speed": {
                "extraction_depth": "basic",
                "confidence_threshold": 0.5,
                "parallel_processing": True,
                "max_workers": 8,
                "batch_size": 20,
                "save_temp_files": False,
                "validation": {
                    "strict_mode": False,
                    "auto_correct": True
                }
            },
            "balanced": {
                "extraction_depth": "standard",
                "confidence_threshold": 0.7,
                "parallel_processing": True,
                "max_workers": 4,
                "batch_size": 10,
                "save_temp_files": True,
                "validation": {
                    "strict_mode": True,
                    "auto_correct": True
                }
            },
            "accuracy": {
                "extraction_depth": "full",
                "confidence_threshold": 0.9,
                "parallel_processing": False,
                "max_workers": 1,
                "batch_size": 5,
                "save_temp_files": True,
                "validation": {
                    "strict_mode": True,
                    "auto_correct": False
                }
            }
        }
        
        logger.info("Gestionnaire de performance initialisé")
    
    def set_mode(self, mode: str) -> bool:
        """
        Définit le mode de performance
        
        Args:
            mode: Mode de performance ('speed', 'balanced', 'accuracy')
            
        Returns:
            bool: True si le mode a été changé avec succès
        """
        if mode not in self._performance_configs:
            logger.warning(f"Mode de performance invalide: {mode}")
            return False
        
        self._current_mode = mode
        logger.info(f"Mode de performance changé pour: {mode}")
        return True
    
    def get_current_config(self) -> Dict[str, Any]:
        """
        Retourne la configuration du mode actuel
        
        Returns:
            Dict[str, Any]: Configuration de performance actuelle
        """
        return self._performance_configs[self._current_mode].copy()
    
    def optimize_extractors(self, extractors_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimise la configuration des extracteurs selon le mode actuel
        
        Args:
            extractors_config: Configuration actuelle des extracteurs
            
        Returns:
            Dict[str, Any]: Configuration optimisée
        """
        current_config = self.get_current_config()
        optimized_config = extractors_config.copy()
        
        # Appliquer les optimisations selon le mode
        for extractor in optimized_config:
            if isinstance(optimized_config[extractor], dict):
                optimized_config[extractor].update({
                    "extraction_depth": current_config["extraction_depth"],
                    "confidence_threshold": current_config["confidence_threshold"]
                })
        
        return optimized_config
    
    def get_processing_params(self) -> Dict[str, Any]:
        """
        Retourne les paramètres de traitement optimisés
        
        Returns:
            Dict[str, Any]: Paramètres de traitement
        """
        current_config = self.get_current_config()
        return {
            "parallel_processing": current_config["parallel_processing"],
            "max_workers": current_config["max_workers"],
            "batch_size": current_config["batch_size"]
        }
    
    def get_validation_params(self) -> Dict[str, Any]:
        """
        Retourne les paramètres de validation optimisés
        
        Returns:
            Dict[str, Any]: Paramètres de validation
        """
        current_config = self.get_current_config()
        return current_config["validation"]

    def check_system_resources(self) -> None:
        """
        Vérifie les ressources système et ajuste le mode de performance si nécessaire
        """
        current_time = time.time()
        if current_time - self._last_performance_check < self._check_interval:
            return

        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent / 100
            cpu_percent = psutil.cpu_percent() / 100

            if memory_percent > self._memory_threshold or cpu_percent > self._cpu_threshold:
                if self._current_mode != "speed":
                    logger.warning("Ressources système limitées, passage en mode rapide")
                    self.set_mode("speed")
            elif memory_percent < self._memory_threshold * 0.7 and cpu_percent < self._cpu_threshold * 0.7:
                if self._current_mode == "speed":
                    logger.info("Ressources système disponibles, retour en mode équilibré")
                    self.set_mode("balanced")

            self._last_performance_check = current_time

        except ImportError:
            logger.warning("psutil non disponible, impossible de vérifier les ressources système")
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des ressources système: {e}")

    def optimize_batch_size(self, current_processing_time: float) -> int:
        """
        Optimise la taille du lot en fonction du temps de traitement
        
        Args:
            current_processing_time: Temps de traitement du dernier lot en secondes
            
        Returns:
            int: Nouvelle taille de lot recommandée
        """
        current_config = self.get_current_config()
        current_batch_size = current_config["batch_size"]
        
        # Ajuster la taille du lot en fonction du temps de traitement
        target_time = 5.0  # Temps de traitement cible en secondes
        
        if current_processing_time > target_time * 1.5:
            # Trop lent, réduire la taille du lot
            new_size = max(1, int(current_batch_size * 0.8))
        elif current_processing_time < target_time * 0.5:
            # Trop rapide, augmenter la taille du lot
            new_size = min(50, int(current_batch_size * 1.2))
        else:
            # Dans la plage acceptable
            return current_batch_size
            
        logger.info(f"Ajustement de la taille du lot: {current_batch_size} -> {new_size}")
        self._performance_configs[self._current_mode]["batch_size"] = new_size
        return new_size 