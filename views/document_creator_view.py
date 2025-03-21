#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue de création de documents pour l'application Vynal Docs Automator
Interface moderne et fluide pour la création de documents
"""

import logging
import customtkinter as ctk
from typing import Any, Dict, List, Optional
import json
import os
import threading
import shutil
import tkinter.filedialog as filedialog
from ai.document_processor import AIDocumentProcessor
from PIL import Image
import datetime
import re

logger = logging.getLogger("VynalDocsAutomator.DocumentCreatorView")

class DocumentCreatorView:
    """
    Vue de création de documents
    Interface utilisateur pour créer des documents avec assistance IA
    """
    
    def __init__(self, parent: ctk.CTk, app_model: Any) -> None:
        """
        Initialise la vue de création de documents
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        self.sidebar = None  # Pour stocker la référence à la barre latérale
        
        # État du processus de création
        self.current_step = 0
        self.selected_template = None
        self.client_info = {}
        self.document_data = {}
        self.missing_variables = {}
        self.preview_content = ""
        self.client_selected = False
        
        # Cadre principal qui occupe tout l'écran
        self.frame = ctk.CTkFrame(parent)
        self.frame.pack(fill="both", expand=True)
        
        # Barre supérieure avec titre et bouton de fermeture
        self.header_frame = ctk.CTkFrame(self.frame, height=50)
        self.header_frame.pack(fill="x", padx=10, pady=5)
        self.header_frame.pack_propagate(False)
        
        # Titre de la fenêtre
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Création de document",
            font=("", 20, "bold")
        )
        self.title_label.pack(side="left", padx=20)
        
        # Bouton de fermeture
        self.close_btn = ctk.CTkButton(
            self.header_frame,
            text="✕",
            width=30,
            height=30,
            command=self.on_close_button,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30")
        )
        self.close_btn.pack(side="right", padx=5)
        
        # Zone principale avec défilement
        self.scroll_container = ctk.CTkScrollableFrame(self.frame)
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Zone de contenu principal
        self.main_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)
        
        # Créer l'interface
        self.create_widgets()
        
        logger.info("Vue de création de documents initialisée")
        
    def create_widgets(self) -> None:
        """
        Crée les widgets de l'interface
        """
        # Barre de progression
        self.progress_frame = ctk.CTkFrame(self.main_frame)
        self.progress_frame.pack(fill="x", pady=(0, 20))
        
        # Étapes du processus
        self.steps = [
            "Type de création",
            "Sélection du modèle",
            "Informations client",
            "Validation",
            "Personnalisation",
            "Finalisation"
        ]
        
        # Créer les indicateurs d'étape
        self.step_indicators = []
        for i, step in enumerate(self.steps):
            step_frame = ctk.CTkFrame(self.progress_frame)
            step_frame.grid(row=0, column=i*2, padx=5, pady=5)
            
            # Numéro de l'étape
            number = ctk.CTkLabel(
                step_frame,
                text=str(i + 1),
                width=30,
                height=30,
                corner_radius=15,
                fg_color=("gray75", "gray25"),
                text_color="white"
            )
            number.pack(pady=5)
            
            # Nom de l'étape
            label = ctk.CTkLabel(step_frame, text=step, font=("", 12))
            label.pack(pady=2)
            
            self.step_indicators.append({"number": number, "label": label})
            
            # Ajouter un séparateur sauf pour la dernière étape
            if i < len(self.steps) - 1:
                separator = ctk.CTkFrame(
                    self.progress_frame,
                    width=50,
                    height=2,
                    fg_color=("gray75", "gray25")
                )
                separator.grid(row=0, column=i*2 + 1, sticky="ew", pady=20)
        
        # Zone de contenu principal
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, pady=10)
        
        # Zone de navigation
        self.nav_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.nav_frame.pack(fill="x", pady=10)
        
        # Afficher la première étape
        self.show_step(0)
        
    def show_step(self, step: int) -> None:
        """
        Affiche l'étape spécifiée du processus
        
        Args:
            step: Numéro de l'étape à afficher
        """
        # S'assurer que l'indice est valide
        if step < 0 or step >= len(self.steps):
            logger.error(f"Indice d'étape invalide: {step}")
            return
        
        # Initialiser selected_template comme un dictionnaire vide s'il n'existe pas
        # pour éviter les erreurs AttributeError: 'NoneType' object has no attribute 'get'
        if not hasattr(self, 'selected_template') or self.selected_template is None:
            self.selected_template = {}
            
        # Mettre à jour les indicateurs d'étape
        for i, indicator in enumerate(self.step_indicators):
            if i < step:
                # Étape terminée
                indicator["number"].configure(
                    fg_color="green",
                    text="✓",
                    text_color="white"
                )
            elif i == step:
                # Étape en cours
                indicator["number"].configure(
                    fg_color="#1f538d",
                    text=str(i + 1),
                    text_color="white"
                )
            else:
                # Étape à venir
                indicator["number"].configure(
                    fg_color=("gray75", "gray25"),
                    text=str(i + 1),
                    text_color=("gray20", "gray80")
                )
                
        # Mettre à jour le titre de la fenêtre
        self.title_label.configure(text=f"Création de document - {self.steps[step]}")
        
        # Nettoyer la zone de contenu
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Afficher le contenu de l'étape
        if step == 0:
            self.show_initial_options()
        elif step == 1:
            self.show_document_types()
        elif step == 2:
            self.show_client_form()
        elif step == 3:
            self.show_validation()
        elif step == 4:
            self.show_customization()
        elif step == 5:
            self.show_finalization()
            
        self.current_step = step
        
        # Mettre à jour les boutons de navigation
        self.update_navigation()
        
        # Faire défiler vers le haut du contenu - méthode corrigée
        try:
            # Utiliser _parent_canvas qui est l'attribut interne de CTkScrollableFrame
            if hasattr(self.scroll_container, '_parent_canvas'):
                self.scroll_container._parent_canvas.yview_moveto(0)
        except Exception as e:
            logger.warning(f"Impossible de faire défiler vers le haut: {e}")
        
        logger.info(f"Affichage de l'étape {step}: {self.steps[step]}")
        
    def show_initial_options(self) -> None:
        """
        Affiche les options initiales (nouveau document ou modèle existant)
        """
        # Nettoyer la zone de contenu
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Titre
        title = ctk.CTkLabel(
            self.content_frame,
            text="Choisissez une option",
            font=("", 24, "bold")
        )
        title.pack(pady=(0, 20))
        
        # Ajouter un message de débogage pour s'assurer que cette méthode est bien appelée
        logger.info("Affichage des options initiales - traiter un document")

        # Frame pour les boutons
        buttons_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        buttons_frame.pack(pady=20)

        # Bouton pour utiliser un modèle existant
        template_btn = ctk.CTkButton(
            buttons_frame,
            text="📂\n\nUtiliser un modèle\nexistant",
            command=self._use_existing_template,  # Nouvelle méthode pour utiliser un modèle existant
            width=250,
            height=250,
            corner_radius=10,
            font=("", 16),
            fg_color=("gray90", "gray20"),
            hover_color=("gray80", "gray30")
        )
        template_btn.pack(side="left", padx=10)

        # Bouton pour importer un document
        import_btn = ctk.CTkButton(
            buttons_frame,
            text="📄\n\nImporter un\ndocument",
            command=self.import_document,  # Nouvelle méthode à créer
            width=250,
            height=250,
            corner_radius=10,
            font=("", 16),
            fg_color=("gray90", "gray20"),
            hover_color=("gray80", "gray30")
        )
        import_btn.pack(side="left", padx=10)
        
        # S'assurer que les boutons sont visibles
        buttons_frame.update()
        
        # Mettre à jour la navigation pour s'assurer que les boutons sont affichés
        self.update_navigation()
    
    def _use_existing_template(self) -> None:
        """
        Redirige vers le formulaire de création de document dans la vue Documents
        """
        try:
            # Masquer cette vue
            self.hide()
            
            # Afficher la vue documents
            if hasattr(self.model, 'show_view'):
                # Afficher la vue documents
                self.model.show_view("documents")
                
                # Accéder à la vue documents
                if hasattr(self.model, 'views') and "documents" in self.model.views:
                    documents_view = self.model.views["documents"]
                    
                    # Vérifier si la vue documents a la méthode new_document
                    if hasattr(documents_view, "new_document"):
                        # Appeler la méthode pour créer un nouveau document
                        logger.info("Redirection vers le formulaire de création de document dans Documents")
                        documents_view.new_document()
                    else:
                        logger.error("La méthode new_document n'existe pas dans la vue documents")
                        self.show_error("La fonctionnalité de création de document n'est pas disponible")
                else:
                    logger.error("La vue documents n'est pas disponible")
                    self.show_error("La vue documents n'est pas disponible")
            else:
                logger.error("Impossible d'accéder à la vue documents")
                self.show_error("Impossible d'accéder à la vue documents")
        except Exception as e:
            logger.error(f"Erreur lors de la redirection vers le formulaire de document: {e}")
            self.show_error(f"Erreur: {str(e)}")

    def show_document_types(self) -> None:
        """
        Affiche les types de documents disponibles sous forme de cartes
        """
        # Nettoyer la zone de contenu
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Titre
        title = ctk.CTkLabel(
            self.content_frame,
            text="Types de documents disponibles",
            font=("", 24, "bold")
        )
        title.pack(pady=(0, 20))

        # Grille pour les cartes
        grid_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        grid_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Configuration de la grille (3 colonnes)
        grid_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Charger les types depuis le dossier data/documents/types
        types_dir = os.path.join("data", "documents", "types")
        if not os.path.exists(types_dir):
            # Créer le dossier s'il n'existe pas
            os.makedirs(types_dir)
            logger.info(f"Dossier créé : {types_dir}")

        # Liste pour stocker les types de documents
        document_types = []
        
        # Dictionnaire de correspondance type -> icône
        type_icons = {
            "contrat": "📜",
            "facture": "💰",
            "devis": "📋",
            "lettre": "✉️",
            "rapport": "📊",
            "presentation": "🎯",
            "proposition": "💡",
            "convention": "🤝",
            "certificat": "🏆",
            "attestation": "📝",
            "formulaire": "📄",
            "note": "📌",
            "procès-verbal": "📋",
            "plan": "🗺️",
            "budget": "💰",
            "planning": "📅",
            "inventaire": "📦",
            "catalogue": "📚",
            "manuel": "📖",
            "guide": "📗",
            "tutoriel": "📘",
            "documentation": "📑",
            "spécification": "📋",
            "analyse": "🔍",
            "étude": "📊",
            "projet": "🎯",
            "résumé": "📝",
            "synthèse": "📊",
            "évaluation": "📈",
            "audit": "🔍",
            "statistiques": "📈",
            "graphique": "📊",
            "tableau": "📋",
            "liste": "📋",
            "registre": "📑",
            "journal": "📓",
            "carnet": "📔",
            "agenda": "📅",
            "calendrier": "📅",
            "horaire": "⏰",
            "emploi du temps": "📅",
            "programme": "📋",
            "plan d'action": "🎯",
            "stratégie": "🎯",
            "objectif": "🎯",
            "mission": "🎯",
            "vision": "👀",
            "suggestion": "💡",
            "recommandation": "💡",
            "avis": "💡",
            "expertise": "🔍",
            "consultation": "💡",
            "recherche": "🔍",
            "enquête": "🔍",
            "sondage": "📊",
            "questionnaire": "📋",
            "demande": "📝",
            "requête": "📝",
            "pétition": "📝",
            "plainte": "📝",
            "réclamation": "📝"
        }
        
        # Parcourir le dossier des types
        if os.path.exists(types_dir):
            for type_name in os.listdir(types_dir):
                type_path = os.path.join(types_dir, type_name)
                if os.path.isdir(type_path):
                    # Compter le nombre de modèles dans le dossier
                    model_count = len([f for f in os.listdir(type_path) if f.endswith(('.docx', '.pdf', '.txt'))])
                    
                    # Déterminer l'icône en fonction du type de dossier
                    icon = "📁"  # Icône par défaut
                    type_lower = type_name.lower()
                    for key, value in type_icons.items():
                        if key in type_lower:
                            icon = value
                            break
                    
                    # Ajouter le type à la liste
                    document_types.append({
                        "name": type_name,
                        "icon": icon,
                        "count": f"{model_count} modèle{'s' if model_count > 1 else ''}"
                    })

        # Créer une carte pour chaque type
        for i, doc_type in enumerate(document_types):
            # Créer un cadre pour la carte
            card = ctk.CTkFrame(
                grid_frame,
                corner_radius=10,
                fg_color=("gray90", "gray20"),
                width=200,
                height=150
            )
            row = i // 3
            col = i % 3
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            card.grid_propagate(False)

            # Contenu de la carte
            icon_label = ctk.CTkLabel(
                card,
                text=doc_type["icon"],
                font=("", 32)
            )
            icon_label.pack(pady=(20, 5))

            name_label = ctk.CTkLabel(
                card,
                text=doc_type["name"],
                font=("", 16, "bold")
            )
            name_label.pack(pady=5)

            count_label = ctk.CTkLabel(
                card,
                text=doc_type["count"],
                font=("", 12),
                text_color=("gray50", "gray70")
            )
            count_label.pack(pady=5)

            # Rendre la carte cliquable
            for widget in [card, icon_label, name_label, count_label]:
                widget.bind("<Button-1>", lambda e, type_name=doc_type["name"]: self.show_models_for_type(type_name))
                widget.bind("<Enter>", lambda e, frame=card: frame.configure(fg_color=("gray80", "gray30")))
                widget.bind("<Leave>", lambda e, frame=card: frame.configure(fg_color=("gray90", "gray20")))
                widget.configure(cursor="hand2")

        # Message si aucun type n'est trouvé
        if not document_types:
            no_types_label = ctk.CTkLabel(
                grid_frame,
                text="Aucun type de document trouvé\ndans le dossier data/documents/types",
                font=("", 14),
                text_color=("gray50", "gray70")
            )
            no_types_label.pack(pady=50)

        # Bouton retour
        back_button = ctk.CTkButton(
            self.content_frame,
            text="Retour",
            command=lambda: self.show_step(0),
            width=100
        )
        back_button.pack(pady=20)

    def show_models_for_type(self, type_name: str) -> None:
        """
        Affiche les modèles disponibles pour un type de document donné
        
        Args:
            type_name: Nom du type de document sélectionné
        """
        # Nettoyer la zone de contenu
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Titre avec le type de document
        title = ctk.CTkLabel(
            self.content_frame,
            text=f"Modèles de {type_name.lower()}",
            font=("", 24, "bold")
        )
        title.pack(pady=(0, 20))

        # Grille pour les cartes
        grid_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        grid_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Configuration de la grille (3 colonnes)
        grid_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Charger les modèles depuis le dossier du type
        type_path = os.path.join("data", "documents", "types", type_name)
        models = []

        if os.path.exists(type_path):
            for model_name in os.listdir(type_path):
                if model_name.endswith(('.docx', '.pdf', '.txt')):
                    # Déterminer l'icône en fonction du type de fichier
                    icon = "📄" if model_name.endswith('.txt') else "📝" if model_name.endswith('.docx') else "📋"
                    
                    # Ajouter le modèle à la liste
                    models.append({
                        "name": os.path.splitext(model_name)[0],  # Nom sans extension
                        "icon": icon,
                        "file": model_name  # Nom complet avec extension
                    })

        # Créer une carte pour chaque modèle
        for i, model in enumerate(models):
            # Créer un cadre pour la carte
            card = ctk.CTkFrame(
                grid_frame,
                corner_radius=10,
                fg_color=("gray90", "gray20"),
                width=200,
                height=150
            )
            row = i // 3
            col = i % 3
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            card.grid_propagate(False)

            # Contenu de la carte
            icon_label = ctk.CTkLabel(
                card,
                text=model["icon"],
                font=("", 32)
            )
            icon_label.pack(pady=(20, 5))

            name_label = ctk.CTkLabel(
                card,
                text=model["name"],
                font=("", 16, "bold")
            )
            name_label.pack(pady=5)

            # Rendre la carte cliquable
            for widget in [card, icon_label, name_label]:
                widget.bind("<Button-1>", lambda e, t=type_name, m=model["file"]: self.select_model(t, m))
                widget.bind("<Enter>", lambda e, frame=card: frame.configure(fg_color=("gray80", "gray30")))
                widget.bind("<Leave>", lambda e, frame=card: frame.configure(fg_color=("gray90", "gray20")))
                widget.configure(cursor="hand2")

        # Message si aucun modèle n'est trouvé
        if not models:
            no_models_label = ctk.CTkLabel(
                grid_frame,
                text=f"Aucun modèle trouvé pour le type {type_name}",
                font=("", 14),
                text_color=("gray50", "gray70")
            )
            no_models_label.pack(pady=50)

        # Bouton retour
        back_button = ctk.CTkButton(
            self.content_frame,
            text="Retour aux types de documents",
            command=self.show_document_types,
            width=200
        )
        back_button.pack(pady=20)

    def select_model(self, type_name: str, model_file: str) -> None:
        """
        Sélectionne un modèle et passe à l'étape suivante
        
        Args:
            type_name: Nom du type de document
            model_file: Nom du fichier modèle
        """
        try:
            self.selected_type = type_name
            self.selected_model = model_file
            self.selected_template = {
                "type": type_name,
                "name": os.path.splitext(model_file)[0],
                "file": model_file,
                "path": os.path.join("data", "documents", "types", type_name, model_file)
            }
            logging.info(f"Modèle sélectionné : {model_file} ({type_name})")
            self.show_step(2)  # Passer à l'étape du formulaire client
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du modèle: {e}")
            self.show_error("Une erreur est survenue lors de la sélection du modèle")

    def show_client_form(self) -> None:
        """
        Affiche le formulaire simplifié de recherche client
        """
        # Si on vient d'un document importé et que l'analyse n'est pas terminée
        if (hasattr(self, 'selected_template') and 
            self.selected_template.get('from_analysis') and 
            not getattr(self, 'analysis_complete', False)):
            
            # Nettoyer la zone de contenu
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            
            # Créer un cadre conteneur pour centrer le contenu
            container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Titre
            title = ctk.CTkLabel(
                container,
                text="Analyse du document en cours",
                font=("", 24, "bold")
            )
            title.pack(pady=(0, 20))
            
            # Message de chargement
            loading_label = ctk.CTkLabel(
                container,
                text=f"Analyse de {self.selected_template['name']}...\nCette opération peut prendre quelques instants.",
                font=("", 14),
                justify="center"
            )
            loading_label.pack(pady=20)
            
            # Barre de progression indéterminée
            progress = ctk.CTkProgressBar(container, width=400)
            progress.pack(pady=10)
            progress.start()  # Animation de chargement
            
            # Cadre pour afficher les variables détectées (initialement vide)
            variables_frame = ctk.CTkScrollableFrame(container, fg_color=("gray95", "gray15"), height=200)
            variables_frame.pack(fill="x", padx=20, pady=10)
            variables_frame.pack_forget()  # Masquer jusqu'à ce que l'analyse soit terminée
            
            # Afficher la barre de recherche client même pendant l'analyse
            search_frame = ctk.CTkFrame(container, fg_color=("transparent"))
            search_frame.pack(fill="x", padx=20, pady=(30, 10))
            
            # Message d'information
            info_label = ctk.CTkLabel(
                search_frame,
                text="Veuillez attendre la fin de l'analyse avant de sélectionner un client.",
                font=("", 12),
                text_color=("gray50", "gray70"),
                wraplength=600,
                justify="center"
            )
            info_label.pack(pady=(0, 10))
            
            # Cadre de recherche (désactivé pendant l'analyse)
            search_input_frame = ctk.CTkFrame(search_frame, fg_color=("gray90", "gray20"))
            search_input_frame.pack(fill="x", padx=20, pady=10)
            
            # Champ de recherche (désactivé)
            self.search_entry = ctk.CTkEntry(
                search_input_frame,
                placeholder_text="Nom, email, téléphone ou entreprise du client...",
                width=400,
                state="disabled",
                fg_color=("gray80", "gray30")
            )
            self.search_entry.pack(side="left", padx=10, pady=10)
            
            # Bouton de recherche (désactivé)
            search_button = ctk.CTkButton(
                search_input_frame,
                text="Rechercher",
                width=100,
                command=self.search_client,
                state="disabled",
                fg_color=("gray75", "gray45")
            )
            search_button.pack(side="left", padx=10, pady=10)
            
            # Zone d'affichage des résultats avec défilement
            self.results_frame = ctk.CTkScrollableFrame(container, fg_color="transparent", height=200)
            self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Message indiquant que la recherche est désactivée
            disabled_msg = ctk.CTkLabel(
                self.results_frame,
                text="La recherche de clients sera disponible une fois l'analyse terminée",
                font=("", 12),
                text_color=("gray50", "gray70")
            )
            disabled_msg.pack(pady=50)
            
            # Vérifier périodiquement si l'analyse est terminée
            def check_analysis():
                if hasattr(self, 'analysis_error') and self.analysis_error:
                    # Arrêter l'animation
                    progress.stop()
                    # Afficher l'erreur
                    error_label = ctk.CTkLabel(
                        container,
                        text=f"Erreur lors de l'analyse : {self.analysis_error}",
                        text_color="red",
                        wraplength=600
                    )
                    error_label.pack(pady=10)
                    return
                
                if getattr(self, 'analysis_complete', False):
                    # Analyse terminée, arrêter le spinner
                    progress.stop()
                    
                    # Vérifier si des variables ont été trouvées
                    if hasattr(self, 'document_data') and self.document_data.get('variables'):
                        # Variables trouvées, mettre à jour l'interface
                        title.configure(text="Analyse du document terminée")
                        loading_label.configure(
                            text="Analyse terminée avec succès.",
                            text_color=("green", "#00AA00")
                        )
                        
                        # Afficher les variables détectées
                        variables_frame.pack(fill="x", padx=20, pady=10)
                        
                        # Titre des variables
                        vars_title = ctk.CTkLabel(
                            variables_frame,
                            text="Variables détectées :",
                            font=("", 14, "bold")
                        )
                        vars_title.pack(anchor="w", padx=10, pady=(10, 5))
                        
                        # Afficher chaque variable
                        var_count = 0
                        for var_name, var_info in self.document_data.get('variables', {}).items():
                            var_count += 1
                            var_frame = ctk.CTkFrame(variables_frame, fg_color="transparent")
                            var_frame.pack(fill="x", padx=10, pady=3)
                            
                            # Nom de la variable
                            var_label = ctk.CTkLabel(
                                var_frame,
                                text=f"{var_name}:",
                                font=("", 12, "bold"),
                                width=150
                            )
                            var_label.pack(side="left")
                            
                            # Valeur courante
                            current_value = var_info.get('current_value', '') if isinstance(var_info, dict) else str(var_info)
                            value_label = ctk.CTkLabel(
                                var_frame,
                                text=current_value,
                                font=("", 12)
                            )
                            value_label.pack(side="left", padx=10)
                        
                        # Message de succès
                        count_label = ctk.CTkLabel(
                            variables_frame,
                            text=f"{var_count} variables trouvées",
                            font=("", 12),
                            text_color=("gray50", "gray70")
                        )
                        count_label.pack(anchor="e", padx=10, pady=(5, 10))
                        
                        # Changer le message d'information
                        info_label.configure(
                            text="Vous pouvez maintenant sélectionner un client pour continuer :",
                            text_color=("black", "white")
                        )
                        
                        # Activer les éléments de recherche
                        self.search_entry.configure(state="normal", fg_color=("white", "gray20"))
                        search_button.configure(state="normal", fg_color=("#3a7ebf", "#1f538d"))
                        
                        # Nettoyer les résultats (mais ne pas afficher tous les clients)
                        for widget in self.results_frame.winfo_children():
                            widget.destroy()
                            
                        # Afficher un message pour inviter à la recherche
                        search_prompt = ctk.CTkLabel(
                            self.results_frame,
                            text="Saisissez un terme pour rechercher un client",
                            font=("Arial", 12)
                        )
                        search_prompt.pack(pady=20, padx=10)
                        
                        # Activer les boutons de navigation
                        self.update_navigation()
                    else:
                        # Aucune variable trouvée
                        title.configure(text="Aucune variable détectée")
                        loading_label.configure(
                            text="Aucune variable n'a été détectée dans le document.\nVeuillez essayer avec un autre document.",
                            text_color="red"
                        )
                        
                        # Désactiver la recherche client
                        info_label.configure(
                            text="Aucune variable n'a été détectée. Veuillez réinitialiser et essayer avec un autre document.",
                            text_color="red"
                        )
                else:
                    # Vérifier à nouveau dans 500ms
                    self.content_frame.after(500, check_analysis)
            
            # Démarrer la vérification
            self.content_frame.after(500, check_analysis)
            
            # Mettre à jour la navigation (boutons suivant/précédent)
            self.update_navigation()
            return
            
        # Nettoyer la zone de contenu
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Créer un cadre conteneur pour centrer le contenu
        container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Titre
        title = ctk.CTkLabel(
            container,
            text="Recherche du client",
            font=("", 24, "bold")
        )
        title.pack(pady=(0, 20))

        # Message d'information
        info_label = ctk.CTkLabel(
            container,
            text="Recherchez un client pour associer à ce document :",
            font=("", 12),
            text_color=("gray50", "gray70"),
            wraplength=600,
            justify="center"
        )
        info_label.pack(pady=(0, 20))

        # Cadre de recherche
        search_frame = ctk.CTkFrame(container)
        search_frame.pack(fill="x", padx=20, pady=10)

        # Champ de recherche
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Nom, email, téléphone ou entreprise du client...",
            width=400
        )
        self.search_entry.pack(side="left", padx=10, pady=10)
        
        # Bouton de recherche
        search_button = ctk.CTkButton(
            search_frame,
            text="Rechercher",
            width=100,
            command=self.search_client
        )
        search_button.pack(side="left", padx=10, pady=10)

        # Zone d'affichage des résultats avec défilement
        self.results_frame = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Afficher un message initial pour guider l'utilisateur
        guide_label = ctk.CTkLabel(
            self.results_frame,
            text="Saisissez un terme pour rechercher un client",
            font=("Arial", 12)
        )
        guide_label.pack(pady=20, padx=10)
        
        # Forcer la mise à jour de l'affichage
        self.content_frame.update()
        container.update()
        self.results_frame.update()
        
        # Lier l'événement Return/Enter au champ de recherche
        self.search_entry.bind("<Return>", lambda e: self.search_client())
        
        # Lier l'événement de modification du texte pour la recherche en temps réel
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_client())
        
        # S'assurer que le focus est sur le champ de recherche
        self.search_entry.focus_set()
        
        # Mettre à jour la navigation (boutons suivant/précédent)
        self.update_navigation()

    def search_client(self) -> None:
        """
        Recherche un client dans la base de données
        Utilise le texte saisi dans le champ de recherche
        """
        try:
            # Nettoyer la zone de résultats
            for widget in self.results_frame.winfo_children():
                if widget.winfo_exists():  # Vérifier que le widget existe toujours
                    widget.destroy()
                
            logger.info("Recherche de clients démarrée")
                
            # Récupérer la valeur de recherche
            search_value = self.search_entry.get().strip().lower() if hasattr(self, 'search_entry') else ""
            
            # Si la recherche est vide, ne pas afficher de clients
            if not search_value:
                logger.info("Aucun terme de recherche, affichage de tous les clients")
                # Afficher un message indiquant qu'il faut effectuer une recherche
                message = ctk.CTkLabel(
                    self.results_frame,
                    text="Saisissez un terme pour rechercher un client",
                    font=("Arial", 12)
                )
                message.pack(pady=20, padx=10)
                return
                
            # Récupérer les clients depuis le modèle
            clients = []
            if hasattr(self.model, 'clients'):
                clients = getattr(self.model, 'clients')
                logger.info(f"Nombre de clients disponibles: {len(clients)}")
                
            # Si self.model.clients n'est pas accessible, essayer de charger les clients depuis le fichier JSON
            if not clients:
                clients_file = os.path.join("data", "clients", "clients.json")
                if os.path.exists(clients_file):
                    try:
                        with open(clients_file, "r", encoding="utf-8") as f:
                            clients = json.load(f)
                        logger.info(f"Clients chargés depuis le fichier: {len(clients)}")
                    except Exception as e:
                        logger.error(f"Erreur lors de la lecture du fichier clients: {e}")
            
            # Filtrer les clients selon la recherche
            filtered_clients = []
            for client in clients:
                for key, value in client.items():
                    if isinstance(value, str) and search_value in value.lower():
                        filtered_clients.append(client)
                        break
            logger.info(f"Recherche '{search_value}': {len(filtered_clients)} clients trouvés")
            
            # Afficher les résultats
            if not filtered_clients:
                no_results = ctk.CTkLabel(
                    self.results_frame,
                    text=f"Aucun client trouvé pour '{search_value}'",
                    font=("Arial", 12)
                )
                no_results.pack(pady=20, padx=10)
                return
            
            # Afficher les clients filtrés avec l'ancien design
            for client in filtered_clients:
                # Créer un cadre pour chaque client
                client_frame = ctk.CTkFrame(self.results_frame)
                client_frame.pack(fill="x", padx=10, pady=5)
                
                # Nom du client (ou société)
                name = client.get('nom', '') or client.get('name', '') or client.get('société', '') or "Client sans nom"
                
                # Email et téléphone pour l'affichage
                email = client.get('email', '')
                phone = client.get('telephone', '')
                
                # Informations du client
                info_text = f"{name}"
                if email:
                    info_text += f" - {email}"
                if phone:
                    info_text += f" - {phone}"
                    
                client_label = ctk.CTkLabel(
                    client_frame,
                    text=info_text,
                    font=("Arial", 12),
                    anchor="w",
                    justify="left"
                )
                client_label.pack(side="left", padx=10, pady=5, fill="x", expand=True)
                
                # Créer une copie locale du client pour éviter les problèmes de référence dans les lambdas
                client_data = client.copy()
                
                # Fonction sécurisée pour sélectionner un client
                def create_safe_select_callback(client_data):
                    def safe_select_callback(event=None):
                        # Vérifier que le cadre parent existe toujours avant d'appeler la sélection
                        if hasattr(self, 'results_frame') and self.results_frame.winfo_exists():
                            self._select_client(client_data)
                    return safe_select_callback
                
                # Bouton de sélection
                select_button = ctk.CTkButton(
                    client_frame,
                    text="Sélectionner",
                    width=100,
                    command=create_safe_select_callback(client_data)
                )
                select_button.pack(side="right", padx=10, pady=5)
                
                # Rendre la ligne cliquable
                safe_callback = create_safe_select_callback(client_data)
                client_frame.bind("<Button-1>", lambda e, cb=safe_callback: cb())
                client_label.bind("<Button-1>", lambda e, cb=safe_callback: cb())
                
                # Configurer le curseur
                client_frame.configure(cursor="hand2")
                client_label.configure(cursor="hand2")
                
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de clients: {e}")
            error_label = ctk.CTkLabel(
                self.results_frame,
                text=f"Erreur: {str(e)}",
                text_color="red",
                font=("Arial", 12)
            )
            error_label.pack(pady=20, padx=10)

    def on_close_button(self) -> None:
        """
        Gère la fermeture de la vue lorsque l'utilisateur clique sur le bouton X
        """
        try:
            # Réinitialiser les variables
            self.current_step = 0
            self.selected_template = None
            self.client_info = {}
            self.document_data = {}
            self.missing_variables = {}
            self.preview_content = ""
            self.client_selected = False
            
            # Revenir à la vue précédente (dashboard)
            if hasattr(self.parent, 'show_view'):
                self.parent.show_view('dashboard')
            
            logger.info("Vue document_creator fermée")
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture de la vue document_creator: {e}")
            # Tenter de revenir à la vue dashboard en cas d'erreur
            try:
                if hasattr(self.parent, 'show_view'):
                    self.parent.show_view('dashboard')
            except:
                pass
                
    def import_document(self) -> None:
        """
        Importe un document externe pour analyse
        Ouvre une boîte de dialogue de fichier
        """
        try:
            # Ouvrir une boîte de dialogue pour sélectionner un fichier
            filetypes = [
                ("Documents", "*.pdf *.docx *.doc *.odt *.txt"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx *.doc"),
                ("OpenDocument", "*.odt"),
                ("Texte", "*.txt"),
                ("Tous les fichiers", "*.*")
            ]
            file_path = filedialog.askopenfilename(
                title="Sélectionner un document",
                filetypes=filetypes
            )
            
            if not file_path:
                # L'utilisateur a annulé la sélection
                return
                
            logger.info(f"Document sélectionné pour analyse: {file_path}")
            
            # Créer un template virtuel basé sur le document importé
            self.selected_template = {
                "type": "import",
                "name": os.path.basename(file_path),
                "file": os.path.basename(file_path),
                "path": file_path,
                "from_analysis": True
            }
            
            # Passer directement à l'étape de recherche de client
            self.show_step(2)
            
            # Démarrer l'analyse du document
            self._start_document_analysis(file_path)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'importation du document: {e}")
            self.show_error(f"Erreur lors de l'importation: {str(e)}")
            
    def _start_document_analysis(self, file_path: str) -> None:
        """
        Démarre l'analyse d'un document avec l'IA
        
        Args:
            file_path: Chemin du fichier à analyser
        """
        try:
            # Initialiser le processeur de documents s'il n'existe pas déjà
            if not hasattr(self, 'document_processor'):
                self.document_processor = AIDocumentProcessor()
                
            logger.info(f"Début de l'analyse du document: {file_path}")
            
            # Indiquer que l'analyse est en cours
            self.analysis_in_progress = True
            self.analysis_complete = False
            self.analysis_error = None
            
            # Créer un thread pour l'analyse afin de ne pas bloquer l'interface
            def analyze_document_thread():
                try:
                    # Effectuer l'analyse
                    result = self.document_processor.analyze_document(file_path)
                    
                    # Stocker les données résultantes
                    self.document_data = result
                    
                    # Marquer l'analyse comme terminée
                    self.analysis_in_progress = False
                    self.analysis_complete = True
                    
                    logger.info("Analyse du document terminée")
                    
                except Exception as e:
                    self.analysis_in_progress = False
                    self.analysis_complete = True
                    self.analysis_error = str(e)
                    logger.error(f"Erreur lors de l'analyse du document: {e}")
            
            # Démarrer le thread d'analyse
            analysis_thread = threading.Thread(target=analyze_document_thread)
            analysis_thread.daemon = True
            analysis_thread.start()
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de l'analyse: {e}")
            self.analysis_in_progress = False
            self.analysis_error = str(e)
            
    def _apply_client_to_analysis(self, client: Dict[str, Any]) -> None:
        """
        Applique les informations du client sélectionné à l'analyse en cours
        
        Args:
            client: Dictionnaire contenant les informations du client
        """
        try:
            # Vérifier que les widgets nécessaires existent toujours
            if not hasattr(self, 'content_frame') or not self.content_frame.winfo_exists():
                logger.error("Le cadre de contenu n'existe plus, abandon de l'application du client")
                return
            
            # Stocker les informations du client
            self.client_info = client
            self.client_selected = True
            
            # Passer à l'étape suivante si l'analyse est terminée, mais avec un délai pour éviter les problèmes de fenêtre
            if self.analysis_complete:
                # Utiliser after pour différer l'exécution et éviter les erreurs de fenêtre
                self.parent.after(100, lambda: self._safe_show_step(3))
                
        except Exception as e:
            logger.error(f"Erreur lors de l'application du client à l'analyse: {e}")
            self.show_error(f"Erreur: {str(e)}")
            
    def _safe_show_step(self, step: int) -> None:
        """
        Version sécurisée de show_step qui vérifie si les widgets existent toujours
        
        Args:
            step: Numéro de l'étape à afficher
        """
        try:
            # Vérifier que les widgets nécessaires existent toujours
            if hasattr(self, 'content_frame') and self.content_frame.winfo_exists():
                self.show_step(step)
            else:
                logger.error(f"Tentative d'afficher l'étape {step} mais les widgets n'existent plus")
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage sécurisé de l'étape {step}: {e}")
            
    def show_error(self, message: str) -> None:
        """
        Affiche un message d'erreur dans une boîte de dialogue
        
        Args:
            message: Message d'erreur à afficher
        """
        try:
            # Utiliser une boîte de dialogue CTk
            from customtkinter import CTkToplevel, CTkLabel, CTkButton
            
            # Créer une fenêtre modale
            error_window = CTkToplevel(self.parent)
            error_window.title("Erreur")
            error_window.geometry("400x200")
            error_window.grab_set()  # Rendre la fenêtre modale
            
            # Message d'erreur
            error_label = CTkLabel(
                error_window,
                text=message,
                wraplength=350,
                text_color="red"
            )
            error_label.pack(padx=20, pady=30, expand=True)
            
            # Bouton OK
            ok_button = CTkButton(
                error_window,
                text="OK",
                width=100,
                command=error_window.destroy
            )
            ok_button.pack(pady=20)
            
            # Centrer la fenêtre
            error_window.update_idletasks()
            width = error_window.winfo_width()
            height = error_window.winfo_height()
            x = (error_window.winfo_screenwidth() // 2) - (width // 2)
            y = (error_window.winfo_screenheight() // 2) - (height // 2)
            error_window.geometry(f"{width}x{height}+{x}+{y}")
            
        except Exception as e:
            # Fallback pour les erreurs dans la gestion des erreurs
            logger.error(f"Erreur lors de l'affichage du message d'erreur: {e}")
            # Tenter d'utiliser la méthode standard
            from tkinter import messagebox
            messagebox.showerror("Erreur", message)
 
    def update_navigation(self) -> None:
        """
        Met à jour les boutons de navigation selon l'étape actuelle
        """
        try:
            # Nettoyer la zone de navigation
            for widget in self.nav_frame.winfo_children():
                widget.destroy()
                
            logger.info(f"Mise à jour de la navigation à l'étape {self.current_step}")
            
            # Bouton de retour (sauf pour la première étape)
            if self.current_step > 0:
                back_btn = ctk.CTkButton(
                    self.nav_frame,
                    text="← Retour",
                    command=lambda: self.show_step(self.current_step - 1),
                    width=100,
                    fg_color=("gray80", "gray30"),
                    text_color=("gray10", "gray90")
                )
                back_btn.pack(side="left", padx=10)
                
            # Bouton de réinitialisation
            reset_btn = ctk.CTkButton(
                self.nav_frame,
                text="↺ Réinitialiser",
                command=self.reset_process,
                width=100,
                fg_color=("gray80", "gray30"),
                text_color=("gray10", "gray90")
            )
            reset_btn.pack(side="left", padx=10)
            
            # Bouton suivant
            next_btn = ctk.CTkButton(
                self.nav_frame,
                text="Suivant →",
                command=lambda: self.show_step(self.current_step + 1),
                width=100
            )
            
            # Déterminer si le bouton suivant doit être activé
            enabled = True
            
            # Gestion de l'état du bouton selon l'étape
            if self.current_step == 2:  # Étape client
                if not getattr(self, 'client_selected', False):
                    enabled = False
                # Si on est en cours d'analyse, désactiver le bouton
                if getattr(self, 'analysis_in_progress', False) and not getattr(self, 'analysis_complete', False):
                    enabled = False
            
            # Configurer l'état du bouton
            if not enabled:
                next_btn.configure(state="disabled", fg_color=("gray75", "gray45"))
            
            next_btn.pack(side="right", padx=10)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la navigation: {e}")
            
    def reset_process(self) -> None:
        """
        Réinitialise le processus de création
        """
        try:
            # Réinitialiser les variables
            self.current_step = 0
            self.selected_template = None
            self.client_info = {}
            self.document_data = {}
            self.missing_variables = {}
            self.preview_content = ""
            self.client_selected = False
            self.analysis_in_progress = False
            self.analysis_complete = False
            self.analysis_error = None
            
            # Retourner à la première étape
            self.show_step(0)
            
            logger.info("Processus de création réinitialisé")
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation: {e}")

    def _select_client(self, client: Dict[str, Any]) -> None:
        """
        Sélectionne un client et met à jour les informations
        
        Args:
            client: Dictionnaire contenant les informations du client
        """
        try:
            # Vérifier si nous sommes déjà en train de traiter une sélection
            if hasattr(self, '_selection_in_progress') and self._selection_in_progress:
                logger.info("Sélection de client déjà en cours, ignorer ce clic")
                return
                
            # Marquer que nous sommes en train de traiter une sélection
            self._selection_in_progress = True
            
            # Stocker les informations du client de manière sécurisée
            # Faire une copie pour éviter des problèmes de référence
            self.client_info = client.copy()
            self.client_selected = True
            
            # Enregistrer le nom du client pour le logging
            name = client.get('nom', '') or client.get('name', '') or client.get('société', '') or "Client sans nom"
            logger.info(f"Client sélectionné: {name}")
            
            # Utiliser une approche complètement différente pour éviter l'erreur de fenêtre
            # Au lieu de manipuler les widgets directement, nous allons repasser par une méthode propre
            
            # Créer une fonction pour gérer la transition de façon sécurisée
            def handle_transition():
                try:
                    # Si nous venons d'un document analysé
                    if hasattr(self, 'selected_template') and self.selected_template and self.selected_template.get('from_analysis'):
                        # Vérifier si l'analyse est terminée
                        if getattr(self, 'analysis_complete', False):
                            logger.info("Transition à l'étape de validation après l'analyse")
                            # Ne pas appeler show_step directement mais nettoyer d'abord l'interface
                            self._clean_interface_for_transition(3)
                        else:
                            logger.info("L'analyse n'est pas terminée, ne pas passer à l'étape suivante")
                    else:
                        # Transition vers l'étape de validation
                        logger.info("Transition à l'étape de validation standard")
                        self._clean_interface_for_transition(3)
                except Exception as e:
                    logger.error(f"Erreur lors de la transition après sélection du client: {e}")
                finally:
                    self._selection_in_progress = False
            
            # Utiliser after pour exécuter la transition de façon asynchrone
            self.parent.after(50, handle_transition)
            
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du client: {e}")
            self.show_error(f"Erreur: {str(e)}")
            self._selection_in_progress = False
            
    def _clean_interface_for_transition(self, target_step: int) -> None:
        """
        Méthode spéciale pour nettoyer l'interface avant une transition d'étape délicate
        Cette méthode évite les erreurs "bad window path name"
        
        Args:
            target_step: Numéro de l'étape cible
        """
        try:
            # Enregistrer l'étape cible
            self.pending_step = target_step
            
            # Nettoyer entièrement la zone de contenu
            if hasattr(self, 'content_frame') and self.content_frame.winfo_exists():
                for widget in self.content_frame.winfo_children():
                    if widget.winfo_exists():
                        widget.destroy()
                
                # Créer un message de transition
                transition_label = ctk.CTkLabel(
                    self.content_frame,
                    text="Chargement...",
                    font=("", 18)
                )
                transition_label.pack(pady=100)
                
                # Forcer la mise à jour de l'interface
                self.content_frame.update_idletasks()
                
                # Planifier l'affichage de l'étape suivante
                self.parent.after(100, lambda: self._complete_transition())
            else:
                logger.error("Le cadre de contenu n'existe plus lors de la transition")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage pour la transition: {e}")
            # Tenter quand même d'afficher l'étape cible
            self.parent.after(200, lambda: self.show_step(target_step))
            
    def _complete_transition(self) -> None:
        """
        Complète la transition vers l'étape cible après nettoyage
        """
        try:
            if hasattr(self, 'pending_step'):
                target = self.pending_step
                # Supprimer l'attribut pour éviter des transitions multiples
                delattr(self, 'pending_step')
                # Afficher l'étape cible
                self.show_step(target)
            else:
                logger.error("Pas d'étape cible définie pour la transition")
        except Exception as e:
            logger.error(f"Erreur lors de la complétion de la transition: {e}")
            # Si une erreur se produit, revenir à l'étape client
            self.show_step(2)

    def show_validation(self) -> None:
        """
        Affiche l'étape de validation du document
        """
        try:
            # Nettoyer la zone de contenu
            for widget in self.content_frame.winfo_children():
                widget.destroy()
                
            # Créer un cadre conteneur pour centrer le contenu
            container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Titre
            title = ctk.CTkLabel(
                container,
                text="Validation du document",
                font=("", 24, "bold")
            )
            title.pack(pady=(0, 20))
            
            # Informations sur le template
            if hasattr(self, 'selected_template') and self.selected_template:
                template_frame = ctk.CTkFrame(container, fg_color=("gray95", "gray15"))
                template_frame.pack(fill="x", padx=20, pady=10)
                
                template_title = ctk.CTkLabel(
                    template_frame,
                    text="Modèle sélectionné :",
                    font=("", 16, "bold")
                )
                template_title.pack(pady=(10, 5), padx=20, anchor="w")
                
                # Nom du template
                template_name = self.selected_template.get('name', 'Document sans nom')
                template_info = ctk.CTkLabel(
                    template_frame,
                    text=f"{template_name}",
                    font=("", 14)
                )
                template_info.pack(pady=2, padx=20, anchor="w")
                
                # Type
                if self.selected_template.get('type'):
                    template_type = ctk.CTkLabel(
                        template_frame,
                        text=f"Type: {self.selected_template['type']}",
                        font=("", 12)
                    )
                    template_type.pack(pady=2, padx=20, anchor="w")
            
            # Informations sur le client
            if hasattr(self, 'client_info') and self.client_info:
                client_frame = ctk.CTkFrame(container, fg_color=("gray95", "gray15"))
                client_frame.pack(fill="x", padx=20, pady=10)
                
                client_title = ctk.CTkLabel(
                    client_frame,
                    text="Client sélectionné :",
                    font=("", 16, "bold")
                )
                client_title.pack(pady=(10, 5), padx=20, anchor="w")
                
                # Nom du client
                client_name = self.client_info.get('nom', '') or self.client_info.get('name', '') or self.client_info.get('société', '') or "Client sans nom"
                client_info = ctk.CTkLabel(
                    client_frame,
                    text=f"{client_name}",
                    font=("", 14)
                )
                client_info.pack(pady=2, padx=20, anchor="w")
                
                # Email
                if self.client_info.get('email'):
                    email_info = ctk.CTkLabel(
                        client_frame,
                        text=f"Email: {self.client_info['email']}",
                        font=("", 12)
                    )
                    email_info.pack(pady=2, padx=20, anchor="w")
                
                # Société
                if self.client_info.get('société'):
                    company_info = ctk.CTkLabel(
                        client_frame,
                        text=f"Société: {self.client_info['société']}",
                        font=("", 12)
                    )
                    company_info.pack(pady=2, padx=20, anchor="w")
                
                # Téléphone
                if self.client_info.get('telephone'):
                    phone_info = ctk.CTkLabel(
                        client_frame,
                        text=f"Téléphone: {self.client_info['telephone']}",
                        font=("", 12)
                    )
                    phone_info.pack(pady=2, padx=20, anchor="w")
            
            # Variables détectées
            if hasattr(self, 'document_data') and self.document_data and self.document_data.get('variables'):
                variables_frame = ctk.CTkFrame(container, fg_color=("gray95", "gray15"))
                variables_frame.pack(fill="x", padx=20, pady=10)
                
                variables_title = ctk.CTkLabel(
                    variables_frame,
                    text="Variables détectées :",
                    font=("", 16, "bold")
                )
                variables_title.pack(pady=(10, 5), padx=20, anchor="w")
                
                # Créer une zone déroulante pour les variables
                variables_scroll = ctk.CTkScrollableFrame(variables_frame, height=200)
                variables_scroll.pack(fill="x", padx=20, pady=10)
                
                # Afficher chaque variable
                var_count = 0
                for var_name, var_info in self.document_data.get('variables', {}).items():
                    var_count += 1
                    var_frame = ctk.CTkFrame(variables_scroll, fg_color="transparent")
                    var_frame.pack(fill="x", padx=10, pady=3)
                    
                    # Nom de la variable
                    var_label = ctk.CTkLabel(
                        var_frame,
                        text=f"{var_name}:",
                        font=("", 12, "bold"),
                        width=150
                    )
                    var_label.pack(side="left")
                    
                    # Valeur courante
                    current_value = var_info.get('current_value', '') if isinstance(var_info, dict) else str(var_info)
                    value_label = ctk.CTkLabel(
                        var_frame,
                        text=current_value,
                        font=("", 12)
                    )
                    value_label.pack(side="left", padx=10)
                
                # Message récapitulatif
                summary_label = ctk.CTkLabel(
                    variables_frame,
                    text=f"{var_count} variables trouvées",
                    font=("", 12),
                    text_color=("gray50", "gray70")
                )
                summary_label.pack(anchor="e", padx=10, pady=(5, 10))
            
            # Message de confirmation
            confirm_frame = ctk.CTkFrame(container)
            confirm_frame.pack(fill="x", padx=20, pady=20)
            
            confirm_label = ctk.CTkLabel(
                confirm_frame,
                text="Confirmer la création du document ?",
                font=("", 16, "bold")
            )
            confirm_label.pack(pady=10)
            
            # Boutons de confirmation
            buttons_frame = ctk.CTkFrame(confirm_frame, fg_color="transparent")
            buttons_frame.pack(pady=10)
            
            confirm_button = ctk.CTkButton(
                buttons_frame,
                text="Confirmer",
                command=self._confirm_document,
                width=150
            )
            confirm_button.pack(side="left", padx=10)
            
            cancel_button = ctk.CTkButton(
                buttons_frame,
                text="Modifier",
                command=lambda: self.show_step(4),  # Aller à l'étape de personnalisation
                width=150,
                fg_color=("gray80", "gray30"),
                text_color=("gray10", "gray90")
            )
            cancel_button.pack(side="left", padx=10)
            
            # Mettre à jour la navigation
            self.update_navigation()
            
            logger.info("Affichage de l'étape de validation")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de l'étape de validation: {e}")
            self.show_error(f"Erreur: {str(e)}")
            
    def _confirm_document(self) -> None:
        """
        Confirme la création du document et passe à l'étape de finalisation
        """
        try:
            # Simuler la génération du document et obtenir le chemin du fichier généré
            # En production, cela devrait appeler le générateur de documents réel
            
            # Pour un test, créons un chemin fictif vers un document PDF
            output_dir = os.path.join("data", "documents", "outputs")
            os.makedirs(output_dir, exist_ok=True)
            
            # Créer un nom de fichier basé sur le template et le client
            template_name = self.selected_template.get('name', 'document')
            client_name = "client"
            if hasattr(self, 'client_info') and self.client_info:
                client_name = self.client_info.get('nom', '') or self.client_info.get('name', '') or self.client_info.get('société', '') or "client"
            
            # Générer un nom de fichier unique
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{template_name}_{client_name}_{timestamp}.pdf"
            
            # Nettoyer le nom du fichier (enlever les caractères spéciaux)
            import re
            filename = re.sub(r'[^\w\-_\. ]', '_', filename)
            
            # Stocker le chemin du document généré
            self.generated_document_path = os.path.join(output_dir, filename)
            
            # En conditions réelles, on génèrerait le document ici:
            # 1. Extraire les variables du modèle
            # 2. Appliquer les variables personnalisées
            # 3. Générer le document avec les infos du client
            
            # Pour simuler un document, créons un fichier texte simple
            try:
                with open(self.generated_document_path, 'w', encoding='utf-8') as f:
                    f.write(f"Document simulé pour {client_name}\n")
                    f.write(f"Modèle: {template_name}\n")
                    f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    # Ajouter les variables (si disponibles)
                    if hasattr(self, 'document_data') and self.document_data and 'variables' in self.document_data:
                        f.write("Variables:\n")
                        for var_name, var_info in self.document_data.get('variables', {}).items():
                            if isinstance(var_info, dict):
                                value = var_info.get('current_value', '')
                            else:
                                value = str(var_info)
                            f.write(f"{var_name}: {value}\n")
                
                logger.info(f"Document simulé créé: {self.generated_document_path}")
            except Exception as e:
                logger.error(f"Erreur lors de la création du document simulé: {e}")
                self.show_error(f"Erreur lors de la génération du document: {str(e)}")
                return
            
            # Passer à l'étape de finalisation
            self.show_step(5)
            
            logger.info("Document confirmé")
            
        except Exception as e:
            logger.error(f"Erreur lors de la confirmation du document: {e}")
            self.show_error(f"Erreur: {str(e)}")
            
    def show_customization(self) -> None:
        """
        Affiche l'étape de personnalisation du document
        """
        try:
            # Nettoyer la zone de contenu
            for widget in self.content_frame.winfo_children():
                widget.destroy()
                
            # Créer un cadre conteneur pour centrer le contenu
            container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Titre
            title = ctk.CTkLabel(
                container,
                text="Personnalisation du document",
                font=("", 24, "bold")
            )
            title.pack(pady=(0, 20))
            
            # Message d'information
            info_label = ctk.CTkLabel(
                container,
                text="Modifiez les variables selon vos besoins :",
                font=("", 14),
                text_color=("gray50", "gray70")
            )
            info_label.pack(pady=(0, 20))
            
            # Zone de modification des variables
            if hasattr(self, 'document_data') and self.document_data and self.document_data.get('variables'):
                # Créer une zone déroulante pour les variables
                variables_scroll = ctk.CTkScrollableFrame(container, height=300, fg_color=("gray95", "gray15"))
                variables_scroll.pack(fill="x", padx=20, pady=10)
                
                # Dictionnaire pour stocker les entrées
                self.variable_entries = {}
                
                # Afficher chaque variable avec un champ de modification
                for var_name, var_info in self.document_data.get('variables', {}).items():
                    var_frame = ctk.CTkFrame(variables_scroll, fg_color="transparent")
                    var_frame.pack(fill="x", padx=10, pady=5)
                    
                    # Nom de la variable
                    var_label = ctk.CTkLabel(
                        var_frame,
                        text=f"{var_name}:",
                        font=("", 12, "bold"),
                        width=150
                    )
                    var_label.pack(side="left")
                    
                    # Description (si disponible)
                    description = var_info.get('description', '') if isinstance(var_info, dict) else ''
                    
                    # Champ de saisie
                    current_value = var_info.get('current_value', '') if isinstance(var_info, dict) else str(var_info)
                    var_entry = ctk.CTkEntry(
                        var_frame,
                        width=400,
                        placeholder_text=description
                    )
                    var_entry.insert(0, current_value)
                    var_entry.pack(side="left", padx=10, fill="x", expand=True)
                    
                    # Stocker l'entrée
                    self.variable_entries[var_name] = var_entry
            else:
                # Message si aucune variable n'est disponible
                no_vars_label = ctk.CTkLabel(
                    container,
                    text="Aucune variable à personnaliser",
                    font=("", 14),
                    text_color="red"
                )
                no_vars_label.pack(pady=30)
            
            # Boutons d'action
            buttons_frame = ctk.CTkFrame(container, fg_color="transparent")
            buttons_frame.pack(pady=20)
            
            save_button = ctk.CTkButton(
                buttons_frame,
                text="Appliquer les modifications",
                command=self._save_customization,
                width=200
            )
            save_button.pack(pady=10)
            
            # Mettre à jour la navigation
            self.update_navigation()
            
            logger.info("Affichage de l'étape de personnalisation")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de l'étape de personnalisation: {e}")
            self.show_error(f"Erreur: {str(e)}")
            
    def _save_customization(self) -> None:
        """
        Sauvegarde les modifications des variables et passe à l'étape de validation
        """
        try:
            # Si les entrées ne sont pas définies, ne rien faire
            if not hasattr(self, 'variable_entries') or not self.variable_entries:
                return
                
            # Récupérer les valeurs des entrées
            for var_name, entry in self.variable_entries.items():
                value = entry.get()
                
                # Mettre à jour la valeur dans document_data
                if hasattr(self, 'document_data') and self.document_data and 'variables' in self.document_data:
                    var_info = self.document_data['variables'].get(var_name)
                    if isinstance(var_info, dict):
                        var_info['current_value'] = value
                    else:
                        self.document_data['variables'][var_name] = value
            
            # Passer à l'étape de validation
            self.show_step(3)
            
            logger.info("Personnalisation sauvegardée")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la personnalisation: {e}")
            self.show_error(f"Erreur: {str(e)}")
            
    def show_finalization(self) -> None:
        """
        Affiche l'étape de finalisation du document
        """
        try:
            # Nettoyer la zone de contenu
            for widget in self.content_frame.winfo_children():
                widget.destroy()
                
            # Créer un cadre conteneur pour centrer le contenu
            container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Titre
            title = ctk.CTkLabel(
                container,
                text="Finalisation du document",
                font=("", 24, "bold")
            )
            title.pack(pady=(0, 20))
            
            # Message de confirmation
            success_frame = ctk.CTkFrame(container, fg_color=("green", "#005000"))
            success_frame.pack(fill="x", padx=20, pady=10)
            
            success_label = ctk.CTkLabel(
                success_frame,
                text="Document créé avec succès !",
                font=("", 16, "bold"),
                text_color="white"
            )
            success_label.pack(pady=10)
            
            # Informations sur le document créé
            if hasattr(self, 'selected_template') and self.selected_template:
                info_frame = ctk.CTkFrame(container, fg_color=("gray95", "gray15"))
                info_frame.pack(fill="x", padx=20, pady=10)
                
                template_name = self.selected_template.get('name', 'Document sans nom')
                
                info_label = ctk.CTkLabel(
                    info_frame,
                    text=f"Document: {template_name}",
                    font=("", 14)
                )
                info_label.pack(pady=10, padx=20, anchor="w")
                
                # Client associé
                if hasattr(self, 'client_info') and self.client_info:
                    client_name = self.client_info.get('nom', '') or self.client_info.get('name', '') or self.client_info.get('société', '') or "Client sans nom"
                    client_label = ctk.CTkLabel(
                        info_frame,
                        text=f"Client: {client_name}",
                        font=("", 14)
                    )
                    client_label.pack(pady=5, padx=20, anchor="w")
            
            # Options de finalisation
            options_frame = ctk.CTkFrame(container)
            options_frame.pack(fill="x", padx=20, pady=20)
            
            options_label = ctk.CTkLabel(
                options_frame,
                text="Que souhaitez-vous faire ?",
                font=("", 16, "bold")
            )
            options_label.pack(pady=10)
            
            # Boutons d'action
            buttons_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
            buttons_frame.pack(pady=10)
            
            # Bouton pour télécharger le document
            download_button = ctk.CTkButton(
                buttons_frame,
                text="Télécharger le document",
                command=self._download_document,
                width=200
            )
            download_button.pack(pady=5)
            
            # Bouton pour voir le document
            view_button = ctk.CTkButton(
                buttons_frame,
                text="Voir le document",
                command=self._view_document,
                width=200
            )
            view_button.pack(pady=5)
            
            # Bouton pour envoyer le document par email
            email_button = ctk.CTkButton(
                buttons_frame,
                text="Envoyer par email",
                command=self._send_email,
                width=200
            )
            email_button.pack(pady=5)
            
            # Bouton pour créer un autre document
            new_button = ctk.CTkButton(
                buttons_frame,
                text="Créer un autre document",
                command=self.reset_process,
                width=200,
                fg_color=("gray80", "gray30"),
                text_color=("gray10", "gray90")
            )
            new_button.pack(pady=5)
            
            # Bouton pour fermer la vue
            close_button = ctk.CTkButton(
                buttons_frame,
                text="Terminer",
                command=self.on_close_button,
                width=200,
                fg_color=("gray80", "gray30"),
                text_color=("gray10", "gray90")
            )
            close_button.pack(pady=5)
            
            # Mettre à jour la navigation
            self.update_navigation()
            
            logger.info("Affichage de l'étape de finalisation")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de l'étape de finalisation: {e}")
            self.show_error(f"Erreur: {str(e)}")
            
    def _download_document(self) -> None:
        """
        Télécharge le document créé
        """
        try:
            # Vérifier que le document a été généré et existe
            if not hasattr(self, 'generated_document_path') or not hasattr(self, 'selected_template'):
                logger.error("Pas de document généré disponible pour le téléchargement")
                self.show_error("Le document n'a pas encore été généré ou n'est pas disponible pour le téléchargement.")
                return
                
            file_path = self.generated_document_path
            
            # Vérifier si le fichier existe
            if not os.path.exists(file_path):
                logger.error(f"Le fichier du document est introuvable: {file_path}")
                self.show_error("Le fichier du document est introuvable.")
                return
                
            # Déterminer l'extension du fichier
            _, ext = os.path.splitext(file_path)
            
            # Ouvrir une boîte de dialogue pour choisir l'emplacement de sauvegarde
            dest_path = filedialog.asksaveasfilename(
                title="Enregistrer le document",
                defaultextension=ext,
                initialfile=os.path.basename(file_path),
                filetypes=[(f"Fichiers {ext.upper()}", f"*{ext}"), ("Tous les fichiers", "*.*")]
            )
            
            if not dest_path:
                return
                
            # Copier le fichier
            shutil.copy2(file_path, dest_path)
            
            logger.info(f"Document téléchargé: {dest_path}")
            self.show_message("Succès", "Document téléchargé avec succès", "info")
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du document: {e}")
            self.show_error(f"Erreur lors du téléchargement: {str(e)}")
            
    def _view_document(self) -> None:
        """
        Ouvre le document pour visualisation
        """
        try:
            # Vérifier que le document a été généré et existe
            if not hasattr(self, 'generated_document_path') or not hasattr(self, 'selected_template'):
                logger.error("Pas de document généré disponible pour la visualisation")
                self.show_error("Le document n'a pas encore été généré ou n'est pas disponible pour la visualisation.")
                return
                
            file_path = self.generated_document_path
            
            # Vérifier si le fichier existe
            if not os.path.exists(file_path):
                logger.error(f"Le fichier du document est introuvable: {file_path}")
                self.show_error("Le fichier du document est introuvable.")
                return
                
            # Ouvrir le fichier avec l'application par défaut du système
            try:
                import subprocess
                
                if os.name == 'nt':  # Windows
                    os.startfile(file_path)
                elif os.name == 'posix':  # macOS ou Linux
                    subprocess.call(('open' if os.uname().sysname == 'Darwin' else 'xdg-open', file_path))
                
                logger.info(f"Document ouvert pour visualisation: {file_path}")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'ouverture du document: {e}")
                self.show_error(f"Erreur lors de l'ouverture du document: {str(e)}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la visualisation du document: {e}")
            self.show_error(f"Erreur: {str(e)}")
            
    def _send_email(self) -> None:
        """
        Envoie le document par email
        """
        try:
            # Implémenter la logique d'envoi par email
            logger.info("Envoi du document par email")
            self.show_error("Cette fonctionnalité n'est pas encore implémentée")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du document par email: {e}")
            self.show_error(f"Erreur: {str(e)}")
    
    def show_message(self, title: str, message: str, message_type: str = "info") -> None:
        """
        Affiche un message dans une boîte de dialogue
        
        Args:
            title: Titre de la boîte de dialogue
            message: Message à afficher
            message_type: Type de message (info, error, warning)
        """
        try:
            # Utiliser DialogUtils si disponible
            if 'DialogUtils' in globals():
                DialogUtils.show_message(self.parent, title, message, message_type)
            else:
                # Fallback avec messagebox standard
                from tkinter import messagebox
                
                if message_type == "error":
                    messagebox.showerror(title, message)
                elif message_type == "warning":
                    messagebox.showwarning(title, message)
                else:
                    messagebox.showinfo(title, message)
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du message: {e}")
            # Dernier recours
            from tkinter import messagebox
            messagebox.showerror("Erreur", message)

    def _reset_client_selection(self) -> None:
        """
        Réinitialise la sélection du client et affiche à nouveau le formulaire de recherche
        """
        try:
            # Réinitialiser la sélection
            self.client_selected = False
            self.client_info = {}
            
            # Afficher à nouveau la recherche
            self.show_client_form()
            
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation de la sélection du client: {e}")
            self.show_error(f"Erreur: {str(e)}")
            
    def show(self) -> None:
        """
        Affiche la vue
        """
        # S'assurer que le conteneur principal est visible
        self.frame.pack(fill="both", expand=True)
        # Réinitialiser l'état si nécessaire
        self.current_step = 0
        # Afficher l'étape initiale
        self.show_step(0)
        logger.info("Vue document_creator affichée")

    def hide(self) -> None:
        """
        Cache la vue
        """
        # Masquer le conteneur principal
        self.frame.pack_forget()
        logger.info("Vue document_creator masquée")