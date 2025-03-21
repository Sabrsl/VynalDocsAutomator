#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue de gestion des utilisateurs pour l'interface d'administration
"""

import logging
import customtkinter as ctk

logger = logging.getLogger("VynalDocsAutomator.Admin.UserManagementView")

class UserManagementView:
    """
    Vue pour la gestion des utilisateurs
    """
    
    def __init__(self, parent, app_model):
        """
        Initialise la vue de gestion des utilisateurs
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        
        # Cadre principal de la vue
        self.frame = ctk.CTkFrame(parent)
        
        # Création de l'interface
        self.create_widgets()
        
        logger.info("UserManagementView initialisée")
    
    def create_widgets(self):
        """
        Crée les widgets de la vue de gestion des utilisateurs
        """
        # En-tête
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.pack(fill=ctk.X, padx=20, pady=10)
        
        # Titre de la page
        ctk.CTkLabel(
            header,
            text="Gestion des utilisateurs",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side=ctk.LEFT)
        
        # Bouton de réinitialisation de mot de passe
        reset_btn = ctk.CTkButton(
            header,
            text="Réinitialisation de mot de passe",
            command=self.show_password_reset
        )
        reset_btn.pack(side=ctk.RIGHT)
        
        # Message temporaire
        ctk.CTkLabel(
            self.frame,
            text="Interface de gestion des utilisateurs en cours de développement",
            font=ctk.CTkFont(size=14)
        ).pack(pady=20)
    
    def show_password_reset(self):
        """
        Affiche le gestionnaire de réinitialisation de mot de passe
        """
        # Le gestionnaire de réinitialisation sera affiché par la classe parente
        if hasattr(self.model, 'show_password_reset'):
            self.model.show_password_reset()
    
    def show(self):
        """Affiche la vue"""
        self.frame.pack(fill=ctk.BOTH, expand=True)
    
    def hide(self):
        """Cache la vue"""
        self.frame.pack_forget()