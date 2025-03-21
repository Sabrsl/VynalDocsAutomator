#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'optimisation des performances pour VynalDocsAutomator
Fournit des utilitaires pour améliorer les performances de l'application
"""

import os
import sys
import gc
import logging
import threading
import time
from functools import wraps, lru_cache
from typing import Callable, Any, Dict, List, Optional, Union, Tuple

logger = logging.getLogger("VynalDocsAutomator.PerformanceOptimizer")

class PerformanceOptimizer:
    """
    Classe utilitaire pour optimiser les performances de l'application
    """
    
    # Paramètres globaux
    CACHE_SIZE = 100  # Taille du cache pour les fonctions décorées
    DEBOUNCE_DELAY = 300  # Délai de debounce en millisecondes
    THROTTLE_DELAY = 100  # Délai de throttle en millisecondes
    
    # Métriques de performance
    metrics = {
        'form_open_time': [],
        'form_close_time': [],
        'data_load_time': [],
        'render_time': []
    }
    
    def __init__(self):
        """Initialise l'optimiseur de performance"""
        self._ui_cache = {}  # Cache pour les éléments d'interface
        self._ui_cache_size = 100  # Taille maximale du cache
        self._ui_cache_lock = threading.Lock()
        self._ui_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }

    def cache_ui_element(self, key: str, element: Any) -> None:
        """
        Met en cache un élément d'interface
        
        Args:
            key: Clé unique pour l'élément
            element: L'élément à mettre en cache
        """
        with self._ui_cache_lock:
            # Si le cache est plein, supprimer l'élément le moins utilisé
            if len(self._ui_cache) >= self._ui_cache_size:
                # Trouver l'élément le moins utilisé
                least_used = min(
                    self._ui_cache.items(),
                    key=lambda x: x[1]['access_count']
                )
                del self._ui_cache[least_used[0]]
                self._ui_stats['evictions'] += 1

            # Ajouter l'élément au cache
            self._ui_cache[key] = {
                'element': element,
                'access_count': 0,
                'last_access': time.time()
            }

    def get_cached_ui_element(self, key: str) -> Optional[Any]:
        """
        Récupère un élément d'interface du cache
        
        Args:
            key: Clé de l'élément à récupérer
            
        Returns:
            L'élément en cache ou None si non trouvé
        """
        with self._ui_cache_lock:
            if key in self._ui_cache:
                self._ui_cache[key]['access_count'] += 1
                self._ui_cache[key]['last_access'] = time.time()
                self._ui_stats['hits'] += 1
                return self._ui_cache[key]['element']
            
            self._ui_stats['misses'] += 1
            return None

    def invalidate_ui_cache(self, key: str = None) -> None:
        """
        Invalide une entrée du cache ou tout le cache
        
        Args:
            key: Clé de l'élément à invalider, ou None pour tout invalider
        """
        with self._ui_cache_lock:
            if key is None:
                self._ui_cache.clear()
            else:
                self._ui_cache.pop(key, None)

    def get_ui_cache_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du cache d'interface
        
        Returns:
            Dict contenant les statistiques du cache
        """
        with self._ui_cache_lock:
            total = self._ui_stats['hits'] + self._ui_stats['misses']
            hit_rate = (self._ui_stats['hits'] / total * 100) if total > 0 else 0
            
            return {
                'cache_size': len(self._ui_cache),
                'max_size': self._ui_cache_size,
                'hits': self._ui_stats['hits'],
                'misses': self._ui_stats['misses'],
                'evictions': self._ui_stats['evictions'],
                'hit_rate': hit_rate
            }

    def optimize_ui_rendering(self, widget: Any) -> None:
        """
        Optimise le rendu d'un widget
        
        Args:
            widget: Le widget à optimiser
        """
        # Désactiver temporairement les mises à jour
        widget.update_idletasks()
        
        # Mettre en cache les widgets enfants
        for child in widget.winfo_children():
            if isinstance(child, (ctk.CTkFrame, ctk.CTkLabel, ctk.CTkButton)):
                self.cache_ui_element(f"{widget.winfo_id()}_{child.winfo_id()}", child)
        
        # Réactiver les mises à jour
        widget.update()

    @classmethod
    def optimize_application(cls, root):
        """
        Applique des optimisations globales à l'application
        
        Args:
            root: Fenêtre principale de l'application
        """
        logger.info("Application des optimisations de performance")
        
        # Optimiser la gestion de la mémoire
        cls._optimize_memory()
        
        # Planifier des nettoyages périodiques
        cls._schedule_cleanup(root)
        
        # Optimiser les paramètres de l'interface
        cls._optimize_ui_settings(root)
        
        # Optimiser le rendu des widgets
        cls._optimize_widget_rendering(root)
        
        logger.info("Optimisations de performance appliquées")
    
    @classmethod
    def _optimize_memory(cls):
        """Optimise la gestion de la mémoire"""
        # Forcer un garbage collection
        gc.collect()
        
        # Réduire la fréquence du garbage collection automatique
        gc.set_threshold(700, 10, 10)  # Valeurs par défaut: 700, 10, 10
        
        # Optimiser la gestion des images
        cls._optimize_image_cache()
        
        logger.debug("Optimisation de la mémoire effectuée")
    
    @classmethod
    def _optimize_image_cache(cls):
        """Optimise la gestion des images en mémoire"""
        try:
            # Limiter la taille du cache d'images
            import tkinter as tk
            
            # Vérifier si le cache d'images existe
            if hasattr(tk, '_default_root') and tk._default_root:
                # Récupérer toutes les images
                images = tk._default_root.tk.call('image', 'names')
                
                # Convertir en liste Python
                if isinstance(images, str):
                    images = images.split()
                
                # Limiter le nombre d'images en cache (garder seulement les 50 dernières)
                if len(images) > 50:
                    # Trier par ordre d'utilisation (si possible)
                    for img_name in images[:-50]:
                        try:
                            tk._default_root.tk.call('image', 'delete', img_name)
                        except Exception:
                            pass
                
                logger.debug(f"Cache d'images optimisé: {len(images)} images en mémoire")
        except Exception as e:
            logger.warning(f"Erreur lors de l'optimisation du cache d'images: {e}")
    
    @classmethod
    def _schedule_cleanup(cls, root, interval=300000):
        """
        Planifie des nettoyages périodiques
        
        Args:
            root: Fenêtre principale de l'application
            interval: Intervalle en millisecondes (défaut: 5 minutes)
        """
        def cleanup():
            # Forcer un garbage collection
            gc.collect()
            
            # Réduire l'utilisation de la mémoire
            for obj in gc.get_objects():
                if isinstance(obj, dict) and not obj:
                    obj.clear()
            
            # Planifier le prochain nettoyage
            if root.winfo_exists():
                root.after(interval, cleanup)
        
        # Planifier le premier nettoyage
        root.after(interval, cleanup)
        logger.debug(f"Nettoyage périodique planifié toutes les {interval/1000} secondes")
    
    @classmethod
    def _optimize_ui_settings(cls, root):
        """
        Optimise les paramètres de l'interface utilisateur
        
        Args:
            root: Fenêtre principale de l'application
        """
        # Réduire la fréquence de mise à jour de l'interface
        if hasattr(root, 'tk'):
            root.tk.call('tk', 'scaling', 1.0)  # Échelle de l'interface
            
            # Désactiver les animations inutiles si possible
            try:
                root.tk.call('set', '::tk::AlwaysShowSelection', '0')
            except Exception:
                pass
        
        logger.debug("Paramètres d'interface optimisés")
    
    @classmethod
    def _optimize_widget_rendering(cls, root):
        """
        Optimise le rendu des widgets pour réduire les hachures
        
        Args:
            root: Fenêtre principale de l'application
        """
        try:
            # Optimisations de base pour l'interface
            if hasattr(root, 'tk'):
                # Optimiser le rendu des images
                root.tk.call('image', 'create', 'photo', 'empty', '-width', '1', '-height', '1')
                
                # Optimisations spécifiques à Windows
                if sys.platform == 'win32':
                    try:
                        # Optimisations douces pour Windows
                        root.tk.call('package', 'require', 'Tk')
                    except Exception:
                        pass
            
            logger.debug("Rendu des widgets optimisé")
        except Exception as e:
            logger.warning(f"Erreur lors de l'optimisation du rendu des widgets: {e}")
    
    @staticmethod
    def debounce(delay=None):
        """
        Décorateur pour appliquer un debounce sur une fonction
        N'exécute la fonction qu'après un délai d'inactivité
        
        Args:
            delay: Délai en millisecondes (utilise DEBOUNCE_DELAY par défaut)
        """
        if delay is None:
            delay = PerformanceOptimizer.DEBOUNCE_DELAY
            
        def decorator(func):
            timer = None
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                nonlocal timer
                
                if timer:
                    timer.cancel()
                
                def call_function():
                    return func(*args, **kwargs)
                
                # Utiliser after de Tkinter si disponible
                if len(args) > 0 and hasattr(args[0], 'after'):
                    if timer:
                        args[0].after_cancel(timer)
                    timer = args[0].after(delay, call_function)
                else:
                    # Fallback sur threading.Timer
                    timer = threading.Timer(delay / 1000.0, call_function)
                    timer.daemon = True
                    timer.start()
            
            return wrapper
        
        return decorator
    
    @staticmethod
    def throttle(delay=None):
        """
        Décorateur pour appliquer un throttle sur une fonction
        Limite la fréquence d'exécution de la fonction
        
        Args:
            delay: Délai en millisecondes (utilise THROTTLE_DELAY par défaut)
        """
        if delay is None:
            delay = PerformanceOptimizer.THROTTLE_DELAY
            
        def decorator(func):
            last_called = 0
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                nonlocal last_called
                
                current_time = time.time() * 1000
                elapsed = current_time - last_called
                
                if elapsed >= delay:
                    last_called = current_time
                    return func(*args, **kwargs)
            
            return wrapper
        
        return decorator
    
    @staticmethod
    def cache(maxsize=None):
        """
        Décorateur pour mettre en cache les résultats d'une fonction
        
        Args:
            maxsize: Taille maximale du cache (utilise CACHE_SIZE par défaut)
        """
        if maxsize is None:
            maxsize = PerformanceOptimizer.CACHE_SIZE
            
        def decorator(func):
            return lru_cache(maxsize=maxsize)(func)
        
        return decorator
    
    @staticmethod
    def async_task(func):
        """
        Décorateur pour exécuter une fonction dans un thread séparé
        
        Args:
            func: Fonction à exécuter de manière asynchrone
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
            thread.start()
            return thread
        
        return wrapper
    
    @staticmethod
    def optimize_view_loading(view_class):
        """
        Décorateur pour optimiser le chargement des vues
        
        Args:
            view_class: Classe de vue à optimiser
        """
        original_init = view_class.__init__
        
        @wraps(original_init)
        def optimized_init(self, *args, **kwargs):
            # Appeler l'initialisation originale
            original_init(self, *args, **kwargs)
            
            # Optimiser le chargement des widgets
            if hasattr(self, 'frame') and hasattr(self.frame, 'update_idletasks'):
                # Désactiver les mises à jour pendant l'initialisation
                self.frame.update_idletasks()
            
            # Optimiser le rendu des grilles
            for attr_name in dir(self):
                try:
                    attr = getattr(self, attr_name)
                    if attr_name.endswith('_grid') and hasattr(attr, 'grid_propagate'):
                        # Empêcher le redimensionnement automatique des grilles
                        attr.grid_propagate(False)
                except Exception:
                    pass
        
        # Remplacer la méthode d'initialisation
        view_class.__init__ = optimized_init
        return view_class
    
    @staticmethod
    def lazy_loading(delay=100):
        """
        Décorateur pour charger une méthode de manière différée
        
        Args:
            delay: Délai en millisecondes avant le chargement
        """
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                if hasattr(self, 'parent') and hasattr(self.parent, 'after'):
                    self.parent.after(delay, lambda: func(self, *args, **kwargs))
                else:
                    # Fallback si parent.after n'est pas disponible
                    threading.Timer(delay / 1000.0, lambda: func(self, *args, **kwargs)).start()
            return wrapper
        return decorator
    
    @classmethod
    def record_metric(cls, category, value):
        """
        Enregistre une métrique de performance
        
        Args:
            category: Catégorie de la métrique
            value: Valeur à enregistrer
        """
        if category in cls.metrics:
            cls.metrics[category].append(value)
            # Limiter la taille des listes de métriques
            if len(cls.metrics[category]) > 100:
                cls.metrics[category] = cls.metrics[category][-100:]
        else:
            cls.metrics[category] = [value]
    
    @classmethod
    def get_average_metric(cls, category):
        """
        Calcule la moyenne d'une métrique
        
        Args:
            category: Catégorie de la métrique
            
        Returns:
            float: Moyenne de la métrique
        """
        if category in cls.metrics and cls.metrics[category]:
            return sum(cls.metrics[category]) / len(cls.metrics[category])
        return 0
    
    @classmethod
    def get_performance_report(cls):
        """
        Génère un rapport de performance
        
        Returns:
            dict: Rapport de performance
        """
        report = {}
        for category, values in cls.metrics.items():
            if values:
                report[category] = {
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
            else:
                report[category] = {
                    'average': 0,
                    'min': 0,
                    'max': 0,
                    'count': 0
                }
        
        # Ajouter des informations sur la mémoire
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            report['memory'] = {
                'rss': memory_info.rss / (1024 * 1024),  # En Mo
                'vms': memory_info.vms / (1024 * 1024)   # En Mo
            }
        except ImportError:
            logger.warning("Module psutil non disponible, informations mémoire limitées")
            import gc
            report['memory'] = {
                'gc_objects': len(gc.get_objects()),
                'gc_stats': gc.get_stats() if hasattr(gc, 'get_stats') else None
            }
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des informations mémoire: {e}")
            report['memory'] = {'rss': 0, 'vms': 0}
        
        return report

# Fonction pour mesurer le temps d'exécution d'une fonction
def measure_time(func):
    """
    Décorateur pour mesurer le temps d'exécution d'une fonction
    
    Args:
        func: Fonction à mesurer
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        
        # Enregistrer la métrique
        category = f"func_{func.__name__}"
        PerformanceOptimizer.record_metric(category, elapsed_time)
        
        # Journaliser si le temps est significatif
        if elapsed_time > 0.1:  # Plus de 100ms
            logger.debug(f"Performance: {func.__name__} a pris {elapsed_time:.3f}s")
        
        return result
    
    return wrapper

# Alias pour les décorateurs
debounce = PerformanceOptimizer.debounce
throttle = PerformanceOptimizer.throttle
cache = PerformanceOptimizer.cache
async_task = PerformanceOptimizer.async_task
optimize_view = PerformanceOptimizer.optimize_view_loading
lazy_load = PerformanceOptimizer.lazy_loading 