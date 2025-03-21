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
        
        def on_closing():
            """Gestionnaire d'événement pour la fermeture de l'application"""
            logger.info("Fermeture de l'application initiée par l'utilisateur")
            try:
                app_model.cleanup()
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage de l'application: {e}")
            
            # Fermeture sécurisée de la fenêtre
            try:
                if hasattr(root, 'winfo_children'):
                    for widget in root.winfo_children():
                        try:
                            if hasattr(widget, 'destroy'):
                                widget.destroy()
                        except:
                            pass
                
                root.quit()
                root.destroy()
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture de la fenêtre: {e}")
                sys.exit(0)
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Chargement de l'icône
        try:
            icon_path = os.path.join("assets", "icon.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except Exception as e:
            logger.warning(f"Impossible de charger l'icône: {e}")
        
        # Vérifier si la protection par mot de passe est activée
        require_password = app_model.config.get("security.require_password", False)
        password_hash = app_model.config.get("security.password_hash", "")
        
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
        
        if require_password and password_hash:
            # Cacher la fenêtre principale pendant la connexion
            root.withdraw()
            
            def on_login_success():
                """Callback appelé après une connexion réussie"""
                root.deiconify()  # Afficher la fenêtre principale
                # Création de la vue principale après la connexion réussie
                main_view = MainView(root, app_model)
                # Création du contrôleur
                controller = AppController(app_model, main_view)
                logger.info("Connexion réussie, affichage de l'application")
                
                # Démarrer les tâches en arrière-plan après l'affichage de l'interface
                root.after(100, start_background_tasks)
            
            # Afficher la fenêtre de connexion
            login_view = LoginView(root, on_login_success)
            login_view.show(password_hash)
        else:
            # Si pas de protection par mot de passe, créer directement la vue et le contrôleur
            main_view = MainView(root, app_model)
            controller = AppController(app_model, main_view)
            
            # Démarrer les tâches en arrière-plan après l'affichage de l'interface
            root.after(100, start_background_tasks)
        
        # Démarrage de l'application
        logger.info("Application démarrée")
        root.mainloop()
        
    except Exception as e:
        if 'logger' in locals():
            logger.error(f"Erreur fatale: {e}")
        else:
            print(f"Erreur fatale avant l'initialisation du logger: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()