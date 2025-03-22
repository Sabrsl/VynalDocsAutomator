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
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import messagebox
import argparse
import tkinter as tk
import hashlib

# Import de la configuration globale
from config import (
    APP_NAME, WINDOW_SIZE, MIN_WINDOW_SIZE,
    REQUIRED_DIRECTORIES, setup_logging, ensure_directories
)

# Correction pour l'erreur de CTkButton lors de la destruction
# Monkey patch pour éviter l'erreur AttributeError: 'CTkButton' object has no attribute '_font'
original_ctkbutton_destroy = ctk.CTkButton.destroy
def safe_destroy(self):
    """Version sécurisée de la méthode destroy pour CTkButton"""
    try:
        # S'assurer que l'attribut _font existe avant la destruction
        if not hasattr(self, '_font'):
            self._font = None
        original_ctkbutton_destroy(self)
    except Exception as e:
        logging.getLogger(APP_NAME).warning(f"Erreur lors de la destruction d'un bouton: {e}")

# Appliquer le monkey patch
ctk.CTkButton.destroy = safe_destroy

# Importation des modules de l'application
from utils.config_manager import ConfigManager
from models.app_model import AppModel

# Cache global pour les initialisations
_initialized_components = {}
_initialized_extractors = {}
_initialized_recognizers = {}

def is_component_initialized(component_name):
    """Vérifie si un composant a déjà été initialisé"""
    return _initialized_components.get(component_name, False)

def mark_component_initialized(component_name):
    """Marque un composant comme initialisé"""
    _initialized_components[component_name] = True

def is_extractor_initialized(extractor_name):
    """Vérifie si un extracteur a déjà été initialisé"""
    return _initialized_extractors.get(extractor_name, False)

def mark_extractor_initialized(extractor_name):
    """Marque un extracteur comme initialisé"""
    _initialized_extractors[extractor_name] = True

def is_recognizer_initialized(recognizer_name):
    """Vérifie si un reconnaisseur a déjà été initialisé"""
    return _initialized_recognizers.get(recognizer_name, False)

def mark_recognizer_initialized(recognizer_name):
    """Marque un reconnaisseur comme initialisé"""
    _initialized_recognizers[recognizer_name] = True

def check_first_run():
    """Vérifie s'il s'agit de la première utilisation de l'application"""
    if is_component_initialized('first_run'):
        return True
        
    config_path = Path("config/installation.json")
    if not config_path.exists():
        logging.getLogger(APP_NAME).info("Première utilisation détectée.")
        
        # Créer le dossier config s'il n'existe pas
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Créer le fichier de configuration
        config = {
            "first_run": False,
            "installation_date": str(datetime.now()),
            "tesseract_optional": True
        }
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
    
    mark_component_initialized('first_run')
    return True

def setup_doc_analyzer():
    """
    Configure le module doc_analyzer et s'assure qu'il est accessible.
    Cette fonction est appelée à la demande lors de l'utilisation de l'OCR.
    """
    if is_component_initialized('doc_analyzer'):
        return True
        
    try:
        # Ajouter le répertoire courant au PYTHONPATH
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            logging.info(f"Répertoire ajouté au PYTHONPATH: {current_dir}")
        
        # Tester l'importation du module doc_analyzer
        from doc_analyzer.analyzer import DocumentAnalyzer
        analyzer = DocumentAnalyzer()
        logging.info("Module doc_analyzer initialisé avec succès")
        mark_component_initialized('doc_analyzer')
        return True
    except ImportError as e:
        logging.error(f"Erreur d'importation du module doc_analyzer: {e}")
        return False
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation de doc_analyzer: {e}")
        return False

def ensure_critical_directories():
    """Crée uniquement les répertoires critiques nécessaires au démarrage"""
    if is_component_initialized('directories'):
        return
        
    critical_dirs = ["config", "logs"]
    for dir_name in critical_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Répertoire critique créé: {dir_name}")
    
    mark_component_initialized('directories')

def initialize_ocr():
    """Initialise l'OCR de manière non bloquante"""
    if is_component_initialized('ocr'):
        return
        
    try:
        from utils.ocr import check_tesseract
        check_tesseract()
        mark_component_initialized('ocr')
    except Exception as e:
        logging.warning(f"OCR non disponible - fonctionnalités limitées: {e}")

def initialize_extractors():
    """Initialise les extracteurs une seule fois"""
    if is_component_initialized('extractors'):
        return
        
    try:
        from doc_analyzer.extractors.personal_data import PersonalDataExtractor
        from doc_analyzer.extractors.identity_docs import IdentityDocExtractor
        from doc_analyzer.extractors.contracts import ContractExtractor
        from doc_analyzer.extractors.business_docs import BusinessDocExtractor
        
        if not is_extractor_initialized('personal_data'):
            PersonalDataExtractor()
            mark_extractor_initialized('personal_data')
            
        if not is_extractor_initialized('identity_docs'):
            IdentityDocExtractor()
            mark_extractor_initialized('identity_docs')
            
        if not is_extractor_initialized('contracts'):
            ContractExtractor()
            mark_extractor_initialized('contracts')
            
        if not is_extractor_initialized('business_docs'):
            BusinessDocExtractor()
            mark_extractor_initialized('business_docs')
            
        mark_component_initialized('extractors')
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation des extracteurs: {e}")

