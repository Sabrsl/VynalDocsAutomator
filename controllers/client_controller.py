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
from tkinter import messagebox, filedialog, simpledialog
from datetime import datetime

logger = logging.getLogger("VynalDocsAutomator.ClientController")

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
        self.view.import_clients = self.import_clients
        self.view.export_clients = self.export_clients
        
        logger.info("Événements de ClientView connectés")
    
    def show_client_form(self, client_id=None):
        """
        Affiche le formulaire pour ajouter ou modifier un client
        
        Args:
            client_id: ID du client à modifier, ou None pour un nouveau client
        """
        # Créer une fenêtre de dialogue
        dialog = tk.Toplevel(self.view.parent)
        dialog.title("Nouveau client" if client_id is None else "Modifier le client")
        dialog.geometry("400x350")
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
        
        # Créer un cadre pour le formulaire
        form_frame = tk.Frame(dialog, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Champs du formulaire
        # Nom
        tk.Label(form_frame, text="Nom*:").grid(row=0, column=0, sticky="w", pady=5)
        name_var = tk.StringVar(value=client_data.get('name', ''))
        name_entry = tk.Entry(form_frame, textvariable=name_var, width=30)
        name_entry.grid(row=0, column=1, sticky="w", pady=5)
        
        # Entreprise
        tk.Label(form_frame, text="Entreprise:").grid(row=1, column=0, sticky="w", pady=5)
        company_var = tk.StringVar(value=client_data.get('company', ''))
        company_entry = tk.Entry(form_frame, textvariable=company_var, width=30)
        company_entry.grid(row=1, column=1, sticky="w", pady=5)
        
        # Email
        tk.Label(form_frame, text="Email*:").grid(row=2, column=0, sticky="w", pady=5)
        email_var = tk.StringVar(value=client_data.get('email', ''))
        email_entry = tk.Entry(form_frame, textvariable=email_var, width=30)
        email_entry.grid(row=2, column=1, sticky="w", pady=5)
        
        # Téléphone
        tk.Label(form_frame, text="Téléphone:").grid(row=3, column=0, sticky="w", pady=5)
        phone_var = tk.StringVar(value=client_data.get('phone', ''))
        phone_entry = tk.Entry(form_frame, textvariable=phone_var, width=30)
        phone_entry.grid(row=3, column=1, sticky="w", pady=5)
        
        # Adresse
        tk.Label(form_frame, text="Adresse:").grid(row=4, column=0, sticky="w", pady=5)
        address_text = tk.Text(form_frame, width=30, height=4)
        address_text.grid(row=4, column=1, sticky="w", pady=5)
        address_text.insert("1.0", client_data.get('address', ''))
        
        # Note obligatoire
        tk.Label(form_frame, text="* Champs obligatoires", fg="gray").grid(row=5, column=0, columnspan=2, sticky="w", pady=10)
        
        # Boutons
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
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
                messagebox.showerror("Erreur", "Le nom est obligatoire", parent=dialog)
                return
            
            if not email:
                messagebox.showerror("Erreur", "L'email est obligatoire", parent=dialog)
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
                
                # Trouver l'index du client dans la liste
                client_index = next((i for i, c in enumerate(self.model.clients) if c.get('id') == client_id), None)
                if client_index is not None:
                    # Remplacer le client dans la liste
                    self.model.clients[client_index] = new_client_data
                    
                    # Sauvegarder les changements
                    self.model.save_clients()
                    
                    # Mettre à jour la vue
                    self.view.update_view()
                    
                    # Ajouter l'activité
                    self.model.add_activity('client', f"Client modifié: {name}")
                    
                    # Fermer la fenêtre
                    dialog.destroy()
                    
                    logger.info(f"Client modifié: {client_id} - {name}")
                    
                    # Afficher un message de succès
                    messagebox.showinfo("Succès", "Client modifié avec succès")
                else:
                    messagebox.showerror("Erreur", "Client non trouvé", parent=dialog)
            else:
                # C'est un nouveau client
                # Générer un ID unique
                new_id = f"client_{len(self.model.clients) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                new_client_data['id'] = new_id
                new_client_data['created_at'] = datetime.now().isoformat()
                new_client_data['updated_at'] = datetime.now().isoformat()
                
                # Ajouter à la liste
                self.model.clients.append(new_client_data)
                
                # Sauvegarder les changements
                self.model.save_clients()
                
                # Mettre à jour la vue
                self.view.update_view()
                
                # Ajouter l'activité
                self.model.add_activity('client', f"Nouveau client: {name}")
                
                # Fermer la fenêtre
                dialog.destroy()
                
                logger.info(f"Nouveau client créé: {new_id} - {name}")
                
                # Afficher un message de succès
                messagebox.showinfo("Succès", "Client ajouté avec succès")
        
        # Fonction pour annuler
        def cancel():
            dialog.destroy()
        
        # Bouton Annuler
        cancel_btn = tk.Button(button_frame, text="Annuler", command=cancel, width=10)
        cancel_btn.pack(side=tk.RIGHT, padx=10)
        
        # Bouton Enregistrer
        save_btn = tk.Button(button_frame, text="Enregistrer", command=save_client, width=10)
        save_btn.pack(side=tk.RIGHT, padx=10)
        
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
            messagebox.showerror("Erreur", "Client non trouvé")
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
            messagebox.showerror("Erreur", "Client non trouvé")
            return
        
        # Demander confirmation
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer le client {client.get('name')} ?"):
            # Supprimer le client
            self.model.clients = [c for c in self.model.clients if c.get('id') != client_id]
            
            # Sauvegarder les changements
            self.model.save_clients()
            
            # Mettre à jour la vue
            self.view.update_view()
            
            # Ajouter l'activité
            self.model.add_activity('client', f"Client supprimé: {client.get('name')}")
            
            logger.info(f"Client supprimé: {client_id} - {client.get('name')}")
            
            # Afficher un message de succès
            messagebox.showinfo("Succès", "Client supprimé avec succès")
        else:
            logger.info(f"Suppression du client annulée: {client_id}")
    
    def import_clients(self):
        """
        Importe des clients depuis un fichier CSV
        """
        # Ouvrir une boîte de dialogue pour sélectionner le fichier
        file_path = filedialog.askopenfilename(
            title="Importer des clients",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            parent=self.view.parent
        )
        
        if not file_path:
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
                messagebox.showwarning("Avertissement", "Aucun client valide trouvé dans le fichier CSV")
                return
            
            # Demander confirmation
            if messagebox.askyesno("Confirmation", f"Voulez-vous importer {len(imported_clients)} clients ?"):
                # Importation
                count = 0
                for client_data in imported_clients:
                    # Vérifier si le client existe déjà (par email)
                    existing_client = next((c for c in self.model.clients if c.get('email') == client_data['email']), None)
                    
                    if existing_client:
                        # Demander s'il faut mettre à jour
                        if messagebox.askyesno("Client existant", 
                                           f"Le client {client_data['name']} ({client_data['email']}) existe déjà. Voulez-vous le mettre à jour ?",
                                           parent=self.view.parent):
                            # Mettre à jour le client existant
                            client_data['id'] = existing_client['id']
                            client_data['created_at'] = existing_client['created_at']
                            client_data['updated_at'] = datetime.now().isoformat()
                            
                            # Remplacer dans la liste
                            index = self.model.clients.index(existing_client)
                            self.model.clients[index] = client_data
                            count += 1
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
                messagebox.showinfo("Succès", f"{count} clients importés avec succès")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'importation des clients: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'importation des clients: {str(e)}")
    
    def export_clients(self):
        """
        Exporte les clients vers un fichier CSV
        """
        if not self.model.clients:
            messagebox.showwarning("Avertissement", "Aucun client à exporter")
            return
        
        # Ouvrir une boîte de dialogue pour sélectionner le fichier de destination
        file_path = filedialog.asksaveasfilename(
            title="Exporter les clients",
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            parent=self.view.parent
        )
        
        if not file_path:
            return
        
        try:
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
            messagebox.showinfo("Succès", f"{len(self.model.clients)} clients exportés avec succès")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation des clients: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'exportation des clients: {str(e)}")