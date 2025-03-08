#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue de gestion des clients pour l'application Vynal Docs Automator
"""

import logging
import customtkinter as ctk

logger = logging.getLogger("VynalDocsAutomator.ClientView")

class ClientTable:
    """
    Composant de tableau pour afficher les clients
    """
    
    def __init__(self, parent, headers):
        """
        Initialise le tableau
        
        Args:
            parent: Widget parent
            headers: Liste des entêtes de colonnes
        """
        self.parent = parent
        self.headers = headers
        
        # Cadre principal du tableau
        self.frame = ctk.CTkFrame(parent)
        
        # Créer les entêtes
        self.header_frame = ctk.CTkFrame(self.frame, fg_color=("gray80", "gray30"))
        self.header_frame.pack(fill=ctk.X, padx=0, pady=0)
        
        # Configurer les colonnes
        for i, header in enumerate(headers):
            self.header_frame.columnconfigure(i, weight=(1 if i < len(headers) - 1 else 0))
        
        # Ajouter les entêtes
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                self.header_frame,
                text=header,
                font=ctk.CTkFont(weight="bold")
            ).grid(row=0, column=i, sticky="ew", padx=5, pady=5)
        
        # Cadre pour le contenu du tableau
        self.content_frame = ctk.CTkScrollableFrame(self.frame)
        self.content_frame.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        
        # Configurer les colonnes du contenu
        for i in range(len(headers)):
            self.content_frame.columnconfigure(i, weight=(1 if i < len(headers) - 1 else 0))
        
        # Liste des lignes
        self.rows = []
    
    def add_row(self, data):
        """
        Ajoute une ligne au tableau
        
        Args:
            data: Liste des données de la ligne
        
        Returns:
            list: Widgets de la ligne
        """
        row_widgets = []
        row_index = len(self.rows)
        
        # Cadre pour la ligne
        row_frame = ctk.CTkFrame(self.content_frame, fg_color=("gray95", "gray15") if row_index % 2 == 0 else ("white", "gray10"))
        row_frame.pack(fill=ctk.X, padx=0, pady=1)
        
        # Configurer les colonnes
        for i in range(len(self.headers)):
            row_frame.columnconfigure(i, weight=(1 if i < len(self.headers) - 1 else 0))
        
        # Ajouter les cellules
        for i, cell_data in enumerate(data):
            if isinstance(cell_data, ctk.CTkBaseClass):  # C'est un widget
                cell_data.grid(row=0, column=i, sticky="ew", padx=5, pady=3)
                row_widgets.append(cell_data)
            else:  # C'est du texte
                cell = ctk.CTkLabel(
                    row_frame,
                    text=str(cell_data),
                    anchor="w"
                )
                cell.grid(row=0, column=i, sticky="ew", padx=5, pady=3)
                row_widgets.append(cell)
        
        # Ajouter à la liste des lignes
        self.rows.append((row_frame, row_widgets))
        
        return row_widgets
    
    def clear(self):
        """
        Efface toutes les lignes du tableau
        """
        for row_frame, _ in self.rows:
            row_frame.destroy()
        
        self.rows = []

class ClientView:
    """
    Vue de gestion des clients
    Permet de visualiser, ajouter, modifier et supprimer des clients
    """
    
    def __init__(self, parent, app_model):
        """
        Initialise la vue de gestion des clients
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        
        # Cadre principal de la vue
        self.frame = ctk.CTkFrame(parent)
        
        # Variables pour le formulaire
        self.current_client_id = None
        self.client_data = {}
        
        # Créer les composants de l'interface
        self.create_widgets()
        
        logger.info("ClientView initialisée")
    
    def create_widgets(self):
        """
        Crée les widgets de la vue
        """
        # Barre d'outils
        self.toolbar = ctk.CTkFrame(self.frame)
        self.toolbar.pack(fill=ctk.X, pady=10)
        
        # Bouton Nouveau client
        self.new_client_btn = ctk.CTkButton(
            self.toolbar,
            text="+ Nouveau client",
            command=self.show_client_form
        )
        self.new_client_btn.pack(side=ctk.LEFT, padx=10)
        
        # Bouton Importer
        self.import_btn = ctk.CTkButton(
            self.toolbar,
            text="Importer",
            command=self.import_clients
        )
        self.import_btn.pack(side=ctk.LEFT, padx=10)
        
        # Bouton Exporter
        self.export_btn = ctk.CTkButton(
            self.toolbar,
            text="Exporter",
            command=self.export_clients
        )
        self.export_btn.pack(side=ctk.LEFT, padx=10)
        
        # Recherche
        self.search_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.search_frame.pack(side=ctk.RIGHT, padx=10)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.filter_clients())
        
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Rechercher un client...",
            width=200,
            textvariable=self.search_var
        )
        self.search_entry.pack(side=ctk.LEFT)
        
        # Cadre pour la liste des clients
        self.list_frame = ctk.CTkFrame(self.frame)
        self.list_frame.pack(fill=ctk.BOTH, expand=True, pady=10)
        
        # Tableau des clients
        self.clients_table = ClientTable(self.list_frame, ["Nom", "Entreprise", "Email", "Téléphone", "Actions"])
        
        # Message si aucun client
        self.no_clients_label = ctk.CTkLabel(
            self.list_frame,
            text="Aucun client disponible. Ajoutez des clients pour commencer.",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color="gray"
        )
        self.no_clients_label.pack(pady=20)
    
    def update_view(self):
        """
        Met à jour la vue avec les données actuelles
        """
        # Récupérer tous les clients
        clients = self.model.get_all_clients()
        
        # Afficher ou masquer le message "Aucun client"
        if clients:
            self.no_clients_label.pack_forget()
            self.clients_table.frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
            
            # Mettre à jour le tableau
            self.clients_table.clear()
            
            for client in clients:
                # Filtrer par recherche si nécessaire
                search_text = self.search_var.get().lower()
                if search_text:
                    if not (search_text in client.get("name", "").lower() or 
                            search_text in client.get("company", "").lower() or 
                            search_text in client.get("email", "").lower()):
                        continue
                
                # Ajouter les données du client
                row_data = [
                    client.get("name", ""),
                    client.get("company", ""),
                    client.get("email", ""),
                    client.get("phone", "")
                ]
                
                # Créer les boutons d'action
                actions_frame = ctk.CTkFrame(self.clients_table.frame, fg_color="transparent")
                
                # Bouton Éditer
                edit_btn = ctk.CTkButton(
                    actions_frame,
                    text="Éditer",
                    width=80,
                    height=25,
                    command=lambda cid=client.get("id"): self.edit_client(cid)
                )
                edit_btn.pack(side=ctk.LEFT, padx=2)
                
                # Bouton Supprimer
                delete_btn = ctk.CTkButton(
                    actions_frame,
                    text="Supprimer",
                    width=80,
                    height=25,
                    fg_color="red",
                    command=lambda cid=client.get("id"): self.confirm_delete_client(cid)
                )
                delete_btn.pack(side=ctk.LEFT, padx=2)
                
                # Ajouter la ligne au tableau
                self.clients_table.add_row(row_data + [actions_frame])
        else:
            self.clients_table.frame.pack_forget()
            self.no_clients_label.pack(pady=20)
        
        logger.info("ClientView mise à jour")
    
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
    
    def filter_clients(self):
        """
        Filtre les clients selon le texte de recherche
        """
        self.update_view()
    
    def show_client_form(self, client_id=None):
        """
        Affiche le formulaire pour ajouter ou modifier un client
        
        Args:
            client_id: ID du client à modifier, ou None pour un nouveau client
        """
        # Créer une fenêtre modale
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Nouveau client" if client_id is None else "Modifier le client")
        dialog.geometry("500x400")
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
        
        # Variables pour les champs du formulaire
        self.client_data = {}
        self.current_client_id = client_id
        
        # Si on modifie un client existant, charger ses données
        if client_id:
            client = self.model.get_client(client_id)
            if client:
                self.client_data = client.copy()
        
        # Formulaire
        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Champs du formulaire
        fields = [
            {"name": "name", "label": "Nom", "required": True},
            {"name": "company", "label": "Entreprise", "required": False},
            {"name": "email", "label": "Email", "required": True},
            {"name": "phone", "label": "Téléphone", "required": False},
            {"name": "address", "label": "Adresse", "required": False, "multiline": True}
        ]
        
        # Créer les champs
        field_widgets = {}
        row = 0
        
        for field in fields:
            # Étiquette
            label = ctk.CTkLabel(
                form_frame,
                text=field["label"] + (" *" if field["required"] else ""),
                anchor="w"
            )
            label.grid(row=row, column=0, sticky="w", padx=5, pady=5)
            
            # Valeur actuelle
            current_value = self.client_data.get(field["name"], "")
            
            # Champ de saisie
            if field.get("multiline", False):
                widget = ctk.CTkTextbox(
                    form_frame,
                    height=80,
                    wrap="word"
                )
                widget.insert("1.0", current_value)
            else:
                var = ctk.StringVar(value=current_value)
                widget = ctk.CTkEntry(
                    form_frame,
                    textvariable=var
                )
                field_widgets[field["name"]] = {"widget": widget, "var": var}
            
            widget.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
            
            if field.get("multiline", False):
                field_widgets[field["name"]] = {"widget": widget, "var": None}
            
            row += 1
        
        # Configurer la colonne des champs pour qu'elle s'étende
        form_frame.columnconfigure(1, weight=1)
        
        # Boutons
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, pady=10)
        
        # Bouton Annuler
        ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            command=dialog.destroy,
            width=100
        ).pack(side=ctk.RIGHT, padx=10)
        
        # Fonction pour valider et enregistrer
        def save_client():
            # Récupérer les valeurs
            client_data = {}
            
            for field in fields:
                field_name = field["name"]
                field_widget = field_widgets[field_name]
                
                if field.get("multiline", False):
                    value = field_widget["widget"].get("1.0", "end-1c").strip()
                else:
                    value = field_widget["var"].get().strip()
                
                # Vérifier les champs requis
                if field["required"] and not value:
                    self.show_error(dialog, f"Le champ {field['label']} est requis.")
                    return
                
                client_data[field_name] = value
            
            # Enregistrer le client
            if client_id:
                success = self.model.update_client(client_id, client_data)
            else:
                client_id = self.model.add_client(client_data)
                success = client_id is not None
            
            if success:
                dialog.destroy()
                self.update_view()
            else:
                self.show_error(dialog, "Erreur lors de l'enregistrement du client.")
        
        # Bouton Enregistrer
        ctk.CTkButton(
            buttons_frame,
            text="Enregistrer",
            command=save_client,
            width=100
        ).pack(side=ctk.RIGHT, padx=10)
    
    def edit_client(self, client_id):
        """
        Édite un client existant
        
        Args:
            client_id: ID du client à modifier
        """
        self.show_client_form(client_id)
    
    def confirm_delete_client(self, client_id):
        """
        Demande confirmation avant de supprimer un client
        
        Args:
            client_id: ID du client à supprimer
        """
        client = self.model.get_client(client_id)
        
        if not client:
            return
        
        # Créer une fenêtre modale de confirmation
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Confirmer la suppression")
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
            text="⚠️ Confirmer la suppression",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(
            msg_frame,
            text=f"Êtes-vous sûr de vouloir supprimer le client {client.get('name')} ?",
            wraplength=360
        ).pack(pady=10)
        
        # Boutons
        btn_frame = ctk.CTkFrame(msg_frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        # Fonction pour supprimer le client
        def delete_confirmed():
            success = self.model.delete_client(client_id)
            
            if success:
                dialog.destroy()
                self.update_view()
            else:
                self.show_error(dialog, "Erreur lors de la suppression du client.")
        
        # Bouton Annuler
        ctk.CTkButton(
            btn_frame,
            text="Annuler",
            width=100,
            command=dialog.destroy
        ).pack(side=ctk.LEFT, padx=10)
        
        # Bouton Supprimer
        ctk.CTkButton(
            btn_frame,
            text="Supprimer",
            width=100,
            fg_color="red",
            command=delete_confirmed
        ).pack(side=ctk.LEFT, padx=10)
    
    def import_clients(self):
        """
        Importe des clients depuis un fichier CSV ou Excel
        """
        # Cette méthode sera implémentée plus tard
        logger.info("Action: Importer des clients (non implémentée)")
    
    def export_clients(self):
        """
        Exporte les clients vers un fichier CSV ou Excel
        """
        # Cette méthode sera implémentée plus tard
        logger.info("Action: Exporter des clients (non implémentée)")
    
    def show_error(self, parent, message):
        """
        Affiche un message d'erreur
        
        Args:
            parent: Widget parent
            message: Message d'erreur
        """
        dialog = ctk.CTkToplevel(parent)
        dialog.title("Erreur")
        dialog.geometry("300x150")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (parent.winfo_rootx() + parent.winfo_width() // 2) - (width // 2)
        y = (parent.winfo_rooty() + parent.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Message
        msg_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        msg_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            msg_frame,
            text="❌ Erreur",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(
            msg_frame,
            text=message,
            wraplength=260
        ).pack(pady=10)
        
        # Bouton OK
        ctk.CTkButton(
            msg_frame,
            text="OK",
            width=100,
            command=dialog.destroy
        ).pack(pady=10)