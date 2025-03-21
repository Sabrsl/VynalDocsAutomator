#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire de réinitialisation de mot de passe pour l'interface d'administration
"""

import logging
import customtkinter as ctk
import tkinter as tk
from datetime import datetime, timedelta
import os
import uuid
import hashlib
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from typing import Dict, List, Any, Optional, Callable, Tuple

from ..models.password_reset_token import PasswordResetToken

logger = logging.getLogger("VynalDocsAutomator.Admin.PasswordResetManager")

class PasswordResetToken:
    """Gère les tokens de réinitialisation de mot de passe"""
    
    def __init__(self, email: str):
        self.token = str(uuid.uuid4())
        self.email = email
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(hours=1)
        self.used = False

    def is_valid(self) -> bool:
        """Vérifie si le token est toujours valide"""
        return not self.used and datetime.now() < self.expires_at

    def to_dict(self) -> dict:
        """Convertit le token en dictionnaire pour le stockage"""
        return {
            "token": self.token,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "used": self.used
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PasswordResetToken':
        """Crée un token à partir d'un dictionnaire"""
        token = cls(data["email"])
        token.token = data["token"]
        token.created_at = datetime.fromisoformat(data["created_at"])
        token.expires_at = datetime.fromisoformat(data["expires_at"])
        token.used = data["used"]
        return token

