#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue de connexion pour l'application Vynal Docs Automator
"""

import os
import logging
import tkinter as tk
import customtkinter as ctk
from typing import Optional, Callable
import hashlib
import json
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
from utils.email_config import EmailConfig
from datetime import datetime, timedelta

logger = logging.getLogger("VynalDocsAutomator.LoginView")

# Création d'une classe simple de gestion des tentatives de connexion
class LoginAttemptManager:
    """Gère les tentatives de connexion et les verrouillages"""
    
    def __init__(self):
        self.last_attempt_time = None
        self.lockout_end_time = None
        self.attempt_count = 0
    
    def record_attempt(self, success: bool):
        """Enregistre une tentative de connexion"""
        self.last_attempt_time = datetime.now()
        
        if not success:
            self.attempt_count += 1
            if self.attempt_count >= 3:
                lockout_minutes = min(15, 1 * (2 ** (self.attempt_count - 3)))
                self.lockout_end_time = self.last_attempt_time + timedelta(minutes=lockout_minutes)
        else:
            # Réinitialiser en cas de succès
            self.attempt_count = 0
            self.lockout_end_time = None
    
    def can_attempt(self):
        """Vérifie si une tentative est autorisée"""
        if not self.lockout_end_time:
            return True, None
        
        now = datetime.now()
        if now >= self.lockout_end_time:
            # Réinitialiser partiellement après expiration du verrouillage
            self.lockout_end_time = None
            return True, None
        
        # Retourner le temps restant
        return False, self.lockout_end_time - now

class LoginView:
    """Vue de connexion avec protection par mot de passe"""
    
    def __init__(self, parent: tk.Widget, on_success: Callable[[], None], app_key=None):
        """
        Initialise la vue de connexion
        
        Args:
            parent: Widget parent
            on_success: Callback appelé après une connexion réussie
            app_key: Clé de l'application pour le chiffrement
        """
        self.parent = parent
        self.on_success = on_success
        self.window = None
        self.password_hash = None
        self.attempt_manager = LoginAttemptManager()
        
        # Timer pour le compte à rebours
        self._countdown_timer = None
        self._password_attempts = 0
        self._max_attempts = 3
        self.email_config = EmailConfig(app_key)
        
        # Configuration email
        self.smtp_config = {
            "server": "smtp.gmail.com",
            "port": 587,
            "username": "",  # À configurer
            "password": "",  # À configurer
            "from_email": ""  # À configurer
        }
        
        # Charger la configuration SMTP depuis le fichier config.json
        self._load_smtp_config()
    
    def _load_smtp_config(self):
        """Charge la configuration SMTP depuis le fichier config.json"""
        try:
            config_file = os.path.join("data", "config.json")
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if "smtp" in config:
                self.smtp_config.update(config["smtp"])
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration SMTP: {e}")
    
    def _generate_temp_password(self, length=12):
        """Génère un mot de passe temporaire aléatoire"""
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _send_temp_password(self, email, temp_password):
        """Envoie le mot de passe temporaire par email"""
        try:
            # Vérifier que l'email est configuré
            if not self.email_config.is_configured():
                logger.error("La configuration email n'est pas disponible")
                return False

            # Récupérer la configuration SMTP
            config = self.email_config.get_config()
            smtp = config.get('smtp', {})

            # Créer le message
            msg = MIMEMultipart()
            msg['From'] = smtp['from_email']
            msg['To'] = email
            msg['Subject'] = "Réinitialisation de votre mot de passe - Vynal Docs Automator"
            
            body = f"""
            Bonjour,
            
            Vous avez demandé la réinitialisation de votre mot de passe pour l'application Vynal Docs Automator.
            
            Voici votre mot de passe temporaire : {temp_password}
            
            Pour des raisons de sécurité, vous devrez changer ce mot de passe à votre prochaine connexion.
            
            Si vous n'êtes pas à l'origine de cette demande, veuillez ignorer cet email.
            
            Cordialement,
            L'équipe Vynal Docs
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Envoyer l'email
            with smtplib.SMTP(smtp['server'], smtp['port']) as server:
                if smtp.get('use_tls', True):
                    server.starttls()
                server.login(smtp['username'], smtp['password'])
                server.send_message(msg)
            
            logger.info(f"Mot de passe temporaire envoyé à {email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {e}")
            return False

    def show(self, password_hash: str):
        """
        Affiche la fenêtre de connexion
        
        Args:
            password_hash: Hash du mot de passe à vérifier
        """
        if self.window is not None:
            return
        
        self.password_hash = password_hash
        
        # Définir les couleurs et styles
        primary_color = "#3498db"       # Bleu principal
        success_color = "#2ecc71"       # Vert pour succès
        error_color = "#e74c3c"         # Rouge pour erreurs
        hover_color = "#2980b9"         # Bleu plus foncé pour hover
        
        # Créer la fenêtre de connexion
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("Connexion")
        self.window.geometry("450x420")
        self.window.resizable(False, False)
        
        # Empêcher l'interaction avec la fenêtre principale
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Centrer parfaitement la fenêtre sur l'écran
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Conteneur principal avec padding
        main_container = ctk.CTkFrame(self.window, fg_color="transparent")
        main_container.pack(fill=ctk.BOTH, expand=True, padx=30, pady=30)
        
        # Frame central avec ombre et coins arrondis
        frame = ctk.CTkFrame(
            main_container,
            corner_radius=15,
            border_width=1,
            border_color=("gray85", "gray25"),
            fg_color=("gray98", "gray10")
        )
        frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Logo/Icône (si disponible)
        # Utilisez une image de verrouillage par défaut
        logo_label = ctk.CTkLabel(
            frame,
            text="🔒",
            font=ctk.CTkFont(size=48)
        )
        logo_label.pack(pady=(30, 10))
        
        # Titre
        title_label = ctk.CTkLabel(
            frame,
            text="Connexion sécurisée",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 5))
        
        # Message
        message_label = ctk.CTkLabel(
            frame,
            text="Entrez votre mot de passe pour accéder à Vynal Docs",
            wraplength=320,
            font=ctk.CTkFont(size=14)
        )
        message_label.pack(pady=(0, 30))
        
        # Champ de mot de passe avec icône
        password_frame = ctk.CTkFrame(frame, fg_color="transparent")
        password_frame.pack(pady=(0, 20), fill=ctk.X, padx=50)
        
        self.password_var = ctk.StringVar()
        self.password_entry = ctk.CTkEntry(
            password_frame,
            placeholder_text="Mot de passe",
            show="•",
            height=40,
            textvariable=self.password_var,
            border_width=1,
            corner_radius=8,
            font=ctk.CTkFont(size=14)
        )
        self.password_entry.pack(fill=ctk.X)
        
        # Bouton de connexion
        self.login_button = ctk.CTkButton(
            frame,
            text="Se connecter",
            width=250,
            height=45,
            corner_radius=8,
            fg_color=primary_color,
            hover_color=hover_color,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._verify_password
        )
        self.login_button.pack(pady=(5, 15))
        
        # Message d'erreur (initialement caché)
        self.error_label = ctk.CTkLabel(
            frame,
            text="",
            text_color=error_color,
            wraplength=320,
            font=ctk.CTkFont(size=13)
        )
        self.error_label.pack(pady=(0, 10))
        
        # Lien "Mot de passe oublié"
        forgot_password_label = ctk.CTkLabel(
            frame,
            text="Mot de passe oublié ?",
            text_color=primary_color,
            cursor="hand2",
            font=ctk.CTkFont(size=13, underline=True)
        )
        forgot_password_label.pack(pady=(5, 20))
        forgot_password_label.bind("<Button-1>", lambda e: self._show_reset_dialog())
        forgot_password_label.bind("<Enter>", lambda e: forgot_password_label.configure(text_color=hover_color))
        forgot_password_label.bind("<Leave>", lambda e: forgot_password_label.configure(text_color=primary_color))
        
        # Lier la touche Entrée à la vérification du mot de passe
        self.window.bind('<Return>', lambda e: self._verify_password())
        
        # Focus sur le champ de mot de passe
        self.password_entry.focus()
        
        # Empêcher la fermeture de la fenêtre
        self.window.protocol("WM_DELETE_WINDOW", self._handle_close)
        
        # Vérifier l'état du blocage au démarrage
        can_attempt, lockout_time = self.attempt_manager.can_attempt()
        if not can_attempt and lockout_time:
            # Désactiver le champ de mot de passe et le bouton de connexion
            self.password_entry.configure(state="disabled")
            self.login_button.configure(state="disabled")
            # Démarrer le compte à rebours
            self._start_countdown(lockout_time)
        
        logger.info("Fenêtre de connexion affichée")
    
    def _handle_close(self):
        """Gère la fermeture de la fenêtre"""
        # Définir les couleurs
        primary_color = "#3498db"     # Bleu principal
        success_color = "#2ecc71"     # Vert pour succès
        error_color = "#e74c3c"       # Rouge pour erreurs
        hover_color = "#2980b9"       # Bleu plus foncé pour hover
        
        # Créer la boîte de dialogue
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Confirmation")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Centrer parfaitement la fenêtre
        dialog.update_idletasks()
        width = 400
        height = 250
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Frame principal avec coins arrondis
        frame = ctk.CTkFrame(
            dialog,
            corner_radius=15,
            border_width=1,
            border_color=("gray85", "gray25")
        )
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Icône d'avertissement
        warning_label = ctk.CTkLabel(
            frame,
            text="⚠️",
            font=ctk.CTkFont(size=40)
        )
        warning_label.pack(pady=(15, 5))
        
        # Message principal
        ctk.CTkLabel(
            frame,
            text="Quitter l'application ?",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(0, 10))
        
        # Message secondaire
        ctk.CTkLabel(
            frame,
            text="L'application se fermera si vous n'êtes pas connecté.",
            wraplength=300,
            font=ctk.CTkFont(size=14)
        ).pack(pady=(0, 20))
        
        # Boutons centrés et espacés
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, pady=(10, 0))
        
        # Bouton Annuler
        ctk.CTkButton(
            button_frame,
            text="Annuler",
            width=150,
            height=40,
            corner_radius=8,
            fg_color=success_color,
            hover_color="#27ae60",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=dialog.destroy
        ).pack(side=ctk.LEFT, padx=10, expand=True)
        
        # Bouton Quitter
        ctk.CTkButton(
            button_frame,
            text="Quitter",
            width=150,
            height=40,
            corner_radius=8,
            fg_color=error_color,
            hover_color="#c0392b",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: [dialog.destroy(), self.window.destroy(), self.parent.destroy()]
        ).pack(side=ctk.RIGHT, padx=10, expand=True)
    
    def _verify_password(self):
        """Vérifie le mot de passe entré"""
        try:
            password = self.password_var.get()
            
            # Hasher le mot de passe entré
            hashed = hashlib.sha256(password.encode()).hexdigest()
            
            if hashed == self.password_hash:
                # Enregistrer la tentative réussie
                self.attempt_manager.record_attempt(True)
                
                logger.info("Connexion réussie")
                self.window.destroy()
                self.window = None
                self.on_success()
                return True
            else:
                # Enregistrer la tentative échouée
                self.attempt_manager.record_attempt(False)
                self._password_attempts += 1
                
                can_attempt, lockout_time = self.attempt_manager.can_attempt()
                if not can_attempt and lockout_time:
                    # Compte bloqué temporairement
                    self.password_entry.configure(state="disabled")
                    self.login_button.configure(state="disabled")
                    self._start_countdown(lockout_time)
                else:
                    # Afficher le nombre de tentatives restantes
                    remaining = self._max_attempts - self._password_attempts
                    if remaining > 0:
                        self.error_label.configure(
                            text=f"Mot de passe incorrect. {remaining} tentative{'s' if remaining > 1 else ''} restante{'s' if remaining > 1 else ''}"
                        )
                    else:
                        # Si on dépasse les tentatives mais pas encore de blocage
                        self.error_label.configure(
                            text="Mot de passe incorrect. Soyez prudent, le compte pourrait être bloqué temporairement."
                        )
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du mot de passe: {e}")
            self.error_label.configure(text="Une erreur est survenue")
            return False
    
    def _start_countdown(self, remaining_time):
        """
        Démarre le compte à rebours
        
        Args:
            remaining_time: Temps restant avant la fin du blocage
        """
        if self._countdown_timer:
            self.window.after_cancel(self._countdown_timer)
        
        end_time = datetime.now() + remaining_time
        
        def update_countdown():
            remaining = end_time - datetime.now()
            if remaining.total_seconds() <= 0:
                # Réactiver les champs
                self.password_entry.configure(state="normal")
                self.login_button.configure(state="normal")
                
                # Réinitialiser le message
                self.error_label.configure(
                    text="Vous pouvez maintenant réessayer.",
                    text_color="#2ecc71"
                )
                
                # Vider le champ de mot de passe
                self.password_var.set("")
                
                # Donner le focus au champ de mot de passe
                self.password_entry.focus()
                
                return
            
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            self.error_label.configure(
                text=f"Compte temporairement bloqué. Réessayez dans {minutes:02d}:{seconds:02d}",
                text_color="#e74c3c"
            )
            self._countdown_timer = self.window.after(1000, update_countdown)
        
        update_countdown()
    
    def _show_reset_dialog(self):
        """Affiche la boîte de dialogue de réinitialisation du mot de passe"""
        # Définir les couleurs
        primary_color = "#3498db"     # Bleu principal
        success_color = "#2ecc71"     # Vert pour succès
        error_color = "#e74c3c"       # Rouge pour erreurs
        hover_color = "#2980b9"       # Bleu plus foncé pour hover
        
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Réinitialisation du mot de passe")
        dialog.geometry("550x450")    # Augmentation de la taille pour éviter les troncatures
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Centrer parfaitement la fenêtre
        dialog.update_idletasks()
        width = 550
        height = 450
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Frame principal avec coins arrondis
        main_frame = ctk.CTkFrame(
            dialog,
            corner_radius=15,
            border_width=1,
            border_color=("gray85", "gray25")
        )
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Icône de réinitialisation
        reset_icon = ctk.CTkLabel(
            main_frame,
            text="🔄",
            font=ctk.CTkFont(size=40)
        )
        reset_icon.pack(pady=(20, 5))
        
        # Titre
        title_label = ctk.CTkLabel(
            main_frame,
            text="Réinitialisation du mot de passe",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Message d'instructions
        message_label = ctk.CTkLabel(
            main_frame,
            text="Entrez votre adresse email pour recevoir\nun mot de passe temporaire",
            wraplength=400,
            font=ctk.CTkFont(size=14)
        )
        message_label.pack(pady=(0, 20))
        
        # Champ email avec icône
        email_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        email_frame.pack(pady=(0, 20), fill=ctk.X, padx=50)
        
        email_var = ctk.StringVar()
        email_entry = ctk.CTkEntry(
            email_frame,
            placeholder_text="Adresse email",
            textvariable=email_var,
            height=40,
            border_width=1,
            corner_radius=8,
            font=ctk.CTkFont(size=14)
        )
        email_entry.pack(fill=ctk.X)
        
        # Message d'erreur
        error_label = ctk.CTkLabel(
            main_frame,
            text="",
            text_color=error_color,
            wraplength=400,
            font=ctk.CTkFont(size=13)
        )
        error_label.pack(pady=(0, 20))
        
        def send_reset_email():
            """Envoie l'email de réinitialisation"""
            email = email_var.get().strip()
            
            if not email:
                error_label.configure(text="Veuillez entrer une adresse email")
                return
            
            # Vérifier que l'email est configuré
            if not self.email_config.is_configured():
                error_label.configure(text="La configuration email n'est pas disponible. Veuillez configurer l'email dans les paramètres.")
                return
            
            # Vérifier que l'email est autorisé (à adapter selon vos besoins)
            config_file = os.path.join("data", "config.json")
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                authorized_email = config.get("security", {}).get("admin_email")
                if not authorized_email or email != authorized_email:
                    error_label.configure(text="Cette adresse email n'est pas autorisée")
                    return
                
                # Générer un mot de passe temporaire
                temp_password = self._generate_temp_password()
                
                # Envoyer l'email
                if self._send_temp_password(email, temp_password):
                    # Hasher et sauvegarder le mot de passe temporaire
                    temp_hash = hashlib.sha256(temp_password.encode()).hexdigest()
                    config["security"]["password_hash"] = temp_hash
                    config["security"]["require_password_change"] = True
                    
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                    
                    # Mettre à jour le hash dans la vue
                    self.password_hash = temp_hash
                    
                    # Fermer la boîte de dialogue
                    dialog.destroy()
                    
                    # Afficher un message de succès
                    self.error_label.configure(
                        text="Un mot de passe temporaire a été envoyé à votre adresse email",
                        text_color=success_color
                    )
                    
                    logger.info(f"Mot de passe temporaire envoyé à {email}")
                else:
                    error_label.configure(text="Erreur lors de l'envoi de l'email. Vérifiez la configuration email dans les paramètres.")
            
            except Exception as e:
                logger.error(f"Erreur lors de la réinitialisation: {e}")
                error_label.configure(text="Une erreur est survenue")
        
        # Boutons avec disposition améliorée
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, pady=(0, 25))  # Augmentation du padding vertical
        
        # Bouton Annuler - à gauche
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Annuler",
            width=100,               # Réduit de 130 à 100
            height=35,               # Réduit de 40 à 35
            corner_radius=8,
            fg_color=error_color,
            hover_color="#c0392b",
            font=ctk.CTkFont(size=13, weight="bold"),  # Taille de police réduite
            command=dialog.destroy
        )
        cancel_button.pack(side=ctk.LEFT, padx=(80, 10), pady=10)  # Padding horizontal augmenté
        
        # Bouton Envoyer - à droite
        send_button = ctk.CTkButton(
            button_frame,
            text="Envoyer",
            width=100,               # Réduit de 130 à 100
            height=35,               # Réduit de 40 à 35
            corner_radius=8,
            fg_color=success_color,
            hover_color="#27ae60",
            font=ctk.CTkFont(size=13, weight="bold"),  # Taille de police réduite
            command=send_reset_email
        )
        send_button.pack(side=ctk.RIGHT, padx=(10, 80), pady=10)  # Padding horizontal augmenté

        # Ajout du lien "Aide" discret et subtil
        help_label = ctk.CTkLabel(
            main_frame,
            text="Aide",
            text_color=("gray40", "gray60"),  # Couleur sombre et subtile
            cursor="hand2",
            font=ctk.CTkFont(size=11, underline=True)  # Petite taille de police
        )
        help_label.pack(pady=(15, 5))  # Position juste en dessous des boutons
        help_label.bind("<Button-1>", lambda e: self._open_email())
        help_label.bind("<Enter>", lambda e: help_label.configure(text_color=("#555555", "#aaaaaa")))
        help_label.bind("<Leave>", lambda e: help_label.configure(text_color=("gray40", "gray60")))
        
        # Focus sur le champ email
        email_entry.focus()
    
    def _open_email(self):
        """Ouvre le client email par défaut"""
        import webbrowser
        webbrowser.open("mailto:contact@vynalapp.com")