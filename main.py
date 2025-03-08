#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vynal Docs Automator - Application de gestion et génération de documents
Point d'entrée principal de l'application
"""

import os
import sys
import json
import logging
from datetime import datetime
import customtkinter as ctk
from PIL import Image

# Importation des modules de l'application
from controllers.app_controller import AppController
from views.main_view import MainView
from models.app_model import AppModel
from utils.config_manager import ConfigManager

# Configuration des logs
def setup_logging():
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("VynalDocsAutomator")

# Vérification des répertoires nécessaires
def ensure_directories():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dirs = [
        os.path.join(base_dir, "data"),
        os.path.join(base_dir, "data", "clients"),
        os.path.join(base_dir, "data", "documents"),
        os.path.join(base_dir, "data", "templates"),
        os.path.join(base_dir, "data", "backup"),
        os.path.join(base_dir, "logs")
    ]
    
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Répertoire vérifié: {directory}")

# Fonction principale
def main():
    # Configuration de l'application CustomTkinter
    ctk.set_appearance_mode("System")  # Modes: "System", "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Thèmes: "blue", "green", "dark-blue"
    
    # Création des objets principaux
    config = ConfigManager()
    app_model = AppModel(config)
    
    # Création de la fenêtre principale
    root = ctk.CTk()
    root.title("Vynal Docs Automator")
    root.geometry("1200x700")
    root.minsize(800, 600)
    
    # Chargement de l'icône
    try:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            icon = Image.open(icon_path)
            # Sur Windows, utiliser photoimage
            if sys.platform.startswith('win'):
                from PIL import ImageTk
                icon_tk = ImageTk.PhotoImage(icon)
                root.iconphoto(True, icon_tk)
            # Sur macOS et Linux
            else:
                root.iconphoto(True, ctk.CTkImage(icon))
    except Exception as e:
        logger.warning(f"Impossible de charger l'icône: {e}")
    
    # Création de la vue principale
    main_view = MainView(root, app_model)
    
    # Création du contrôleur
    controller = AppController(app_model, main_view)
    
    # Démarrage de l'application
    logger.info("Application démarrée")
    root.mainloop()

if __name__ == "__main__":
    # Configuration des logs
    logger = setup_logging()
    logger.info("Démarrage de Vynal Docs Automator")
    
    try:
        # Vérification des répertoires
        ensure_directories()
        
        # Lancement de l'application
        main()
        
        logger.info("Fermeture normale de l'application")
    except Exception as e:
        logger.critical(f"Erreur critique: {e}", exc_info=True)
        sys.exit(1)