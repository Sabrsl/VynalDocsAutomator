#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue d'authentification moderne pour l'application Vynal Docs Automator
"""

import os
import json
import logging
import hashlib
import customtkinter as ctk
from typing import Callable, Optional, Dict, Any
from utils.usage_tracker import UsageTracker
from datetime import datetime
import tkinter as tk
from PIL import Image
import time

logger = logging.getLogger("VynalDocsAutomator.AuthView")

class AuthView:
    """Vue moderne pour l'authentification et la gestion de compte"""
    
    # Constantes pour la validation
    PASSWORD_MIN_LENGTH = 8
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_TIMEOUT = 300  # 5 minutes
    
    def __init__(self, parent, usage_tracker=None):
        """
        Initialise la vue d'authentification
        
        Args:
            parent: Widget parent
            usage_tracker: Instance du gestionnaire d'utilisation
        """
        self.parent = parent
        self.usage_tracker = usage_tracker or UsageTracker()
        
        # État de connexion et sécurité
        self.current_user = None
        self.on_auth_change_callback = None
        self.login_attempts = {}  # {email: [timestamp, count]}
        
        # Variables de validation
        self.email_valid = False
        self.password_valid = False
        self.confirm_password_valid = False
        
        # Variables
        self.current_tab = ctk.StringVar(value="login")
        self.email_var = ctk.StringVar()
        self.password_var = ctk.StringVar()
        self.confirm_password_var = ctk.StringVar()
        self.register_name_var = ctk.StringVar()
        
        # Stockage des références aux widgets
        self.main_frame = None
        self.window = None
        self.login_frame = None
        self.register_frame = None
        self.account_frame = None
        self.login_tab = None
        self.register_tab = None
        self.account_tab = None
        
        # Tracer les changements des variables
        self.email_var.trace_add("write", self._validate_email)
        self.password_var.trace_add("write", self._validate_password)
        self.confirm_password_var.trace_add("write", self._validate_confirm_password)
        
        # Référence aux onglets
        self.tabs = None
        
        # Ne pas créer les widgets immédiatement, attendre l'appel à show()
    
    def _create_widgets(self):
        """Crée les widgets de l'interface"""
        try:
            # Frame principal avec padding
            self.main_frame = ctk.CTkFrame(self.window)
            self.main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            
            # En-tête avec logo/icône
            self._create_header()
            
            # Onglets de navigation
            self._create_tabs()
            
            # Frame de contenu
            self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            self.content_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
            
            # Créer les différentes vues
            self._create_login_view()
            self._create_register_view()
            self._create_account_view()
            
            # Mettre à jour l'affichage selon l'onglet courant
            tab_name = self.current_tab.get()
            self._update_tab_content()
            
            logger.info("Widgets de l'interface d'authentification créés")
        except Exception as e:
            logger.error(f"Erreur lors de la création des widgets de l'interface: {e}")
            # Tenter une approche plus simple en cas d'échec
            try:
                # Frame principal
                self.main_frame = ctk.CTkFrame(self.window)
                self.main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
                
                # Titre simple
                ctk.CTkLabel(
                    self.main_frame,
                    text="Connexion à l'application",
                    font=ctk.CTkFont(size=16, weight="bold")
                ).pack(pady=10)
                
                # Créer juste la vue de connexion
                self.login_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
                self.login_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
                
                # Champs de connexion
                ctk.CTkLabel(self.login_frame, text="Email:").pack(anchor="w", pady=(10, 0))
                self.email_var = ctk.StringVar()
                ctk.CTkEntry(
                    self.login_frame,
                    textvariable=self.email_var,
                    width=250
                ).pack(pady=(0, 10))
                
                ctk.CTkLabel(self.login_frame, text="Mot de passe:").pack(anchor="w", pady=(10, 0))
                self.password_var = ctk.StringVar()
                ctk.CTkEntry(
                    self.login_frame,
                    textvariable=self.password_var,
                    show="•",
                    width=250
                ).pack(pady=(0, 10))
                
                # Bouton de connexion
                ctk.CTkButton(
                    self.login_frame,
                    text="Se connecter",
                    command=self._handle_login,
                    width=250
                ).pack(pady=20)
                
                # Message d'erreur
                self.login_status_label = ctk.CTkLabel(
                    self.login_frame,
                    text="",
                    text_color="red"
                )
                self.login_status_label.pack(pady=5)
                
                logger.info("Interface d'authentification simplifiée créée")
            except Exception as e2:
                logger.critical(f"Échec critique lors de la création d'une interface de secours: {e2}")
    
    def _create_header(self):
        """Crée l'en-tête avec logo"""
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.pack(fill=ctk.X, pady=(0, 20))
        
        # Logo/Icône
        logo_label = ctk.CTkLabel(
            header,
            text="👤",  # Emoji comme icône
            font=ctk.CTkFont(size=48)
        )
        logo_label.pack(pady=(0, 10))
        
        # Titre
        title_label = ctk.CTkLabel(
            header,
            text="Bienvenue",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack()
    
    def _create_tabs(self):
        """Crée les onglets de navigation"""
        try:
            # Créer le frame des onglets
            self.tabs = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            self.tabs.pack(fill=ctk.X, padx=10, pady=(10, 0))
            
            # Styles des onglets
            tab_height = 30
            tab_width = 120
            tab_corner_radius = 8
            
            # Créer les onglets
            # Onglet Connexion
            self.login_tab = ctk.CTkButton(
                self.tabs,
                text="Connexion",
                height=tab_height,
                width=tab_width,
                corner_radius=tab_corner_radius,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                command=lambda: self._show_tab("login")
            )
            self.login_tab.pack(side=ctk.LEFT, padx=5, pady=0)
            
            # Onglet Inscription
            self.register_tab = ctk.CTkButton(
                self.tabs,
                text="Inscription",
                height=tab_height,
                width=tab_width,
                corner_radius=tab_corner_radius,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                command=lambda: self._show_tab("register")
            )
            self.register_tab.pack(side=ctk.LEFT, padx=5, pady=0)
            
            # Onglet Compte (visible uniquement si connecté)
            self.account_tab = ctk.CTkButton(
                self.tabs,
                text="Compte",
                height=tab_height,
                width=tab_width,
                corner_radius=tab_corner_radius,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                command=lambda: self._show_tab("account")
            )
            self.account_tab.pack(side=ctk.LEFT, padx=5, pady=0)
            
            # Séparateur horizontal sous les onglets
            ctk.CTkFrame(self.main_frame, height=1, fg_color="gray").pack(fill=ctk.X, padx=10, pady=(0, 0))
            
            # Mettre en évidence l'onglet actuel
            tab_name = self.current_tab.get()
            if tab_name == "login":
                self.login_tab.configure(fg_color=("gray85", "gray25"))
            elif tab_name == "register":
                self.register_tab.configure(fg_color=("gray85", "gray25"))
            elif tab_name == "account":
                self.account_tab.configure(fg_color=("gray85", "gray25"))
                
            logger.debug("Onglets créés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la création des onglets: {e}")
            # Créer une version simplifiée des onglets avec une gestion d'erreur plus robuste
            try:
                # Si le frame des onglets existe déjà, le nettoyer
                if hasattr(self, 'tabs') and self.tabs:
                    for widget in self.tabs.winfo_children():
                        widget.destroy()
                else:
                    # Sinon créer un nouveau frame
                    self.tabs = ctk.CTkFrame(self.main_frame, fg_color="transparent")
                    self.tabs.pack(fill=ctk.X, padx=10, pady=(10, 0))
                
                # Créer les onglets basiques
                tabs_info = [
                    {"name": "login", "text": "Connexion"},
                    {"name": "register", "text": "Inscription"},
                    {"name": "account", "text": "Compte"}
                ]
                
                # Créer chaque onglet individuellement
                for tab in tabs_info:
                    btn = ctk.CTkButton(
                        self.tabs,
                        text=tab["text"],
                        height=30,
                        width=120,
                        corner_radius=8,
                        fg_color="transparent",
                        text_color=("gray10", "gray90"),
                        hover_color=("gray85", "gray25"),
                        command=lambda t=tab["name"]: self._show_tab(t)
                    )
                    btn.pack(side=ctk.LEFT, padx=5, pady=0)
                    
                    # Garder une référence aux onglets
                    setattr(self, f"{tab['name']}_tab", btn)
                
                # Séparateur
                ctk.CTkFrame(self.main_frame, height=1, fg_color="gray").pack(fill=ctk.X, padx=10, pady=(0, 0))
                
                logger.debug("Version simplifiée des onglets créée après erreur")
            except Exception as e2:
                logger.error(f"Échec critique lors de la création des onglets alternatifs: {e2}")
                # Dernière tentative ultra simplifiée
                self.tabs = ctk.CTkFrame(self.main_frame, fg_color="transparent")
                self.tabs.pack(fill=ctk.X, padx=10, pady=(10, 0))
                
                # Juste un titre pour indiquer l'onglet actuel
                tab_name = self.current_tab.get().capitalize()
                ctk.CTkLabel(
                    self.tabs,
                    text=f"Vue: {tab_name}",
                    font=ctk.CTkFont(size=14, weight="bold")
                ).pack(pady=5)
    
    def _create_login_view(self):
        """Crée la vue de connexion"""
        self.login_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Titre
        ctk.CTkLabel(
            self.login_frame,
            text="Connexion à votre compte",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(fill=ctk.X, padx=5, pady=(0, 5))
        
        # Cadre du formulaire
        form_frame = ctk.CTkFrame(self.login_frame, fg_color="transparent")
        form_frame.pack(fill=ctk.X, padx=20)
        
        # Champ email
        email_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        email_frame.pack(fill=ctk.X, pady=(0, 15))
        
        ctk.CTkLabel(
            email_frame,
            text="Adresse email",
            anchor="w"
        ).pack(fill=ctk.X, padx=5, pady=(0, 5))
        
        self.login_email = ctk.CTkEntry(
            email_frame,
            textvariable=self.email_var,
            placeholder_text="Votre adresse email",
            height=40,
            border_width=1
        )
        self.login_email.pack(fill=ctk.X)
        
        # Message d'erreur email
        self.login_email_error = ctk.CTkLabel(
            email_frame,
            text="",
            text_color="red",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.login_email_error.pack(fill=ctk.X, padx=5)
        
        # Champ mot de passe
        password_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        password_frame.pack(fill=ctk.X, pady=(0, 10))
        
        # Libellé et lien "Mot de passe oublié"
        pwd_header = ctk.CTkFrame(password_frame, fg_color="transparent")
        pwd_header.pack(fill=ctk.X, padx=5, pady=(0, 5))
        
        ctk.CTkLabel(
            pwd_header,
            text="Mot de passe",
            anchor="w"
        ).pack(side=ctk.LEFT)
        
        # Champ de saisie du mot de passe
        self.login_password = ctk.CTkEntry(
            password_frame,
            textvariable=self.password_var,
            placeholder_text="Votre mot de passe",
            show="•",
            height=40,
            border_width=1
        )
        self.login_password.pack(fill=ctk.X)
        
        # Message d'erreur mot de passe
        self.login_password_error = ctk.CTkLabel(
            password_frame,
            text="",
            text_color="red",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.login_password_error.pack(fill=ctk.X, padx=5)
        
        # Option "Se souvenir de moi"
        self.remember_var = ctk.BooleanVar(value=False)
        remember_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        remember_frame.pack(fill=ctk.X, pady=(0, 20))
        
        remember_checkbox = ctk.CTkCheckBox(
            remember_frame,
            text="Se souvenir de moi",
            variable=self.remember_var,
            border_width=2,
            corner_radius=6,
            hover_color=("#3498db", "#2980b9"),
            fg_color=("#3498db", "#2980b9")
        )
        remember_checkbox.pack(side=ctk.LEFT, padx=5)
        
        # Message de statut pour la connexion
        self.login_status_label = ctk.CTkLabel(
            form_frame,
            text="",
            text_color="red",
            anchor="center",
            font=ctk.CTkFont(size=12)
        )
        self.login_status_label.pack(fill=ctk.X, padx=5, pady=(0, 10))
        
        # Bouton de connexion
        self.login_button = ctk.CTkButton(
            form_frame,
            text="Se connecter",
            command=self._handle_login,
            height=40,
            corner_radius=8,
            fg_color=("#3498db", "#2980b9"),
            hover_color=("#2980b9", "#1f618d")
        )
        self.login_button.pack(fill=ctk.X, pady=(0, 20))
        
        # Pas de séparateur pour simplifier
        # self._create_separator(form_frame)
        
        # Lien vers l'inscription
        register_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        register_frame.pack(fill=ctk.X, pady=(10, 0))
        
        ctk.CTkLabel(
            register_frame,
            text="Vous n'avez pas de compte ?",
            anchor="center"
        ).pack(pady=(0, 5))
        
        register_link = ctk.CTkButton(
            register_frame,
            text="Créer un compte",
            font=ctk.CTkFont(size=13, underline=True),
            fg_color="transparent",
            hover_color="transparent",
            text_color=("#3498db", "#2980b9"),
            width=30,
            height=20,
            command=lambda: self._show_tab("register")
        )
        register_link.pack()
    
    def _create_separator(self, parent):
        """
        Crée un séparateur avec le texte 'ou'
        
        Args:
            parent: Widget parent
        """
        separator_frame = ctk.CTkFrame(parent, fg_color="transparent")
        separator_frame.pack(fill=ctk.X, pady=10)
        
        # Ligne gauche
        left_line = ctk.CTkFrame(separator_frame, height=1, fg_color="gray")
        left_line.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=(0, 10))
        
        # Texte "ou"
        ctk.CTkLabel(
            separator_frame,
            text="ou",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        ).pack(side=ctk.LEFT)
        
        # Ligne droite
        right_line = ctk.CTkFrame(separator_frame, height=1, fg_color="gray")
        right_line.pack(side=ctk.RIGHT, fill=ctk.X, expand=True, padx=(10, 0))
    
    def _create_register_view(self):
        """Crée la vue d'inscription"""
        self.register_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Titre
        ctk.CTkLabel(
            self.register_frame,
            text="Créer un compte",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 20))
        
        # Cadre du formulaire
        form_frame = ctk.CTkFrame(self.register_frame, fg_color="transparent")
        form_frame.pack(fill=ctk.X, padx=20)
        
        # Champ nom
        name_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        name_frame.pack(fill=ctk.X, pady=(0, 15))
        
        ctk.CTkLabel(
            name_frame,
            text="Nom complet",
            anchor="w"
        ).pack(fill=ctk.X, padx=5, pady=(0, 5))
        
        self.name_var = ctk.StringVar()
        self.register_name = ctk.CTkEntry(
            name_frame,
            textvariable=self.name_var,
            placeholder_text="Votre nom complet",
            height=40,
            border_width=1
        )
        self.register_name.pack(fill=ctk.X)
        
        # Message d'erreur nom
        self.register_name_error = ctk.CTkLabel(
            name_frame,
            text="",
            text_color="red",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.register_name_error.pack(fill=ctk.X, padx=5)
        
        # Champ email
        email_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        email_frame.pack(fill=ctk.X, pady=(0, 15))
        
        ctk.CTkLabel(
            email_frame,
            text="Adresse email",
            anchor="w"
        ).pack(fill=ctk.X, padx=5, pady=(0, 5))
        
        self.register_email = ctk.CTkEntry(
            email_frame,
            textvariable=self.email_var,
            placeholder_text="Votre adresse email",
            height=40,
            border_width=1
        )
        self.register_email.pack(fill=ctk.X)
        
        # Message d'erreur email
        self.register_email_error = ctk.CTkLabel(
            email_frame,
            text="",
            text_color="red",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.register_email_error.pack(fill=ctk.X, padx=5)
        
        # Champ mot de passe
        password_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        password_frame.pack(fill=ctk.X, pady=(0, 15))
        
        ctk.CTkLabel(
            password_frame,
            text="Mot de passe",
            anchor="w"
        ).pack(fill=ctk.X, padx=5, pady=(0, 5))
        
        self.register_password = ctk.CTkEntry(
            password_frame,
            textvariable=self.password_var,
            placeholder_text="Créez un mot de passe sécurisé",
            show="•",
            height=40,
            border_width=1
        )
        self.register_password.pack(fill=ctk.X)
        
        # Message d'erreur mot de passe
        self.register_password_error = ctk.CTkLabel(
            password_frame,
            text="",
            text_color="red",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.register_password_error.pack(fill=ctk.X, padx=5)
        
        # Indicateur de force du mot de passe
        self.password_strength_frame = ctk.CTkFrame(password_frame, fg_color="transparent")
        self.password_strength_frame.pack(fill=ctk.X, padx=5, pady=(5, 0))
        
        self.password_strength_indicator = ctk.CTkProgressBar(
            self.password_strength_frame,
            width=200,
            height=8,
            corner_radius=2,
            mode="determinate"
        )
        self.password_strength_indicator.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
        self.password_strength_indicator.set(0)
        
        self.password_strength_label = ctk.CTkLabel(
            self.password_strength_frame,
            text="Faible",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.password_strength_label.pack(side=ctk.RIGHT, padx=(10, 0))
        
        # Champ confirmation de mot de passe
        confirm_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        confirm_frame.pack(fill=ctk.X, pady=(0, 15))
        
        ctk.CTkLabel(
            confirm_frame,
            text="Confirmer le mot de passe",
            anchor="w"
        ).pack(fill=ctk.X, padx=5, pady=(0, 5))
        
        self.register_confirm = ctk.CTkEntry(
            confirm_frame,
            textvariable=self.confirm_password_var,
            placeholder_text="Confirmez votre mot de passe",
            show="•",
            height=40,
            border_width=1
        )
        self.register_confirm.pack(fill=ctk.X)
        
        # Message d'erreur confirmation
        self.register_confirm_error = ctk.CTkLabel(
            confirm_frame,
            text="",
            text_color="red",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.register_confirm_error.pack(fill=ctk.X, padx=5)
        
        # Conditions d'utilisation
        terms_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        terms_frame.pack(fill=ctk.X, pady=(0, 20))
        
        self.terms_var = ctk.BooleanVar(value=False)
        terms_checkbox = ctk.CTkCheckBox(
            terms_frame,
            text="J'accepte les ",
            variable=self.terms_var,
            border_width=2,
            corner_radius=6,
            hover_color=("#3498db", "#2980b9"),
            fg_color=("#3498db", "#2980b9")
        )
        terms_checkbox.pack(side=ctk.LEFT, padx=5)
        
        terms_link = ctk.CTkButton(
            terms_frame,
            text="conditions d'utilisation",
            font=ctk.CTkFont(size=13, underline=True),
            fg_color="transparent",
            hover_color="transparent",
            text_color=("#3498db", "#2980b9"),
            width=30,
            height=20,
            command=self._show_terms
        )
        terms_link.pack(side=ctk.LEFT, padx=0)
        
        # Bouton d'inscription
        self.register_button = ctk.CTkButton(
            form_frame,
            text="Créer mon compte",
            command=self._handle_register,
            height=40,
            corner_radius=8,
            fg_color=("#3498db", "#2980b9"),
            hover_color=("#2980b9", "#1f618d")
        )
        self.register_button.pack(fill=ctk.X, pady=(0, 20))
        
        # Séparateur ou
        self._create_separator(form_frame)
        
        # Bouton d'authentification Google
        google_button = ctk.CTkButton(
            form_frame,
            text="S'inscrire avec Google",
            image=self._get_google_icon(),
            compound="left",
            command=self._handle_google_auth,
            height=40,
            corner_radius=8,
            fg_color=("#ffffff", "#333333"),
            text_color=("#333333", "#ffffff"),
            hover_color=("#eeeeee", "#444444"),
            border_width=1,
            border_color=("#dddddd", "#555555")
        )
        google_button.pack(fill=ctk.X, pady=(0, 10))
        
        # Déjà un compte ?
        login_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        login_frame.pack(fill=ctk.X, pady=(10, 0))
        
        ctk.CTkLabel(
            login_frame,
            text="Déjà un compte ?",
            font=ctk.CTkFont(size=13)
        ).pack(side=ctk.LEFT, padx=(5, 5))
        
        login_link = ctk.CTkButton(
            login_frame,
            text="Se connecter",
            font=ctk.CTkFont(size=13, underline=True),
            fg_color="transparent",
            hover_color="transparent",
            text_color=("#3498db", "#2980b9"),
            width=30,
            height=20,
            command=lambda: self._show_tab("login")
        )
        login_link.pack(side=ctk.LEFT)
    
    def _create_account_view(self):
        """Crée la vue du compte utilisateur"""
        # Ne rien faire - la vue account est maintenant gérée ailleurs
        logger.info("Vue du compte utilisateur désactivée dans AuthView")
        pass
    
    def _handle_keyboard_nav(self, event):
        """
        Gère la navigation au clavier pour améliorer l'accessibilité
        
        Args:
            event: Événement clavier
        """
        try:
            # Récupérer la touche pressée
            key = event.keysym
            
            # Gérer la touche Tab pour la navigation entre les champs
            if key == "Tab":
                # La navigation par défaut est gérée par Tkinter
                pass
                
            # Gérer la touche Entrée pour soumettre le formulaire
            elif key == "Return":
                # Déterminer l'onglet actif
                current_tab = self.current_tab.get()
                
                # Soumettre le formulaire correspondant
                if current_tab == "login":
                    self._handle_login()
                elif current_tab == "register":
                    self._handle_register()
                elif current_tab == "account":
                    self._save_profile()
                    
            # Gérer les touches de navigation entre les onglets
            elif key == "1" and event.state & 4:  # Ctrl+1
                self._show_tab("login")
            elif key == "2" and event.state & 4:  # Ctrl+2
                self._show_tab("register")
            elif key == "3" and event.state & 4:  # Ctrl+3
                self._show_tab("account")
                
            # Gérer la touche Échap pour fermer la fenêtre
            elif key == "Escape":
                self.hide()
        except Exception as e:
            logger.error(f"Erreur lors de la gestion de la navigation au clavier: {e}")

    def _check_login_attempts(self, email):
        """
        Vérifie si l'utilisateur a dépassé le nombre maximum de tentatives de connexion
        
        Args:
            email: Email de l'utilisateur
            
        Returns:
            bool: True si l'utilisateur peut tenter de se connecter, False sinon
        """
        try:
            # Si l'email n'est pas dans le dictionnaire des tentatives, autoriser
            if email not in self.login_attempts:
                return True
                
            # Récupérer les informations sur les tentatives
            timestamp, count = self.login_attempts[email]
            
            # Vérifier si le délai d'attente est écoulé
            elapsed = (datetime.now() - timestamp).total_seconds()
            if elapsed > self.LOGIN_TIMEOUT:
                # Réinitialiser les tentatives
                del self.login_attempts[email]
                return True
                
            # Vérifier si le nombre maximum de tentatives est atteint
            if count >= self.MAX_LOGIN_ATTEMPTS:
                logger.warning(f"Nombre maximum de tentatives atteint pour {email}")
                return False
                
            # Autoriser la tentative
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des tentatives de connexion: {e}")
            # En cas d'erreur, autoriser par défaut
            return True
        
    def _handle_logout(self):
        """Gère la déconnexion de l'utilisateur"""
        try:
            # Vérifier si un utilisateur est connecté
            if not self.current_user:
                logger.warning("Tentative de déconnexion sans utilisateur connecté")
                return
                
            # Déconnecter l'utilisateur
            email = self.current_user.get("email", "")
            success = self.usage_tracker.clear_current_user()
            
            if success:
                logger.info(f"Utilisateur déconnecté: {email}")
                
                # Réinitialiser l'utilisateur courant
                self.current_user = None
                
                # Mettre à jour l'interface
                self._update_auth_state()
                
                # Appeler le callback d'authentification si défini
                if hasattr(self, 'auth_callback') and self.auth_callback:
                    self.auth_callback(False, None)
                
                # Afficher l'onglet login
                self._show_tab("login")
                
                # Afficher un message de succès
                if hasattr(self, 'login_status_label'):
                    self.login_status_label.configure(
                        text="Déconnexion réussie",
                        text_color="green"
                    )
                    # Effacer le message après 3 secondes
                    self.window.after(3000, lambda: self.login_status_label.configure(text=""))
            else:
                logger.error(f"Erreur lors de la déconnexion de {email}")
                
                # Afficher un message d'erreur
                if hasattr(self, 'login_status_label'):
                    self.login_status_label.configure(
                        text="Erreur lors de la déconnexion",
                        text_color="red"
                    )
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion: {e}")
            
            # Afficher un message d'erreur
            if hasattr(self, 'login_status_label'):
                self.login_status_label.configure(
                    text=f"Erreur: {str(e)}",
                    text_color="red"
                )
        
    def _get_google_icon(self):
        """Récupère l'icône Google ou crée une icône temporaire"""
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "google_icon.png")
            if os.path.exists(icon_path):
                return ctk.CTkImage(Image.open(icon_path), size=(20, 20))
            else:
                # Créer une icône Google factice
                logger.info("Icône Google non trouvée, création d'une icône factice")
                # Créer une image avec un G blanc sur fond rouge
                img = Image.new("RGB", (20, 20), color=(234, 67, 53))  # Rouge Google
                return ctk.CTkImage(img, size=(20, 20))
        except Exception as e:
            logger.warning(f"Impossible de charger l'icône Google: {e}")
            # Si une erreur se produit, retourner une image vide
            img = Image.new("RGB", (20, 20), color=(255, 255, 255))
            return ctk.CTkImage(img, size=(20, 20))

    def _show_tab(self, tab_name):
        """
        Affiche un onglet spécifique
        
        Args:
            tab_name: Nom de l'onglet à afficher (login, register, account)
        """
        try:
            logger.info(f"Demande d'affichage de l'onglet: {tab_name}")
            
            # Si l'onglet est "account", utiliser la vue AccountView directement
            if tab_name == "account":
                logger.info("Redirection vers la vue AccountView")
                self.hide()  # Masquer cette vue
                
                # Rediriger vers la vue account via MainView si possible
                try:
                    from views.main_view import get_main_view_instance
                    main_view = get_main_view_instance()
                    if main_view and hasattr(main_view, 'show_account'):
                        main_view.show_account()
                        return
                except Exception as e:
                    logger.error(f"Erreur lors de la redirection vers AccountView: {e}")
                
                # Sinon essayer d'utiliser le bouton d'authentification du dashboard
                try:
                    # Rechercher le bouton d'authentification dans la hiérarchie des widgets
                    root = self.window.winfo_toplevel()
                    for widget in root.winfo_children():
                        if hasattr(widget, "_show_user_account"):
                            widget._show_user_account()
                            return
                except Exception as e:
                    logger.error(f"Erreur lors de la recherche du bouton d'authentification: {e}")
                
                # Si ça échoue, afficher un message
                self.hide()
                self.window.after(100, lambda: CTkMessagebox(
                    title="Accès au compte",
                    message="Utilisez le bouton 'Mon compte' du tableau de bord pour accéder à votre compte.",
                    icon="info"
                ))
                return
            
            # Pour les autres onglets, continuer normalement
            # Mettre à jour la variable d'onglet actuel
            self.current_tab.set(tab_name)
            
            # Mettre en évidence l'onglet actuel
            if hasattr(self, 'login_tab'):
                self.login_tab.configure(fg_color="transparent" if tab_name != "login" else ("gray85", "gray25"))
            if hasattr(self, 'register_tab'):
                self.register_tab.configure(fg_color="transparent" if tab_name != "register" else ("gray85", "gray25"))
            if hasattr(self, 'account_tab'):
                self.account_tab.configure(fg_color="transparent" if tab_name != "account" else ("gray85", "gray25"))
            
            # Mettre à jour l'affichage en fonction de l'onglet sélectionné
            self._update_tab_content()
            
            logger.debug(f"Onglet {tab_name} affiché avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de l'onglet {tab_name}: {e}")
            # Tenter une approche alternative en cas d'erreur
            self._show_tab_alternative(tab_name)
    
    def _update_tab_content(self):
        """Met à jour le contenu affiché selon l'onglet sélectionné"""
        try:
            tab_name = self.current_tab.get()
            
            # Masquer tous les contenus d'onglets
            for content in ["login_frame", "register_frame", "account_frame"]:
                if hasattr(self, content) and getattr(self, content):
                    getattr(self, content).pack_forget()
            
            # Afficher le contenu approprié
            if tab_name == "login" and hasattr(self, 'login_frame'):
                self.login_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            elif tab_name == "register" and hasattr(self, 'register_frame'):
                self.register_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            elif tab_name == "account" and hasattr(self, 'account_frame'):
                self.account_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            
            # Mettre à jour les styles des onglets
            if hasattr(self, 'tabs') and self.tabs:
                for tab in self.tabs.winfo_children():
                    tab_id = tab.cget("text").lower()
                    if tab_id == tab_name:
                        tab.configure(fg_color=("gray85", "gray25"))
                    else:
                        tab.configure(fg_color="transparent")
                        
            logger.debug(f"Contenu de l'onglet {tab_name} affiché")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du contenu de l'onglet: {e}")
            # En cas d'erreur, on peut essayer une approche plus directe
            try:
                if tab_name == "login" and hasattr(self, 'login_frame'):
                    for content in ["register_frame", "account_frame"]:
                        if hasattr(self, content) and getattr(self, content):
                            getattr(self, content).pack_forget()
                    self.login_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
                elif tab_name == "register" and hasattr(self, 'register_frame'):
                    for content in ["login_frame", "account_frame"]:
                        if hasattr(self, content) and getattr(self, content):
                            getattr(self, content).pack_forget()
                    self.register_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
                elif tab_name == "account" and hasattr(self, 'account_frame'):
                    for content in ["login_frame", "register_frame"]:
                        if hasattr(self, content) and getattr(self, content):
                            getattr(self, content).pack_forget()
                    self.account_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
                    
                logger.debug(f"Contenu de l'onglet {tab_name} affiché via méthode alternative")
            except Exception as e2:
                logger.error(f"Échec critique lors de l'affichage alternatif de l'onglet: {e2}")
    
    def _load_user_data(self):
        """
        Charge les données de l'utilisateur actuellement connecté
        et met à jour l'interface en conséquence
        """
        try:
            # Récupérer les données utilisateur
            user_data = self.usage_tracker.get_user_data()
            
            if user_data and "email" in user_data:
                self.current_user = user_data
                logger.info(f"Utilisateur chargé: {user_data.get('email')}")
                
                # Mettre à jour les champs du profil
                if hasattr(self, 'user_name_label'):
                    name = user_data.get('name', 'Utilisateur')
                    self.user_name_label.configure(text=name)
                
                if hasattr(self, 'user_email_label'):
                    email = user_data.get('email', '')
                    self.user_email_label.configure(text=email)
                
                # Mettre à jour les autres champs du profil si disponibles
                if hasattr(self, 'profile_name_var') and 'name' in user_data:
                    self.profile_name_var.set(user_data['name'])
                
                if hasattr(self, 'profile_email_var') and 'email' in user_data:
                    self.profile_email_var.set(user_data['email'])
                
                if hasattr(self, 'profile_created_var') and 'created_at' in user_data:
                    created_at = user_data.get('created_at', '')
                    if created_at:
                        try:
                            # Formater la date si c'est une chaîne ISO
                            date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            formatted_date = date_obj.strftime('%d/%m/%Y %H:%M')
                            self.profile_created_var.set(formatted_date)
                        except:
                            self.profile_created_var.set(created_at)
                
                # Appeler le callback d'authentification si défini
                if hasattr(self, 'auth_callback') and self.auth_callback:
                    self.auth_callback(True, user_data)
            else:
                self.current_user = None
                logger.info("Aucun utilisateur connecté")
                
                # Appeler le callback d'authentification si défini
                if hasattr(self, 'auth_callback') and self.auth_callback:
                    self.auth_callback(False, None)
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données utilisateur: {e}")
            self.current_user = None
    
    def _update_auth_state(self):
        """
        Met à jour l'interface en fonction de l'état d'authentification
        """
        try:
            # Vérifier si un utilisateur est connecté
            is_logged_in = self.current_user is not None
            
            # Mettre à jour la visibilité des onglets
            if is_logged_in:
                # Afficher l'onglet Compte et masquer l'onglet Inscription
                if hasattr(self, 'account_tab') and self.account_tab:
                    self.account_tab.grid()
                
                # Si on est sur l'onglet login ou register, basculer vers account
                current_tab = self.current_tab.get()
                if current_tab in ["login", "register"]:
                    self._show_tab("account")
            else:
                # Masquer l'onglet Compte si on n'est pas connecté
                # et qu'on est sur cet onglet, basculer vers login
                current_tab = self.current_tab.get()
                if current_tab == "account":
                    self._show_tab("login")
            
            # Mettre à jour les boutons de connexion/déconnexion
            if hasattr(self, 'login_button') and hasattr(self, 'logout_button'):
                if self.login_button and self.logout_button:
                    if is_logged_in:
                        if self.login_button and self.login_button.winfo_exists():
                            self.login_button.pack_forget()
                        if self.logout_button and self.logout_button.winfo_exists():
                            self.logout_button.pack(fill=ctk.X, pady=(10, 0))
                    else:
                        if self.logout_button and self.logout_button.winfo_exists():
                            self.logout_button.pack_forget()
                        if self.login_button and self.login_button.winfo_exists():
                            self.login_button.pack(fill=ctk.X, pady=(10, 0))
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'état d'authentification: {e}")
            
    def _save_user_settings(self, user_data: Dict[str, Any]) -> bool:
        """
        Sauvegarde les paramètres de l'utilisateur
        
        Args:
            user_data: Données utilisateur à sauvegarder
            
        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        try:
            if not user_data or "email" not in user_data:
                logger.error("Données utilisateur invalides")
                return False
                
            # Récupérer les utilisateurs existants
            users_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users.json")
            users = {}
            
            if os.path.exists(users_file):
                try:
                    with open(users_file, 'r', encoding='utf-8') as f:
                        users = json.load(f)
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture des utilisateurs: {e}")
            
            # Mettre à jour les données de l'utilisateur
            email = user_data.get("email")
            
            # Supprimer l'email des données pour éviter la duplication
            user_data_copy = user_data.copy()
            if "email" in user_data_copy:
                del user_data_copy["email"]
                
            # Mettre à jour les données
            users[email] = user_data_copy
            
            # Sauvegarder les utilisateurs
            os.makedirs(os.path.dirname(users_file), exist_ok=True)
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Paramètres utilisateur sauvegardés pour {email}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des paramètres utilisateur: {e}")
            return False
            
    def _save_profile(self):
        """Sauvegarde les modifications du profil utilisateur"""
        try:
            if not self.current_user:
                logger.error("Aucun utilisateur connecté")
                return
                
            # Récupérer les valeurs des champs
            name = self.profile_name_var.get() if hasattr(self, 'profile_name_var') else ""
            
            # Mettre à jour les données utilisateur
            user_data = self.current_user.copy()
            user_data["name"] = name
            
            # Sauvegarder les modifications
            if self._save_user_settings(user_data):
                # Mettre à jour l'utilisateur courant
                self.current_user = user_data
                
                # Mettre à jour l'interface
                if hasattr(self, 'user_name_label'):
                    self.user_name_label.configure(text=name)
                    
                # Afficher un message de succès
                logger.info("Profil mis à jour avec succès")
                
                # Afficher un message dans l'interface
                if hasattr(self, 'profile_status_label'):
                    self.profile_status_label.configure(
                        text="Profil mis à jour avec succès",
                        text_color="green"
                    )
                    # Effacer le message après 3 secondes
                    self.window.after(3000, lambda: self.profile_status_label.configure(text=""))
            else:
                # Afficher un message d'erreur
                logger.error("Erreur lors de la mise à jour du profil")
                
                # Afficher un message dans l'interface
                if hasattr(self, 'profile_status_label'):
                    self.profile_status_label.configure(
                        text="Erreur lors de la mise à jour du profil",
                        text_color="red"
                    )
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du profil: {e}")
            
            # Afficher un message dans l'interface
            if hasattr(self, 'profile_status_label'):
                self.profile_status_label.configure(
                    text=f"Erreur: {str(e)}",
                    text_color="red"
                )
                
    def _handle_login(self):
        """Gère la connexion de l'utilisateur"""
        try:
            # Récupérer les valeurs des champs
            email = self.email_var.get()
            password = self.password_var.get()
            remember_me = self.remember_var.get() if hasattr(self, 'remember_var') else False
            
            # Vérifier que les champs sont remplis
            if not email or not password:
                logger.warning("Champs de connexion incomplets")
                if hasattr(self, 'login_status_label'):
                    self.login_status_label.configure(
                        text="Veuillez remplir tous les champs",
                        text_color="red"
                    )
                return
            
            # Vérifier le format de l'email
            if not self._is_valid_email(email):
                logger.warning("Format d'email invalide")
                if hasattr(self, 'login_status_label'):
                    self.login_status_label.configure(
                        text="Format d'email invalide",
                        text_color="red"
                    )
                return
            
            # Vérifier les tentatives de connexion
            if not self._check_login_attempts(email):
                logger.warning(f"Trop de tentatives de connexion pour {email}")
                if hasattr(self, 'login_status_label'):
                    self.login_status_label.configure(
                        text=f"Trop de tentatives, réessayez dans {self.LOGIN_TIMEOUT//60} minutes",
                        text_color="red"
                    )
                return
            
            # Vérifier les identifiants
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            user_data = self.usage_tracker.authenticate_user(email, hashed_password)
            
            if user_data:
                logger.info(f"Utilisateur connecté: {email} (Rester connecté: {remember_me})")
                
                # Mettre à jour l'utilisateur courant
                self.current_user = user_data
                
                # Enregistrer la préférence "Rester connecté"
                self.usage_tracker.set_remember_me(email, remember_me)
                logger.info(f"Préférence 'Rester connecté' définie à {remember_me} pour {email}")
                
                # Réinitialiser les tentatives de connexion
                if email in self.login_attempts:
                    del self.login_attempts[email]
                
                # Mettre à jour l'interface
                self._update_auth_state()
                
                # Masquer la fenêtre d'authentification
                self.hide()
                
                # Appeler le callback d'authentification si défini
                if hasattr(self, 'auth_callback') and self.auth_callback:
                    self.auth_callback(True, user_data)
                
                # Restaurer complètement l'interface principale
                if hasattr(self.parent, 'main_frame') and self.parent.main_frame:
                    # S'assurer que tous les widgets sont visibles et correctement positionnés
                    try:
                        if not self.parent.main_frame.winfo_ismapped():
                            self.parent.main_frame.pack(fill="both", expand=True)
                            logger.info("Interface principale restaurée après connexion")
                    except Exception as e:
                        logger.error(f"Erreur lors de la restauration de l'interface principale: {e}")
                
                # S'assurer que le tableau de bord est affiché
                if hasattr(self.parent, 'show_dashboard'):
                    try:
                        self.parent.show_dashboard()
                        logger.info("Tableau de bord affiché après connexion")
                    except Exception as e:
                        logger.error(f"Erreur lors de l'affichage du tableau de bord: {e}")
                
                # Charger les paramètres utilisateur
                self._load_user_data()
                
                return True
            else:
                logger.warning(f"Échec de connexion pour {email}")
                
                # Incrémenter les tentatives de connexion
                if email in self.login_attempts:
                    self.login_attempts[email][1] += 1
                else:
                    self.login_attempts[email] = [datetime.now(), 1]
                
                # Afficher un message d'erreur
                if hasattr(self, 'login_status_label'):
                    self.login_status_label.configure(
                        text="Email ou mot de passe incorrect",
                        text_color="red"
                    )
                
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la connexion: {e}")
            
            # Afficher un message d'erreur
            if hasattr(self, 'login_status_label'):
                self.login_status_label.configure(
                    text=f"Erreur: {str(e)}",
                    text_color="red"
                )
            
            return False
            
    def _is_valid_email(self, email):
        """Vérifie si l'email est valide"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
        
    def _handle_register(self):
        """Gère l'inscription d'un nouvel utilisateur"""
        try:
            # Récupérer les valeurs des champs
            name = self.register_name_var.get() if hasattr(self, 'register_name_var') else ""
            email = self.email_var.get()
            password = self.password_var.get()
            confirm_password = self.confirm_password_var.get()
            
            # Vérifier que les champs sont remplis
            if not email or not password or not confirm_password:
                logger.warning("Champs d'inscription incomplets")
                if hasattr(self, 'register_status_label'):
                    self.register_status_label.configure(
                        text="Veuillez remplir tous les champs obligatoires",
                        text_color="red"
                    )
                return False
            
            # Vérifier le format de l'email
            if not self._is_valid_email(email):
                logger.warning("Format d'email invalide")
                if hasattr(self, 'register_status_label'):
                    self.register_status_label.configure(
                        text="Format d'email invalide",
                        text_color="red"
                    )
                return False
            
            # Vérifier que les mots de passe correspondent
            if password != confirm_password:
                logger.warning("Les mots de passe ne correspondent pas")
                if hasattr(self, 'register_status_label'):
                    self.register_status_label.configure(
                        text="Les mots de passe ne correspondent pas",
                        text_color="red"
                    )
                return False
            
            # Vérifier la complexité du mot de passe
            if len(password) < self.PASSWORD_MIN_LENGTH:
                logger.warning("Mot de passe trop court")
                if hasattr(self, 'register_status_label'):
                    self.register_status_label.configure(
                        text=f"Le mot de passe doit contenir au moins {self.PASSWORD_MIN_LENGTH} caractères",
                        text_color="red"
                    )
                return False
            
            # Vérifier si l'utilisateur existe déjà
            users_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users.json")
            users = {}
            
            if os.path.exists(users_file):
                try:
                    with open(users_file, 'r', encoding='utf-8') as f:
                        users = json.load(f)
                        
                    if email in users:
                        logger.warning(f"L'utilisateur {email} existe déjà")
                        if hasattr(self, 'register_status_label'):
                            self.register_status_label.configure(
                                text="Cet email est déjà utilisé",
                                text_color="red"
                            )
                        return False
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture des utilisateurs: {e}")
            
            # Créer le nouvel utilisateur
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            user_data = {
                "email": email,
                "password": hashed_password,
                "name": name,
                "created_at": datetime.now().isoformat(),
                "last_login": datetime.now().isoformat(),
                "settings": {}
            }
            
            # Sauvegarder l'utilisateur
            users[email] = {k: v for k, v in user_data.items() if k != "email"}
            
            os.makedirs(os.path.dirname(users_file), exist_ok=True)
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Nouvel utilisateur créé: {email}")
            
            # Connecter l'utilisateur
            self.current_user = user_data
            self.usage_tracker.set_current_user(user_data)
            
            # Mettre à jour l'interface
            self._update_auth_state()
            
            # Afficher un message de succès temporaire
            if hasattr(self, 'register_status_label'):
                self.register_status_label.configure(
                    text="Inscription réussie ! Redirection vers le tableau de bord...",
                    text_color="green"
                )
            
            # Créer un spinner de chargement pendant la redirection
            loading_frame = None
            try:
                loading_frame = ctk.CTkFrame(self.window)
                loading_frame.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)
                
                # Titre du chargement
                ctk.CTkLabel(
                    loading_frame,
                    text="Préparation du tableau de bord",
                    font=ctk.CTkFont(size=16, weight="bold")
                ).pack(pady=(10, 5))
                
                # Message
                ctk.CTkLabel(
                    loading_frame,
                    text="Veuillez patienter pendant l'initialisation de votre tableau de bord..."
                ).pack(pady=5)
                
                # Spinner
                spinner = ctk.CTkProgressBar(loading_frame, width=200)
                spinner.pack(pady=10)
                spinner.configure(mode="indeterminate")
                spinner.start()
                
                # Forcer la mise à jour de l'interface
                self.window.update()
            except Exception as e:
                logger.error(f"Erreur lors de la création du spinner: {e}")
            
            # Appeler le callback d'authentification si défini après un court délai
            def complete_registration():
                try:
                    # Appeler le callback d'authentification si défini
                    if hasattr(self, 'auth_callback') and self.auth_callback:
                        self.auth_callback(True, user_data)
                    
                    # Fermer la fenêtre d'authentification
                    self.hide()
                    
                    # Afficher un message de succès et rediriger vers le tableau de bord
                    if hasattr(self.parent, 'show_dashboard') and callable(self.parent.show_dashboard):
                        # Rediriger vers le tableau de bord
                        self.parent.show_dashboard()
                        logger.info("Utilisateur redirigé vers le tableau de bord après inscription")
                    else:
                        logger.warning("Impossible de rediriger vers le tableau de bord: méthode non trouvée")
                        # Tentative alternative pour afficher le tableau de bord
                        try:
                            if hasattr(self.parent, 'show_view') and callable(self.parent.show_view):
                                self.parent.show_view("dashboard")
                                logger.info("Redirection alternative vers le tableau de bord")
                            elif hasattr(self.parent, 'winfo_toplevel') and hasattr(self.parent.winfo_toplevel(), 'show_view'):
                                # Si nous sommes dans une fenêtre modale, essayer avec la fenêtre principale
                                self.parent.winfo_toplevel().show_view("dashboard")
                                logger.info("Redirection via la fenêtre principale vers le tableau de bord")
                        except Exception as e:
                            logger.error(f"Erreur lors de la redirection vers le tableau de bord: {e}")
                    
                    # Afficher un message de bienvenue
                    if hasattr(self.parent, 'show_message'):
                        self.parent.show_message(
                            "Inscription réussie",
                            f"Bienvenue {name if name else email} ! Votre compte a été créé avec succès.",
                            "success"
                        )
                except Exception as e:
                    logger.error(f"Erreur lors de la finalisation de l'inscription: {e}")
                    if loading_frame and loading_frame.winfo_exists():
                        loading_frame.destroy()
            
            # Déclencher la redirection après un court délai pour permettre l'affichage du spinner
            self.window.after(500, complete_registration)
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'inscription: {e}")
            
            # Afficher un message d'erreur
            if hasattr(self, 'register_status_label'):
                self.register_status_label.configure(
                    text=f"Erreur: {str(e)}",
                    text_color="red"
                )
            
            return False
            
    def _validate_email(self, *args):
        """Valide le format de l'email en temps réel"""
        try:
            email = self.email_var.get()
            
            # Vérifier si l'email est vide
            if not email:
                self.email_valid = False
                
                # Mettre à jour les messages d'erreur
                if hasattr(self, 'login_email_error'):
                    self.login_email_error.configure(text="")
                if hasattr(self, 'register_email_error'):
                    self.register_email_error.configure(text="")
                    
                return
            
            # Vérifier le format de l'email
            is_valid = self._is_valid_email(email)
            self.email_valid = is_valid
            
            # Mettre à jour les messages d'erreur
            error_msg = "" if is_valid else "Format d'email invalide"
            
            if hasattr(self, 'login_email_error'):
                self.login_email_error.configure(text=error_msg)
                
            if hasattr(self, 'register_email_error'):
                self.register_email_error.configure(text=error_msg)
        except Exception as e:
            logger.error(f"Erreur lors de la validation de l'email: {e}")
            
    def _validate_password(self, *args):
        """Valide la complexité du mot de passe en temps réel"""
        try:
            password = self.password_var.get()
            
            # Vérifier si le mot de passe est vide
            if not password:
                self.password_valid = False
                
                # Mettre à jour les messages d'erreur
                if hasattr(self, 'login_password_error'):
                    self.login_password_error.configure(text="")
                if hasattr(self, 'register_password_error'):
                    self.register_password_error.configure(text="")
                    
                return
            
            # Vérifier la longueur du mot de passe
            is_valid = len(password) >= self.PASSWORD_MIN_LENGTH
            self.password_valid = is_valid
            
            # Mettre à jour les messages d'erreur
            error_msg = "" if is_valid else f"Minimum {self.PASSWORD_MIN_LENGTH} caractères"
            
            if hasattr(self, 'login_password_error'):
                self.login_password_error.configure(text=error_msg)
                
            if hasattr(self, 'register_password_error'):
                self.register_password_error.configure(text=error_msg)
                
            # Valider également la confirmation si elle existe
            if hasattr(self, 'confirm_password_var'):
                self._validate_confirm_password()
        except Exception as e:
            logger.error(f"Erreur lors de la validation du mot de passe: {e}")
            
    def _validate_confirm_password(self, *args):
        """Valide que la confirmation du mot de passe correspond au mot de passe"""
        try:
            password = self.password_var.get()
            confirm_password = self.confirm_password_var.get()
            
            # Vérifier si la confirmation est vide
            if not confirm_password:
                self.confirm_password_valid = False
                
                # Mettre à jour le message d'erreur
                if hasattr(self, 'register_confirm_password_error'):
                    self.register_confirm_password_error.configure(text="")
                    
                return
            
            # Vérifier que les mots de passe correspondent
            is_valid = password == confirm_password
            self.confirm_password_valid = is_valid
            
            # Mettre à jour le message d'erreur
            error_msg = "" if is_valid else "Les mots de passe ne correspondent pas"
            
            if hasattr(self, 'register_confirm_password_error'):
                self.register_confirm_password_error.configure(text=error_msg)
        except Exception as e:
            logger.error(f"Erreur lors de la validation de la confirmation du mot de passe: {e}")

    def hide(self):
        """Masque la fenêtre d'authentification"""
        try:
            # Si nous utilisons une fenêtre Toplevel, la masquer
            if hasattr(self, 'window') and self.window.winfo_exists():
                self.window.withdraw()
                logger.info("Fenêtre d'authentification masquée")
            # Si nous utilisons le parent directement, masquer les widgets
            elif hasattr(self, 'main_frame'):
                self.main_frame.pack_forget()
                logger.info("Widgets d'authentification masqués")
        except Exception as e:
            logger.error(f"Erreur lors du masquage de l'interface d'authentification: {e}")
            
    def show(self):
        """Affiche la fenêtre d'authentification"""
        try:
            # Détruire toute fenêtre TopLevel existante pour éviter les doublons
            if hasattr(self, 'window') and self.window.winfo_exists():
                try:
                    self.window.destroy()
                except Exception as e:
                    logger.debug(f"Erreur lors de la destruction de la fenêtre existante: {e}")
            
            # Créer une interface directement dans le parent
            if not hasattr(self, 'main_frame') or not self.main_frame:
                # Créer les widgets directement dans le parent
                self._create_widgets()
                logger.info("Widgets d'authentification créés directement dans le parent")
            
            # Mettre à jour l'interface selon l'état de connexion
            self._update_auth_state()
            
            # S'assurer que le contenu est visible
            if hasattr(self, 'main_frame'):
                self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Forcer la mise à jour pour éviter les problèmes d'affichage
            self.parent.update_idletasks()
            
            logger.info("Interface d'authentification affichée directement dans le parent")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de l'interface d'authentification: {e}")
            # Créer une interface de secours en cas d'erreur
            try:
                # Nettoyer l'interface existante
                for widget in self.parent.winfo_children():
                    widget.destroy()
                
                # Créer une interface minimaliste
                frame = ctk.CTkFrame(self.parent)
                frame.pack(fill="both", expand=True, padx=20, pady=20)
                
                label = ctk.CTkLabel(
                    frame,
                    text="Interface d'authentification",
                    font=ctk.CTkFont(size=16, weight="bold")
                )
                label.pack(pady=20)
                
                # Champs d'authentification simples
                email_label = ctk.CTkLabel(frame, text="Email:")
                email_label.pack(anchor="w", pady=(10, 0))
                
                self.email_var = ctk.StringVar()
                email_entry = ctk.CTkEntry(frame, width=300, textvariable=self.email_var)
                email_entry.pack(pady=(0, 10))
                
                password_label = ctk.CTkLabel(frame, text="Mot de passe:")
                password_label.pack(anchor="w", pady=(10, 0))
                
                self.password_var = ctk.StringVar()
                password_entry = ctk.CTkEntry(frame, show="•", width=300, textvariable=self.password_var)
                password_entry.pack(pady=(0, 20))
                
                login_button = ctk.CTkButton(
                    frame,
                    text="Se connecter",
                    width=200,
                    command=self._handle_login
                )
                login_button.pack(pady=10)
                
                logger.info("Interface d'authentification simplifiée créée après erreur")
            except Exception as e2:
                logger.critical(f"Échec critique lors de la création d'une interface de secours: {e2}")
                # Afficher un simple message d'erreur
                try:
                    label = ctk.CTkLabel(
                        self.parent,
                        text="Erreur lors de l'affichage de l'interface d'authentification.\nVeuillez redémarrer l'application.",
                        font=ctk.CTkFont(size=14),
                        text_color="red"
                    )
                    label.pack(expand=True, pady=50)
                except:
                    pass

    def set_auth_callback(self, callback):
        """
        Définit le callback à appeler lorsque l'état d'authentification change
        
        Args:
            callback: Fonction à appeler avec (is_authenticated, user_data)
        """
        self.auth_callback = callback
        logger.info("Callback d'authentification défini")

    def _show_tab_alternative(self, tab_name):
        """
        Méthode alternative pour afficher un onglet lorsque l'approche principale échoue
        
        Args:
            tab_name: Nom de l'onglet à afficher (login, register, account)
        """
        try:
            # Mettre à jour la variable d'onglet actuel
            self.current_tab.set(tab_name)
            
            # Si les frames d'onglets n'existent pas, essayer de les créer
            try:
                if tab_name == "login" and (not hasattr(self, 'login_frame') or not self.login_frame):
                    self._create_login_tab()
                elif tab_name == "register" and (not hasattr(self, 'register_frame') or not self.register_frame):
                    self._create_register_tab()
                elif tab_name == "account" and (not hasattr(self, 'account_frame') or not self.account_frame):
                    self._create_account_tab()
            except Exception as e:
                logger.error(f"Erreur lors de la création de l'onglet {tab_name}: {e}")
                # Continuer malgré l'erreur
            
            # Vérifier si les frames d'onglets existent maintenant
            tab_frames = {
                "login": getattr(self, 'login_frame', None),
                "register": getattr(self, 'register_frame', None),
                "account": getattr(self, 'account_frame', None)
            }
            
            # Vider le content_frame si disponible
            if hasattr(self, 'content_frame') and self.content_frame:
                for widget in self.content_frame.winfo_children():
                    try:
                        widget.pack_forget()
                    except Exception:
                        pass
            else:
                # Si content_frame n'existe pas, recréer l'UI
                self._create_widgets()
                logger.info("Interface recréée car content_frame n'existe pas")
                # Réessayer après la recréation
                self._show_tab(tab_name)
                return
            
            # Si l'onglet demandé existe maintenant, l'afficher
            if tab_frames[tab_name]:
                try:
                    self.content_frame.update_idletasks()  # Force une mise à jour des widgets
                    tab_frames[tab_name].pack(fill=ctk.BOTH, expand=True, pady=(15, 0))
                    logger.info(f"Onglet {tab_name} affiché (méthode alternative)")
                except Exception as e:
                    logger.error(f"Erreur lors de l'affichage de l'onglet {tab_name}: {e}")
                    # Continuer malgré l'erreur
            
            # Dans tous les cas, afficher un message simple si nécessaire
            if not (tab_frames[tab_name] and tab_frames[tab_name].winfo_ismapped()):
                try:
                    # Créer un frame d'erreur simple
                    error_frame = ctk.CTkFrame(self.content_frame)
                    error_frame.pack(fill=ctk.BOTH, expand=True, pady=(15, 0))
                    
                    ctk.CTkLabel(
                        error_frame,
                        text=f"Bienvenue sur Vynal Docs Automator",
                        font=ctk.CTkFont(size=18, weight="bold")
                    ).pack(pady=(20, 10))
                    
                    if tab_name == "account":
                        message = "Gestion de votre compte utilisateur"
                    elif tab_name == "register":
                        message = "Créez un compte pour commencer"
                    else:
                        message = "Connectez-vous pour continuer"
                        
                    ctk.CTkLabel(
                        error_frame,
                        text=message
                    ).pack(pady=10)
                    
                    logger.info(f"Vue simplifiée affichée pour {tab_name}")
                except Exception as e:
                    logger.error(f"Erreur lors de l'affichage du message alternatif: {e}")
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage alternatif de l'onglet {tab_name}: {e}")
            # En dernier recours, essayer de recréer complètement l'interface
            if hasattr(self, '_create_widgets'):
                try:
                    self._create_widgets()
                    logger.info("Interface recréée après erreur d'affichage d'onglet")
                except Exception as e2:
                    logger.error(f"Échec critique lors de la recréation de l'interface: {e2}")

    def _create_account_tab(self):
        """Crée le contenu de l'onglet compte"""
        try:
            if not hasattr(self, 'content_frame') or not self.content_frame:
                logger.error("content_frame n'existe pas, impossible de créer l'onglet compte")
                return

            # Créer le frame pour l'onglet compte s'il n'existe pas
            if not hasattr(self, 'account_frame') or not self.account_frame:
                self.account_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            
            # Options de style
            title_font = ctk.CTkFont(size=18, weight="bold")
            section_font = ctk.CTkFont(size=14, weight="bold")
            
            # Titre
            title_frame = ctk.CTkFrame(self.account_frame, fg_color="transparent")
            title_frame.pack(fill=ctk.X, pady=(0, 15))
            
            ctk.CTkLabel(
                title_frame, 
                text="Mon Compte", 
                font=title_font
            ).pack(anchor=ctk.W)
            
            # Informations utilisateur
            if hasattr(self, 'current_user') and self.current_user:
                # Frame d'informations
                info_frame = ctk.CTkFrame(self.account_frame)
                info_frame.pack(fill=ctk.X, pady=10)
                
                # Email et nom
                user_details = ctk.CTkFrame(info_frame, fg_color="transparent")
                user_details.pack(fill=ctk.X, padx=15, pady=15)
                
                ctk.CTkLabel(
                    user_details,
                    text="Informations personnelles",
                    font=section_font
                ).pack(anchor=ctk.W, pady=(0, 10))
                
                # Email
                email_frame = ctk.CTkFrame(user_details, fg_color="transparent")
                email_frame.pack(fill=ctk.X, pady=5)
                
                ctk.CTkLabel(
                    email_frame,
                    text="Email:",
                    width=100,
                    anchor="w"
                ).pack(side=ctk.LEFT)
                
                ctk.CTkLabel(
                    email_frame,
                    text=self.current_user.get('email', 'Non défini'),
                    anchor="w"
                ).pack(side=ctk.LEFT, fill=ctk.X, expand=True)
                
                # Nom (si disponible)
                if 'name' in self.current_user:
                    name_frame = ctk.CTkFrame(user_details, fg_color="transparent")
                    name_frame.pack(fill=ctk.X, pady=5)
                    
                    ctk.CTkLabel(
                        name_frame,
                        text="Nom:",
                        width=100,
                        anchor="w"
                    ).pack(side=ctk.LEFT)
                    
                    ctk.CTkLabel(
                        name_frame,
                        text=self.current_user.get('name', 'Non défini'),
                        anchor="w"
                    ).pack(side=ctk.LEFT, fill=ctk.X, expand=True)
                
                # Licence (si disponible)
                if 'license_valid' in self.current_user:
                    is_valid = self.current_user.get('license_valid', False)
                    
                    license_frame = ctk.CTkFrame(self.account_frame)
                    license_frame.pack(fill=ctk.X, pady=10)
                    
                    license_title = ctk.CTkFrame(license_frame, fg_color="transparent")
                    license_title.pack(fill=ctk.X, padx=15, pady=(15, 10))
                    
                    ctk.CTkLabel(
                        license_title,
                        text="Licence",
                        font=section_font
                    ).pack(anchor=ctk.W)
                    
                    status_frame = ctk.CTkFrame(license_frame, fg_color="transparent")
                    status_frame.pack(fill=ctk.X, padx=15, pady=5)
                    
                    status_text = "Active" if is_valid else "Inactive"
                    status_color = "#4CAF50" if is_valid else "#F44336"
                    
                    ctk.CTkLabel(
                        status_frame,
                        text="Statut:",
                        width=100,
                        anchor="w"
                    ).pack(side=ctk.LEFT)
                    
                    ctk.CTkLabel(
                        status_frame,
                        text=status_text,
                        text_color=status_color,
                        anchor="w"
                    ).pack(side=ctk.LEFT, fill=ctk.X, expand=True)
            else:
                # Message si aucun utilisateur n'est connecté
                ctk.CTkLabel(
                    self.account_frame,
                    text="Aucun utilisateur connecté",
                    font=section_font
                ).pack(pady=20)
            
            # Boutons d'action
            buttons_frame = ctk.CTkFrame(self.account_frame, fg_color="transparent")
            buttons_frame.pack(fill=ctk.X, pady=(20, 10))
            
            # Bouton de déconnexion
            logout_button = ctk.CTkButton(
                buttons_frame,
                text="Déconnexion",
                command=self._handle_logout,
                fg_color="#E74C3C",
                hover_color="#C0392B"
            )
            logout_button.pack(pady=5)
            
            # Bouton pour fermer la fenêtre
            close_button = ctk.CTkButton(
                buttons_frame,
                text="Fermer",
                command=self.hide
            )
            close_button.pack(pady=5)
            
            logger.info("Onglet compte créé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'onglet compte: {e}")