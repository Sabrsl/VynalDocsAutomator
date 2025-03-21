#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour vérifier les optimisations de performance
"""

import os
import sys
import time
import logging
import threading
import customtkinter as ctk

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PerformanceTest")

def test_performance_optimizer():
    """Teste le module d'optimisation des performances"""
    logger.info("Test du module d'optimisation des performances")
    
    try:
        from utils.performance_optimizer import (
            PerformanceOptimizer, 
            debounce, 
            throttle, 
            cache, 
            async_task,
            measure_time
        )
        
        # Créer une fenêtre de test
        root = ctk.CTk()
        root.title("Test Performance")
        root.geometry("400x300")
        
        # Appliquer les optimisations
        PerformanceOptimizer.optimize_application(root)
        
        # Tester le debounce
        debounce_counter = 0
        
        @debounce(300)
        def debounced_function():
            nonlocal debounce_counter
            debounce_counter += 1
            logger.info(f"Fonction debounce appelée (compteur: {debounce_counter})")
        
        # Tester le throttle
        throttle_counter = 0
        
        @throttle(500)
        def throttled_function():
            nonlocal throttle_counter
            throttle_counter += 1
            logger.info(f"Fonction throttle appelée (compteur: {throttle_counter})")
        
        # Tester le cache
        cache_counter = 0
        
        @cache(10)
        def cached_function(param):
            nonlocal cache_counter
            cache_counter += 1
            logger.info(f"Fonction cache appelée avec {param} (compteur: {cache_counter})")
            return param * 2
        
        # Tester async_task
        async_counter = 0
        
        @async_task
        def async_function(sleep_time):
            nonlocal async_counter
            time.sleep(sleep_time)
            async_counter += 1
            logger.info(f"Fonction async terminée (compteur: {async_counter})")
        
        # Tester measure_time
        @measure_time
        def slow_function():
            time.sleep(0.2)
            return "Résultat"
        
        # Créer l'interface de test
        frame = ctk.CTkFrame(root)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre
        title = ctk.CTkLabel(
            frame, 
            text="Test des optimisations de performance",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=10)
        
        # Boutons de test
        debounce_btn = ctk.CTkButton(
            frame,
            text="Test Debounce",
            command=lambda: [debounced_function() for _ in range(5)]
        )
        debounce_btn.pack(pady=5)
        
        throttle_btn = ctk.CTkButton(
            frame,
            text="Test Throttle",
            command=lambda: [throttled_function() for _ in range(5)]
        )
        throttle_btn.pack(pady=5)
        
        cache_btn = ctk.CTkButton(
            frame,
            text="Test Cache",
            command=lambda: [cached_function(i % 3) for i in range(10)]
        )
        cache_btn.pack(pady=5)
        
        async_btn = ctk.CTkButton(
            frame,
            text="Test Async",
            command=lambda: async_function(0.5)
        )
        async_btn.pack(pady=5)
        
        measure_btn = ctk.CTkButton(
            frame,
            text="Test Measure Time",
            command=slow_function
        )
        measure_btn.pack(pady=5)
        
        report_btn = ctk.CTkButton(
            frame,
            text="Afficher Rapport",
            command=lambda: logger.info(f"Rapport: {PerformanceOptimizer.get_performance_report()}")
        )
        report_btn.pack(pady=5)
        
        # Lancer la boucle principale
        root.mainloop()
        
        return True
    except ImportError as e:
        logger.error(f"Module d'optimisation non disponible: {e}")
        return False
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    # Ajouter le répertoire parent au chemin de recherche
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    
    # Exécuter le test
    success = test_performance_optimizer()
    
    if success:
        logger.info("Test réussi!")
        sys.exit(0)
    else:
        logger.error("Test échoué!")
        sys.exit(1) 