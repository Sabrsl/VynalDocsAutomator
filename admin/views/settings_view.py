#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue des paramètres avancés pour l'interface d'administration
"""

import logging
import customtkinter as ctk
import os
import json
import shutil
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog

logger = logging.getLogger("VynalDocsAutomator.Admin.SettingsView")

class AdminSettingsView:
    """
    Vue des paramètres avancés de l'application
    Permet de configurer l'application, les chemins, les options avancées, etc.
    """
    
    def __init__(self, parent, app_model):
        """
        Initialise la vue des paramètres avancés
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        self.config = {}
        self.original_config = {}
        self.has_unsaved_changes = False
        self.reset_dialog = None
        
        # Cadre principal de la vue
        self.frame = ctk.CTkFrame(parent)
        
        # Création de l'interface
        self.create_widgets()
        
        logger.info("AdminSettingsView initialisée")
    
    def get_nested_config(self, config_dict, key):
        """
        Récupère une valeur dans une configuration imbriquée
        
        Args:
            config_dict: Dictionnaire de configuration
            key: Clé avec notation pointée (ex: 'app.name')
            
        Returns:
            any: Valeur de configuration ou None si non trouvée
        """
        parts = key.split('.')
        current = config_dict
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def set_nested_config(self, config_dict, key, value):
        """
        Définit une valeur dans une configuration imbriquée
        
        Args:
            config_dict: Dictionnaire de configuration
            key: Clé avec notation pointée (ex: 'app.name')
            value: Valeur à définir
        """
        parts = key.split('.')
        current = config_dict
        
        # Créer les dictionnaires intermédiaires si nécessaire
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Définir la valeur finale
        current[parts[-1]] = value
    
    def confirm_reset_settings(self):
        """
        Demande confirmation avant de réinitialiser les paramètres
        """
        dialog = ctk.CTkToplevel(self.frame)
        self.reset_dialog = dialog
        dialog.title("Confirmer la réinitialisation")
        dialog.geometry("400x200")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Contenu de la boîte de dialogue
        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Message d'avertissement
        warning_label = ctk.CTkLabel(
            content_frame,
            text="⚠️ Attention",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#e74c3c"
        )
        warning_label.pack(pady=(0, 10))
        
        # Message détaillé
        message_label = ctk.CTkLabel(
            content_frame,
            text="Vous êtes sur le point de réinitialiser tous les paramètres à leurs valeurs par défaut.\n\nCette action est irréversible et l'application devra être redémarrée.",
            wraplength=360
        )
        message_label.pack(pady=10)
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, pady=10)
        
        # Bouton Annuler
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            command=dialog.destroy
        )
        cancel_btn.pack(side=ctk.LEFT, padx=5)
        
        # Bouton Confirmer
        confirm_btn = ctk.CTkButton(
            buttons_frame,
            text="Confirmer",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.reset_settings
        )
        confirm_btn.pack(side=ctk.RIGHT, padx=5)
    
    def reset_settings(self):
        """
        Réinitialise les paramètres aux valeurs par défaut
        """
        try:
            # Valeurs par défaut
            defaults = {
                "app.name": "Vynal Docs Automator",
                "app.company_name": "Vynal Agency LTD",
                "app.language": "fr",
                "app.theme": "dark",
                "app.font": "Roboto",
                "app.font_size": "12",
                "app.border_radius": "10",
                "storage.data_dir": os.path.join(os.path.expanduser("~"), ".vynal_docs_automator", "data"),
                "storage.logs_dir": os.path.join(os.path.expanduser("~"), ".vynal_docs_automator", "logs"),
                "storage.backup_dir": os.path.join(os.path.expanduser("~"), ".vynal_docs_automator", "backups"),
                "storage.backup_format": "zip",
                "storage.auto_backup_interval": "7",
                "storage.backup_count": "5",
                "notifications.enabled": "true",
                "notifications.email_enabled": "false",
                "notifications.error_notifications": "true",
                "notifications.update_notifications": "true",
                "security.require_login": "true",
                "security.session_timeout": "30",
                "security.require_strong_password": "true",
                "security.max_login_attempts": "5",
                "security.lockout_duration": "15",
                "admin.debug_mode": "false",
                "admin.log_level": "INFO",
                "admin.log_retention": "30",
                "admin.max_log_size": "10",
                "admin.remote_access": "false"
            }
            
            # Mettre à jour les widgets avec les valeurs par défaut
            for key, default_value in defaults.items():
                if key in self.config and isinstance(self.config[key], (ctk.StringVar, ctk.BooleanVar)):
                    if isinstance(self.config[key], ctk.BooleanVar):
                        self.config[key].set(default_value.lower() == "true")
                    else:
                        self.config[key].set(default_value)
            
            # Marquer comme modifié
            self.has_unsaved_changes = True
            self.save_btn.configure(state="normal")
            
            # Fermer la boîte de dialogue de confirmation si elle est ouverte
            if self.reset_dialog:
                self.reset_dialog.destroy()
                
            self.show_message(
                "Paramètres réinitialisés",
                "Les paramètres ont été réinitialisés aux valeurs par défaut. Cliquez sur Sauvegarder pour appliquer les changements.",
                "info"
            )
            
            logger.info("Paramètres réinitialisés aux valeurs par défaut")
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation des paramètres: {e}")
            self.show_message("Erreur", f"Impossible de réinitialiser les paramètres: {e}", "error")
    
    def create_widgets(self):
        """
        Crée les widgets de la vue des paramètres avancés
        """
        # Cadre pour le titre de la page
        self.header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.header_frame.pack(fill=ctk.X, pady=(0, 10))
        
        # Titre principal
        ctk.CTkLabel(
            self.header_frame,
            text="Paramètres avancés",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side=ctk.LEFT, anchor="w", padx=20, pady=10)
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        buttons_frame.pack(side=ctk.RIGHT, padx=20, pady=10)
        
        # Bouton Réinitialiser
        self.reset_btn = ctk.CTkButton(
            buttons_frame,
            text="Réinitialiser",
            width=100,
            command=self.confirm_reset_settings
        )
        self.reset_btn.pack(side=ctk.LEFT, padx=5)
        
        # Bouton Sauvegarder
        self.save_btn = ctk.CTkButton(
            buttons_frame,
            text="Sauvegarder",
            width=100,
            state="disabled",
            command=self.save_settings
        )
        self.save_btn.pack(side=ctk.LEFT, padx=5)
        
        # Conteneur principal avec défilement
        self.main_container = ctk.CTkScrollableFrame(self.frame)
        self.main_container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Créer les sections de paramètres
        self.create_general_settings()
        self.create_appearance_settings()
        self.create_storage_settings()
        self.create_notification_settings()
        self.create_security_settings()
        self.create_admin_settings()
        
        # Charger les paramètres actuels
        self.load_settings()

    def create_general_settings(self):
        """
        Crée la section des paramètres généraux
        """
        section = self.create_section("Paramètres généraux", "Configurez les paramètres de base de l'application")
        section.pack(fill=ctk.X, pady=10)
        
        # Nom de l'application
        self.create_setting(
            section,
            "app.name",
            "Nom de l'application",
            "Vynal Docs Automator",
            "Le nom affiché dans l'interface de l'application",
            widget_type="entry"
        )
        
        # Version
        self.create_setting(
            section,
            "app.version",
            "Version",
            "1.0.0",
            "Version actuelle de l'application",
            widget_type="entry",
            readonly=True
        )
        
        # Nom de l'entreprise
        self.create_setting(
            section,
            "app.company_name",
            "Nom de l'entreprise",
            "Vynal Agency LTD",
            "Nom de l'entreprise affiché dans les pieds de page et documents",
            widget_type="entry"
        )
        
        # Logo de l'entreprise
        self.create_setting(
            section,
            "app.company_logo",
            "Logo de l'entreprise",
            "",
            "Chemin vers le logo de l'entreprise",
            widget_type="file"
        )
        
        # Langue par défaut
        self.create_setting(
            section,
            "app.language",
            "Langue par défaut",
            "fr",
            "Langue utilisée dans l'interface",
            widget_type="dropdown",
            options=["fr", "en", "es", "de"]
        )
    
    def create_appearance_settings(self):
        """
        Crée la section des paramètres d'apparence
        """
        section = self.create_section("Apparence", "Personnalisez l'apparence de l'application")
        section.pack(fill=ctk.X, pady=10)
        
        # Thème
        self.create_setting(
            section,
            "app.theme",
            "Thème",
            "dark",
            "Thème clair ou sombre",
            widget_type="dropdown",
            options=["light", "dark"]
        )
        
        # Police
        self.create_setting(
            section,
            "app.font",
            "Police",
            "Roboto",
            "Police utilisée dans l'interface",
            widget_type="dropdown",
            options=["Default", "Roboto", "Arial", "Helvetica", "Times New Roman"]
        )
        
        # Taille de police
        self.create_setting(
            section,
            "app.font_size",
            "Taille de police",
            "12",
            "Taille de police (en points)",
            widget_type="spinbox",
            min_value=8,
            max_value=20
        )
        
        # Rayon des bordures
        self.create_setting(
            section,
            "app.border_radius",
            "Rayon des bordures",
            "10",
            "Rayon des coins arrondis (en pixels)",
            widget_type="spinbox",
            min_value=0,
            max_value=20
        )
    
    def create_storage_settings(self):
        """
        Crée la section des paramètres de stockage
        """
        section = self.create_section("Stockage", "Configurez le stockage des données")
        section.pack(fill=ctk.X, pady=10)
        
        # Répertoire de données
        self.create_setting(
            section,
            "storage.data_dir",
            "Répertoire de données",
            os.path.join(os.path.expanduser("~"), ".vynal_docs_automator", "data"),
            "Répertoire où sont stockées les données de l'application",
            widget_type="directory"
        )
        
        # Répertoire des logs
        self.create_setting(
            section,
            "storage.logs_dir",
            "Répertoire des logs",
            os.path.join(os.path.expanduser("~"), ".vynal_docs_automator", "logs"),
            "Répertoire où sont stockés les fichiers journaux",
            widget_type="directory"
        )
        
        # Répertoire des sauvegardes
        self.create_setting(
            section,
            "storage.backup_dir",
            "Répertoire des sauvegardes",
            os.path.join(os.path.expanduser("~"), ".vynal_docs_automator", "backups"),
            "Répertoire où sont stockées les sauvegardes",
            widget_type="directory"
        )
        
        # Format de sauvegarde
        self.create_setting(
            section,
            "storage.backup_format",
            "Format de sauvegarde",
            "zip",
            "Format utilisé pour les sauvegardes",
            widget_type="dropdown",
            options=["zip", "tar", "tar.gz"]
        )
        
        # Intervalle de sauvegarde automatique
        self.create_setting(
            section,
            "storage.auto_backup_interval",
            "Intervalle de sauvegarde automatique",
            "7",
            "Nombre de jours entre les sauvegardes automatiques (0 pour désactiver)",
            widget_type="spinbox",
            min_value=0,
            max_value=30
        )
        
        # Nombre de sauvegardes à conserver
        self.create_setting(
            section,
            "storage.backup_count",
            "Nombre de sauvegardes à conserver",
            "5",
            "Nombre maximum de sauvegardes à conserver (les plus anciennes sont supprimées)",
            widget_type="spinbox",
            min_value=1,
            max_value=50
        )
    
    def create_notification_settings(self):
        """
        Crée la section des paramètres de notification
        """
        section = self.create_section("Notifications", "Configurez les notifications et alertes")
        section.pack(fill=ctk.X, pady=10)
        
        # Activer les notifications
        self.create_setting(
            section,
            "notifications.enabled",
            "Activer les notifications",
            "true",
            "Activer ou désactiver toutes les notifications",
            widget_type="switch"
        )
        
        # Notifications par email
        self.create_setting(
            section,
            "notifications.email_enabled",
            "Notifications par email",
            "false",
            "Envoyer les notifications importantes par email",
            widget_type="switch"
        )
        
        # Email de l'administrateur
        self.create_setting(
            section,
            "notifications.admin_email",
            "Email de l'administrateur",
            "",
            "Adresse email pour recevoir les notifications d'administration",
            widget_type="entry"
        )
        
        # Notifications d'erreurs
        self.create_setting(
            section,
            "notifications.error_notifications",
            "Notifications d'erreurs",
            "true",
            "Notifier les erreurs critiques",
            widget_type="switch"
        )
        
        # Notifications de mises à jour
        self.create_setting(
            section,
            "notifications.update_notifications",
            "Notifications de mises à jour",
            "true",
            "Notifier les nouvelles mises à jour disponibles",
            widget_type="switch"
        )
    
    def create_security_settings(self):
        """
        Crée la section des paramètres de sécurité
        """
        section = self.create_section("Sécurité", "Configurez les paramètres de sécurité")
        section.pack(fill=ctk.X, pady=10)
        
        # Exiger une authentification au démarrage
        self.create_setting(
            section,
            "security.require_login",
            "Exiger une authentification",
            "true",
            "Exiger une authentification au démarrage de l'application",
            widget_type="switch"
        )
        
        # Délai d'expiration de session
        self.create_setting(
            section,
            "security.session_timeout",
            "Délai d'expiration de session",
            "30",
            "Délai d'inactivité avant déconnexion automatique (minutes, 0 pour désactiver)",
            widget_type="spinbox",
            min_value=0,
            max_value=240
        )
        
        # Exiger un mot de passe fort
        self.create_setting(
            section,
            "security.require_strong_password",
            "Exiger un mot de passe fort",
            "true",
            "Exiger un mot de passe avec des lettres, chiffres et caractères spéciaux",
            widget_type="switch"
        )
        
        # Nombre maximal de tentatives de connexion
        self.create_setting(
            section,
            "security.max_login_attempts",
            "Tentatives de connexion maximum",
            "5",
            "Nombre maximal de tentatives de connexion avant blocage temporaire",
            widget_type="spinbox",
            min_value=1,
            max_value=10
        )
        
        # Durée de blocage après tentatives échouées
        self.create_setting(
            section,
            "security.lockout_duration",
            "Durée de blocage (minutes)",
            "15",
            "Durée de blocage après trop de tentatives échouées (minutes)",
            widget_type="spinbox",
            min_value=5,
            max_value=60
        )
    
    def create_admin_settings(self):
        """
        Crée la section des paramètres d'administration
        """
        section = self.create_section("Administration", "Paramètres réservés aux administrateurs")
        section.pack(fill=ctk.X, pady=10)
        
        # Mode debug
        self.create_setting(
            section,
            "admin.debug_mode",
            "Mode debug",
            "false",
            "Activer le mode debug pour des journaux plus détaillés",
            widget_type="switch"
        )
        
        # Niveau de journalisation
        self.create_setting(
            section,
            "admin.log_level",
            "Niveau de journalisation",
            "INFO",
            "Niveau de détail des journaux",
            widget_type="dropdown",
            options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
        
        # Conservation des journaux
        self.create_setting(
            section,
            "admin.log_retention",
            "Conservation des journaux (jours)",
            "30",
            "Nombre de jours de conservation des fichiers journaux",
            widget_type="spinbox",
            min_value=1,
            max_value=365
        )
        
        # Taille maximale des journaux
        self.create_setting(
            section,
            "admin.max_log_size",
            "Taille maximale des journaux (Mo)",
            "10",
            "Taille maximale d'un fichier journal en Mo",
            widget_type="spinbox",
            min_value=1,
            max_value=100
        )
        
        # Accès distant
        self.create_setting(
            section,
            "admin.remote_access",
            "Accès distant",
            "false",
            "Autoriser l'accès à l'application depuis d'autres machines (nécessite un redémarrage)",
            widget_type="switch"
        )
    
    def create_section(self, title, description=""):
        """
        Crée une section de paramètres
        
        Args:
            title: Titre de la section
            description: Description de la section
            
        Returns:
            ctk.CTkFrame: Cadre contenant la section
        """
        section = ctk.CTkFrame(self.main_container)
        
        # En-tête de la section
        header = ctk.CTkFrame(section, fg_color="transparent")
        header.pack(fill=ctk.X, padx=15, pady=10)
        
        # Titre
        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w")
        
        # Description
        if description:
            ctk.CTkLabel(
                header,
                text=description,
                font=ctk.CTkFont(size=12),
                text_color="gray"
            ).pack(anchor="w")
        
        # Conteneur pour les paramètres
        settings_container = ctk.CTkFrame(section, fg_color="transparent")
        settings_container.pack(fill=ctk.BOTH, expand=True, padx=15, pady=10)
        
        return section
    
    def create_setting(self, parent, key, label, default_value, help_text="", 
                     widget_type="entry", readonly=False, options=None, 
                     min_value=None, max_value=None):
        """
        Crée un paramètre avec son étiquette et son widget d'entrée
        
        Args:
            parent: Widget parent
            key: Clé du paramètre dans la configuration
            label: Étiquette affichée
            default_value: Valeur par défaut
            help_text: Texte d'aide (info-bulle)
            widget_type: Type de widget ('entry', 'spinbox', 'dropdown', 'switch', 'directory', 'file')
            readonly: Indique si le paramètre est en lecture seule
            options: Options pour les dropdown
            min_value: Valeur minimale pour spinbox
            max_value: Valeur maximale pour spinbox
        """
        # Stocker la valeur par défaut
        if key not in self.config:
            self.config[key] = default_value
        
        # Cadre pour le paramètre
        setting_frame = ctk.CTkFrame(parent, fg_color="transparent")
        setting_frame.pack(fill=ctk.X, pady=5)
        
        # Étiquette
        label_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        label_frame.pack(side=ctk.LEFT, fill=ctk.Y)
        
        label_widget = ctk.CTkLabel(
            label_frame,
            text=label,
            anchor="w",
            width=200,
            justify="left"
        )
        label_widget.pack(side=ctk.LEFT, padx=(0, 10))
        
        # Fonction pour détecter les changements
        def on_value_change(*args):
            self.has_unsaved_changes = True
            self.save_btn.configure(state="normal")
        
        # Widget de contrôle selon le type
        if widget_type == "entry":
            var = ctk.StringVar(value=self.config.get(key, default_value))
            var.trace_add("write", on_value_change)
            
            entry = ctk.CTkEntry(
                setting_frame,
                textvariable=var,
                width=300,
                state="readonly" if readonly else "normal"
            )
            entry.pack(side=ctk.LEFT, padx=5)
            
            # Stocker la variable et le widget
            self.config[key] = var
        
        elif widget_type == "spinbox":
            var = ctk.StringVar(value=self.config.get(key, default_value))
            var.trace_add("write", on_value_change)
            
            spinbox = ctk.CTkEntry(setting_frame, textvariable=var, width=100)
            spinbox.pack(side=ctk.LEFT, padx=5)
            
            # Cadre pour les boutons +/-
            buttons_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
            buttons_frame.pack(side=ctk.LEFT)
            
            # Fonction pour incrémenter/décrémenter
            def increment():
                try:
                    current = int(var.get())
                    if max_value is None or current < max_value:
                        var.set(str(current + 1))
                except ValueError:
                    var.set(str(min_value or 0))
            
            def decrement():
                try:
                    current = int(var.get())
                    if min_value is None or current > min_value:
                        var.set(str(current - 1))
                except ValueError:
                    var.set(str(min_value or 0))
            
            # Boutons +/-
            minus_btn = ctk.CTkButton(
                buttons_frame,
                text="-",
                width=30,
                height=30,
                command=decrement
            )
            minus_btn.pack(side=ctk.LEFT, padx=2)
            
            plus_btn = ctk.CTkButton(
                buttons_frame,
                text="+",
                width=30,
                height=30,
                command=increment
            )
            plus_btn.pack(side=ctk.LEFT, padx=2)
            
            # Stocker la variable et le widget
            self.config[key] = var
        
        elif widget_type == "dropdown":
            var = ctk.StringVar(value=self.config.get(key, default_value))
            var.trace_add("write", on_value_change)
            
            dropdown = ctk.CTkOptionMenu(
                setting_frame,
                values=options or [],
                variable=var,
                width=150,
                state="disabled" if readonly else "normal"
            )
            dropdown.pack(side=ctk.LEFT, padx=5)
            
            # Stocker la variable et le widget
            self.config[key] = var
        
        elif widget_type == "switch":
            # Convertir la valeur en booléen
            default_bool = default_value.lower() == "true" if isinstance(default_value, str) else bool(default_value)
            current_value = self.config.get(key, default_bool)
            if isinstance(current_value, str):
                current_value = current_value.lower() == "true"
            
            var = ctk.BooleanVar(value=current_value)
            var.trace_add("write", on_value_change)
            
            switch = ctk.CTkSwitch(
                setting_frame,
                text="",
                variable=var,
                onvalue=True,
                offvalue=False,
                state="disabled" if readonly else "normal"
            )
            switch.pack(side=ctk.LEFT, padx=5)
            
            # Stocker la variable et le widget
            self.config[key] = var
        
        elif widget_type in ["directory", "file"]:
            var = ctk.StringVar(value=self.config.get(key, default_value))
            var.trace_add("write", on_value_change)
            
            # Cadre pour le champ et le bouton
            input_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
            input_frame.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
            
            # Champ de texte
            entry = ctk.CTkEntry(
                input_frame,
                textvariable=var,
                width=300,
                state="readonly" if readonly else "normal"
            )
            entry.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)
            
            # Fonction pour ouvrir le sélecteur
            def browse():
                if widget_type == "directory":
                    path = filedialog.askdirectory(
                        initialdir=var.get() or os.path.expanduser("~"),
                        title=f"Sélectionner {label}"
                    )
                else:  # file
                    path = filedialog.askopenfilename(
                        initialdir=os.path.dirname(var.get()) or os.path.expanduser("~"),
                        title=f"Sélectionner {label}",
                        filetypes=[("All files", "*.*"), ("Images", "*.png *.jpg *.jpeg *.gif")]
                    )
                
                if path:  # Si un chemin a été sélectionné
                    var.set(path)
            
            # Bouton pour parcourir
            browse_btn = ctk.CTkButton(
                input_frame,
                text="Parcourir",
                width=100,
                command=browse,
                state="disabled" if readonly else "normal"
            )
            browse_btn.pack(side=ctk.LEFT, padx=5)
            
            # Stocker la variable et le widget
            self.config[key] = var
        
        # Bouton d'aide si un texte d'aide est fourni
        if help_text:
            help_btn = ctk.CTkButton(
                setting_frame,
                text="?",
                width=30,
                height=30,
                corner_radius=15,
                fg_color="gray",
                hover_color="darkgray",
                command=lambda ht=help_text: self.show_help(label, ht)
            )
            help_btn.pack(side=ctk.RIGHT, padx=5)
    
    def show_help(self, title, help_text):
        """
        Affiche une boîte de dialogue d'aide
        
        Args:
            title: Titre du paramètre
            help_text: Texte d'aide à afficher
        """
        dialog = ctk.CTkToplevel(self.frame)
        dialog.title(f"Aide: {title}")
        dialog.geometry("400x180")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Contenu de l'aide
        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Icône d'information
        icon_label = ctk.CTkLabel(content_frame, text="ℹ️", font=ctk.CTkFont(size=24))
        icon_label.pack(pady=(0, 10))
        
        # Titre
        title_label = ctk.CTkLabel(
            content_frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Texte d'aide
        help_label = ctk.CTkLabel(
            content_frame,
            text=help_text,
            wraplength=360,
            justify="left"
        )
        help_label.pack(pady=10)
        
        # Bouton Fermer
        close_btn = ctk.CTkButton(
            content_frame,
            text="Fermer",
            width=100,
            command=dialog.destroy
        )
        close_btn.pack(pady=10)
    
    def load_settings(self):
        """
        Charge les paramètres depuis le fichier de configuration
        """
        try:
            # Récupérer les paramètres du modèle
            if hasattr(self.model, 'config'):
                config_dict = self.model.config.get_all()
            else:
                # Si le modèle n'a pas de config, charger depuis un fichier
                config_file = os.path.join(self.get_config_dir(), "config.json")
                
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_dict = json.load(f)
                else:
                    # Si le fichier n'existe pas, utiliser les valeurs par défaut
                    config_dict = {}
            
            # Mettre à jour les valeurs des widgets
            for key, var in self.config.items():
                if isinstance(var, (ctk.StringVar, ctk.BooleanVar)):
                    # Récupérer la valeur depuis la configuration
                    value = self.get_nested_config(config_dict, key)
                    
                    if value is not None:
                        # Convertir en booléen si nécessaire
                        if isinstance(var, ctk.BooleanVar):
                            if isinstance(value, str):
                                value = value.lower() == "true"
                            var.set(bool(value))
                        else:
                            var.set(str(value))
            
            # Stocker la configuration originale
            self.original_config = self.get_current_config()
            
            # Réinitialiser l'état de modification
            self.has_unsaved_changes = False
            self.save_btn.configure(state="disabled")
            
            logger.info("Paramètres chargés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des paramètres: {e}")
            self.show_message("Erreur", f"Impossible de charger les paramètres: {e}", "error")
    
    def get_current_config(self):
        """
        Récupère la configuration actuelle à partir des valeurs des widgets
        
        Returns:
            dict: Configuration actuelle
        """
        config_dict = {}
        
        for key, var in self.config.items():
            if isinstance(var, (ctk.StringVar, ctk.BooleanVar)):
                # Récupérer la valeur du widget
                value = var.get()
                
                # Stocker dans la structure hiérarchique
                self.set_nested_config(config_dict, key, value)
        
        return config_dict
    
    def save_settings(self):
        """
        Sauvegarde les paramètres dans le fichier de configuration
        """
        try:
            # Récupérer la configuration actuelle
            config_dict = self.get_current_config()
            
            # Sauvegarder dans le modèle si possible
            if hasattr(self.model, 'config') and hasattr(self.model.config, 'update'):
                for key, value in config_dict.items():
                    self.model.config.update(key, value)
                
                # Appliquer les changements si nécessaire
                if hasattr(self.model, 'apply_config'):
                    self.model.apply_config()
            else:
                # Sinon, sauvegarder dans un fichier
                config_file = os.path.join(self.get_config_dir(), "config.json")
                
                # Créer le répertoire si nécessaire
                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                
                # Écrire la configuration
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=4, ensure_ascii=False)
            
            # Mettre à jour la configuration originale
            self.original_config = config_dict
            
            # Réinitialiser l'état de modification
            self.has_unsaved_changes = False
            self.save_btn.configure(state="disabled")
            
            # Afficher un message de succès
            self.show_message(
                "Paramètres sauvegardés",
                "Les paramètres ont été sauvegardés avec succès. Certains changements\n"
                "nécessitent un redémarrage de l'application pour prendre effet.",
                "success"
            )
            
            logger.info("Paramètres sauvegardés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des paramètres: {e}")
            self.show_message("Erreur", f"Impossible de sauvegarder les paramètres: {e}", "error")
    
    def get_config_dir(self):
        """
        Récupère le répertoire de configuration
        
        Returns:
            str: Chemin vers le répertoire de configuration
        """
        # Utiliser le répertoire de données de l'application si disponible
        if hasattr(self.model, 'data_dir'):
            return os.path.join(self.model.data_dir, "admin")
        
        # Sinon, utiliser un répertoire par défaut
        return os.path.join(os.path.expanduser("~"), ".vynal_docs_automator", "admin")

    def show_message(self, title, message, message_type="info"):
        """
        Affiche un message dans une boîte de dialogue
        
        Args:
            title: Titre du message
            message: Contenu du message
            message_type: Type de message ('info', 'success', 'warning', 'error')
        """
        # Déterminer l'icône en fonction du type de message
        if message_type == "error":
            icon = "❌"
            color = "#e74c3c"
        elif message_type == "warning":
            icon = "⚠️"
            color = "#f39c12"
        elif message_type == "success":
            icon = "✅"
            color = "#2ecc71"
        else:
            icon = "ℹ️"
            color = "#3498db"
        
        # Créer la boîte de dialogue
        dialog = ctk.CTkToplevel(self.frame)
        dialog.title(title)
        dialog.geometry("400x180")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Contenu du message
        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Icône et titre
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill=ctk.X, pady=(0, 10))
        
        icon_label = ctk.CTkLabel(header_frame, text=icon, font=ctk.CTkFont(size=24))
        icon_label.pack(side=ctk.LEFT, padx=(0, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=color
        )
        title_label.pack(side=ctk.LEFT)
        
        # Message
        message_label = ctk.CTkLabel(
            content_frame,
            text=message,
            wraplength=360,
            justify="left"
        )
        message_label.pack(fill=ctk.X, pady=10)
        
        # Bouton OK
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, pady=10)
        
        ok_button = ctk.CTkButton(
            button_frame,
            text="OK",
            width=100,
            command=dialog.destroy
        )
        ok_button.pack(side=ctk.RIGHT)
        
    def show(self):
        """
        Affiche la vue des paramètres
        """
        self.frame.pack(fill=ctk.BOTH, expand=True)
        
    def hide(self):
        """
        Cache la vue des paramètres
        """
        self.frame.pack_forget()