#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue d'upload de documents pour l'application Vynal Docs Automator
Interface permettant d'uploader un document ou utiliser un modèle existant
"""

import logging
import customtkinter as ctk
from typing import Any, Dict, List, Optional, Callable
import os
import threading
from PIL import Image
import tkinter.filedialog as filedialog

logger = logging.getLogger("VynalDocsAutomator.DocumentUploadView")

class DocumentUploadView:
    """
    Vue d'upload de documents
    Interface utilisateur pour uploader un document ou utiliser un modèle existant
    """
    
    def __init__(self, parent: ctk.CTk, app_model: Any) -> None:
        """
        Initialise la vue d'upload de documents
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        
        # Initialiser les callbacks avec des fonctions par défaut
        self.on_upload_document = lambda file_path: logger.info(f"Upload document: {file_path}")
        self.on_use_template = lambda: logger.info("Utiliser un modèle existant")
        self.on_back = lambda: logger.info("Retour au tableau de bord")
        
        # État de la vue
        self.selected_file = None
        self.analysis_in_progress = False
        self.selected_client_id = None
        
        # Cadre principal qui occupe tout l'écran
        self.frame = ctk.CTkFrame(parent)
        
        # Conteneur principal pour gérer les différentes étapes
        self.main_container = ctk.CTkFrame(self.frame)
        self.main_container.pack(fill="both", expand=True)
        
        # Créer les différentes étapes (vues)
        self.upload_selection_frame = ctk.CTkFrame(self.main_container)
        self.analysis_frame = ctk.CTkFrame(self.main_container)
        
        # Barre supérieure avec titre et bouton de retour
        self.header_frame = ctk.CTkFrame(self.frame, height=50)
        self.header_frame.pack(fill="x", padx=10, pady=5)
        self.header_frame.pack_propagate(False)
        
        # Titre de la fenêtre
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Traitement de document",
            font=("", 20, "bold")
        )
        self.title_label.pack(side="left", padx=20)
        
        # Bouton de retour
        self.back_btn = ctk.CTkButton(
            self.header_frame,
            text="⬅ Retour",
            width=100,
            height=30,
            command=self._on_back_click,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30")
        )
        self.back_btn.pack(side="right", padx=5)
        
        # Initialiser les widgets des différentes étapes
        self.create_upload_selection_widgets()
        self.create_analysis_widgets()
        
        # Afficher l'étape initiale (upload/sélection)
        self.show_upload_selection()
        
        logger.info("Vue d'upload de documents initialisée")
    
    def create_upload_selection_widgets(self) -> None:
        """
        Crée les widgets de l'interface de sélection/upload
        """
        # Zone principale avec défilement
        self.main_frame = ctk.CTkFrame(self.upload_selection_frame, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Création des deux grandes zones pour upload ou utiliser un modèle
        self.options_frame = ctk.CTkFrame(self.main_frame)
        self.options_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configuration de la grille pour les deux options
        self.options_frame.columnconfigure(0, weight=1)
        self.options_frame.columnconfigure(1, weight=1)
        self.options_frame.rowconfigure(0, weight=1)
        
        # --- Option 1: Upload d'un document ---
        self.upload_frame = ctk.CTkFrame(self.options_frame, corner_radius=10)
        self.upload_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Titre de la section
        ctk.CTkLabel(
            self.upload_frame,
            text="Uploader un document",
            font=("", 18, "bold")
        ).pack(pady=(20, 10))
        
        # Description
        ctk.CTkLabel(
            self.upload_frame,
            text="Uploadez un document pour analyse et traitement",
            font=("", 12),
            text_color=("gray40", "gray60")
        ).pack(pady=(0, 20))
        
        # Icône d'upload
        # Créer un canvas pour l'icône d'upload
        upload_icon_frame = ctk.CTkFrame(self.upload_frame, fg_color="transparent")
        upload_icon_frame.pack(pady=20)
        
        # Charger l'icône si disponible, sinon utiliser un texte
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons", "upload.png")
            if os.path.exists(icon_path):
                upload_icon = ctk.CTkImage(
                    light_image=Image.open(icon_path),
                    dark_image=Image.open(icon_path),
                    size=(64, 64)
                )
                ctk.CTkLabel(upload_icon_frame, image=upload_icon, text="").pack()
            else:
                ctk.CTkLabel(upload_icon_frame, text="📤", font=("", 36)).pack()
        except Exception as e:
            logger.warning(f"Erreur lors du chargement de l'icône d'upload: {e}")
            ctk.CTkLabel(upload_icon_frame, text="📤", font=("", 36)).pack()
        
        # Zone d'affichage du fichier sélectionné
        self.file_label = ctk.CTkLabel(
            self.upload_frame,
            text="Aucun fichier sélectionné",
            font=("", 12),
            text_color=("gray40", "gray60")
        )
        self.file_label.pack(pady=10)
        
        # Bouton pour sélectionner un fichier
        self.select_file_btn = ctk.CTkButton(
            self.upload_frame,
            text="Sélectionner un fichier",
            command=self._select_file
        )
        self.select_file_btn.pack(pady=50)
        
        # --- Option 2: Utiliser un modèle existant ---
        self.template_frame = ctk.CTkFrame(self.options_frame, corner_radius=10)
        self.template_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Titre de la section
        ctk.CTkLabel(
            self.template_frame,
            text="Utiliser un modèle existant",
            font=("", 18, "bold")
        ).pack(pady=(20, 10))
        
        # Description
        ctk.CTkLabel(
            self.template_frame,
            text="Créez un document à partir d'un modèle existant",
            font=("", 12),
            text_color=("gray40", "gray60")
        ).pack(pady=(0, 20))
        
        # Icône de modèle
        template_icon_frame = ctk.CTkFrame(self.template_frame, fg_color="transparent")
        template_icon_frame.pack(pady=20)
        
        # Charger l'icône si disponible, sinon utiliser un texte
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons", "template.png")
            if os.path.exists(icon_path):
                template_icon = ctk.CTkImage(
                    light_image=Image.open(icon_path),
                    dark_image=Image.open(icon_path),
                    size=(64, 64)
                )
                ctk.CTkLabel(template_icon_frame, image=template_icon, text="").pack()
            else:
                ctk.CTkLabel(template_icon_frame, text="📋", font=("", 36)).pack()
        except Exception as e:
            logger.warning(f"Erreur lors du chargement de l'icône de modèle: {e}")
            ctk.CTkLabel(template_icon_frame, text="📋", font=("", 36)).pack()
        
        # Zone d'informations sur les modèles
        ctk.CTkLabel(
            self.template_frame,
            text="Accédez à vos modèles prédéfinis",
            font=("", 12),
            text_color=("gray40", "gray60")
        ).pack(pady=10)
        
        # Bouton pour utiliser un modèle
        self.use_template_btn = ctk.CTkButton(
            self.template_frame,
            text="Sélectionner un modèle",
            command=self._use_template
        )
        self.use_template_btn.pack(pady=50)
    
    def create_analysis_widgets(self) -> None:
        """
        Crée les widgets de l'interface d'analyse
        """
        # Conteneur principal d'analyse
        self.analysis_container = ctk.CTkFrame(self.analysis_frame, fg_color="transparent")
        self.analysis_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Section supérieure pour l'analyse
        self.analysis_status_frame = ctk.CTkFrame(self.analysis_container)
        self.analysis_status_frame.pack(fill="x", padx=10, pady=10)
        
        # Titre de la section
        ctk.CTkLabel(
            self.analysis_status_frame,
            text="Analyse du document en cours",
            font=("", 18, "bold")
        ).pack(pady=10)
        
        # Nom du fichier analysé
        self.analysis_file_label = ctk.CTkLabel(
            self.analysis_status_frame,
            text="",
            font=("", 12)
        )
        self.analysis_file_label.pack(pady=5)
        
        # Cadre pour le spinner
        self.spinner_frame = ctk.CTkFrame(self.analysis_status_frame, fg_color="transparent")
        self.spinner_frame.pack(pady=20)
        
        # Barre de progression indéterminée
        self.progress_bar = ctk.CTkProgressBar(
            self.spinner_frame,
            width=300,
            mode="indeterminate"
        )
        self.progress_bar.pack(pady=10)
        
        # Texte d'état
        self.status_label = ctk.CTkLabel(
            self.spinner_frame,
            text="Extraction des informations du document...",
            font=("", 12)
        )
        self.status_label.pack(pady=5)
        
        # Séparateur
        separator = ctk.CTkFrame(self.analysis_container, height=2, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", padx=10, pady=20)
        
        # Section de sélection du client
        self.client_section_frame = ctk.CTkFrame(self.analysis_container)
        self.client_section_frame.pack(fill="x", padx=10, pady=10)
        
        # Titre de la section
        ctk.CTkLabel(
            self.client_section_frame,
            text="Sélection du client",
            font=("", 18, "bold")
        ).pack(pady=10, anchor="w")
        
        # Description
        ctk.CTkLabel(
            self.client_section_frame,
            text="Sélectionnez un client pour ce document ou créez-en un nouveau",
            font=("", 12),
            text_color=("gray40", "gray60")
        ).pack(pady=5, anchor="w")
        
        # Zone de recherche
        self.search_frame = ctk.CTkFrame(self.client_section_frame, fg_color="transparent")
        self.search_frame.pack(fill="x", pady=10)
        
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Rechercher un client...",
            width=400
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        
        self.search_btn = ctk.CTkButton(
            self.search_frame,
            text="Rechercher",
            width=100,
            command=self._search_client
        )
        self.search_btn.pack(side="left")
        
        self.new_client_btn = ctk.CTkButton(
            self.search_frame,
            text="Nouveau client",
            width=120,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=self._create_new_client
        )
        self.new_client_btn.pack(side="right")
        
        # Liste des clients
        self.clients_container = ctk.CTkScrollableFrame(
            self.client_section_frame,
            height=300
        )
        self.clients_container.pack(fill="x", pady=10)
        
        # Label pour aucun client
        self.no_clients_label = ctk.CTkLabel(
            self.clients_container,
            text="Aucun client trouvé",
            font=("", 12),
            text_color=("gray40", "gray60")
        )
        self.no_clients_label.pack(pady=20)
        
        # Conteneur pour les cartes de clients
        self.client_cards_frame = ctk.CTkFrame(self.clients_container, fg_color="transparent")
        
        # Bouton pour continuer
        self.continue_frame = ctk.CTkFrame(self.analysis_container, fg_color="transparent")
        self.continue_frame.pack(fill="x", pady=20)
        
        self.continue_btn = ctk.CTkButton(
            self.continue_frame,
            text="Continuer",
            width=200,
            height=40,
            fg_color="#3498db",
            hover_color="#2980b9",
            state="disabled",
            command=self._continue_to_next_step
        )
        self.continue_btn.pack(pady=10)
    
    def _select_file(self) -> None:
        """
        Fonction callback pour sélectionner un fichier à uploader
        """
        file_path = filedialog.askopenfilename(
            title="Sélectionner un document",
            filetypes=[
                ("Documents", "*.docx *.doc *.pdf *.txt"),
                ("Documents Word", "*.docx *.doc"),
                ("PDF", "*.pdf"),
                ("Texte", "*.txt"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if file_path:
            self.selected_file = file_path
            # Afficher uniquement le nom du fichier, pas le chemin complet
            file_name = os.path.basename(file_path)
            self.file_label.configure(text=f"Fichier sélectionné: {file_name}")
            
            # Passer automatiquement à la vue d'analyse
            self._start_analysis()
    
    def _start_analysis(self) -> None:
        """
        Démarre l'analyse du document et passe à la vue d'analyse
        """
        if not self.selected_file:
            return
            
        # Configurer la vue d'analyse
        file_name = os.path.basename(self.selected_file)
        self.analysis_file_label.configure(text=f"Fichier: {file_name}")
        
        # Passer à la vue d'analyse
        self.show_analysis()
        
        # Démarrer l'animation du spinner
        self.progress_bar.start()
        
        # Définir l'état d'analyse en cours
        self.analysis_in_progress = True
        
        # Désactiver les contrôles de sélection client pendant l'analyse
        self._set_client_controls_state("disabled")
        
        # Lancer l'analyse en arrière-plan
        threading.Thread(target=self._process_analysis, daemon=True).start()
    
    def _process_analysis(self) -> None:
        """
        Processus d'analyse du document en arrière-plan
        """
        try:
            # Appeler la fonction de traitement du document
            if callable(self.on_upload_document):
                self.on_upload_document(self.selected_file)
                
            # Simuler un délai pour le chargement des clients
            import time
            time.sleep(1)
            
            # Charger les clients
            self._load_clients()
                
            # Mettre à jour l'état
            self.status_label.configure(text="Analyse terminée avec succès!")
            
            # Arrêter l'animation du spinner
            self.progress_bar.stop()
            
            # Mettre à jour l'état d'analyse
            self.analysis_in_progress = False
            
            # Activer les contrôles de sélection client
            self._set_client_controls_state("normal")
            
            # Le bouton Continuer reste désactivé jusqu'à ce qu'un client soit sélectionné
            self.continue_btn.configure(state="disabled")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}")
            self.status_label.configure(text=f"Erreur: {str(e)}")
            self.progress_bar.stop()
            self.analysis_in_progress = False
            self._set_client_controls_state("normal")
    
    def _set_client_controls_state(self, state: str) -> None:
        """
        Définit l'état des contrôles de sélection client
        
        Args:
            state: État des contrôles ('normal' ou 'disabled')
        """
        self.search_entry.configure(state=state)
        self.search_btn.configure(state=state)
        self.new_client_btn.configure(state=state)
    
    def _load_clients(self) -> None:
        """
        Charge la liste des clients
        """
        # Effacer les widgets existants
        for widget in self.clients_container.winfo_children():
            widget.destroy()
        
        # Récupérer les clients
        try:
            clients = self.model.clients.get_all_clients()
            
            if not clients:
                self.no_clients_label = ctk.CTkLabel(
                    self.clients_container,
                    text="Aucun client trouvé",
                    font=("", 12),
                    text_color=("gray40", "gray60")
                )
                self.no_clients_label.pack(pady=20)
                return
                
            # Créer une grille pour les cartes
            self.client_cards_frame = ctk.CTkFrame(self.clients_container, fg_color="transparent")
            self.client_cards_frame.pack(fill="both", expand=True)
            
            # Configurer une grille avec 3 colonnes
            for i in range(3):
                self.client_cards_frame.columnconfigure(i, weight=1)
            
            # Ajouter chaque client
            for i, client in enumerate(clients):
                row = i // 3
                col = i % 3
                self._create_client_card(client, row, col)
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement des clients: {e}")
            self.no_clients_label = ctk.CTkLabel(
                self.clients_container,
                text=f"Erreur lors du chargement des clients: {e}",
                font=("", 12),
                text_color=("gray40", "gray60")
            )
            self.no_clients_label.pack(pady=20)
    
    def _create_client_card(self, client: Dict, row: int, col: int) -> None:
        """
        Crée une carte pour un client
        
        Args:
            client: Données du client
            row: Ligne dans la grille
            col: Colonne dans la grille
        """
        # Cadre pour la carte
        card = ctk.CTkFrame(self.client_cards_frame, corner_radius=10)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # Nom du client
        name = client.get("name", "Sans nom")
        email = client.get("email", "")
        client_id = client.get("id", "")
        
        # Titre de la carte
        name_label = ctk.CTkLabel(
            card,
            text=name,
            font=("", 14, "bold")
        )
        name_label.pack(pady=(10, 5), padx=10)
        
        # Email
        if email:
            email_label = ctk.CTkLabel(
                card,
                text=email,
                font=("", 12),
                text_color=("gray40", "gray60")
            )
            email_label.pack(pady=2, padx=10)
        
        # Bouton de sélection
        select_btn = ctk.CTkButton(
            card,
            text="Sélectionner",
            width=100,
            command=lambda c_id=client_id, c_name=name: self._select_client(c_id, c_name)
        )
        select_btn.pack(pady=10)
        
        # Stocker la référence à la carte et au client
        card.client_id = client_id
    
    def _select_client(self, client_id: str, client_name: str) -> None:
        """
        Sélectionne un client
        
        Args:
            client_id: ID du client
            client_name: Nom du client
        """
        self.selected_client_id = client_id
        
        # Mettre à jour l'interface pour montrer le client sélectionné
        for widget in self.client_cards_frame.winfo_children():
            if hasattr(widget, 'client_id'):
                if widget.client_id == client_id:
                    widget.configure(fg_color=("gray80", "gray20"))
                else:
                    widget.configure(fg_color=("gray90", "gray10"))
        
        # Activer le bouton Continuer
        self.continue_btn.configure(state="normal")
        self.status_label.configure(text=f"Client sélectionné: {client_name}")
    
    def _search_client(self) -> None:
        """
        Recherche un client
        """
        search_term = self.search_entry.get().strip()
        if not search_term:
            self._load_clients()
            return
            
        # Effacer les widgets existants
        for widget in self.clients_container.winfo_children():
            widget.destroy()
            
        # Rechercher les clients
        try:
            clients = self.model.clients.search_clients(search_term)
            
            if not clients:
                self.no_clients_label = ctk.CTkLabel(
                    self.clients_container,
                    text=f"Aucun client trouvé pour '{search_term}'",
                    font=("", 12),
                    text_color=("gray40", "gray60")
                )
                self.no_clients_label.pack(pady=20)
                return
                
            # Créer une grille pour les cartes
            self.client_cards_frame = ctk.CTkFrame(self.clients_container, fg_color="transparent")
            self.client_cards_frame.pack(fill="both", expand=True)
            
            # Configurer une grille avec 3 colonnes
            for i in range(3):
                self.client_cards_frame.columnconfigure(i, weight=1)
            
            # Ajouter chaque client
            for i, client in enumerate(clients):
                row = i // 3
                col = i % 3
                self._create_client_card(client, row, col)
                
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des clients: {e}")
            self.no_clients_label = ctk.CTkLabel(
                self.clients_container,
                text=f"Erreur lors de la recherche des clients: {e}",
                font=("", 12),
                text_color=("gray40", "gray60")
            )
            self.no_clients_label.pack(pady=20)
    
    def _create_new_client(self) -> None:
        """
        Crée un nouveau client
        """
        # Cette fonction sera configurée par le contrôleur
        pass
    
    def _continue_to_next_step(self) -> None:
        """
        Passe à l'étape suivante après la sélection du client
        """
        if self.selected_client_id and not self.analysis_in_progress:
            # Cette fonction sera implémentée par le contrôleur
            pass
    
    def _use_template(self) -> None:
        """
        Fonction callback pour utiliser un modèle existant
        """
        if callable(self.on_use_template):
            self.on_use_template()
    
    def _on_back_click(self) -> None:
        """
        Fonction callback pour le bouton retour
        """
        if callable(self.on_back):
            self.on_back()
    
    def show_upload_selection(self) -> None:
        """
        Affiche la vue de sélection d'upload
        """
        # Cacher toutes les vues
        self.analysis_frame.pack_forget()
        
        # Afficher la vue de sélection d'upload
        self.upload_selection_frame.pack(fill="both", expand=True)
    
    def show_analysis(self) -> None:
        """
        Affiche la vue d'analyse
        """
        # Cacher toutes les vues
        self.upload_selection_frame.pack_forget()
        
        # Afficher la vue d'analyse
        self.analysis_frame.pack(fill="both", expand=True)
    
    def show(self) -> None:
        """
        Affiche la vue
        """
        # S'assurer que les vues internes sont correctement affichées/cachées
        self.show_upload_selection()
        
        # Réinitialiser l'état
        self.selected_file = None
        self.selected_client_id = None
        self.analysis_in_progress = False
        
        # Afficher la vue complète
        self.frame.pack(fill="both", expand=True)
    
    def hide(self) -> None:
        """
        Cache la vue
        """
        # Si une analyse est en cours, l'arrêter
        if self.analysis_in_progress:
            self.analysis_in_progress = False
        
        # Cacher la vue
        self.frame.pack_forget() 