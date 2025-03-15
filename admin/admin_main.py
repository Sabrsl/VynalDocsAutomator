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
        
        # Créer le modèle d'administration
        self.admin_model = AdminModel(app_model)
        
        # Créer le contrôleur
        self.controller = AdminController(self, self.app_model)
        
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
        
        # Créer les vues
        self.dashboard = AdminDashboardView(self.content_frame, self.admin_model)
        self.user_management = UserManagementView(self.content_frame, self.admin_model)
        self.permissions = PermissionsView(self.content_frame, self.admin_model)
        self.logs = SystemLogsView(self.content_frame, self.admin_model)
        self.settings = AdminSettingsView(self.content_frame, self.admin_model)
        
        # Fonction de correction pour les méthodes manquantes
        self.fix_missing_methods()
        
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
        """Cache toutes les vues"""
        for view in [self.dashboard, self.user_management, self.permissions, self.logs, self.settings]:
            if hasattr(view, 'hide'):
                view.hide()
    
    def show(self):
        """Affiche l'interface d'administration"""
        self.main_frame.pack(fill=ctk.BOTH, expand=True)
        
        # Si c'est une fenêtre séparée, lancer la boucle principale
        if self.parent is None:
            self.window.mainloop()
    
    def hide(self):
        """Cache l'interface d'administration"""
        self.main_frame.pack_forget()