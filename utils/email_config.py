#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire de configuration email sécurisé
"""

import os
import json
import logging
from .crypto_utils import CryptoUtils

logger = logging.getLogger("VynalDocsAutomator.EmailConfig")

class EmailConfig:
    """Gestionnaire de configuration email sécurisé"""
    
    def __init__(self, app_key=None):
        """
        Initialise le gestionnaire de configuration email
        
        Args:
            app_key: Clé de l'application pour le chiffrement
        """
        self.config_file = os.path.join("data", "email_config.enc")
        self.crypto = CryptoUtils(app_key)
        self._config = self._load_config()
    
    def _load_config(self) -> dict:
        """
        Charge la configuration email
        
        Returns:
            dict: Configuration email
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    encrypted_data = f.read()
                return self.crypto.decrypt_data(encrypted_data)
            else:
                return {
                    "enabled": False,
                    "smtp": {
                        "server": "",
                        "port": 587,
                        "username": "",
                        "password": "",
                        "from_email": "",
                        "use_tls": True
                    }
                }
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration email: {e}")
            return {
                "enabled": False,
                "smtp": {
                    "server": "",
                    "port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "",
                    "use_tls": True
                }
            }
    
    def save_config(self, config: dict):
        """
        Sauvegarde la configuration email de manière sécurisée
        
        Args:
            config: Configuration email à sauvegarder
        """
        try:
            encrypted_data = self.crypto.encrypt_data(config)
            with open(self.config_file, 'w') as f:
                f.write(encrypted_data)
            self._config = config
            logger.info("Configuration email sauvegardée")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration email: {e}")
            raise
    
    def get_config(self) -> dict:
        """
        Récupère la configuration email
        
        Returns:
            dict: Configuration email
        """
        return self._config
    
    def update_config(self, **kwargs):
        """
        Met à jour la configuration email
        
        Args:
            **kwargs: Paramètres à mettre à jour
        """
        config = self._config.copy()
        for key, value in kwargs.items():
            if key.startswith('smtp_'):
                smtp_key = key[5:]  # Enlever le préfixe 'smtp_'
                config['smtp'][smtp_key] = value
            else:
                config[key] = value
        self.save_config(config)
    
    def is_configured(self) -> bool:
        """
        Vérifie si l'email est configuré
        
        Returns:
            bool: True si l'email est configuré, False sinon
        """
        smtp = self._config.get('smtp', {})
        return all([
            self._config.get('enabled', False),
            smtp.get('server'),
            smtp.get('port'),
            smtp.get('username'),
            smtp.get('password'),
            smtp.get('from_email')
        ])
    
    def test_connection(self) -> bool:
        """
        Teste la connexion SMTP
        
        Returns:
            bool: True si la connexion est réussie, False sinon
        """
        if not self.is_configured():
            return False
            
        try:
            import smtplib
            smtp = self._config.get('smtp', {})
            
            with smtplib.SMTP(smtp['server'], smtp['port']) as server:
                if smtp.get('use_tls', True):
                    server.starttls()
                server.login(smtp['username'], smtp['password'])
            
            logger.info("Test de connexion SMTP réussi")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du test de connexion SMTP: {e}")
            return False 