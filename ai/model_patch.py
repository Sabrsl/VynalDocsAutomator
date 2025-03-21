#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Patch pour le modèle d'IA afin d'améliorer la gestion des interactions utilisateur
"""

import logging
import re
import traceback
import requests
import time
import socket
import os
import threading
import json
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
import unicodedata
import types

logger = logging.getLogger("VynalDocsAutomator.AIModelPatch")

# Ajout des fonctions utilisées par patch_ai_model
def _convert_form_info_to_variables(form_info):
    """
    Convertit les informations de formulaire en variables utilisables.
    
    Args:
        form_info (list): Liste des informations fournies par l'utilisateur
        
    Returns:
        dict: Dictionnaire de variables
    """
    try:
        variables = {}
        
        if not form_info:
            return variables
            
        # Analyser chaque ligne
        for info in form_info:
            # Chercher un format "clé: valeur"
            if ":" in info:
                key, value = info.split(":", 1)
                variables[key.strip()] = value.strip()
            # Sinon, essayer de deviner le type d'information
            else:
                info_lower = info.lower()
                if any(word in info_lower for word in ["nom", "client", "personne"]):
                    variables["nom"] = info
                elif any(word in info_lower for word in ["entreprise", "société", "societe", "company"]):
                    variables["entreprise"] = info
                elif any(word in info_lower for word in ["email", "mail", "courriel"]):
                    variables["email"] = info
                elif any(word in info_lower for word in ["adresse", "coordonnées", "coordonnees"]):
                    variables["adresse"] = info
                elif any(word in info_lower for word in ["téléphone", "telephone", "tel", "tél", "phone"]):
                    variables["telephone"] = info
                elif any(word in info_lower for word in ["montant", "prix", "somme", "tarif"]):
                    variables["montant"] = info
                elif any(word in info_lower for word in ["date", "jour"]):
                    variables["date"] = info
                else:
                    # Si on ne peut pas déterminer, utiliser un nom générique
                    key = f"information_{len(variables) + 1}"
                    variables[key] = info
        
        return variables
        
    except Exception as e:
        logger.error(f"Erreur dans _convert_form_info_to_variables: {e}")
        return {}

def get_model_path(instance, category, model_name):
    """
    Retourne le chemin complet d'un modèle.
    
    Args:
        instance: L'instance de la classe (self)
        category (str): Catégorie du modèle
        model_name (str): Nom du modèle
        
    Returns:
        str: Chemin complet du modèle
    """
    try:
        # Vérifier si le chemin des modèles est défini
        if not hasattr(instance, 'models_path'):
            instance.models_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'templates')
            
        # Construire le chemin complet
        model_path = os.path.join(instance.models_path, category, model_name)
        
        # Vérifier que le fichier existe
        if not os.path.exists(model_path):
            logger.error(f"Le modèle n'existe pas: {model_path}")
            return None
            
        return model_path
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du chemin du modèle: {e}")
        return None

# Modèles de données avec Pydantic pour une validation stricte
class DocumentTemplate(BaseModel):
    """Modèle pour les templates de documents."""
    name: str = Field(...)
    category: str = Field(...)
    path: str = Field(...)
    size: int = Field(default=0)
    description: Optional[str] = Field(default="")
    variables: List[str] = Field(default_factory=list)
    
    @validator('path')
    def path_must_exist(cls, v):
        """Valide que le chemin du fichier existe."""
        if not os.path.exists(v):
            raise ValueError(f'Le chemin du fichier {v} n\'existe pas')
        return v

class ClientData(BaseModel):
    """Modèle pour les données client."""
    id: str = Field(default="")
    nom: str = Field(...)  # Champ obligatoire
    entreprise: Optional[str] = Field(default="")
    adresse: Optional[str] = Field(default="")
    téléphone: Optional[str] = Field(default="")
    email: Optional[str] = Field(default="")
    
    @validator('email')
    def email_must_be_valid(cls, v):
        """Valide que l'email a un format correct."""
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Format d\'email invalide')
        return v

class ConversationContext(BaseModel):
    """Modèle pour le contexte de conversation."""
    state: str = Field(default="initial")
    last_action: Optional[str] = Field(default=None)
    subject: Optional[str] = Field(default=None)
    details: Dict[str, Any] = Field(default_factory=dict)
    document_type: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)
    form_info: List[str] = Field(default_factory=list)
    client: Optional[ClientData] = Field(default=None)
    available_categories: List[str] = Field(default_factory=list)
    available_models: List[str] = Field(default_factory=list)
    available_clients: List[ClientData] = Field(default_factory=list)
    state_history: List[str] = Field(default_factory=list)
    missing_vars: List[str] = Field(default_factory=list)
    current_vars: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True

class AIResponse(BaseModel):
    """Modèle pour les réponses de l'IA."""
    response: str = Field(...)  # Champ obligatoire
    state: str = Field(default="initial")
    action: Optional[str] = Field(default=None)

# Créer une session HTTP persistante pour reduire la latence
session = requests.Session()

# Variables globales pour suivre les erreurs d'Ollama
ollama_consecutive_failures = 0
ollama_disabled_until = 0

# États possibles de la conversation
STATES = {
    "initial": {
        "description": "État initial de la conversation",
        "valid_transitions": ["asking_document_type", "general_query"],
        "required_context": []
    },
    "asking_document_type": {
        "description": "Demande du type de document",
        "valid_transitions": ["choosing_category", "creating_new"],
        "required_context": []
    },
    "choosing_category": {
        "description": "Choix d'une catégorie de document",
        "valid_transitions": ["choosing_model"],
        "required_context": ["available_categories"]
    },
    "choosing_model": {
        "description": "Choix d'un modèle spécifique",
        "valid_transitions": ["model_selected"],
        "required_context": ["category", "available_models"]
    },
    "model_selected": {
        "description": "Un modèle a été sélectionné",
        "valid_transitions": ["filling_document", "using_model"],
        "required_context": ["model"]
    },
    "filling_document": {
        "description": "Remplissage du document",
        "valid_transitions": ["document_completed", "filling_document"],
        "required_context": ["model", "form_fields"]
    },
    "creating_new": {
        "description": "Création d'un nouveau document",
        "valid_transitions": ["document_type_selected", "creating_new"],
        "required_context": []
    }
}

def _validate_state_transition(current_state, new_state, context):
    """
    Valide une transition d'état.
    
    Args:
        current_state (str): L'état actuel
        new_state (str): Le nouvel état demandé
        context (dict): Le contexte actuel
        
    Returns:
        tuple: (bool, str) - (transition valide, message d'erreur)
    """
    # Vérifier si les états existent
    if current_state not in STATES:
        return False, f"État actuel invalide: {current_state}"
    if new_state not in STATES:
        return False, f"Nouvel état invalide: {new_state}"
        
    # Vérifier si la transition est autorisée
    if new_state not in STATES[current_state]["valid_transitions"]:
        return False, f"Transition non autorisée de {current_state} vers {new_state}"
        
    # Vérifier si le contexte requis est présent
    required_context = STATES[new_state]["required_context"]
    missing_context = [key for key in required_context if key not in context]
    if missing_context:
        return False, f"Contexte manquant pour {new_state}: {', '.join(missing_context)}"
        
    return True, ""

def should_use_ollama():
    """
    Détermine si Ollama doit être utilisé en fonction des échecs précédents.
    """
    global ollama_consecutive_failures, ollama_disabled_until
    
    # Si Ollama est temporairement désactivé
    if time.time() < ollama_disabled_until:
        return False
    
    # Si trop d'échecs consécutifs, vérifier Ollama
    if ollama_consecutive_failures >= 3:
        if check_ollama_running():
            # Réinitialiser le compteur d'échecs
            ollama_consecutive_failures = 0
            return True
        else:
            # Désactiver Ollama pendant 60 secondes
            ollama_disabled_until = time.time() + 60
            logger.warning(f"Ollama désactivé pendant 60 secondes suite à {ollama_consecutive_failures} échecs consécutifs")
            return False
    
    return True

def check_ollama_running(url="http://localhost:11434/api/version", timeout=2):
    """
    Vérifie si le serveur Ollama est en cours d'exécution.
    """
    try:
        response = session.get(url, timeout=timeout)
        return response.status_code == 200
    except (requests.exceptions.RequestException, socket.error):
        return False

