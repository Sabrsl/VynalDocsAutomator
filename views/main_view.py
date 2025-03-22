#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue principale de l'application Vynal Docs Automator
"""

import os
import logging
import customtkinter as ctk
from PIL import Image, ImageTk
import json
import tkinter as tk
import hashlib
from datetime import datetime

# Importation des vues
from views.dashboard_view import DashboardView
from views.client_view import ClientView
from views.document_view import DocumentView
from views.template_view import TemplateView
from views.settings_view import SettingsView
from views.chat_ai_view import ChatAIView

# Importer le moniteur d'activité
from utils.activity_monitor import ActivityMonitor

logger = logging.getLogger("VynalDocsAutomator.MainView")

class MainView:
    """
    Vue principale de l'application
    Gère l'interface utilisateur globale et la navigation entre les différentes vues
    """
    
    def __init__(self, root, app_model, on_ready=None):
        """
        Initialise la vue principale
        
        Args:
            root: Fenêtre principale CTk
            app_model: Modèle de l'application
            on_ready: Callback appelé lorsque l'interface est prête
        """
        self.root = root
        self.model = app_model
        self.on_ready = on_ready
        
        # Initialiser les trackers avant tout
        from utils.usage_tracker import UsageTracker
        self.usage_tracker = UsageTracker()
        
        # Configurer la fenêtre principale
        self.root.title(self.model.config.get("app.name", "Vynal Docs Automator"))
        
        # Récupérer le thème des préférences utilisateur ou de la configuration globale
        user_theme = None
        if self.usage_tracker.is_user_registered():
            try:
                user_data = self.usage_tracker.get_user_data()
                if isinstance(user_data, dict) and "theme" in user_data:
                    user_theme = user_data["theme"].lower()
            except Exception as e:
                logger.warning(f"Erreur lors de la lecture des préférences utilisateur: {e}")
        
        # Utiliser le thème utilisateur ou la configuration globale
        theme = user_theme if user_theme else self.model.config.get("app.theme", "dark").lower()
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")
        
        # Créer le cadre principal
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=ctk.BOTH, expand=True)
        
        # Initialiser les dictionnaires de widgets
        self.views = {}
        self.nav_buttons = {}
        
        # Créer l'interface
        self._create_widgets()
        
        # Initialiser le moniteur d'activité
        self.activity_monitor = None
        self._setup_activity_monitor()
        
        # Configurer les événements pour détecter l'activité
        self._setup_activity_events()
        
        logger.info("Vue principale initialisée")
    
    def _create_widgets(self):
        """
        Crée la barre latérale et le contenu principal
        """
        # Créer la barre latérale et le contenu principal
        try:
            self.create_sidebar()
            self.create_content_area()
            
            # Créer les différentes vues
            self.create_views()
            
            # Afficher la vue par défaut (tableau de bord)
            self.show_view("dashboard")
            
            logger.info("Vue dashboard affichée")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la vue principale: {e}")
            # Afficher un message d'erreur à l'utilisateur
            self.root.after(100, lambda: self.show_message(
                "Erreur d'initialisation", 
                f"Une erreur est survenue lors de l'initialisation de l'application: {e}",
                "error"
            ))

    def create_sidebar(self):
        """
        Crée la barre latérale avec le menu de navigation
        """
        # Cadre de la barre latérale
        self.sidebar = ctk.CTkFrame(self.main_frame, width=200, corner_radius=0)
        self.sidebar.pack(side=ctk.LEFT, fill=ctk.Y, padx=0, pady=0)
        self.sidebar.pack_propagate(False)  # Empêcher le redimensionnement
        
        # Logo et titre
        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.pack(side=ctk.TOP, fill=ctk.X, padx=20, pady=20)
        
        # Charger le logo s'il existe
        logo_path = self.model.config.get("app.company_logo", "")
        try:
            # Utiliser l'image du logo si elle existe, sinon créer un placeholder
            if logo_path and os.path.exists(logo_path):
                logo_image = Image.open(logo_path)
                logo_image = logo_image.resize((150, 70), Image.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_image)
                
                self.logo_label = ctk.CTkLabel(self.logo_frame, image=logo_photo, text="")
                self.logo_label.image = logo_photo  # Garder une référence
                self.logo_label.pack(side=ctk.TOP, pady=5)
            else:
                # Créer une image de placeholder
                logger.info("Logo non trouvé, utilisation d'un texte à la place")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du logo: {e}")
        
        # Titre de l'application en dégradé visuel très subtil
        self.title_label = ctk.CTkLabel(
            self.logo_frame, 
            text="Vynal Docs",
            font=ctk.CTkFont(family="Helvetica", size=12, weight="normal"),  # Plus petit et normal
            text_color=("gray65", "gray75")  # Couleur encore plus subtile
        )
        self.title_label.pack(side=ctk.TOP, pady=(3, 0))  # Espacement minimal

        # Version intégrée avec dégradé subtil
        version_text = f"Version {self.model.config.get('app.version', '1.0.0')}"
        ctk.CTkLabel(
            self.logo_frame,
            text=version_text,
            font=ctk.CTkFont(family="Helvetica", size=7),  # Encore plus petit
            text_color=("gray55", "gray65")  # Couleur encore plus subtile
        ).pack(side=ctk.TOP, pady=(0, 3))  # Espacement minimal
        
        # Séparateur
        ctk.CTkFrame(self.sidebar, height=1, fg_color="gray").pack(side=ctk.TOP, fill=ctk.X, padx=10, pady=5)
        
        # Boutons de navigation
        
        # Cadre pour les boutons
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Définition des boutons du menu
        nav_items = [
            {"id": "dashboard", "text": "Tableau de bord", "icon": "📊"},
            {"id": "clients", "text": "Clients", "icon": "👥"},
            {"id": "templates", "text": "Modèles", "icon": "📋"},
            {"id": "documents", "text": "Documents", "icon": "📄"},
            {"id": "analysis", "text": "Chat IA", "icon": "🤖"},
            {"id": "settings", "text": "Paramètres", "icon": "⚙️"}
        ]
        
        # Créer les boutons
        for item in nav_items:
            btn = ctk.CTkButton(
                self.nav_frame,
                text=f"{item['icon']} {item['text']}",
                anchor="w",
                height=40,
                corner_radius=10,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                command=lambda i=item["id"]: self.show_view(i)
            )
            btn.pack(side=ctk.TOP, fill=ctk.X, padx=5, pady=2)
            self.nav_buttons[item["id"]] = btn
        
        # Informations en bas de la barre latérale
        self.sidebar_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_footer.pack(side=ctk.BOTTOM, fill=ctk.X, padx=10, pady=10)
        
        # Toolbar pour les boutons supplémentaires
        self.toolbar = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.toolbar.pack(side=ctk.BOTTOM, fill=ctk.X, padx=10, pady=5)
        
        # Version de l'application
        ctk.CTkLabel(
            self.sidebar_footer,
            text=f"Version {self.model.config.get('app.version', '1.0.0')}",
            font=ctk.CTkFont(size=10)
        ).pack(side=ctk.TOP, pady=2)
        
        # Copyright
        ctk.CTkLabel(
            self.sidebar_footer,
            text=f"© {self.model.config.get('app.company_name', 'Vynal Agency LTD')}",
            font=ctk.CTkFont(size=10)
        ).pack(side=ctk.TOP, pady=2)
        
        # Bouton Mon compte
        # Vérifier l'état de connexion
        is_logged_in = self.usage_tracker.is_user_registered()
        
        # Créer le bouton principal selon l'état de connexion
        if is_logged_in:
            # Utilisateur connecté - afficher son nom
            user_data = self.usage_tracker.get_user_data()
            display_name = user_data.get('email', 'Utilisateur').split('@')[0]
            button_text = f"👤 {display_name}"
            button_color = "#3498db"
            hover_color = "#2980b9"
        else:
            # Utilisateur non connecté - afficher "Se connecter"
            button_text = "👤 Se connecter"
            button_color = "#2ecc71"
            hover_color = "#27ae60"
        
        # Créer le bouton principal
        auth_button = ctk.CTkButton(
            self.sidebar_footer,
            text=button_text,
            command=self._show_auth_dialog,
            fg_color=button_color,
            hover_color=hover_color
        )
        auth_button.pack(side=ctk.TOP, fill=ctk.X, pady=5)
        self.auth_button = auth_button
        
        # Nous n'ajoutons pas les boutons supplémentaires ici
        # Ils seront ajoutés par update_auth_button
        self.update_auth_button()

    def create_content_area(self):
        """
        Crée la zone de contenu principal
        """
        try:
            # Cadre pour le contenu
            self.content_area = ctk.CTkFrame(self.main_frame)
            self.content_area.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True, padx=0, pady=0)
            
            # En-tête du contenu
            self.content_header = ctk.CTkFrame(self.content_area, height=60, fg_color=("gray90", "gray20"))
            self.content_header.pack(side=ctk.TOP, fill=ctk.X, padx=0, pady=0)
            self.content_header.pack_propagate(False)  # Empêcher le redimensionnement
            
            # Titre de la page
            self.page_title = ctk.CTkLabel(
                self.content_header,
                text="Tableau de bord",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            self.page_title.pack(side=ctk.LEFT, padx=20, pady=10)
            
            # Barre d'état
            self.status_bar = ctk.CTkFrame(
                self.content_area,
                height=25,
                fg_color=("#DBDBDB", "#2B2B2B")  # Gris clair pour le mode clair, gris foncé pour le mode sombre
            )
            self.status_bar.pack(side=ctk.BOTTOM, fill=ctk.X)
            
            # Label de statut
            self.status_label = ctk.CTkLabel(
                self.status_bar,
                text="Prêt",
                font=ctk.CTkFont(size=11),
                anchor="w",
                text_color=("gray10", "gray90")  # Texte foncé pour le mode clair, clair pour le mode sombre
            )
            self.status_label.pack(side=ctk.LEFT, padx=10, pady=2)
            
            # Cadre principal pour les différentes vues
            self.main_content = ctk.CTkFrame(self.content_area, fg_color="transparent")
            self.main_content.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True, padx=20, pady=20)
            
            logger.debug("Zone de contenu créée avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la création de la zone de contenu: {e}")
            # Créer une structure minimale en cas d'erreur
            self.content_area = ctk.CTkFrame(self.main_frame)
            self.content_area.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True)
            self.main_content = ctk.CTkFrame(self.content_area)
            self.main_content.pack(fill=ctk.BOTH, expand=True)
    
    def create_views(self):
        """
        Crée les différentes vues de l'application
        """
        try:
            # Initialiser le dictionnaire des vues s'il n'existe pas
            if not hasattr(self, 'views'):
                self.views = {}
            
            # Créer les vues dans le bon conteneur
            view_classes = {
                "dashboard": DashboardView,
                "clients": ClientView,
                "templates": TemplateView,
                "documents": DocumentView,
                "analysis": ChatAIView,
                "settings": SettingsView
            }
            
            # Importer document_creator_view si nécessaire
            try:
                from views.document_creator_view import DocumentCreatorView
                view_classes["document_creator"] = DocumentCreatorView
                logger.info("DocumentCreatorView importée dans les classes de vues disponibles")
            except Exception as e:
                logger.warning(f"Impossible d'importer DocumentCreatorView: {e}")
            
            # Créer chaque vue individuellement avec gestion des erreurs
            for view_id, view_class in view_classes.items():
                try:
                    if view_id not in self.views:
                        self.views[view_id] = view_class(self.main_content, self.model)
                        logger.info(f"Vue {view_id} créée avec succès")
                except Exception as e:
                    logger.error(f"Erreur lors de la création de la vue {view_id}: {e}")
            
            # S'assurer que toutes les vues sont initialement cachées
            for view_id, view in self.views.items():
                try:
                    if hasattr(view, 'hide'):
                        view.hide()
                        logger.debug(f"Vue {view_id} masquée")
                except Exception as e:
                    logger.error(f"Erreur lors du masquage de la vue {view_id}: {e}")
            
            logger.info("Toutes les vues ont été initialisées")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des vues: {e}")
            # Créer une structure minimale pour éviter les erreurs fatales
            if "dashboard" not in self.views:
                self.views["dashboard"] = DashboardView(self.main_content, self.model)
                logger.info("Vue dashboard créée comme fallback")
    
    def show_view(self, view_id):
        """
        Affiche une vue spécifique et masque les autres
        
        Args:
            view_id: Identifiant de la vue à afficher
        """
        # Vérifier si la vue existe, sinon tenter de la créer
        if view_id not in self.views:
            try:
                view_classes = {
                    "dashboard": DashboardView,
                    "clients": ClientView,
                    "templates": TemplateView,
                    "documents": DocumentView,
                    "analysis": ChatAIView,
                    "settings": SettingsView
                }
                # Ajouter DocumentCreatorView si elle n'est pas déjà là
                if "document_creator" not in view_classes and view_id == "document_creator":
                    try:
                        from views.document_creator_view import DocumentCreatorView
                        view_classes["document_creator"] = DocumentCreatorView
                    except Exception as e:
                        logger.error(f"Erreur d'importation de DocumentCreatorView: {e}")
                
                if view_id in view_classes:
                    self.views[view_id] = view_classes[view_id](self.main_content, self.model)
                    logger.info(f"Vue {view_id} créée avec succès")
                else:
                    logger.error(f"Vue {view_id} non trouvée et impossible à créer")
                    return
            except Exception as e:
                logger.error(f"Erreur lors de la création de la vue {view_id}: {e}")
                return
        
        # Mettre à jour le titre de la page
        titles = {
            "dashboard": "Tableau de bord",
            "clients": "Gestion des clients",
            "templates": "Modèles de documents",
            "documents": "Bibliothèque de documents",
            "analysis": "Chat IA",
            "settings": "Paramètres",
            "document_creator": "Traitement de document"
        }
        
        try:
            self.page_title.configure(text=titles.get(view_id, ""))
        except Exception as e:
            logger.warning(f"Impossible de mettre à jour le titre: {e}")
        
        # Mettre à jour l'état des boutons de navigation
        for btn_id, btn in self.nav_buttons.items():
            try:
                if btn_id == view_id:
                    btn.configure(
                        fg_color=("gray85", "gray25"),
                        text_color=("gray10", "gray90")
                    )
                else:
                    btn.configure(
                        fg_color="transparent",
                        text_color=("gray10", "gray90")
                    )
            except Exception as e:
                logger.warning(f"Impossible de mettre à jour le bouton {btn_id}: {e}")
        
        # Masquer toutes les vues
        for view in self.views.values():
            if hasattr(view, 'hide'):
                try:
                    view.hide()
                except Exception as e:
                    logger.warning(f"Erreur lors du masquage d'une vue: {e}")
        
        # Afficher la vue sélectionnée
        if view_id in self.views:
            view = self.views[view_id]
            if hasattr(view, 'show'):
                view.show()
                
                # Si c'est le tableau de bord, envoyer le signal ready au splash screen
                if view_id == "dashboard":
                    # Appeler le callback on_ready si disponible
                    if hasattr(self, 'on_ready') and self.on_ready is not None:
                        self.on_ready()
                    
                    # Pour la compatibilité, maintenir aussi l'ancien code
                    try:
                        import socket
                        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        client.connect(('127.0.0.1', 12345))  # Port de synchronisation
                        client.send(json.dumps({'status': 'ready'}).encode('utf-8'))
                        client.close()
                        logger.info("Signal 'ready' envoyé au splash screen")
                    except Exception as e:
                        logger.error(f"Erreur lors de l'envoi du signal 'ready': {e}")
    
    def show_message(self, title, message, message_type="info"):
        """
        Affiche une boîte de dialogue avec un message
        
        Args:
            title: Titre de la boîte de dialogue
            message: Message à afficher
            message_type: Type de message ('info', 'error', 'warning')
        """
        if message_type == "error":
            icon = "❌"
        elif message_type == "warning":
            icon = "⚠️"
        else:
            icon = "ℹ️"
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.lift()  # Mettre au premier plan
        dialog.focus_force()  # Donner le focus
        dialog.grab_set()  # Modal
        
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
            text=f"{icon} {title}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(
            msg_frame,
            text=message,
            wraplength=360
        ).pack(pady=10)
        
        # Bouton OK
        ctk.CTkButton(
            msg_frame,
            text="OK",
            width=100,
            command=dialog.destroy
        ).pack(pady=10)
    
    def show_confirmation(self, title, message, on_yes, on_no=None):
        """
        Affiche une boîte de dialogue de confirmation
        
        Args:
            title: Titre de la boîte de dialogue
            message: Message à afficher
            on_yes: Fonction à appeler si l'utilisateur confirme
            on_no: Fonction à appeler si l'utilisateur annule
        """
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
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
            text=f"⚠️ {title}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(
            msg_frame,
            text=message,
            wraplength=360
        ).pack(pady=10)
        
        # Boutons
        btn_frame = ctk.CTkFrame(msg_frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def yes_action():
            dialog.destroy()
            if on_yes:
                on_yes()
        
        def no_action():
            dialog.destroy()
            if on_no:
                on_no()
        
        ctk.CTkButton(
            btn_frame,
            text="Oui",
            width=100,
            fg_color="green",
            command=yes_action
        ).pack(side=ctk.LEFT, padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Non",
            width=100,
            fg_color="red",
            command=no_action
        ).pack(side=ctk.LEFT, padx=10)
    
    def update_view(self):
        """
        Méthode générique pour mettre à jour la vue principale
        """
        # Mettre à jour le titre de l'application
        self.root.title(self.model.config.get("app.name", "Vynal Docs Automator"))
        
        # Mettre à jour le thème
        theme = self.model.config.get("app.theme", "dark").lower()
        ctk.set_appearance_mode(theme)

    def _show_auth_dialog(self):
        """Affiche la fenêtre d'authentification"""
        try:
            # Créer la vue d'authentification si elle n'existe pas
            if not hasattr(self, 'auth_view'):
                from views.auth_view import AuthView
                self.auth_view = AuthView(self.root, self.usage_tracker)
                self.auth_view.set_auth_callback(self._on_auth_change)
            
            # Vérifier si l'utilisateur est connecté
            is_logged_in = self.usage_tracker.is_user_registered()
            
            # Afficher la vue d'authentification
            self.auth_view.show()
            
            # Afficher l'onglet approprié
            if is_logged_in:
                self.auth_view._show_tab("account")
            else:
                self.auth_view._show_tab("login")
                
            logger.info("Fenêtre d'authentification affichée")
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de la fenêtre d'authentification: {e}")
            self.show_message(
                "Erreur",
                "Une erreur est survenue lors de l'affichage de la fenêtre d'authentification.",
                "error"
            )

    def _on_auth_change(self, is_logged_in, user_data):
        """
        Callback appelé lorsque l'état d'authentification change
        
        Args:
            is_logged_in (bool): True si l'utilisateur est connecté, False sinon
            user_data (dict): Données de l'utilisateur si connecté, None sinon
        """
        try:
            # Mettre à jour l'interface utilisateur
            self.update_auth_button()
            
            # Afficher un message approprié
            if is_logged_in:
                self.show_message(
                    "Connexion réussie",
                    f"Bienvenue {user_data.get('name', 'utilisateur')} !",
                    "success"
                )
            else:
                self.show_message(
                    "Déconnexion",
                    "Vous avez été déconnecté avec succès.",
                    "info"
                )
                
            logger.info(f"État d'authentification mis à jour - Connecté: {is_logged_in}")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'état d'authentification: {e}")
            
    def update_auth_button(self):
        """Met à jour l'interface utilisateur selon l'état d'authentification"""
        if not hasattr(self, 'usage_tracker'):
            from utils.usage_tracker import UsageTracker
            self.usage_tracker = UsageTracker()
        
        is_logged_in = self.usage_tracker.is_user_registered()
        
        # Mettre à jour le texte et la couleur des boutons selon l'état de connexion
        if is_logged_in:
            # Utilisateur connecté
            user_data = self.usage_tracker.get_user_data()
            display_name = user_data.get('email', 'Utilisateur').split('@')[0]
            button_text = f"👤 {display_name}"
            button_color = "#3498db"
            hover_color = "#2980b9"
        else:
            # Utilisateur non connecté
            button_text = "👤 Se connecter"
            button_color = "#2ecc71"
            hover_color = "#27ae60"
        
        # Mettre à jour le bouton principal
        if hasattr(self, 'auth_button') and self.auth_button:
            try:
                self.auth_button.configure(
                    text=button_text,
                    fg_color=button_color,
                    hover_color=hover_color
                )
            except Exception as e:
                logger.warning(f"Erreur lors de la mise à jour du bouton d'authentification: {e}")
        
        # Nettoyer tous les boutons existants dans la barre latérale
        try:
            if hasattr(self, 'sidebar_footer') and self.sidebar_footer:
                # Supprimer tous les widgets enfants sauf le bouton principal
                for widget in list(self.sidebar_footer.winfo_children()):
                    if widget != self.auth_button:
                        try:
                            widget.destroy()
                        except Exception as e:
                            logger.warning(f"Erreur lors de la suppression d'un widget: {e}")
            
            # Supprimer les références aux boutons
            for btn_name in ['logout_button', 'register_button', 'login_button']:
                if hasattr(self, btn_name):
                    delattr(self, btn_name)
            
            # Ajouter les boutons appropriés selon l'état de connexion
            if hasattr(self, 'sidebar_footer') and self.sidebar_footer:
                if is_logged_in:
                    # Utilisateur connecté - ajouter le bouton de déconnexion
                    logout_button = ctk.CTkButton(
                        self.sidebar_footer,
                        text="🔒 Déconnexion",
                        command=self._handle_logout,
                        fg_color="transparent",
                        hover_color=("gray85", "gray25"),
                        anchor="w"
                    )
                    logout_button.pack(side=ctk.TOP, fill=ctk.X, pady=5)
                    self.logout_button = logout_button
                else:
                    # Utilisateur non connecté - ajouter les boutons d'inscription et de connexion
                    register_button = ctk.CTkButton(
                        self.sidebar_footer,
                        text="✏️ S'inscrire",
                        command=lambda: self._show_auth_dialog_tab("register"),
                        fg_color="transparent",
                        hover_color=("gray85", "gray25"),
                        anchor="w"
                    )
                    register_button.pack(side=ctk.TOP, fill=ctk.X, pady=5)
                    self.register_button = register_button
                    
                    login_button = ctk.CTkButton(
                        self.sidebar_footer,
                        text="🔑 Se connecter",
                        command=lambda: self._show_auth_dialog_tab("login"),
                        fg_color="transparent",
                        hover_color=("gray85", "gray25"),
                        anchor="w"
                    )
                    login_button.pack(side=ctk.TOP, fill=ctk.X, pady=5)
                    self.login_button = login_button
        except Exception as e:
            logger.warning(f"Erreur lors de la mise à jour des boutons d'authentification: {e}")
        
        # Mettre à jour l'interface de la vue principale
        self.update_view()
        
        # Journaliser le changement d'état
        logger.info(f"État d'authentification mis à jour - Connecté: {is_logged_in}")

    def _show_auth_dialog_tab(self, tab_name):
        """
        Affiche le dialogue d'authentification avec un onglet spécifique
        
        Args:
            tab_name: Nom de l'onglet à afficher ("login", "register" ou "account")
        """
        # Utiliser la méthode standard pour afficher la fenêtre d'authentification
        self._show_auth_dialog()
        
        # Puis afficher l'onglet spécifié
        try:
            if hasattr(self, 'auth_view') and self.auth_view:
                logger.info(f"Affichage de l'onglet {tab_name}")
                self.auth_view._show_tab(tab_name)
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de l'onglet {tab_name}: {e}")

    # Methods for activity monitor integration and lock/unlock functionality
    def _setup_activity_monitor(self):
        """Configure et initialise le moniteur d'activité si nécessaire"""
        try:
            # Créer une instance du moniteur d'activité
            self.activity_monitor = ActivityMonitor(
                lock_callback=self._lock_application,
                config_manager=self.model.config
            )
            
            # Démarrer le moniteur si les conditions sont remplies
            self.activity_monitor.start()
            
            logger.info("Moniteur d'activité configuré")
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du moniteur d'activité: {e}")
    
    def _setup_activity_events(self):
        """Configure les événements pour détecter l'activité de l'utilisateur"""
        try:
            if self.activity_monitor:
                # Associer les événements de la fenêtre principale
                self.root.bind("<Motion>", self._on_user_activity)
                self.root.bind("<Key>", self._on_user_activity)
                self.root.bind("<Button>", self._on_user_activity)
                self.root.bind("<MouseWheel>", self._on_user_activity)
                
                # Bind événements sur le frame principal aussi
                self.main_frame.bind("<Motion>", self._on_user_activity)
                self.main_frame.bind("<Button>", self._on_user_activity)
                
                logger.debug("Événements de surveillance d'activité configurés")
        except Exception as e:
            logger.error(f"Erreur lors de la configuration des événements d'activité: {e}")
    
    def _on_user_activity(self, event=None):
        """Callback appelé lors d'une activité utilisateur"""
        if self.activity_monitor:
            self.activity_monitor.register_activity(event)
    
    def _lock_application(self):
        """Verrouille l'application et affiche l'écran de connexion"""
        try:
            # Exécuter sur le thread principal pour éviter les problèmes d'interface
            self.root.after(0, self._show_unlock_dialog)
            logger.info("Application verrouillée par inactivité")
        except Exception as e:
            logger.error(f"Erreur lors du verrouillage de l'application: {e}")
    
    def _show_unlock_dialog(self):
        """Affiche la boîte de dialogue de déverrouillage"""
        try:
            # Masquer l'application principale
            for widget in self.root.winfo_children():
                widget.pack_forget()
            
            # Créer une fenêtre modale par-dessus l'application
            self.lock_dialog = ctk.CTkToplevel(self.root)
            self.lock_dialog.title("Déverrouillage requis")
            self.lock_dialog.attributes("-topmost", True)
            
            # Rendre la fenêtre modale
            self.lock_dialog.grab_set()
            self.lock_dialog.focus_force()
            
            # Empêcher la fermeture par la croix
            self.lock_dialog.protocol("WM_DELETE_WINDOW", lambda: None)
            
            # Dimensions
            width = 400
            height = 250
            self.lock_dialog.geometry(f"{width}x{height}")
            
            # Centrer la fenêtre
            self.lock_dialog.update_idletasks()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.lock_dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            # Frame principal avec padding
            main_frame = ctk.CTkFrame(self.lock_dialog)
            main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            
            # Titre
            title_label = ctk.CTkLabel(
                main_frame,
                text="🔒 Session verrouillée",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            title_label.pack(pady=(0, 20))
            
            # Message
            message_label = ctk.CTkLabel(
                main_frame,
                text="Votre session a été verrouillée en raison d'inactivité.\nVeuillez entrer votre mot de passe pour continuer.",
                wraplength=350
            )
            message_label.pack(pady=(0, 20))
            
            # Champ de mot de passe
            password_var = ctk.StringVar()
            password_entry = ctk.CTkEntry(
                main_frame,
                placeholder_text="Mot de passe",
                show="•",
                width=200,
                textvariable=password_var
            )
            password_entry.pack(pady=(0, 10))
            password_entry.focus_set()
            
            # Message d'erreur
            error_label = ctk.CTkLabel(
                main_frame,
                text="",
                text_color="red"
            )
            error_label.pack(pady=(0, 10))
            
            # Fonction de validation
            def validate_password():
                password = password_var.get()
                if not password:
                    error_label.configure(text="Veuillez entrer votre mot de passe")
                    return
                
                # Vérifier le mot de passe
                if self._check_password(password):
                    # Fermer la boîte de dialogue
                    self.lock_dialog.destroy()
                    
                    # Réafficher les widgets principaux de l'application
                    self._restore_main_view()
                    
                    # Réinitialiser le moniteur d'activité
                    if self.activity_monitor:
                        self.activity_monitor.reset()
                    
                    logger.info("Application déverrouillée avec succès")
                else:
                    error_label.configure(text="Mot de passe incorrect")
                    password_entry.delete(0, "end")
            
            # Gestion de l'événement Entrée
            password_entry.bind("<Return>", lambda event: validate_password())
            
            # Bouton de déverrouillage
            unlock_button = ctk.CTkButton(
                main_frame,
                text="Déverrouiller",
                width=150,
                command=validate_password
            )
            unlock_button.pack(pady=10)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de la boîte de dialogue de déverrouillage: {e}")
            # En cas d'erreur, restaurer l'interface principale
            self._restore_main_view()
    
    def _restore_main_view(self):
        """Restaure l'affichage principal de l'application après déverrouillage"""
        try:
            # Réafficher les widgets principaux
            if hasattr(self, 'main_frame'):
                # Clear le root d'abord
                for widget in self.root.winfo_children():
                    if widget != self.lock_dialog:  # Ne pas toucher au dialogue de verrouillage
                        widget.pack_forget()
                
                # Réafficher le frame principal
                self.main_frame.pack(fill=ctk.BOTH, expand=True)
                
                # Réorganiser les composants principaux
                if hasattr(self, 'sidebar'):
                    self.sidebar.pack(side=ctk.LEFT, fill=ctk.Y, padx=0, pady=0)
                
                if hasattr(self, 'content_area'):
                    self.content_area.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True)
                    
                    # Réafficher les composants de la zone de contenu
                    if hasattr(self, 'toolbar_frame'):
                        self.toolbar_frame.pack(side=ctk.TOP, fill=ctk.X, padx=0, pady=0)
                    
                    if hasattr(self, 'main_content'):
                        self.main_content.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True, padx=20, pady=20)
                    
                    if hasattr(self, 'status_bar'):
                        self.status_bar.pack(side=ctk.BOTTOM, fill=ctk.X)
            
            # Redessiner la fenêtre
            self.root.update_idletasks()
            logger.info("Interface principale restaurée après déverrouillage")
        except Exception as e:
            logger.error(f"Erreur lors de la restauration de l'interface principale: {e}")
            # En cas d'erreur grave, essayer de recharger complètement l'interface
            try:
                self._create_widgets()
                logger.info("Interface réinitialisée après erreur de restauration")
            except Exception as e2:
                logger.critical(f"Erreur critique lors de la réinitialisation de l'interface: {e2}")
    
    def _check_password(self, password):
        """
        Vérifie si le mot de passe est correct
        
        Args:
            password: Mot de passe à vérifier
            
        Returns:
            bool: True si le mot de passe est correct, False sinon
        """
        try:
            # Vérifier si la configuration contient un hash de mot de passe
            password_hash = self.model.config.get("security.password_hash", "")
            if not password_hash:
                logger.error("Aucun mot de passe n'est configuré")
                return False
            
            # Hacher le mot de passe entré
            input_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Comparer les hash
            return input_hash == password_hash
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du mot de passe: {e}")
            return False
    
    def update_activity_monitor(self):
        """Met à jour le moniteur d'activité selon les paramètres actuels"""
        if self.activity_monitor:
            # Arrêter l'ancien moniteur
            self.activity_monitor.stop()
            
            # Redémarrer avec les nouveaux paramètres
            self.activity_monitor.start()
            
            logger.info("Moniteur d'activité mis à jour")
    
    def shutdown(self):
        """Arrête proprement le moniteur d'activité lors de la fermeture"""
        if self.activity_monitor:
            self.activity_monitor.stop()
            logger.info("Moniteur d'activité arrêté lors de la fermeture de l'application")