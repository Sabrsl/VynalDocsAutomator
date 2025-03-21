#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fonctions d'initialisation de l'application
"""

import os
import logging
import asyncio
from doc_analyzer.analyzer import DocumentAnalyzer

def setup_logging():
    """Configure le système de journalisation"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def ensure_directories():
    """Crée les répertoires nécessaires s'ils n'existent pas"""
    directories = [
        "data",
        "data/clients",
        "data/templates",
        "data/documents",
        "data/cache",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

async def setup_doc_analyzer():
    """Configure et initialise l'analyseur de documents"""
    try:
        analyzer = DocumentAnalyzer()
        await analyzer.initialize()
        return analyzer
    except Exception as e:
        logging.getLogger("VynalDocsAutomator").error(f"Erreur lors de l'initialisation de l'analyseur: {e}")
        return None 