def initialize_recognizers():
    """Initialise les reconnaisseurs une seule fois"""
    if is_component_initialized('recognizers'):
        return
        
    try:
        from doc_analyzer.recognizers.phone import PhoneRecognizer
        from doc_analyzer.recognizers.name import NameRecognizer
        from doc_analyzer.recognizers.id import IDRecognizer
        from doc_analyzer.recognizers.address import AddressRecognizer
        
        if not is_recognizer_initialized('phone'):
            PhoneRecognizer()
            mark_recognizer_initialized('phone')
            
        if not is_recognizer_initialized('name'):
            NameRecognizer()
            mark_recognizer_initialized('name')
            
        if not is_recognizer_initialized('id'):
            IDRecognizer()
            mark_recognizer_initialized('id')
            
        if not is_recognizer_initialized('address'):
            AddressRecognizer()
            mark_recognizer_initialized('address')
            
        mark_component_initialized('recognizers')
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation des reconnaisseurs: {e}")

def initialize_components_on_demand(component_type=None):
    """
    Initialise les composants à la demande
    
    Args:
        component_type (str, optional): Type de composant à initialiser ('ocr', 'extractors', 'recognizers')
                                        Si None, initialise tous les composants
    """
    try:
        if component_type is None or component_type == 'ocr':
            initialize_ocr()
            
        if component_type is None or component_type == 'extractors':
            initialize_extractors()
            
        if component_type is None or component_type == 'recognizers':
            initialize_recognizers()
            
        logging.info(f"Composants initialisés à la demande: {component_type if component_type else 'tous'}")
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation des composants à la demande: {e}")

