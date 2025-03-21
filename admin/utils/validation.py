#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitaires de validation pour l'administration
"""

import re
from typing import Tuple

def validate_email(email: str) -> Tuple[bool, str]:
    """
    Valide une adresse email
    
    Args:
        email: Adresse email à valider
        
    Returns:
        Tuple[bool, str]: (True si valide, message d'erreur si invalide)
    """
    # Vérifier que l'email n'est pas vide
    if not email:
        return False, "L'adresse email ne peut pas être vide"
    
    # Expression régulière pour la validation d'email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "Format d'adresse email invalide"
    
    return True, ""

def validate_password(password: str) -> Tuple[bool, str]:
    """
    Valide un mot de passe
    
    Args:
        password: Mot de passe à valider
        
    Returns:
        Tuple[bool, str]: (True si valide, message d'erreur si invalide)
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    
    if not re.search(r'[A-Z]', password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    
    if not re.search(r'[a-z]', password):
        return False, "Le mot de passe doit contenir au moins une minuscule"
    
    if not re.search(r'[0-9]', password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial"
    
    return True, "" 