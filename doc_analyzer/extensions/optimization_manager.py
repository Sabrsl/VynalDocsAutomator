"""
Gestionnaire d'optimisation pour l'analyse de documents
Intègre les optimisations de performance et de fichiers
"""

import logging
import time
from typing import Dict, Any, Optional
from .performance_manager import PerformanceManager
from utils.file_optimizer import FileOptimizer
import threading

logger = logging.getLogger("VynalDocsAutomator.Extensions.Optimization")

class OptimizationManager:
    """Gestionnaire d'optimisation pour l'analyse de documents"""
    
    def __init__(self):
        """Initialise le gestionnaire d'optimisation"""
        self.performance_manager = PerformanceManager()
        self.file_optimizer = FileOptimizer()
        self._processing_times = []
        self._last_optimization = time.time()
        self._optimization_interval = 300  # 5 minutes
        self._dependencies = {}  # {component_id: set(dependent_components)}
        self._last_update = {}  # {component_id: timestamp}
        self._update_queue = set()  # Components pending update
        self._lock = threading.Lock()
        self._update_thread = None
        self._stop_update_thread = False
        
    def before_analysis(self, document_path: str) -> Dict[str, Any]:
        """
        Prépare l'analyse d'un document avec les optimisations appropriées
        
        Args:
            document_path: Chemin du document à analyser
            
        Returns:
            Dict[str, Any]: Configuration optimisée pour l'analyse
        """
        # Vérifier les ressources système
        self.performance_manager.check_system_resources()
        
        # Obtenir la configuration de performance actuelle
        config = self.performance_manager.get_current_config()
        
        # Optimiser la taille du lot si nécessaire
        if self._processing_times:
            avg_time = sum(self._processing_times) / len(self._processing_times)
            config["batch_size"] = self.performance_manager.optimize_batch_size(avg_time)
        
        return config
        
    def after_analysis(self, processing_time: float) -> None:
        """
        Enregistre les métriques après l'analyse d'un document
        
        Args:
            processing_time: Temps de traitement en secondes
        """
        self._processing_times.append(processing_time)
        # Garder seulement les 10 derniers temps
        if len(self._processing_times) > 10:
            self._processing_times = self._processing_times[-10:]
            
        # Optimiser périodiquement
        current_time = time.time()
        if current_time - self._last_optimization > self._optimization_interval:
            self._optimize_system()
            self._last_optimization = current_time
            
    def _optimize_system(self) -> None:
        """Effectue des optimisations périodiques du système"""
        try:
            # Nettoyer les caches si nécessaire
            cache_stats = self.file_optimizer.get_stats()
            if cache_stats["hit_rate"] < 50:  # Si le taux de succès du cache est faible
                logger.info("Faible taux de succès du cache, nettoyage...")
                self.file_optimizer.clear_cache()
            
            # Ajuster le mode de performance si nécessaire
            if self._processing_times:
                avg_time = sum(self._processing_times) / len(self._processing_times)
                if avg_time > 10:  # Si le traitement est trop lent
                    self.performance_manager.set_mode("speed")
                elif avg_time < 2:  # Si le traitement est très rapide
                    self.performance_manager.set_mode("accuracy")
                    
            logger.info("Optimisation système effectuée")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation système: {e}")
            
    def get_optimization_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques d'optimisation
        
        Returns:
            Dict[str, Any]: Statistiques d'optimisation
        """
        return {
            "cache_stats": self.file_optimizer.get_stats(),
            "performance_mode": self.performance_manager._current_mode,
            "avg_processing_time": sum(self._processing_times) / len(self._processing_times) if self._processing_times else 0,
            "batch_size": self.performance_manager.get_current_config()["batch_size"]
        }

    def _start_update_thread(self):
        """Démarre le thread de mise à jour des dépendances"""
        def update_task():
            while not self._stop_update_thread:
                self._process_update_queue()
                time.sleep(0.1)  # Petit délai pour éviter la surcharge CPU

        self._update_thread = threading.Thread(target=update_task, daemon=True)
        self._update_thread.start()

    def _process_update_queue(self):
        """Traite la file d'attente des mises à jour"""
        with self._lock:
            if not self._update_queue:
                return

            # Trier les composants par priorité (basée sur le nombre de dépendances)
            components = sorted(
                self._update_queue,
                key=lambda c: len(self._dependencies.get(c, set())),
                reverse=True
            )

            for component in components:
                self._update_component(component)
                self._update_queue.remove(component)

    def _update_component(self, component_id: str):
        """Met à jour un composant et ses dépendances"""
        if component_id not in self._dependencies:
            return

        current_time = time.time()
        last_update = self._last_update.get(component_id, 0)
        
        # Vérifier si une mise à jour est nécessaire
        if current_time - last_update < 1.0:  # Éviter les mises à jour trop fréquentes
            return

        try:
            # Mettre à jour le composant
            self._perform_component_update(component_id)
            self._last_update[component_id] = current_time

            # Mettre à jour les dépendances
            for dependent in self._dependencies[component_id]:
                self._update_queue.add(dependent)

        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du composant {component_id}: {e}")

    def _perform_component_update(self, component_id: str):
        """Effectue la mise à jour effective d'un composant"""
        # Implémentation spécifique selon le type de composant
        if component_id.startswith("doc_"):
            self._update_document_component(component_id)
        elif component_id.startswith("client_"):
            self._update_client_component(component_id)
        elif component_id.startswith("template_"):
            self._update_template_component(component_id)

    def _update_document_component(self, doc_id: str):
        """Met à jour un composant de document"""
        # Implémentation spécifique pour les documents
        pass

    def _update_client_component(self, client_id: str):
        """Met à jour un composant client"""
        # Implémentation spécifique pour les clients
        pass

    def _update_template_component(self, template_id: str):
        """Met à jour un composant de template"""
        # Implémentation spécifique pour les templates
        pass

    def add_dependency(self, component_id: str, depends_on: str):
        """Ajoute une dépendance entre deux composants"""
        with self._lock:
            if component_id not in self._dependencies:
                self._dependencies[component_id] = set()
            self._dependencies[component_id].add(depends_on)

    def remove_dependency(self, component_id: str, depends_on: str):
        """Supprime une dépendance entre deux composants"""
        with self._lock:
            if component_id in self._dependencies:
                self._dependencies[component_id].discard(depends_on)

    def schedule_update(self, component_id: str):
        """Planifie la mise à jour d'un composant"""
        with self._lock:
            self._update_queue.add(component_id)

    def get_dependencies(self, component_id: str) -> set:
        """Retourne les dépendances d'un composant"""
        with self._lock:
            return self._dependencies.get(component_id, set()).copy()

    def cleanup(self):
        """Nettoie les ressources"""
        self._stop_update_thread = True
        if self._update_thread:
            self._update_thread.join(timeout=1.0) 