def main():
    """
    Fonction principale de l'application.
    
    Configure l'apparence de l'application, crée les objets principaux 
    (config, modèle, vue, contrôleur) et démarre l'interface graphique.
    """
    try:
        # Configuration du logging
        logger = setup_logging()
        logger.info("Démarrage de l'application...")
        
        # Analyser les arguments de ligne de commande
        parser = argparse.ArgumentParser(description="Lance Vynal Docs Automator")
        parser.add_argument("--no-splash", action="store_true", help="Désactiver l'écran de démarrage")
        parser.add_argument("--no-splash-recursion", action="store_true", help="Flag interne pour éviter la récursion")
        parser.add_argument("--skip-auth", action="store_true", help="Ignorer l'authentification (déjà faite)")
        args = parser.parse_args()
        
        # Création des objets principaux
        config = ConfigManager()
        app_model = AppModel(config=config)
        
        # Initialiser le tracker d'utilisation
        from utils.usage_tracker import UsageTracker
        usage_tracker = UsageTracker()
        
        # Configuration de l'application CustomTkinter avec le thème de l'utilisateur ou par défaut
        user_theme = None
        if usage_tracker.is_user_registered():
            try:
                user_data = usage_tracker.get_user_data()
                if isinstance(user_data, dict) and "theme" in user_data:
                    user_theme = user_data["theme"].lower()
            except Exception as e:
                logger.warning(f"Erreur lors de la lecture des préférences utilisateur: {e}")
        
        # Utiliser le thème utilisateur ou la configuration globale
        theme = user_theme if user_theme else config.get("app.theme", "dark").lower()
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")
        
        # Création de la fenêtre principale
        root = ctk.CTk()
        root.title(APP_NAME)
        root.geometry(WINDOW_SIZE)
        root.minsize(MIN_WINDOW_SIZE[0], MIN_WINDOW_SIZE[1])
        
        # Configurer pour le plein écran
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # Centrer et mettre à une taille raisonnable (90% de l'écran)
        width = int(screen_width * 0.9)
        height = int(screen_height * 0.9)
        x_offset = (screen_width - width) // 2
        y_offset = (screen_height - height) // 2
        
        root.geometry(f"{width}x{height}+{x_offset}+{y_offset}")
        
        # Importer les vues ici pour éviter les importations circulaires
        from views.main_view import MainView
        from views.login_view import LoginView
        from controllers.app_controller import AppController
        
        def run_background_tasks():
            """Exécute les tâches en arrière-plan dans un thread séparé"""
            try:
                # Vérifier la première utilisation
                check_first_run()
                
                # Créer uniquement les répertoires critiques
                ensure_critical_directories()
                
                # Ne pas initialiser automatiquement ces composants au démarrage
                # Ils seront initialisés à la demande lors de leur première utilisation
                # initialize_ocr()
                # initialize_extractors()
                # initialize_recognizers()
                
                logger.info("Tâches d'initialisation en arrière-plan terminées")
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution des tâches en arrière-plan: {e}")
        
        def start_background_tasks():
            """Démarre les tâches en arrière-plan dans un thread séparé"""
            thread = threading.Thread(target=run_background_tasks, daemon=True)
            thread.start()
        
        # Vérifier s'il faut se synchroniser avec le splash screen
        sync_with_splash = False
        sync_port = None
        if not args.no_splash and not args.no_splash_recursion:
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                sync_file = os.path.join(current_dir, ".sync_splash")
                if os.path.exists(sync_file):
                    with open(sync_file, 'r') as f:
                        sync_port = int(f.read().strip())
                    sync_with_splash = True
                    logger.info(f"Synchronisation avec le splash screen sur le port {sync_port}")
            except Exception as e:
                logger.warning(f"Erreur lors de la lecture du fichier de synchronisation: {e}")
        
        # Vérifier si la protection par mot de passe est activée
        require_password = app_model.config.get("security.require_password", False)
        password_hash = app_model.config.get("security.password_hash", "")
        
        # Callback pour une fois que l'interface principale est prête
        def on_main_view_ready():
            """Appelé une fois que l'interface principale est prête"""
            # Si nous devons nous synchroniser avec le splash screen
            if sync_with_splash and sync_port:
                try:
                    import socket
                    import json
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect(('127.0.0.1', sync_port))
                    client.send(json.dumps({'status': 'ready'}).encode('utf-8'))
                    client.close()
                    logger.info("Signal 'ready' envoyé au splash screen depuis main.py")
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi du signal 'ready': {e}")
        
        # Si --skip-auth est passé, on considère que l'authentification a déjà été faite
        if args.skip_auth:
            logger.info("Authentification ignorée (déjà faite)")
            # Créer directement la vue principale et le contrôleur
            main_view = MainView(root, app_model, on_ready=on_main_view_ready)
            controller = AppController(app_model, main_view)
            
            # Démarrer les tâches en arrière-plan après l'affichage de l'interface
            root.after(100, start_background_tasks)
        elif require_password and password_hash:
            # Utiliser une approche différente: ne pas créer la vue principale tout de suite
            # La fenêtre reste vide avant la connexion
            root.withdraw()  # Cacher la fenêtre vide
            
            def on_login_success():
                """Callback appelé après une connexion réussie"""
                try:
                    logger.info("Connexion réussie, création de l'interface principale...")
                    
                    # Créer la vue principale et le contrôleur UNIQUEMENT après la connexion réussie
                    nonlocal main_view, controller
                    main_view = MainView(root, app_model, on_ready=on_main_view_ready)
                    controller = AppController(app_model, main_view)
                    
                    # Démarrer les tâches en arrière-plan
                    start_background_tasks()
                    
                    # Maintenant qu'on a tout initialisé, afficher la fenêtre
                    root.deiconify()
                    logger.info("Application complètement initialisée et affichée")
                except Exception as e:
                    logger.error(f"ERREUR CRITIQUE lors de l'initialisation après connexion: {e}")
                    messagebox.showerror("Erreur d'initialisation", 
                                        f"Une erreur est survenue lors de l'initialisation de l'application: {e}")
                    root.destroy()
            
            # Déclarer ces variables pour pouvoir les référencer dans on_login_success
            main_view = None
            controller = None
            
            # Préparer la vue de connexion
            login_view = LoginView(root, on_login_success)
            
            # Délai fixe avant d'afficher la boîte de dialogue de mot de passe
            # Ce délai est suffisant pour que le splash screen se termine
            def show_login_after_delay():
                logger.info("Délai écoulé, affichage de la boîte de dialogue de connexion")
                try:
                    login_view.show(password_hash)
                except Exception as e:
                    logger.error(f"ERREUR lors de l'affichage de la boîte de dialogue: {e}")
                    messagebox.showerror("Erreur critique", 
                                        f"Impossible d'afficher la boîte de dialogue de connexion: {e}")
                    root.destroy()
            
            # Utiliser un délai de 3 secondes pour s'assurer que le splash screen est terminé
            logger.info("Attente d'un délai avant d'afficher la boîte de dialogue de connexion...")
            root.after(3000, show_login_after_delay)
        else:
            # Si pas de protection par mot de passe, créer directement la vue et le contrôleur
            main_view = MainView(root, app_model, on_ready=on_main_view_ready)
            controller = AppController(app_model, main_view)
            
            # Démarrer les tâches en arrière-plan après l'affichage de l'interface
            root.after(100, start_background_tasks)
        
        # Configurer le gestionnaire de fermeture pour arrêter le moniteur d'activité
        def on_closing():
            """Gestionnaire d'événement pour la fermeture de l'application"""
            try:
                # Arrêter le moniteur d'activité
                if hasattr(main_view, 'shutdown'):
                    main_view.shutdown()
                
                # Fermer l'application
                root.destroy()
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture de l'application: {e}")
                root.destroy()
        
        # Configurer le protocole de fermeture
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Démarrage de l'application
        logger.info("Application démarrée")
        root.mainloop()
        
    except Exception as e:
        if 'logger' in locals():
            logger.error(f"Erreur fatale: {e}")
        else:
            print(f"Erreur fatale avant l'initialisation du logger: {e}")
        messagebox.showerror("Erreur critique", f"Une erreur critique est survenue: {e}\n"
                            "L'application va se fermer. Veuillez consulter les logs pour plus de détails.")
        sys.exit(1)

if __name__ == "__main__":
    main()