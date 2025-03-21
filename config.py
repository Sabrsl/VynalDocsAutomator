#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration globale de l'application Vynal Docs Automator
"""

import os
import sys
import logging
from datetime import datetime

# Constantes de l'application
APP_NAME = "Vynal Docs Automator"
WINDOW_SIZE = "1200x700"
MIN_WINDOW_SIZE = (800, 600)
REQUIRED_DIRECTORIES = [
    "data",
    "data/clients",
    "data/documents",
    "data/templates",
    "data/backup",
    "logs",
    "exports",
    "plugins",
    "error_logs"
]
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ajouter le répertoire de base au PYTHONPATH
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Configuration du logging
def setup_logging():
    """Configure le système de logging"""
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        log_file = os.path.join(LOGS_DIR, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format=LOG_FORMAT,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        return logging.getLogger(APP_NAME)
    except Exception as e:
        print(f"Erreur lors de la configuration du logging: {e}")
        sys.exit(1)

# Configuration des répertoires
def ensure_directories():
    """Crée les répertoires nécessaires s'ils n'existent pas"""
    for directory in REQUIRED_DIRECTORIES:
        try:
            path = os.path.join(BASE_DIR, directory)
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            print(f"Erreur lors de la création du répertoire {directory}: {e}")
            sys.exit(1)

# Version de l'application
APP_VERSION = "1.0.0"

# Nom de l'entreprise
COMPANY_NAME = "Vynal Agency LTD"

# Configuration par défaut
DEFAULT_CONFIG = {
    "app": {
        "name": APP_NAME,
        "version": APP_VERSION,
        "company_name": COMPANY_NAME,
        "theme": "dark",
        "language": "fr"
    }
} 