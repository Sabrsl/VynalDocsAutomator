import os
import logging
from typing import Optional
from functools import wraps

logger = logging.getLogger("VynalDocsAutomator.AccessControl")

class AccessControl:
    """Gestionnaire de contrôle d'accès"""
    
    def __init__(self):
        # Liste des administrateurs (seuls ces utilisateurs auront accès à l'interface admin)
        self.admin_users = {
            "DESKTOP-L5HUVH6\\badza"  # Votre compte administrateur
        }
    
    def is_admin(self, username: str) -> bool:
        """Vérifie si l'utilisateur est administrateur"""
        return username in self.admin_users
    
    def check_admin_access(self) -> bool:
        """Vérifie si l'utilisateur actuel a les droits d'administration"""
        try:
            current_user = os.getenv('USERNAME')
            if not current_user:
                logger.error("Impossible de déterminer l'utilisateur actuel")
                return False
            
            is_admin = self.is_admin(f"{os.getenv('COMPUTERNAME')}\\{current_user}")
            if not is_admin:
                logger.warning(f"Tentative d'accès administrateur non autorisée par {current_user}")
            
            return is_admin
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des droits d'administration: {e}")
            return False
    
    def check_user_access(self) -> bool:
        """Vérifie si l'utilisateur peut accéder à l'application
        Tous les utilisateurs ont accès aux fonctionnalités standard"""
        return True

# Décorateur pour protéger les fonctions administratives
def admin_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        access_control = AccessControl()
        if not access_control.check_admin_access():
            raise PermissionError("Cette fonctionnalité est réservée à l'administrateur")
        return func(*args, **kwargs)
    return wrapper

# Décorateur pour les fonctionnalités utilisateur standard
def user_access(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        access_control = AccessControl()
        if not access_control.check_user_access():
            raise PermissionError("Accès non autorisé")
        return func(*args, **kwargs)
    return wrapper 