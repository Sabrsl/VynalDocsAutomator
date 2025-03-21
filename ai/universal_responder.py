#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'amélioration de la réponse pour permettre une interaction plus naturelle
avec l'utilisateur dans tous les contextes.
"""

import logging
import re
import os
import traceback
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger("VynalDocsAutomator.UniversalResponder")

class UniversalResponder:
    """
    Classe qui augmente les capacités de réponse de l'IA en détectant
    et répondant aux entrées utilisateur de manière plus naturelle.
    """
    
    def __init__(self):
        """Initialise le répondeur universel"""
        # Patterns pour différents types d'entrées utilisateur
        self.patterns = {
            "greeting": [
                r'\bbonjour\b', r'\bsalut\b', r'\bhello\b', r'\bhey\b', r'\bhi\b',
                r'\bcava\b', r'\bça va\b', r'\bcomment vas[ -]tu\b', r'\bcomment allez[ -]vous\b',
                r'\bcomment ça va\b', r'\bcomment cv\b', r'\bcv\b', r'^cv$'
            ],
            "thanks": [
                r'\bmerci\b', r'\bthanks\b', r'\bthank\b', r'\bthx\b', r'\bty\b',
                r'\bje te remercie\b', r'\bje vous remercie\b'
            ],
            "goodbye": [
                r'\bau revoir\b', r'\badieu\b', r'\bciao\b', r'\bbye\b', r'\bgoodbye\b',
                r'\bà bientôt\b', r'\bà plus\b', r'\bà \+\b'
            ],
            "help": [
                r'\baide[-\s]moi\b', r'\baide\b', r'\bhelp\b', r'\bbesoin d\'aide\b',
                r'\bcomment [çc]a marche\b', r'\bcomment faire\b', r'\bque peux[-\s]tu faire\b'
            ],
            "affirmation": [
                r'\boui\b', r'\bouais\b', r'\byes\b', r'\byep\b', r'\bd\'accord\b',
                r'\bok\b', r'\bbien sûr\b', r'\bsûr\b', r'\bj\'accepte\b', r'\bvolontiers\b'
            ],
            "negation": [
                r'\bnon\b', r'\bnope\b', r'\bno\b', r'\bpas\b', r'\bpas d\'accord\b',
                r'\bje refuse\b', r'\bje ne veux pas\b', r'\bpassons\b'
            ],
            "confusion": [
                r'\bje ne comprends pas\b', r'\bc\'est confus\b', r'\bc\'est flou\b',
                r'\bje suis perdu\b', r'\bc\'est compliqué\b', r'\bqu\'est-ce que [çc]a veut dire\b'
            ],
            # Nouvelles intentions
            "question_about_you": [
                r'\bqui es[-\s]tu\b', r'\bc\'est quoi ton nom\b', r'\bcomment t\'appelles[-\s]tu\b',
                r'\btu es qui\b', r'\btu fais quoi\b', r'\btu sers à quoi\b', r'\bque fais[-\s]tu\b',
                r'\bc\'est quoi ton but\b', r'\bquel est ton rôle\b'
            ],
            "small_talk": [
                r'\btu aimes\b', r'\btu préfères\b', r'\btu peux\b', r'\btu sais\b',
                r'\bc\'est cool\b', r'\bc\'est génial\b', r'\bc\'est super\b', r'\bc\'est bien\b',
                r'\bje suis content\b', r'\bje suis heureux\b', r'\bje suis satisfait\b',
                r'\btu connais\b', r'\bquelle heure\b', r'\bquel jour\b', r'\bquel temps\b'
            ],
            "compliment": [
                r'\btu es génial\b', r'\btu es super\b', r'\btu es intelligent\b', r'\btu es efficace\b',
                r'\bmerci pour ton aide\b', r'\btu m\'aides beaucoup\b', r'\btu es utile\b',
                r'\bc\'est pratique\b', r'\bc\'est rapide\b', r'\bc\'est parfait\b'
            ],
            "frustration": [
                r'\bc\'est long\b', r'\bc\'est lent\b', r'\bc\'est compliqué\b', r'\bc\'est difficile\b',
                r'\bje n\'arrive pas\b', r'\bc\'est pénible\b', r'\bc\'est ennuyeux\b',
                r'\bça ne marche pas\b', r'\bça fonctionne pas\b', r'\bc\'est impossible\b',
                r'\bpfffff\b', r'\bpfff\b', r'\bpff\b', r'\bargh\b', r'\braaah\b'
            ],
            "question_générale": [
                r'\bpourquoi\b', r'\bcomment\b', r'\bquand\b', r'\boù\b', r'\bqui\b', r'\bquoi\b',
                r'\bquel\b', r'\bquelle\b', r'\bcombien\b', r'\bà quoi\b', r'\best-ce que\b',
                r'\bqu\'est-ce\b', r'\btu penses\b', r'\btu crois\b', r'\bton avis\b',
                r'\bpenses-tu\b', r'\bcrois-tu\b'
            ],
            "demande_avis": [
                r'\bque penses[-\s]tu\b', r'\bquel est ton avis\b', r'\bqu\'en penses[-\s]tu\b',
                r'\bcomment trouves[-\s]tu\b', r'\best-ce bien\b', r'\best-ce bon\b',
                r'\best-ce correct\b', r'\bton opinion\b', r'\bton conseil\b'
            ]
        }
    
    def detect_intent(self, message: str) -> Tuple[str, float]:
        """
        Détecte l'intention de l'utilisateur dans le message.
        
        Args:
            message (str): Le message de l'utilisateur
            
        Returns:
            Tuple[str, float]: L'intention détectée et sa probabilité
        """
        # Normaliser le message
        message = message.lower().strip()
        
        # Détecter les intentions
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    return intent, 0.9  # Haute probabilité si match direct
        
        return "unknown", 0.0
    
    def should_intercept(self, message: str, context: Dict[str, Any]) -> bool:
        """
        Détermine si le message devrait être intercepté et traité différemment.
        
        Args:
            message (str): Le message de l'utilisateur
            context (Dict[str, Any]): Le contexte actuel de la conversation
            
        Returns:
            bool: True si le message devrait être intercepté
        """
        intent, confidence = self.detect_intent(message)
        
        # Vérifier d'abord les intentions liées à une demande d'avis ou question générale
        if intent in ["demande_avis", "question_générale", "frustration"]:
            current_state = context.get("state", "initial")
            if current_state not in ["initial", "greeting"]:
                return True
        
        # Intentions à toujours intercepter, quelle que soit l'étape du processus
        always_intercept = ["thanks", "goodbye", "help", "confusion", 
                           "question_about_you", "compliment"]
        if intent in always_intercept and confidence > 0.7:
            return True
            
        # Intentions à intercepter uniquement si on est dans un processus de document
        current_state = context.get("state", "initial")
        if current_state not in ["initial", "greeting"]:
            # En plein processus, intercepter les digressions
            process_intercept = ["greeting", "small_talk"]
            if intent in process_intercept and confidence > 0.7:
                return True
        
        # Cas spécial: question courte non liée au processus
        if len(message.split()) <= 3 and intent == "random_question":
            return True
            
        return False
    
    def _ensure_response_consistency(self, response: str, context: Dict[str, Any]) -> str:
        """
        Assure la cohérence des réponses en fonction du contexte.
        
        Args:
            response (str): La réponse générée
            context (Dict[str, Any]): Le contexte actuel
            
        Returns:
            str: La réponse corrigée si nécessaire
        """
        current_state = context.get("state", "initial")
        
        # Si on est dans un état spécifique, s'assurer que la réponse est cohérente
        if current_state == "document_creation":
            if not any(doc_type in response.lower() for doc_type in self.patterns.keys()):
                response = self._handle_document_creation()
        elif current_state == "template_selection":
            if not any(word in response.lower() for word in ["modèle", "template", "exemple"]):
                response = self._handle_template_selection()
                
        # Ajouter un rappel si nécessaire
        if current_state not in ["initial", "greeting"]:
            reminder = self._get_contextual_reminder(current_state)
            if reminder and reminder not in response:
                response = f"{response}\n\n{reminder}"
                
        return response

    def _handle_document_creation(self) -> str:
        """Gère la création d'un nouveau document"""
        return ("Très bien ! Quel type de document souhaitez-vous créer ?\n\n"
                "📝 Contrat\n"
                "💰 Facture\n"
                "📊 Proposition\n"
                "📈 Rapport\n"
                "✉️ Lettre\n"
                "🔖 Attestation\n"
                "📄 Autre")
                
    def _handle_template_selection(self) -> str:
        """Gère la sélection d'un modèle"""
        return ("Voici les modèles disponibles :\n\n"
                "📝 Modèles de contrats\n"
                "💰 Modèles de factures\n"
                "📊 Modèles de propositions\n"
                "📈 Modèles de rapports\n"
                "✉️ Modèles de lettres\n"
                "🔖 Modèles d'attestations\n\n"
                "Quel type de modèle vous intéresse ?")

    def get_response(self, message: str, context: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Génère une réponse appropriée au message si nécessaire.
        
        Args:
            message (str): Le message de l'utilisateur
            context (Dict[str, Any]): Le contexte actuel de la conversation
            
        Returns:
            Optional[Tuple[str, Dict[str, Any]]]: La réponse et le contexte mis à jour, ou None
        """
        try:
            intent, confidence = self.detect_intent(message)
            current_state = context.get("state", "initial")
            
            # Vérifier si le message devrait être intercepté
            if self.should_intercept(message, context):
                # Obtenir la réponse de base
                response, new_context = self._get_base_response(message, intent, context)
                
                # Assurer la cohérence de la réponse
                if response:
                    response = self._ensure_response_consistency(response, new_context)
                
                return response, new_context
            
            # Si le message ne doit pas être intercepté, retourner None
            return None, context
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse: {e}")
            return self.get_error_message(), context

    def _get_base_response(self, message: str, intent: str, context: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Obtient la réponse de base en fonction de l'intention.
        
        Args:
            message (str): Le message de l'utilisateur
            intent (str): L'intention détectée
            context (Dict[str, Any]): Le contexte actuel
            
        Returns:
            Tuple[Optional[str], Dict[str, Any]]: La réponse et le contexte mis à jour
        """
        current_state = context.get("state", "initial")
        
        # Copier le contexte pour ne pas le modifier directement
        new_context = context.copy()
        
        # Traiter les intentions spéciales
        if intent in ["greeting", "thanks", "goodbye", "help", "confusion"]:
            return self._handle_special_intent(intent, new_context)
            
        # Traiter les questions pendant le processus
        if intent in ["question_générale", "demande_avis"] and current_state not in ["initial", "greeting"]:
            return self._handle_question(message, intent, new_context)
            
        # Traiter les demandes de document
        if any(word in message.lower() for word in ["document", "contrat", "modèle"]):
            return self._handle_document_request(message, new_context)
            
        # Par défaut, laisser le modèle principal gérer la réponse
        return None, new_context

    def _handle_special_intent(self, intent: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Gère les intentions spéciales comme les salutations et les remerciements.
        
        Args:
            intent (str): L'intention détectée
            context (Dict[str, Any]): Le contexte actuel
            
        Returns:
            Tuple[str, Dict[str, Any]]: La réponse et le contexte mis à jour
        """
        # Définir des réponses pour les intentions spéciales
        responses = {
            "greeting": [
                "Bonjour ! Je suis là pour vous aider avec vos documents. Que puis-je faire pour vous ?",
                "Bonjour ! Comment puis-je vous aider aujourd'hui ?",
                "Bonjour ! Je suis votre assistant de documents. Que souhaitez-vous faire ?"
            ],
            "thanks": [
                "Je vous en prie !",
                "C'est avec plaisir !",
                "Pas de problème, je suis là pour vous aider."
            ],
            "goodbye": [
                "Au revoir ! N'hésitez pas à revenir si vous avez besoin d'aide.",
                "À bientôt ! Je reste disponible pour vos futures demandes.",
                "Au revoir et bonne journée !"
            ],
            "help": [
                "Je peux vous aider à créer différents types de documents. Voici ce que je peux faire :\n\n"
                "📄 Créer un nouveau document\n"
                "- Utiliser un modèle existant\n"
                "- Remplir des modèles avec vos informations\n\n"
                "Pour commencer, dites-moi simplement ce que vous souhaitez.",
                "Besoin d'aide ? Je peux vous accompagner pour :\n\n"
                "- Créer un nouveau document\n"
                "- Utiliser un modèle existant\n"
                "- Remplir des modèles avec vos informations\n\n"
                "Dites-moi simplement ce que vous voulez faire."
            ],
            "confusion": [
                "Pas de problème, je vais essayer d'être plus clair. Que souhaitez-vous faire ?\n\n"
                "1. Créer un document\n"
                "2. Utiliser un modèle\n"
                "3. Autre chose",
                "Je comprends votre confusion. Pour simplifier, dites-moi si vous voulez :\n\n"
                "1. Créer un document\n"
                "2. Utiliser un modèle existant\n"
                "3. Autre chose"
            ]
        }
        
        # Mettre à jour le contexte
        # Pour les salutations, passer à l'état "greeting"
        if intent == "greeting":
            context["state"] = "greeting" if context["state"] == "initial" else context["state"]
            context["last_action"] = "greeting"
        
        # Pour les autres intentions, ne pas modifier l'état
        # mais mettre à jour la dernière action
        else:
            context["last_action"] = intent
        
        # Sélectionner une réponse aléatoire pour l'intention
        import random
        response = random.choice(responses.get(intent, ["Je suis désolé, je ne comprends pas."]))
        
        return response, context

    def get_error_message(self) -> str:
        """Retourne un message d'erreur standard"""
        return """Je suis désolé, mais j'ai rencontré un problème. Essayons de nouveau.

Vous pouvez dire "Je veux un document" pour commencer ou me poser une question."""
    
    def _get_contextual_reminder(self, current_state):
        """
        Génère un rappel contextuel basé sur l'état actuel.
        
        Args:
            current_state (str): L'état actuel de la conversation
            
        Returns:
            str: Le rappel contextuel
        """
        if current_state == "choosing_category":
            return "Pour continuer, veuillez choisir une catégorie de document parmi celles proposées."
        elif current_state == "choosing_model":
            return "Pour continuer, veuillez sélectionner un modèle de document parmi ceux proposés."
        elif current_state == "model_selected":
            return "Pour continuer, veuillez choisir une action à effectuer sur le document sélectionné."
        else:
            return "Maintenant, revenons à votre document."
            
    def _verify_llama_availability(self):
        """
        Vérifie si Llama est disponible et fonctionnel.
        """
        try:
            import requests
            url = "http://localhost:11434/api/version"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de Llama: {e}")
            return False

    def _get_llama_response(self, message: str) -> str:
        """
        Obtient une réponse de Llama pour les questions générales et complexes.
        """
        # Vérifier d'abord si Llama est disponible
        if not self._verify_llama_availability():
            logger.warning("Llama n'est pas disponible, utilisation du comportement standard")
            return None
            
        try:
            import requests
            import json
            
            # Configuration de la requête Llama
            url = "http://localhost:11434/api/generate"
            
            # Construire le prompt avec le contexte approprié
            prompt = f"""Tu es un assistant professionnel et amical. 
            Réponds à cette demande de manière claire et détaillée : {message}
            
            Important:
            - Reste professionnel et courtois
            - Donne des explications claires et concises
            - Si tu n'es pas sûr, dis-le honnêtement
            - N'invente pas d'informations
            """
            
            # Paramètres de la requête
            data = {
                "model": "llama2",
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            # Envoyer la requête avec timeout
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                # Traiter la réponse
                response_data = response.json()
                if "response" in response_data:
                    return response_data["response"].strip()
            
            raise Exception(f"Erreur de réponse Llama: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à Llama: {e}")
            return None

    def apply_to_ai_model(self, AIModel):
        """
        Applique le répondeur universel au modèle d'IA.
        
        Args:
            AIModel (class): La classe du modèle d'IA
            
        Returns:
            class: La classe modifiée
        """
        # Sauvegarde des méthodes originales
        original_generate_response = AIModel.generate_response
        responder = self
        
        def enhanced_generate_response(self, message, stream=False):
            """
            Version améliorée de generate_response qui utilise le répondeur universel
            et fait appel à Llama pour les questions générales.
            """
            try:
                # Si le message est vide
                if not message or len(message.strip()) == 0:
                    return "Je ne peux pas traiter un message vide. Veuillez me dire ce que vous souhaitez faire."
                
                # Normalisation du message
                normalized_message = message.lower().strip()
                print(f"DEBUG - Message reçu: '{message}'")
                print(f"DEBUG - État actuel: '{self.current_context.get('state', 'initial')}'")
                
                # Obtenir l'état actuel
                current_state = self.current_context.get("state", "initial")
                
                # Si nous sommes dans un état de traitement de document, utiliser la logique standard
                document_states = ["asking_document_type", "choosing_category", "choosing_model", 
                                 "model_selected", "filling_document"]
                if current_state in document_states:
                    return original_generate_response(self, message, stream)
                
                # Patterns pour détecter les demandes liées aux documents
                document_patterns = [
                    r'(?:je\s+(?:veux|voudrais|souhaite|aimerais)\s+)?(?:un\s+)?document',
                    r'créer\s+(?:un\s+)?document',
                    r'nouveau\s+document',
                    r'modèle\s+de\s+document',
                    r'template',
                    r'formulaire',
                    r'contrat',
                    r'facture'
                ]
                
                # Si le message correspond à une demande de document
                if any(re.search(pattern, normalized_message) for pattern in document_patterns):
                    return self._handle_document_request(message)
                
                # Pour les autres cas, vérifier si c'est une demande complexe ou générale
                complex_patterns = [
                    r'pourquoi',
                    r'comment',
                    r'explique',
                    r'analyse',
                    r'compare',
                    r'différence',
                    r'meilleur',
                    r'conseil',
                    r'avis',
                    r'pense[sz]',
                    r'suggestion'
                ]
                
                # Si c'est une demande complexe ou générale, utiliser Llama
                if any(re.search(pattern, normalized_message) for pattern in complex_patterns):
                    print("DEBUG - Utilisation de Llama pour une demande complexe/générale")
                    llama_response = self._get_llama_response(message)
                    if llama_response:
                        return llama_response
                    else:
                        print("DEBUG - Llama non disponible, utilisation du comportement standard")
                
                # Pour tout autre cas, utiliser la réponse standard
                return original_generate_response(self, message, stream)
                
            except Exception as e:
                logger.error(f"Erreur dans enhanced_generate_response: {e}")
                print(f"DEBUG - Exception dans enhanced_generate_response: {e}")
                return original_generate_response(self, message, stream)

        def _similarity_score(self, str1, str2):
            """
            Calcule un score de similarité entre deux chaînes.
            """
            # Normaliser les chaînes
            str1 = str1.lower().strip()
            str2 = str2.lower().strip()
            
            # Si une chaîne est vide, retourner 0
            if not str1 or not str2:
                return 0
            
            # Si les chaînes sont identiques, retourner 1
            if str1 == str2:
                return 1
            
            # Si une chaîne est contenue dans l'autre
            if str1 in str2:
                return len(str1) / len(str2)
            if str2 in str1:
                return len(str2) / len(str1)
            
            # Calculer la distance de Levenshtein
            try:
                import Levenshtein
                distance = Levenshtein.distance(str1, str2)
                max_len = max(len(str1), len(str2))
                return 1 - (distance / max_len)
            except ImportError:
                # Fallback si Levenshtein n'est pas disponible
                # Compter les caractères communs
                common = sum(1 for c in str1 if c in str2)
                return common / max(len(str1), len(str2))

        # Remplacer la méthode originale
        AIModel.generate_response = enhanced_generate_response
        
        return AIModel

    def _transfer_to_main_model(self, context: Dict[str, Any], message: str) -> Tuple[None, Dict[str, Any]]:
        """
        Transfère le contrôle au modèle principal en mettant à jour le contexte approprié.
        
        Args:
            context (Dict[str, Any]): Le contexte actuel
            message (str): Le message de l'utilisateur
            
        Returns:
            Tuple[None, Dict[str, Any]]: None et le contexte mis à jour
        """
        # Préparer le nouveau contexte
        new_context = context.copy()
        
        # Sauvegarder l'état de UniversalResponder pour le modèle principal
        new_context["universal_responder_state"] = {
            "state": context.get("state"),
            "document_type": context.get("document_type"),
            "category": context.get("category"),
            "model": context.get("model"),
            "details": context.get("details", {})
        }
        
        # Transférer l'état au modèle principal
        current_state = context.get("state")
        
        # Pour un document sélectionné à partir d'un modèle
        if current_state == "model_ready":
            new_context["state"] = "model_selected"
            new_context["last_action"] = "model_selection"
            new_context["category"] = context.get("category")
            # Ne pas définir model_ready ici pour éviter la confusion avec l'état du modèle principal
        
        # Pour un nouveau document créé
        elif current_state == "document_ready":
            new_context["state"] = "document_creation"
            new_context["last_action"] = "document_creation"
            new_context["document_type"] = context.get("document_type")
            # Conserver les détails pour le modèle principal
            if "details" in context and isinstance(context["details"], dict):
                for key, value in context["details"].items():
                    new_context[key] = value
        
        # Logger le transfert
        logger.info(f"Transfert au modèle principal: {current_state} -> {new_context['state']}")
        
        return None, new_context 

    def _handle_document_request(self, message: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Gère une demande de document de manière intelligente.
        
        Args:
            message (str): Le message de l'utilisateur
            context (Dict[str, Any]): Le contexte actuel
            
        Returns:
            Tuple[str, Dict[str, Any]]: La réponse et le contexte mis à jour
        """
        # Normaliser le message
        normalized_message = message.lower().strip()
        
        # Mettre à jour le contexte
        new_context = context.copy()
        new_context["state"] = "asking_document_type"
        new_context["last_action"] = "demande_document"
        
        # Détecter si l'utilisateur a déjà exprimé une préférence dans sa demande
        create_patterns = [
            r'(?:je\s+(?:veux|voudrais|souhaite|aimerais)\s+)?créer\s+(?:un\s+)?(?:nouveau\s+)?document',
            r'nouveau\s+document',
            r'faire\s+un\s+(?:nouveau\s+)?document',
            r'rédiger\s+(?:un\s+)?document',
            r'écrire\s+(?:un\s+)?document'
        ]
        
        use_patterns = [
            r'utiliser\s+(?:un\s+)?(?:modèle|template|exemple)',
            r'modèle\s+existant',
            r'template\s+existant',
            r'voir\s+les\s+modèles',
            r'choisir\s+(?:un\s+)?modèle'
        ]
        
        # Si l'utilisateur veut créer un nouveau document
        if any(re.search(pattern, normalized_message) for pattern in create_patterns):
            new_context["state"] = "creating_new"
            new_context["last_action"] = "creer_nouveau_document"
            return """Pour créer un nouveau document, j'ai besoin de quelques informations :

1. Quel type de document souhaitez-vous créer ?
2. Quel est son objectif ?
3. Quelles informations doit-il contenir ?

Vous pouvez me donner ces informations comme vous le souhaitez.""", new_context
            
        # Si l'utilisateur veut utiliser un modèle existant
        elif any(re.search(pattern, normalized_message) for pattern in use_patterns):
            new_context["state"] = "choosing_category"
            new_context["last_action"] = "choisir_modele_existant"
            return self._show_available_categories()
            
        # Si l'intention n'est pas claire, demander plus de précisions
        return """Je peux vous aider de deux façons :

📝 Utiliser un modèle existant : Je vous montrerai les modèles disponibles par catégorie
✨ Créer un nouveau document : Je vous guiderai dans la création d'un document personnalisé

Que préférez-vous ?""", new_context 

    def _show_available_categories(self):
        """
        Affiche les catégories de documents disponibles de manière intelligente.
        """
        try:
            # Vérifier si le chemin des modèles est défini
            if not hasattr(self, 'models_path'):
                self.models_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'templates')
            
            # Vérifier que le dossier existe
            if not os.path.exists(self.models_path):
                logger.error(f"Le dossier des modèles n'existe pas: {self.models_path}")
                return """❌ Je suis désolé, je ne trouve pas le dossier des modèles.
                
Veuillez contacter l'administrateur système."""
            
            # Lister les catégories (dossiers)
            categories = []
            category_info = {}
            
            for item in os.listdir(self.models_path):
                item_path = os.path.join(self.models_path, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    # Compter les modèles dans la catégorie
                    model_count = len([f for f in os.listdir(item_path) 
                                     if os.path.isfile(os.path.join(item_path, f)) 
                                     and not f.startswith('.')])
                    
                    # Normaliser le nom de la catégorie
                    normalized_name = item.lower().strip()
                    if normalized_name not in category_info:
                        category_info[normalized_name] = {
                            'display_name': item,
                            'count': model_count,
                            'path': item_path
                        }
                    else:
                        # Fusionner les catégories similaires
                        category_info[normalized_name]['count'] += model_count
                    
                    categories.append(normalized_name)
            
            # Si aucune catégorie n'est trouvée
            if not categories:
                logger.warning("Aucune catégorie trouvée")
                return """❌ Je ne trouve aucune catégorie de document.
                
Veuillez contacter l'administrateur système pour ajouter des modèles."""
            
            # Regrouper les catégories similaires
            merged_categories = {}
            for cat in categories:
                base_name = re.sub(r's$', '', cat)  # Enlever le 's' final si présent
                if base_name not in merged_categories:
                    merged_categories[base_name] = category_info[cat]
                else:
                    merged_categories[base_name]['count'] += category_info[cat]['count']
            
            # Trier les catégories par nombre de modèles
            sorted_categories = sorted(merged_categories.items(), 
                                    key=lambda x: (-x[1]['count'], x[0]))
            
            # Construire le message de réponse
            response = """📂 Voici les catégories de documents disponibles :

"""
            for i, (cat_name, info) in enumerate(sorted_categories, 1):
                model_count = info['count']
                display_name = info['display_name'].capitalize()
                emoji = self._get_category_emoji(cat_name)
                response += f"{emoji} {display_name} ({model_count} modèle{'s' if model_count > 1 else ''})\n"
            
            response += """
Vous pouvez me dire quelle catégorie vous intéresse en utilisant son nom.
Par exemple : "Je voudrais voir les contrats" ou "Montre-moi les factures"."""
            
            # Mettre à jour le contexte avec les catégories normalisées
            self.current_context = {
                "state": "choosing_category",
                "last_action": "afficher_categories",
                "available_categories": list(merged_categories.keys()),
                "category_info": merged_categories
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des catégories: {e}")
            logger.error(traceback.format_exc())
            return """❌ Une erreur s'est produite lors de la récupération des catégories.
            
Veuillez réessayer ou contacter l'administrateur système."""

    def _get_category_emoji(self, category_name):
        """
        Retourne un emoji approprié pour une catégorie donnée.
        """
        emoji_map = {
            'contrat': '📄',
            'facture': '💰',
            'juridique': '⚖️',
            'commercial': '🤝',
            'bancaire': '🏦',
            'administratif': '📋',
            'import': '🚢',
            'proposition': '📊',
            'autre': '📎',
            'document': '📑'
        }
        return emoji_map.get(category_name.lower(), '📁')

    def _show_available_models(self, category):
        """
        Affiche les modèles disponibles dans une catégorie de manière intelligente.
        """
        try:
            # Vérifier si le chemin des modèles est défini
            if not hasattr(self, 'models_path'):
                self.models_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'templates')
            
            # Obtenir les informations de la catégorie depuis le contexte
            category_info = self.current_context.get("category_info", {})
            if category.lower() in category_info:
                category_path = category_info[category.lower()]['path']
                display_name = category_info[category.lower()]['display_name']
            else:
                # Fallback sur le chemin direct
                category_path = os.path.join(self.models_path, category)
                display_name = category
            
            # Vérifier que le dossier existe
            if not os.path.exists(category_path):
                logger.error(f"La catégorie n'existe pas: {category_path}")
                return f"""❌ Je suis désolé, je ne trouve pas la catégorie "{category}".
                
Veuillez choisir une autre catégorie."""
            
            # Lister les modèles (fichiers)
            models = []
            for item in os.listdir(category_path):
                item_path = os.path.join(category_path, item)
                if os.path.isfile(item_path) and not item.startswith('.'):
                    # Obtenir les métadonnées du fichier
                    size = os.path.getsize(item_path)
                    mtime = os.path.getmtime(item_path)
                    
                    # Nettoyer le nom du fichier
                    clean_name = self._clean_model_name(item)
                    
                    models.append({
                        'filename': item,
                        'clean_name': clean_name,
                        'size': size,
                        'mtime': mtime,
                        'path': item_path
                    })
            
            # Si aucun modèle n'est trouvé
            if not models:
                logger.warning(f"Aucun modèle trouvé dans la catégorie {category}")
                return f"""❌ Je ne trouve aucun modèle dans la catégorie "{display_name}".
                
Veuillez choisir une autre catégorie."""
            
            # Trier les modèles par date de modification (plus récents en premier)
            models.sort(key=lambda x: x['mtime'], reverse=True)
            
            # Construire le message de réponse
            emoji = self._get_category_emoji(category)
            response = f"""{emoji} Voici les modèles disponibles dans la catégorie {display_name} :

"""
            for model in models:
                # Formater la taille du fichier
                size = model['size']
                if size > 1024 * 1024:
                    size_str = f"{size/(1024*1024):.1f} MB"
                elif size > 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size} bytes"
                
                response += f"📄 {model['clean_name']} ({size_str})\n"
            
            response += """
Vous pouvez me dire quel modèle vous intéresse en utilisant son nom ou en le décrivant.
Par exemple : "Je voudrais le premier modèle" ou "Montre-moi le modèle de test"."""
            
            # Mettre à jour le contexte
            self.current_context["state"] = "choosing_model"
            self.current_context["last_action"] = "afficher_modeles"
            self.current_context["category"] = category
            self.current_context["available_models"] = models
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des modèles: {e}")
            logger.error(traceback.format_exc())
            return f"""❌ Une erreur s'est produite lors de la récupération des modèles de la catégorie "{category}".
            
Veuillez réessayer ou contacter l'administrateur système."""

    def _clean_model_name(self, filename):
        """
        Nettoie le nom d'un modèle pour l'affichage.
        """
        # Enlever l'extension
        name = os.path.splitext(filename)[0]
        
        # Remplacer les underscores par des espaces
        name = name.replace('_', ' ')
        
        # Enlever les dates au format YYYY-MM-DD
        name = re.sub(r'\d{4}-\d{2}-\d{2}', '', name)
        
        # Enlever les caractères répétés (comme 'xxxxx')
        name = re.sub(r'(.)\1{4,}', r'\1', name)
        
        # Nettoyer les espaces multiples
        name = re.sub(r'\s+', ' ', name)
        
        return name.strip() 