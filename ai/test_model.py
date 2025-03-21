#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modèle d'IA simplifié pour tester l'interface de chat
"""

import time
import logging

logger = logging.getLogger("VynalDocsAutomator.TestModel")

class AIModel:
    """Version simplifiée du modèle AI pour les tests"""
    
    def __init__(self):
        """Initialise le modèle d'IA factice"""
        # Initialiser le logger
        self.logger = logging.getLogger("VynalDocsAutomator.TestModel")
        self.logger.info("Initialisation du modèle d'IA de test")
        
        # Initialiser la conversation
        self.conversation_history = []
        
        # Initialiser les états
        self.current_context = {
            "state": "initial",      # État initial de la conversation
            "last_action": None,     # Dernière action effectuée
            "subject": None,         # Sujet de la conversation
            "details": {}            # Détails pour le traitement
        }
    
    def generate_response(self, message):
        """
        Génère une réponse simulée
        
        Args:
            message (str): Le message de l'utilisateur
            
        Returns:
            str: La réponse générée
        """
        # Simulation d'un délai de traitement
        time.sleep(1)
        
        # Logging
        self.logger.info(f"Message reçu: {message}")
        
        # Traitement simple basé sur le contenu du message
        lower_message = message.lower()
        
        # Mise à jour de l'état selon le contenu du message
        if "document" in lower_message or "doc" in lower_message:
            if "créer" in lower_message or "creer" in lower_message or "nouveau" in lower_message:
                self.current_context["state"] = "asking_document_type"
                self.current_context["last_action"] = "demande_document"
                return """📌 Que souhaitez-vous faire ?

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document

Veuillez choisir une option en tapant 1 ou 2."""
            
            elif "modèle" in lower_message or "modele" in lower_message or "template" in lower_message:
                self.current_context["state"] = "choosing_category"
                self.current_context["last_action"] = "demande_modele"
                return """📋 Voici les catégories de modèles disponibles:

1. Contrats
2. Factures
3. Lettres
4. Rapports

Veuillez choisir une catégorie en tapant son numéro."""

        # Réponses selon l'état actuel
        if self.current_context["state"] == "asking_document_type":
            if message == "1":
                self.current_context["state"] = "choosing_category"
                return """📋 Voici les catégories de modèles disponibles:

1. Contrats
2. Factures
3. Lettres
4. Rapports

Veuillez choisir une catégorie en tapant son numéro."""
            elif message == "2":
                self.current_context["state"] = "new_document"
                return "📝 Veuillez décrire le type de document que vous souhaitez créer."
        
        elif self.current_context["state"] == "choosing_category":
            self.current_context["state"] = "choosing_model"
            return """📄 Voici les modèles disponibles dans cette catégorie:

1. Modèle standard
2. Modèle premium
3. Modèle personnalisé

Veuillez choisir un modèle en tapant son numéro."""
        
        elif self.current_context["state"] == "choosing_model":
            self.current_context["state"] = "filling_model"
            return "✅ Excellent choix! Je vais maintenant vous guider pour remplir ce modèle. Quel est votre nom complet?"
        
        elif self.current_context["state"] == "filling_model":
            self.current_context["details"]["nom"] = message
            self.current_context["state"] = "document_ready"
            return f"✅ Merci {message}! Votre document est prêt. Vous pouvez le télécharger en cliquant sur le bouton ci-dessous."
        
        elif self.current_context["state"] == "new_document":
            self.current_context["details"]["type"] = message
            self.current_context["state"] = "document_ready"
            return f"✅ J'ai créé un nouveau document de type '{message}'. Vous pouvez le télécharger en cliquant sur le bouton ci-dessous."
        
        # Réponse par défaut
        return "Comment puis-je vous aider avec vos documents aujourd'hui?" 