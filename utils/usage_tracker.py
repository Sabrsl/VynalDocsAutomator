#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire de suivi d'utilisation simplifié pour l'application Vynal Docs Automator
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger("VynalDocsAutomator.UsageTracker")

class UsageTracker:
    """Gestionnaire de suivi d'utilisation simplifié"""
    
    def __init__(self):
        """Initialise le gestionnaire de suivi"""
        self.data_dir = os.path.join("data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.usage_file = os.path.join(self.data_dir, "usage_count.json")
        self.usage_count = self._load_usage_count()
        
        # Limites d'utilisation
        self.max_uses = 10  # Nombre maximum d'utilisations avant demande d'inscription
        
        # Fonctionnalités nécessitant une inscription
        self.protected_features = {
            "password_protection": True,    # Protection par mot de passe
            "template_editing": True,       # Modification de modèles
            "template_deletion": True,      # Suppression de modèles
            "export_pdf": False,           # Export PDF (libre)
            "create_document": False       # Création de documents (libre)
        }
    
    def _load_usage_count(self) -> int:
        """Charge le compteur d'utilisation"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    return data.get("count", 0)
            return 0
        except Exception as e:
            logger.error(f"Erreur lors du chargement du compteur: {e}")
            return 0
    
    def _save_usage_count(self):
        """Sauvegarde le compteur d'utilisation"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump({"count": self.usage_count}, f)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du compteur: {e}")
    
    def increment_usage(self) -> Dict[str, Any]:
        """
        Incrémente le compteur d'utilisation
        
        Returns:
            Dict contenant les informations sur l'utilisation
        """
        self.usage_count += 1
        self._save_usage_count()
        
        remaining = max(0, self.max_uses - self.usage_count)
        should_register = self.usage_count >= self.max_uses
        
        return {
            "count": self.usage_count,
            "remaining": remaining,
            "should_register": should_register,
            "message": f"Il vous reste {remaining} utilisation{'s' if remaining > 1 else ''} avant de devoir vous inscrire."
        }
    
    def needs_registration(self, feature: str = None) -> Dict[str, Any]:
        """
        Vérifie si l'inscription est nécessaire
        
        Args:
            feature: Nom de la fonctionnalité à vérifier (optionnel)
        
        Returns:
            Dict contenant les informations sur la nécessité de s'inscrire
        """
        # Si une fonctionnalité spécifique est vérifiée
        if feature and self.is_protected_feature(feature):
            return {
                "needs_registration": True,
                "reason": "protected_feature",
                "message": "Cette fonctionnalité nécessite un compte utilisateur."
            }
        
        # Vérification basée sur le nombre d'utilisations
        if self.usage_count >= self.max_uses:
            return {
                "needs_registration": True,
                "reason": "usage_limit",
                "message": "Vous avez atteint le nombre maximum d'utilisations. Veuillez vous inscrire pour continuer."
            }
        
        return {
            "needs_registration": False,
            "reason": None,
            "message": None
        }
    
    def is_protected_feature(self, feature: str) -> bool:
        """
        Vérifie si une fonctionnalité nécessite une inscription
        
        Args:
            feature: Nom de la fonctionnalité à vérifier
        
        Returns:
            bool: True si la fonctionnalité nécessite une inscription, False sinon
        """
        return self.protected_features.get(feature, False)
    
    def reset_usage(self):
        """Réinitialise le compteur d'utilisation"""
        self.usage_count = 0
        self._save_usage_count()
    
    def is_user_registered(self) -> bool:
        """
        Vérifie si un utilisateur est inscrit
        
        Returns:
            bool: True si au moins un utilisateur est inscrit, False sinon
        """
        try:
            # D'abord, vérifier s'il y a un utilisateur actif
            current_user_file = os.path.join(self.data_dir, "current_user.json")
            if os.path.exists(current_user_file):
                try:
                    with open(current_user_file, 'r', encoding='utf-8') as f:
                        current_user = json.load(f)
                        if current_user.get("email"):
                            # Vérifier que cet utilisateur existe toujours
                            users_file = os.path.join(self.data_dir, "users.json")
                            if os.path.exists(users_file):
                                with open(users_file, 'r', encoding='utf-8') as f2:
                                    users = json.load(f2)
                                    if current_user.get("email") in users:
                                        return True
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture de l'utilisateur actif: {e}")
            
            # Sinon, vérifier s'il y a des utilisateurs enregistrés
            users_file = os.path.join(self.data_dir, "users.json")
            if os.path.exists(users_file):
                with open(users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                    return bool(users)  # True si le dictionnaire n'est pas vide
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des utilisateurs: {e}")
            return False

    def get_user_data(self) -> Dict[str, Any]:
        """
        Récupère les données de l'utilisateur actuellement connecté
        
        Returns:
            Dict: Données de l'utilisateur ou un dictionnaire vide si aucun utilisateur n'est connecté
        """
        try:
            # D'abord, vérifier s'il y a un utilisateur actif
            current_user_file = os.path.join(self.data_dir, "current_user.json")
            if os.path.exists(current_user_file):
                try:
                    with open(current_user_file, 'r', encoding='utf-8') as f:
                        current_user = json.load(f)
                        if current_user.get("email"):
                            # Vérifier que cet utilisateur existe toujours
                            users_file = os.path.join(self.data_dir, "users.json")
                            if os.path.exists(users_file):
                                with open(users_file, 'r', encoding='utf-8') as f2:
                                    users = json.load(f2)
                                    if current_user.get("email") in users:
                                        # Ajouter l'email aux données utilisateur
                                        user_data = users[current_user.get("email")]
                                        user_data["email"] = current_user.get("email")
                                        return user_data
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture de l'utilisateur actif: {e}")
            
            # Sinon, vérifier s'il y a des utilisateurs enregistrés et prendre le premier
            users_file = os.path.join(self.data_dir, "users.json")
            if os.path.exists(users_file):
                with open(users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                    
                    # S'il y a au moins un utilisateur, retourner le premier
                    if users:
                        first_email = next(iter(users))
                        user_data = users[first_email]
                        # Ajouter l'email dans les données utilisateur
                        user_data["email"] = first_email
                        
                        # Enregistrer cet utilisateur comme utilisateur actif
                        self.set_current_user(user_data)
                        
                        return user_data
            
            # Aucun utilisateur trouvé
            return {}
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données utilisateur: {e}")
            return {}
    
    def set_current_user(self, user_data: Dict[str, Any]) -> bool:
        """
        Définit l'utilisateur actuellement connecté
        
        Args:
            user_data: Données de l'utilisateur
        
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            current_user_file = os.path.join(self.data_dir, "current_user.json")
            
            # Créer un dictionnaire avec juste les informations nécessaires
            current_user = {
                "email": user_data.get("email"),
                "last_login": datetime.now().isoformat()
            }
            
            # Écrire dans un fichier temporaire d'abord
            temp_file = f"{current_user_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(current_user, f, indent=4)
            
            # Remplacer le fichier original par le temporaire
            if os.path.exists(current_user_file):
                os.replace(temp_file, current_user_file)
            else:
                os.rename(temp_file, current_user_file)
            
            logger.info(f"Utilisateur actif défini: {user_data.get('email')}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la définition de l'utilisateur actif: {e}")
            return False
    
    def clear_current_user(self) -> bool:
        """
        Supprime l'utilisateur actuellement connecté
        
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        try:
            current_user_file = os.path.join(self.data_dir, "current_user.json")
            if os.path.exists(current_user_file):
                os.remove(current_user_file)
                logger.info("Utilisateur actif supprimé")
                return True
            return True  # Aucun utilisateur à supprimer
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'utilisateur actif: {e}")
            return False
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authentifie un utilisateur avec son email et son mot de passe
        
        Args:
            email: Email de l'utilisateur
            password: Mot de passe hashé de l'utilisateur
            
        Returns:
            Dict: Données de l'utilisateur si l'authentification réussit, sinon un dictionnaire vide
        """
        try:
            # Vérifier que l'email et le mot de passe sont fournis
            if not email or not password:
                logger.error("Email ou mot de passe manquant")
                return {}
                
            # Récupérer les utilisateurs
            users_file = os.path.join(self.data_dir, "users.json")
            if not os.path.exists(users_file):
                logger.error("Fichier utilisateurs non trouvé")
                return {}
                
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
                
            # Vérifier si l'utilisateur existe
            if email not in users:
                logger.warning(f"Utilisateur {email} non trouvé")
                return {}
                
            # Vérifier le mot de passe
            user_data = users[email]
            if user_data.get("password") != password:
                logger.warning(f"Mot de passe incorrect pour {email}")
                return {}
                
            # Authentification réussie
            logger.info(f"Authentification réussie pour {email}")
            
            # Ajouter l'email aux données utilisateur
            user_data["email"] = email
            
            # Enregistrer l'utilisateur comme utilisateur actif
            self.set_current_user(user_data)
            
            return user_data
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification: {e}")
            return {} 