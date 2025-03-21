#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Optimiseur de performance pour l'application
Améliore les performances de l'application en optimisant les paramètres de Tkinter
"""

import os
import sys
import platform
import logging
import threading
import time

# Configuration du logger
logger = logging.getLogger("VynalDocsAutomator.PerformanceOptimizer")

class PerformanceOptimizer:
    """
    Classe statique pour optimiser les performances de l'application
    """
    
    @staticmethod
    def optimize_application(root):
        """
        Applique des optimisations générales à l'application
        
        Args:
            root: Fenêtre principale de l'application
        """
        try:
            # Optimisations spécifiques à la plateforme
            system = platform.system().lower()
            
            if system == "windows":
                PerformanceOptimizer._optimize_for_windows(root)
            elif system == "darwin":
                PerformanceOptimizer._optimize_for_macos(root)
            elif system == "linux":
                PerformanceOptimizer._optimize_for_linux(root)
            
            # Optimisations générales
            PerformanceOptimizer._apply_general_optimizations(root)
            
            # Précharger les ressources fréquemment utilisées en arrière-plan
            threading.Thread(target=PerformanceOptimizer._preload_resources, daemon=True).start()
            
            logger.info("Optimisations de performance appliquées")
            return True
        except Exception as e:
            logger.warning(f"Impossible d'appliquer toutes les optimisations: {e}")
            return False
    
    @staticmethod
    def _optimize_for_windows(root):
        """
        Applique des optimisations spécifiques à Windows
        
        Args:
            root: Fenêtre principale de l'application
        """
        try:
            # Optimiser le rafraîchissement d'écran sur Windows
            root.update_idletasks()
            
            # Accélérer les animations
            try:
                root.tk.call('tk', 'scaling', 1.0)
            except:
                pass
                
            # Désactiver le DPI awareness pour des performances plus régulières
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass
            
            # Configurer le ramasse-miettes Python pour limiter les pauses
            try:
                import gc
                gc.set_threshold(100000, 10, 10)
            except:
                pass
            
            logger.info("Optimisations Windows appliquées")
        except Exception as e:
            logger.warning(f"Erreur lors de l'optimisation pour Windows: {e}")
    
    @staticmethod
    def _optimize_for_macos(root):
        """
        Applique des optimisations spécifiques à macOS
        
        Args:
            root: Fenêtre principale de l'application
        """
        try:
            # Optimiser la synchronisation entre les threads sur macOS
            os.environ['TK_SILENCE_DEPRECATION'] = '1'
            
            # Configurer le ramasse-miettes Python pour limiter les pauses
            try:
                import gc
                gc.set_threshold(100000, 10, 10)
            except:
                pass
            
            logger.info("Optimisations macOS appliquées")
        except Exception as e:
            logger.warning(f"Erreur lors de l'optimisation pour macOS: {e}")
    
    @staticmethod
    def _optimize_for_linux(root):
        """
        Applique des optimisations spécifiques à Linux
        
        Args:
            root: Fenêtre principale de l'application
        """
        try:
            # Désactiver la synchronisation complète pour améliorer les performances
            try:
                root.attributes('-alpha', 0.9999)
            except:
                pass
                
            try:
                root.attributes('-alpha', 1.0)
            except:
                pass
            
            # Configurer le ramasse-miettes Python pour limiter les pauses
            try:
                import gc
                gc.set_threshold(100000, 10, 10)
            except:
                pass
            
            logger.info("Optimisations Linux appliquées")
        except Exception as e:
            logger.warning(f"Erreur lors de l'optimisation pour Linux: {e}")
    
    @staticmethod
    def _apply_general_optimizations(root):
        """
        Applique des optimisations générales
        
        Args:
            root: Fenêtre principale de l'application
        """
        try:
            # Limiter les mises à jour inutiles
            root.update_idletasks()
            
            # Configurer le ramasse-miettes
            try:
                import gc
                gc.disable()
                
                # Réactiver le ramasse-miettes après le démarrage
                def enable_gc():
                    time.sleep(5)  # Attendre 5 secondes
                    gc.enable()
                    logger.info("Ramasse-miettes Python réactivé")
                
                threading.Thread(target=enable_gc, daemon=True).start()
            except:
                pass
            
            # Optimiser les paramètres de synchronisation
            try:
                root.tk.call('tk', 'useinputmethods', '0')
            except:
                pass
            
            logger.info("Optimisations générales appliquées")
        except Exception as e:
            logger.warning(f"Erreur lors de l'application des optimisations générales: {e}")
    
    @staticmethod
    def _preload_resources():
        """
        Précharge les ressources fréquemment utilisées
        """
        try:
            # Simuler le préchargement des ressources
            time.sleep(1)
            
            # Précharger les modules Python couramment utilisés
            modules_to_preload = [
                "json", "os.path", "glob", "re", "datetime", 
                "PIL.Image", "PIL.ImageTk", "customtkinter"
            ]
            
            for module_name in modules_to_preload:
                try:
                    __import__(module_name)
                except:
                    pass
            
            logger.info("Ressources préchargées avec succès")
        except Exception as e:
            logger.warning(f"Erreur lors du préchargement des ressources: {e}")

# Classe pour optimiser les accès au disque
class DiskCache:
    """
    Cache pour optimiser les accès au disque
    """
    
    _instance = None
    _cache = {}
    _last_access = {}
    _max_cache_size = 100
    _max_cache_age = 300  # 5 minutes
    
    @staticmethod
    def get_instance():
        """Récupère l'instance unique (singleton)"""
        if DiskCache._instance is None:
            DiskCache._instance = DiskCache()
        return DiskCache._instance
    
    def __init__(self):
        """Initialise le cache"""
        # Démarrer le thread de nettoyage
        threading.Thread(target=self._clean_cache_periodically, daemon=True).start()
    
    def get(self, key, default=None):
        """
        Récupère une valeur du cache
        
        Args:
            key: Clé à rechercher
            default: Valeur par défaut
            
        Returns:
            Valeur associée à la clé ou la valeur par défaut
        """
        if key in self._cache:
            self._last_access[key] = time.time()
            return self._cache[key]
        return default
    
    def set(self, key, value):
        """
        Définit une valeur dans le cache
        
        Args:
            key: Clé à définir
            value: Valeur à associer
        """
        self._cache[key] = value
        self._last_access[key] = time.time()
        
        # Limiter la taille du cache
        if len(self._cache) > self._max_cache_size:
            self._clean_cache()
    
    def _clean_cache(self):
        """Nettoie le cache en supprimant les entrées les plus anciennes"""
        now = time.time()
        
        # Supprimer les entrées trop anciennes
        keys_to_delete = [
            k for k, last_access in self._last_access.items()
            if now - last_access > self._max_cache_age
        ]
        
        for key in keys_to_delete:
            if key in self._cache:
                del self._cache[key]
            if key in self._last_access:
                del self._last_access[key]
        
        # Si le cache est toujours trop grand, supprimer les entrées les plus anciennes
        if len(self._cache) > self._max_cache_size:
            # Trier par date d'accès
            sorted_keys = sorted(
                self._last_access.keys(),
                key=lambda k: self._last_access[k]
            )
            
            # Supprimer les entrées les plus anciennes
            for key in sorted_keys[:len(sorted_keys) // 2]:
                if key in self._cache:
                    del self._cache[key]
                if key in self._last_access:
                    del self._last_access[key]
    
    def _clean_cache_periodically(self):
        """Nettoie périodiquement le cache"""
        while True:
            time.sleep(60)  # Nettoyer toutes les minutes
            self._clean_cache()

# Préparation du singleton pour le cache
disk_cache = DiskCache.get_instance() 