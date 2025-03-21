#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitaire d'optimisation des opérations de fichiers
Fournit des fonctions optimisées pour la lecture/écriture de fichiers
"""

import os
import json
import gzip
import logging
from typing import Any, Dict, Optional
from functools import lru_cache
import threading
import time

logger = logging.getLogger("VynalDocsAutomator.FileOptimizer")

class FileOptimizer:
    """Gestionnaire optimisé des opérations de fichiers"""

    def __init__(self, buffer_size: int = 8192, max_cache_size: int = 100):
        """
        Initialise l'optimiseur de fichiers
        
        Args:
            buffer_size: Taille du buffer en octets
            max_cache_size: Taille maximale du cache en nombre d'entrées
        """
        self.buffer_size = buffer_size
        self.max_cache_size = max_cache_size
        self._file_locks = {}
        self._compression_enabled = True
        self._cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._last_access = {}
        self._access_patterns = {}
        self._memory_usage = 0
        self._max_memory = 512 * 1024 * 1024  # 512 MB max memory usage
        
        # Démarrer le thread de nettoyage du cache
        self._start_cache_cleanup()

    def _start_cache_cleanup(self):
        """Démarre le thread de nettoyage du cache"""
        def cleanup():
            while True:
                try:
                    self._cleanup_cache()
                    time.sleep(300)  # Nettoyer toutes les 5 minutes
                except Exception as e:
                    logger.error(f"Erreur lors du nettoyage du cache: {e}")
                    time.sleep(60)

        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()

    def _update_cache_stats(self, filepath: str, hit: bool):
        """Met à jour les statistiques du cache"""
        if hit:
            self._cache_hits += 1
        else:
            self._cache_misses += 1
        
        current_time = time.time()
        self._last_access[filepath] = current_time
        
        # Mettre à jour les modèles d'accès
        if filepath not in self._access_patterns:
            self._access_patterns[filepath] = []
        
        self._access_patterns[filepath].append(current_time)
        # Garder seulement les 10 derniers accès
        if len(self._access_patterns[filepath]) > 10:
            self._access_patterns[filepath] = self._access_patterns[filepath][-10:]

    def _predict_next_access(self, filepath: str) -> bool:
        """
        Prédit si un fichier sera bientôt accédé
        
        Args:
            filepath: Chemin du fichier
            
        Returns:
            bool: True si le fichier devrait être gardé en cache
        """
        if filepath not in self._access_patterns:
            return False
            
        accesses = self._access_patterns[filepath]
        if len(accesses) < 2:
            return False
            
        # Calculer l'intervalle moyen entre les accès
        intervals = [accesses[i] - accesses[i-1] for i in range(1, len(accesses))]
        avg_interval = sum(intervals) / len(intervals)
        
        # Si le dernier accès était il y a moins de 2x l'intervalle moyen
        last_access = accesses[-1]
        time_since_last = time.time() - last_access
        return time_since_last < avg_interval * 2

    def _estimate_memory_usage(self, data: Any) -> int:
        """
        Estime l'utilisation mémoire d'une donnée
        
        Args:
            data: Donnée à évaluer
            
        Returns:
            int: Taille estimée en octets
        """
        import sys
        return sys.getsizeof(data)

    def _cleanup_cache(self):
        """Nettoie le cache en supprimant les entrées les moins utilisées"""
        if len(self._cache) <= self.max_cache_size:
            return

        # Calculer l'utilisation mémoire totale
        total_memory = sum(self._estimate_memory_usage(data) for data in self._cache.values())
        
        # Si l'utilisation mémoire dépasse la limite
        if total_memory > self._max_memory:
            logger.warning(f"Utilisation mémoire excessive ({total_memory/1024/1024:.1f} MB), nettoyage forcé")
            items_to_remove = len(self._cache) // 2
        else:
            items_to_remove = len(self._cache) - self.max_cache_size

        # Trier les entrées par priorité
        entries = []
        for filepath in self._cache:
            priority = 1
            if self._predict_next_access(filepath):
                priority += 2
            if filepath in self._last_access:
                # Plus récent = plus prioritaire
                priority += 1 / (time.time() - self._last_access[filepath] + 1)
            entries.append((filepath, priority))

        # Trier par priorité (plus basse en premier)
        sorted_entries = sorted(entries, key=lambda x: x[1])
        
        # Supprimer les entrées les moins prioritaires
        for filepath, _ in sorted_entries[:items_to_remove]:
            self._cache.pop(filepath, None)
            self._last_access.pop(filepath, None)
            self._access_patterns.pop(filepath, None)

        logger.info(f"Cache nettoyé: {items_to_remove} entrées supprimées")

    def _get_file_lock(self, filepath: str) -> threading.Lock:
        """Obtient un verrou pour un fichier"""
        if filepath not in self._file_locks:
            self._file_locks[filepath] = threading.Lock()
        return self._file_locks[filepath]

    @lru_cache(maxsize=100)
    def read_json(self, filepath: str) -> Optional[Dict]:
        """
        Lit un fichier JSON de manière optimisée
        
        Args:
            filepath: Chemin du fichier à lire
            
        Returns:
            dict: Contenu du fichier JSON ou None en cas d'erreur
        """
        # Vérifier le cache
        if filepath in self._cache:
            self._update_cache_stats(filepath, True)
            return self._cache[filepath]

        try:
            with self._get_file_lock(filepath):
                if filepath.endswith('.gz'):
                    with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    with open(filepath, 'r', encoding='utf-8', buffering=self.buffer_size) as f:
                        data = json.load(f)

                # Mettre en cache si la taille le permet
                if len(self._cache) < self.max_cache_size:
                    self._cache[filepath] = data
                self._update_cache_stats(filepath, False)
                return data

        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier {filepath}: {e}")
            return None

    def write_json(self, filepath: str, data: Any, compress: bool = False) -> bool:
        """
        Écrit des données dans un fichier JSON de manière optimisée
        
        Args:
            filepath: Chemin du fichier à écrire
            data: Données à écrire
            compress: Si True, compresse le fichier
            
        Returns:
            bool: True si l'écriture a réussi, False sinon
        """
        try:
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with self._get_file_lock(filepath):
                # Écrire d'abord dans un fichier temporaire
                temp_path = f"{filepath}.tmp"
                
                if compress and self._compression_enabled:
                    output_path = f"{filepath}.gz"
                    with gzip.open(temp_path, 'wt', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    with open(temp_path, 'w', encoding='utf-8', buffering=self.buffer_size) as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                # Remplacer le fichier original
                if os.path.exists(filepath):
                    os.replace(temp_path, filepath)
                else:
                    os.rename(temp_path, filepath)

                # Mettre à jour le cache
                self._cache[filepath] = data
                self._update_cache_stats(filepath, False)
                return True

        except Exception as e:
            logger.error(f"Erreur lors de l'écriture du fichier {filepath}: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            return False

    def invalidate_cache(self, filepath: str = None):
        """
        Invalide une entrée du cache ou tout le cache
        
        Args:
            filepath: Chemin du fichier à invalider, ou None pour tout invalider
        """
        if filepath is None:
            self._cache.clear()
            self._last_access.clear()
        else:
            self._cache.pop(filepath, None)
            self._last_access.pop(filepath, None)

    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du cache
        
        Returns:
            dict: Statistiques du cache
        """
        total_accesses = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_accesses * 100) if total_accesses > 0 else 0

        return {
            "cache_size": len(self._cache),
            "max_cache_size": self.max_cache_size,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
            "buffer_size": self.buffer_size
        }

    @lru_cache(maxsize=1000)
    def file_exists(self, filepath: str) -> bool:
        """
        Vérifie si un fichier existe (avec cache)
        
        Args:
            filepath: Chemin du fichier à vérifier
            
        Returns:
            bool: True si le fichier existe, False sinon
        """
        return os.path.exists(filepath)

    def clear_cache(self) -> None:
        """Vide le cache des opérations sur les fichiers"""
        self.read_json.cache_clear()
        self.file_exists.cache_clear()

    def optimize_directory(self, directory: str) -> None:
        """
        Optimise un répertoire en compressant les fichiers peu utilisés
        
        Args:
            directory: Chemin du répertoire à optimiser
        """
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith('.json'):
                        filepath = os.path.join(root, file)
                        # Vérifier si le fichier est peu utilisé
                        if not self._is_frequently_accessed(filepath):
                            # Compresser le fichier
                            self._compress_file(filepath)
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation du répertoire {directory}: {e}")

    def _is_frequently_accessed(self, filepath: str) -> bool:
        """
        Vérifie si un fichier est fréquemment accédé
        
        Args:
            filepath: Chemin du fichier à vérifier
            
        Returns:
            bool: True si le fichier est fréquemment accédé
        """
        try:
            # Vérifier la date de dernier accès
            last_access = os.path.getatime(filepath)
            # Si accédé dans les dernières 24h, considéré comme fréquent
            return (time.time() - last_access) < 86400
        except:
            return True

    def _compress_file(self, filepath: str) -> None:
        """
        Compresse un fichier
        
        Args:
            filepath: Chemin du fichier à compresser
        """
        try:
            if not filepath.endswith('.gz'):
                with open(filepath, 'r', encoding='utf-8') as f_in:
                    data = json.load(f_in)
                
                gz_path = f"{filepath}.gz"
                with gzip.open(gz_path, 'wt', encoding='utf-8') as f_out:
                    json.dump(data, f_out)
                
                # Supprimer l'original après compression réussie
                os.remove(filepath)
                logger.info(f"Fichier compressé: {filepath}")
        except Exception as e:
            logger.error(f"Erreur lors de la compression du fichier {filepath}: {e}")

# Instance globale pour l'optimisation des fichiers
file_optimizer = FileOptimizer() 