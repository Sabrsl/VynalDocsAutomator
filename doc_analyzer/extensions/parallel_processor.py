"""
Processeur parallèle pour l'analyse de documents
"""

import logging
import threading
import queue
import concurrent.futures
from typing import List, Dict, Any, Optional, Callable
from ..analyzer import Analysis

logger = logging.getLogger("VynalDocsAutomator.Extensions.Parallel")

class ParallelProcessor:
    """
    Gère le traitement parallèle des documents
    S'intègre avec l'analyseur existant sans le modifier
    """
    
    def __init__(self, analyzer: Analysis, max_workers: int = 4):
        """
        Initialise le processeur parallèle
        
        Args:
            analyzer: Instance de l'analyseur existant
            max_workers: Nombre maximum de workers
        """
        self.analyzer = analyzer
        self.max_workers = max_workers
        self._results_queue = queue.Queue()
        self._error_queue = queue.Queue()
        self._progress_callback = None
        
        logger.info(f"Processeur parallèle initialisé avec {max_workers} workers")
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """
        Définit la fonction de callback pour le suivi de progression
        
        Args:
            callback: Fonction appelée avec (processed, total, current_file)
        """
        self._progress_callback = callback
    
    def process_batch(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Traite un lot de documents en parallèle
        
        Args:
            file_paths: Liste des chemins de fichiers à analyser
            
        Returns:
            Dict[str, Any]: Résultats d'analyse pour chaque fichier
        """
        total_files = len(file_paths)
        processed_files = 0
        results = {}
        
        def process_file(file_path: str):
            try:
                logger.debug(f"Analyse de {file_path}")
                result = self.analyzer.analyze_document(file_path)
                self._results_queue.put((file_path, result))
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse de {file_path}: {e}")
                self._error_queue.put((file_path, str(e)))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Soumettre tous les fichiers pour traitement
            futures = [executor.submit(process_file, file_path) for file_path in file_paths]
            
            # Collecter les résultats au fur et à mesure
            while processed_files < total_files:
                # Vérifier les résultats
                try:
                    file_path, result = self._results_queue.get_nowait()
                    results[file_path] = result
                    processed_files += 1
                    
                    if self._progress_callback:
                        self._progress_callback(processed_files, total_files, file_path)
                except queue.Empty:
                    pass
                
                # Vérifier les erreurs
                try:
                    file_path, error = self._error_queue.get_nowait()
                    results[file_path] = {"error": error, "status": "failed"}
                    processed_files += 1
                    
                    if self._progress_callback:
                        self._progress_callback(processed_files, total_files, file_path)
                except queue.Empty:
                    pass
        
        logger.info(f"Traitement parallèle terminé: {processed_files}/{total_files} fichiers traités")
        return results
    
    def process_with_dependencies(self, file_paths: List[str], dependencies: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Traite les documents en parallèle en respectant les dépendances
        
        Args:
            file_paths: Liste des chemins de fichiers à analyser
            dependencies: Dictionnaire des dépendances entre fichiers
            
        Returns:
            Dict[str, Any]: Résultats d'analyse pour chaque fichier
        """
        results = {}
        processed = set()
        processing = set()
        
        def can_process(file_path: str) -> bool:
            if file_path not in dependencies:
                return True
            return all(dep in processed for dep in dependencies[file_path])
        
        def process_file(file_path: str):
            if file_path in processing:
                return
            if not can_process(file_path):
                return
            
            processing.add(file_path)
            try:
                result = self.analyzer.analyze_document(file_path)
                self._results_queue.put((file_path, result))
            except Exception as e:
                self._error_queue.put((file_path, str(e)))
            finally:
                processing.remove(file_path)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while len(processed) < len(file_paths):
                # Trouver les fichiers qui peuvent être traités
                processable = [f for f in file_paths if f not in processed and can_process(f)]
                
                if not processable:
                    # Attendre les résultats si aucun fichier ne peut être traité
                    try:
                        file_path, result = self._results_queue.get(timeout=1)
                        results[file_path] = result
                        processed.add(file_path)
                        
                        if self._progress_callback:
                            self._progress_callback(len(processed), len(file_paths), file_path)
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.error(f"Erreur inattendue: {e}")
                        continue
                
                # Soumettre les fichiers processables
                for file_path in processable:
                    if file_path not in processing:
                        executor.submit(process_file, file_path)
                
                # Vérifier les erreurs
                try:
                    file_path, error = self._error_queue.get_nowait()
                    results[file_path] = {"error": error, "status": "failed"}
                    processed.add(file_path)
                    
                    if self._progress_callback:
                        self._progress_callback(len(processed), len(file_paths), file_path)
                except queue.Empty:
                    pass
        
        return results 