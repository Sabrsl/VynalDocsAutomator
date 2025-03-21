#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modèle pour les tokens de réinitialisation de mot de passe
"""

from datetime import datetime, timedelta
import uuid

class PasswordResetToken:
    """Gère les tokens de réinitialisation de mot de passe"""
    
    def __init__(self, email: str):
        self.token = str(uuid.uuid4())
        self.email = email
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(hours=1)
        self.used = False
        self.temp_password = None

    def is_valid(self) -> bool:
        """Vérifie si le token est toujours valide"""
        return not self.used and datetime.now() < self.expires_at

    def to_dict(self) -> dict:
        """Convertit le token en dictionnaire pour le stockage"""
        data = {
            "token": self.token,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "used": self.used
        }
        if self.temp_password:
            data["temp_password"] = self.temp_password
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'PasswordResetToken':
        """Crée un token à partir d'un dictionnaire"""
        token = cls(data["email"])
        token.token = data["token"]
        token.created_at = datetime.fromisoformat(data["created_at"])
        token.expires_at = datetime.fromisoformat(data["expires_at"])
        token.used = data["used"]
        token.temp_password = data.get("temp_password")
        return token

    def set_expiry(self, hours: int) -> None:
        """Définit la date d'expiration du token"""
        self.expires_at = datetime.now() + timedelta(hours=hours)

    def mark_as_used(self) -> None:
        """Marque le token comme utilisé"""
        self.used = True 