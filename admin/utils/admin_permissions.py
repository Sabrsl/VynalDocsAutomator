#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Système de gestion des permissions pour l'interface d'administration
Définit les permissions et les rôles pour contrôler l'accès aux fonctionnalités administratives
"""

import logging
import functools

logger = logging.getLogger("VynalDocsAutomator.Admin.Permissions")

class PermissionDenied(Exception):
    """Exception levée lorsqu'un utilisateur tente d'accéder à une fonctionnalité sans les permissions nécessaires"""
    pass

class AdminPermissions:
    """
    Gère les permissions administratives et les accès des utilisateurs
    """
    
    # Définir les permissions disponibles
    PERMISSIONS = {
        # Accès au tableau de bord
        'admin.dashboard.view': "Voir le tableau de bord d'administration",
        
        # Gestion des utilisateurs
        'admin.users.view': "Voir la liste des utilisateurs",
        'admin.users.create': "Créer des utilisateurs",
        'admin.users.edit': "Modifier les utilisateurs",
        'admin.users.delete': "Supprimer des utilisateurs",
        
        # Gestion des logs système
        'admin.logs.view': "Voir les journaux système",
        'admin.logs.export': "Exporter les journaux",
        'admin.logs.clear': "Nettoyer les anciens journaux",
        
        # Paramètres avancés
        'admin.settings.view': "Voir les paramètres avancés",
        'admin.settings.edit': "Modifier les paramètres avancés",
        'admin.settings.reset': "Réinitialiser les paramètres aux valeurs par défaut",
        
        # Opérations système
        'admin.system.backup': "Effectuer des sauvegardes",
        'admin.system.integrity': "Vérifier l'intégrité des données",
        'admin.system.optimize': "Optimiser l'application",
        'admin.system.update': "Mettre à jour l'application"
    }
    
    # Définir les rôles avec leurs permissions associées
    ROLES = {
        'admin': [
            # L'administrateur a toutes les permissions
            'admin.dashboard.view',
            'admin.users.view', 'admin.users.create', 'admin.users.edit', 'admin.users.delete',
            'admin.logs.view', 'admin.logs.export', 'admin.logs.clear',
            'admin.settings.view', 'admin.settings.edit', 'admin.settings.reset',
            'admin.system.backup', 'admin.system.integrity', 'admin.system.optimize', 'admin.system.update'
        ],
        'manager': [
            # Le manager a la plupart des permissions sauf les plus sensibles
            'admin.dashboard.view',
            'admin.users.view', 'admin.users.create', 'admin.users.edit',
            'admin.logs.view', 'admin.logs.export',
            'admin.settings.view',
            'admin.system.backup', 'admin.system.integrity', 'admin.system.optimize'
        ],
        'support': [
            # Le support a un accès limité pour l'assistance
            'admin.dashboard.view',
            'admin.users.view',
            'admin.logs.view',
            'admin.settings.view',
            'admin.system.backup', 'admin.system.integrity'
        ],
        'user': [
            # Un utilisateur standard n'a aucune permission administrative
        ]
    }
    
    def __init__(self, app_model):
        """
        Initialise le gestionnaire de permissions
        
        Args:
            app_model: Modèle de l'application principale
        """
        self.app_model = app_model
        logger.info("Gestionnaire de permissions administratives initialisé")
    
    def get_current_user(self):
        """
        Récupère l'utilisateur actuellement connecté
        
        Returns:
            dict: L'utilisateur actuel ou None si non connecté
        """
        # Récupérer l'utilisateur depuis le modèle
        if hasattr(self.app_model, 'current_user'):
            return self.app_model.current_user
        return None
    
    def get_user_role(self, user=None):
        """
        Récupère le rôle d'un utilisateur
        
        Args:
            user: L'utilisateur (utilise l'utilisateur actuel si None)
            
        Returns:
            str: Le rôle de l'utilisateur ('user' par défaut)
        """
        if user is None:
            user = self.get_current_user()
        
        if user and 'role' in user:
            return user['role']
        
        return 'user'  # Rôle par défaut
    
    def has_permission(self, permission, user=None):
        """
        Vérifie si un utilisateur a une permission spécifique
        
        Args:
            permission: La permission à vérifier
            user: L'utilisateur (utilise l'utilisateur actuel si None)
            
        Returns:
            bool: True si l'utilisateur a la permission, False sinon
        """
        # Si la permission n'existe pas, refuser
        if permission not in self.PERMISSIONS:
            logger.warning(f"Permission inconnue: {permission}")
            return False
        
        role = self.get_user_role(user)
        
        # Si le rôle n'existe pas, utiliser le rôle 'user'
        if role not in self.ROLES:
            logger.warning(f"Rôle inconnu: {role}, utilisation du rôle 'user'")
            role = 'user'
        
        # Vérifier si la permission est dans la liste des permissions du rôle
        return permission in self.ROLES[role]
    
    def has_any_permission(self, permissions, user=None):
        """
        Vérifie si un utilisateur a au moins une des permissions spécifiées
        
        Args:
            permissions: Liste des permissions à vérifier
            user: L'utilisateur (utilise l'utilisateur actuel si None)
            
        Returns:
            bool: True si l'utilisateur a au moins une permission, False sinon
        """
        for permission in permissions:
            if self.has_permission(permission, user):
                return True
        return False
    
    def has_all_permissions(self, permissions, user=None):
        """
        Vérifie si un utilisateur a toutes les permissions spécifiées
        
        Args:
            permissions: Liste des permissions à vérifier
            user: L'utilisateur (utilise l'utilisateur actuel si None)
            
        Returns:
            bool: True si l'utilisateur a toutes les permissions, False sinon
        """
        for permission in permissions:
            if not self.has_permission(permission, user):
                return False
        return True
    
    def check_permission(self, permission, user=None):
        """
        Vérifie une permission et lève une exception si l'utilisateur ne l'a pas
        
        Args:
            permission: La permission à vérifier
            user: L'utilisateur (utilise l'utilisateur actuel si None)
            
        Raises:
            PermissionDenied: Si l'utilisateur n'a pas la permission
        """
        if not self.has_permission(permission, user):
            user_info = user if user else self.get_current_user()
            user_id = user_info.get('id', 'inconnu') if user_info else 'non connecté'
            logger.warning(f"Permission refusée: {permission} pour l'utilisateur {user_id}")
            raise PermissionDenied(f"Vous n'avez pas la permission '{permission}'")
    
    def check_any_permission(self, permissions, user=None):
        """
        Vérifie si l'utilisateur a au moins une des permissions et lève une exception sinon
        
        Args:
            permissions: Liste des permissions à vérifier
            user: L'utilisateur (utilise l'utilisateur actuel si None)
            
        Raises:
            PermissionDenied: Si l'utilisateur n'a aucune des permissions
        """
        if not self.has_any_permission(permissions, user):
            user_info = user if user else self.get_current_user()
            user_id = user_info.get('id', 'inconnu') if user_info else 'non connecté'
            logger.warning(f"Permissions refusées: {permissions} pour l'utilisateur {user_id}")
            raise PermissionDenied(f"Vous n'avez aucune des permissions requises")
    
    def check_all_permissions(self, permissions, user=None):
        """
        Vérifie si l'utilisateur a toutes les permissions et lève une exception sinon
        
        Args:
            permissions: Liste des permissions à vérifier
            user: L'utilisateur (utilise l'utilisateur actuel si None)
            
        Raises:
            PermissionDenied: Si l'utilisateur n'a pas toutes les permissions
        """
        for permission in permissions:
            self.check_permission(permission, user)
    
    def get_user_permissions(self, user=None):
        """
        Récupère toutes les permissions d'un utilisateur
        
        Args:
            user: L'utilisateur (utilise l'utilisateur actuel si None)
            
        Returns:
            list: Liste des permissions de l'utilisateur
        """
        role = self.get_user_role(user)
        
        # Si le rôle n'existe pas, utiliser le rôle 'user'
        if role not in self.ROLES:
            role = 'user'
        
        return self.ROLES[role]
    
    def get_permission_description(self, permission):
        """
        Récupère la description d'une permission
        
        Args:
            permission: La permission
            
        Returns:
            str: Description de la permission ou None si elle n'existe pas
        """
        return self.PERMISSIONS.get(permission)
    
    def require_permission(self, permission):
        """
        Décorateur pour exiger une permission pour une fonction
        
        Args:
            permission: La permission requise
        
        Returns:
            function: Décorateur
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                self.check_permission(permission)
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_any_permission(self, permissions):
        """
        Décorateur pour exiger au moins une des permissions pour une fonction
        
        Args:
            permissions: Liste des permissions dont au moins une est requise
            
        Returns:
            function: Décorateur
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                self.check_any_permission(permissions)
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_all_permissions(self, permissions):
        """
        Décorateur pour exiger toutes les permissions pour une fonction
        
        Args:
            permissions: Liste des permissions requises
            
        Returns:
            function: Décorateur
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                self.check_all_permissions(permissions)
                return func(*args, **kwargs)
            return wrapper
        return decorator


