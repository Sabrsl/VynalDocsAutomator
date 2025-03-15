#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import customtkinter as ctk
from datetime import datetime
from admin import start_admin

# Configurer le logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configurer customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ConfigObject:
    """Objet de configuration compatible avec les attentes du code admin"""
    def __init__(self, config_dict):
        self._config = config_dict
        
    def get(self, key, default=None):
        """Récupère une valeur de configuration"""
        parts = key.split('.')
        current = self._config
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current
    
    def update(self, key, value):
        """Met à jour une valeur de configuration"""
        parts = key.split('.')
        current = self._config
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
        return True
    
    def get_all(self):
        """Renvoie toute la configuration"""
        return self._config

class AppModel:
    """
    Modèle simple pour simuler l'application principale
    """
    def __init__(self):
        self.version = "1.0.0"
        self.data_dir = os.path.join(os.path.expanduser("~"), ".vynal_docs_automator")
        self.logs_dir = os.path.join(self.data_dir, "logs")
        self.backup_dir = os.path.join(self.data_dir, "backups")
        self.start_time = datetime.now()
        
        # S'assurer que les répertoires existent
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Configuration de base
        config_dict = {
            'app': {
                'version': self.version,
                'name': 'Vynal Docs Automator',
                'company_name': 'Vynal Agency LTD',
                'language': 'fr',
                'theme': 'dark'
            }
        }
        
        self.config = ConfigObject(config_dict)
        
        # Initialiser des utilisateurs de test
        self.users = [
            {
                "id": "usr_001",
                "email": "admin@example.com",
                "username": "Admin",
                "role": "admin",
                "is_active": True
            }
        ]
        
        # Initialiser d'autres données nécessaires
        self.documents = []
        self.templates = []
        self.system_alerts = []
        self.admin_activities = []
        
        # Définir l'utilisateur actuel comme admin
        self.current_user = self.users[0]

try:
    # Créer la fenêtre principale
    root = ctk.CTk()
    root.title("Vynal Docs Admin - Interface Améliorée")
    root.geometry("1200x800")
    
    # Centrer la fenêtre
    position_x = int((root.winfo_screenwidth() / 2) - (1200 / 2))
    position_y = int((root.winfo_screenheight() / 2) - (800 / 2))
    root.geometry(f"+{position_x}+{position_y}")

    # Créer une instance du modèle d'application
    app_model = AppModel()
    print("Modèle d'application créé avec succès")

    # Démarrer l'interface d'administration avec app_model
    print("Démarrage de l'interface d'administration...")
    admin = start_admin(root, app_model)
    print("Interface d'administration démarrée")

    # Lancer la boucle principale
    root.mainloop()
except Exception as e:
    print(f"Erreur lors du démarrage: {e}")
    import traceback
    traceback.print_exc()