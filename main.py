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
from PIL import Image, ImageTk

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
        logging.getLogger("Vynal Docs Automator").warning(f"Erreur lors de la destruction d'un bouton: {e}")

# Appliquer le monkey patch
ctk.CTkButton.destroy = safe_destroy

# Constantes de l'application
APP_NAME = "Vynal Docs Automator"
WINDOW_SIZE = "1200x700"
MIN_WINDOW_SIZE = (800, 600)
REQUIRED_DIRECTORIES = ["data", "data/clients", "data/documents", "data/templates", "data/backup", "logs"]
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Importation des modules de l'application
from controllers.app_controller import AppController
from views.main_view import MainView
from models.app_model import AppModel
from utils.config_manager import ConfigManager

def setup_logging():
    """
    Configure la journalisation de l'application.
    
    Crée un répertoire de logs s'il n'existe pas, et configure les handlers
    pour écrire les logs dans un fichier et sur la console.
    
    Retourne :
        logger (logging.Logger) : Logger configuré pour l'application.
    
    Lève :
        OSError : Si la création du répertoire de logs échoue
    """
    try:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format=LOG_FORMAT,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        logger = logging.getLogger(APP_NAME)
        return logger
    except OSError as e:
        print(f"Erreur critique lors de la configuration des logs: {e}")
        sys.exit(1)

def ensure_directories():
    """
    Vérifie et crée les répertoires nécessaires au bon fonctionnement de l'application.
    
    Lève :
        OSError : Si la création d'un répertoire échoue
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    for dir_name in REQUIRED_DIRECTORIES:
        try:
            directory = os.path.join(base_dir, dir_name)
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Répertoire vérifié: {directory}")
        except OSError as e:
            logger.error(f"Impossible de créer le répertoire {directory}: {e}")
            raise

def main():
    """
    Fonction principale de l'application.
    
    Configure l'apparence de l'application, crée les objets principaux 
    (config, modèle, vue, contrôleur) et démarre l'interface graphique.
    """
    # Création des objets principaux
    config = ConfigManager()
    app_model = AppModel(config)
    
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
            # Pour éviter les erreurs CTkButton lors de la destruction
            # Détruire d'abord tous les widgets customtkinter connus pour causer des problèmes
            if hasattr(root, 'winfo_children'):
                for widget in root.winfo_children():
                    try:
                        if hasattr(widget, 'destroy'):
                            widget.destroy()
                    except:
                        pass
            
            # Puis détruire la fenêtre principale
            root.quit()
            root.destroy()
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture de la fenêtre: {e}")
            # Forcer la fermeture en cas d'erreur
            import sys
            sys.exit(0)
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Chargement de l'icône
    try:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")
        if os.path.exists(icon_path):
            icon = Image.open(icon_path)
            # Sur Windows, utiliser photoimage
            if sys.platform.startswith('win'):
                icon_tk = ImageTk.PhotoImage(icon)
                root.iconphoto(True, icon_tk)
            # Sur macOS et Linux
            else:
                root.iconphoto(True, ctk.CTkImage(icon))
    except Exception as e:
        logger.warning(f"Impossible de charger l'icône: {e}")
    
    # Vérifier si la protection par mot de passe est activée
    require_password = app_model.config.get("security.require_password", False)
    password_hash = app_model.config.get("security.password_hash", "")
    
    if require_password and password_hash:
        from views.login_view import LoginView
        
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
        
        # Afficher la fenêtre de connexion
        login_view = LoginView(root, on_login_success)
        login_view.show(password_hash)
    else:
        # Si pas de protection par mot de passe, créer directement la vue et le contrôleur
        main_view = MainView(root, app_model)
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