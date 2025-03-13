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

# Importation des vues
from views.dashboard_view import DashboardView
from views.client_view import ClientView
from views.document_view import DocumentView
from views.template_view import TemplateView
from views.settings_view import SettingsView

logger = logging.getLogger("VynalDocsAutomator.MainView")

class MainView:
    """
    Vue principale de l'application
    Gère l'interface utilisateur globale et la navigation entre les différentes vues
    """
    
    def __init__(self, root, app_model):
        """
        Initialise la vue principale
        
        Args:
            root: Fenêtre principale CTk
            app_model: Modèle de l'application
        """
        self.root = root
        self.model = app_model
        
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
        
        # Titre de l'application
        self.title_label = ctk.CTkLabel(
            self.logo_frame, 
            text=self.model.config.get("app.name", "Vynal Docs Automator"),
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(side=ctk.TOP, pady=10)
        
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
                fg_color="transparent",  # Couleur d'origine transparente
                hover_color=("gray85", "gray25"),  # Couleur de survol d'origine
                command=lambda i=item["id"]: self.show_view(i)
            )
            btn.pack(side=ctk.TOP, fill=ctk.X, padx=5, pady=5)
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

    def create_user_menu(self, parent_frame):
        """Crée le menu utilisateur dans la barre latérale"""
        # Frame pour le menu utilisateur
        user_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        user_frame.pack(fill=ctk.X, pady=5)
        
        # Bouton principal "Mon compte"
        if self.usage_tracker.is_user_registered():
            user_data = self.usage_tracker.get_user_data()
            display_name = user_data.get('email', 'Utilisateur').split('@')[0]
            button_text = f"👤 {display_name}"
            button_color = "#3498db"
            hover_color = "#2980b9"
        else:
            button_text = "👤 Se connecter"
            button_color = "#2ecc71"
            hover_color = "#27ae60"
        
        self.auth_button = ctk.CTkButton(
            user_frame,
            text=button_text,
            fg_color=button_color,
            hover_color=hover_color,
            command=self._show_auth_dialog
        )
        self.auth_button.pack(fill=ctk.X)
        
        # Si l'utilisateur est connecté, ajouter l'option de déconnexion
        if self.usage_tracker.is_user_registered():
            # Séparateur
            ctk.CTkFrame(user_frame, height=1, fg_color="gray50").pack(fill=ctk.X, pady=5)
            
            # Option de déconnexion
            logout_button = ctk.CTkButton(
                user_frame,
                text="🔒 Déconnexion",
                fg_color="transparent",
                hover_color=("gray80", "gray30"),
                anchor="w",
                command=self._handle_logout
            )
            logout_button.pack(fill=ctk.X, pady=2)
    
    def _show_account_settings(self):
        """Affiche les paramètres du compte utilisateur"""
        if hasattr(self, 'auth_view'):
            self.auth_view.show_account()
            self.auth_view._show_tab("account")
        else:
            self._show_auth_dialog()
    
    def _show_usage_stats(self):
        """Affiche les statistiques d'utilisation"""
        # À implémenter - Afficher les statistiques d'utilisation
        self.show_message("Statistiques", "Les statistiques d'utilisation seront disponibles prochainement.")
    
    def _handle_logout(self):
        """Gère la déconnexion de l'utilisateur"""
        if hasattr(self, 'auth_view'):
            try:
                # Appeler la méthode de déconnexion de AuthView
                self.auth_view._handle_logout()
                
                # Fermer la fenêtre d'authentification
                try:
                    self.auth_view.hide()
                except:
                    pass
                
                # Mettre à jour l'interface après la déconnexion
                self.update_auth_button()
                
                # Afficher un message de confirmation
                self.show_message("Déconnexion", "Vous avez été déconnecté avec succès.", "success")
            except Exception as e:
                logger.error(f"Erreur lors de la déconnexion: {e}")
                self.show_message("Erreur", f"Une erreur est survenue lors de la déconnexion: {e}", "error")
        else:
            # Si auth_view n'existe pas, effectuer une déconnexion directe
            try:
                # Réinitialiser l'état de connexion dans UsageTracker
                if hasattr(self, 'usage_tracker'):
                    # Supprimer les données de connexion
                    users_file = os.path.join(self.usage_tracker.data_dir, "users.json")
                    if os.path.exists(users_file):
                        with open(users_file, 'w') as f:
                            json.dump({}, f)
                    
                    # Mettre à jour l'interface
                    self.update_auth_button()
                    
                    # Afficher un message de confirmation
                    self.show_message("Déconnexion", "Vous avez été déconnecté avec succès.", "success")
            except Exception as e:
                logger.error(f"Erreur lors de la déconnexion directe: {e}")
                self.show_message("Erreur", f"Une erreur est survenue lors de la déconnexion: {e}", "error")
    
    def create_toolbar_buttons(self):
        """Crée les boutons de la barre d'outils"""
        # Bouton Paramètres
        settings_button = ctk.CTkButton(
            self.toolbar,
            text="⚙️ Paramètres",
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            command=lambda: self.show_view("settings")
        )
        settings_button.pack(fill=ctk.X, pady=5)
        
        # Bouton Aide
        help_button = ctk.CTkButton(
            self.toolbar,
            text="❓ Aide",
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            command=self._show_help
        )
        help_button.pack(fill=ctk.X, pady=5)
    
    def _show_help(self):
        """Affiche l'aide de l'application"""
        # À implémenter - Afficher l'aide
        self.show_message("Aide", "L'aide sera disponible prochainement.")

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
        # Vue du tableau de bord
        self.views["dashboard"] = DashboardView(self.main_content, self.model)
        
        # Vue des clients
        self.views["clients"] = ClientView(self.main_content, self.model)
        
        # Vue des modèles
        self.views["templates"] = TemplateView(self.main_content, self.model)
        
        # Vue des documents
        self.views["documents"] = DocumentView(self.main_content, self.model)
        
        # Vue des paramètres
        self.views["settings"] = SettingsView(self.main_content, self.model)
        
        # Cacher toutes les vues initialement
        for view in self.views.values():
            view.hide()
    
    def show_view(self, view_id):
        """
        Affiche une vue spécifique et masque les autres
        
        Args:
            view_id: Identifiant de la vue à afficher
        """
        # Vérifier si la vue existe
        if view_id not in self.views:
            logger.error(f"Vue {view_id} non trouvée")
            return
        
        # Mettre à jour le titre de la page
        titles = {
            "dashboard": "Tableau de bord",
            "clients": "Gestion des clients",
            "templates": "Modèles de documents",
            "documents": "Bibliothèque de documents",
            "settings": "Paramètres"
        }
        
        try:
            self.page_title.configure(text=titles.get(view_id, ""))
        except Exception as e:
            logger.warning(f"Impossible de mettre à jour le titre: {e}")
        
        # Mettre à jour l'état des boutons de navigation
        for btn_id, btn in self.nav_buttons.items():
            try:
                if btn_id == view_id:
                    btn.configure(fg_color=("blue", "#1f538d"))
                else:
                    btn.configure(fg_color=("gray75", "#333333"))
            except Exception as e:
                logger.warning(f"Impossible de mettre à jour le bouton {btn_id}: {e}")
        
        # Masquer toutes les vues
        for view in self.views.values():
            view.hide()
        
        # Afficher la vue demandée
        self.views[view_id].show()
        
        # Mettre à jour la vue si nécessaire
        if hasattr(self.views[view_id], "update_view"):
            self.views[view_id].update_view()
        
        logger.info(f"Vue {view_id} affichée")
    
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
        """Affiche le dialogue d'authentification"""
        from views.auth_view import AuthView
        from utils.usage_tracker import UsageTracker
        
        if not hasattr(self, 'usage_tracker'):
            self.usage_tracker = UsageTracker()
        
        # Vérifier si l'instance auth_view existe et est valide
        try:
            if hasattr(self, 'auth_view'):
                self.auth_view.window.winfo_exists()
        except (tk.TclError, AttributeError):
            # Recréer l'instance si elle n'existe pas ou n'est plus valide
            self.auth_view = None
        
        if not hasattr(self, 'auth_view') or self.auth_view is None:
            self.auth_view = AuthView(self.root, self.usage_tracker)
            # Définir le callback pour mettre à jour le bouton
            if hasattr(self.auth_view, 'set_auth_callback'):
                self.auth_view.set_auth_callback(lambda is_logged_in, user: self.update_auth_button())
            else:
                # Si la méthode set_auth_callback n'existe pas, définir directement l'attribut
                self.auth_view.auth_callback = lambda is_logged_in, user: self.update_auth_button()
        
        # Vérifier l'état de connexion
        is_logged_in = self.usage_tracker.is_user_registered()
        
        # Afficher la vue d'authentification
        if is_logged_in:
            # Si l'utilisateur est connecté, afficher directement l'onglet Mon compte
            self.auth_view.show()
            try:
                self.auth_view._show_tab("account")
            except Exception as e:
                logger.error(f"Erreur lors de l'affichage de l'onglet compte: {e}")
        else:
            # Sinon, afficher la vue de connexion
            self.auth_view.show()
            try:
                self.auth_view._show_tab("login")
            except Exception as e:
                logger.error(f"Erreur lors de l'affichage de l'onglet login: {e}")

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