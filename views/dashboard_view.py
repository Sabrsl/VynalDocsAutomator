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
        
        # Initialiser les actions rapides avec des fonctions par défaut.
        # Ces callbacks seront redéfinis par l'AppController.
        self.new_document = lambda: logger.info("Action: Nouveau document (non implémentée)")
        self.add_client = lambda: logger.info("Action: Ajouter un client (non implémentée)")
        self.new_template = lambda: logger.info("Action: Créer un modèle (non implémentée)")
        
        # Cadre principal de la vue
        self.frame = ctk.CTkFrame(parent)
        
        # Création de l'interface
        self.create_widgets()
        
        logger.info("DashboardView initialisée")
    
    def create_widgets(self):
        """
        Crée les widgets du tableau de bord.
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
        
        # Configuration d'une grille à 3 colonnes
        self.cards_frame.columnconfigure(0, weight=1)
        self.cards_frame.columnconfigure(1, weight=1)
        self.cards_frame.columnconfigure(2, weight=1)
        
        # Carte des clients
        self.client_card = self.create_stat_card(self.cards_frame, "Clients", "👥", "0", 0, 0)
        
        # Carte des modèles
        self.template_card = self.create_stat_card(self.cards_frame, "Modèles", "📋", "0", 0, 1)
        
        # Carte des documents
        self.document_card = self.create_stat_card(self.cards_frame, "Documents", "📄", "0", 0, 2)
        
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
        
        # Créer le bouton "Nouveau document"
        self.new_doc_btn = ctk.CTkButton(
            self.action_buttons_frame,
            text="Nouveau document",
            width=150,
            command=self._new_document_callback
        )
        self.new_doc_btn.pack(side=ctk.LEFT, padx=5, pady=5)
        
        # Créer le bouton "Ajouter un client"
        self.add_client_btn = ctk.CTkButton(
            self.action_buttons_frame,
            text="Ajouter un client",
            width=150,
            command=self._add_client_callback
        )
        self.add_client_btn.pack(side=ctk.LEFT, padx=5, pady=5)
        
        # Créer le bouton "Créer un modèle"
        self.new_template_btn = ctk.CTkButton(
            self.action_buttons_frame,
            text="Créer un modèle",
            width=150,
            command=self._new_template_callback
        )
        self.new_template_btn.pack(side=ctk.LEFT, padx=5, pady=5)
        
        # Cadre pour les activités récentes
        self.activities_frame = ctk.CTkFrame(self.frame)
        self.activities_frame.pack(fill=ctk.BOTH, expand=True, pady=10)
        
        # Titre de la section
        ctk.CTkLabel(
            self.activities_frame,
            text="Activités récentes",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Zone défilante pour les activités
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
    
    def _new_document_callback(self):
        """
        Fonction callback pour le bouton "Nouveau document"
        Utilise la fonction définie par le contrôleur
        """
        try:
            if callable(self.new_document):
                logger.info("Appel de la fonction new_document depuis le tableau de bord")
                self.new_document()
            else:
                logger.error("La fonction new_document n'est pas définie ou n'est pas callable")
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à new_document: {e}")
    
    def _add_client_callback(self):
        """
        Fonction callback pour le bouton "Ajouter un client"
        Utilise la fonction définie par le contrôleur
        """
        try:
            if callable(self.add_client):
                logger.info("Appel de la fonction add_client depuis le tableau de bord")
                self.add_client()
            else:
                logger.error("La fonction add_client n'est pas définie ou n'est pas callable")
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à add_client: {e}")
    
    def _new_template_callback(self):
        """
        Fonction callback pour le bouton "Créer un modèle"
        Utilise la fonction définie par le contrôleur
        """
        try:
            if callable(self.new_template):
                logger.info("Appel de la fonction new_template depuis le tableau de bord")
                self.new_template()
            else:
                logger.error("La fonction new_template n'est pas définie ou n'est pas callable")
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à new_template: {e}")
    
    def create_stat_card(self, parent, title, icon, value, row, col):
        """
        Crée une carte de statistique.

        Args:
            parent: Widget parent.
            title: Titre de la carte.
            icon: Icône à afficher.
            value: Valeur à afficher.
            row: Ligne dans la grille.
            col: Colonne dans la grille.
        
        Returns:
            dict: Dictionnaire contenant les widgets de la carte.
        """
        card = ctk.CTkFrame(parent)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=30))
        icon_label.pack(pady=(10, 5))
        
        value_label = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=24, weight="bold"))
        value_label.pack(pady=5)
        
        title_label = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14))
        title_label.pack(pady=(5, 10))
        
        return {"frame": card, "icon": icon_label, "value": value_label, "title": title_label}
    
    def create_activity_item(self, parent, activity):
        """
        Crée un élément d'activité.

        Args:
            parent: Widget parent.
            activity: Dictionnaire contenant les données d'activité.
        
        Returns:
            ctk.CTkFrame: Cadre contenant l'élément d'activité.
        """
        item = ctk.CTkFrame(parent, fg_color="transparent")
        item.pack(fill=ctk.X, pady=2)
        
        icons = {
            "client": "👥",
            "document": "📄",
            "template": "📋",
            "settings": "⚙️"
        }
        
        try:
            timestamp = datetime.fromisoformat(activity["timestamp"])
            formatted_time = timestamp.strftime("%d/%m/%Y %H:%M")
        except Exception:
            formatted_time = activity.get("timestamp", "")
        
        icon = icons.get(activity.get("type"), "ℹ️")
        
        description = ctk.CTkLabel(item, text=f"{icon} {activity.get('description', '')}", anchor="w", font=ctk.CTkFont(size=12))
        description.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)
        
        time_label = ctk.CTkLabel(item, text=formatted_time, font=ctk.CTkFont(size=10), text_color="gray")
        time_label.pack(side=ctk.RIGHT, padx=5)
        
        return item
    
    def update_view(self):
        """
        Met à jour la vue avec les données actuelles.
        """
        # Mettre à jour les statistiques
        self.client_card["value"].configure(text=str(len(self.model.clients)))
        self.template_card["value"].configure(text=str(len(self.model.templates)))
        self.document_card["value"].configure(text=str(len(self.model.documents)))
        
        # Mettre à jour la liste des activités récentes
        for widget in self.activities_list_frame.winfo_children():
            if widget != self.no_activities_label:
                widget.destroy()
        
        activities = self.model.get_recent_activities()
        if activities:
            self.no_activities_label.pack_forget()
            for activity in activities:
                self.create_activity_item(self.activities_list_frame, activity)
        else:
            self.no_activities_label.pack(pady=20)
        
        logger.info("DashboardView mise à jour")
    
    def show(self):
        """
        Affiche la vue.
        """
        self.frame.pack(fill=ctk.BOTH, expand=True)
        self.update_view()
    
    def hide(self):
        """
        Masque la vue.
        """
        self.frame.pack_forget()