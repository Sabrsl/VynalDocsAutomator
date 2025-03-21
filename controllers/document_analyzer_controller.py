#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contrôleur pour l'analyseur de documents
"""

import os
import logging
import asyncio
from typing import List, Dict, Any
from doc_analyzer.analyzer import DocumentAnalyzer

logger = logging.getLogger("VynalDocsAutomator.DocumentAnalyzerController")

class DocumentAnalyzerController:
    """Contrôleur pour l'analyseur de documents"""
    
    def __init__(self, analyzer):
        """
        Initialise le contrôleur de l'analyseur
        
        Args:
            analyzer: Instance de DocumentAnalyzer
        """
        self.analyzer = analyzer
        self.config = {}  # Configuration par défaut vide
        self.processing_queue = asyncio.Queue()
        self.processing_task = None
        self.is_processing = False
        
        logger.info("DocumentAnalyzerController initialisé")
    
    def set_config(self, config):
        """
        Définit la configuration de l'analyseur
        
        Args:
            config: Configuration à utiliser
        """
        self.config = config
        logger.info("Configuration de l'analyseur mise à jour")
    
    async def analyze_files(self, files: List[str]) -> Dict[str, Any]:
        """
        Analyse une liste de fichiers
        
        Args:
            files: Liste des chemins de fichiers à analyser
            
        Returns:
            Résultats de l'analyse
        """
        try:
            results = {}
            for file_path in files:
                if os.path.exists(file_path):
                    result = await self.analyzer.analyze_document(file_path)
                    results[file_path] = result
                else:
                    logger.warning(f"Fichier non trouvé: {file_path}")
            return results
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des fichiers: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Nettoie les ressources"""
        try:
            if self.analyzer:
                await self.analyzer.cleanup()
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage de l'analyseur: {e}") 