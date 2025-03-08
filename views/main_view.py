#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue principale de l'application Vynal Docs Automator
"""

import os
import logging
import customtkinter as ctk
from PIL import Image, ImageTk

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
        
        # Configurer la fenêtre principale
        self.root.title(self.model.config.get("app.name", "Vynal Docs Automator"))
        
        # Créer le cadre principal
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=ctk.BOTH, expand=True)
        
        # Créer la barre latérale et le contenu principal
        self.create_sidebar()
        self.create_content_area()
        
        # Dictionnaire des vues
        self.views = {}
        
        # Créer les différentes vues
        self.create_views()
        
        # Afficher la vue par défaut (tableau de bord)
        self.show_view("dashboard")
        
        logger.info("Vue principale initialisée")
    
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
        if logo_path and os.path.exists(logo_path):
            try:
                logo_image = Image.open(logo_path)
                logo_image = logo_image.resize((150, 70), Image.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_image)
                
                self.logo_label = ctk.CTkLabel(self.logo_frame, image=logo_photo, text="")
                self.logo_label.image = logo_photo  # Garder une référence
                self.logo_label.pack(side=ctk.TOP, pady=5)
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
        self.nav_buttons = {}
        
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
                command=lambda i=item["id"]: self.show_view(i)
            )
            btn.pack(side=ctk.TOP, fill=ctk.X, padx=5, pady=5)
            self.nav_buttons[item["id"]] = btn
        
        # Informations en bas de la barre latérale
        self.sidebar_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_footer.pack(side=ctk.BOTTOM, fill=ctk.X, padx=10, pady=10)
        
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
    
    def create_content_area(self):
        """
        Crée la zone de contenu principal
        """
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
        self.page_title.configure(text=titles.get(view_id, ""))
        
        # Mettre à jour l'état des boutons de navigation
        for btn_id, btn in self.nav_buttons.items():
            if btn_id == view_id:
                btn.configure(fg_color=("blue", "#1f538d"))
            else:
                btn.configure(fg_color=("gray75", "#333333"))
        
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
        theme = self.model.config.get("app.theme", "system")
        ctk.set_appearance_mode(theme)