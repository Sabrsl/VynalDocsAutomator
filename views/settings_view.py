#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue des paramètres pour l'application Vynal Docs Automator
"""

import os
import logging
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog

logger = logging.getLogger("VynalDocsAutomator.SettingsView")

class DialogUtils:
    """
    Utilitaires pour créer des boîtes de dialogue cohérentes dans l'application
    """
    
    @staticmethod
    def show_confirmation(parent, title, message, on_yes=None, on_no=None):
        """
        Affiche une boîte de dialogue de confirmation
        
        Args:
            parent: Widget parent
            title: Titre de la boîte de dialogue
            message: Message à afficher
            on_yes: Fonction à appeler si l'utilisateur confirme
            on_no: Fonction à appeler si l'utilisateur annule
            
        Returns:
            bool: True si confirmé, False sinon
        """
        dialog = ctk.CTkToplevel(parent)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.focus_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Résultat par défaut
        result = [False]
        
        # Cadre principal
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre avec icône
        ctk.CTkLabel(
            frame,
            text=f"⚠️ {title}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 10))
        
        # Message
        ctk.CTkLabel(
            frame,
            text=message,
            wraplength=360
        ).pack(pady=10)
        
        # Cadre pour les boutons
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(pady=10)
        
        # Fonctions de callback
        def yes_action():
            result[0] = True
            dialog.destroy()
            if on_yes:
                on_yes()
        
        def no_action():
            result[0] = False
            dialog.destroy()
            if on_no:
                on_no()
        
        # Bouton Non
        ctk.CTkButton(
            button_frame,
            text="Non",
            command=no_action,
            width=100,
            fg_color="#e74c3c",
            hover_color="#c0392b"
        ).pack(side=ctk.LEFT, padx=10)
        
        # Bouton Oui
        ctk.CTkButton(
            button_frame,
            text="Oui",
            command=yes_action,
            width=100,
            fg_color="#2ecc71",
            hover_color="#27ae60"
        ).pack(side=ctk.LEFT, padx=10)
        
        # Attendre que la fenêtre soit fermée
        parent.wait_window(dialog)
        
        return result[0]
    
    @staticmethod
    def show_message(parent, title, message, message_type="info"):
        """
        Affiche une boîte de dialogue avec un message
        
        Args:
            parent: Widget parent
            title: Titre de la boîte de dialogue
            message: Message à afficher
            message_type: Type de message ('info', 'error', 'warning', 'success')
        """
        dialog = ctk.CTkToplevel(parent)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.focus_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Icône selon le type
        icon = "ℹ️"
        button_color = "#3498db"
        hover_color = "#2980b9"
        
        if message_type == "error":
            icon = "❌"
            button_color = "#e74c3c"
            hover_color = "#c0392b"
        elif message_type == "warning":
            icon = "⚠️"
            button_color = "#f39c12"
            hover_color = "#d35400"
        elif message_type == "success":
            icon = "✅"
            button_color = "#2ecc71"
            hover_color = "#27ae60"
        
        # Cadre principal
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre avec icône
        ctk.CTkLabel(
            frame,
            text=f"{icon} {title}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 10))
        
        # Message
        ctk.CTkLabel(
            frame,
            text=message,
            wraplength=360
        ).pack(pady=10)
        
        # Bouton OK
        ctk.CTkButton(
            frame,
            text="OK",
            command=dialog.destroy,
            width=100,
            fg_color=button_color,
            hover_color=hover_color
        ).pack(pady=10)

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
        default_pattern = "{document_type}_{client_name}_{date}"
        self.filename_pattern_var = ctk.StringVar(value=self.model.config.get("document.filename_pattern", default_pattern))
        self.create_setting(
            "Modèle de nom de fichier",
            "Pattern pour nommer les fichiers (ex: {document_type}_{client_name}_{date})",
            "entry",
            self.filename_pattern_var
        )
        
        # Format de date
        default_format = "%Y-%m-%d"
        self.date_format_var = ctk.StringVar(value=self.model.config.get("document.date_format", default_format))
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
            fg_color="#e74c3c",
            hover_color="#c0392b",
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
            fg_color="#2ecc71",
            hover_color="#27ae60",
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
                width=250,
                state="readonly"  # Assure qu'on ne peut que sélectionner des valeurs valides
            ).pack(side=ctk.RIGHT, pady=5)
        
        elif widget_type == "switch":
            ctk.CTkSwitch(
                widget_frame,
                text="",
                variable=variable,
                onvalue=True,
                offvalue=False
            ).pack(side=ctk.RIGHT, pady=5)
        
        elif widget_type == "slider":
            min_val, max_val = options
            slider_frame = ctk.CTkFrame(widget_frame, fg_color="transparent")
            slider_frame.pack(side=ctk.RIGHT, fill=ctk.X, expand=True, pady=5)
            
            slider = ctk.CTkSlider(
                slider_frame,
                from_=min_val,
                to=max_val,
                number_of_steps=max_val-min_val,
                variable=variable
            )
            slider.pack(side=ctk.LEFT, fill=ctk.X, expand=True, pady=5)
            
            value_label = ctk.CTkLabel(
                slider_frame,
                text=str(int(variable.get())),
                width=30
            )
            value_label.pack(side=ctk.RIGHT, padx=10)
            
            # Mettre à jour l'étiquette de valeur
            def update_value_label(*args):
                try:
                    value = int(variable.get())
                    value_label.configure(text=str(value))
                except:
                    pass
            
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
        # Mettre à jour les variables avec des valeurs par défaut si non définies
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
        
        # Utiliser une valeur par défaut pour le modèle de nom de fichier si non défini
        default_pattern = "{document_type}_{client_name}_{date}"
        self.filename_pattern_var.set(self.model.config.get("document.filename_pattern", default_pattern))
        
        # Utiliser une valeur par défaut pour le format de date si non défini
        default_format = "%Y-%m-%d"
        self.date_format_var.set(self.model.config.get("document.date_format", default_format))
        
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
            "app.save_interval": int(self.save_interval_var.get()),
            "paths.documents": self.documents_dir_var.get(),
            "paths.templates": self.templates_dir_var.get(),
            "security.require_password": self.require_password_var.get(),
            "security.auto_lock": self.auto_lock_var.get(),
            "security.lock_time": int(self.lock_time_var.get()),
            "document.default_format": self.default_format_var.get(),
            "document.filename_pattern": self.filename_pattern_var.get() or "{document_type}_{client_name}_{date}",
            "document.date_format": self.date_format_var.get() or "%Y-%m-%d"
        }
        
        # Créer les répertoires s'ils n'existent pas
        for path_key in ["paths.documents", "paths.templates"]:
            path = settings.get(path_key, "")
            if path and not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                    logger.info(f"Répertoire créé: {path}")
                except Exception as e:
                    logger.error(f"Erreur lors de la création du répertoire {path}: {e}")
                    DialogUtils.show_message(
                        self.parent,
                        "Erreur",
                        f"Impossible de créer le répertoire {path}:\n{str(e)}",
                        "error"
                    )
                    return
        
        # Enregistrer les paramètres
        try:
            for key, value in settings.items():
                self.model.config.set(key, value)
            
            # Mettre à jour les chemins dans le modèle
            self.model.paths['documents'] = settings["paths.documents"]
            self.model.paths['templates'] = settings["paths.templates"]
            
            # Mettre à jour l'interface
            # (Si le thème a changé, il faut le mettre à jour dans l'application)
            current_theme = ctk.get_appearance_mode().lower()
            new_theme = settings["app.theme"].lower()
            
            if new_theme != "system" and new_theme != current_theme:
                ctk.set_appearance_mode(new_theme)
                logger.info(f"Thème changé: {new_theme}")
            
            # Afficher un message de confirmation
            DialogUtils.show_message(
                self.parent,
                "Paramètres enregistrés",
                "Les paramètres ont été enregistrés avec succès.",
                "success"
            )
            
            logger.info("Paramètres enregistrés")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des paramètres: {e}")
            DialogUtils.show_message(
                self.parent,
                "Erreur",
                f"Erreur lors de l'enregistrement des paramètres:\n{str(e)}",
                "error"
            )
    
    def create_backup(self):
        """
        Crée une sauvegarde des données
        """
        try:
            # Demander l'emplacement de la sauvegarde
            backup_path = filedialog.asksaveasfilename(
                title="Créer une sauvegarde",
                defaultextension=".zip",
                filetypes=[("Fichiers ZIP", "*.zip"), ("Tous les fichiers", "*.*")]
            )
            
            if not backup_path:
                return
            
            # Appeler la méthode du modèle pour créer la sauvegarde
            result = self.model.create_backup(backup_path)
            
            if result:
                DialogUtils.show_message(
                    self.parent,
                    "Sauvegarde créée",
                    f"Sauvegarde créée avec succès:\n{backup_path}",
                    "success"
                )
                logger.info(f"Sauvegarde créée: {backup_path}")
            else:
                DialogUtils.show_message(
                    self.parent,
                    "Erreur",
                    "Impossible de créer la sauvegarde.",
                    "error"
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de la sauvegarde: {e}")
            DialogUtils.show_message(
                self.parent,
                "Erreur",
                f"Erreur lors de la création de la sauvegarde:\n{str(e)}",
                "error"
            )
    
    def restore_backup(self):
        """
        Restaure les données à partir d'une sauvegarde
        """
        try:
            # Demander le fichier de sauvegarde
            backup_path = filedialog.askopenfilename(
                title="Restaurer une sauvegarde",
                filetypes=[("Fichiers ZIP", "*.zip"), ("Tous les fichiers", "*.*")]
            )
            
            if not backup_path:
                return
            
            def process_restore():
                try:
                    # Appeler la méthode du modèle pour restaurer la sauvegarde
                    result = self.model.restore_backup(backup_path)
                    
                    if result:
                        DialogUtils.show_message(
                            self.parent,
                            "Restauration terminée",
                            "La sauvegarde a été restaurée avec succès.\nVeuillez redémarrer l'application pour appliquer les changements.",
                            "success"
                        )
                        logger.info(f"Sauvegarde restaurée: {backup_path}")
                        
                        # Mettre à jour la vue
                        self.update_view()
                    else:
                        DialogUtils.show_message(
                            self.parent,
                            "Erreur",
                            "Impossible de restaurer la sauvegarde.",
                            "error"
                        )
                except Exception as e:
                    logger.error(f"Erreur lors de la restauration: {e}")
                    DialogUtils.show_message(
                        self.parent,
                        "Erreur",
                        f"Erreur lors de la restauration:\n{str(e)}",
                        "error"
                    )
            
            # Demander confirmation
            DialogUtils.show_confirmation(
                self.parent,
                "Confirmer la restauration",
                "Restaurer une sauvegarde remplacera toutes vos données actuelles. Cette action est irréversible.\n\nÊtes-vous sûr de vouloir continuer?",
                on_yes=process_restore
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la restauration de la sauvegarde: {e}")
            DialogUtils.show_message(
                self.parent,
                "Erreur",
                f"Erreur lors de la restauration de la sauvegarde:\n{str(e)}",
                "error"
            )
    
    def reset_settings(self):
        """
        Réinitialise les paramètres aux valeurs par défaut
        """
        # Demander confirmation
        def confirm_reset():
            try:
                # Définir des valeurs par défaut sécurisées
                default_values = {
                    "app.company_name": "Vynal Docs",
                    "app.company_logo": "",
                    "app.theme": "system",
                    "app.auto_save": True,
                    "app.save_interval": 5,
                    "paths.documents": os.path.join(os.path.expanduser("~"), "VynalDocs", "Documents"),
                    "paths.templates": os.path.join(os.path.expanduser("~"), "VynalDocs", "Templates"),
                    "security.require_password": False,
                    "security.auto_lock": False,
                    "security.lock_time": 10,
                    "document.default_format": "pdf",
                    "document.filename_pattern": "{document_type}_{client_name}_{date}",
                    "document.date_format": "%Y-%m-%d"
                }
                
                # Éviter d'utiliser la méthode reset_to_defaults qui peut causer des problèmes
                # Définir directement les valeurs dans la configuration
                try:
                    # Sauvegarder le thème actuel pour le restaurer après
                    current_theme = self.model.config.get("app.theme", "system")
                    
                    # Définir chaque valeur individuellement
                    for key, value in default_values.items():
                        self.model.config.set(key, value)
                    
                    # Créer les répertoires nécessaires
                    os.makedirs(default_values["paths.documents"], exist_ok=True)
                    os.makedirs(default_values["paths.templates"], exist_ok=True)
                    
                    # Mettre à jour les chemins dans le modèle
                    self.model.paths['documents'] = default_values["paths.documents"]
                    self.model.paths['templates'] = default_values["paths.templates"]
                    
                    # Mettre à jour la vue sans toucher au thème pour l'instant
                    self.company_name_var.set(default_values["app.company_name"])
                    self.company_logo_var.set(default_values["app.company_logo"])
                    self.theme_var.set(default_values["app.theme"])
                    self.auto_save_var.set(default_values["app.auto_save"])
                    self.save_interval_var.set(default_values["app.save_interval"])
                    self.documents_dir_var.set(default_values["paths.documents"])
                    self.templates_dir_var.set(default_values["paths.templates"])
                    self.require_password_var.set(default_values["security.require_password"])
                    self.auto_lock_var.set(default_values["security.auto_lock"])
                    self.lock_time_var.set(default_values["security.lock_time"])
                    self.default_format_var.set(default_values["document.default_format"])
                    self.filename_pattern_var.set(default_values["document.filename_pattern"])
                    self.date_format_var.set(default_values["document.date_format"])
                    
                    # Afficher un message de succès
                    DialogUtils.show_message(
                        self.parent,
                        "Paramètres réinitialisés",
                        "Les paramètres ont été réinitialisés aux valeurs par défaut.",
                        "success"
                    )
                    
                    logger.info("Paramètres réinitialisés avec succès")
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la réinitialisation des paramètres: {e}")
                    DialogUtils.show_message(
                        self.parent,
                        "Erreur",
                        f"Erreur lors de la réinitialisation des paramètres:\n{str(e)}",
                        "error"
                    )
            except Exception as e:
                logger.error(f"Erreur globale lors de la réinitialisation des paramètres: {e}")
                DialogUtils.show_message(
                    self.parent,
                    "Erreur",
                    f"Une erreur inattendue s'est produite:\n{str(e)}",
                    "error"
                )
        
        DialogUtils.show_confirmation(
            self.parent,
            "Confirmer la réinitialisation",
            "Êtes-vous sûr de vouloir réinitialiser tous les paramètres aux valeurs par défaut ?",
            on_yes=confirm_reset
        )