def patch_ai_model(AIModel):
    """
    Applique les modifications au modèle d'IA.
    """
    original_handle_model_actions = AIModel._handle_model_actions
    original_handle_user_choice = AIModel._handle_user_choice
    
    # Sauvegarder la méthode originale _normalize_input si elle existe
    original_normalize_input = None
    if hasattr(AIModel, '_normalize_input'):
        original_normalize_input = AIModel._normalize_input

    def enhanced_normalize_input(self, text):
        """
        Version améliorée de _normalize_input qui normalise plus efficacement les entrées
        utilisateur pour une meilleure correspondance.
        """
        if not text:
            return ""
            
        # Appeler d'abord la méthode originale si elle existe
        if original_normalize_input:
            result = original_normalize_input(self, text)
        else:
            # Sinon, faire une normalisation de base
            result = text.lower().strip()
        
        # Normalisation supplémentaire
        result = result.replace("é", "e").replace("è", "e").replace("ê", "e")
        result = result.replace("à", "a").replace("â", "a")
        result = result.replace("ô", "o")
        result = result.replace("î", "i").replace("ï", "i")
        result = result.replace("û", "u").replace("ù", "u")
        result = result.replace("ç", "c")
        
        # Supprimer la ponctuation et les caractères spéciaux
        result = re.sub(r'[^\w\s]', '', result)
        
        # Remplacer les espaces multiples par un seul espace
        result = re.sub(r'\s+', ' ', result)
        
        return result.strip()

    def _show_available_categories(self):
        """
        Affiche les catégories disponibles en utilisant _get_available_categories.
        """
        try:
            # Obtenir les catégories disponibles
            categories = self._get_available_categories()
            
            if not categories:
                return """❌ Je n'ai trouvé aucune catégorie de documents.
                
Veuillez contacter l'administrateur système."""
            
            # Construire le message de réponse
            response = "📂 Voici les catégories de documents disponibles :\n\n"
            for i, category in enumerate(categories, 1):
                response += f"{i}️⃣ {category}\n"
            
            response += "\nVeuillez choisir une catégorie en tapant son numéro ou son nom."
            
            # Mettre à jour le contexte
            self.current_context["state"] = "choosing_category"
            self.current_context["last_action"] = "afficher_categories"
            self.current_context["available_categories"] = categories
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des catégories: {e}")
            logger.error(traceback.format_exc())
            return """❌ Une erreur s'est produite lors de la récupération des catégories.
            
Veuillez réessayer ou contacter l'administrateur système."""


    def _is_simple_thanks(self, message):
        """
        Vérifie si le message est un simple remerciement.
        """
        message = message.lower().strip()
        thanks_patterns = [
            r'^merci$',
            r'^thanks$',
            r'^thank you$'
        ]
        return any(re.match(pattern, message) for pattern in thanks_patterns)

    def _reset_context(self):
        """
        Réinitialise le contexte de conversation complet en utilisant le modèle Pydantic.
        """
        self.current_context = ConversationContext(
            state="initial",
            last_action="reinitialisation",
            subject=None,
            details={},
            document_type=None,
            category=None,
            model=None,
            form_info=[]
        ).dict()  # Convertir en dictionnaire pour compatibilité avec le code existant
        
        return self.current_context

    def _handle_state_transition(self, message, context):
        """
        Gère une transition d'état basée sur le message et le contexte.
        
        Args:
            message (str): Le message de l'utilisateur
            context (dict): Le contexte actuel
            
        Returns:
            tuple: (str, dict) - (nouvel état, contexte mis à jour)
        """
        try:
            current_state = context.get("state", "initial")
            normalized_message = self._normalize_input(message)
            
            # Priorité sur les options 1 et 2 dans l'état asking_document_type
            if current_state == "asking_document_type" and normalized_message in ["1", "2"]:
                if normalized_message == "1":
                    new_state = "choosing_category"
                    context["available_categories"] = self._get_available_categories()
                else:  # normalized_message == "2"
                    new_state = "creating_new"
                
                # Mettre à jour l'historique des états
                if "state_history" not in context:
                    context["state_history"] = []
                context["state_history"].append(current_state)
                
                # Mettre à jour le contexte
                context["state"] = new_state
                context["last_action"] = f"transition_vers_{new_state}"
                
                return new_state, context
            
            # Commandes spéciales
            if normalized_message in ["annuler", "retour", "back"]:
                state_history = context.get("state_history", [])
                if state_history:
                    new_state = state_history.pop()
                    context["state_history"] = state_history
                    return new_state, context
            
            # Déterminer le nouvel état
            new_state = current_state  # Par défaut, rester dans l'état actuel
            
            # Transitions basées sur l'état actuel
            if current_state == "initial":
                if "document" in normalized_message or "modele" in normalized_message:
                    new_state = "asking_document_type"
                
            elif current_state == "asking_document_type":
                if normalized_message in ["1", "modele", "existant"]:
                    new_state = "choosing_category"
                elif normalized_message in ["2", "nouveau", "creer"]:
                    new_state = "creating_new"
                
            elif current_state == "choosing_category":
                if self._is_valid_category_choice(normalized_message, context):
                    new_state = "choosing_model"
                
            elif current_state == "choosing_model":
                if self._is_valid_model_choice(normalized_message, context):
                    new_state = "model_selected"
                
            elif current_state == "model_selected":
                if normalized_message in ["1", "remplir", "completer"]:
                    new_state = "filling_document"
                elif normalized_message in ["2", "utiliser", "tel quel"]:
                    new_state = "using_model"
            
            # Valider la transition
            is_valid, error_message = _validate_state_transition(current_state, new_state, context)
            if not is_valid:
                logger.warning(f"Transition invalide: {error_message}")
                return current_state, context
            
            # Mettre à jour l'historique des états
            if "state_history" not in context:
                context["state_history"] = []
            if new_state != current_state:
                context["state_history"].append(current_state)
            
            # Mettre à jour le contexte
            context["state"] = new_state
            context["last_action"] = f"transition_vers_{new_state}"
            
            return new_state, context
            
        except Exception as e:
            logger.error(f"Erreur lors de la transition d'état: {e}")
            return current_state, context

    def _is_valid_category_choice(self, category, context):
        """
        Vérifie si la catégorie sélectionnée est valide et met à jour le contexte.
        """
        try:
            available_categories = context.get("available_categories", [])
            normalized_category = self._normalize_input(category)
            
            # Vérifier si c'est un numéro
            if normalized_category.isdigit():
                index = int(normalized_category) - 1
                if 0 <= index < len(available_categories):
                    # Mettre à jour le contexte avec la catégorie sélectionnée
                    context["category"] = available_categories[index]
                    return True
                return False
            
            # Vérifier si la catégorie existe
            for cat in available_categories:
                if self._normalize_input(cat) == normalized_category:
                    # Mettre à jour le contexte avec la catégorie sélectionnée
                    context["category"] = cat
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation de la catégorie: {e}")
            return False

    def _is_valid_model_choice(self, model, context):
        """
        Vérifie si le modèle sélectionné est valide.
        """
        try:
            available_models = context.get("available_models", [])
            normalized_model = self._normalize_input(model)
            
            # Vérifier si c'est un numéro
            if normalized_model.isdigit():
                index = int(normalized_model) - 1
                return 0 <= index < len(available_models)
            
            # Vérifier si le modèle existe
            return any(self._normalize_input(m) == normalized_model for m in available_models)
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation du modèle: {e}")
            return False

    def _handle_workflow(self, message, stream=False):
        """
        Gère le workflow de conversation en fonction de l'état actuel.
        """
        try:
            # Obtenir l'état actuel
            current_state = self.current_context.get("state", "initial")
            
            # Debug - afficher l'état actuel
            print(f"DEBUG - _handle_workflow - État actuel: {current_state}")
            
            # Gérer la transition d'état
            new_state, updated_context = self._handle_state_transition(message, self.current_context)
            
            # Mettre à jour le contexte avec le nouvel état
            self.current_context = updated_context
            self.current_context["state"] = new_state
            
            # Si l'état a changé, logger la transition
            if new_state != current_state:
                print(f"DEBUG - Transition d'état effectuée: {current_state} -> {new_state}")
            
            # Continuer avec le traitement normal du workflow
            return self._process_current_state(message, new_state)
            
        except Exception as e:
            logger.error(f"Erreur dans _handle_workflow: {e}")
            return "Une erreur s'est produite. Veuillez réessayer."

    def _process_current_state(self, message, state):
        """
        Traite le message en fonction de l'état actuel.
        """
        try:
            # Normaliser le message
            normalized_message = self._normalize_input(message)
            
            # Traitement en fonction de l'état
            if state == "asking_document_type":
                if normalized_message == "1":
                    self.current_context["state"] = "choosing_category"
                    self.current_context["available_categories"] = self._get_available_categories()
                    return self._show_available_categories()
                elif normalized_message == "2":
                    self.current_context["state"] = "creating_new"
                    return """Pour créer un nouveau document, j'ai besoin de quelques informations :

1. Quel type de document souhaitez-vous créer ?
2. Quel est son objectif ?
3. Quelles informations doit-il contenir ?

Veuillez me donner ces informations."""
                else:
                    return """📌 Que souhaitez-vous faire ?

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document"""
                
            elif state == "choosing_category":
                if self._is_valid_category_choice(normalized_message, self.current_context):
                    self.current_context["state"] = "choosing_model"
                    category = self.current_context.get("category")
                    self.current_context["available_models"] = self._get_available_models(category)
                    return self._show_available_models(category)
                else:
                    return "Veuillez choisir une catégorie valide.\n\n" + self._show_available_categories()
                
            elif state == "choosing_model":
                if self._is_valid_model_choice(normalized_message, self.current_context):
                    self.current_context["state"] = "asking_client"
                    if normalized_message.isdigit():
                        index = int(normalized_message) - 1
                        available_models = self.current_context.get("available_models", [])
                        if 0 <= index < len(available_models):
                            self.current_context["model"] = available_models[index]
                    else:
                        self.current_context["model"] = normalized_message
                    
                    return """Pour quel client souhaitez-vous utiliser ce modèle ?
Veuillez entrer le nom du client ou son identifiant."""
                else:
                    category = self.current_context.get("category")
                    return "Veuillez choisir un modèle valide.\n\n" + self._show_available_models(category)
                
            elif state == "asking_client":
                # Chercher le client dans la base de données
                client_name = message.strip()
                clients = self._search_clients(client_name)
                
                if not clients:
                    self.current_context["client"] = client_name
                    self.current_context["state"] = "client_not_found"
                    return f"""⚠️ Je n'ai pas trouvé de client correspondant à "{client_name}".

Souhaitez-vous :
1️⃣ Créer un nouveau client
2️⃣ Réessayer avec un autre nom
3️⃣ Continuer sans client"""
                
                elif len(clients) == 1:
                    # Un seul client trouvé, on le sélectionne
                    self.current_context["client"] = clients[0]
                    self.current_context["state"] = "model_selected"
                    
                    # Déterminer si les informations sont disponibles
                    entreprise = clients[0].get('entreprise', '')
                    email = clients[0].get('email', '')
                    telephone = clients[0].get('téléphone', '')
                    
                    return f"""✅ Client trouvé : {clients[0]['nom']}
                    
📋 Détails du client :
🏢 Entreprise : {entreprise if entreprise else 'Non disponible'}
📧 Email : {email if email else 'Non disponible'}
📞 Téléphone : {telephone if telephone else 'Non disponible'}

Que souhaitez-vous faire avec ce modèle ?
1️⃣ Remplir le document
2️⃣ Utiliser tel quel"""
                
                else:
                    # Plusieurs clients trouvés, demander à l'utilisateur de choisir
                    self.current_context["state"] = "choosing_client"
                    self.current_context["available_clients"] = clients
                    
                    # Créer une liste formatée des clients avec les informations disponibles
                    clients_list = []
                    for i, client in enumerate(clients):
                        # Récupérer les informations disponibles
                        nom = client.get('nom', 'Sans nom')
                        entreprise = client.get('entreprise', '')
                        email = client.get('email', '')
                        
                        # Créer la ligne avec les informations disponibles
                        client_line = f"{i+1}️⃣ {nom}"
                        if entreprise:
                            client_line += f" - {entreprise}"
                        if email:
                            client_line += f" - {email}"
                            
                        clients_list.append(client_line)
                    
                    formatted_clients = "\n".join(clients_list)
                    return f"""J'ai trouvé plusieurs clients correspondants :

{formatted_clients}

Veuillez choisir un client en tapant son numéro."""
                    
            elif state == "choosing_client":
                if normalized_message.isdigit():
                    index = int(normalized_message) - 1
                    available_clients = self.current_context.get("available_clients", [])
                    
                    if 0 <= index < len(available_clients):
                        self.current_context["client"] = available_clients[index]
                        self.current_context["state"] = "model_selected"
                        
                        # Déterminer si les informations sont disponibles
                        entreprise = available_clients[index].get('entreprise', '')
                        email = available_clients[index].get('email', '')
                        telephone = available_clients[index].get('téléphone', '')
                        
                        return f"""✅ Client sélectionné : {available_clients[index]['nom']}

📋 Détails du client :
🏢 Entreprise : {entreprise if entreprise else 'Non disponible'}
📧 Email : {email if email else 'Non disponible'}
📞 Téléphone : {telephone if telephone else 'Non disponible'}

Que souhaitez-vous faire avec ce modèle ?
1️⃣ Remplir le document
2️⃣ Utiliser tel quel"""
                    
                return """⚠️ Veuillez choisir un client valide en tapant son numéro."""
                    
            elif state == "client_not_found":
                if normalized_message == "1":
                    self.current_context["state"] = "creating_client"
                    return """Pour créer un nouveau client, j'ai besoin des informations suivantes :

1. Nom complet
2. Email
3. Téléphone
4. Adresse

Veuillez me donner ces informations."""
                    
                elif normalized_message == "2":
                    self.current_context["state"] = "asking_client"
                    return "Veuillez entrer un autre nom de client :"
                    
                elif normalized_message == "3":
                    self.current_context["state"] = "model_selected"
                    return """Que souhaitez-vous faire avec ce modèle ?
1️⃣ Remplir le document
2️⃣ Utiliser tel quel"""
                    
                else:
                    return """⚠️ Option non valide.

Souhaitez-vous :
1️⃣ Créer un nouveau client
2️⃣ Réessayer avec un autre nom
3️⃣ Continuer sans client"""
                    
            elif state == "model_selected":
                if normalized_message == "1":
                    self.current_context["state"] = "filling_document"
                    return "D'accord, je vais vous aider à remplir ce document. Commençons par le nom du client."
                elif normalized_message == "2":
                    model_path = self.get_model_path(self.current_context.get("category"), self.current_context.get("model"))
                    if self._open_document(model_path):
                        return "Le document a été ouvert. Souhaitez-vous créer un autre document ?"
                    else:
                        return "Désolé, je n'ai pas pu ouvrir le document. Veuillez réessayer."
                else:
                    return """Veuillez choisir une option :

1️⃣ Remplir le document
2️⃣ Utiliser tel quel"""
                
            elif state == "creating_new":
                # Stocker les informations fournies
                if "form_info" not in self.current_context:
                    self.current_context["form_info"] = []
                self.current_context["form_info"].append(message)
                
                return """✅ Information enregistrée.

Avez-vous d'autres informations à ajouter ?
Tapez 'terminer' quand vous avez fini."""
                
            else:
                return """Je ne comprends pas votre demande dans ce contexte.

📌 Que souhaitez-vous faire ?

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document"""
                
        except Exception as e:
            logger.error(f"Erreur dans _process_current_state: {e}")
            return "Une erreur s'est produite. Veuillez réessayer."

    def _generate_llama_response(self, message, stream=False):
        """
        Génère une réponse en utilisant l'API Llama.
        """
        global ollama_consecutive_failures
        try:
            if not should_use_ollama():
                logger.warning("Ollama n'est pas disponible. Utilisation d'une réponse par défaut.")
                return "Je suis désolé, je ne peux pas répondre à cette question pour le moment. Comment puis-je vous aider avec vos documents ?"

            prompt = f"""Tu es un assistant IA amical et professionnel spécialisé dans la gestion de documents.
Réponds à la question suivante de façon directe et concise: {message}"""

            params = {
                "model": self.model,
                "prompt": prompt,
                "stream": stream,
                "temperature": 0.7,
                "max_tokens": 800,
                "top_p": 0.9,
                "stop": ["Question:", "Humain:", "Utilisateur:", "\n\n"]
            }

            response = session.post(
                "http://localhost:11434/api/generate",
                json=params,
                timeout=30
            )

            if response.status_code == 200:
                ollama_consecutive_failures = 0

                if stream:
                    return self._stream_response(response)
                else:
                    result = response.json()
                    if "response" in result:
                        return self._clean_response(result["response"])

            ollama_consecutive_failures += 1
            logger.warning(f"Erreur d'API Ollama ({response.status_code}). Échecs consécutifs: {ollama_consecutive_failures}")
            return "Je suis désolé, je rencontre des difficultés pour répondre à cette question. Comment puis-je vous aider avec vos documents ?"

        except Exception as e:
            ollama_consecutive_failures += 1
            logger.error(f"Erreur lors de l'appel à Llama: {e}")
            logger.error(traceback.format_exc())
            return "Je suis désolé, une erreur technique m'empêche de répondre. Comment puis-je vous aider avec vos documents ?"

    def patched_generate_response(self, message, stream=False):
        """
        Version patchée de generate_response avec une meilleure gestion des états
        et des réponses plus naturelles
        """
        try:
            # Ne pas traiter les messages vides
            if not message or len(message.strip()) == 0:
                return "Je n'ai pas compris votre message. Pourriez-vous reformuler?"
            
            # Normaliser l'entrée pour la recherche
            if not hasattr(self, '_normalize_input'):
                def _normalize_input(self, text):
                    """Normalise le texte en entrée"""
                    if not text:
                        return ""
                    # Convertir en minuscules et supprimer les espaces inutiles
                    text = text.lower().strip()
                    # Supprimer les accents
                    text = ''.join(c for c in unicodedata.normalize('NFD', text)
                                if unicodedata.category(c) != 'Mn')
                    return text
                self._normalize_input = types.MethodType(_normalize_input, self)
            
            normalized_input = self._normalize_input(message)
            
            # DEBUG
            print(f"DEBUG - patched_generate_response - Message reçu: '{message}'")
            print(f"DEBUG - patched_generate_response - Message normalisé: '{normalized_input}'")
            print(f"DEBUG - patched_generate_response - État actuel: '{self.current_context.get('state', 'initial')}'")
            
            # Gérer directement les choix 1 et 2 dans l'état asking_document_type
            current_state = self.current_context.get('state', 'initial')
            
            # Gestion spéciale pour les choix 1 et 2 dans tous les états pertinents
            if normalized_input == "1" or normalized_input == "2":
                # Si dans l'état initial ou asking_document_type
                if current_state in ["initial", "asking_document_type"]:
                    if normalized_input == "1":
                        # Option 1: Utiliser un modèle existant
                        self.current_context["state"] = "choosing_category"
                        self.current_context["last_action"] = "choisir_modele_existant"
                        # Assurer que le chemin des modèles est défini
                        if not hasattr(self, 'models_path'):
                            self.models_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'templates')
                        # Mettre à jour les catégories disponibles
                        self.current_context["available_categories"] = self._get_available_categories()
                        return self._show_available_categories()
                    else:  # normalized_input == "2"
                        # Option 2: Créer un nouveau document
                        self.current_context["state"] = "creating_new"
                        self.current_context["last_action"] = "creer_nouveau_document"
                        return """Pour créer un nouveau document, j'ai besoin de quelques informations :

1. Quel type de document souhaitez-vous créer ?
2. Quel est son objectif ?
3. Quelles informations doit-il contenir ?

Veuillez me donner ces informations."""
            
            # Détection spécifique pour "cv" et "cava" qui peuvent être ambigus
            if normalized_input in ["cv", "cava", "ca va", "ça va"]:
                print(f"DEBUG - Détection spéciale pour '{normalized_input}'")
                return """Je vais très bien, merci ! 👋

Je peux vous aider à :
📄 Créer un nouveau document
📝 Utiliser un modèle existant
🧩 Remplir des modèles avec vos informations

Que souhaitez-vous faire ?"""
            
            # Si nous sommes dans un état spécifique du workflow, traiter avec _handle_workflow
            if current_state != "initial":
                print(f"DEBUG - État non initial: '{current_state}', utilisation de _handle_workflow")
                # Priorité à _handle_workflow pour les états spécifiques
                workflow_response = self._handle_workflow(message)
                if workflow_response:
                    return workflow_response
                
                # Si _handle_workflow ne donne pas de réponse, essayer _handle_model_actions
                model_action_response = self._handle_model_actions(message)
                if model_action_response:
                    return model_action_response

                # Si on est toujours dans asking_document_type et les chiffres 1/2 sont entrés
                if current_state == "asking_document_type" and normalized_input in ["1", "2"]:
                    print(f"DEBUG - Réponse forcée pour '{normalized_input}' dans l'état '{current_state}'")
                    if normalized_input == "1":
                        self.current_context["state"] = "choosing_category"
                        self.current_context["last_action"] = "choisir_modele_existant"
                        return self._show_available_categories()
                    else:  # normalized_input == "2"
                        self.current_context["state"] = "creating_new"
                        self.current_context["last_action"] = "creer_nouveau_document"
                        return """Pour créer un nouveau document, j'ai besoin de quelques informations :

1. Quel type de document souhaitez-vous créer ?
2. Quel est son objectif ?
3. Quelles informations doit-il contenir ?

Veuillez me donner ces informations."""
            
            # Patterns renforcés pour les salutations
            greeting_patterns = [
                # Salutations simples
                r'\b(?:salut|bonjour|bonsoir|hey|hi|hello|coucou|yo|hola)\b',
                # Variations de "ça va"
                r'\b(?:ca|ça)\s*(?:va|vas?)\b',
                r'\bcomment\s*(?:ca|ça)\s*(?:va|vas?)\b',
                r'\bcomment\s*(?:tu\s*)?(?:vas?|allez)\b',
                r'\btu\s*vas?\s*bien\b',
                # Variations de "cv"
                r'\bcv\b',
                r'\bc+\s*v+\b',
                r'\bsv+[tp]?\b',
                # Formules de politesse
                r'\benchanté\b',
                r'\bravi\b',
                r'\bplaisir\b',
                # Moments de la journée
                r'\bbonne?\s*(?:journée|soirée|nuit|matinée|après[\s-]midi)\b'
            ]
            
            # Si c'est une salutation
            if any(re.search(pattern, normalized_input, re.IGNORECASE) for pattern in greeting_patterns):
                print(f"DEBUG - C'est une salutation: '{normalized_input}'")
                return """Je vais très bien, merci ! 👋

Je peux vous aider à :
📄 Créer un nouveau document
📝 Utiliser un modèle existant
🧩 Remplir des modèles avec vos informations

Que souhaitez-vous faire ?"""
            
            # Patterns renforcés pour les commandes courtes
            short_command_patterns = {
                # Commandes d'accord
                "accord": [r'\b(?:ok|okay|oké|oki|oui|ouais?|yep|yes|yeah|dac+(?:ord)?|bien|très?\s*bien|parfait|super|excellent|génial|cool|nickel|top)\b'],
                # Commandes de refus
                "refus": [r'\b(?:non|no|nope|pas|jamais)\b'],
                # Commandes de continuation
                "continue": [r'\b(?:suivant|continue[rz]?|après|ensuite|puis|next)\b'],
                # Commandes de retour
                "retour": [r'\b(?:retour|back|précédent|precedent|arrière|revenir|annuler|cancel)\b'],
                # Commandes de fin
                "fin": [r'\b(?:fin|fini|terminer?|stop|arrête[rz]?|quitter?|exit|bye|au\s*revoir|a\+)\b'],
                # Commandes de répétition
                "repeter": [r'\b(?:répéte[rz]?|repeat|redis|encore|again)\b'],
                # Commandes d'aide
                "aide": [r'\b(?:aide|help|sos|besoin|aider?)\b']
            }
            
            # Vérifier les commandes courtes
            for command_type, patterns in short_command_patterns.items():
                if any(re.search(pattern, normalized_input, re.IGNORECASE) for pattern in patterns):
                    print(f"DEBUG - C'est une commande courte de type '{command_type}': '{normalized_input}'")
                    # Si nous sommes dans l'état initial
                    if self.current_context["state"] == "initial":
                        if command_type == "accord":
                            return self._show_available_categories()
                        elif command_type in ["fin", "retour"]:
                            return """Au revoir ! N'hésitez pas à revenir si vous avez besoin d'aide pour vos documents. 👋"""
                    # Si nous venons de terminer un document
                    elif self.current_context.get("last_action") == "document_completed":
                        if command_type == "accord":
                            return """Excellent ! Je suis ravi d'avoir pu vous aider. 

Souhaitez-vous créer un autre document ?
1️⃣ Oui, créer un autre document
2️⃣ Non, c'est tout pour aujourd'hui"""
                    
                    # Pour toute autre commande d'accord dans un autre état
                    if command_type == "accord":
                        result = self._handle_model_actions(message)
                        print(f"DEBUG - Résultat de _handle_model_actions pour commande '{command_type}': {result}")
                        return result if result else self._handle_workflow(message)
                    elif command_type == "aide":
                        return """Je suis là pour vous aider ! Voici ce que je peux faire :

1️⃣ Utiliser un modèle existant de document
2️⃣ Créer un nouveau document personnalisé
3️⃣ Remplir automatiquement vos documents

Que souhaitez-vous faire ?"""
                    
            # Patterns renforcés pour les demandes de documents
            doc_patterns = [
                # Types de documents
                r'\b(?:document|doc|fichier|dossier|papier)s?\b',
                r'\b(?:modele|modèle|template|exemple|formulaire)s?\b',
                r'\b(?:contrat|facture|devis|lettre|attestation|certificat|déclaration)s?\b',
                r'\b(?:image|photo|figure|graphique|diagramme|schéma)s?\b',
                r'\b(?:pdf|word|excel|powerpoint|ppt|docx|xlsx|txt)s?\b',
                
                # Actions sur les documents
                r'\b(?:créer|creer|faire|générer|generer|rédiger|rediger|écrire|ecrire)\b',
                r'\b(?:remplir|completer|compléter|modifier|éditer|editer)\b',
                r'\b(?:utiliser|ouvrir|voir|afficher|montrer|consulter)\b',
                
                # Expressions de besoin
                r'\b(?:je\s*(?:veux|voudrais|souhaite|aimerais|dois|peux|dois|cherche))\b',
                r'\b(?:il\s*(?:me\s*)?faut)\b',
                r'\b(?:j\'ai\s*besoin)\b',
                r'\b(?:besoin\s*d[e\'])\b',
                
                # Catégories spécifiques
                r'\b(?:administratif|juridique|commercial|financier|technique)\b',
                r'\b(?:personnel|professionnel|officiel|standard|template)\b',
                
                # Variations et fautes courantes
                r'\b(?:documant|documment|documens|documant)s?\b',
                r'\b(?:je\s*(?:veut|veu|veus|veus|vx))\b',
                r'\bunn?\s*(?:document|doc)s?\b',
                r'\b(?:cre+|cré+)(?:er?|é)\b',
                r'\b(?:model|modl|modle|modele)s?\b',
                
                # Expressions informelles
                r'\b(?:truc|chose|papier|feuille)s?\b',
                r'\bfaut\s*(?:que|qu\')\s*(?:je|j\')\b',
                
                # Demandes indirectes
                r'\b(?:comment|où|ou)\s*(?:je|j\'|on)\s*(?:peux?|dois|fait|trouve)\b',
                r'\b(?:aide|help|sos|besoin\s*d\'aide)\b',
                
                # Symboles et emojis courants
                r'[📄📝✍️📋📎]',
                
                # Expressions de début
                r'^(?:ok|okay|dac|bien|super|parfait|go|allez|aller)\b'
            ]
            
            # Si c'est une demande de document ou si nous sommes déjà dans le processus
            if any(re.search(pattern, normalized_input, re.IGNORECASE) for pattern in doc_patterns) or current_state != "initial":
                # Si l'utilisateur a entré 1 ou 2
                if normalized_input in ["1", "2"]:
                    if normalized_input == "1":
                        self.current_context["state"] = "choosing_category"
                        self.current_context["last_action"] = "choisir_modele_existant"
                        return self._show_available_categories()
                    else:  # normalized_input == "2"
                        self.current_context["state"] = "creating_new"
                        self.current_context["last_action"] = "creer_nouveau_document"
                        return """Pour créer un nouveau document, j'ai besoin de quelques informations :

1. Quel type de document souhaitez-vous créer ?
2. Quel est son objectif ?
3. Quelles informations doit-il contenir ?

Veuillez me donner ces informations."""
                
                # Si c'est une salutation simple
                if normalized_input in ["cv", "cava", "ca va", "ça va"]:
                    return """Je vais très bien, merci ! 👋

Je peux vous aider à :
📄 Créer un nouveau document
📝 Utiliser un modèle existant
🧩 Remplir des modèles avec vos informations

Que souhaitez-vous faire ?"""
                
                # Réponse par défaut pour une demande de document
                return """📌 Que souhaitez-vous faire ?

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document"""
            
            # Si nous sommes dans un état spécifique du workflow, ne pas utiliser Llama
            if self.current_context["state"] != "initial":
                workflow_response = self._handle_workflow(message)
                if workflow_response:
                    return workflow_response
                
                return self._handle_model_actions(message)
            
            # Si c'est un chiffre ou un numéro seul
            if re.match(r'^\d+$', normalized_input):
                return self._handle_model_actions(message)
            
            # Patterns renforcés pour les questions
            question_patterns = [
                # Mots interrogatifs
                r'\b(?:comment|pourquoi|quand|où|qui|quel(?:le)?s?|quoi|combien|lequel)\b',
                r'\b(?:qu[\'e](?:st[-\s]ce\s*(?:que)?)?)\b',
                # Inversions interrogatives
                r'\b(?:peux[-\s]tu|pouvez[-\s]vous|sais[-\s]tu|savez[-\s]vous)\b',
                r'\b(?:est[-\s]ce\s*(?:que)?|as[-\s]tu|avez[-\s]vous)\b',
                # Marqueurs de question
                r'\?+',
                # Expressions de demande d'information
                r'\b(?:explique[rz]?[-\s]moi|dis[-\s]moi|montre[-\s]moi)\b',
                r'\b(?:je\s*(?:veux|voudrais|souhaite|aimerais)\s*savoir)\b'
            ]
            
            # Si c'est une question
            is_question = (
                any(re.search(pattern, normalized_input, re.IGNORECASE) for pattern in question_patterns) or
                len(message.split()) > 3  # Si c'est une phrase plus longue
            )
            
            if is_question:
                return self._generate_llama_response(message, stream)
            else:
                # Pour tout autre cas, montrer le menu principal
                self._reset_context()
                return """Je peux vous aider à gérer vos documents. Que souhaitez-vous faire ?

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document"""
                
        except Exception as e:
            logger.error(f"Erreur dans patched_generate_response: {e}")
            logger.error(traceback.format_exc())
            print(f"DEBUG - Exception dans patched_generate_response: {e}")
            return "Une erreur s'est produite lors du traitement de votre demande. Veuillez réessayer ou contacter l'assistance."

    def patched_handle_user_choice(self, user_input):
        """
        Version améliorée de _handle_user_choice qui gère mieux les entrées de l'utilisateur
        et les changements de contexte.
        """
        try:
            msg_lower = user_input.lower().strip()
            
            # Vérifier les salutations
            greeting_patterns = [
                r'\bcava\b', r'\bça va\b', r'\bcomment ça va\b', r'\bcomment vas[\s-]tu\b', 
                r'\bcomment tu vas\b', r'\bcomment tu va\b', r'\btu vas bien\b',
                r'\bcomment cv\b', r'\bcv\??\b', r'\bbonjour\b', r'\bsalut\b', r'\bhello\b'
            ]
            
            # Si c'est une simple salutation
            if any(re.search(pattern, msg_lower) for pattern in greeting_patterns) and len(user_input.split()) <= 3:
                current_state = self.current_context.get("state", "initial")
                
                # Si nous sommes au début
                if current_state in ["initial", "greeting"]:
                    self.current_context["state"] = "greeting"
                    return "Je vais très bien, merci ! Comment puis-je vous aider avec vos documents aujourd'hui ?"
                
                # Si nous sommes au milieu d'un processus
                if current_state == "choosing_category":
                    return "Je vais bien, merci ! Pour continuer, veuillez choisir une catégorie de document parmi celles proposées."
                elif current_state == "choosing_model":
                    return "Je vais bien, merci ! Pour continuer, veuillez choisir un modèle de document parmi ceux proposés."
                elif current_state == "model_selected":
                    return "Je vais bien, merci ! Pour continuer, que souhaitez-vous faire avec le document sélectionné ?"
                else:
                    return "Je vais bien, merci ! Continuons avec votre document. Comment puis-je vous aider ?"
            
            # Vérifier si c'est une demande d'avis sur un document
            opinion_doc_patterns = [
                r'ton avis sur ce(tte)? doc(ument)?', r'penses[\s-]tu (de )?ce doc(ument)?',
                r'avis sur (le|ce) (document|modèle|fichier|template)',
                r'que penses[\s-]tu (de )?ce(tte)? (document|modèle|fichier|template)'
            ]
            
            is_opinion_doc_request = any(re.search(pattern, msg_lower) for pattern in opinion_doc_patterns)
            
            # Si l'utilisateur demande un avis sur un document spécifique
            current_state = self.current_context.get("state", "initial")
            if is_opinion_doc_request and current_state in ["choosing_model", "model_selected"]:
                # Extraire le document actuellement sélectionné s'il existe
                current_model = self.current_context.get("model")
                current_category = self.current_context.get("category")
                
                if current_model and current_category:
                    # Vérifier si Ollama est disponible et fiable
                    if should_use_ollama():
                        try:
                            # Créer un prompt adapté pour l'avis sur le document
                            prompt = f"""Je suis un assistant IA qui aide à créer des documents. L'utilisateur me demande mon avis sur un document de type '{current_category}', nommé '{current_model}'. 
Comment puis-je lui donner un avis professionnel et utile sur ce document sans l'avoir vu, en me basant sur son type et son nom?"""
                            
                            # Générer une réponse avec Llama
                            llama_response = self._get_llama_response(prompt)
                            
                            # Si Llama a réussi à générer une réponse pertinente
                            if llama_response and len(llama_response) > 15:
                                context_reminder = "\n\nSi vous souhaitez utiliser ce document, vous pouvez :\n1️⃣ Le remplir maintenant\n2️⃣ L'utiliser tel quel\n\nVeuillez choisir en tapant 1 ou 2."
                                full_response = llama_response + context_reminder
                                
                                # Mettre à jour l'état
                                self.current_context["state"] = "model_selected"
                                
                                return full_response
                        except Exception as e:
                            logger.error(f"Erreur lors de la génération d'avis sur document: {e}")
                            logger.error(traceback.format_exc())
                    
                    # Si Ollama n'est pas disponible ou a échoué, utiliser une réponse par défaut
                    return f"Ce document '{current_model}' de la catégorie '{current_category}' semble être un bon choix pour votre besoin. Souhaitez-vous:\n1️⃣ Le remplir maintenant\n2️⃣ L'utiliser tel quel\n\nVeuillez choisir en tapant 1 ou 2."
                else:
                    # Si aucun document n'est encore sélectionné
                    return "Veuillez d'abord sélectionner un document spécifique pour que je puisse vous donner mon avis dessus."
            
            # Vérifier si c'est une demande courte de document
            doc_request_patterns = [
                # Demandes directes de document
                r'\b(?:je\s*(?:veux|voudrais|souhaite|aimerais)\s*(?:un|une|des|le|la|les)?\s*(?:docs?|documents?|modele?s?|modèle?s?))\b',
                r'\bun\s*(?:docs?|documents?|modele?s?|modèle?s?)\b',
                r'\b(?:creer|créer|faire|nouveau)\s*(?:un|une|des|le|la|les)?\s*(?:docs?|documents?|modele?s?|modèle?s?)\b',
                r'\b(?:utiliser|prendre|choisir|voir)\s*(?:un|une|des|le|la|les)?\s*(?:docs?|documents?|modele?s?|modèle?s?)\s*(?:existants?|disponibles?)?\b',
                
                # Mots-clés simples
                r'\b(?:docs?|documents?|modele?s?|modèle?s?)\b',
                r'\b(?:existants?|nouveaux?|disponibles?)\b',
                r'\b(?:creer|créer|faire|nouveau)\b',
                
                # Variations et fautes courantes
                r'\b(?:documant|documment|documens|documan)s?\b',
                r'\b(?:modl|modle|modele|model)s?\b',
                r'\b(?:cre+|cré+)(?:er?|é)\b',
                
                # Expressions de besoin
                r'\b(?:il\s*(?:me\s*)?faut)\b',
                r'\b(?:j\'ai\s*besoin)\b',
                r'\b(?:besoin\s*d[e\'])\b'
            ]
            
            # Normaliser l'entrée utilisateur
            normalized_input = message.lower().strip()
            
            # Si c'est une demande de document (vérifier tous les patterns)
            if any(re.search(pattern, normalized_input, re.IGNORECASE) for pattern in doc_request_patterns):
                # Si nous sommes déjà dans un état spécifique, continuer le processus
                if current_state != "initial":
                    return {
                        "response": self._get_state_response(current_state),
                        "state": current_state,
                        "action": "continue_process"
                    }
                
                # Sinon, commencer le processus
                return {
                    "response": """📌 Que souhaitez-vous faire ?

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document

Veuillez choisir une option en tapant 1 ou 2.""",
                    "state": "asking_document_type",
                    "action": "demande_document"
                }
            
            # Détecter s'il s'agit d'une question générale ou d'une demande d'information
            general_question_patterns = [
                r'\bpourquoi\b', r'\bcomment\b', r'\bquand\b', r'\boù\b', r'\bqui\b', 
                r'\bquel\b', r'\bquelle\b', r'\bcombien\b', r'\bque\b', r'\bqu\'est(-ce)?(\s+que)?\b'
            ]
            
            # Patterns pour les demandes d'avis
            opinion_patterns = [
                r'\bpenses[\s-]tu\b', r'\bton avis\b', r'\bpenses[\s-]tu\b', 
                r'\bton opinion\b', r'\bque penses[\s-]tu\b'
            ]
            
            is_general_question = any(re.search(pattern, msg_lower) for pattern in general_question_patterns)
            is_opinion_request = any(re.search(pattern, msg_lower) for pattern in opinion_patterns)
            
            # Si c'est une question générale ou une demande d'avis pendant le processus
            if (is_opinion_request or (is_general_question and len(user_input.split()) > 3)) and current_state not in ["initial", "greeting"]:
                # Utiliser Llama pour répondre tout en maintenant le contexte
                try:
                    # Vérifier si Ollama est disponible
                    if not should_use_ollama():
                        logger.warning("Ollama n'est pas disponible dans _handle_user_choice. Utilisation du comportement standard.")
                        return original_handle_user_choice(self, user_input)
                        
                    # Adapter le prompt en fonction du type de question
                    if is_opinion_request:
                        prompt = f"L'utilisateur me demande mon avis pendant le processus de document: {user_input}. Réponds de façon sympathique et professionnelle."
                    else:
                        prompt = f"L'utilisateur me pose cette question pendant le processus de document: {user_input}. Réponds de façon concise et précise."
                    
                    # Générer une réponse avec Llama
                    llama_response = self._get_llama_response(prompt)
                    
                    # Vérifier que la réponse est valide
                    if llama_response and len(llama_response) > 15:
                        # Déterminer un rappel du contexte basé sur l'état actuel
                        if current_state == "choosing_category":
                            context_reminder = "\n\nPour revenir à notre processus, veuillez choisir une catégorie de document."
                        elif current_state == "choosing_model":
                            context_reminder = "\n\nPour revenir à notre processus, veuillez choisir un modèle de document."
                        elif current_state == "model_selected":
                            context_reminder = "\n\nPour revenir à notre processus, veuillez indiquer ce que vous souhaitez faire avec le document."
                        else:
                            context_reminder = "\n\nMaintenant, revenons à votre document."
                        
                        return llama_response + context_reminder
                except Exception as e:
                    logger.error(f"Erreur lors de l'appel à Llama dans _handle_user_choice: {e}")
                    # En cas d'erreur, continuer avec le comportement normal
            
            # Pour toute autre entrée utilisateur pendant le processus, essayer d'utiliser Llama
            if current_state not in ["initial", "greeting"] and len(user_input.split()) > 1:
                try:
                    # Vérifier si Ollama est disponible
                    if not should_use_ollama():
                        logger.warning("Ollama n'est pas disponible pour le traitement général dans _handle_user_choice. Utilisation du comportement standard.")
                        return original_handle_user_choice(self, user_input)
                        
                    # Créer un prompt contextualisé
                    prompt = f"Je suis un assistant IA qui aide à créer des documents. L'utilisateur est en train de {self._get_state_description(current_state)} et me dit: '{user_input}'. Comment dois-je interpréter cette entrée et y répondre de manière utile?"
                    
                    # Générer une réponse avec Llama
                    llama_response = self._get_llama_response(prompt)
                    
                    # Si Llama a réussi à générer une réponse pertinente
                    if llama_response and len(llama_response) > 15:
                        # Ajouter un rappel contextuel
                        if current_state == "choosing_category":
                            context_reminder = "\n\nVeuillez choisir une catégorie de document pour continuer."
                        elif current_state == "choosing_model":
                            context_reminder = "\n\nVeuillez choisir un modèle de document pour continuer."
                        elif current_state == "model_selected":
                            context_reminder = "\n\nVeuillez indiquer ce que vous souhaitez faire avec le document."
                        else:
                            context_reminder = "\n\nContinuons avec votre document."
                        
                        return llama_response + context_reminder
                except Exception as e:
                    logger.error(f"Erreur lors de l'appel général à Llama dans _handle_user_choice: {e}")
                    # En cas d'erreur, continuer avec le comportement normal
            
            # Appliquer le comportement normal pour tous les autres cas
            return original_handle_user_choice(self, user_input)
            
        except Exception as e:
            # Capturer les erreurs et fournir une réponse utile
            logger.error(f"Erreur dans _handle_user_choice: {e}")
            logger.error(traceback.format_exc())
            
            # Réinitialiser le contexte et reprendre depuis le début
            self.current_context["state"] = "asking_document_type"
            return """Je suis désolé, j'ai perdu le contexte de notre conversation. Reprenons :

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document

Veuillez choisir une option en tapant 1 ou 2."""

    def _analyze_document_with_llama(self, document_text):
        """
        Utilise Llama pour analyser le document et détecter les variables personnalisables.
        """
        try:
            prompt = f"""Tu es un assistant spécialisé en analyse et personnalisation de documents.
    
1️⃣ **Analyse le document** et **détecte toutes les variables personnalisables** (Nom, Adresse, Date, Montant, Lieu, etc.).
2️⃣ **Évite les répétitions** : Si une variable est présente plusieurs fois, ne la demande qu'une seule fois.
3️⃣ **Génère une liste claire des informations nécessaires** à l'utilisateur.

📄 **Document :**
```text
{document_text}
```

🔍 **Résultat attendu (format JSON) :**
```json
{{
    "nom": "??",
    "adresse": "??",
    "date": "??",
    "montant": "??",
    "lieu": "??",
    "téléphone": "??",
    "référence": "??"
}}
```

Renvoie uniquement la liste des variables trouvées sous format JSON. Si une variable n'est pas trouvée, ne l'inclus pas."""

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model if hasattr(self, 'model') else "llama3",
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.2,
                    "max_tokens": 300
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json().get("response", "{}")
                # Extraire uniquement la partie JSON de la réponse
                json_str = re.search(r'\{.*\}', result, re.DOTALL)
                if json_str:
                    return json.loads(json_str.group())
            return {}

        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du document avec Llama: {e}")
            return {}

    def _refine_document_with_llama(self, final_document):
        """
        Utilise Llama pour améliorer la fluidité du texte final.
        """
        try:
            prompt = f"""Ce document a été personnalisé avec des valeurs fournies par l'utilisateur. 
Vérifie la fluidité du texte et reformule si nécessaire.

📄 **Document personnalisé :**
```text
{final_document}
```

🔍 **Instructions :**
- Corrige les erreurs grammaticales et syntaxiques
- Reformule pour plus de clarté et fluidité
- Garde le même format et la même structure
- Ne modifie pas les informations personnelles

📢 **Texte final corrigé :**"""

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model if hasattr(self, 'model') else "llama3",
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,
                    "max_tokens": 500
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json().get("response", final_document)
            return final_document

        except Exception as e:
            logger.error(f"Erreur lors du raffinement du document avec Llama: {e}")
            return final_document

    def patched_handle_model_actions(self, message: str) -> Dict[str, Any]:
        try:
            # Patterns de demande de document
            doc_request_patterns = [
                # ... existing code ...
            ]
            
            # Normaliser l'entrée utilisateur
            normalized_input = message.lower().strip()
            
            # Variables du contexte actuelles
            current_state = self.current_context.get("state", "")
            category = self.current_context.get("category")
            selected_model = self.current_context.get("model")
            last_action = self.current_context.get("last_action", "")
            
            # Liste des commandes de complétion
            completion_commands = [
                "completer", "compléter", "terminer", "fini", "finir", "done",
                "c'est tout", "ca suffit", "ça suffit", "ok", "termine"
            ]
            
            # Si nous sommes en train de remplir le document
            if current_state == "filling_document":
                # Si c'est la première fois (pas encore de client)
                if not self.current_context.get("client_asked"):
                    self.current_context["client_asked"] = True
                    return """Pour commencer, j'ai besoin du nom du client.
Quel est le nom du client pour ce document ?"""
                
                # Si nous attendons le nom du client
                elif not self.current_context.get("client_data"):
                    # Rechercher le client
                    clients = self._search_clients(message)
                    
                    if clients and len(clients) > 0:
                        self.current_context["client_data"] = clients[0]
                        
                        # Analyser le document pour les variables
                        try:
                            model_path = self.get_model_path(category, selected_model)
                            with open(model_path, 'r', encoding='utf-8') as f:
                                document_text = f.read()
                            
                            # Analyser le document avec Llama
                            variables = self._analyze_document_with_llama(document_text)
                            
                            # Compléter avec les données client
                            completed_vars = self._complete_variables_with_client(variables, clients[0])
                            
                            # Identifier les variables manquantes
                            missing_vars = [var for var, val in completed_vars.items() if val == "??"]
                            
                            if missing_vars:
                                # Il manque des informations à demander
                                self.current_context["state"] = "filling_missing_vars"
                                self.current_context["missing_vars"] = missing_vars
                                self.current_context["current_vars"] = completed_vars
                                
                                return f"""✅ Client trouvé : {clients[0]['nom']} ({clients[0]['entreprise']})

J'ai analysé le document et j'ai besoin des informations suivantes :

{chr(10).join([f"• {var}" for var in missing_vars])}

Veuillez me donner ces informations une par une."""
                            else:
                                # Toutes les variables sont remplies
                                final_document = document_text
                                for var_name, value in completed_vars.items():
                                    final_document = final_document.replace(f"<<{var_name}>>", value)
                                
                                # Raffiner le document
                                refined_document = self._refine_document_with_llama(final_document)
                                
                                # Sauvegarder le document final
                                output_path = os.path.join(self.models_path, category, f"filled_{selected_model}")
                                with open(output_path, 'w', encoding='utf-8') as f:
                                    f.write(refined_document)
                                
                                return f"""✅ Parfait ! J'ai complété le document "{selected_model}" avec les informations du client.

Le document a été enregistré sous : {output_path}

Souhaitez-vous :
1️⃣ Créer un autre document
2️⃣ Terminer et revenir au menu principal"""
                        
                        except Exception as e:
                            logger.error(f"Erreur lors de l'analyse du document: {e}")
                            return """❌ Une erreur s'est produite lors de l'analyse du document.

Veuillez réessayer ou contacter l'assistance."""
                    
                    else:
                        return """❌ Je ne trouve pas ce client dans la base de données.

Veuillez vérifier le nom et réessayer, ou tapez 'nouveau' pour créer un nouveau client."""
                
                # Vérifier si c'est une commande de complétion
                elif normalized_input in completion_commands:
                    # Le reste du code pour la complétion...
                    return self._handle_completion(message)
                
                else:
                    # Ajouter l'information au formulaire
                    if "form_info" not in self.current_context:
                        self.current_context["form_info"] = []
                    self.current_context["form_info"].append(message)
                    return """✅ Information bien enregistrée.

Donnez-moi une autre information à inclure dans le document,
ou tapez 'compléter' quand vous avez terminé."""
            
            # Si nous sommes en train de remplir les variables manquantes
            elif current_state == "filling_missing_vars":
                missing_vars = self.current_context.get("missing_vars", [])
                current_vars = self.current_context.get("current_vars", {})
                
                if not missing_vars:
                    # Toutes les variables sont remplies, générer le document
                    saved_model = self.current_context.get("completed_model")
                    category = self.current_context.get("category")
                    
                    try:
                        model_path = self.get_model_path(category, saved_model)
                        with open(model_path, 'r', encoding='utf-8') as f:
                            document_text = f.read()
                        
                        # Générer le document final
                        final_document = document_text
                        for var_name, value in current_vars.items():
                            final_document = final_document.replace(f"<<{var_name}>>", value)
                        
                        # Raffiner le document avec Llama
                        refined_document = self._refine_document_with_llama(final_document)
                        
                        # Sauvegarder le document final
                        output_path = os.path.join(self.models_path, category, f"filled_{saved_model}")
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(refined_document)
                        
                        # Réinitialiser le contexte
                        self._reset_context()
                        
                        return f"""✅ Parfait ! J'ai complété le document "{saved_model}" avec toutes les informations.

Le document a été enregistré sous : {output_path}

Souhaitez-vous :
1️⃣ Créer un autre document
2️⃣ Terminer et revenir au menu principal"""
                        
                    except Exception as e:
                        logger.error(f"Erreur lors de la génération du document final: {e}")
                        return """❌ Une erreur s'est produite lors de la génération du document.

Veuillez réessayer ou contacter l'assistance."""
                
                # Ajouter la nouvelle information
                current_var = missing_vars[0]
                current_vars[current_var] = message
                missing_vars.pop(0)
                
                self.current_context["missing_vars"] = missing_vars
                self.current_context["current_vars"] = current_vars
                
                if missing_vars:
                    return f"""✅ Information bien enregistrée.

Il me manque encore : {missing_vars[0]}"""
                else:
                    return self._handle_model_actions("compléter")
            
            # Le reste du code existant...
            # Remplacer l'appel à super() par une solution plus simple
            # return super()._handle_model_actions(message)
            return "Je ne comprends pas votre demande dans ce contexte. Veuillez choisir une option parmi celles proposées."
            
        except Exception as e:
            logger.error(f"Erreur dans patched_handle_model_actions: {e}")
            logger.error(traceback.format_exc())
            return "Une erreur s'est produite. Veuillez réessayer ou contacter l'assistance."

    def _get_state_description(self, state):
        """
        Génère une description textuelle de l'état actuel pour le prompt Llama.
        """
        descriptions = {
            "choosing_category": "est en train de choisir une catégorie de document parmi une liste proposée",
            "choosing_model": "est en train de sélectionner un modèle de document spécifique dans une catégorie",
            "model_selected": "a sélectionné un modèle de document et doit choisir quoi faire avec (le remplir, le prévisualiser, etc.)",
            "filling_document": "est en train de remplir un formulaire pour un document"
        }
        
        try:
            return descriptions.get(state, "est dans une étape du processus de gestion de documents")
        except Exception as e:
            logger.error(f"Erreur dans _get_state_description: {e}")
            return "est en train d'utiliser l'application"

    def _open_document(self, path):
        """
        Ouvre un document avec l'application par défaut du système.
        """
        if not os.path.exists(path):
            logger.error(f"Le document n'existe pas: {path}")
            return False
        
        try:
            import platform
            system = platform.system()
            
            if system == 'Windows':
                os.startfile(path)
            elif system == 'Darwin':  # macOS
                import subprocess
                subprocess.call(['open', path])
            else:  # Linux
                import subprocess
                subprocess.call(['xdg-open', path])
            
            logger.info(f"Document ouvert avec succès: {path}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du document: {e}")
            return False

    def _get_llama_response(self, message: str) -> str:
        """
        Obtient une réponse pour les interactions de base avec l'utilisateur.
        
        Args:
            message (str): Le message de l'utilisateur
            
        Returns:
            str: La réponse générée
        """
        try:
            # Vérifier si Ollama est disponible
            if not should_use_ollama():
                logger.warning("Ollama n'est pas disponible. Utilisation d'une réponse par défaut.")
                return "Je suis désolé, je ne peux pas répondre à cette question pour le moment."
                
            # Créer un prompt adapté
            prompt = f"L'utilisateur me dit: {message}. Je suis un assistant spécialisé dans la gestion de documents. Je dois répondre de façon concise et précise."
            
            # Appeler l'API Ollama
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model if hasattr(self, 'model') else "llama3",
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                    "max_tokens": 300
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "Je ne comprends pas votre question.")
            else:
                return "Je suis désolé, je rencontre des difficultés techniques."
                
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à Llama dans _get_llama_response: {e}")
            return "Je suis désolé, une erreur technique m'empêche de répondre correctement."

    def _show_available_models(self, category):
        """
        Affiche les modèles disponibles dans une catégorie en utilisant le modèle DocumentTemplate.
        """
        try:
            # Vérifier si la catégorie est None ou vide
            if not category:
                logger.error("Catégorie non spécifiée pour l'affichage des modèles")
                return """❌ Erreur: Aucune catégorie n'a été spécifiée.

Veuillez d'abord choisir une catégorie valide."""
                
            # Vérifier si le chemin des modèles est défini
            if not hasattr(self, 'models_path'):
                self.models_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'templates')
            
            # Construire le chemin de la catégorie
            category_path = os.path.join(self.models_path, category)
            
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
                    # Obtenir la taille du fichier
                    size = os.path.getsize(item_path)
                    
                    try:
                        # Créer un modèle DocumentTemplate validé
                        template = DocumentTemplate(
                            name=item,
                            category=category,
                            path=item_path,
                            size=size,
                            variables=[]  # On pourrait les analyser ici si nécessaire
                        )
                        models.append(template)
                    except Exception as validation_error:
                        logger.warning(f"Validation du modèle {item} échouée: {validation_error}")
                        # Ignorer ce modèle et continuer avec les autres
            
            # Si aucun modèle n'est trouvé
            if not models:
                logger.warning(f"Aucun modèle trouvé dans la catégorie {category}")
                return f"""❌ Je ne trouve aucun modèle dans la catégorie "{category}".
                
Veuillez choisir une autre catégorie ou contacter l'administrateur système."""
            
            # Trier les modèles par ordre alphabétique
            models.sort(key=lambda x: x.name)
            
            # Construire le message de réponse
            response = f"📄 Voici les modèles disponibles dans la catégorie {category} :\n\n"
            for i, model in enumerate(models, 1):
                # Formater la taille du fichier
                size_str = f"{model.size/1024:.1f} KB" if model.size > 1024 else f"{model.size} bytes"
                
                # Ajouter le modèle avec sa taille
                response += f"{i}️⃣ {model.name} ({size_str})\n"
            
            response += "\nVeuillez choisir un modèle en tapant son numéro ou son nom."
            
            # Mettre à jour le contexte
            self.current_context["state"] = "choosing_model"
            self.current_context["last_action"] = "afficher_modeles"
            self.current_context["category"] = category
            self.current_context["available_models"] = [model.name for model in models]
            
            return response
                
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des modèles: {e}")
            logger.error(traceback.format_exc())
            return f"""❌ Une erreur s'est produite lors de la récupération des modèles de la catégorie "{category}".
            
Veuillez réessayer ou contacter l'administrateur système."""

    def _search_client(self, query):
        """
        Recherche des clients dans la base de données.
        """
        try:
            # Chemin direct vers clients.json, en suivant la configuration
            clients_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'clients', 'clients.json')
            
            # Vérifier si le fichier existe
            if not os.path.exists(clients_file):
                logger.warning(f"Fichier clients.json non trouvé: {clients_file}")
                return []
            
            # Charger les clients
            with open(clients_file, 'r', encoding='utf-8') as f:
                clients_data = json.load(f)
            
            # Debug - afficher les clients trouvés
            logger.info(f"Recherche de client: '{query}' dans {len(clients_data)} clients")
            
            # Normaliser la recherche
            normalized_query = self._normalize_input(query)
            
            # Rechercher les clients correspondants
            matching_clients = []
            for client in clients_data:
                # Vérifier que le client est un dict valide avec les champs nécessaires
                if not isinstance(client, dict) or 'name' not in client:
                    continue
                    
                # Utiliser les champs name et company pour la recherche
                client_name = self._normalize_input(client.get('name', ''))
                client_company = self._normalize_input(client.get('company', ''))
                client_email = self._normalize_input(client.get('email', ''))
                
                if (normalized_query in client_name or 
                    normalized_query in client_company or 
                    normalized_query in client_email):
                    try:
                        # Créer un modèle ClientData validé
                        matching_client = ClientData(
                            id=client.get('id', ''),
                            nom=client.get('name', 'Sans nom'),  # Champ obligatoire
                            entreprise=client.get('company', ''),
                            adresse=client.get('address', ''),
                            téléphone=client.get('phone', ''),
                            email=client.get('email', '')
                        )
                        # Convertir en dictionnaire pour compatibilité avec le code existant
                        matching_clients.append(matching_client.dict())
                    except Exception as validation_error:
                        logger.warning(f"Validation du client échouée: {validation_error}")
                        # Ignorer ce client et continuer avec les autres
            
            # Debug - afficher les correspondances trouvées
            logger.info(f"Clients correspondants pour '{query}': {len(matching_clients)}")
            
            return matching_clients
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de clients: {e}")
            logger.error(traceback.format_exc())
            return []

    def _complete_variables_with_client(self, variables, client_data):
        """
        Remplit les variables détectées avec les données du client.
        """
        completed_variables = {}
        
        # Mapping des clés du client vers les variables du document
        client_mapping = {
            "nom": ["nom", "client", "nom_client", "client_nom"],
            "entreprise": ["entreprise", "societe", "société", "raison_sociale"],
            "adresse": ["adresse", "adresse_client", "domicile"],
            "téléphone": ["telephone", "téléphone", "tel", "tél"],
            "email": ["email", "courriel", "mail"]
        }
        
        for var_name, value in variables.items():
            if value == "??":  # Si c'est une variable à remplir
                # Chercher dans le mapping client
                for client_key, possible_vars in client_mapping.items():
                    if any(possible_var in var_name.lower() for possible_var in possible_vars):
                        if client_key in client_data:
                            completed_variables[var_name] = client_data[client_key]
                            break
                else:
                    # Si la variable n'est pas trouvée dans les données client
                    completed_variables[var_name] = "??"
        
        return completed_variables

    def _get_state_response(self, state):
        """
        Retourne la réponse appropriée pour l'état actuel.
        """
        if state == "choosing_category":
            return "Veuillez choisir une catégorie parmi celles proposées :\n\n" + self._show_available_categories()
        elif state == "choosing_model":
            category = self.current_context.get("category", "")
            return f"Veuillez choisir un modèle dans la catégorie {category} :\n\n" + self._show_available_models(category)
        elif state == "model_selected":
            model = self.current_context.get("model", "")
            return f"""Que souhaitez-vous faire avec le modèle "{model}" ?

1️⃣ Remplir le document
2️⃣ Utiliser tel quel"""
        else:
            return """📌 Que souhaitez-vous faire ?

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document

Veuillez choisir une option en tapant 1 ou 2."""

    def _get_available_categories(self):
        """
        Retourne la liste des catégories disponibles.
        """
        try:
            # Vérifier si le chemin des modèles est défini
            if not hasattr(self, 'models_path'):
                self.models_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'templates')
            
            # Vérifier si le dossier existe
            if not os.path.exists(self.models_path):
                logger.error(f"Dossier des modèles non trouvé: {self.models_path}")
                return []
            
            # Lister les sous-dossiers (catégories)
            categories = [d for d in os.listdir(self.models_path) if os.path.isdir(os.path.join(self.models_path, d))]
            return categories
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des catégories: {e}")
            return []

    def _get_available_models(self, category):
        """
        Retourne la liste des modèles disponibles dans une catégorie.
        """
        try:
            # Vérifier si la catégorie est None ou vide
            if not category:
                logger.error("Catégorie non spécifiée pour la récupération des modèles")
                return []
                
            # Vérifier si le chemin des modèles est défini
            if not hasattr(self, 'models_path'):
                self.models_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'templates')
            
            # Construire le chemin de la catégorie
            category_path = os.path.join(self.models_path, category)
            
            # Vérifier que le dossier existe
            if not os.path.exists(category_path):
                logger.error(f"La catégorie n'existe pas: {category_path}")
                return []
            
            # Lister les fichiers (modèles)
            models = [f for f in os.listdir(category_path) if os.path.isfile(os.path.join(category_path, f))]
            return models
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des modèles: {e}")
            return []

    # Patch the methods
    AIModel._is_simple_thanks = _is_simple_thanks
    AIModel._reset_context = _reset_context
    AIModel._handle_workflow = _handle_workflow
    AIModel._handle_state_transition = _handle_state_transition
    AIModel._process_current_state = _process_current_state
    AIModel._generate_llama_response = _generate_llama_response
    AIModel.generate_response = patched_generate_response
    AIModel._handle_user_choice = patched_handle_user_choice
    AIModel._handle_model_actions = patched_handle_model_actions
    AIModel._get_state_description = _get_state_description
    AIModel._open_document = _open_document
    AIModel._get_llama_response = _get_llama_response
    AIModel._convert_form_info_to_variables = _convert_form_info_to_variables
    AIModel.get_model_path = get_model_path
    AIModel._show_available_categories = _show_available_categories
    AIModel._show_available_models = _show_available_models
    AIModel._is_valid_category_choice = _is_valid_category_choice
    AIModel._is_valid_model_choice = _is_valid_model_choice
    
    
    # Remplacer la méthode originale _normalize_input si elle existe
    if hasattr(AIModel, '_normalize_input'):
        original_normalize_input = AIModel._normalize_input
        AIModel._normalize_input = enhanced_normalize_input
    else:
        # Si la méthode n'existe pas, l'ajouter directement
        AIModel._normalize_input = enhanced_normalize_input

    # Dans la section de patch des méthodes, ajouter :
    AIModel._search_clients = _search_client  # Utiliser le nom correct de la fonction définie
    AIModel._get_available_categories = _get_available_categories
    AIModel._get_available_models = _get_available_models

    return AIModel 

    def _handle_completion(self, message):
        """
        Gère la complétion d'un document.
        """
        try:
            # Obtenir les informations du formulaire
            form_info = self.current_context.get("form_info", [])
            
            if not form_info:
                return "Vous n'avez pas encore fourni d'informations. Veuillez d'abord me donner les informations nécessaires."
            
            # Convertir les informations du formulaire en variables
            variables = self._convert_form_info_to_variables(form_info)
            
            # Obtenir le modèle et la catégorie
            category = self.current_context.get("category")
            model = self.current_context.get("model")
            
            if not category or not model:
                return "Je ne peux pas compléter le document car je n'ai pas toutes les informations nécessaires. Veuillez réessayer depuis le début."
            
            # Obtenir le chemin du modèle
            model_path = self.get_model_path(category, model)
            if not model_path:
                return "Je ne trouve pas le modèle spécifié. Veuillez réessayer avec un autre modèle."
            
            try:
                # Lire le modèle
                with open(model_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                # Remplacer les variables
                final_content = template_content
                for var_name, value in variables.items():
                    # Rechercher les marqueurs de la forme <<var_name>>
                    final_content = final_content.replace(f"<<{var_name}>>", value)
                
                # Enregistrer le document complété
                output_filename = f"filled_{model}"
                output_path = os.path.join(self.models_path, category, output_filename)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(final_content)
                
                # Mettre à jour le contexte
                self.current_context["state"] = "initial"
                self.current_context["last_action"] = "document_completed"
                self.current_context["completed_document"] = output_path
                
                return f"""✅ Document complété avec succès !

Le document a été enregistré sous : {output_path}

Souhaitez-vous :
1️⃣ Ouvrir le document maintenant
2️⃣ Créer un autre document
3️⃣ Terminer"""
                
            except Exception as e:
                logger.error(f"Erreur lors de la complétion du document: {e}")
                logger.error(traceback.format_exc())
                return "Une erreur s'est produite lors de la complétion du document. Veuillez réessayer."
            
        except Exception as e:
            logger.error(f"Erreur dans _handle_completion: {e}")
            logger.error(traceback.format_exc())
            return "Une erreur s'est produite. Veuillez réessayer."

    def _show_available_categories(self):
        """
        Affiche les catégories disponibles en utilisant _get_available_categories.
        """
        try:
            # Obtenir les catégories disponibles
            categories = self._get_available_categories()
            
            if not categories:
                return """❌ Je n'ai trouvé aucune catégorie de documents.
                
Veuillez contacter l'administrateur système."""
            
            # Construire le message de réponse
            response = "📂 Voici les catégories de documents disponibles :\n\n"
            for i, category in enumerate(categories, 1):
                response += f"{i}️⃣ {category}\n"
            
            response += "\nVeuillez choisir une catégorie en tapant son numéro ou son nom."
            
            # Mettre à jour le contexte
            self.current_context["state"] = "choosing_category"
            self.current_context["last_action"] = "afficher_categories"
            self.current_context["available_categories"] = categories
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des catégories: {e}")
            logger.error(traceback.format_exc())
            return """❌ Une erreur s'est produite lors de la récupération des catégories.
            
Veuillez réessayer ou contacter l'administrateur système."""