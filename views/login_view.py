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

logger = logging.getLogger("VynalDocsAutomator.LoginView")

class LoginView:
    """Vue de connexion avec protection par mot de passe"""
    
    def __init__(self, parent: tk.Widget, on_success: Callable[[], None]):
        """
        Initialise la vue de connexion
        
        Args:
            parent: Widget parent
            on_success: Callback appelé après une connexion réussie
        """
        self.parent = parent
        self.on_success = on_success
        self.window = None
        self._password_attempts = 0
        self._max_attempts = 3
        
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
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = ''.join(random.choice(characters) for _ in range(length))
            # Vérifier que le mot de passe respecte les critères
            if (any(c.isupper() for c in password) and
                any(c.islower() for c in password) and
                any(c.isdigit() for c in password) and
                any(c in "!@#$%^&*" for c in password)):
                return password
    
    def _send_temp_password(self, email, temp_password):
        """Envoie le mot de passe temporaire par email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config["from_email"]
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
            
            server = smtplib.SMTP(self.smtp_config["server"], self.smtp_config["port"])
            server.starttls()
            server.login(self.smtp_config["username"], self.smtp_config["password"])
            server.send_message(msg)
            server.quit()
            
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
        
        # Créer la fenêtre de connexion
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("Connexion")
        self.window.geometry("400x350")
        self.window.resizable(False, False)
        
        # Empêcher l'interaction avec la fenêtre principale
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Centrer la fenêtre
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - self.window.winfo_width()) // 2
        y = (self.window.winfo_screenheight() - self.window.winfo_height()) // 2
        self.window.geometry(f"+{x}+{y}")
        
        # Créer les widgets
        frame = ctk.CTkFrame(self.window)
        frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre
        title_label = ctk.CTkLabel(
            frame,
            text="🔒 Protection par mot de passe",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Message
        message_label = ctk.CTkLabel(
            frame,
            text="Veuillez entrer votre mot de passe pour accéder à l'application",
            wraplength=300
        )
        message_label.pack(pady=(0, 20))
        
        # Champ de mot de passe
        self.password_var = ctk.StringVar()
        password_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Mot de passe",
            show="•",
            width=200,
            textvariable=self.password_var
        )
        password_entry.pack(pady=(0, 20))
        
        # Bouton de connexion
        login_button = ctk.CTkButton(
            frame,
            text="Se connecter",
            width=200,
            command=self._verify_password
        )
        login_button.pack(pady=(0, 10))
        
        # Message d'erreur (initialement caché)
        self.error_label = ctk.CTkLabel(
            frame,
            text="",
            text_color="red"
        )
        self.error_label.pack(pady=(0, 10))
        
        # Lien "Mot de passe oublié"
        forgot_password_label = ctk.CTkLabel(
            frame,
            text="Mot de passe oublié ?",
            text_color=("blue", "#3498db"),
            cursor="hand2"
        )
        forgot_password_label.pack(pady=(10, 0))
        forgot_password_label.bind("<Button-1>", lambda e: self._show_reset_dialog())
        
        # Lier la touche Entrée à la vérification du mot de passe
        self.window.bind('<Return>', lambda e: self._verify_password())
        
        # Focus sur le champ de mot de passe
        password_entry.focus()
        
        # Empêcher la fermeture de la fenêtre
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        
        logger.info("Fenêtre de connexion affichée")
    
    def _verify_password(self):
        """Vérifie le mot de passe entré"""
        try:
            password = self.password_var.get()
            
            # Hasher le mot de passe entré
            hashed = hashlib.sha256(password.encode()).hexdigest()
            
            if hashed == self.password_hash:
                logger.info("Connexion réussie")
                self.window.destroy()
                self.window = None
                self.on_success()
            else:
                self._password_attempts += 1
                remaining = self._max_attempts - self._password_attempts
                
                if remaining > 0:
                    self.error_label.configure(
                        text=f"Mot de passe incorrect. {remaining} tentative{'s' if remaining > 1 else ''} restante{'s' if remaining > 1 else ''}"
                    )
                else:
                    logger.warning("Nombre maximum de tentatives atteint")
                    self.error_label.configure(
                        text="Nombre maximum de tentatives atteint. L'application va se fermer."
                    )
                    self.window.after(2000, self.parent.destroy)
        
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du mot de passe: {e}")
            self.error_label.configure(text="Une erreur est survenue")
    
    def _show_reset_dialog(self):
        """Affiche la boîte de dialogue de réinitialisation du mot de passe"""
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Réinitialisation du mot de passe")
        dialog.geometry("500x300")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Frame principal
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔄 Réinitialisation du mot de passe",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Message d'instructions
        message_label = ctk.CTkLabel(
            main_frame,
            text="Entrez votre adresse email pour recevoir un mot de passe temporaire",
            wraplength=400
        )
        message_label.pack(pady=(0, 20))
        
        # Champ email
        email_var = ctk.StringVar()
        email_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="Adresse email",
            width=300,
            textvariable=email_var
        )
        email_entry.pack(pady=(0, 20))
        
        # Message d'erreur
        error_label = ctk.CTkLabel(
            main_frame,
            text="",
            text_color="red",
            wraplength=400
        )
        error_label.pack(pady=(0, 20))
        
        def send_reset_email():
            """Envoie l'email de réinitialisation"""
            email = email_var.get().strip()
            
            if not email:
                error_label.configure(text="Veuillez entrer une adresse email")
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
                        text_color="green"
                    )
                    
                    logger.info(f"Mot de passe temporaire envoyé à {email}")
                else:
                    error_label.configure(text="Erreur lors de l'envoi de l'email")
            
            except Exception as e:
                logger.error(f"Erreur lors de la réinitialisation: {e}")
                error_label.configure(text="Une erreur est survenue")
        
        # Boutons
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, pady=(20, 0))
        
        # Bouton Annuler
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            width=140,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=dialog.destroy
        )
        cancel_button.pack(side=ctk.LEFT, padx=10)
        
        # Bouton Envoyer
        send_button = ctk.CTkButton(
            buttons_frame,
            text="Envoyer",
            width=140,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=send_reset_email
        )
        send_button.pack(side=ctk.RIGHT, padx=10)
        
        # Focus sur le champ email
        email_entry.focus()
    
    def _on_close(self):
        """Empêche la fermeture de la fenêtre"""
        pass 