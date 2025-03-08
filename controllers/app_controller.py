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
    
    def setup_event_handlers(self):
        """
        Configure les gestionnaires d'événements globaux et les connexions entre vues et contrôleurs
        """
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
        # À implémenter si nécessaire plus tard
        
        logger.info("Gestionnaires d'événements configurés")
    
    def on_exit(self):
        """
        Gère la fermeture de l'application
        """
        logger.info("Fermeture de l'application demandée")
        
        # Demander confirmation
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
        
        directory = filedialog.askdirectory(initialdir=initial_dir)
        
        if directory:
            logger.info(f"Dossier sélectionné: {directory}")
            return directory
        
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
        
        file_path = filedialog.askopenfilename(
            filetypes=file_types,
            initialdir=initial_dir
        )
        
        if file_path:
            logger.info(f"Fichier sélectionné: {file_path}")
            return file_path
        
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
        
        file_path = filedialog.asksaveasfilename(
            filetypes=file_types,
            initialdir=initial_dir,
            defaultextension=default_extension,
            initialfile=initial_file
        )
        
        if file_path:
            logger.info(f"Fichier à enregistrer: {file_path}")
            return file_path
        
        return None
    
    def backup_data(self):
        """
        Crée une sauvegarde des données de l'application
        
        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        try:
            # Sauvegarder la configuration
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
            self.view.show_message("Erreur", f"Échec de la sauvegarde: {e}", "error")
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
            
            if not all(os.path.exists(file) for file in [clients_backup, templates_backup, documents_backup]):
                self.view.show_message("Erreur", "Sauvegarde incomplète ou invalide", "error")
                return False
            
            # Confirmer la restauration
            def perform_restore():
                # Restaurer les fichiers
                try:
                    # Remplacer les fichiers existants par les sauvegardes
                    clients_file = os.path.join(self.model.paths['clients'], "clients.json")
                    templates_file = os.path.join(self.model.paths['templates'], "templates.json")
                    documents_file = os.path.join(self.model.paths['documents'], "documents.json")
                    
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
                    self.view.show_message("Erreur", f"Échec de la restauration: {e}", "error")
                    return False
            
            message = "Êtes-vous sûr de vouloir restaurer les données à partir de cette sauvegarde ? Les données actuelles seront remplacées."
            self.view.show_confirmation("Confirmer la restauration", message, perform_restore)
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la restauration des données: {e}")
            self.view.show_message("Erreur", f"Échec de la restauration: {e}", "error")
            return False