#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitaires de sécurité pour l'administration
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Dict, Optional

logger = logging.getLogger("VynalDocsAutomator.Admin.Security")

def send_secure_email(
    to_email: str,
    subject: str,
    body: str,
    smtp_config: Dict[str, any],
    from_name: Optional[str] = None
) -> bool:
    """
    Envoie un email de manière sécurisée
    
    Args:
        to_email: Adresse email du destinataire
        subject: Sujet de l'email
        body: Corps de l'email
        smtp_config: Configuration SMTP
        from_name: Nom de l'expéditeur (optionnel)
        
    Returns:
        bool: True si l'envoi a réussi, False sinon
    """
    try:
        msg = MIMEMultipart()
        
        # Configuration de l'email
        if from_name:
            msg['From'] = f"{from_name} <{smtp_config['user']}>"
        else:
            msg['From'] = smtp_config['user']
            
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Corps du message
        msg.attach(MIMEText(body, 'plain'))
        
        # Connexion sécurisée au serveur SMTP
        with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
            if smtp_config.get('use_tls', True):
                server.starttls()
            
            server.login(smtp_config['user'], smtp_config['password'])
            server.send_message(msg)
        
        logger.info(f"Email envoyé avec succès à {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email à {to_email}: {e}")
        return False 