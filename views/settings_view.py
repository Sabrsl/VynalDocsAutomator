#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue des paramètres pour l'application Vynal Docs Automator
"""

import os
import logging
import customtkinter as ctk
from tkinter import filedialog

logger = logging.getLogger("VynalDocsAutomator.SettingsView")

class SettingsView:
    """
    Vue des paramètres
    Permet de configurer l'application
    """
    
    def __init__(self, parent, app_model):
        """
        Initialise la vue des paramètres
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        
        # Cadre principal de la vue
        self.frame = ctk.CTkFrame(parent)
        
        # Créer les composants de l'interface
        self.create_widgets()
        
        logger.info("SettingsView initialisée")
    
    def create_widgets(self):
        """
        Crée les widgets de la vue
        """
        # Zone de défilement
        self.scrollable_frame = ctk.CTkScrollableFrame(self.frame)
        self.scrollable_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Section: Paramètres généraux
        self.create_section("Paramètres généraux")
        
        # Nom de l'entreprise
        self.company_name_var = ctk.StringVar(value=self.model.config.get("app.company_name", ""))
        self.create_setting(
            "Nom de l'entreprise",
            "Nom qui apparaîtra sur les documents",
            "entry",
            self.company_name_var
        )
        
        # Logo de l'entreprise
        self.company_logo_var = ctk.StringVar(value=self.model.config.get("app.company_logo", ""))
        self.create_setting(
            "Logo de l'entreprise",
            "Image qui apparaîtra sur les documents",
            "file",
            self.company_logo_var,
            [("Images", "*.png;*.jpg;*.jpeg")]
        )
        
        # Thème
        self.theme_var = ctk.StringVar(value=self.model.config.get("app.theme", "system"))
        self.create_setting(
            "Thème",
            "Apparence de l'application",
            "combobox",
            self.theme_var,
            ["system", "light", "dark"]
        )
        
        # Sauvegarde automatique
        self.auto_save_var = ctk.BooleanVar(value=self.model.config.get("app.auto_save", True))
        self.create_setting(
            "Sauvegarde automatique",
            "Enregistrer automatiquement les modifications",
            "switch",
            self.auto_save_var
        )
        
        # Intervalle de sauvegarde
        self.save_interval_var = ctk.IntVar(value=self.model.config.get("app.save_interval", 5))
        self.create_setting(
            "Intervalle de sauvegarde",
            "Minutes entre chaque sauvegarde automatique",
            "slider",
            self.save_interval_var,
            (1, 30)
        )
        
        # Section: Dossiers par défaut
        self.create_section("Dossiers par défaut")
        
        # Dossier des documents
        self.documents_dir_var = ctk.StringVar(value=self.model.config.get("paths.documents", ""))
        self.create_setting(
            "Dossier des documents",
            "Emplacement des documents générés",
            "directory",
            self.documents_dir_var
        )
        
        # Dossier des modèles
        self.templates_dir_var = ctk.StringVar(value=self.model.config.get("paths.templates", ""))
        self.create_setting(
            "Dossier des modèles",
            "Emplacement des modèles de documents",
            "directory",
            self.templates_dir_var
        )
        
        # Section: Sécurité
        self.create_section("Sécurité")
        
        # Protection par mot de passe
        self.require_password_var = ctk.BooleanVar(value=self.model.config.get("security.require_password", False))
        self.create_setting(
            "Protection par mot de passe",
            "Demander un mot de passe au démarrage",
            "switch",
            self.require_password_var
        )
        
        # Verrouillage automatique
        self.auto_lock_var = ctk.BooleanVar(value=self.model.config.get("security.auto_lock", False))
        self.create_setting(
            "Verrouillage automatique",
            "Verrouiller après une période d'inactivité",
            "switch",
            self.auto_lock_var
        )
        
        # Délai de verrouillage
        self.lock_time_var = ctk.IntVar(value=self.model.config.get("security.lock_time", 10))
        self.create_setting(
            "Délai de verrouillage",
            "Minutes d'inactivité avant verrouillage",
            "slider",
            self.lock_time_var,
            (1, 60)
        )
        
        # Section: Format des documents
        self.create_section("Format des documents")
        
        # Format par défaut
        self.default_format_var = ctk.StringVar(value=self.model.config.get("document.default_format", "pdf"))
        self.create_setting(
            "Format par défaut",
            "Format utilisé lors de la génération de documents",
            "combobox",
            self.default_format_var,
            ["pdf", "docx"]
        )
        
        # Modèle de nom de fichier
        self.filename_pattern_var = ctk.StringVar(value=self.model.config.get("document.filename_pattern", ""))
        self.create_setting(
            "Modèle de nom de fichier",
            "Pattern pour nommer les fichiers (ex: {type}_{client}_{date})",
            "entry",
            self.filename_pattern_var
        )
        
        # Format de date
        self.date_format_var = ctk.StringVar(value=self.model.config.get("document.date_format", "%Y-%m-%d"))
        self.create_setting(
            "Format de date",
            "Format des dates dans les noms de fichiers",
            "entry",
            self.date_format_var
        )
        
        # Section: Sauvegarde et restauration
        self.create_section("Sauvegarde et restauration")
        
        # Boutons de sauvegarde et restauration
        backup_restore_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        backup_restore_frame.pack(fill=ctk.X, pady=10)
        
        # Bouton Créer une sauvegarde
        ctk.CTkButton(
            backup_restore_frame,
            text="Créer une sauvegarde",
            command=self.create_backup
        ).pack(side=ctk.LEFT, padx=10)
        
        # Bouton Restaurer une sauvegarde
        ctk.CTkButton(
            backup_restore_frame,
            text="Restaurer une sauvegarde",
            command=self.restore_backup
        ).pack(side=ctk.LEFT, padx=10)
        
        # Bouton Réinitialiser les paramètres
        ctk.CTkButton(
            backup_restore_frame,
            text="Réinitialiser",
            fg_color="red",
            command=self.reset_settings
        ).pack(side=ctk.RIGHT, padx=10)
        
        # Bouton Enregistrer
        save_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        save_frame.pack(fill=ctk.X, pady=20)
        
        ctk.CTkButton(
            save_frame,
            text="Enregistrer les paramètres",
            width=200,
            height=40,
            command=self.save_settings
        ).pack(side=ctk.RIGHT, padx=10)
    
    def create_section(self, title):
        """
        Crée une section dans les paramètres
        
        Args:
            title: Titre de la section
        """
        section_frame = ctk.CTkFrame(self.scrollable_frame)
        section_frame.pack(fill=ctk.X, pady=10)
        
        # Titre de la section
        ctk.CTkLabel(
            section_frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Séparateur
        ctk.CTkFrame(section_frame, height=1, fg_color="gray").pack(fill=ctk.X, padx=10, pady=5)
    
    def create_setting(self, label, description, widget_type, variable, options=None):
        """
        Crée un paramètre dans l'interface
        
        Args:
            label: Étiquette du paramètre
            description: Description du paramètre
            widget_type: Type de widget ('entry', 'combobox', 'switch', 'slider', 'file', 'directory')
            variable: Variable liée au widget
            options: Options supplémentaires (valeurs pour combobox, limites pour slider, etc.)
        """
        # Cadre pour le paramètre
        setting_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        setting_frame.pack(fill=ctk.X, pady=5)
        
        # Zone d'étiquette
        label_frame = ctk.CTkFrame(setting_frame, fg_color="transparent", width=200)
        label_frame.pack(side=ctk.LEFT, padx=10, fill=ctk.Y)
        label_frame.pack_propagate(False)
        
        # Étiquette
        ctk.CTkLabel(
            label_frame,
            text=label,
            anchor="w",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(5, 0))
        
        # Description
        if description:
            ctk.CTkLabel(
                label_frame,
                text=description,
                anchor="w",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            ).pack(anchor="w", pady=(0, 5))
        
        # Zone de widget
        widget_frame = ctk.CTkFrame(setting_frame, fg_color="transparent")
        widget_frame.pack(side=ctk.RIGHT, padx=10, fill=ctk.BOTH, expand=True)
        
        # Créer le widget en fonction du type
        if widget_type == "entry":
            ctk.CTkEntry(
                widget_frame,
                textvariable=variable,
                width=250
            ).pack(side=ctk.RIGHT, pady=5)
        
        elif widget_type == "combobox":
            ctk.CTkComboBox(
                widget_frame,
                values=options,
                variable=variable,
                width=250
            ).pack(side=ctk.RIGHT, pady=5)
        
        elif widget_type == "switch":
            ctk.CTkSwitch(
                widget_frame,
                text="",
                variable=variable
            ).pack(side=ctk.RIGHT, pady=5)
        
        elif widget_type == "slider":
            min_val, max_val = options
            slider_frame = ctk.CTkFrame(widget_frame, fg_color="transparent")
            slider_frame.pack(side=ctk.RIGHT, fill=ctk.X, expand=True, pady=5)
            
            slider = ctk.CTkSlider(
                slider_frame,
                from_=min_val,
                to=max_val,
                variable=variable
            )
            slider.pack(side=ctk.LEFT, fill=ctk.X, expand=True, pady=5)
            
            value_label = ctk.CTkLabel(
                slider_frame,
                text=str(variable.get()),
                width=30
            )
            value_label.pack(side=ctk.RIGHT, padx=10)
            
            # Mettre à jour l'étiquette de valeur
            def update_value_label(*args):
                value_label.configure(text=str(variable.get()))
            
            variable.trace_add("write", update_value_label)
        
        elif widget_type == "file" or widget_type == "directory":
            file_frame = ctk.CTkFrame(widget_frame, fg_color="transparent")
            file_frame.pack(side=ctk.RIGHT, fill=ctk.X, expand=True, pady=5)
            
            entry = ctk.CTkEntry(
                file_frame,
                textvariable=variable,
                width=200
            )
            entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
            
            def browse_callback():
                if widget_type == "file":
                    path = filedialog.askopenfilename(filetypes=options) if options else filedialog.askopenfilename()
                else:  # directory
                    path = filedialog.askdirectory()
                
                if path:
                    variable.set(path)
            
            ctk.CTkButton(
                file_frame,
                text="Parcourir",
                width=80,
                command=browse_callback
            ).pack(side=ctk.RIGHT, padx=5)
    
    def show(self):
        """
        Affiche la vue
        """
        self.frame.pack(fill=ctk.BOTH, expand=True)
        self.update_view()
    
    def hide(self):
        """
        Masque la vue
        """
        self.frame.pack_forget()
    
    def update_view(self):
        """
        Met à jour la vue avec les données actuelles
        """
        # Mettre à jour les variables
        self.company_name_var.set(self.model.config.get("app.company_name", ""))
        self.company_logo_var.set(self.model.config.get("app.company_logo", ""))
        self.theme_var.set(self.model.config.get("app.theme", "system"))
        self.auto_save_var.set(self.model.config.get("app.auto_save", True))
        self.save_interval_var.set(self.model.config.get("app.save_interval", 5))
        self.documents_dir_var.set(self.model.config.get("paths.documents", ""))
        self.templates_dir_var.set(self.model.config.get("paths.templates", ""))
        self.require_password_var.set(self.model.config.get("security.require_password", False))
        self.auto_lock_var.set(self.model.config.get("security.auto_lock", False))
        self.lock_time_var.set(self.model.config.get("security.lock_time", 10))
        self.default_format_var.set(self.model.config.get("document.default_format", "pdf"))
        self.filename_pattern_var.set(self.model.config.get("document.filename_pattern", ""))
        self.date_format_var.set(self.model.config.get("document.date_format", "%Y-%m-%d"))
        
        logger.info("SettingsView mise à jour")
    
    def save_settings(self):
        """
        Enregistre les paramètres
        """
        # Récupérer les valeurs des widgets
        settings = {
            "app.company_name": self.company_name_var.get(),
            "app.company_logo": self.company_logo_var.get(),
            "app.theme": self.theme_var.get(),
            "app.auto_save": self.auto_save_var.get(),
            "app.save_interval": self.save_interval_var.get(),
            "paths.documents": self.documents_dir_var.get(),
            "paths.templates": self.templates_dir_var.get(),
            "security.require_password": self.require_password_var.get(),
            "security.auto_lock": self.auto_lock_var.get(),
            "security.lock_time": self.lock_time_var.get(),
            "document.default_format": self.default_format_var.get(),
            "document.filename_pattern": self.filename_pattern_var.get(),
            "document.date_format": self.date_format_var.get()
        }
        
        # Enregistrer les paramètres
        for key, value in settings.items():
            self.model.config.set(key, value)
        
        # Mettre à jour l'interface
        # (Si le thème a changé, il faut le mettre à jour dans l'application)
        if hasattr(self.parent, "update_theme"):
            self.parent.update_theme()
        
        # Afficher un message de confirmation
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Paramètres enregistrés")
        dialog.geometry("300x150")
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
        
        # Message
        msg_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        msg_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            msg_frame,
            text="✅ Paramètres enregistrés",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(
            msg_frame,
            text="Les paramètres ont été enregistrés avec succès."
        ).pack(pady=10)
        
        # Bouton OK
        ctk.CTkButton(
            msg_frame,
            text="OK",
            width=100,
            command=dialog.destroy
        ).pack(pady=10)
        
        logger.info("Paramètres enregistrés")
    
    def create_backup(self):
        """
        Crée une sauvegarde des données
        """
        # Cette méthode sera implémentée plus tard
        logger.info("Action: Créer une sauvegarde (non implémentée)")
    
    def restore_backup(self):
        """
        Restaure les données à partir d'une sauvegarde
        """
        # Cette méthode sera implémentée plus tard
        logger.info("Action: Restaurer une sauvegarde (non implémentée)")
    
    def reset_settings(self):
        """
        Réinitialise les paramètres aux valeurs par défaut
        """
        # Demander confirmation
        dialog = ctk.CTkToplevel(self.parent)
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
        
        # Message
        msg_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        msg_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            msg_frame,
            text="⚠️ Confirmer la réinitialisation",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(
            msg_frame,
            text="Êtes-vous sûr de vouloir réinitialiser tous les paramètres aux valeurs par défaut ?",
            wraplength=360
        ).pack(pady=10)
        
        # Boutons
        btn_frame = ctk.CTkFrame(msg_frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        # Fonction pour réinitialiser
        def confirm_reset():
            # Réinitialiser la configuration
            self.model.config.reset_to_defaults()
            
            # Mettre à jour la vue
            self.update_view()
            
            # Fermer la boîte de dialogue
            dialog.destroy()
            
            logger.info("Paramètres réinitialisés")
        
        # Bouton Annuler
        ctk.CTkButton(
            btn_frame,
            text="Annuler",
            width=100,
            command=dialog.destroy
        ).pack(side=ctk.LEFT, padx=10)
        
        # Bouton Réinitialiser
        ctk.CTkButton(
            btn_frame,
            text="Réinitialiser",
            width=100,
            fg_color="red",
            command=confirm_reset
        ).pack(side=ctk.LEFT, padx=10)