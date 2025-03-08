#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue de gestion des documents pour l'application Vynal Docs Automator
"""

import os
import logging
import customtkinter as ctk

logger = logging.getLogger("VynalDocsAutomator.DocumentView")

class DocumentView:
    """
    Vue de gestion des documents
    Permet de visualiser, créer et gérer des documents
    """
    
    def __init__(self, parent, app_model):
        """
        Initialise la vue de gestion des documents
        
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
        
        logger.info("DocumentView initialisée")
    
    def create_widgets(self):
        """
        Crée les widgets de la vue
        """
        # Barre d'outils
        self.toolbar = ctk.CTkFrame(self.frame)
        self.toolbar.pack(fill=ctk.X, pady=10)
        
        # Bouton Nouveau document
        self.new_doc_btn = ctk.CTkButton(
            self.toolbar,
            text="+ Nouveau document",
            command=self.new_document
        )
        self.new_doc_btn.pack(side=ctk.LEFT, padx=10)
        
        # Filtres
        self.filter_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.filter_frame.pack(side=ctk.RIGHT, padx=10)
        
        # Filtre client
        self.client_var = ctk.StringVar(value="")
        self.client_combobox = ctk.CTkComboBox(
            self.filter_frame,
            values=["Tous les clients"],
            variable=self.client_var,
            width=150,
            command=self.filter_documents
        )
        self.client_combobox.pack(side=ctk.LEFT, padx=5)
        
        # Filtre type
        self.type_var = ctk.StringVar(value="")
        self.type_combobox = ctk.CTkComboBox(
            self.filter_frame,
            values=["Tous les types"],
            variable=self.type_var,
            width=150,
            command=self.filter_documents
        )
        self.type_combobox.pack(side=ctk.LEFT, padx=5)
        
        # Recherche
        self.search_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.search_frame.pack(side=ctk.RIGHT, padx=10)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.filter_documents())
        
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Rechercher un document...",
            width=200,
            textvariable=self.search_var
        )
        self.search_entry.pack(side=ctk.LEFT)
        
        # Zone principale de contenu
        self.content_frame = ctk.CTkScrollableFrame(self.frame)
        self.content_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Message si aucun document
        self.no_documents_label = ctk.CTkLabel(
            self.content_frame,
            text="Aucun document disponible. Créez un nouveau document pour commencer.",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color="gray"
        )
        self.no_documents_label.pack(pady=20)
        
        # Grille de documents (contiendra les cartes de documents)
        self.documents_grid = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Configurer la grille pour avoir 3 colonnes
        for i in range(3):
            self.documents_grid.columnconfigure(i, weight=1)
    
    def update_view(self):
        """
        Met à jour la vue avec les données actuelles
        """
        # Récupérer tous les documents
        documents = self.model.documents
        
        # Mettre à jour les filtres clients
        clients = ["Tous les clients"]
        clients.extend([c.get("name", "") for c in self.model.clients])
        self.client_combobox.configure(values=clients)
        
        # Mettre à jour les filtres types
        doc_types = ["Tous les types"]
        unique_types = set([d.get("type", "") for d in documents])
        doc_types.extend(sorted(list(unique_types)))
        self.type_combobox.configure(values=doc_types)
        
        # Afficher ou masquer le message "Aucun document"
        if documents:
            self.no_documents_label.pack_forget()
            self.documents_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
            
            # Appliquer les filtres
            filtered_docs = self.apply_filters(documents)
            
            # Nettoyer la grille
            for widget in self.documents_grid.winfo_children():
                widget.destroy()
            
            # Remplir la grille avec les documents filtrés
            if filtered_docs:
                row, col = 0, 0
                for doc in filtered_docs:
                    self.create_document_card(doc, row, col)
                    col += 1
                    if col >= 3:  # 3 cartes par ligne
                        col = 0
                        row += 1
            else:
                # Aucun document après filtrage
                ctk.CTkLabel(
                    self.documents_grid,
                    text="Aucun document ne correspond aux critères de recherche.",
                    font=ctk.CTkFont(size=12),
                    fg_color="transparent",
                    text_color="gray"
                ).grid(row=0, column=0, columnspan=3, pady=20)
        else:
            self.documents_grid.pack_forget()
            self.no_documents_label.pack(pady=20)
        
        logger.info("DocumentView mise à jour")
    
    def create_document_card(self, document, row, col):
        """
        Crée une carte pour afficher un document
        
        Args:
            document: Données du document
            row: Ligne dans la grille
            col: Colonne dans la grille
        """
        # Cadre de la carte
        card = ctk.CTkFrame(self.documents_grid)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Icône selon le type
        doc_type = document.get("type", "")
        icon = "📄"  # Par défaut
        
        if doc_type == "contrat":
            icon = "📝"
        elif doc_type == "facture":
            icon = "💰"
        elif doc_type == "proposition":
            icon = "📊"
        elif doc_type == "rapport":
            icon = "📈"
        
        # En-tête avec icône et type
        header = ctk.CTkFrame(card, fg_color=("gray90", "gray20"), corner_radius=6)
        header.pack(fill=ctk.X, padx=5, pady=5)
        
        ctk.CTkLabel(
            header,
            text=f"{icon} {doc_type.capitalize() if doc_type else 'Document'}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side=ctk.LEFT, padx=10, pady=5)
        
        # Date
        doc_date = document.get("date", "")
        if doc_date:
            ctk.CTkLabel(
                header,
                text=doc_date,
                font=ctk.CTkFont(size=10),
                text_color="gray"
            ).pack(side=ctk.RIGHT, padx=10, pady=5)
        
        # Titre du document
        ctk.CTkLabel(
            card,
            text=document.get("title", "Sans titre"),
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=200
        ).pack(fill=ctk.X, padx=10, pady=5)
        
        # Client
        client_id = document.get("client_id", "")
        client_name = "Aucun client"
        
        if client_id:
            client = next((c for c in self.model.clients if c.get("id") == client_id), None)
            if client:
                client_name = client.get("name", "Inconnu")
        
        ctk.CTkLabel(
            card,
            text=f"Client: {client_name}",
            font=ctk.CTkFont(size=12),
            wraplength=200
        ).pack(fill=ctk.X, padx=10, pady=2)
        
        # Description
        description = document.get("description", "")
        if description:
            ctk.CTkLabel(
                card,
                text=description,
                font=ctk.CTkFont(size=12),
                wraplength=200,
                text_color="gray",
                justify="left"
            ).pack(fill=ctk.X, padx=10, pady=5)
        
        # Boutons d'action
        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.pack(fill=ctk.X, padx=10, pady=10)
        
        # Bouton Ouvrir
        ctk.CTkButton(
            actions_frame,
            text="Ouvrir",
            width=80,
            height=25,
            command=lambda doc_id=document.get("id"): self.open_document(doc_id)
        ).pack(side=ctk.LEFT, padx=2)
        
        # Bouton Télécharger
        ctk.CTkButton(
            actions_frame,
            text="Télécharger",
            width=80,
            height=25,
            command=lambda doc_id=document.get("id"): self.download_document(doc_id)
        ).pack(side=ctk.RIGHT, padx=2)
    
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
    
    def apply_filters(self, documents):
        """
        Applique les filtres aux documents
        
        Args:
            documents: Liste des documents à filtrer
            
        Returns:
            list: Documents filtrés
        """
        filtered = documents
        
        # Filtre par client
        client_filter = self.client_var.get()
        if client_filter and client_filter != "Tous les clients":
            # Trouver l'ID du client par son nom
            client = next((c for c in self.model.clients if c.get("name") == client_filter), None)
            if client:
                client_id = client.get("id")
                filtered = [d for d in filtered if d.get("client_id") == client_id]
        
        # Filtre par type
        type_filter = self.type_var.get()
        if type_filter and type_filter != "Tous les types":
            filtered = [d for d in filtered if d.get("type") == type_filter.lower()]
        
        # Filtre par recherche
        search_text = self.search_var.get().lower()
        if search_text:
            filtered = [d for d in filtered if 
                        search_text in d.get("title", "").lower() or 
                        search_text in d.get("description", "").lower()]
        
        return filtered
    
    def filter_documents(self, *args):
        """
        Filtre les documents selon les critères sélectionnés
        """
        self.update_view()
    
    def new_document(self):
        """
        Crée un nouveau document
        """
        # Cette méthode sera implémentée plus tard
        logger.info("Action: Nouveau document (non implémentée)")
    
    def open_document(self, document_id):
        """
        Ouvre un document pour le visualiser ou le modifier
        
        Args:
            document_id: ID du document à ouvrir
        """
        # Cette méthode sera implémentée plus tard
        logger.info(f"Action: Ouvrir le document {document_id} (non implémentée)")
    
    def download_document(self, document_id):
        """
        Télécharge un document
        
        Args:
            document_id: ID du document à télécharger
        """
        # Cette méthode sera implémentée plus tard
        logger.info(f"Action: Télécharger le document {document_id} (non implémentée)")