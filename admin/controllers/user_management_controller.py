#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contrôleur de gestion des utilisateurs pour l'interface d'administration
Gère les opérations liées aux utilisateurs de l'application
"""

import logging
import re
import os
import json
import csv
import hashlib
from datetime import datetime, timedelta
import threading
from admin.utils.admin_permissions import PermissionDenied, admin_required, manager_required

logger = logging.getLogger("VynalDocsAutomator.Admin.UserManagementController")

class UserManagementController:
    """
    Contrôleur pour la gestion des utilisateurs
    Coordonne les actions entre les vues de gestion des utilisateurs et le modèle
    """
    
    def __init__(self, admin_controller, admin_model):
        """
        Initialise le contrôleur de gestion des utilisateurs
        
        Args:
            admin_controller: Contrôleur principal d'administration
            admin_model: Modèle d'administration
        """
        self.admin_controller = admin_controller
        self.model = admin_model
        self.permissions = admin_controller.permissions if hasattr(admin_controller, 'permissions') else None
        
        # Cache des utilisateurs (pour éviter des requêtes fréquentes)
        self.users_cache = []
        self.last_cache_update = None
        self.cache_lock = threading.Lock()
        
        # Paramètres de validation
        self.password_min_length = 8
        self.password_requires_mixed_case = True
        self.password_requires_digit = True
        self.password_requires_special = True
        self.email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # Limites de tentatives de connexion
        self.failed_login_attempts = {}  # {email: {count: n, last_attempt: timestamp}}
        self.max_login_attempts = 5
        self.lockout_duration_minutes = 15
        
        # Initialisation
        self._load_security_settings()
        
        logger.info("Contrôleur de gestion des utilisateurs initialisé")
    
    def _load_security_settings(self):
        """
        Charge les paramètres de sécurité depuis la configuration
        """
        try:
            # Charger les paramètres s'ils existent
            if hasattr(self.model, 'get_config'):
                # Paramètres de mot de passe
                self.password_min_length = int(self.model.get_config('security.password_min_length', self.password_min_length))
                self.password_requires_mixed_case = self.model.get_config('security.password_requires_mixed_case', 'true').lower() == 'true'
                self.password_requires_digit = self.model.get_config('security.password_requires_digit', 'true').lower() == 'true'
                self.password_requires_special = self.model.get_config('security.password_requires_special', 'true').lower() == 'true'
                
                # Limites de tentatives
                self.max_login_attempts = int(self.model.get_config('security.max_login_attempts', self.max_login_attempts))
                self.lockout_duration_minutes = int(self.model.get_config('security.lockout_duration', self.lockout_duration_minutes))
            
            logger.debug("Paramètres de sécurité chargés")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des paramètres de sécurité: {e}")
    
    #-----------------------
    # Gestion des utilisateurs
    #-----------------------
    
    def get_users(self, force_refresh=False):
        """
        Récupère la liste des utilisateurs avec mise en cache
        
        Args:
            force_refresh: Force le rafraîchissement du cache
            
        Returns:
            list: Liste des utilisateurs
        """
        with self.cache_lock:
            current_time = datetime.now()
            cache_expired = (self.last_cache_update is None or 
                           (current_time - self.last_cache_update).total_seconds() > 60)
            
            if force_refresh or cache_expired or not self.users_cache:
                try:
                    # Récupérer les utilisateurs depuis le modèle
                    self.users_cache = self.model.get_users()
                    self.last_cache_update = current_time
                    
                    # Trier les utilisateurs (admins en premier, puis par nom)
                    self.users_cache.sort(key=lambda u: (
                        0 if u.get('role') == 'admin' else 
                        1 if u.get('role') == 'manager' else 
                        2 if u.get('role') == 'support' else 3,
                        u.get('last_name', '').lower(),
                        u.get('first_name', '').lower()
                    ))
                    
                    # Filtrer les mots de passe pour la sécurité
                    for user in self.users_cache:
                        if 'password' in user:
                            del user['password']
                    
                    logger.debug(f"Liste des utilisateurs mise à jour ({len(self.users_cache)} utilisateurs)")
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération des utilisateurs: {e}")
                    # En cas d'erreur, conserver l'ancien cache s'il existe
                    if not self.users_cache:
                        self.users_cache = []
            
            return self.users_cache.copy()
    
    @manager_required
    def create_user(self, user_data):
        """
        Crée un nouvel utilisateur
        
        Args:
            user_data: Données de l'utilisateur
            
        Returns:
            tuple: (success, message, user_id)
        """
        try:
            # Vérifier les permissions
            if self.permissions:
                self.permissions.check_permission('admin.users.create')
            
            # Valider les données
            validation_result, validation_message = self.validate_user_data(user_data, is_new=True)
            if not validation_result:
                return False, validation_message, None
            
            # Vérifier si l'email existe déjà
            existing_user = self.get_user_by_email(user_data.get('email'))
            if existing_user:
                return False, "Un utilisateur avec cet email existe déjà", None
            
            # Préparer les données pour la création
            user_data_copy = user_data.copy()
            
            # Si le rôle n'est pas spécifié, attribuer le rôle par défaut
            if 'role' not in user_data_copy:
                user_data_copy['role'] = 'user'
            
            # Vérifier si l'utilisateur a le droit d'attribuer ce rôle
            if not self.can_manage_role(user_data_copy.get('role')):
                return False, f"Vous n'avez pas les droits pour créer un utilisateur avec le rôle '{user_data_copy.get('role')}'", None
            
            # Générer un mot de passe aléatoire si non fourni
            if 'password' not in user_data_copy or not user_data_copy['password']:
                user_data_copy['password'] = self.generate_secure_password()
                temporary_password = user_data_copy['password']
            else:
                temporary_password = None
            
            # Ajouter l'utilisateur
            success = self.model.add_user(user_data_copy)
            
            if success:
                # Rafraîchir le cache
                self.get_users(force_refresh=True)
                
                # Journaliser l'action
                if self.admin_controller and hasattr(self.admin_controller, 'add_activity'):
                    self.admin_controller.add_activity(
                        "Création d'utilisateur",
                        f"Email: {user_data_copy.get('email')}, Rôle: {user_data_copy.get('role')}"
                    )
                
                # Retrouver l'ID de l'utilisateur créé
                created_user = self.get_user_by_email(user_data_copy.get('email'))
                user_id = created_user.get('id') if created_user else None
                
                # Message de succès
                if temporary_password:
                    message = f"Utilisateur créé avec succès. Mot de passe temporaire: {temporary_password}"
                else:
                    message = "Utilisateur créé avec succès"
                
                return True, message, user_id
            else:
                return False, "Erreur lors de la création de l'utilisateur", None
        except PermissionDenied:
            return False, "Vous n'avez pas les permissions nécessaires pour créer un utilisateur", None
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
            return False, f"Une erreur est survenue: {e}", None
    
    @manager_required
    def update_user(self, user_data):
        """
        Met à jour un utilisateur existant
        
        Args:
            user_data: Données de l'utilisateur
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Vérifier les permissions
            if self.permissions:
                self.permissions.check_permission('admin.users.edit')
            
            # Vérifier l'ID
            if 'id' not in user_data:
                return False, "ID utilisateur manquant"
            
            # Récupérer l'utilisateur existant
            existing_user = self.get_user_by_id(user_data['id'])
            if not existing_user:
                return False, f"Utilisateur avec ID {user_data['id']} non trouvé"
            
            # Vérifier si l'utilisateur courant a le droit de modifier cet utilisateur
            if not self.can_edit_user(existing_user):
                return False, "Vous n'avez pas les droits pour modifier cet utilisateur"
            
            # Vérifier si l'email est modifié et déjà utilisé par un autre
            if 'email' in user_data and user_data['email'] != existing_user.get('email'):
                other_user = self.get_user_by_email(user_data['email'])
                if other_user and other_user['id'] != user_data['id']:
                    return False, "Cet email est déjà utilisé par un autre utilisateur"
            
            # Valider les données
            validation_result, validation_message = self.validate_user_data(user_data, is_new=False, existing_user=existing_user)
            if not validation_result:
                return False, validation_message
            
            # Préparer les données pour la mise à jour
            user_data_copy = user_data.copy()
            
            # Préserver les champs non modifiés
            for key in existing_user:
                if key not in user_data_copy:
                    user_data_copy[key] = existing_user[key]
            
            # Vérifier si le rôle est modifié et si l'utilisateur a le droit de le faire
            if 'role' in user_data_copy and user_data_copy['role'] != existing_user.get('role'):
                if not self.can_manage_role(user_data_copy['role']):
                    return False, f"Vous n'avez pas les droits pour attribuer le rôle '{user_data_copy['role']}'"
            
            # Vérifier si c'est le dernier administrateur
            if existing_user.get('role') == 'admin' and user_data_copy.get('role') != 'admin':
                admin_count = sum(1 for u in self.get_users() if u.get('role') == 'admin')
                if admin_count <= 1:
                    return False, "Impossible de modifier le dernier administrateur"
            
            # Ajouter l'horodatage de mise à jour
            user_data_copy['updated_at'] = datetime.now().isoformat()
            
            # Mettre à jour l'utilisateur
            success = self.model.update_user(user_data_copy)
            
            if success:
                # Rafraîchir le cache
                self.get_users(force_refresh=True)
                
                # Journaliser l'action
                if self.admin_controller and hasattr(self.admin_controller, 'add_activity'):
                    self.admin_controller.add_activity(
                        "Mise à jour d'utilisateur",
                        f"ID: {user_data_copy['id']}, Email: {user_data_copy.get('email')}"
                    )
                
                return True, "Utilisateur mis à jour avec succès"
            else:
                return False, "Erreur lors de la mise à jour de l'utilisateur"
        except PermissionDenied:
            return False, "Vous n'avez pas les permissions nécessaires pour modifier un utilisateur"
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'utilisateur: {e}")
            return False, f"Une erreur est survenue: {e}"
    
    @admin_required
    def delete_user(self, user_id):
        """
        Supprime un utilisateur
        
        Args:
            user_id: ID de l'utilisateur à supprimer
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Vérifier les permissions
            if self.permissions:
                self.permissions.check_permission('admin.users.delete')
            
            # Récupérer l'utilisateur
            user = self.get_user_by_id(user_id)
            if not user:
                return False, f"Utilisateur avec ID {user_id} non trouvé"
            
            # Vérifier si l'utilisateur courant a le droit de supprimer cet utilisateur
            if not self.can_delete_user(user):
                return False, "Vous n'avez pas les droits pour supprimer cet utilisateur"
            
            # Vérifier si c'est le dernier administrateur
            if user.get('role') == 'admin':
                admin_count = sum(1 for u in self.get_users() if u.get('role') == 'admin')
                if admin_count <= 1:
                    return False, "Impossible de supprimer le dernier administrateur"
            
            # Vérifier si c'est l'utilisateur actuel
            if self.model.current_user and self.model.current_user.get('id') == user_id:
                return False, "Vous ne pouvez pas supprimer votre propre compte"
            
            # Supprimer l'utilisateur
            success = self.model.delete_user(user_id)
            
            if success:
                # Rafraîchir le cache
                self.get_users(force_refresh=True)
                
                # Journaliser l'action
                if self.admin_controller and hasattr(self.admin_controller, 'add_activity'):
                    self.admin_controller.add_activity(
                        "Suppression d'utilisateur",
                        f"ID: {user_id}, Email: {user.get('email')}"
                    )
                
                return True, "Utilisateur supprimé avec succès"
            else:
                return False, "Erreur lors de la suppression de l'utilisateur"
        except PermissionDenied:
            return False, "Vous n'avez pas les permissions nécessaires pour supprimer un utilisateur"
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'utilisateur: {e}")
            return False, f"Une erreur est survenue: {e}"
    
    def get_user_by_id(self, user_id):
        """
        Récupère un utilisateur par son ID
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            dict: Utilisateur ou None si non trouvé
        """
        # Essayer d'abord dans le cache
        for user in self.get_users():
            if user.get('id') == user_id:
                return user
        
        # Si non trouvé, essayer directement depuis le modèle
        return self.model.get_user_by_id(user_id)
    
    def get_user_by_email(self, email):
        """
        Récupère un utilisateur par son email
        
        Args:
            email: Email de l'utilisateur
            
        Returns:
            dict: Utilisateur ou None si non trouvé
        """
        # Essayer d'abord dans le cache
        for user in self.get_users():
            if user.get('email') == email:
                return user
        
        # Si non trouvé, essayer directement depuis le modèle
        return self.model.get_user_by_email(email)
    
    def can_edit_user(self, user):
        """
        Vérifie si l'utilisateur courant peut modifier un utilisateur donné
        
        Args:
            user: Utilisateur à modifier
            
        Returns:
            bool: True si l'édition est autorisée
        """
        if not user:
            return False
        
        current_user = self.model.current_user
        if not current_user:
            return False
        
        # Les admins peuvent modifier n'importe qui
        if current_user.get('role') == 'admin':
            return True
        
        # Les managers peuvent modifier les utilisateurs de niveau inférieur
        if current_user.get('role') == 'manager':
            if user.get('role') in ['user', 'support']:
                return True
            # Les managers peuvent aussi modifier leur propre profil
            if user.get('id') == current_user.get('id'):
                return True
        
        # Les autres ne peuvent modifier que leur propre profil
        return user.get('id') == current_user.get('id')
    
    def can_delete_user(self, user):
        """
        Vérifie si l'utilisateur courant peut supprimer un utilisateur donné
        
        Args:
            user: Utilisateur à supprimer
            
        Returns:
            bool: True si la suppression est autorisée
        """
        if not user:
            return False
        
        current_user = self.model.current_user
        if not current_user:
            return False
        
        # Les admins peuvent supprimer n'importe qui sauf eux-mêmes
        if current_user.get('role') == 'admin':
            return user.get('id') != current_user.get('id')
        
        # Les managers peuvent supprimer les utilisateurs de niveau inférieur
        if current_user.get('role') == 'manager':
            return user.get('role') in ['user', 'support']
        
        # Les autres ne peuvent pas supprimer d'utilisateurs
        return False
    
    def can_manage_role(self, role):
        """
        Vérifie si l'utilisateur courant peut attribuer un rôle donné
        
        Args:
            role: Rôle à attribuer
            
        Returns:
            bool: True si l'attribution est autorisée
        """
        current_user = self.model.current_user
        if not current_user:
            return False
        
        # Les admins peuvent attribuer n'importe quel rôle
        if current_user.get('role') == 'admin':
            return True
        
        # Les managers peuvent attribuer des rôles inférieurs
        if current_user.get('role') == 'manager':
            return role in ['user', 'support']
        
        # Les autres ne peuvent pas attribuer de rôles
        return False
    
    #-----------------------
    # Authentification
    #-----------------------
    
    def authenticate(self, email, password):
        """
        Authentifie un utilisateur
        
        Args:
            email: Email de l'utilisateur
            password: Mot de passe
            
        Returns:
            tuple: (success, message, user)
        """
        try:
            # Vérifier si l'utilisateur est bloqué
            if self.is_user_locked(email):
                return False, "Compte temporairement bloqué après trop de tentatives échouées", None
            
            # Authentifier l'utilisateur
            user = self.model.authenticate_user(email, password)
            
            if user:
                # Réinitialiser les tentatives échouées
                if email in self.failed_login_attempts:
                    del self.failed_login_attempts[email]
                
                return True, "Authentification réussie", user
            else:
                # Incrémenter les tentatives échouées
                self.record_failed_login(email)
                
                # Vérifier si l'utilisateur est maintenant bloqué
                if self.is_user_locked(email):
                    return False, f"Compte temporairement bloqué pour {self.lockout_duration_minutes} minutes", None
                
                # Utilisateur non authentifié
                return False, "Email ou mot de passe incorrect", None
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification: {e}")
            return False, f"Une erreur est survenue: {e}", None
    
    def record_failed_login(self, email):
        """
        Enregistre une tentative de connexion échouée
        
        Args:
            email: Email de l'utilisateur
        """
        now = datetime.now()
        
        if email not in self.failed_login_attempts:
            self.failed_login_attempts[email] = {'count': 1, 'last_attempt': now}
        else:
            self.failed_login_attempts[email]['count'] += 1
            self.failed_login_attempts[email]['last_attempt'] = now
    
    def is_user_locked(self, email):
        """
        Vérifie si un utilisateur est temporairement bloqué
        
        Args:
            email: Email de l'utilisateur
            
        Returns:
            bool: True si l'utilisateur est bloqué
        """
        if email not in self.failed_login_attempts:
            return False
        
        attempts = self.failed_login_attempts[email]
        
        # Vérifier si le nombre de tentatives dépasse le maximum
        if attempts['count'] < self.max_login_attempts:
            return False
        
        # Vérifier si la durée de blocage est écoulée
        lockout_until = attempts['last_attempt'] + timedelta(minutes=self.lockout_duration_minutes)
        if datetime.now() > lockout_until:
            # Réinitialiser si la durée est écoulée
            del self.failed_login_attempts[email]
            return False
        
        return True
    
    def change_password(self, user_id, current_password, new_password):
        """
        Change le mot de passe d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            current_password: Mot de passe actuel
            new_password: Nouveau mot de passe
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Récupérer l'utilisateur
            user = self.model.get_user_by_id(user_id)
            if not user:
                return False, "Utilisateur non trouvé"
            
            # Vérifier le mot de passe actuel
            if not self.model.verify_password(current_password, user.get('password', '')):
                return False, "Mot de passe actuel incorrect"
            
            # Valider le nouveau mot de passe
            if not self.validate_password(new_password):
                return False, self.get_password_requirements_message()
            
            # Mettre à jour le mot de passe
            user_data = user.copy()
            user_data['password'] = new_password
            
            success = self.model.update_user(user_data)
            
            if success:
                return True, "Mot de passe modifié avec succès"
            else:
                return False, "Erreur lors de la modification du mot de passe"
        except Exception as e:
            logger.error(f"Erreur lors du changement de mot de passe: {e}")
            return False, f"Une erreur est survenue: {e}"
    
    def reset_password(self, user_id):
        """
        Réinitialise le mot de passe d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            tuple: (success, message, new_password)
        """
        try:
            # Vérifier les permissions
            if self.permissions:
                self.permissions.check_permission('admin.users.edit')
            
            # Récupérer l'utilisateur
            user = self.get_user_by_id(user_id)
            if not user:
                return False, "Utilisateur non trouvé", None
            
            # Vérifier si l'utilisateur courant peut modifier cet utilisateur
            if not self.can_edit_user(user):
                return False, "Vous n'avez pas les droits pour modifier cet utilisateur", None
            
            # Générer un nouveau mot de passe
            new_password = self.generate_secure_password()
            
            # Mettre à jour l'utilisateur
            user_data = user.copy()
            user_data['password'] = new_password
            user_data['updated_at'] = datetime.now().isoformat()
            user_data['password_reset'] = True
            
            success = self.model.update_user(user_data)
            
            if success:
                # Journaliser l'action
                if self.admin_controller and hasattr(self.admin_controller, 'add_activity'):
                    self.admin_controller.add_activity(
                        "Réinitialisation de mot de passe",
                        f"ID: {user_id}, Email: {user.get('email')}"
                    )
                
                return True, "Mot de passe réinitialisé avec succès", new_password
            else:
                return False, "Erreur lors de la réinitialisation du mot de passe", None
        except PermissionDenied:
            return False, "Vous n'avez pas les permissions nécessaires pour réinitialiser un mot de passe", None
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation du mot de passe: {e}")
            return False, f"Une erreur est survenue: {e}", None
    
    def generate_secure_password(self, length=10):
        """
        Génère un mot de passe aléatoire sécurisé
        
        Args:
            length: Longueur du mot de passe
            
        Returns:
            str: Mot de passe généré
        """
        import random
        import string
        
        # Définir les ensembles de caractères
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        
        # S'assurer que le mot de passe contient au moins un caractère de chaque ensemble
        password = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
            random.choice(special)
        ]
        
        # Compléter avec des caractères aléatoires
        all_chars = lowercase + uppercase + digits + special
        password.extend(random.choice(all_chars) for _ in range(length - 4))
        
        # Mélanger le mot de passe
        random.shuffle(password)
        
        return ''.join(password)
    
    #-----------------------
    # Validation
    #-----------------------
    
    def validate_user_data(self, user_data, is_new=True, existing_user=None):
        """
        Valide les données d'un utilisateur
        
        Args:
            user_data: Données à valider
            is_new: Indique s'il s'agit d'un nouvel utilisateur
            existing_user: Utilisateur existant (pour mise à jour)
            
        Returns:
            tuple: (is_valid, message)
        """
        # Vérifier l'email
        if 'email' in user_data:
            if not user_data['email']:
                return False, "L'email est obligatoire"
            
            if not re.match(self.email_regex, user_data['email']):
                return False, "Format d'email invalide"
        elif is_new:
            return False, "L'email est obligatoire"
        
        # Vérifier le mot de passe pour les nouveaux utilisateurs
        if is_new and 'password' in user_data and user_data['password']:
            if not self.validate_password(user_data['password']):
                return False, self.get_password_requirements_message()
        
        # Vérifier le mot de passe pour les mises à jour
        if not is_new and 'password' in user_data and user_data['password']:
            if not self.validate_password(user_data['password']):
                return False, self.get_password_requirements_message()
        
        # Vérifier le rôle
        if 'role' in user_data:
            valid_roles = ['admin', 'manager', 'support', 'user']
            if user_data['role'] not in valid_roles:
                return False, f"Rôle invalide. Rôles valides: {', '.join(valid_roles)}"
        
        # Tout est valide
        return True, ""
    
    def validate_password(self, password):
        """
        Valide un mot de passe selon les critères de sécurité
        
        Args:
            password: Mot de passe à valider
            
        Returns:
            bool: True si le mot de passe est valide
        """
        # Vérifier la longueur
        if len(password) < self.password_min_length:
            return False
        
        # Vérifier la présence de caractères minuscules et majuscules
        if self.password_requires_mixed_case:
            if not any(c.islower() for c in password) or not any(c.isupper() for c in password):
                return False
        
        # Vérifier la présence de chiffres
        if self.password_requires_digit:
            if not any(c.isdigit() for c in password):
                return False
        
        # Vérifier la présence de caractères spéciaux
        if self.password_requires_special:
            special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
            if not any(c in special_chars for c in password):
                return False
        
        return True
    
    def get_password_requirements_message(self):
        """
        Récupère un message décrivant les exigences de mot de passe
        
        Returns:
            str: Message décrivant les exigences
        """
        requirements = [f"Au moins {self.password_min_length} caractères"]
        
        if self.password_requires_mixed_case:
            requirements.append("Des lettres minuscules et majuscules")
        
        if self.password_requires_digit:
            requirements.append("Au moins un chiffre")
        
        if self.password_requires_special:
            requirements.append("Au moins un caractère spécial (!@#$%^&*()_+-=[]{}|;:,.<>?)")
        
        return "Le mot de passe doit respecter les critères suivants: " + ", ".join(requirements)
    
    #-----------------------
    # Importation/Exportation
    #-----------------------
    
    @admin_required
    def import_users(self, file_path, options=None):
        """
        Importe des utilisateurs depuis un fichier CSV ou JSON
        
        Args:
            file_path: Chemin du fichier
            options: Options d'importation
            
        Returns:
            tuple: (success, message, stats)
        """
        try:
            # Vérifier les permissions
            if self.permissions:
                self.permissions.check_permission('admin.users.create')
            
            options = options or {}
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Statistiques d'importation
            stats = {
                'total': 0,
                'created': 0,
                'updated': 0,
                'failed': 0,
                'errors': []
            }
            
            # Gérer les différents formats
            if file_ext == '.json':
                result = self._import_users_json(file_path, options, stats)
            elif file_ext == '.csv':
                result = self._import_users_csv(file_path, options, stats)
            else:
                return False, f"Format de fichier non pris en charge: {file_ext}", stats
            
            if not result:
                return False, "Erreur lors de l'importation des utilisateurs", stats
            
            # Rafraîchir le cache
            self.get_users(force_refresh=True)
            
            # Journaliser l'action
            if self.admin_controller and hasattr(self.admin_controller, 'add_activity'):
                self.admin_controller.add_activity(
                    "Importation d'utilisateurs",
                    f"Fichier: {os.path.basename(file_path)}, "
                    f"Créés: {stats['created']}, Mis à jour: {stats['updated']}, Échecs: {stats['failed']}"
                )
            
            # Message de résultat
            message = (f"Importation terminée. "
                      f"Total: {stats['total']}, "
                      f"Créés: {stats['created']}, "
                      f"Mis à jour: {stats['updated']}, "
                      f"Échecs: {stats['failed']}")
            
            return True, message, stats
        except PermissionDenied:
            return False, "Vous n'avez pas les permissions nécessaires pour importer des utilisateurs", None
        except Exception as e:
            logger.error(f"Erreur lors de l'importation des utilisateurs: {e}")
            return False, f"Une erreur est survenue: {e}", None
    
    def _import_users_json(self, file_path, options, stats):
        """
        Importe des utilisateurs depuis un fichier JSON
        
        Args:
            file_path: Chemin du fichier
            options: Options d'importation
            stats: Statistiques d'importation à mettre à jour
            
        Returns:
            bool: True si l'importation a réussi
        """
        try:
            # Charger le fichier JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Vérifier que c'est une liste
            if not isinstance(data, list):
                stats['errors'].append("Format JSON invalide, liste attendue")
                return False
            
            stats['total'] = len(data)
            
            # Importer chaque utilisateur
            for user_data in data:
                try:
                    # Vérifier les champs requis
                    if "email" not in user_data:
                        stats['failed'] += 1
                        stats['errors'].append(f"Utilisateur sans email ignoré")
                        continue
                    
                    # Vérifier si l'utilisateur existe déjà
                    existing_user = self.get_user_by_email(user_data["email"])
                    if existing_user:
                        if options.get("update_existing", False):
                            # Mettre à jour l'utilisateur existant
                            user_data["id"] = existing_user["id"]
                            
                            # Préserver le mot de passe si non spécifié
                            if "password" not in user_data and "password" in existing_user:
                                user_data["password"] = existing_user["password"]
                            
                            # Mettre à jour
                            result, _ = self.update_user(user_data)
                            if result:
                                stats['updated'] += 1
                            else:
                                stats['failed'] += 1
                                stats['errors'].append(f"Erreur lors de la mise à jour de {user_data['email']}")
                        else:
                            stats['failed'] += 1
                            stats['errors'].append(f"Utilisateur existant ignoré: {user_data['email']}")
                    else:
                        # Créer un nouvel utilisateur
                        if "password" not in user_data:
                            user_data["password"] = self.generate_secure_password()
                        
                        # Si le rôle n'est pas spécifié, attribuer le rôle par défaut
                        if 'role' not in user_data:
                            user_data['role'] = 'user'
                        
                        # Vérifier si l'utilisateur a le droit d'attribuer ce rôle
                        if not self.can_manage_role(user_data.get('role')):
                            user_data['role'] = 'user'  # Rétrograder au rôle 'user' si pas les droits
                        
                        # Créer l'utilisateur
                        result, _, _ = self.create_user(user_data)
                        if result:
                            stats['created'] += 1
                        else:
                            stats['failed'] += 1
                            stats['errors'].append(f"Erreur lors de la création de {user_data['email']}")
                except Exception as e:
                    stats['failed'] += 1
                    stats['errors'].append(f"Erreur pour {user_data.get('email', 'utilisateur inconnu')}: {e}")
            
            return True
        except Exception as e:
            stats['errors'].append(f"Erreur lors de l'importation JSON: {e}")
            return False
    
    def _import_users_csv(self, file_path, options, stats):
        """
        Importe des utilisateurs depuis un fichier CSV
        
        Args:
            file_path: Chemin du fichier
            options: Options d'importation
            stats: Statistiques d'importation à mettre à jour
            
        Returns:
            bool: True si l'importation a réussi
        """
        try:
            users = []
            
            # Charger le fichier CSV
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                # Vérifier que la colonne 'email' est présente
                if 'email' not in reader.fieldnames:
                    stats['errors'].append("La colonne 'email' est obligatoire dans le fichier CSV")
                    return False
                
                # Lire toutes les lignes
                for row in reader:
                    users.append(row)
            
            stats['total'] = len(users)
            
            # Importer chaque utilisateur
            for user_data in users:
                try:
                    # Nettoyer les données (supprimer les espaces)
                    for key in user_data:
                        if isinstance(user_data[key], str):
                            user_data[key] = user_data[key].strip()
                    
                    # Vérifier que l'email est présent
                    if not user_data.get("email"):
                        stats['failed'] += 1
                        stats['errors'].append("Utilisateur sans email ignoré")
                        continue
                    
                    # Vérifier si l'utilisateur existe déjà
                    existing_user = self.get_user_by_email(user_data["email"])
                    if existing_user:
                        if options.get("update_existing", False):
                            # Mettre à jour l'utilisateur existant
                            user_data["id"] = existing_user["id"]
                            
                            # Préserver le mot de passe si non spécifié
                            if (not user_data.get("password") or user_data.get("password") == "") and "password" in existing_user:
                                user_data["password"] = existing_user["password"]
                            
                            # Convertir les valeurs booléennes
                            if "is_active" in user_data:
                                user_data["is_active"] = user_data["is_active"].lower() in ['true', 'yes', '1', 'oui']
                            
                            # Mettre à jour
                            result, _ = self.update_user(user_data)
                            if result:
                                stats['updated'] += 1
                            else:
                                stats['failed'] += 1
                                stats['errors'].append(f"Erreur lors de la mise à jour de {user_data['email']}")
                        else:
                            stats['failed'] += 1
                            stats['errors'].append(f"Utilisateur existant ignoré: {user_data['email']}")
                    else:
                        # Créer un nouvel utilisateur
                        if not user_data.get("password") or user_data.get("password") == "":
                            user_data["password"] = self.generate_secure_password()
                        
                        # Convertir les valeurs booléennes
                        if "is_active" in user_data:
                            user_data["is_active"] = user_data["is_active"].lower() in ['true', 'yes', '1', 'oui']
                        
                        # Si le rôle n'est pas spécifié, attribuer le rôle par défaut
                        if not user_data.get('role'):
                            user_data['role'] = 'user'
                        
                        # Vérifier si l'utilisateur a le droit d'attribuer ce rôle
                        if not self.can_manage_role(user_data.get('role')):
                            user_data['role'] = 'user'  # Rétrograder au rôle 'user' si pas les droits
                        
                        # Créer l'utilisateur
                        result, _, _ = self.create_user(user_data)
                        if result:
                            stats['created'] += 1
                        else:
                            stats['failed'] += 1
                            stats['errors'].append(f"Erreur lors de la création de {user_data['email']}")
                except Exception as e:
                    stats['failed'] += 1
                    stats['errors'].append(f"Erreur pour {user_data.get('email', 'utilisateur inconnu')}: {e}")
            
            return True
        except Exception as e:
            stats['errors'].append(f"Erreur lors de l'importation CSV: {e}")
            return False
    
    @manager_required
    def export_users(self, file_path, format='json', options=None):
        """
        Exporte les utilisateurs vers un fichier
        
        Args:
            file_path: Chemin du fichier de destination
            format: Format d'exportation ('json' ou 'csv')
            options: Options d'exportation
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Vérifier les permissions
            if self.permissions:
                self.permissions.check_permission('admin.users.view')
            
            options = options or {}
            
            # Récupérer les utilisateurs
            users = self.get_users(force_refresh=True)
            
            # Filtrer les utilisateurs si des critères sont spécifiés
            if 'role' in options:
                users = [u for u in users if u.get('role') == options['role']]
            
            if 'active_only' in options and options['active_only']:
                users = [u for u in users if u.get('is_active', True)]
            
            # Supprimer les mots de passe par sécurité, sauf si explicitement demandé
            if not options.get('include_passwords', False):
                for user in users:
                    if 'password' in user:
                        del user['password']
            
            # Exporter selon le format
            if format.lower() == 'json':
                result = self._export_users_json(file_path, users, options)
            elif format.lower() == 'csv':
                result = self._export_users_csv(file_path, users, options)
            else:
                return False, f"Format d'exportation non pris en charge: {format}"
            
            if not result:
                return False, "Erreur lors de l'exportation des utilisateurs"
            
            # Journaliser l'action
            if self.admin_controller and hasattr(self.admin_controller, 'add_activity'):
                self.admin_controller.add_activity(
                    "Exportation d'utilisateurs",
                    f"Fichier: {os.path.basename(file_path)}, Format: {format}, Nombre: {len(users)}"
                )
            
            return True, f"{len(users)} utilisateurs exportés vers {file_path}"
        except PermissionDenied:
            return False, "Vous n'avez pas les permissions nécessaires pour exporter des utilisateurs"
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation des utilisateurs: {e}")
            return False, f"Une erreur est survenue: {e}"
    
    def _export_users_json(self, file_path, users, options):
        """
        Exporte les utilisateurs vers un fichier JSON
        
        Args:
            file_path: Chemin du fichier
            users: Liste des utilisateurs à exporter
            options: Options d'exportation
            
        Returns:
            bool: True si l'exportation a réussi
        """
        try:
            # Créer le répertoire de destination si nécessaire
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Écrire le fichier JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2, default=str)
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation JSON: {e}")
            return False
    
    def _export_users_csv(self, file_path, users, options):
        """
        Exporte les utilisateurs vers un fichier CSV
        
        Args:
            file_path: Chemin du fichier
            users: Liste des utilisateurs à exporter
            options: Options d'exportation
            
        Returns:
            bool: True si l'exportation a réussi
        """
        try:
            # Créer le répertoire de destination si nécessaire
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Déterminer les champs à exporter
            fields = options.get('fields', [
                'id', 'email', 'first_name', 'last_name', 'role', 'is_active',
                'created_at', 'updated_at', 'last_login'
            ])
            
            # Écrire le fichier CSV
            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
                writer.writeheader()
                
                for user in users:
                    # Ne garder que les champs spécifiés
                    row = {field: user.get(field, '') for field in fields}
                    writer.writerow(row)
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation CSV: {e}")
            return False
    
    #-----------------------
    # Utilitaires
    #-----------------------
    
    def get_user_roles(self):
        """
        Récupère la liste des rôles disponibles
        
        Returns:
            list: Liste des rôles
        """
        return ['admin', 'manager', 'support', 'user']
    
    def get_user_activity(self, user_id, limit=50):
        """
        Récupère l'historique d'activité d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            limit: Nombre maximum d'activités à récupérer
            
        Returns:
            list: Liste des activités de l'utilisateur
        """
        try:
            # Vérifier si l'utilisateur existe
            user = self.get_user_by_id(user_id)
            if not user:
                return []
            
            # Récupérer les activités depuis le modèle
            if hasattr(self.model, 'get_recent_activities'):
                return self.model.get_recent_activities(user_id=user_id, limit=limit)
            
            # Si le modèle n'a pas cette méthode, retourner une liste vide
            return []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des activités de l'utilisateur: {e}")
            return []
    
    def get_user_stats(self, user_id):
        """
        Récupère des statistiques sur un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            dict: Statistiques de l'utilisateur
        """
        try:
            # Vérifier si l'utilisateur existe
            user = self.get_user_by_id(user_id)
            if not user:
                return {}
            
            # Récupérer les activités
            activities = self.get_user_activity(user_id, limit=1000)
            
            # Calculer des statistiques
            stats = {
                'activity_count': len(activities),
                'last_login': user.get('last_login'),
                'account_age': None,
                'active_days': 0,
                'documents_created': 0,
                'documents_edited': 0
            }
            
            # Calculer l'âge du compte
            if 'created_at' in user:
                created_at = datetime.fromisoformat(user['created_at']) if isinstance(user['created_at'], str) else user['created_at']
                stats['account_age'] = (datetime.now() - created_at).days
            
            # Calculer les jours actifs (jours uniques avec activité)
            active_days = set()
            for activity in activities:
                if 'timestamp' in activity:
                    timestamp = datetime.fromisoformat(activity['timestamp']) if isinstance(activity['timestamp'], str) else activity['timestamp']
                    active_days.add(timestamp.date().isoformat())
            
            stats['active_days'] = len(active_days)
            
            # Compter les documents créés/édités (à adapter selon votre modèle de données)
            for activity in activities:
                if activity.get('type') == 'document' and 'created' in activity.get('description', '').lower():
                    stats['documents_created'] += 1
                elif activity.get('type') == 'document' and 'edit' in activity.get('description', '').lower():
                    stats['documents_edited'] += 1
            
            return stats
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques de l'utilisateur: {e}")
            return {}
    
    def find_inactive_users(self, days=30):
        """
        Trouve les utilisateurs inactifs depuis un certain nombre de jours
        
        Args:
            days: Nombre de jours d'inactivité
            
        Returns:
            list: Liste des utilisateurs inactifs
        """
        try:
            inactive_users = []
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_date_str = cutoff_date.isoformat()
            
            for user in self.get_users():
                # Vérifier la dernière connexion
                last_login = user.get('last_login')
                if not last_login or last_login < cutoff_date_str:
                    inactive_users.append(user)
            
            return inactive_users
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des utilisateurs inactifs: {e}")
            return []
    
    def get_online_users(self, minutes=15):
        """
        Récupère les utilisateurs actuellement en ligne
        
        Args:
            minutes: Délai en minutes pour considérer un utilisateur comme en ligne
            
        Returns:
            list: Liste des utilisateurs en ligne
        """
        try:
            online_users = []
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            cutoff_time_str = cutoff_time.isoformat()
            
            for user in self.get_users():
                # Vérifier la dernière activité (si disponible)
                last_activity = user.get('last_activity') or user.get('last_login')
                if last_activity and last_activity > cutoff_time_str:
                    online_users.append(user)
            
            return online_users
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des utilisateurs en ligne: {e}")
            return []