# Décorateurs pratiques
def admin_required(func):
    """
    Décorateur pour exiger le rôle d'administrateur
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        perm_manager = getattr(self, 'permissions', None)
        if perm_manager is None and hasattr(self, 'admin_controller'):
            perm_manager = getattr(self.admin_controller, 'permissions', None)
        
        if perm_manager is None:
            logger.error("Gestionnaire de permissions non trouvé")
            raise PermissionDenied("Système de permissions non initialisé")
        
        user = perm_manager.get_current_user()
        role = perm_manager.get_user_role(user)
        
        if role != 'admin':
            logger.warning(f"Accès refusé: rôle administrateur requis, utilisateur: {role}")
            raise PermissionDenied("Vous devez être administrateur pour effectuer cette action")
        
        return func(self, *args, **kwargs)
    return wrapper


def manager_required(func):
    """
    Décorateur pour exiger au moins le rôle de manager
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        perm_manager = getattr(self, 'permissions', None)
        if perm_manager is None and hasattr(self, 'admin_controller'):
            perm_manager = getattr(self.admin_controller, 'permissions', None)
        
        if perm_manager is None:
            logger.error("Gestionnaire de permissions non trouvé")
            raise PermissionDenied("Système de permissions non initialisé")
        
        user = perm_manager.get_current_user()
        role = perm_manager.get_user_role(user)
        
        if role not in ['admin', 'manager']:
            logger.warning(f"Accès refusé: rôle manager requis, utilisateur: {role}")
            raise PermissionDenied("Vous devez être manager ou administrateur pour effectuer cette action")
        
        return func(self, *args, **kwargs)
    return wrapper