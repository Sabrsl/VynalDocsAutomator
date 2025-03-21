#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue du tableau de bord pour l'application Vynal Docs Automator
"""

import logging
from typing import Callable, Dict, List, Optional, Any
import customtkinter as ctk
from datetime import datetime
import os
import sys
from PIL import Image

logger = logging.getLogger("VynalDocsAutomator.DashboardView")

class DashboardView:
    """
    Vue du tableau de bord
    Affiche un résumé des données et des activités récentes
    """
    
    def __init__(self, parent: ctk.CTk, app_model: Any) -> None:
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
        self.new_document: Callable[[], None] = lambda: logger.info("Action: Nouveau document (non implémentée)")
        self.add_client: Callable[[], None] = lambda: logger.info("Action: Ajouter un client (non implémentée)")
        self.new_template: Callable[[], None] = lambda: logger.info("Action: Créer un modèle (non implémentée)")
        self.process_document: Callable[[], None] = lambda: logger.info("Action: Nouveau document (non implémentée)")
        
        # Charger les icônes
        self.load_icons()
        
        # Cadre principal de la vue avec bordure arrondie
        self.frame = ctk.CTkFrame(parent, corner_radius=10)
        
        # Création de l'interface
        self.create_widgets()
        
        logger.info("DashboardView initialisée")
    
    def load_icons(self) -> None:
        """
        Charge les icônes pour l'interface utilisateur
        """
        try:
            # Chemin du répertoire des icônes (à ajuster selon votre structure de projet)
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons")
            
            # Si le répertoire des icônes n'existe pas, utiliser des icônes par défaut
            if not os.path.exists(icon_path):
                logger.warning(f"Répertoire d'icônes non trouvé: {icon_path}")
                self.icons = {
                    "client": "👥",
                    "document": "📄",
                    "template": "📋",
                    "settings": "⚙️"
                }
                self.use_text_icons = True
                return
                
            # Taille des icônes pour les cartes de statistiques
            icon_size = (64, 64)
            
            # Charger les icônes
            self.icons = {}
            
            # Icône clients
            try:
                client_icon_path = os.path.join(icon_path, "users.png")
                if os.path.exists(client_icon_path):
                    self.icons["client"] = ctk.CTkImage(
                        light_image=Image.open(client_icon_path),
                        dark_image=Image.open(client_icon_path),
                        size=icon_size
                    )
                else:
                    self.icons["client"] = "👥"
            except Exception as e:
                logger.warning(f"Erreur lors du chargement de l'icône clients: {e}")
                self.icons["client"] = "👥"
                
            # Icône documents
            try:
                doc_icon_path = os.path.join(icon_path, "document.png")
                if os.path.exists(doc_icon_path):
                    self.icons["document"] = ctk.CTkImage(
                        light_image=Image.open(doc_icon_path),
                        dark_image=Image.open(doc_icon_path),
                        size=icon_size
                    )
                else:
                    self.icons["document"] = "📄"
            except Exception as e:
                logger.warning(f"Erreur lors du chargement de l'icône documents: {e}")
                self.icons["document"] = "📄"
                
            # Icône modèles
            try:
                template_icon_path = os.path.join(icon_path, "template.png")
                if os.path.exists(template_icon_path):
                    self.icons["template"] = ctk.CTkImage(
                        light_image=Image.open(template_icon_path),
                        dark_image=Image.open(template_icon_path),
                        size=icon_size
                    )
                else:
                    self.icons["template"] = "📋"
            except Exception as e:
                logger.warning(f"Erreur lors du chargement de l'icône modèles: {e}")
                self.icons["template"] = "📋"
                
            # Icône paramètres
            self.icons["settings"] = "⚙️"
            
            # Utiliser des icônes d'image au lieu de texte
            self.use_text_icons = not all(
                isinstance(self.icons[key], ctk.CTkImage) 
                for key in ["client", "document", "template"]
            )
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement des icônes: {e}")
            # Fallback sur les icônes texte
            self.icons = {
                "client": "👥",
                "document": "📄",
                "template": "📋",
                "settings": "⚙️"
            }
            self.use_text_icons = True
    
    def create_widgets(self) -> None:
        """
        Crée les widgets du tableau de bord.
        """
        # Cadre pour les statistiques avec bordure complètement arrondie
        self.stats_frame = ctk.CTkFrame(self.frame, corner_radius=10)
        self.stats_frame.pack(fill=ctk.X, pady=10, padx=10)  # Ajout de padx pour éviter le débordement
        
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
        self.client_card = self.create_stat_card(self.cards_frame, "Clients", self.icons["client"], "0", 0, 0)
        
        # Carte des modèles
        self.template_card = self.create_stat_card(self.cards_frame, "Modèles", self.icons["template"], "0", 0, 1)
        
        # Carte des documents
        self.document_card = self.create_stat_card(self.cards_frame, "Documents", self.icons["document"], "0", 0, 2)
        
        # Cadre pour les actions rapides
        self.actions_frame = ctk.CTkFrame(self.frame, corner_radius=10)
        self.actions_frame.pack(fill=ctk.X, pady=10, padx=10)  # Ajout de padx pour éviter le débordement
        
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
        
        # Créer le bouton "Traiter un document"
        self.process_doc_btn = ctk.CTkButton(
            self.action_buttons_frame,
            text="Traiter un document",
            width=150,
            command=self._process_document_callback
        )
        self.process_doc_btn.pack(side=ctk.LEFT, padx=5, pady=5)
        
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
        self.activities_frame = ctk.CTkFrame(self.frame, corner_radius=10)
        self.activities_frame.pack(fill=ctk.BOTH, expand=True, pady=10, padx=10)  # Ajout de padx pour éviter le débordement
        
        # Titre de la section
        ctk.CTkLabel(
            self.activities_frame,
            text="Activités récentes",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        # Zone défilante pour les activités avec coin arrondis
        self.activities_list_frame = ctk.CTkScrollableFrame(self.activities_frame, corner_radius=8)
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
    
    def _new_document_callback(self) -> None:
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
    
    def _add_client_callback(self) -> None:
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
    
    def _new_template_callback(self) -> None:
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
    
    def _process_document_callback(self) -> None:
        """
        Fonction callback pour le bouton "Traiter un document"
        Utilise la fonction définie par le contrôleur
        """
        try:
            if callable(self.process_document):
                logger.info("Appel de la fonction process_document depuis le tableau de bord")
                self.process_document()
            else:
                logger.error("La fonction process_document n'est pas définie ou n'est pas callable")
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à process_document: {e}")
    
    def create_stat_card(
            self,
            parent: ctk.CTkFrame,
            title: str,
            icon,  # Peut être une chaîne ou CTkImage
            value: str,
            row: int,
            col: int
    ) -> Dict[str, ctk.CTkBaseClass]:
        """
        Crée une carte de statistique.

        Args:
            parent: Widget parent.
            title: Titre de la carte.
            icon: Icône à afficher (texte ou CTkImage).
            value: Valeur à afficher.
            row: Ligne dans la grille.
            col: Colonne dans la grille.
        
        Returns:
            dict: Dictionnaire contenant les widgets de la carte.
        """
        card = ctk.CTkFrame(parent, corner_radius=8)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # Créer un label pour l'icône, avec gestion des deux types (texte ou image)
        if isinstance(icon, ctk.CTkImage):
            icon_label = ctk.CTkLabel(card, text="", image=icon)
        else:
            icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=30))
        
        icon_label.pack(pady=(10, 5))
        
        value_label = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=24, weight="bold"))
        value_label.pack(pady=5)
        
        title_label = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14))
        title_label.pack(pady=(5, 10))
        
        return {"frame": card, "icon": icon_label, "value": value_label, "title": title_label}
    
    def create_activity_item(
            self,
            parent: ctk.CTkScrollableFrame,
            activity: Dict[str, Any]
    ) -> ctk.CTkFrame:
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
        
        # Utiliser les icônes modernes ou emoji fallback
        activity_type = activity.get("type", "")
        if activity_type in self.icons:
            icon = self.icons.get(activity_type, "ℹ️")
        else:
            icons = {
                "client": "👥",
                "document": "📄",
                "template": "📋",
                "settings": "⚙️"
            }
            icon = icons.get(activity_type, "ℹ️")
        
        try:
            timestamp = datetime.fromisoformat(activity["timestamp"])
            formatted_time = timestamp.strftime("%d/%m/%Y %H:%M")
        except (ValueError, KeyError, TypeError):
            formatted_time = activity.get("timestamp", "")
        
        # Si l'icône est une image, utiliser un autre layout
        if isinstance(icon, ctk.CTkImage):
            # Créer un frame pour contenir l'icône et la description
            content_frame = ctk.CTkFrame(item, fg_color="transparent")
            content_frame.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
            
            # Icône plus petite pour les éléments d'activité
            small_icon = ctk.CTkImage(
                light_image=icon._light_image,
                dark_image=icon._dark_image,
                size=(20, 20)
            )
            
            icon_label = ctk.CTkLabel(content_frame, text="", image=small_icon)
            icon_label.pack(side=ctk.LEFT, padx=5)
            
            description = ctk.CTkLabel(
                content_frame, 
                text=activity.get('description', ''), 
                anchor="w", 
                font=ctk.CTkFont(size=12)
            )
            description.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
        else:
            # Version texte/emoji
            description = ctk.CTkLabel(
                item, 
                text=f"{icon} {activity.get('description', '')}", 
                anchor="w", 
                font=ctk.CTkFont(size=12)
            )
            description.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)
        
        time_label = ctk.CTkLabel(
            item, 
            text=formatted_time, 
            font=ctk.CTkFont(size=10), 
            text_color="gray"
        )
        time_label.pack(side=ctk.RIGHT, padx=5)
        
        return item
    
    def update_view(self) -> None:
        """
        Met à jour la vue avec les données actuelles.
        """
        # Mettre à jour les statistiques
        clients_count = len(getattr(self.model, "clients", []))
        templates_count = len(getattr(self.model, "templates", []))
        documents_count = len(getattr(self.model, "documents", []))
        
        self.client_card["value"].configure(text=str(clients_count))
        self.template_card["value"].configure(text=str(templates_count))
        self.document_card["value"].configure(text=str(documents_count))
        
        # Mettre à jour la liste des activités récentes
        for widget in self.activities_list_frame.winfo_children():
            if widget != self.no_activities_label:
                widget.destroy()
        
        activities = []
        try:
            activities = self.model.get_recent_activities()
        except AttributeError:
            logger.warning("La méthode get_recent_activities n'existe pas dans le modèle")
        
        if activities:
            self.no_activities_label.pack_forget()
            for activity in activities:
                self.create_activity_item(self.activities_list_frame, activity)
        else:
            self.no_activities_label.pack(pady=20)
        
        logger.info("DashboardView mise à jour")
    
    def show(self) -> None:
        """
        Affiche la vue et s'assure qu'elle est complètement initialisée.
        """
        # S'assurer que le tableau de bord est complètement initialisé
        self.frame.pack(fill=ctk.BOTH, expand=True)
        
        # Mettre à jour les données
        self.update_view()
        
        # Forcer la mise à jour de l'interface
        self.frame.update()
        
        logger.info("DashboardView affichée et initialisée")
    
    def hide(self) -> None:
        """
        Masque la vue.
        """
        self.frame.pack_forget()