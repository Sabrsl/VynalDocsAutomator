#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue de gestion des permissions pour l'interface d'administration
"""

import logging
import customtkinter as ctk

logger = logging.getLogger("VynalDocsAutomator.Admin.PermissionsView")

class PermissionsView:
    """
    Vue pour la gestion des permissions des utilisateurs
    """
    
    def __init__(self, parent, app_model):
        """
        Initialise la vue de gestion des permissions
        
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
        
        logger.info("PermissionsView initialisée")
    
    def create_widgets(self):
        """
        Crée les widgets de la vue de gestion des permissions
        """
        # Cadre pour le titre de la page
        self.header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.header_frame.pack(fill=ctk.X, pady=(0, 10))
        
        # Titre principal
        ctk.CTkLabel(
            self.header_frame,
            text="Gestion des permissions",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", padx=20, pady=10)
        
        # Conteneur principal
        self.main_container = ctk.CTkFrame(self.frame)
        self.main_container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Message temporaire
        ctk.CTkLabel(
            self.main_container,
            text="La gestion des permissions sera disponible prochainement",
            font=ctk.CTkFont(size=14)
        ).pack(expand=True)
    
    def show(self):
        """
        Affiche la vue de gestion des permissions
        """
        self.frame.pack(fill=ctk.BOTH, expand=True)
    
    def hide(self):
        """
        Masque la vue de gestion des permissions
        """
        self.frame.pack_forget()