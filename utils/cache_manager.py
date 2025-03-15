#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire de cache pour l'application
Implémente un système de cache efficace avec différentes stratégies
"""

import os
import json
import time
import logging
import threading
from typing import Any, Dict, Optional
from functools import lru_cache
import gc

logger = logging.getLogger("VynalDocsAutomator.CacheManager")

class CacheEntry:
    """Représente une entrée dans le cache avec TTL"""
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.timestamp = time.time()
        self.ttl = ttl

    def is_expired(self) -> bool:
        """Vérifie si l'entrée est expirée"""
        return time.time() - self.timestamp > self.ttl

class CacheManager:
    """Gestionnaire de cache principal"""
    
    def __init__(self, config_path: str = "config/cache_config.json"):
        """Initialise le gestionnaire de cache"""
        self._cache: Dict[str, Dict[str, CacheEntry]] = {}
        self._lock = threading.RLock()
        self._config = self._load_config(config_path)
        self._setup_cache_types()
        self._start_cleanup_thread()

    def _load_config(self, config_path: str) -> dict:
        """Charge la configuration du cache"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info("Configuration du cache chargée avec succès")
            return config
        except Exception as e:
            logger.warning(f"Erreur lors du chargement de la configuration du cache: {e}")
            return {
                "enabled": True,
                "cache_types": {
                    "documents": {"max_size": 1000, "ttl": 3600, "strategy": "lru"},
                    "templates": {"max_size": 500, "ttl": 7200, "strategy": "lru"},
                    "clients": {"max_size": 200, "ttl": 3600, "strategy": "lru"},
                    "search": {"max_size": 100, "ttl": 300, "strategy": "lru"}
                }
            }

    def _setup_cache_types(self):
        """Configure les différents types de cache"""
        for cache_type, config in self._config["cache_types"].items():
            self._cache[cache_type] = {}

    def _start_cleanup_thread(self):
        """Démarre le thread de nettoyage du cache"""
        def cleanup_task():
            while True:
                self.cleanup()
                time.sleep(self._config["file_cache"]["cleanup_interval"])

        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()

    @lru_cache(maxsize=1000)
    def get(self, cache_type: str, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        if not self._config["enabled"]:
            return None

        with self._lock:
            if cache_type not in self._cache:
                return None

            entry = self._cache[cache_type].get(key)
            if entry is None:
                return None

            if entry.is_expired():
                del self._cache[cache_type][key]
                return None

            return entry.value

    def set(self, cache_type: str, key: str, value: Any) -> None:
        """Stocke une valeur dans le cache"""
        if not self._config["enabled"]:
            return

        with self._lock:
            if cache_type not in self._cache:
                return

            config = self._config["cache_types"][cache_type]
            ttl = config["ttl"]

            # Vérifier la taille du cache
            if len(self._cache[cache_type]) >= config["max_size"]:
                # Supprimer l'entrée la plus ancienne
                oldest_key = min(
                    self._cache[cache_type].keys(),
                    key=lambda k: self._cache[cache_type][k].timestamp
                )
                del self._cache[cache_type][oldest_key]

            self._cache[cache_type][key] = CacheEntry(value, ttl)

    def invalidate(self, cache_type: str, key: str) -> None:
        """Invalide une entrée du cache"""
        with self._lock:
            if cache_type in self._cache and key in self._cache[cache_type]:
                del self._cache[cache_type][key]

    def cleanup(self) -> None:
        """Nettoie les entrées expirées du cache"""
        with self._lock:
            for cache_type in self._cache:
                expired_keys = [
                    key for key, entry in self._cache[cache_type].items()
                    if entry.is_expired()
                ]
                for key in expired_keys:
                    del self._cache[cache_type][key]

        # Vérifier l'utilisation de la mémoire
        if gc.get_count()[0] > self._config["memory_cache"]["gc_threshold"]:
            gc.collect()

    def clear(self) -> None:
        """Vide complètement le cache"""
        with self._lock:
            for cache_type in self._cache:
                self._cache[cache_type].clear()
            gc.collect()

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """Retourne les statistiques du cache"""
        stats = {}
        with self._lock:
            for cache_type in self._cache:
                stats[cache_type] = {
                    "size": len(self._cache[cache_type]),
                    "max_size": self._config["cache_types"][cache_type]["max_size"]
                }
        return stats 