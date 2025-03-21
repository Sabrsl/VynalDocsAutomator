#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de chargement différé des modèles
Charge d'abord les métadonnées, puis les détails complets uniquement lors de la sélection
"""

import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VynalDocsAutomator.LazyLoader")

class ModelType(Enum):
    """Types de modèles supportés"""
    CLIENT = "client"
    DOCUMENT = "document"
    TEMPLATE = "template"

@dataclass
class ModelMetadata:
    """Métadonnées d'un modèle"""
    id: str
    name: str
    type: ModelType
    created_at: str
    updated_at: str
    summary: str
    last_accessed: float = 0.0

class LazyModelLoader:
    """Gestionnaire de chargement différé des modèles"""
    
    def __init__(self, cache_ttl: int = 3600, max_cache_size: int = 1000):
        """
        Initialise le chargeur différé
        
        Args:
            cache_ttl: Durée de vie du cache en secondes
            max_cache_size: Taille maximale du cache par type de modèle
        """
        self._metadata_cache: Dict[str, Dict[str, ModelMetadata]] = {
            model_type.value: {} for model_type in ModelType
        }
        self._full_data_cache: Dict[str, Dict[str, Any]] = {
            model_type.value: {} for model_type in ModelType
        }
        self._load_callbacks: Dict[ModelType, Callable] = {}
        self._metadata_callbacks: Dict[ModelType, Callable] = {}
        self._cache_ttl = cache_ttl
        self._max_cache_size = max_cache_size
        
    def register_callbacks(self, model_type: ModelType, 
                         load_callback: Callable[[str], Any],
                         metadata_callback: Callable[[], List[ModelMetadata]]):
        """
        Enregistre les callbacks pour un type de modèle
        
        Args:
            model_type: Type de modèle
            load_callback: Fonction pour charger les données complètes
            metadata_callback: Fonction pour charger les métadonnées
        """
        self._load_callbacks[model_type] = load_callback
        self._metadata_callbacks[model_type] = metadata_callback
        
    def load_metadata(self, model_type: ModelType) -> List[ModelMetadata]:
        """
        Charge les métadonnées pour un type de modèle
        
        Args:
            model_type: Type de modèle
            
        Returns:
            Liste des métadonnées
        """
        if model_type not in self._metadata_callbacks:
            raise ValueError(f"Pas de callback enregistré pour {model_type}")
            
        try:
            metadata_list = self._metadata_callbacks[model_type]()
            current_time = time.time()
            
            # Met à jour le cache avec les nouvelles métadonnées
            for metadata in metadata_list:
                metadata.last_accessed = current_time
                self._metadata_cache[model_type.value][metadata.id] = metadata
                
            return metadata_list
        except Exception as e:
            logger.error(f"Erreur lors du chargement des métadonnées: {e}")
            return []
            
    def get_model(self, model_type: ModelType, model_id: str) -> Optional[Any]:
        """
        Récupère un modèle complet par son ID
        
        Args:
            model_type: Type de modèle
            model_id: ID du modèle
            
        Returns:
            Modèle complet ou None si non trouvé
        """
        if model_type not in self._load_callbacks:
            raise ValueError(f"Pas de callback enregistré pour {model_type}")
            
        # Vérifie le cache
        cache = self._full_data_cache[model_type.value]
        if model_id in cache:
            cache[model_id]["last_accessed"] = time.time()
            return cache[model_id]["data"]
            
        try:
            # Charge les données complètes
            model_data = self._load_callbacks[model_type](model_id)
            
            if model_data:
                # Met à jour le cache
                cache[model_id] = {
                    "data": model_data,
                    "last_accessed": time.time()
                }
                
                # Gère la taille maximale du cache
                self._cleanup_cache(model_type)
                
            return model_data
        except Exception as e:
            logger.error(f"Erreur lors du chargement du modèle {model_id}: {e}")
            return None
            
    def get_metadata(self, model_type: ModelType, model_id: str) -> Optional[ModelMetadata]:
        """
        Récupère les métadonnées d'un modèle
        
        Args:
            model_type: Type de modèle
            model_id: ID du modèle
            
        Returns:
            Métadonnées ou None si non trouvées
        """
        metadata = self._metadata_cache[model_type.value].get(model_id)
        if metadata:
            metadata.last_accessed = time.time()
        return metadata
        
    def _cleanup_cache(self, model_type: ModelType):
        """
        Nettoie le cache si nécessaire
        
        Args:
            model_type: Type de modèle
        """
        cache = self._full_data_cache[model_type.value]
        if len(cache) > self._max_cache_size:
            # Supprime les entrées les plus anciennes
            sorted_entries = sorted(cache.items(), key=lambda x: x[1]["last_accessed"])
            entries_to_remove = len(cache) - self._max_cache_size
            for key, _ in sorted_entries[:entries_to_remove]:
                del cache[key]
                
    def clear_cache(self, model_type: Optional[ModelType] = None):
        """
        Vide le cache
        
        Args:
            model_type: Type de modèle spécifique à vider (None pour tout vider)
        """
        if model_type is None:
            self._metadata_cache = {
                model_type.value: {} for model_type in ModelType
            }
            self._full_data_cache = {
                model_type.value: {} for model_type in ModelType
            }
        else:
            self._metadata_cache[model_type.value] = {}
            self._full_data_cache[model_type.value] = {}
            
    def get_cache_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Retourne les statistiques du cache
        
        Returns:
            Statistiques du cache par type de modèle
        """
        return {
            model_type.value: {
                "metadata_count": len(self._metadata_cache[model_type.value]),
                "full_data_count": len(self._full_data_cache[model_type.value])
            }
            for model_type in ModelType
        } 