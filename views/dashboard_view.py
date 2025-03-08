#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue du tableau de bord pour l'application Vynal Docs Automator
"""

import logging
import customtkinter as ctk
from datetime import datetime

logger = logging.getLogger("VynalDocsAutomator.DashboardView")

class DashboardView:
    """
    Vue du tableau de bord
    Affiche un résumé des données et des activités récentes
    """
    
    def __init__(self, parent, app_model):
        """
        Initialise la vue du tableau de bord
        
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
        
        logger.info("DashboardView initialisée")
    
    def create_widgets(self):
        """
        Crée les widgets du tableau de bord
        """
        # Cadre pour les statistiques
        self.stats_frame = ctk.CTkFrame(self.frame)
        self.stats_frame.pack(fill=ctk.X, pady=10)
        
        # Titre de la section
        ctk.CTkLabel(
            self.stats_frame,
            text="Vue d'ensemble",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Cartes de statistiques
        self.cards_frame = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        self.cards_frame.pack(fill=ctk.X, padx=10, pady=5)
        
        # Configurer la grille pour les cartes
        self.cards_frame.columnconfigure(0, weight=1)
        self.cards_frame.columnconfigure(1, weight=1)
        self.cards_frame.columnconfigure(2, weight=1)
        
        # Carte des clients
        self.client_card = self.create_stat_card(
            self.cards_frame,
            "Clients",
            "👥",
            "0",
            0, 0
        )
        
        # Carte des modèles
        self.template_card = self.create_stat_card(
            self.cards_frame,
            "Modèles",
            "📋",
            "0",
            0, 1
        )
        
        # Carte des documents
        self.document_card = self.create_stat_card(
            self.cards_frame,
            "Documents",
            "📄",
            "0",
            0, 2
        )
        
        # Cadre pour les actions rapides
        self.actions_frame = ctk.CTkFrame(self.frame)
        self.actions_frame.pack(fill=ctk.X, pady=10)
        
        # Titre de la section
        ctk.CTkLabel(
            self.actions_frame,
            text="Actions rapides",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Boutons d'actions rapides
        self.action_buttons_frame = ctk.CTkFrame(self.actions_frame, fg_color="transparent")
        self.action_buttons_frame.pack(fill=ctk.X, padx=10, pady=5)
        
        # Créer un document
        ctk.CTkButton(
            self.action_buttons_frame,
            text="Nouveau document",
            width=200,
            command=self.new_document
        ).pack(side=ctk.LEFT, padx=5, pady=5)
        
        # Ajouter un client
        ctk.CTkButton(
            self.action_buttons_frame,
            text="Ajouter un client",
            width=200,
            command=self.add_client
        ).pack(side=ctk.LEFT, padx=5, pady=5)
        
        # Nouveau modèle
        ctk.CTkButton(
            self.action_buttons_frame,
            text="Créer un modèle",
            width=200,
            command=self.new_template
        ).pack(side=ctk.LEFT, padx=5, pady=5)
        
        # Cadre pour les activités récentes
        self.activities_frame = ctk.CTkFrame(self.frame)
        self.activities_frame.pack(fill=ctk.BOTH, expand=True, pady=10)
        
        # Titre de la section
        ctk.CTkLabel(
            self.activities_frame,
            text="Activités récentes",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Liste des activités
        self.activities_list_frame = ctk.CTkScrollableFrame(self.activities_frame)
        self.activities_list_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        
        # Message si aucune activité
        self.no_activities_label = ctk.CTkLabel(
            self.activities_list_frame,
            text="Aucune activité récente",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color="gray"
        )
        self.no_activities_label.pack(pady=20)
    
    def create_stat_card(self, parent, title, icon, value, row, col):
        """
        Crée une carte de statistique
        
        Args:
            parent: Widget parent
            title: Titre de la carte
            icon: Icône à afficher
            value: Valeur à afficher
            row: Ligne dans la grille
            col: Colonne dans la grille
            
        Returns:
            dict: Dictionnaire contenant les widgets de la carte
        """
        card = ctk.CTkFrame(parent)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # Icône
        icon_label = ctk.CTkLabel(
            card,
            text=icon,
            font=ctk.CTkFont(size=30)
        )
        icon_label.pack(pady=(10, 5))
        
        # Valeur
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        value_label.pack(pady=5)
        
        # Titre
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=14)
        )
        title_label.pack(pady=(5, 10))
        
        return {
            "frame": card,
            "icon": icon_label,
            "value": value_label,
            "title": title_label
        }
    
    def create_activity_item(self, parent, activity):
        """
        Crée un élément d'activité
        
        Args:
            parent: Widget parent
            activity: Données de l'activité
            
        Returns:
            ctk.CTkFrame: Cadre contenant l'élément d'activité
        """
        # Cadre pour l'activité
        item = ctk.CTkFrame(parent, fg_color="transparent")
        item.pack(fill=ctk.X, pady=2)
        
        # Icônes par type d'activité
        icons = {
            "client": "👥",
            "document": "📄",
            "template": "📋",
            "settings": "⚙️"
        }
        
        # Horodatage
        try:
            timestamp = datetime.fromisoformat(activity["timestamp"])
            formatted_time = timestamp.strftime("%d/%m/%Y %H:%M")
        except:
            formatted_time = activity["timestamp"]
        
        # Icône du type d'activité
        icon = icons.get(activity["type"], "ℹ️")
        
        # Description avec icône
        description = ctk.CTkLabel(
            item,
            text=f"{icon} {activity['description']}",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        description.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)
        
        # Horodatage
        time_label = ctk.CTkLabel(
            item,
            text=formatted_time,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        time_label.pack(side=ctk.RIGHT, padx=5)
        
        return item
    
    def update_view(self):
        """
        Met à jour la vue avec les données actuelles
        """
        # Mettre à jour les statistiques
        self.client_card["value"].configure(text=str(len(self.model.clients)))
        self.template_card["value"].configure(text=str(len(self.model.templates)))
        self.document_card["value"].configure(text=str(len(self.model.documents)))
        
        # Mettre à jour les activités récentes
        # D'abord, supprimer toutes les activités existantes
        for widget in self.activities_list_frame.winfo_children():
            if widget != self.no_activities_label:
                widget.destroy()
        
        # Récupérer les activités récentes
        activities = self.model.get_recent_activities()
        
        # Afficher ou masquer le message "Aucune activité"
        if activities:
            self.no_activities_label.pack_forget()
            
            # Créer les éléments d'activité
            for activity in activities:
                self.create_activity_item(self.activities_list_frame, activity)
        else:
            self.no_activities_label.pack(pady=20)
        
        logger.info("DashboardView mise à jour")
    
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
    
    def new_document(self):
        """
        Action pour créer un nouveau document
        """
        # Cette méthode sera implémentée lorsque le contrôleur de documents sera créé
        logger.info("Action: Nouveau document (non implémentée)")
    
    def add_client(self):
        """
        Action pour ajouter un client
        """
        # Cette méthode sera implémentée lorsque le contrôleur de clients sera créé
        logger.info("Action: Ajouter un client (non implémentée)")
    
    def new_template(self):
        """
        Action pour créer un nouveau modèle
        """
        # Cette méthode sera implémentée lorsque le contrôleur de modèles sera créé
        logger.info("Action: Créer un modèle (non implémentée)")