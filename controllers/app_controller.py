#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contrôleur principal de l'application Vynal Docs Automator
"""

import os
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
import datetime
import shutil
import customtkinter as ctk

logger = logging.getLogger("VynalDocsAutomator.AppController")

class AppController:
    """
    Contrôleur principal de l'application
    Gère la logique globale et coordonne les différents composants
    """
    
    def __init__(self, app_model, main_view):
        """
        Initialise le contrôleur principal
        
        Args:
            app_model: Modèle de l'application
            main_view: Vue principale
        """
        self.model = app_model
        self.view = main_view
        
        logger.info("Initialisation du contrôleur principal...")
        
        try:
            # Import des contrôleurs spécifiques
            from controllers.client_controller import ClientController
            from controllers.document_controller import DocumentController
            from controllers.template_controller import TemplateController
            
            # Initialiser les contrôleurs spécifiques
            logger.info("Initialisation des contrôleurs spécifiques...")
            self.client_controller = ClientController(app_model, main_view.views["clients"])
            self.document_controller = DocumentController(app_model, main_view.views["documents"])
            self.template_controller = TemplateController(app_model, main_view.views["templates"])
            
            # TRÈS IMPORTANT: Connecter les événements des contrôleurs
            logger.info("Connexion des événements des contrôleurs...")
            self.client_controller.connect_events()
            self.document_controller.connect_events()
            self.template_controller.connect_events()
            
            # Configuration des événements globaux
            self.setup_event_handlers()
            
            logger.info("AppController initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du contrôleur: {e}")
            self.view.show_message("Erreur d'initialisation", 
                                  f"Une erreur est survenue lors de l'initialisation de l'application: {str(e)}", 
                                  "error")
    
    def setup_event_handlers(self):
        """
        Configure les gestionnaires d'événements globaux et les connexions entre vues et contrôleurs
        """
        try:
            # Configurer les actions du tableau de bord
            dashboard_view = self.view.views["dashboard"]
            dashboard_view.new_document = self.document_controller.new_document
            dashboard_view.add_client = self.client_controller.show_client_form
            dashboard_view.new_template = self.template_controller.new_template
            
            # Configurer les actions des paramètres
            settings_view = self.view.views["settings"]
            if hasattr(settings_view, 'create_backup'):
                settings_view.create_backup = self.backup_data
            if hasattr(settings_view, 'restore_backup'):
                settings_view.restore_backup = self.restore_data
            
            # Configuration des raccourcis clavier globaux
            self.setup_keyboard_shortcuts()
            
            logger.info("Gestionnaires d'événements configurés")
        except Exception as e:
            logger.error(f"Erreur lors de la configuration des événements: {e}")
    
    def setup_keyboard_shortcuts(self):
        """
        Configure les raccourcis clavier globaux
        """
        # Raccourcis clavier à implémenter dans une future version
        pass
    
    def on_exit(self):
        """
        Gère la fermeture de l'application
        
        Returns:
            bool: True si l'application doit être fermée, False sinon
        """
        logger.info("Fermeture de l'application demandée")
        
        # Vérifier s'il y a des données non sauvegardées
        # Cette vérification pourrait être plus sophistiquée dans une future version
        
        # Demander confirmation avec une boîte de dialogue customtkinter si disponible
        try:
            # Utiliser une boîte de dialogue customtkinter pour un style cohérent
            dialog = ctk.CTkToplevel(self.view.root)
            dialog.title("Confirmer la fermeture")
            dialog.geometry("400x150")
            dialog.transient(self.view.root)
            dialog.grab_set()
            
            # Centrer la fenêtre
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
            y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")
            
            frame = ctk.CTkFrame(dialog)
            frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            
            ctk.CTkLabel(
                frame, 
                text="Êtes-vous sûr de vouloir quitter l'application?",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=10)
            
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.pack(fill=ctk.X, pady=10)
            
            result = [False]  # Utiliser une liste pour pouvoir modifier la valeur dans les callbacks
            
            def on_yes():
                result[0] = True
                dialog.destroy()
                
            def on_no():
                result[0] = False
                dialog.destroy()
            
            ctk.CTkButton(
                btn_frame, 
                text="Oui", 
                command=on_yes,
                width=100,
                fg_color="#2ecc71",
                hover_color="#27ae60"
            ).pack(side=ctk.RIGHT, padx=10)
            
            ctk.CTkButton(
                btn_frame, 
                text="Non", 
                command=on_no,
                width=100,
                fg_color="#e74c3c",
                hover_color="#c0392b"
            ).pack(side=ctk.RIGHT, padx=10)
            
            # Attendre que la boîte de dialogue soit fermée
            self.view.root.wait_window(dialog)
            confirm = result[0]
            
        except Exception as e:
            # Fallback sur la messagebox standard en cas d'erreur
            logger.error(f"Erreur lors de l'affichage de la boîte de dialogue CTk: {e}")
            confirm = messagebox.askyesno(
                "Confirmer la fermeture",
                "Êtes-vous sûr de vouloir quitter l'application?",
                parent=self.view.root
            )
        
        if confirm:
            # Sauvegarder les données non enregistrées
            try:
                self.model.save_clients()
                self.model.save_templates()
                self.model.save_documents()
                logger.info("Données sauvegardées avant fermeture")
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde des données: {e}")
                
                # Informer l'utilisateur et demander s'il veut continuer la fermeture
                continue_exit = messagebox.askyesno(
                    "Erreur de sauvegarde",
                    f"Une erreur est survenue lors de la sauvegarde des données: {str(e)}\n\nVoulez-vous quand même quitter l'application?",
                    parent=self.view.root
                )
                
                if not continue_exit:
                    return False
            
            logger.info("Fermeture confirmée")
            return True
        
        return False
     
    def show_dashboard(self):
        """
        Affiche le tableau de bord
        """
        self.view.show_view("dashboard")
    
    def show_clients(self):
        """
        Affiche la vue de gestion des clients
        """
        self.view.show_view("clients")
    
    def show_templates(self):
        """
        Affiche la vue de gestion des modèles
        """
        self.view.show_view("templates")
    
    def show_documents(self):
        """
        Affiche la vue de gestion des documents
        """
        self.view.show_view("documents")
    
    def show_settings(self):
        """
        Affiche la vue des paramètres
        """
        self.view.show_view("settings")
    
    def browse_directory(self, initial_dir=None):
        """
        Ouvre une boîte de dialogue pour sélectionner un dossier
        
        Args:
            initial_dir: Dossier initial à afficher
            
        Returns:
            str: Chemin du dossier sélectionné ou None si annulé
        """
        if initial_dir is None:
            initial_dir = os.path.expanduser("~")
        
        try:
            directory = filedialog.askdirectory(initialdir=initial_dir)
            
            if directory:
                logger.info(f"Dossier sélectionné: {directory}")
                return directory
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du dossier: {e}")
            self.view.show_message("Erreur", f"Impossible de sélectionner un dossier: {str(e)}", "error")
        
        return None
    
    def browse_file(self, file_types=None, initial_dir=None):
        """
        Ouvre une boîte de dialogue pour sélectionner un fichier
        
        Args:
            file_types: Liste des types de fichiers à afficher
            initial_dir: Dossier initial à afficher
            
        Returns:
            str: Chemin du fichier sélectionné ou None si annulé
        """
        if file_types is None:
            file_types = [("Tous les fichiers", "*.*")]
        
        if initial_dir is None:
            initial_dir = os.path.expanduser("~")
        
        try:
            file_path = filedialog.askopenfilename(
                filetypes=file_types,
                initialdir=initial_dir
            )
            
            if file_path:
                logger.info(f"Fichier sélectionné: {file_path}")
                return file_path
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du fichier: {e}")
            self.view.show_message("Erreur", f"Impossible de sélectionner un fichier: {str(e)}", "error")
        
        return None
    
    def save_file(self, file_types=None, initial_dir=None, default_extension=None, initial_file=None):
        """
        Ouvre une boîte de dialogue pour enregistrer un fichier
        
        Args:
            file_types: Liste des types de fichiers à afficher
            initial_dir: Dossier initial à afficher
            default_extension: Extension par défaut
            initial_file: Nom de fichier initial
            
        Returns:
            str: Chemin du fichier sélectionné ou None si annulé
        """
        if file_types is None:
            file_types = [("Tous les fichiers", "*.*")]
        
        if initial_dir is None:
            initial_dir = os.path.expanduser("~")
        
        if default_extension is None:
            default_extension = ".pdf"
        
        try:
            file_path = filedialog.asksaveasfilename(
                filetypes=file_types,
                initialdir=initial_dir,
                defaultextension=default_extension,
                initialfile=initial_file
            )
            
            if file_path:
                logger.info(f"Fichier à enregistrer: {file_path}")
                return file_path
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du fichier: {e}")
            self.view.show_message("Erreur", f"Impossible d'enregistrer le fichier: {str(e)}", "error")
        
        return None
    
    def backup_data(self):
        """
        Crée une sauvegarde des données de l'application
        
        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        try:
            # Vérifier si le dossier de sauvegarde existe
            if not os.path.exists(self.model.paths['backup']):
                os.makedirs(self.model.paths['backup'])
            
            # Sauvegarder la configuration
            if hasattr(self.model.config, 'backup_config'):
                config_backup_path = self.model.config.backup_config()
            
            # Créer un dossier de sauvegarde avec la date
            backup_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(self.model.paths['backup'], f"backup_{backup_date}")
            
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Sauvegarder les fichiers de données
            clients_backup = os.path.join(backup_dir, "clients.json")
            templates_backup = os.path.join(backup_dir, "templates.json")
            documents_backup = os.path.join(backup_dir, "documents.json")
            
            # Sauvegarder les clients, modèles et documents
            self.model.save_clients()
            self.model.save_templates()
            self.model.save_documents()
            
            # Copier les fichiers
            clients_file = os.path.join(self.model.paths['clients'], "clients.json")
            templates_file = os.path.join(self.model.paths['templates'], "templates.json")
            documents_file = os.path.join(self.model.paths['documents'], "documents.json")
            
            if os.path.exists(clients_file):
                shutil.copy2(clients_file, clients_backup)
            
            if os.path.exists(templates_file):
                shutil.copy2(templates_file, templates_backup)
            
            if os.path.exists(documents_file):
                shutil.copy2(documents_file, documents_backup)
            
            message = f"Sauvegarde créée avec succès dans {backup_dir}"
            self.view.show_message("Sauvegarde réussie", message, "info")
            
            logger.info(f"Sauvegarde complète créée dans {backup_dir}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des données: {e}")
            self.view.show_message("Erreur", f"Échec de la sauvegarde: {str(e)}", "error")
            return False
    
    def restore_data(self, backup_path=None):
        """
        Restaure les données à partir d'une sauvegarde
        
        Args:
            backup_path: Chemin du fichier de sauvegarde à utiliser
            
        Returns:
            bool: True si la restauration a réussi, False sinon
        """
        try:
            if backup_path is None:
                # Demander à l'utilisateur de sélectionner un dossier de sauvegarde
                backup_path = self.browse_directory(
                    initial_dir=self.model.paths['backup']
                )
            
            if not backup_path:
                return False
            
            # Vérifier que les fichiers nécessaires existent
            clients_backup = os.path.join(backup_path, "clients.json")
            templates_backup = os.path.join(backup_path, "templates.json")
            documents_backup = os.path.join(backup_path, "documents.json")
            
            missing_files = []
            if not os.path.exists(clients_backup):
                missing_files.append("clients.json")
            if not os.path.exists(templates_backup):
                missing_files.append("templates.json")
            if not os.path.exists(documents_backup):
                missing_files.append("documents.json")
                
            if missing_files:
                self.view.show_message(
                    "Sauvegarde incomplète", 
                    f"La sauvegarde est incomplète. Fichiers manquants: {', '.join(missing_files)}", 
                    "error"
                )
                return False
            
            # Confirmer la restauration
            def perform_restore():
                # Restaurer les fichiers
                try:
                    # Remplacer les fichiers existants par les sauvegardes
                    clients_file = os.path.join(self.model.paths['clients'], "clients.json")
                    templates_file = os.path.join(self.model.paths['templates'], "templates.json")
                    documents_file = os.path.join(self.model.paths['documents'], "documents.json")
                    
                    # Vérifier que les dossiers existent
                    os.makedirs(os.path.dirname(clients_file), exist_ok=True)
                    os.makedirs(os.path.dirname(templates_file), exist_ok=True)
                    os.makedirs(os.path.dirname(documents_file), exist_ok=True)
                    
                    shutil.copy2(clients_backup, clients_file)
                    shutil.copy2(templates_backup, templates_file)
                    shutil.copy2(documents_backup, documents_file)
                    
                    # Recharger les données
                    self.model.load_all_data()
                    
                    # Mettre à jour les vues
                    self.view.update_view()
                    
                    message = "Les données ont été restaurées avec succès."
                    self.view.show_message("Restauration réussie", message, "info")
                    
                    logger.info(f"Données restaurées depuis {backup_path}")
                    return True
                except Exception as e:
                    logger.error(f"Erreur lors de la restauration des fichiers: {e}")
                    self.view.show_message("Erreur", f"Échec de la restauration: {str(e)}", "error")
                    return False
            
            message = "Êtes-vous sûr de vouloir restaurer les données à partir de cette sauvegarde ? Les données actuelles seront remplacées."
            self.view.show_confirmation("Confirmer la restauration", message, perform_restore)
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la restauration des données: {e}")
            self.view.show_message("Erreur", f"Échec de la restauration: {str(e)}", "error")
            return False