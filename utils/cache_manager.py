#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de gestion du cache pour l'application Vynal Docs Automator
Gère le cache des documents, templates et clients avec prédiction d'accès
"""

import os
import json
import time
import logging
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict

from .predictive_loader import PredictiveLoader

logger = logging.getLogger("VynalDocsAutomator.CacheManager")

class CacheEntry:
    """Classe représentant une entrée du cache"""
    
    def __init__(self, data: Any, ttl: int = 3600):
        """
        Initialise une entrée du cache
        
        Args:
            data: Données à mettre en cache
            ttl: Durée de vie en secondes
        """
        self.data = data
        self.created_at = time.time()
        self.last_access = time.time()
        self.access_count = 0
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """
        Vérifie si l'entrée est expirée
        
        Returns:
            bool: True si expirée, False sinon
        """
        return time.time() - self.created_at > self.ttl
    
    def update_access(self) -> None:
        """Met à jour les statistiques d'accès"""
        self.last_access = time.time()
        self.access_count += 1

class CacheManager:
    """Gestionnaire de cache avec prédiction d'accès"""
    
    def __init__(self):
        """Initialise le gestionnaire de cache"""
        self._caches: Dict[str, Dict[str, CacheEntry]] = defaultdict(dict)
        self._config = self._load_config()
        self._predictive_loader = PredictiveLoader(self)
        self._lock = threading.Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = self._config.get("cleanup_interval", 3600)
        
        # Initialiser les caches selon la configuration
        for cache_type in self._config.get("cache_types", {}):
            self._caches[cache_type] = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Charge la configuration du cache
        
        Returns:
            Dict[str, Any]: Configuration
        """
        try:
            config_path = os.path.join("config", "cache_config.json")
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration du cache: {e}")
            return {}
    
    def get(self, cache_type: str, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache
        
        Args:
            cache_type: Type de cache (documents, templates, clients)
            key: Clé de l'entrée
            
        Returns:
            Optional[Any]: Valeur en cache ou None
        """
        with self._lock:
            if cache_type not in self._caches:
                return None
            
            entry = self._caches[cache_type].get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._caches[cache_type][key]
                return None
            
            entry.update_access()
            self._predictive_loader.record_access(cache_type, key)
            return entry.data
    
    def set(self, cache_type: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Stocke une valeur dans le cache
        
        Args:
            cache_type: Type de cache
            key: Clé de l'entrée
            value: Valeur à stocker
            ttl: Durée de vie optionnelle
        """
        with self._lock:
            if cache_type not in self._caches:
                self._caches[cache_type] = {}
            
            if ttl is None:
                ttl = self._config.get("cache_types", {}).get(cache_type, {}).get("ttl", 3600)
            
            self._caches[cache_type][key] = CacheEntry(value, ttl)
    
    def delete(self, cache_type: str, key: str) -> None:
        """
        Supprime une entrée du cache
        
        Args:
            cache_type: Type de cache
            key: Clé de l'entrée
        """
        with self._lock:
            if cache_type in self._caches and key in self._caches[cache_type]:
                del self._caches[cache_type][key]
    
    def clear(self, cache_type: Optional[str] = None) -> None:
        """
        Vide le cache
        
        Args:
            cache_type: Type de cache optionnel
        """
        with self._lock:
            if cache_type is None:
                self._caches.clear()
            elif cache_type in self._caches:
                self._caches[cache_type].clear()
    
    def cleanup(self) -> None:
        """Nettoie les entrées expirées"""
        with self._lock:
            current_time = time.time()
            if current_time - self._last_cleanup < self._cleanup_interval:
                return
            
            for cache_type in list(self._caches.keys()):
                self._caches[cache_type] = {
                    k: v for k, v in self._caches[cache_type].items()
                    if not v.is_expired()
                }
            
            self._last_cleanup = current_time
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du cache
        
        Returns:
            Dict[str, Any]: Statistiques
        """
        with self._lock:
            stats = {
                "cache_types": {},
                "total_entries": 0,
                "predictive_stats": self._predictive_loader.get_stats()
            }
            
            for cache_type, cache in self._caches.items():
                stats["cache_types"][cache_type] = {
                    "entries": len(cache),
                    "total_accesses": sum(entry.access_count for entry in cache.values()),
                    "avg_ttl": sum(entry.ttl for entry in cache.values()) / len(cache) if cache else 0
                }
                stats["total_entries"] += len(cache)
            
            return stats
    
    def preload_data(self) -> None:
        """Déclenche le préchargement des données"""
        self._predictive_loader.preload_data()
    
    def record_navigation(self, current_view: str) -> None:
        """
        Enregistre une navigation dans l'application
        
        Args:
            current_view: Vue actuelle
        """
        self._predictive_loader.record_navigation(current_view) 