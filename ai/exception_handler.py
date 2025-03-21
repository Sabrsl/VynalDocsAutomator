#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire d'exceptions pour le modèle d'IA
"""

import logging
import traceback
import sys
import functools

logger = logging.getLogger("VynalDocsAutomator.AIExceptionHandler")

def safe_ai_method(func):
    """
    Décorateur qui sécurise les méthodes du modèle d'IA contre les exceptions.
    
    Args:
        func: La fonction à sécuriser
        
    Returns:
        function: La fonction sécurisée qui ne lèvera pas d'exception
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            logger.error(f"Exception dans {func.__name__}: {e}")
            logger.error(traceback.format_exc())
            
            # Réinitialiser le contexte au besoin
            if hasattr(self, 'current_context'):
                # Préserver certaines informations si elles existent
                old_state = self.current_context.get('state', 'initial')
                
                # Réinitialiser le contexte
                self.current_context = {
                    "state": "error_recovery",
                    "last_action": "exception_handled",
                    "previous_state": old_state,
                    "subject": None,
                    "details": {},
                    "document_type": None,
                    "category": None,
                    "model": None
                }
            
            # Message d'erreur utilisateur convivial
            if 'document_type' in str(e):
                return """Je suis désolé, j'ai rencontré un problème avec la gestion de votre document.
                
Souhaitez-vous:
1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document"""
            elif 'KeyError' in str(e):
                return "Je suis désolé, j'ai perdu le fil de notre conversation. Comment puis-je vous aider ?"
            else:
                return "Je suis désolé, j'ai rencontré un problème. Pouvez-vous reformuler votre demande ?"
    
    return wrapper

def patch_with_exception_handling(cls):
    """
    Applique le gestionnaire d'exceptions à toutes les méthodes d'une classe.
    
    Args:
        cls: La classe à sécuriser
        
    Returns:
        class: La classe avec toutes ses méthodes sécurisées
    """
    # Ne pas modifier les méthodes spéciales (__init__, etc.)
    for name, method in cls.__dict__.items():
        if callable(method) and not name.startswith('__'):
            setattr(cls, name, safe_ai_method(method))
    
    return cls 