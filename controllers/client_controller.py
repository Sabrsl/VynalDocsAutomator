#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contrôleur de gestion des clients pour l'application Vynal Docs Automator
"""

import os
import csv
import json
import logging
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
from datetime import datetime

logger = logging.getLogger("VynalDocsAutomator.ClientController")

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

class ClientController:
    """
    Contrôleur de gestion des clients
    Gère la logique métier liée aux clients
    """
    
    def __init__(self, app_model, client_view):
        """
        Initialise le contrôleur des clients
        
        Args:
            app_model: Modèle de l'application
            client_view: Vue de gestion des clients
        """
        self.model = app_model
        self.view = client_view
        
        # Garantir l'existence du dictionnaire clients dans le modèle
        if not hasattr(self.model, 'clients'):
            self.model.clients = []
        
        # Connecter les événements de la vue aux méthodes du contrôleur
        self.connect_events()
        
        logger.info("ClientController initialisé")
    
    def connect_events(self):
        """
        Connecte les événements de la vue aux méthodes du contrôleur
        """
        # Remplacer les méthodes de la vue par les méthodes du contrôleur
        self.view.show_client_form = self.show_client_form
        self.view.edit_client = self.edit_client
        self.view.confirm_delete_client = self.confirm_delete_client
        
        # S'assurer que les boutons d'importation et d'exportation sont correctement liés
        try:
            if hasattr(self.view, 'import_btn'):
                self.view.import_btn.configure(command=self.import_clients)
                logger.info("Bouton d'importation connecté")
            
            if hasattr(self.view, 'export_btn'):
                self.view.export_btn.configure(command=self.export_clients)
                logger.info("Bouton d'exportation connecté")
                
            # Assurer également que les méthodes de la vue sont correctement liées
            self.view.import_clients = self.import_clients
            self.view.export_clients = self.export_clients
        except Exception as e:
            logger.error(f"Erreur lors de la connexion des boutons: {e}")
        
        # Ajouter les méthodes nécessaires au modèle pour que la vue puisse les utiliser
        self.model.get_all_clients = lambda: self.model.clients if hasattr(self.model, 'clients') else []
        self.model.get_client = lambda client_id: next((c for c in self.model.clients if c.get('id') == client_id), None)
        self.model.update_client = self.update_client_model
        self.model.add_client = self.add_client_model
        self.model.delete_client = self.delete_client_model
        
        logger.info("Événements de ClientView connectés")
    
    def update_client_model(self, client_id, data):
        """
        Mise à jour d'un client dans le modèle
        
        Args:
            client_id: ID du client à mettre à jour
            data: Nouvelles données du client
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            # Trouver le client
            client_index = next((i for i, c in enumerate(self.model.clients) if c.get('id') == client_id), None)
            if client_index is None:
                return False
            
            # Conserver l'ID et les timestamps
            data['id'] = client_id
            data['created_at'] = self.model.clients[client_index].get('created_at', datetime.now().isoformat())
            data['updated_at'] = datetime.now().isoformat()
            
            # Mettre à jour le client
            self.model.clients[client_index] = data
            
            # Sauvegarder les modifications
            self.model.save_clients()
            
            # Ajouter l'activité
            self.model.add_activity('client', f"Client modifié: {data.get('name')}")
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du client: {e}")
            return False
    
    def add_client_model(self, data):
        """
        Ajout d'un client dans le modèle
        
        Args:
            data: Données du client
            
        Returns:
            str/None: ID du client si succès, None sinon
        """
        try:
            # Générer un ID unique
            new_id = f"client_{len(self.model.clients) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Ajouter les timestamps
            data['id'] = new_id
            data['created_at'] = datetime.now().isoformat()
            data['updated_at'] = datetime.now().isoformat()
            
            # Ajouter le client
            self.model.clients.append(data)
            
            # Sauvegarder les modifications
            self.model.save_clients()
            
            # Ajouter l'activité
            self.model.add_activity('client', f"Nouveau client: {data.get('name')}")
            
            return new_id
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du client: {e}")
            return None
    
    def delete_client_model(self, client_id):
        """
        Suppression d'un client du modèle
        
        Args:
            client_id: ID du client à supprimer
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            # Trouver le client
            client = next((c for c in self.model.clients if c.get('id') == client_id), None)
            if client is None:
                return False
            
            # Supprimer le client
            self.model.clients = [c for c in self.model.clients if c.get('id') != client_id]
            
            # Sauvegarder les modifications
            self.model.save_clients()
            
            # Ajouter l'activité
            self.model.add_activity('client', f"Client supprimé: {client.get('name')}")
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du client: {e}")
            return False
    
    def show_client_form(self, client_id=None):
        """
        Affiche le formulaire pour ajouter ou modifier un client
        
        Args:
            client_id: ID du client à modifier, ou None pour un nouveau client
        """
        # Créer une fenêtre de dialogue
        dialog = ctk.CTkToplevel(self.view.parent)
        dialog.title("Nouveau client" if client_id is None else "Modifier le client")
        dialog.geometry("550x550")
        dialog.resizable(False, False)
        dialog.grab_set()  # Modal
        dialog.focus_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Variables pour le formulaire
        client_data = {}
        if client_id:
            # Chercher le client existant
            client = next((c for c in self.model.clients if c.get('id') == client_id), None)
            if client:
                client_data = client.copy()
        
        # Créer un cadre principal avec défilement
        main_frame = ctk.CTkScrollableFrame(dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Informations du client
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill=ctk.X, pady=10)
        
        ctk.CTkLabel(
            info_frame, 
            text="Informations du client", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        form_frame = ctk.CTkFrame(info_frame)
        form_frame.pack(fill=ctk.X, padx=10, pady=10)
        
        # Nom
        name_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        name_row.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(name_row, text="Nom*:").pack(side=ctk.LEFT, padx=5)
        name_var = ctk.StringVar(value=client_data.get('name', ''))
        name_entry = ctk.CTkEntry(name_row, textvariable=name_var, width=300)
        name_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5)
        
        # Entreprise
        company_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        company_row.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(company_row, text="Entreprise:").pack(side=ctk.LEFT, padx=5)
        company_var = ctk.StringVar(value=client_data.get('company', ''))
        company_entry = ctk.CTkEntry(company_row, textvariable=company_var, width=300)
        company_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5)
        
        # Email
        email_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        email_row.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(email_row, text="Email*:").pack(side=ctk.LEFT, padx=5)
        email_var = ctk.StringVar(value=client_data.get('email', ''))
        email_entry = ctk.CTkEntry(email_row, textvariable=email_var, width=300)
        email_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5)
        
        # Téléphone
        phone_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        phone_row.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(phone_row, text="Téléphone:").pack(side=ctk.LEFT, padx=5)
        phone_var = ctk.StringVar(value=client_data.get('phone', ''))
        phone_entry = ctk.CTkEntry(phone_row, textvariable=phone_var, width=300)
        phone_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5)
        
        # Adresse
        address_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        address_row.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(address_row, text="Adresse:").pack(side=ctk.LEFT, padx=5)
        address_frame = ctk.CTkFrame(address_row, fg_color="transparent")
        address_frame.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5)
        address_text = ctk.CTkTextbox(address_frame, width=300, height=80)
        address_text.pack(fill=ctk.BOTH, expand=True)
        address_text.insert("1.0", client_data.get('address', ''))
        
        # Note obligatoire
        note_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        note_frame.pack(fill=ctk.X, pady=10)
        ctk.CTkLabel(
            note_frame, 
            text="* Champs obligatoires", 
            text_color="gray"
        ).pack(anchor="w")
        
        # Boutons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill=ctk.X, pady=10, padx=20)
        
        # Fonction pour sauvegarder
        def save_client():
            # Récupérer les valeurs
            name = name_var.get().strip()
            company = company_var.get().strip()
            email = email_var.get().strip()
            phone = phone_var.get().strip()
            address = address_text.get("1.0", "end-1c").strip()
            
            # Validation
            if not name:
                DialogUtils.show_message(dialog, "Erreur", "Le nom est obligatoire", "error")
                return
            
            if not email:
                DialogUtils.show_message(dialog, "Erreur", "L'email est obligatoire", "error")
                return
            
            # Créer un dictionnaire avec les données
            new_client_data = {
                'name': name,
                'company': company,
                'email': email,
                'phone': phone,
                'address': address
            }
            
            # Mettre à jour ou créer le client
            if client_id:
                # C'est une modification
                new_client_data['id'] = client_id
                new_client_data['created_at'] = client_data.get('created_at', datetime.now().isoformat())
                new_client_data['updated_at'] = datetime.now().isoformat()
                
                # Mettre à jour le client via le modèle
                if self.model.update_client(client_id, new_client_data):
                    # Fermer la fenêtre
                    dialog.destroy()
                    
                    logger.info(f"Client modifié: {client_id} - {name}")
                    
                    # Afficher un message de succès
                    DialogUtils.show_message(self.view.parent, "Succès", "Client modifié avec succès", "success")
                else:
                    DialogUtils.show_message(dialog, "Erreur", "Client non trouvé ou erreur lors de la modification", "error")
            else:
                # C'est un nouveau client
                # Ajouter via le modèle
                new_id = self.model.add_client(new_client_data)
                
                if new_id:
                    # Fermer la fenêtre
                    dialog.destroy()
                    
                    logger.info(f"Nouveau client créé: {new_id} - {name}")
                    
                    # Afficher un message de succès
                    DialogUtils.show_message(self.view.parent, "Succès", "Client ajouté avec succès", "success")
                else:
                    DialogUtils.show_message(dialog, "Erreur", "Erreur lors de l'ajout du client", "error")
            
            # Mettre à jour la vue
            self.view.update_view()
        
        # Bouton Annuler
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Annuler",
            command=dialog.destroy,
            width=120
        )
        cancel_btn.pack(side=ctk.RIGHT, padx=10)
        
        # Bouton Enregistrer
        save_btn = ctk.CTkButton(
            button_frame,
            text="Enregistrer",
            command=save_client,
            width=120
        )
        save_btn.pack(side=ctk.RIGHT, padx=10)
        
        # Focus sur le premier champ
        name_entry.focus_set()
        
        logger.info(f"Formulaire client affiché pour {'nouveau client' if client_id is None else 'modification'}")
    
    def edit_client(self, client_id):
        """
        Édite un client existant
        
        Args:
            client_id: ID du client à modifier
        """
        # Vérifier si le client existe
        client = next((c for c in self.model.clients if c.get('id') == client_id), None)
        if not client:
            DialogUtils.show_message(self.view.parent, "Erreur", "Client non trouvé", "error")
            return
        
        # Appeler la méthode pour afficher le formulaire
        self.show_client_form(client_id)
        
        logger.info(f"Édition du client {client_id}")
    
    def confirm_delete_client(self, client_id):
        """
        Demande confirmation avant de supprimer un client
        
        Args:
            client_id: ID du client à supprimer
        """
        # Vérifier si le client existe
        client = next((c for c in self.model.clients if c.get('id') == client_id), None)
        if not client:
            DialogUtils.show_message(self.view.parent, "Erreur", "Client non trouvé", "error")
            return
        
        # Demander confirmation
        def delete_action():
            # Supprimer le client via le modèle
            if self.model.delete_client(client_id):
                # Mettre à jour la vue
                self.view.update_view()
                
                logger.info(f"Client supprimé: {client_id} - {client.get('name')}")
                
                # Afficher un message de succès
                DialogUtils.show_message(self.view.parent, "Succès", "Client supprimé avec succès", "success")
            else:
                DialogUtils.show_message(self.view.parent, "Erreur", "Erreur lors de la suppression du client", "error")
        
        DialogUtils.show_confirmation(
            self.view.parent,
            "Confirmer la suppression",
            f"Êtes-vous sûr de vouloir supprimer le client {client.get('name')} ?",
            on_yes=delete_action
        )
    
    def import_clients(self):
        """
        Importe des clients depuis un fichier CSV
        """
        # Log pour débogage
        logger.info("Méthode import_clients appelée")
        
        # Ouvrir une boîte de dialogue pour sélectionner le fichier
        file_path = filedialog.askopenfilename(
            title="Importer des clients",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            parent=self.view.parent
        )
        
        if not file_path:
            logger.info("Importation annulée : aucun fichier sélectionné")
            return
        
        try:
            # Lire le fichier CSV
            imported_clients = []
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'name' in row and 'email' in row:  # Vérifier les colonnes obligatoires
                        imported_clients.append({
                            'name': row['name'],
                            'company': row.get('company', ''),
                            'email': row['email'],
                            'phone': row.get('phone', ''),
                            'address': row.get('address', '')
                        })
            
            if not imported_clients:
                logger.warning(f"Aucun client valide trouvé dans le fichier {file_path}")
                DialogUtils.show_message(self.view.parent, "Avertissement", "Aucun client valide trouvé dans le fichier CSV", "warning")
                return
            
            # Demander confirmation
            def import_action():
                # Importation directe sans demander confirmation pour chaque client
                count = 0
                for client_data in imported_clients:
                    # Vérifier si le client existe déjà (par email)
                    existing_client = next((c for c in self.model.clients if c.get('email') == client_data['email']), None)
                    
                    if existing_client:
                        # Mettre à jour le client existant
                        client_data['id'] = existing_client['id']
                        client_data['created_at'] = existing_client['created_at']
                        client_data['updated_at'] = datetime.now().isoformat()
                        
                        # Remplacer dans la liste
                        index = self.model.clients.index(existing_client)
                        self.model.clients[index] = client_data
                    else:
                        # Nouveau client
                        new_id = f"client_{len(self.model.clients) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        client_data['id'] = new_id
                        client_data['created_at'] = datetime.now().isoformat()
                        client_data['updated_at'] = datetime.now().isoformat()
                        
                        # Ajouter à la liste
                        self.model.clients.append(client_data)
                    
                    count += 1
                
                # Sauvegarder les changements
                self.model.save_clients()
                
                # Mettre à jour la vue
                self.view.update_view()
                
                # Ajouter l'activité
                self.model.add_activity('client', f"Importation de {count} clients")
                
                logger.info(f"Importation de {count} clients depuis {file_path}")
                
                # Afficher un message de succès
                DialogUtils.show_message(self.view.parent, "Succès", f"{count} clients importés avec succès", "success")
            
            DialogUtils.show_confirmation(
                self.view.parent,
                "Confirmation d'importation",
                f"Voulez-vous importer {len(imported_clients)} clients ?",
                on_yes=import_action
            )
        
        except Exception as e:
            logger.error(f"Erreur lors de l'importation des clients: {e}")
            DialogUtils.show_message(self.view.parent, "Erreur", f"Erreur lors de l'importation des clients: {str(e)}", "error")
    
    def export_clients(self):
        """
        Exporte les clients vers un fichier CSV
        """
        # Log pour débogage
        logger.info("Méthode export_clients appelée")
        
        if not self.model.clients:
            logger.warning("Tentative d'exportation sans clients")
            DialogUtils.show_message(self.view.parent, "Avertissement", "Aucun client à exporter", "warning")
            return
        
        # Propose un nom de fichier par défaut basé sur la date
        default_filename = f"clients_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Ouvrir une boîte de dialogue pour sélectionner le fichier de destination
        file_path = filedialog.asksaveasfilename(
            title="Exporter les clients",
            defaultextension=".csv",
            initialfile=default_filename,
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            parent=self.view.parent
        )
        
        if not file_path:
            logger.info("Exportation annulée : aucun fichier sélectionné")
            return
        
        try:
            # S'assurer que l'extension est .csv
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'
            
            # Exporter vers CSV
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                # Définir les champs à exporter
                fieldnames = ['name', 'company', 'email', 'phone', 'address']
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                # Écrire les données
                for client in self.model.clients:
                    # Créer un dictionnaire avec seulement les champs à exporter
                    row = {field: client.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            # Ajouter l'activité
            self.model.add_activity('client', f"Exportation de {len(self.model.clients)} clients")
            
            logger.info(f"Exportation de {len(self.model.clients)} clients vers {file_path}")
            
            # Afficher un message de succès
            DialogUtils.show_message(self.view.parent, "Succès", f"{len(self.model.clients)} clients exportés avec succès", "success")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation des clients: {e}")
            DialogUtils.show_message(self.view.parent, "Erreur", f"Erreur lors de l'exportation des clients: {str(e)}", "error")