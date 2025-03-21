#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitaire de chiffrement pour les données sensibles
"""

import os
import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger("VynalDocsAutomator.CryptoUtils")

class CryptoUtils:
    """Utilitaire pour chiffrer/déchiffrer les données sensibles"""
    
    def __init__(self, app_key=None):
        """
        Initialise l'utilitaire de chiffrement
        
        Args:
            app_key: Clé de l'application pour le chiffrement
        """
        self.key_file = os.path.join("data", ".key")
        self.salt = b'VynalDocsAutomator'  # Salt fixe pour la dérivation de clé
        self._fernet = None
        
        # Générer ou charger la clé
        if app_key:
            self._init_key(app_key)
        else:
            self._load_or_generate_key()
    
    def _init_key(self, password):
        """Initialise la clé de chiffrement à partir d'un mot de passe"""
        try:
            # Dériver une clé à partir du mot de passe
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            self._fernet = Fernet(key)
            
            # Sauvegarder la clé
            with open(self.key_file, 'wb') as f:
                f.write(key)
            
            logger.info("Clé de chiffrement initialisée")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la clé: {e}")
            raise
    
    def _load_or_generate_key(self):
        """Charge ou génère une clé de chiffrement"""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
            
            self._fernet = Fernet(key)
            logger.info("Clé de chiffrement chargée")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la clé: {e}")
            raise
    
    def encrypt_data(self, data: dict) -> str:
        """
        Chiffre des données
        
        Args:
            data: Dictionnaire de données à chiffrer
            
        Returns:
            str: Données chiffrées en base64
        """
        try:
            json_data = json.dumps(data)
            encrypted = self._fernet.encrypt(json_data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Erreur lors du chiffrement: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> dict:
        """
        Déchiffre des données
        
        Args:
            encrypted_data: Données chiffrées en base64
            
        Returns:
            dict: Données déchiffrées
        """
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_data)
            decrypted = self._fernet.decrypt(encrypted)
            return json.loads(decrypted)
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement: {e}")
            raise 