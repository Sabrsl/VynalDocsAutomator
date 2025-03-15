#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de lancement de Vynal Docs Automator
Configure l'environnement Python et lance l'application
"""

import os
import sys
import logging
from datetime import datetime

# Configuration du logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("VynalDocsAutomator.Launcher")

def setup_environment():
    """Configure l'environnement Python"""
    try:
        # Ajouter le répertoire courant au PYTHONPATH
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            logger.info(f"Répertoire ajouté au PYTHONPATH: {current_dir}")
        
        # Créer les répertoires nécessaires
        required_dirs = [
            "data",
            "data/clients",
            "data/documents",
            "data/templates",
            "data/backup",
            "logs",
            "temp_docs"
        ]
        
        for directory in required_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Répertoire créé: {directory}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la configuration de l'environnement: {e}")
        return False

def main():
    """Point d'entrée principal"""
    try:
        # Configurer l'environnement
        if not setup_environment():
            logger.error("Impossible de configurer l'environnement")
            return 1
        
        # Importer et lancer l'application
        import main
        return 0
        
    except Exception as e:
        logger.error(f"Erreur lors du lancement de l'application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 