"""
Gestionnaire de sauvegarde automatique pour les résultats d'analyse
"""

import os
import json
import time
import logging
import threading
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger("VynalDocsAutomator.Extensions.AutoBackup")

class AutoBackupManager:
    """
    Gère la sauvegarde automatique des résultats d'analyse
    S'intègre avec le système existant sans le modifier
    """
    
    def __init__(self, backup_dir: str, interval: int = 300, max_backups: int = 10):
        """
        Initialise le gestionnaire de sauvegarde automatique
        
        Args:
            backup_dir: Répertoire de sauvegarde
            interval: Intervalle entre les sauvegardes (en secondes)
            max_backups: Nombre maximum de sauvegardes à conserver
        """
        self.backup_dir = backup_dir
        self.interval = interval
        self.max_backups = max_backups
        
        self._stop_event = threading.Event()
        self._backup_thread = None
        self._last_results = {}
        self._backup_lock = threading.Lock()
        
        # Créer le répertoire de sauvegarde s'il n'existe pas
        os.makedirs(backup_dir, exist_ok=True)
        
        logger.info(f"Gestionnaire de sauvegarde automatique initialisé (intervalle: {interval}s)")
    
    def start(self):
        """Démarre le processus de sauvegarde automatique"""
        if self._backup_thread is not None and self._backup_thread.is_alive():
            logger.warning("Le processus de sauvegarde est déjà en cours")
            return
        
        self._stop_event.clear()
        self._backup_thread = threading.Thread(target=self._backup_loop, daemon=True)
        self._backup_thread.start()
        
        logger.info("Processus de sauvegarde automatique démarré")
    
    def stop(self):
        """Arrête le processus de sauvegarde automatique"""
        if self._backup_thread is None or not self._backup_thread.is_alive():
            return
        
        self._stop_event.set()
        self._backup_thread.join()
        self._backup_thread = None
        
        logger.info("Processus de sauvegarde automatique arrêté")
    
    def update_results(self, results: Dict[str, Any]):
        """
        Met à jour les résultats à sauvegarder
        
        Args:
            results: Nouveaux résultats d'analyse
        """
        with self._backup_lock:
            self._last_results = results.copy()
    
    def force_backup(self) -> Optional[str]:
        """
        Force une sauvegarde immédiate
        
        Returns:
            str: Chemin du fichier de sauvegarde ou None en cas d'erreur
        """
        return self._create_backup()
    
    def get_backups(self) -> List[Dict[str, Any]]:
        """
        Retourne la liste des sauvegardes disponibles
        
        Returns:
            List[Dict[str, Any]]: Liste des sauvegardes avec leurs métadonnées
        """
        backups = []
        
        for filename in os.listdir(self.backup_dir):
            if not filename.endswith('.json'):
                continue
            
            file_path = os.path.join(self.backup_dir, filename)
            try:
                stat = os.stat(file_path)
                backups.append({
                    'filename': filename,
                    'path': file_path,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'modified': datetime.fromtimestamp(stat.st_mtime)
                })
            except Exception as e:
                logger.error(f"Erreur lors de la lecture des métadonnées de {filename}: {e}")
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def restore_backup(self, backup_path: str) -> Optional[Dict[str, Any]]:
        """
        Restaure une sauvegarde
        
        Args:
            backup_path: Chemin du fichier de sauvegarde
            
        Returns:
            Dict[str, Any]: Données restaurées ou None en cas d'erreur
        """
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Sauvegarde restaurée depuis {backup_path}")
            return data
        except Exception as e:
            logger.error(f"Erreur lors de la restauration de la sauvegarde {backup_path}: {e}")
            return None
    
    def _backup_loop(self):
        """Boucle principale de sauvegarde automatique"""
        while not self._stop_event.is_set():
            try:
                self._create_backup()
                self._cleanup_old_backups()
            except Exception as e:
                logger.error(f"Erreur dans la boucle de sauvegarde: {e}")
            
            # Attendre l'intervalle ou l'arrêt
            self._stop_event.wait(self.interval)
    
    def _create_backup(self) -> Optional[str]:
        """
        Crée une nouvelle sauvegarde
        
        Returns:
            str: Chemin du fichier de sauvegarde ou None en cas d'erreur
        """
        with self._backup_lock:
            if not self._last_results:
                return None
            
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}.json")
                
                # Créer une copie temporaire
                temp_path = backup_path + '.tmp'
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(self._last_results, f, ensure_ascii=False, indent=2)
                
                # Renommer le fichier temporaire
                os.replace(temp_path, backup_path)
                
                logger.info(f"Sauvegarde créée: {backup_path}")
                return backup_path
            
            except Exception as e:
                logger.error(f"Erreur lors de la création de la sauvegarde: {e}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                return None
    
    def _cleanup_old_backups(self):
        """Nettoie les anciennes sauvegardes"""
        try:
            backups = self.get_backups()
            
            # Supprimer les sauvegardes excédentaires
            if len(backups) > self.max_backups:
                for backup in backups[self.max_backups:]:
                    try:
                        os.remove(backup['path'])
                        logger.debug(f"Ancienne sauvegarde supprimée: {backup['filename']}")
                    except Exception as e:
                        logger.error(f"Erreur lors de la suppression de {backup['filename']}: {e}")
        
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des anciennes sauvegardes: {e}")
    
    def __enter__(self):
        """Support du context manager"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support du context manager"""
        self.stop() 