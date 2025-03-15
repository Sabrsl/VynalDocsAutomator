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
        # Titre de la page
        ctk.CTkLabel(
            self.frame,
            text="Gestion des utilisateurs",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", padx=20, pady=10)
        
        # Message temporaire
        ctk.CTkLabel(
            self.frame,
            text="La gestion des utilisateurs sera disponible prochainement",
            font=ctk.CTkFont(size=14)
        ).pack(expand=True)
    
    def show(self):
        """
        Affiche la vue de gestion des utilisateurs
        """
        self.frame.pack(fill=ctk.BOTH, expand=True)
    
    def hide(self):
        """
        Masque la vue de gestion des utilisateurs
        """
        self.frame.pack_forget()