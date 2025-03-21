#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire de réinitialisation de mot de passe pour l'interface d'administration
"""

import logging
import customtkinter as ctk
from datetime import datetime, timedelta
import os
import uuid
import secrets
import string
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

from admin.utils.security import send_secure_email
from admin.utils.config import get_smtp_config
from admin.utils.validation import validate_email

logger = logging.getLogger("VynalDocsAutomator.Admin.PasswordResetManager")

class PasswordResetManager:
    """Gestionnaire de réinitialisation de mot de passe sécurisée"""
    
    def __init__(self, parent: ctk.CTkFrame, app_model: Any) -> None:
        """Initialise le gestionnaire"""
        self.parent = parent
        self.model = app_model
        self.reset_tokens = {}
        
        # Créer le répertoire de stockage des jetons
        self.tokens_dir = self._get_tokens_dir()
        os.makedirs(self.tokens_dir, exist_ok=True)
        
        # Charger les tokens existants
        self._load_tokens()
        
        # Créer l'interface
        self.frame = ctk.CTkFrame(parent)
        self.create_widgets()
        
        # Planifier le nettoyage des tokens expirés
        self._schedule_token_cleanup()
        
        logger.info("PasswordResetManager initialisé")
    
    def show(self) -> None:
        """Affiche la vue"""
        self.frame.pack(fill=ctk.BOTH, expand=True)
        self.refresh_token_list()
    
    def hide(self) -> None:
        """Cache la vue"""
        self.frame.pack_forget()
    
    def _get_tokens_dir(self) -> str:
        """Retourne le répertoire de stockage des jetons"""
        return os.path.join(self.model.admin_dir, 'data', 'password_reset_tokens')
    
    def _load_tokens(self) -> None:
        """Charge les jetons depuis le stockage"""
        try:
            tokens_file = os.path.join(self.tokens_dir, 'tokens.json')
            if os.path.exists(tokens_file):
                with open(tokens_file, 'r', encoding='utf-8') as f:
                    tokens_data = json.load(f)
                    
                    # Convertir les dates
                    for token_id, token_info in tokens_data.items():
                        if 'expiry' in token_info:
                            token_info['expiry'] = datetime.fromisoformat(token_info['expiry'])
                    
                    self.reset_tokens = tokens_data
                    logger.info(f"Chargement de {len(self.reset_tokens)} jetons")
            else:
                logger.info("Aucun jeton existant")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des jetons: {e}")
            self.reset_tokens = {}
    
    def _save_tokens(self) -> None:
        """Sauvegarde les jetons dans le stockage"""
        try:
            tokens_file = os.path.join(self.tokens_dir, 'tokens.json')
            
            # Convertir les dates pour JSON
            tokens_data = {}
            for token_id, token_info in self.reset_tokens.items():
                tokens_data[token_id] = token_info.copy()
                if 'expiry' in tokens_data[token_id]:
                    tokens_data[token_id]['expiry'] = token_info['expiry'].isoformat()
            
            with open(tokens_file, 'w', encoding='utf-8') as f:
                json.dump(tokens_data, f, indent=2)
            
            logger.info(f"Sauvegarde de {len(self.reset_tokens)} jetons")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des jetons: {e}")
    
    def _schedule_token_cleanup(self) -> None:
        """Planifie le nettoyage des jetons expirés"""
        self._cleanup_expired_tokens()
        self.frame.after(3600000, self._schedule_token_cleanup)  # 1 heure
    
    def _cleanup_expired_tokens(self) -> None:
        """Supprime les jetons expirés"""
        now = datetime.now()
        expired_tokens = []
        
        for token_id, token_info in self.reset_tokens.items():
            if 'expiry' in token_info and token_info['expiry'] < now:
                expired_tokens.append(token_id)
        
        if expired_tokens:
            for token_id in expired_tokens:
                del self.reset_tokens[token_id]
            
            self._save_tokens()
            logger.info(f"Suppression de {len(expired_tokens)} jetons expirés")
            
            if self.frame.winfo_ismapped():
                self.refresh_token_list()
    
    def create_widgets(self) -> None:
        """Crée les widgets de l'interface"""
        # En-tête
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.pack(fill=ctk.X, pady=(0, 10))
        
        ctk.CTkLabel(
            header,
            text="Gestion des réinitialisations de mot de passe",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side=ctk.LEFT, padx=20, pady=10)
        
        # Bouton d'actualisation
        ctk.CTkButton(
            header,
            text="Actualiser",
            width=100,
            command=self.refresh_token_list
        ).pack(side=ctk.RIGHT, padx=20, pady=10)
        
        # Conteneur principal
        main_container = ctk.CTkFrame(self.frame)
        main_container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Configuration des colonnes
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        
        # Liste des demandes
        self.list_frame = ctk.CTkFrame(main_container)
        self.list_frame.grid(row=0, column=0, padx=(5, 10), pady=5, sticky="nsew")
        
        # Formulaire de création
        self.creation_frame = ctk.CTkFrame(main_container)
        self.creation_frame.grid(row=0, column=1, padx=(10, 5), pady=5, sticky="nsew")
        
        # Créer les composants
        self.create_token_list()
        self.create_token_form()
    
    def create_token_list(self) -> None:
        """Crée la liste des jetons"""
        # ... (le reste du code de la liste des jetons reste identique)
        pass
    
    def create_token_form(self) -> None:
        """Crée le formulaire de création"""
        # ... (le reste du code du formulaire reste identique)
        pass
    
    def refresh_token_list(self) -> None:
        """Rafraîchit la liste des jetons"""
        # ... (le reste du code de rafraîchissement reste identique)
        pass
    
    def create_reset_token(self) -> None:
        """Crée un nouveau jeton"""
        # ... (le reste du code de création de jeton reste identique)
        pass
    
    def revoke_token(self, token_id: str) -> None:
        """Révoque un jeton"""
        # ... (le reste du code de révocation reste identique)
        pass
    
    def show_message(self, title: str, message: str, level: str = "info") -> None:
        """Affiche un message"""
        # ... (le reste du code d'affichage de message reste identique)
        pass 