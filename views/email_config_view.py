#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interface de configuration email
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from utils.email_config import EmailConfig

logger = logging.getLogger("VynalDocsAutomator.EmailConfigView")

class EmailConfigDialog(tk.Toplevel):
    """Dialogue de configuration email"""
    
    def __init__(self, parent, app_key=None):
        """
        Initialise le dialogue de configuration email
        
        Args:
            parent: Fenêtre parente
            app_key: Clé de l'application pour le chiffrement
        """
        super().__init__(parent)
        
        self.title("Configuration Email")
        self.geometry("500x450")
        self.resizable(False, False)
        
        # Centrer la fenêtre
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
        self.email_config = EmailConfig(app_key)
        self._create_widgets()
        self._load_config()
    
    def _create_widgets(self):
        """Crée les widgets de l'interface"""
        # Frame principal
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Activation email
        enabled_frame = ttk.LabelFrame(main_frame, text="Activation", padding="5")
        enabled_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self.enabled_var = tk.BooleanVar()
        enabled_check = ttk.Checkbutton(
            enabled_frame,
            text="Activer l'envoi d'emails",
            variable=self.enabled_var
        )
        enabled_check.grid(row=0, column=0, sticky="w")
        
        # Configuration SMTP
        smtp_frame = ttk.LabelFrame(main_frame, text="Configuration SMTP", padding="5")
        smtp_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        
        # Serveur SMTP
        ttk.Label(smtp_frame, text="Serveur:").grid(row=0, column=0, sticky="w", pady=2)
        self.server_var = tk.StringVar()
        server_entry = ttk.Entry(smtp_frame, textvariable=self.server_var, width=40)
        server_entry.grid(row=0, column=1, sticky="ew", pady=2)
        
        # Port SMTP
        ttk.Label(smtp_frame, text="Port:").grid(row=1, column=0, sticky="w", pady=2)
        self.port_var = tk.StringVar()
        port_entry = ttk.Entry(smtp_frame, textvariable=self.port_var, width=10)
        port_entry.grid(row=1, column=1, sticky="w", pady=2)
        
        # Nom d'utilisateur
        ttk.Label(smtp_frame, text="Utilisateur:").grid(row=2, column=0, sticky="w", pady=2)
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(smtp_frame, textvariable=self.username_var, width=40)
        username_entry.grid(row=2, column=1, sticky="ew", pady=2)
        
        # Mot de passe
        ttk.Label(smtp_frame, text="Mot de passe:").grid(row=3, column=0, sticky="w", pady=2)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(smtp_frame, textvariable=self.password_var, show="•", width=40)
        password_entry.grid(row=3, column=1, sticky="ew", pady=2)
        
        # Email expéditeur
        ttk.Label(smtp_frame, text="Email expéditeur:").grid(row=4, column=0, sticky="w", pady=2)
        self.from_email_var = tk.StringVar()
        from_email_entry = ttk.Entry(smtp_frame, textvariable=self.from_email_var, width=40)
        from_email_entry.grid(row=4, column=1, sticky="ew", pady=2)
        
        # TLS
        self.use_tls_var = tk.BooleanVar(value=True)
        use_tls_check = ttk.Checkbutton(
            smtp_frame,
            text="Utiliser TLS",
            variable=self.use_tls_var
        )
        use_tls_check.grid(row=5, column=0, columnspan=2, sticky="w", pady=2)
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Tester la connexion",
            command=self._test_connection
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="Annuler",
            command=self.destroy
        ).pack(side="right", padx=5)
        
        ttk.Button(
            button_frame,
            text="Enregistrer",
            command=self._save_config
        ).pack(side="right", padx=5)
    
    def _load_config(self):
        """Charge la configuration existante"""
        config = self.email_config.get_config()
        smtp = config.get('smtp', {})
        
        self.enabled_var.set(config.get('enabled', False))
        self.server_var.set(smtp.get('server', ''))
        self.port_var.set(str(smtp.get('port', 587)))
        self.username_var.set(smtp.get('username', ''))
        self.password_var.set(smtp.get('password', ''))
        self.from_email_var.set(smtp.get('from_email', ''))
        self.use_tls_var.set(smtp.get('use_tls', True))
    
    def _save_config(self):
        """Sauvegarde la configuration"""
        try:
            # Valider le port
            try:
                port = int(self.port_var.get())
            except ValueError:
                messagebox.showerror(
                    "Erreur",
                    "Le port doit être un nombre entier"
                )
                return
            
            config = {
                "enabled": self.enabled_var.get(),
                "smtp": {
                    "server": self.server_var.get().strip(),
                    "port": port,
                    "username": self.username_var.get().strip(),
                    "password": self.password_var.get(),
                    "from_email": self.from_email_var.get().strip(),
                    "use_tls": self.use_tls_var.get()
                }
            }
            
            self.email_config.save_config(config)
            messagebox.showinfo(
                "Succès",
                "Configuration email sauvegardée avec succès"
            )
            self.destroy()
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
            messagebox.showerror(
                "Erreur",
                "Une erreur est survenue lors de la sauvegarde"
            )
    
    def _test_connection(self):
        """Teste la connexion SMTP"""
        try:
            # Sauvegarder temporairement la configuration
            config = {
                "enabled": True,
                "smtp": {
                    "server": self.server_var.get().strip(),
                    "port": int(self.port_var.get()),
                    "username": self.username_var.get().strip(),
                    "password": self.password_var.get(),
                    "from_email": self.from_email_var.get().strip(),
                    "use_tls": self.use_tls_var.get()
                }
            }
            
            self.email_config.save_config(config)
            
            if self.email_config.test_connection():
                messagebox.showinfo(
                    "Succès",
                    "Connexion SMTP réussie"
                )
            else:
                messagebox.showerror(
                    "Erreur",
                    "Impossible de se connecter au serveur SMTP"
                )
                
        except Exception as e:
            logger.error(f"Erreur lors du test de connexion: {e}")
            messagebox.showerror(
                "Erreur",
                "Une erreur est survenue lors du test de connexion"
            ) 