#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Point d'entrée principal pour l'interface d'administration - Version améliorée
Gère l'initialisation et la coordination des différentes vues
"""

import logging
import customtkinter as ctk
from admin.models.admin_model import AdminModel
from admin.controllers.admin_controller import AdminController
from admin.views.admin_dashboard_view import AdminDashboardView
from admin.views.user_management_view import UserManagementView
from admin.views.permissions_view import PermissionsView
from admin.views.system_logs_view import SystemLogsView
from admin.views.settings_view import AdminSettingsView
from admin.views.password_reset_manager_view import PasswordResetManager
from utils.access_control import admin_only

logger = logging.getLogger("VynalDocsAutomator.Admin.Main")

class AdminMain:
    """
    Classe principale de l'interface d'administration
    Coordonne les différentes vues et gère la navigation
    """
    
    def __init__(self, parent, app_model):
        """
        Initialise l'interface d'administration
        
        Args:
            parent: Widget parent (peut être None pour une fenêtre séparée)
            app_model: Modèle de l'application principale
        """
        self.parent = parent
        self.app_model = app_model
        
        # Configuration du logging avec un niveau approprié
        logger.setLevel(logging.INFO)
        
        # Créer le modèle d'administration (lazy loading)
        self._admin_model = None
        self._controller = None
        
        # Appliquer un thème sombre
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Créer la fenêtre principale si nécessaire
        if parent is None:
            self.window = ctk.CTk()
            self.window.title("Administration - Vynal Docs Automator")
            self.window.geometry("1200x800")
        else:
            self.window = parent
        
        # Créer le cadre principal avec fond foncé
        self.main_frame = ctk.CTkFrame(self.window, fg_color="#1a1a1a")
        self.main_frame.pack(fill=ctk.BOTH, expand=True)
        
        # Zone de contenu pour les vues
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="#2a2a2a")
        
        # Configurer la disposition principale
        self.setup_layout()
        
        # Initialiser les vues de manière différée
        self._init_views()
        
        logger.info("Interface d'administration initialisée")
        
        # Afficher le tableau de bord par défaut
        self.show_dashboard()
    
    def setup_layout(self):
        """
        Configure la disposition de l'interface principale
        """
        # Créer une structure à deux colonnes avec grid
        self.main_frame.grid_columnconfigure(0, weight=0)  # Navigation (taille fixe)
        self.main_frame.grid_columnconfigure(1, weight=1)  # Contenu (prend tout l'espace disponible)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Cadre de gauche (navigation)
        self.nav_frame = ctk.CTkFrame(self.main_frame, fg_color="#1e1e1e", width=220)
        self.nav_frame.grid(row=0, column=0, sticky="nsew")
        self.nav_frame.grid_propagate(False)  # Empêche le redimensionnement
        
        # Titre de la navigation avec un arrière-plan plus foncé
        nav_header = ctk.CTkFrame(self.nav_frame, fg_color="#161616", height=60)
        nav_header.pack(fill=ctk.X, pady=0, padx=0)
        nav_header.pack_propagate(False)
        
        ctk.CTkLabel(
            nav_header,
            text="Administration",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=15)
        
        # Container pour les boutons de navigation
        nav_buttons_frame = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        nav_buttons_frame.pack(fill=ctk.BOTH, expand=True, pady=(20, 10))
        
        # Style et marge pour les boutons
        button_style = {
            "corner_radius": 0,
            "height": 45,
            "border_spacing": 10,
            "anchor": "w",
            "font": ctk.CTkFont(size=14),
            "fg_color": "transparent",
            "text_color": "#cccccc",
            "hover_color": "#3a3a3a"
        }
        
        # Créer les boutons de navigation avec des icônes
        self.nav_buttons = []
        
        # Bouton Tableau de bord
        dashboard_btn = ctk.CTkButton(
            nav_buttons_frame,
            text="Tableau de bord",
            command=self.show_dashboard,
            **button_style
        )
        dashboard_btn.pack(fill=ctk.X, pady=1)
        self.nav_buttons.append((dashboard_btn, "dashboard"))
        
        # Bouton Utilisateurs
        users_btn = ctk.CTkButton(
            nav_buttons_frame,
            text="Utilisateurs",
            command=self.show_user_management,
            **button_style
        )
        users_btn.pack(fill=ctk.X, pady=1)
        self.nav_buttons.append((users_btn, "users"))
        
        # Bouton Permissions
        permissions_btn = ctk.CTkButton(
            nav_buttons_frame,
            text="Permissions",
            command=self.show_permissions,
            **button_style
        )
        permissions_btn.pack(fill=ctk.X, pady=1)
        self.nav_buttons.append((permissions_btn, "permissions"))
        
        # Bouton Journaux
        logs_btn = ctk.CTkButton(
            nav_buttons_frame,
            text="Journaux",
            command=self.show_logs,
            **button_style
        )
        logs_btn.pack(fill=ctk.X, pady=1)
        self.nav_buttons.append((logs_btn, "logs"))
        
        # Bouton Paramètres
        settings_btn = ctk.CTkButton(
            nav_buttons_frame,
            text="Paramètres",
            command=self.show_settings,
            **button_style
        )
        settings_btn.pack(fill=ctk.X, pady=1)
        self.nav_buttons.append((settings_btn, "settings"))
        
        # Information utilisateur en bas
        user_frame = ctk.CTkFrame(self.nav_frame, fg_color="#222222", height=80)
        user_frame.pack(side=ctk.BOTTOM, fill=ctk.X, pady=0)
        user_frame.pack_propagate(False)
        
        # Nom d'utilisateur et rôle
        user_info = self.app_model.current_user if hasattr(self.app_model, 'current_user') else None
        
        user_name = f"{user_info.get('username', 'Admin')}" if user_info else "Admin"
        user_role = f"{user_info.get('role', 'Administrateur')}" if user_info else "Administrateur"
        
        ctk.CTkLabel(
            user_frame,
            text=user_name,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=(15, 0))
        
        ctk.CTkLabel(
            user_frame,
            text=user_role,
            font=ctk.CTkFont(size=12),
            text_color="#aaaaaa"
        ).pack(pady=(0, 10))
        
        # Cadre de contenu (occupe toute la zone droite)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
    
    def fix_missing_methods(self):
        """
        Corrige les méthodes manquantes dans les vues
        """
        # Dashboard: ajouter les méthodes manquantes
        if hasattr(self.dashboard, 'perform_backup_stub'):
            self.dashboard.perform_backup = self.dashboard.perform_backup_stub
        
        if hasattr(self.dashboard, 'check_integrity_stub'):
            self.dashboard.check_integrity = self.dashboard.check_integrity_stub
        
        if hasattr(self.dashboard, 'optimize_app_stub'):
            self.dashboard.optimize_app = self.dashboard.optimize_app_stub
        
        if hasattr(self.dashboard, 'handle_alert_action_stub'):
            self.dashboard.handle_alert_action = self.dashboard.handle_alert_action_stub
    
    def update_nav_buttons(self, active_section):
        """
        Met à jour l'apparence des boutons de navigation
        
        Args:
            active_section: Section active ('dashboard', 'users', etc.)
        """
        for button, section in self.nav_buttons:
            if section == active_section:
                button.configure(
                    fg_color="#3d5afe",
                    text_color="#ffffff",
                    hover_color="#5872ff"
                )
            else:
                button.configure(
                    fg_color="transparent",
                    text_color="#cccccc",
                    hover_color="#3a3a3a"
                )
    
    def show_dashboard(self):
        """Affiche le tableau de bord"""
        self.hide_all_views()
        self.dashboard.show()
        self.update_nav_buttons("dashboard")
    
    def show_user_management(self):
        """Affiche la gestion des utilisateurs"""
        self.hide_all_views()
        self.user_management.show()
        self.update_nav_buttons("users")
    
    def show_permissions(self):
        """Affiche la gestion des permissions"""
        self.hide_all_views()
        self.permissions.show()
        self.update_nav_buttons("permissions")
    
    def show_logs(self):
        """Affiche les journaux système"""
        self.hide_all_views()
        self.logs.show()
        self.update_nav_buttons("logs")
    
    def show_settings(self):
        """Affiche les paramètres"""
        self.hide_all_views()
        self.settings.show()
        self.update_nav_buttons("settings")
    
    def hide_all_views(self):
        """Cache toutes les vues de manière optimisée"""
        # Ne cacher que les vues qui ont été initialisées
        if self._dashboard is not None:
            self._dashboard.hide()
        if self._user_management is not None:
            self._user_management.hide()
        if self._permissions is not None:
            self._permissions.hide()
        if self._logs is not None:
            self._logs.hide()
        if self._settings is not None:
            self._settings.hide()
        if self._password_reset is not None:
            self._password_reset.hide()
    
    def show_password_reset_view(self):
        """Affiche la vue de réinitialisation de mot de passe"""
        self.hide_all_views()
        if hasattr(self, 'password_reset'):
            self.password_reset.show()
            logger.info("Vue de réinitialisation de mot de passe affichée")
        else:
            logger.error("Vue de réinitialisation de mot de passe non disponible")
    
    def show(self):
        """Affiche l'interface d'administration"""
        if self.parent is None:
            self.window.mainloop()
        else:
            self.main_frame.pack(fill=ctk.BOTH, expand=True)
    
    def hide(self):
        """Cache l'interface d'administration"""
        self.main_frame.pack_forget()

    @property
    def admin_model(self):
        """Lazy loading du modèle d'administration"""
        if self._admin_model is None:
            self._admin_model = AdminModel(self.app_model)
            self._admin_model.set_main_view(self)
        return self._admin_model

    @property
    def controller(self):
        """Lazy loading du contrôleur"""
        if self._controller is None:
            self._controller = AdminController(self, self.app_model)
        return self._controller

    def _init_views(self):
        """Initialise les vues de manière optimisée"""
        # Créer les vues avec lazy loading
        self._dashboard = None
        self._user_management = None
        self._permissions = None
        self._logs = None
        self._settings = None
        self._password_reset = None

    @property
    def dashboard(self):
        if self._dashboard is None:
            self._dashboard = AdminDashboardView(self.content_frame, self.admin_model)
        return self._dashboard

    @property
    def user_management(self):
        if self._user_management is None:
            self._user_management = UserManagementView(self.content_frame, self.admin_model)
        return self._user_management

    @property
    def permissions(self):
        if self._permissions is None:
            self._permissions = PermissionsView(self.content_frame, self.admin_model)
        return self._permissions

    @property
    def logs(self):
        if self._logs is None:
            self._logs = SystemLogsView(self.content_frame, self.admin_model)
        return self._logs

    @property
    def settings(self):
        if self._settings is None:
            self._settings = AdminSettingsView(self.content_frame, self.admin_model)
        return self._settings

    @property
    def password_reset(self):
        if self._password_reset is None:
            self._password_reset = PasswordResetManager(self.content_frame, self.admin_model)
        return self._password_reset

@admin_only
def initialize_admin_interface():
    """Initialise l'interface d'administration"""
    try:
        # Code d'initialisation existant...
        pass
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de l'interface admin: {e}")
        raise

@admin_only
def show_admin_interface():
    """Affiche l'interface d'administration"""
    try:
        # Code d'affichage existant...
        pass
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage de l'interface admin: {e}")
        raise