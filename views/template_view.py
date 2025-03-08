#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue de gestion des modèles pour l'application Vynal Docs Automator
"""

import os
import logging
import customtkinter as ctk

logger = logging.getLogger("VynalDocsAutomator.TemplateView")

class TemplateView:
    """
    Vue de gestion des modèles
    Permet de visualiser, créer et gérer des modèles de documents
    """
    
    def __init__(self, parent, app_model):
        """
        Initialise la vue de gestion des modèles
        
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
        
        logger.info("TemplateView initialisée")
    
    def create_widgets(self):
        """
        Crée les widgets de la vue
        """
        # Barre d'outils
        self.toolbar = ctk.CTkFrame(self.frame)
        self.toolbar.pack(fill=ctk.X, pady=10)
        
        # Bouton Nouveau modèle
        self.new_template_btn = ctk.CTkButton(
            self.toolbar,
            text="+ Nouveau modèle",
            command=self.new_template
        )
        self.new_template_btn.pack(side=ctk.LEFT, padx=10)
        
        # Bouton Importer
        self.import_btn = ctk.CTkButton(
            self.toolbar,
            text="Importer",
            command=self.import_template
        )
        self.import_btn.pack(side=ctk.LEFT, padx=10)
        
        # Recherche
        self.search_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.search_frame.pack(side=ctk.RIGHT, padx=10)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.filter_templates())
        
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Rechercher un modèle...",
            width=200,
            textvariable=self.search_var
        )
        self.search_entry.pack(side=ctk.LEFT)
        
        # Zone principale de contenu
        self.content_frame = ctk.CTkScrollableFrame(self.frame)
        self.content_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Message si aucun modèle
        self.no_templates_label = ctk.CTkLabel(
            self.content_frame,
            text="Aucun modèle disponible. Créez ou importez un modèle pour commencer.",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color="gray"
        )
        self.no_templates_label.pack(pady=20)
        
        # Grille de modèles (contiendra les cartes de modèles)
        self.templates_grid = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Configurer la grille pour avoir 3 colonnes
        for i in range(3):
            self.templates_grid.columnconfigure(i, weight=1)
    
    def update_view(self):
        """
        Met à jour la vue avec les données actuelles
        """
        # Récupérer tous les modèles
        templates = self.model.templates
        
        # Afficher ou masquer le message "Aucun modèle"
        if templates:
            self.no_templates_label.pack_forget()
            self.templates_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
            
            # Appliquer les filtres
            filtered_templates = self.apply_filters(templates)
            
            # Nettoyer la grille
            for widget in self.templates_grid.winfo_children():
                widget.destroy()
            
            # Remplir la grille avec les modèles filtrés
            if filtered_templates:
                row, col = 0, 0
                for template in filtered_templates:
                    self.create_template_card(template, row, col)
                    col += 1
                    if col >= 3:  # 3 cartes par ligne
                        col = 0
                        row += 1
            else:
                # Aucun modèle après filtrage
                ctk.CTkLabel(
                    self.templates_grid,
                    text="Aucun modèle ne correspond aux critères de recherche.",
                    font=ctk.CTkFont(size=12),
                    fg_color="transparent",
                    text_color="gray"
                ).grid(row=0, column=0, columnspan=3, pady=20)
        else:
            self.templates_grid.pack_forget()
            self.no_templates_label.pack(pady=20)
        
        logger.info("TemplateView mise à jour")
    
    def create_template_card(self, template, row, col):
        """
        Crée une carte pour afficher un modèle
        
        Args:
            template: Données du modèle
            row: Ligne dans la grille
            col: Colonne dans la grille
        """
        # Cadre de la carte
        card = ctk.CTkFrame(self.templates_grid)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Icône selon le type
        template_type = template.get("type", "")
        icon = "📋"  # Par défaut
        
        if template_type == "contrat":
            icon = "📝"
        elif template_type == "facture":
            icon = "💰"
        elif template_type == "proposition":
            icon = "📊"
        elif template_type == "rapport":
            icon = "📈"
        
        # En-tête avec icône et type
        header = ctk.CTkFrame(card, fg_color=("gray90", "gray20"), corner_radius=6)
        header.pack(fill=ctk.X, padx=5, pady=5)
        
        ctk.CTkLabel(
            header,
            text=f"{icon} {template_type.capitalize() if template_type else 'Modèle'}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side=ctk.LEFT, padx=10, pady=5)
        
        # Titre du modèle
        ctk.CTkLabel(
            card,
            text=template.get("name", "Sans nom"),
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=200
        ).pack(fill=ctk.X, padx=10, pady=5)
        
        # Description
        description = template.get("description", "")
        if description:
            ctk.CTkLabel(
                card,
                text=description,
                font=ctk.CTkFont(size=12),
                wraplength=200,
                text_color="gray",
                justify="left"
            ).pack(fill=ctk.X, padx=10, pady=5)
        
        # Variables disponibles
        variables = template.get("variables", [])
        if variables:
            variables_text = ", ".join(variables[:3])
            if len(variables) > 3:
                variables_text += f" et {len(variables) - 3} autres..."
            
            ctk.CTkLabel(
                card,
                text=f"Variables: {variables_text}",
                font=ctk.CTkFont(size=10),
                wraplength=200,
                text_color="gray"
            ).pack(fill=ctk.X, padx=10, pady=2)
        
        # Boutons d'action
        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.pack(fill=ctk.X, padx=10, pady=10)
        
        # Bouton Éditer
        ctk.CTkButton(
            actions_frame,
            text="Éditer",
            width=80,
            height=25,
            command=lambda tid=template.get("id"): self.edit_template(tid)
        ).pack(side=ctk.LEFT, padx=2)
        
        # Bouton Utiliser
        ctk.CTkButton(
            actions_frame,
            text="Utiliser",
            width=80,
            height=25,
            command=lambda tid=template.get("id"): self.use_template(tid)
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
    
    def apply_filters(self, templates):
        """
        Applique les filtres aux modèles
        
        Args:
            templates: Liste des modèles à filtrer
            
        Returns:
            list: Modèles filtrés
        """
        filtered = templates
        
        # Filtre par recherche
        search_text = self.search_var.get().lower()
        if search_text:
            filtered = [t for t in filtered if 
                        search_text in t.get("name", "").lower() or 
                        search_text in t.get("description", "").lower() or
                        search_text in t.get("type", "").lower()]
        
        return filtered
    
    def filter_templates(self, *args):
        """
        Filtre les modèles selon les critères de recherche
        """
        self.update_view()
    
    def new_template(self):
        """
        Crée un nouveau modèle
        """
        # Cette méthode sera implémentée plus tard
        logger.info("Action: Nouveau modèle (non implémentée)")
    
    def edit_template(self, template_id):
        """
        Édite un modèle existant
        
        Args:
            template_id: ID du modèle à éditer
        """
        # Cette méthode sera implémentée plus tard
        logger.info(f"Action: Éditer le modèle {template_id} (non implémentée)")
    
    def use_template(self, template_id):
        """
        Utilise un modèle pour créer un nouveau document
        
        Args:
            template_id: ID du modèle à utiliser
        """
        # Cette méthode sera implémentée plus tard
        logger.info(f"Action: Utiliser le modèle {template_id} (non implémentée)")
    
    def import_template(self):
        """
        Importe un modèle depuis un fichier externe
        """
        # Cette méthode sera implémentée plus tard
        logger.info("Action: Importer un modèle (non implémentée)")