class PasswordResetManager:
    """
    Gestionnaire de réinitialisation de mot de passe sécurisée
    Permet aux administrateurs de générer des liens de réinitialisation temporaires
    et de suivre les demandes en cours
    """
    
    def __init__(self, parent: ctk.CTkFrame, app_model: Any) -> None:
        """
        Initialise le gestionnaire de réinitialisation de mot de passe
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        self.reset_tokens = {}  # Stocke les jetons de réinitialisation
        
        # Créer le répertoire de stockage des jetons
        self.tokens_dir = self._get_tokens_dir()
        os.makedirs(self.tokens_dir, exist_ok=True)
        
        # Charger les tokens existants
        self._load_tokens()
        
        # Cadre principal de la vue
        self.frame = ctk.CTkFrame(parent)
        
        # Création de l'interface
        self.create_widgets()
        
        # Planifier une vérification des tokens expirés
        self._schedule_token_cleanup()
        
        logger.info("PasswordResetManager initialisé")

    def show(self):
        """Affiche la vue du gestionnaire de réinitialisation"""
        self.frame.pack(fill=ctk.BOTH, expand=True)
        # Rafraîchir la liste des tokens lorsque la vue devient visible
        self.refresh_token_list()
        logger.info("Vue du gestionnaire de réinitialisation affichée")

    def hide(self):
        """Cache la vue du gestionnaire de réinitialisation"""
        self.frame.pack_forget()
        logger.info("Vue du gestionnaire de réinitialisation masquée")
    
    def _get_tokens_dir(self) -> str:
        """
        Retourne le répertoire de stockage des jetons de réinitialisation
        
        Returns:
            str: Chemin du répertoire
        """
        if hasattr(self.model, 'admin_dir'):
            return os.path.join(self.model.admin_dir, 'password_reset_tokens')
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'password_reset_tokens')
    
    def _load_tokens(self) -> None:
        """
        Charge les jetons de réinitialisation depuis le stockage
        """
        try:
            tokens_file = os.path.join(self.tokens_dir, 'tokens.json')
            if os.path.exists(tokens_file):
                with open(tokens_file, 'r', encoding='utf-8') as f:
                    tokens_data = json.load(f)
                    
                    # Convertir les données en objets PasswordResetToken
                    self.reset_tokens = {
                        token_id: PasswordResetToken.from_dict(token_data)
                        for token_id, token_data in tokens_data.items()
                    }
                    
                    logger.info(f"Chargement de {len(self.reset_tokens)} jetons de réinitialisation")
            else:
                logger.info("Aucun jeton de réinitialisation existant")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des jetons: {e}")
            self.reset_tokens = {}
    
    def _save_tokens(self) -> None:
        """
        Sauvegarde les jetons de réinitialisation dans le stockage
        """
        try:
            tokens_file = os.path.join(self.tokens_dir, 'tokens.json')
            
            # Convertir les objets PasswordResetToken en dictionnaires
            tokens_data = {
                token_id: token.to_dict()
                for token_id, token in self.reset_tokens.items()
            }
            
            with open(tokens_file, 'w', encoding='utf-8') as f:
                json.dump(tokens_data, f, indent=2)
            
            logger.info(f"Sauvegarde de {len(self.reset_tokens)} jetons de réinitialisation")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des jetons: {e}")
    
    def _schedule_token_cleanup(self) -> None:
        """
        Planifie une vérification régulière des jetons expirés
        """
        # Nettoyer maintenant, puis toutes les heures
        self._cleanup_expired_tokens()
        self.frame.after(3600000, self._schedule_token_cleanup)  # 3600000 ms = 1 heure
    
    def _cleanup_expired_tokens(self) -> None:
        """
        Supprime les jetons de réinitialisation expirés
        """
        now = datetime.now()
        expired_tokens = []
        
        for token_id, token in self.reset_tokens.items():
            if token.expires_at < now:
                expired_tokens.append(token_id)
        
        if expired_tokens:
            for token_id in expired_tokens:
                del self.reset_tokens[token_id]
            
            self._save_tokens()
            logger.info(f"Suppression de {len(expired_tokens)} jetons expirés")
            
            # Mettre à jour la liste si elle est visible
            if self.frame.winfo_ismapped():
                self.refresh_token_list()
    
    def create_widgets(self) -> None:
        """
        Crée les widgets de l'interface
        """
        # Cadre pour le titre
        self.header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.header_frame.pack(fill=ctk.X, pady=(0, 10))
        
        # Titre principal
        ctk.CTkLabel(
            self.header_frame,
            text="Gestion des réinitialisations de mot de passe",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side=ctk.LEFT, anchor="w", padx=20, pady=10)
        
        # Bouton d'actualisation
        refresh_btn = ctk.CTkButton(
            self.header_frame,
            text="Actualiser",
            width=100,
            command=self.refresh_token_list
        )
        refresh_btn.pack(side=ctk.RIGHT, padx=20, pady=10)
        
        # Conteneur principal avec deux sections
        self.main_container = ctk.CTkFrame(self.frame)
        self.main_container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Configurer deux colonnes
        self.main_container.columnconfigure(0, weight=1)  # Liste des demandes
        self.main_container.columnconfigure(1, weight=1)  # Création de demande
        
        # Cadre pour la liste des demandes en cours
        self.list_frame = ctk.CTkFrame(self.main_container)
        self.list_frame.grid(row=0, column=0, padx=(5, 10), pady=5, sticky="nsew")
        
        # Cadre pour la création de nouvelles demandes
        self.creation_frame = ctk.CTkFrame(self.main_container)
        self.creation_frame.grid(row=0, column=1, padx=(10, 5), pady=5, sticky="nsew")
        
        # Créer la liste des demandes
        self.create_token_list()
        
        # Créer le formulaire de création
        self.create_token_form()
    
    def create_token_list(self) -> None:
        """
        Crée la liste des jetons de réinitialisation en cours
        """
        # Titre
        ctk.CTkLabel(
            self.list_frame,
            text="Demandes de réinitialisation en cours",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=10)
        
        # Cadre pour la liste avec défilement
        self.tokens_container = ctk.CTkScrollableFrame(self.list_frame)
        self.tokens_container.pack(fill=ctk.BOTH, expand=True, padx=15, pady=10)
        
        # En-tête de la liste
        header_frame = ctk.CTkFrame(self.tokens_container, fg_color="#2c3e50", height=30)
        header_frame.pack(fill=ctk.X, pady=(0, 5))
        
        # Colonnes d'en-tête
        columns = ["Utilisateur", "Date d'expiration", "État", "Actions"]
        column_widths = [0.3, 0.3, 0.15, 0.25]  # Poids relatifs
        
        for i, (col, width) in enumerate(zip(columns, column_widths)):
            header_frame.columnconfigure(i, weight=int(width * 100))
            
            ctk.CTkLabel(
                header_frame,
                text=col,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#ffffff"
            ).grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        # Message initial
        self.no_tokens_label = ctk.CTkLabel(
            self.tokens_container,
            text="Aucune demande de réinitialisation en cours",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.no_tokens_label.pack(pady=20)
        
        # Charger les jetons existants
        self.refresh_token_list()
    
    def clear_form(self):
        """Réinitialise le formulaire de création de token."""
        # Effacer les champs du formulaire
        self.user_entry.delete(0, 'end')
        self.expiry_var.set("24 heures")  # Remettre la durée par défaut
        self.reset_mode.set("Lien unique")  # Remettre le mode par défaut
        
        # Réinitialiser les labels d'erreur
        if hasattr(self, 'error_label'):
            self.error_label.configure(text="")
        
        # Réinitialiser le focus sur le champ email
        self.user_entry.focus()
        
        logger.debug("Formulaire de création de token réinitialisé")

    def create_token_form(self) -> None:
        """
        Crée le formulaire de création de nouvelles demandes
        """
        # Titre
        ctk.CTkLabel(
            self.creation_frame,
            text="Créer une nouvelle demande de réinitialisation",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=10)
        
        # Formulaire
        form_frame = ctk.CTkFrame(self.creation_frame, fg_color="transparent")
        form_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=10)
        
        # Espacement entre les champs
        form_padding = 10
        
        # Champ utilisateur
        user_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        user_frame.pack(fill=ctk.X, pady=form_padding)
        
        ctk.CTkLabel(
            user_frame,
            text="Utilisateur:",
            font=ctk.CTkFont(size=12),
            anchor="w",
            width=100
        ).pack(side=ctk.LEFT)
        
        self.user_var = ctk.StringVar()
        self.user_entry = ctk.CTkEntry(
            user_frame,
            textvariable=self.user_var,
            placeholder_text="Adresse e-mail de l'utilisateur",
            width=200
        )
        self.user_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
        
        # Mode de réinitialisation (lien ou mot de passe temporaire)
        mode_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        mode_frame.pack(fill=ctk.X, pady=form_padding)
        
        ctk.CTkLabel(
            mode_frame,
            text="Mode:",
            font=ctk.CTkFont(size=12),
            anchor="w",
            width=100
        ).pack(side=ctk.LEFT)
        
        self.reset_mode = ctk.StringVar(value="Lien unique")
        
        modes_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        modes_frame.pack(side=ctk.LEFT, fill=ctk.X)
        
        ctk.CTkRadioButton(
            modes_frame,
            text="Lien unique",
            variable=self.reset_mode,
            value="Lien unique"
        ).pack(side=ctk.LEFT, padx=(0, 10))
        
        ctk.CTkRadioButton(
            modes_frame,
            text="Mot de passe temporaire",
            variable=self.reset_mode,
            value="Mot de passe temporaire"
        ).pack(side=ctk.LEFT)
        
        # Durée de validité
        expiry_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        expiry_frame.pack(fill=ctk.X, pady=form_padding)
        
        ctk.CTkLabel(
            expiry_frame,
            text="Validité:",
            font=ctk.CTkFont(size=12),
            anchor="w",
            width=100
        ).pack(side=ctk.LEFT)
        
        self.expiry_var = ctk.StringVar(value="24 heures")
        
        expiry_options = ["1 heure", "6 heures", "12 heures", "24 heures", "48 heures", "7 jours"]
        expiry_dropdown = ctk.CTkOptionMenu(
            expiry_frame,
            values=expiry_options,
            variable=self.expiry_var
        )
        expiry_dropdown.pack(side=ctk.LEFT)
        
        # Message personnalisé
        message_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        message_frame.pack(fill=ctk.BOTH, expand=True, pady=form_padding)
        
        ctk.CTkLabel(
            message_frame,
            text="Message:",
            font=ctk.CTkFont(size=12),
            anchor="w"
        ).pack(anchor="w")
        
        self.message_text = ctk.CTkTextbox(
            message_frame,
            height=100
        )
        self.message_text.pack(fill=ctk.BOTH, expand=True, pady=5)
        
        # Texte par défaut
        default_message = (
            "Bonjour,\n\n"
            "Vous recevez ce message suite à une demande de réinitialisation de mot de passe.\n\n"
            "Si vous n'êtes pas à l'origine de cette demande, veuillez ignorer ce message.\n\n"
            "Cordialement,\n"
            "L'équipe support"
        )
        self.message_text.insert("1.0", default_message)
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, pady=form_padding)
        
        ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            fg_color="transparent",
            hover_color="#34495e",
            command=self.clear_form
        ).pack(side=ctk.LEFT, padx=(0, 10))
        
        ctk.CTkButton(
            buttons_frame,
            text="Créer la demande",
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=self.create_reset_token
        ).pack(side=ctk.LEFT)
    
    def refresh_token_list(self) -> None:
        """
        Rafraîchit la liste des jetons de réinitialisation
        """
        # Nettoyer les tokens expirés
        self._cleanup_expired_tokens()
        
        # Supprimer les éléments actuels
        for widget in self.tokens_container.winfo_children():
            if widget != self.no_tokens_label:
                widget.destroy()
        
        if not self.reset_tokens:
            self.no_tokens_label.pack(pady=20)
            return
        
        # Cacher le message "aucun jeton"
        self.no_tokens_label.pack_forget()
        
        # Recréer l'en-tête
        header_frame = ctk.CTkFrame(self.tokens_container, fg_color="#2c3e50", height=30)
        header_frame.pack(fill=ctk.X, pady=(0, 5))
        
        # Colonnes d'en-tête
        columns = ["Utilisateur", "Date d'expiration", "État", "Actions"]
        column_widths = [0.3, 0.3, 0.15, 0.25]  # Poids relatifs
        
        for i, (col, width) in enumerate(zip(columns, column_widths)):
            header_frame.columnconfigure(i, weight=int(width * 100))
            
            ctk.CTkLabel(
                header_frame,
                text=col,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#ffffff"
            ).grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        # Ajouter les jetons triés par date d'expiration (plus récents en premier)
        sorted_tokens = sorted(
            self.reset_tokens.items(),
            key=lambda x: x[1].expires_at,
            reverse=True
        )
        
        for i, (token_id, token) in enumerate(sorted_tokens):
            token_frame = ctk.CTkFrame(self.tokens_container)
            token_frame.pack(fill=ctk.X, pady=2)
            
            # Configurer les colonnes avec les mêmes poids
            for j, width in enumerate(column_widths):
                token_frame.columnconfigure(j, weight=int(width * 100))
            
            # Email utilisateur
            ctk.CTkLabel(
                token_frame,
                text=token.email,
                font=ctk.CTkFont(size=12),
                anchor="w"
            ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            
            # Date d'expiration
            expiry_text = token.expires_at.strftime("%d/%m/%Y %H:%M")
            
            ctk.CTkLabel(
                token_frame,
                text=expiry_text,
                font=ctk.CTkFont(size=12),
                anchor="w"
            ).grid(row=0, column=1, padx=5, pady=5, sticky="w")
            
            # État
            if token.is_valid():
                status = "Actif"
                status_color = "#2ecc71"  # Vert
            else:
                status = "Expiré"
                status_color = "#e74c3c"  # Rouge
            
            ctk.CTkLabel(
                token_frame,
                text=status,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=status_color,
                anchor="w"
            ).grid(row=0, column=2, padx=5, pady=5, sticky="w")
            
            # Boutons d'action
            actions_frame = ctk.CTkFrame(token_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=3, padx=5, pady=5, sticky="e")
            
            ctk.CTkButton(
                actions_frame,
                text="Copier",
                width=70,
                height=25,
                font=ctk.CTkFont(size=11),
                command=lambda t=token_id: self.copy_token_to_clipboard(t)
            ).pack(side=ctk.LEFT, padx=(0, 5))
            
            ctk.CTkButton(
                actions_frame,
                text="Révoquer",
                width=70,
                height=25,
                font=ctk.CTkFont(size=11),
                fg_color="#e74c3c",
                hover_color="#c0392b",
                command=lambda t=token_id: self.revoke_token(t)
            ).pack(side=ctk.LEFT)
    
    def create_reset_token(self) -> None:
        """
        Crée un nouveau jeton de réinitialisation
        """
        try:
            # Récupérer les données du formulaire
            user_email = self.user_var.get().strip()
            reset_mode = self.reset_mode.get()
            expiry_str = self.expiry_var.get()
            message = self.message_text.get("1.0", "end-1c")
            
            # Valider l'email
            if not user_email or "@" not in user_email:
                self.show_message("Erreur", "Veuillez saisir une adresse e-mail valide", "error")
                return
            
            # Créer le token
            token = PasswordResetToken(user_email)
            
            # Calculer et définir l'expiration
            expiry = self.calculate_expiry_date(expiry_str)
            token.expires_at = expiry
            
            # Générer un ID unique pour le token
            token_id = str(uuid.uuid4())
            
            # Stocker le token
            self.reset_tokens[token_id] = token
            
            # Générer le lien ou mot de passe selon le mode
            if reset_mode == "Lien unique":
                reset_link = f"https://votre-application.com/reset-password?token={token.token}"
                self.show_reset_info(user_email, reset_link, token.expires_at, "lien")
            else:  # Mot de passe temporaire
                temp_password = self.generate_temp_password()
                token.temp_password = temp_password
                self._save_tokens()
                self.show_reset_info(user_email, temp_password, token.expires_at, "password")
            
            # Rafraîchir la liste
            self.refresh_token_list()
            
            # Nettoyer le formulaire
            self.clear_form()
            
            logger.info(f"Jeton de réinitialisation créé pour {user_email}")
        except Exception as e:
            logger.error(f"Erreur lors de la création du jeton: {e}")
            self.show_message("Erreur", f"Impossible de créer le jeton: {e}", "error")
    
    def revoke_token(self, token_id: str) -> None:
        """
        Révoque un jeton de réinitialisation
        
        Args:
            token_id: Identifiant du jeton à révoquer
        """
        try:
            if token_id in self.reset_tokens:
                # Demander confirmation
                self.confirm_revoke_token(token_id)
            else:
                logger.warning(f"Tentative de révocation d'un jeton inexistant: {token_id}")
        except Exception as e:
            logger.error(f"Erreur lors de la révocation du jeton: {e}")
            self.show_message("Erreur", f"Impossible de révoquer le jeton: {e}", "error")
    
    def confirm_revoke_token(self, token_id: str) -> None:
        """
        Affiche une boîte de dialogue de confirmation pour révoquer un jeton
        
        Args:
            token_id: Identifiant du jeton à révoquer
        """
        token = self.reset_tokens.get(token_id)
        if not token:
            logger.warning(f"Tentative de révocation d'un jeton inexistant: {token_id}")
            return
        
        user_email = token.email
        
        dialog = ctk.CTkToplevel(self.frame)
        dialog.title("Confirmation")
        dialog.geometry("400x200")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        dialog.transient(self.frame)
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Message
        message_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        message_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            message_frame,
            text="⚠️",
            font=ctk.CTkFont(size=48)
        ).pack(pady=10)
        
        ctk.CTkLabel(
            message_frame,
            text=f"Êtes-vous sûr de vouloir révoquer le jeton pour {user_email} ?\n"
                 f"L'utilisateur ne pourra plus réinitialiser son mot de passe avec ce jeton.",
            font=ctk.CTkFont(size=12),
            wraplength=300,
            text_color="#f39c12"
        ).pack(pady=10)
        
        # Boutons
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, padx=20, pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            fg_color="transparent",
            hover_color="#34495e",
            command=dialog.destroy
        ).pack(side=ctk.LEFT, expand=True, padx=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="Révoquer",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=lambda: [dialog.destroy(), self._do_revoke_token(token_id)]
        ).pack(side=ctk.RIGHT, expand=True, padx=5)
        
        # Gestion des touches de clavier
        dialog.bind("<Return>", lambda e: dialog.destroy())
        dialog.bind("<Escape>", lambda e: dialog.destroy())
    
    def _do_revoke_token(self, token_id: str) -> None:
        """
        Exécute la révocation effective du jeton
        
        Args:
            token_id: Identifiant du jeton à révoquer
        """
        try:
            if token_id in self.reset_tokens:
                token = self.reset_tokens[token_id]
                user_email = token.email
                del self.reset_tokens[token_id]
                self._save_tokens()
                self.refresh_token_list()
                self.show_message(
                    "Révocation réussie",
                    f"Le jeton pour {user_email} a été révoqué",
                    "success"
                )
                logger.info(f"Jeton révoqué pour {user_email}")
        except Exception as e:
            logger.error(f"Erreur lors de la révocation du jeton: {e}")
            self.show_message("Erreur", f"Impossible de révoquer le jeton: {e}", "error")
    
    def copy_token_to_clipboard(self, token_id: str) -> None:
        """
        Copie les informations du jeton dans le presse-papiers
        
        Args:
            token_id: Identifiant du jeton
        """
        try:
            token = self.reset_tokens.get(token_id)
            if not token:
                logger.warning(f"Tentative de copie d'un jeton inexistant: {token_id}")
                return
            
            # Générer les informations
            user_email = token.email
            reset_mode = "Lien unique" if token.token else "Mot de passe temporaire"
            
            if reset_mode == "Lien unique":
                reset_link = f"https://votre-application.com/reset-password?token={token.token}"
                info_to_copy = reset_link
            else:  # Mot de passe temporaire
                temp_password = token.temp_password
                info_to_copy = f"Mot de passe temporaire pour {user_email}: {temp_password}"
            
            # Copier dans le presse-papiers
            self.frame.clipboard_clear()
            self.frame.clipboard_append(info_to_copy)
            
            self.show_message(
                "Copie réussie",
                f"Les informations ont été copiées dans le presse-papiers",
                "success"
            )
            
            logger.info(f"Copie de {info_to_copy} réussie")
        except Exception as e:
            logger.error(f"Erreur lors de la copie des informations: {e}")
            self.show_message("Erreur", f"Impossible de copier les informations: {e}", "error")

    def calculate_expiry_date(self, expiry_str: str) -> datetime:
        """
        Calcule la date d'expiration à partir de la chaîne
        
        Args:
            expiry_str: Chaîne de durée (ex: "24 heures")
            
        Returns:
            datetime: Date d'expiration
        """
        now = datetime.now()
        
        if "heure" in expiry_str:
            hours = int(expiry_str.split()[0])
            return now + timedelta(hours=hours)
        elif "jour" in expiry_str:
            days = int(expiry_str.split()[0])
            return now + timedelta(days=days)
        else:
            # Par défaut: 24 heures
            return now + timedelta(hours=24)
    
    def generate_temp_password(self, length: int = 12) -> str:
        """
        Génère un mot de passe temporaire
        
        Args:
            length: Longueur du mot de passe (défaut: 12 caractères)
            
        Returns:
            str: Mot de passe généré
        """
        # Caractères pour le mot de passe
        chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        
        # Générer un mot de passe qui contient au moins un caractère de chaque type
        while True:
            password = ''.join(secrets.choice(chars) for _ in range(length))
            
            # Vérifier que le mot de passe contient au moins une lettre minuscule,
            # une lettre majuscule, un chiffre et un caractère spécial
            if (any(c.islower() for c in password)
                    and any(c.isupper() for c in password)
                    and any(c.isdigit() for c in password)
                    and any(c in "!@#$%^&*()-_=+" for c in password)):
                return password
    
    def show_reset_info(self, user_email: str, reset_info: str, expiry: datetime, info_type: str) -> None:
        """
        Affiche les informations de réinitialisation
        
        Args:
            user_email: Email de l'utilisateur
            reset_info: Lien ou mot de passe temporaire
            expiry: Date d'expiration
            info_type: Type d'information ('lien' ou 'password')
        """
        dialog = ctk.CTkToplevel(self.frame)
        dialog.title("Réinitialisation créée")
        dialog.geometry("500x350")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        dialog.transient(self.frame)
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Contenu
        content_frame = ctk.CTkFrame(dialog)
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre
        ctk.CTkLabel(
            content_frame,
            text="✅ Réinitialisation créée avec succès",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#2ecc71"
        ).pack(pady=10)
        
        # Informations utilisateur
        user_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        user_frame.pack(fill=ctk.X, pady=5)
        
        ctk.CTkLabel(
            user_frame,
            text="Utilisateur:",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=100,
            anchor="w"
        ).pack(side=ctk.LEFT)
        
        ctk.CTkLabel(
            user_frame,
            text=user_email,
            font=ctk.CTkFont(size=12)
        ).pack(side=ctk.LEFT)
        
        # Expiration
        expiry_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        expiry_frame.pack(fill=ctk.X, pady=5)
        
        ctk.CTkLabel(
            expiry_frame,
            text="Expiration:",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=100,
            anchor="w"
        ).pack(side=ctk.LEFT)
        
        ctk.CTkLabel(
            expiry_frame,
            text=expiry.strftime("%d/%m/%Y %H:%M"),
            font=ctk.CTkFont(size=12)
        ).pack(side=ctk.LEFT)
        
        # Information de réinitialisation
        info_label = "Lien de réinitialisation:" if info_type == "lien" else "Mot de passe temporaire:"
        
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(fill=ctk.X, pady=5)
        
        ctk.CTkLabel(
            info_frame,
            text=info_label,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        ).pack(anchor="w")
        
        # Zone de texte avec les informations
        info_text = ctk.CTkTextbox(
            content_frame,
            height=80,
            font=ctk.CTkFont(family="Courier", size=12),
            wrap="word"
        )
        info_text.pack(fill=ctk.X, pady=5)
        info_text.insert("1.0", reset_info)
        info_text.configure(state="disabled")
        
        # Instructions
        instructions = ""
        if info_type == "lien":
            instructions = (
                "1. Envoyez ce lien à l'utilisateur via un canal sécurisé\n"
                "2. Le lien expirera automatiquement à la date indiquée\n"
                "3. L'utilisateur devra définir un nouveau mot de passe après avoir cliqué sur le lien"
            )
        else:  # password
            instructions = (
                "1. Communiquez ce mot de passe à l'utilisateur via un canal sécurisé\n"
                "2. Le mot de passe expirera automatiquement à la date indiquée\n"
                "3. L'utilisateur devra changer ce mot de passe temporaire après sa première connexion"
            )
        
        ctk.CTkLabel(
            content_frame,
            text="Instructions:",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        ).pack(anchor="w", pady=(10, 0))
        
        ctk.CTkLabel(
            content_frame,
            text=instructions,
            font=ctk.CTkFont(size=12),
            justify="left",
            anchor="w"
        ).pack(fill=ctk.X)
        
        # Boutons
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, padx=20, pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="Copier dans le presse-papiers",
            command=lambda: [dialog.clipboard_clear(), dialog.clipboard_append(reset_info),
                             self.show_message("Copie réussie", "Information copiée dans le presse-papiers", "success")]
        ).pack(side=ctk.LEFT, expand=True, padx=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="Envoyer par e-mail",
            command=lambda: self.send_reset_email(user_email, reset_info, expiry, info_type)
        ).pack(side=ctk.LEFT, expand=True, padx=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="Fermer",
            command=dialog.destroy
        ).pack(side=ctk.LEFT, expand=True, padx=5)
        
        # Gestion des touches de clavier
        dialog.bind("<Return>", lambda e: dialog.destroy())
        dialog.bind("<Escape>", lambda e: dialog.destroy())
    
    def send_reset_email(self, user_email: str, reset_info: str, expiry: datetime, info_type: str) -> None:
        """
        Envoie un email avec les informations de réinitialisation
        
        Args:
            user_email: Email de l'utilisateur
            reset_info: Lien ou mot de passe temporaire
            expiry: Date d'expiration
            info_type: Type d'information ('lien' ou 'password')
        """
        try:
            # Configuration de l'envoi d'email (à adapter selon votre configuration)
            smtp_host = "smtp.votre-serveur.com"
            smtp_port = 587
            smtp_user = "votre-email@votre-serveur.com"
            smtp_password = "votre-mot-de-passe"
            
            # Demander confirmation avant l'envoi
            self.confirm_send_email(user_email, reset_info, expiry, info_type, 
                                    smtp_host, smtp_port, smtp_user, smtp_password)
        except Exception as e:
            logger.error(f"Erreur lors de la préparation de l'email: {e}")
            self.show_message("Erreur", f"Impossible de préparer l'email: {e}", "error")
    
    def confirm_send_email(self, user_email: str, reset_info: str, expiry: datetime, 
                           info_type: str, smtp_host: str, smtp_port: int, 
                           smtp_user: str, smtp_password: str) -> None:
        """
        Demande confirmation avant d'envoyer l'email
        """
        dialog = ctk.CTkToplevel(self.frame)
        dialog.title("Confirmation d'envoi")
        dialog.geometry("400x300")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        dialog.transient(self.frame)
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Message
        message_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        message_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            message_frame,
            text="📧",
            font=ctk.CTkFont(size=48)
        ).pack(pady=10)
        
        ctk.CTkLabel(
            message_frame,
            text=f"Voulez-vous envoyer un email à {user_email} contenant les informations de réinitialisation ?",
            font=ctk.CTkFont(size=12),
            wraplength=300
        ).pack(pady=10)
        
        # Configuration SMTP
        smtp_frame = ctk.CTkFrame(message_frame)
        smtp_frame.pack(fill=ctk.X, pady=10)
        
        # Variables pour les champs
        self.smtp_host_var = ctk.StringVar(value=smtp_host)
        self.smtp_port_var = ctk.StringVar(value=str(smtp_port))
        self.smtp_user_var = ctk.StringVar(value=smtp_user)
        self.smtp_password_var = ctk.StringVar(value=smtp_password)
        
        # Champs de configuration
        smtp_grid = ctk.CTkFrame(smtp_frame, fg_color="transparent")
        smtp_grid.pack(fill=ctk.X, padx=10, pady=5)
        
        # Serveur SMTP
        ctk.CTkLabel(
            smtp_grid,
            text="Serveur SMTP:",
            font=ctk.CTkFont(size=11),
            anchor="w",
            width=80
        ).grid(row=0, column=0, sticky="w", pady=2)
        
        ctk.CTkEntry(
            smtp_grid,
            textvariable=self.smtp_host_var,
            width=150,
            height=25,
            font=ctk.CTkFont(size=11)
        ).grid(row=0, column=1, sticky="ew", pady=2)
        
        # Port SMTP
        ctk.CTkLabel(
            smtp_grid,
            text="Port:",
            font=ctk.CTkFont(size=11),
            anchor="w",
            width=80
        ).grid(row=1, column=0, sticky="w", pady=2)
        
        ctk.CTkEntry(
            smtp_grid,
            textvariable=self.smtp_port_var,
            width=150,
            height=25,
            font=ctk.CTkFont(size=11)
        ).grid(row=1, column=1, sticky="ew", pady=2)
        
        # Utilisateur SMTP
        ctk.CTkLabel(
            smtp_grid,
            text="Utilisateur:",
            font=ctk.CTkFont(size=11),
            anchor="w",
            width=80
        ).grid(row=2, column=0, sticky="w", pady=2)
        
        ctk.CTkEntry(
            smtp_grid,
            textvariable=self.smtp_user_var,
            width=150,
            height=25,
            font=ctk.CTkFont(size=11)
        ).grid(row=2, column=1, sticky="ew", pady=2)
        
        # Mot de passe SMTP
        ctk.CTkLabel(
            smtp_grid,
            text="Mot de passe:",
            font=ctk.CTkFont(size=11),
            anchor="w",
            width=80
        ).grid(row=3, column=0, sticky="w", pady=2)
        
        ctk.CTkEntry(
            smtp_grid,
            textvariable=self.smtp_password_var,
            width=150,
            height=25,
            font=ctk.CTkFont(size=11),
            show="*"
        ).grid(row=3, column=1, sticky="ew", pady=2)
        
        # Configurer la grille
        smtp_grid.columnconfigure(1, weight=1)
        
        # Boutons
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, padx=20, pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            fg_color="transparent",
            hover_color="#34495e",
            command=dialog.destroy
        ).pack(side=ctk.LEFT, expand=True, padx=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="Envoyer",
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=lambda: [
                dialog.destroy(),
                self._do_send_email(
                    user_email, reset_info, expiry, info_type,
                    self.smtp_host_var.get(), int(self.smtp_port_var.get()),
                    self.smtp_user_var.get(), self.smtp_password_var.get()
                )
            ]
        ).pack(side=ctk.RIGHT, expand=True, padx=5)
        
        # Gestion des touches de clavier
        dialog.bind("<Return>", lambda e: dialog.destroy())
        dialog.bind("<Escape>", lambda e: dialog.destroy())
    
    def _do_send_email(self, user_email: str, reset_info: str, expiry: datetime, 
                     info_type: str, smtp_host: str, smtp_port: int, 
                     smtp_user: str, smtp_password: str) -> None:
        """
        Envoie effectivement l'email
        """
        try:
            # Créer le message
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = user_email
            
            if info_type == "lien":
                msg['Subject'] = "Réinitialisation de votre mot de passe"
                body = f"""
                Bonjour,
                
                Vous avez demandé une réinitialisation de votre mot de passe.
                
                Veuillez cliquer sur le lien suivant pour réinitialiser votre mot de passe:
                {reset_info}
                
                Ce lien expirera le {expiry.strftime("%d/%m/%Y")} à {expiry.strftime("%H:%M")}.
                
                Si vous n'êtes pas à l'origine de cette demande, veuillez ignorer ce message.
                
                Cordialement,
                L'équipe support
                """
            else:  # password
                msg['Subject'] = "Votre mot de passe temporaire"
                body = f"""
                Bonjour,
                
                Un mot de passe temporaire a été généré pour votre compte.
                
                Votre mot de passe temporaire: {reset_info}
                
                Ce mot de passe expirera le {expiry.strftime("%d/%m/%Y")} à {expiry.strftime("%H:%M")}.
                Vous devrez le changer lors de votre prochaine connexion.
                
                Si vous n'êtes pas à l'origine de cette demande, veuillez contacter le support immédiatement.
                
                Cordialement,
                L'équipe support
                """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Essayer d'envoyer l'email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            self.show_message(
                "Envoi réussi",
                f"L'email de réinitialisation a été envoyé à {user_email}",
                "success"
            )
            
            logger.info(f"Email de réinitialisation envoyé à {user_email}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {e}")
            self.show_message("Erreur", f"Impossible d'envoyer l'email: {e}", "error")
    
    def show_message(self, title: str, message: str, level: str = "info") -> None:
        """
        Affiche une boîte de dialogue avec un message
        
        Args:
            title: Titre de la boîte de dialogue
            message: Message à afficher
            level: Niveau du message (info, warning, error, success)
        """
        dialog = ctk.CTkToplevel(self.frame)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        dialog.transient(self.frame)
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Icône en fonction du niveau
        if level == "error":
            icon = "❌"
            color = "#e74c3c"
        elif level == "warning":
            icon = "⚠️"
            color = "#f39c12"
        elif level == "success":
            icon = "✅"
            color = "#2ecc71"
        else:
            icon = "ℹ️"
            color = "#3498db"
        
        # Message
        message_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        message_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            message_frame,
            text=icon,
            font=ctk.CTkFont(size=48)
        ).pack(pady=10)
        
        ctk.CTkLabel(
            message_frame,
            text=message,
            font=ctk.CTkFont(size=12),
            wraplength=300,
            text_color=color
        ).pack(pady=10)
        
        # Bouton OK
        ctk.CTkButton(
            dialog,
            text="OK",
            command=dialog.destroy
        ).pack(pady=10)
        
        # Gestion des touches de clavier
        dialog.bind("<Return>", lambda e: dialog.destroy())
        dialog.bind("<Escape>", lambda e: dialog.destroy())