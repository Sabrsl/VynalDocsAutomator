#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestion de la configuration pour l'administration
"""

import os
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger("VynalDocsAutomator.Admin.Config")

def get_smtp_config() -> Dict[str, any]:
    """
    Récupère la configuration SMTP depuis le fichier de configuration
    
    Returns:
        Dict[str, any]: Configuration SMTP
    """
    try:
        config_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'config',
            'smtp_config.json'
        )
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # Valider la configuration
                required_fields = ['host', 'port', 'user', 'password']
                for field in required_fields:
                    if field not in config:
                        raise ValueError(f"Champ requis manquant dans la configuration SMTP: {field}")
                
                return config
        else:
            # Configuration par défaut
            default_config = {
                'host': 'smtp.gmail.com',
                'port': 587,
                'user': 'no-reply@votre-domaine.com',
                'password': '',  # À configurer
                'use_tls': True
            }
            
            # Créer le fichier avec la configuration par défaut
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            
            logger.warning("Fichier de configuration SMTP créé avec des valeurs par défaut")
            return default_config
            
    except Exception as e:
        logger.error(f"Erreur lors de la lecture de la configuration SMTP: {e}")
        return {
            'host': 'smtp.gmail.com',
            'port': 587,
            'user': 'no-reply@votre-domaine.com',
            'password': '',
            'use_tls': True
        } 