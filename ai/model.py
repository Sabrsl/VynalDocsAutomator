#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modèle d'IA pour la gestion des documents
"""

import requests
import logging
import json
import os
import difflib
import time
import re
from typing import Dict, List, Optional, Tuple, Generator, Any
from models.document_model_manager import DocumentModelManager
from pathlib import Path

logger = logging.getLogger("VynalDocsAutomator.AIModel")

# Prompt Vynal•GPT
DOCSGPT_PROMPT = """Tu es DocsGPT, un assistant expert en rédaction de documents professionnels.

Tu sais créer :
- des documents complets (contrats, lettres, rapports…)
- bien structurés (titres, sections, signatures…)
- adaptés au ton requis (formel, administratif, commercial…)

Tu peux aussi :
- reformuler ou corriger un texte
- expliquer des termes juridiques ou administratifs
- améliorer la clarté, la cohérence ou la présentation d'un contenu

Quand tu rédiges un document :
- ne dis jamais "voici le document"
- écris directement le texte final, clair et prêt à l'emploi
- structure-le avec des titres, paragraphes, ou articles si nécessaire
- adapte-le à la demande sans blabla inutile

Ne réponds rien si l'utilisateur dit "merci", "ok", "c'est bon", etc.

Sois rapide, efficace et professionnel."""

class AIModel:
    def __init__(self, model_name="llama3"):
        """
        Initialise le modèle d'IA avec les paramètres par défaut
        
        Args:
            model_name: Nom du modèle à utiliser (par défaut: llama3)
        """
        # Initialiser le logger
        self.logger = logging.getLogger("VynalDocsAutomator.AI")
        
        # Configuration du modèle
        self.model = model_name
        self.api_base = "http://localhost:11434/api"
        self.api_url = "http://localhost:11434/api/generate"
        self.timeout = 60
        
        # Paramètres de génération
        self.max_tokens = 4096
        self.num_predict = 4096  # Nombre maximum de tokens à générer
        self.num_ctx = 2048
        self.temperature = 0.7  # Température pour la créativité
        self.top_p = 0.9
        self.top_k = 40
        self.repeat_penalty = 1.1
        self.presence_penalty = 0
        self.frequency_penalty = 0
        self.seed = None
        self.num_thread = 4
        self.num_gpu = 1
        self.stop = []  # Suppression des tokens d'arrêt
        self.echo = False
        
        # Système de prompt pour contexte juridique
        self.system_prompt = DOCSGPT_PROMPT
        
        # Initialiser les données
        self._initialize_data()
    
    def _initialize_data(self):
        """Initialise les données et l'état de conversation"""
        # Initialisation des états de conversation
        self.conversation_state = {}
        self.conversation_history = [{"role": "system", "content": self.system_prompt}]
        self.selected_category = None
        self.selected_model = None
        
        # États du flux de conversation
        self.waiting_for_category = False
        self.waiting_for_model = False
        self.waiting_for_details = False
        
        # Dictionnaires pour stocker les templates par catégorie
        self.templates_by_category = {}
        
        # Liste des types de documents
        self.document_types = []
        
        # Charger les modèles de documents
        self._load_document_templates()
        
        # Vérifier que le modèle est disponible
        self._verify_model()
        
        # Commandes disponibles
        self.commands = {
            "help": self._help_command,
            "clear": self._clear_command,
            "status": self._status_command,
            "model": self._model_command
        }
        
        self.logger.info(f"AIModel initialisé avec le modèle {self.model}")

    def _load_categories(self):
        """
        Charge les catégories et thèmes disponibles depuis templates.json.
        """
        try:
            templates_file = os.path.join(self.models_path, "templates.json")
            if os.path.exists(templates_file):
                with open(templates_file, "r", encoding="utf-8") as f:
                    templates = json.load(f)
                
                # Organiser les templates par catégorie et thème
                for template in templates:
                    category = template.get("category", "").lower()
                    theme = template.get("theme", "").lower()
                    
                    if category and theme:
                        if category not in self.categories:
                            self.categories[category] = set()
                        self.categories[category].add(theme)
                
                self.logger.info("Catégories et thèmes chargés avec succès")
            else:
                self.logger.warning("Fichier templates.json non trouvé")
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des catégories : {e}")
            self.categories = {}

    def _extract_document_info(self, message: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Analyse le message pour extraire le type de document et le domaine.
        
        Args:
            message (str): Le message à analyser
            
        Returns:
            Tuple[Optional[str], Optional[str], Optional[str]]: (type, catégorie, thème)
        """
        message_lower = message.lower()
        doc_type = None
        doc_category = None
        doc_theme = None

        # Mots-clés pour les types de documents
        doc_types = {
            "contrat": ["contrat", "convention", "accord", "engagement"],
            "proposition": ["proposition", "devis", "offre", "soumission"],
            "lettre": ["lettre", "courrier", "mail", "correspondance"],
            "rapport": ["rapport", "compte-rendu", "bilan", "synthèse"]
        }

        # Détecter le type de document
        for doc_type_key, keywords in doc_types.items():
            if any(keyword in message_lower for keyword in keywords):
                doc_type = doc_type_key
                break

        # Vérifier d'abord si une catégorie est déjà dans le contexte
        if self.current_context.get("category"):
            doc_category = self.current_context["category"]

        # Chercher la catégorie dans le message
        for category in self.categories:
            if category in message_lower:
                doc_category = category
                self.current_context["category"] = category
                break

        return doc_type, doc_category, doc_theme

    def _update_available_models(self):
        """
        Met à jour la liste des types de documents disponibles en explorant
        les dossiers présents dans data/documents/types.
        """
        # Vérifier si le répertoire existe
        if not os.path.exists(self.models_path):
            os.makedirs(self.models_path, exist_ok=True)
            self.logger.info(f"Répertoire '{self.models_path}' créé")
        
        # Réinitialiser la liste des types de documents
        self.document_types = []
        
        # Explorer les dossiers dans le répertoire des modèles
        try:
            # Lister tous les dossiers dans data/documents/types
            category_dirs = [d for d in os.listdir(self.models_path) 
                           if os.path.isdir(os.path.join(self.models_path, d))]
            
            # Ajouter les dossiers trouvés à la liste des types de documents
            for category in category_dirs:
                if category not in self.document_types:
                    self.document_types.append(category)
            
            # Trier la liste par ordre alphabétique pour une meilleure présentation
            self.document_types.sort()
            
            # Mettre à jour les catégories pour chaque type
            categories = {}
            for doc_type in self.document_types:
                # Chercher les modèles pour cette catégorie
                models = self._find_available_models(doc_type)
                if doc_type.lower() not in categories:
                    categories[doc_type.lower()] = []
                categories[doc_type.lower()] = models
            
            # Mettre à jour le cache interne
            self.categories = categories
            
            self.logger.info(f"Mise à jour des types de documents terminée: {len(self.document_types)} types trouvés")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour des types de documents: {e}")
            
            # Si une erreur survient, utiliser une liste par défaut
            self.document_types = [
                "Juridique", "Commercial", "Administratif",
                "Contrats", "Bancaires", "Immobiliers", "Autres"
            ]

    def _find_available_models(self, category):
        """
        Trouve les modèles disponibles pour une catégorie donnée dans data/documents/types.
        
        Args:
            category (str): La catégorie de document (ex: juridique, commercial)
            
        Returns:
            list: Liste des modèles disponibles
        """
        if not category:
            return []
            
        # Normaliser la catégorie pour la recherche
        category_normalized = self._normalize_input(category)
        
        # Vérifier si la catégorie existe dans les modèles disponibles
        available_models = []
        models_cache_key = f"models_{category_normalized}"
        
        # Utiliser le cache si disponible et récent (moins de 5 minutes)
        if models_cache_key in self.cache and time.time() - self.cache[models_cache_key]["timestamp"] < 300:
            return self.cache[models_cache_key]["models"]
        
        # Sinon, rechercher les modèles dans le dossier de la catégorie
        try:
            # Chemin vers le dossier de la catégorie
            category_path = os.path.join(self.models_path, category)
            
            # Vérifier si le dossier existe
            if os.path.exists(category_path) and os.path.isdir(category_path):
                # Lister uniquement les fichiers (pas les dossiers)
                for file_name in os.listdir(category_path):
                    file_path = os.path.join(category_path, file_name)
                    # Ne prendre que les fichiers avec extensions reconnues (.docx, .pdf, .txt, .rtf)
                    if os.path.isfile(file_path) and any(file_name.lower().endswith(ext) for ext in ['.docx', '.pdf', '.txt', '.rtf']):
                        available_models.append(file_name)
                
                self.logger.info(f"{len(available_models)} modèles trouvés pour la catégorie '{category}'")
            else:
                self.logger.warning(f"Le dossier '{category_path}' n'existe pas")
                
            # Si aucun modèle n'est trouvé, ajouter un exemple par défaut
            if not available_models:
                # Créer un exemple par défaut pour faciliter la démonstration
                try:
                    if not os.path.exists(category_path):
                        os.makedirs(category_path, exist_ok=True)
                        self.logger.info(f"Dossier '{category_path}' créé")
                    
                    example_file = os.path.join(category_path, f"Exemple_{category}.txt")
                    if not os.path.exists(example_file):
                        with open(example_file, "w", encoding="utf-8") as f:
                            f.write(f"Ceci est un exemple de document pour la catégorie {category}.\n")
                            f.write("Vous pouvez remplacer ce fichier par vos propres modèles.\n")
                        self.logger.info(f"Exemple créé: {example_file}")
                    
                    # Ajouter l'exemple à la liste
                    available_models.append(f"Exemple_{category}.txt")
                except Exception as e:
                    self.logger.error(f"Erreur lors de la création de l'exemple: {e}")
            
            # Mettre en cache les résultats
            self.cache[models_cache_key] = {
                "models": available_models,
                "timestamp": time.time()
            }
            
            return available_models
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche des modèles: {e}")
            return []

    def _suggest_existing_models(self, category, models):
        """
        Affiche les modèles existants et demande à l'utilisateur de choisir.
        
        Args:
            category (str): La catégorie de documents
            models (list): Liste des modèles disponibles
            
        Returns:
            str: Message de suggestion
        """
        # Formater la liste des modèles de manière plus claire
        model_list = "\n".join(f"{i+1}. {model}" for i, model in enumerate(models))
        return f"""📂 J'ai trouvé {len(models)} modèle(s) dans la catégorie {category} :

{model_list}

Que souhaitez-vous faire ?
1. Utiliser un modèle existant (tapez le numéro du modèle)
2. Créer un nouveau document (tapez 'nouveau')"""

    def _ask_for_category(self):
        """Demande à l'utilisateur de préciser le type de document."""
        if not self.categories:
            return "📌 Je ne trouve pas de catégories disponibles. Veuillez réessayer plus tard."
        
        categories_list = "\n".join(f"- {category}" for category in self.categories)
        return f"""📌 Voici les catégories disponibles :

{categories_list}

Quelle catégorie souhaitez-vous utiliser ?"""

    def _ask_for_theme(self, category):
        """Demande à l'utilisateur de choisir un thème dans la catégorie."""
        if category not in self.categories or not self.categories[category]:
            return f"📌 Je ne trouve pas de thèmes disponibles pour la catégorie {category}."
        
        themes_list = "\n".join(f"- {theme}" for theme in self.categories[category])
        return f"""📌 Voici les thèmes disponibles pour la catégorie {category} :

{themes_list}

Quel thème souhaitez-vous utiliser ?"""

    def _ask_for_specific_details(self, category, doc_type=None):
        """
        Demande des précisions spécifiques pour la création d'un document.
        
        Args:
            category (str): La catégorie de documents
            doc_type (str): Le type de document si connu
            
        Returns:
            str: Message demandant des précisions
        """
        if doc_type:
            return f"""📝 Je vais vous aider à créer un nouveau {doc_type} {category}.

Pour commencer, j'ai besoin de quelques informations :
1. Quel est le sujet principal de ce {doc_type} ?
2. Quelles sont les parties impliquées ?
3. Avez-vous des exigences particulières ?

Je peux vous guider dans la création de votre document étape par étape."""
        else:
            return f"""📝 Je vais vous aider à créer un nouveau document {category}.

Pour commencer, j'ai besoin de savoir :
1. Quel type de document souhaitez-vous créer ? (contrat, lettre, rapport...)
2. Quel est le sujet principal ?
3. Quelles sont les parties impliquées ?

Je peux vous guider dans la création de votre document étape par étape."""

    def generate_response(self, message, stream=False):
        """
        Génère une réponse à un message utilisateur
        
        Args:
            message: Message de l'utilisateur
            stream: Si True, renvoie un générateur de réponse par stream
        
        Returns:
            str ou generator: Réponse générée
        """
        print(f"DEBUG - generate_response appelé avec message: {message[:50]}...")
        
        if message.startswith('/'):
            command = message[1:].strip().split()[0].lower()
            if command in self.commands:
                return self.commands[command]()
            else:
                return f"Commande inconnue: {command}. Tapez /help pour voir les commandes disponibles."
        
        # Ajouter le message à l'historique
        self.conversation_history.append({"role": "user", "content": message})
        
        # Conserver seulement les 10 derniers messages pour éviter de dépasser le contexte
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        # Construire le prompt complet avec l'historique de conversation
        prompt = self._build_prompt(message)
        print(f"DEBUG - Prompt construit, longueur: {len(prompt)} caractères")
        
        # Paramètres pour l'appel à l'API
        params = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "num_predict": self.num_predict,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "repeat_penalty": self.repeat_penalty,
                "seed": self.seed,
                "num_thread": self.num_thread,
                "num_gpu": self.num_gpu,
                "stop": self.stop,
                "echo": self.echo
            }
        }
        
        # Vérifier que le modèle est disponible avant de faire la requête
        if not self._verify_model():
            error_msg = "Le modèle LLaMa n'est pas disponible. Vérifiez que Ollama est en cours d'exécution."
            self.logger.error(error_msg)
            print(f"ERREUR - {error_msg}")
            return error_msg
            
        try:
            print(f"DEBUG - Envoi de la requête à l'API Ollama ({self.api_url})")
            if stream:
                # Appel en streaming
                print(f"DEBUG - Mode streaming activé")
                response = requests.post(
                    self.api_url,
                    json=params,
                    timeout=self.timeout,
                    stream=True
                )
                
                if response.status_code != 200:
                    error_msg = f"Erreur API: {response.status_code} - {response.text}"
                    self.logger.error(error_msg)
                    print(f"ERREUR - {error_msg}")
                    return error_msg
                
                print(f"DEBUG - Réponse de streaming obtenue, code: {response.status_code}")
                return self._stream_response(response)
            else:
                # Appel normal
                print(f"DEBUG - Appel normal (non-streaming)")
                response = requests.post(
                    self.api_url,
                    json=params,
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    error_msg = f"Erreur API: {response.status_code} - {response.text}"
                    self.logger.error(error_msg)
                    print(f"ERREUR - {error_msg}")
                    return error_msg
                
                print(f"DEBUG - Réponse obtenue, code: {response.status_code}")
                result = response.json()
                ai_response = result.get("response", "")
                
                if not ai_response:
                    error_msg = "Réponse vide reçue de l'API Ollama"
                    self.logger.warning(error_msg)
                    print(f"AVERTISSEMENT - {error_msg}")
                    return "Le modèle n'a pas généré de réponse. Veuillez réessayer."
                
                # Ajouter la réponse à l'historique
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                
                print(f"DEBUG - Réponse finale longueur: {len(ai_response)} caractères")
                return ai_response
                
        except requests.exceptions.Timeout:
            error_msg = f"Délai d'attente dépassé (timeout: {self.timeout}s)"
            self.logger.error(error_msg)
            print(f"ERREUR - {error_msg}")
            return "La requête a pris trop de temps. L'API Ollama pourrait être surchargée."
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Erreur de connexion à l'API Ollama: {e}"
            self.logger.error(error_msg)
            print(f"ERREUR CRITIQUE - {error_msg}")
            return "Impossible de se connecter à l'API Ollama. Vérifiez que le service est en cours d'exécution."
        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur de requête à l'API: {e}"
            self.logger.error(error_msg)
            print(f"ERREUR - {error_msg}")
            return f"Erreur lors de la communication avec l'API: {str(e)}"
        except json.JSONDecodeError as e:
            error_msg = f"Erreur de décodage JSON: {e}"
            self.logger.error(error_msg)
            print(f"ERREUR - {error_msg}")
            return "Erreur lors du traitement de la réponse du serveur."
        except Exception as e:
            error_msg = f"Erreur inattendue: {e}"
            self.logger.error(error_msg)
            print(f"ERREUR CRITIQUE - {error_msg}")
            return f"Une erreur inattendue s'est produite: {str(e)}"
    
    def _build_prompt(self, message):
        """
        Construit le prompt complet à envoyer au modèle
        
        Args:
            message: Message de l'utilisateur
        
        Returns:
            str: Prompt complet
        """
        # Construire le prompt à partir de l'historique de conversation
        prompt = "<s>"
        
        # Parcourir l'historique de conversation
        for i, msg in enumerate(self.conversation_history):
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                prompt = f"<s>[INST] {content} [/INST]\n\n"
            elif role == "user":
                prompt += f"[INST] {content} [/INST]\n\n"
            else:  # assistant
                prompt += f"{content}\n\n"
        
        # Ajouter le nouveau message de l'utilisateur (qui n'est pas encore dans l'historique)
        prompt += f"[INST] {message} [/INST]\n\n"
        
        return prompt
    
    def _stream_response(self, response):
        """
        Traite une réponse en streaming
        
        Args:
            response: Réponse de l'API en streaming
        
        Returns:
            generator: Générateur de morceaux de réponse
        """
        ai_response = ""
        
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    text = chunk.get("response", "")
                    ai_response += text
                    yield text
                except json.JSONDecodeError:
                    continue
        
        # Ajouter la réponse complète à l'historique
        self.conversation_history.append({"role": "assistant", "content": ai_response})
    
    def _verify_model(self):
        """Vérifie si le modèle est disponible"""
        try:
            print(f"DEBUG - Vérification du modèle {self.model} via l'API Ollama")
            
            # Vérifier si l'API Ollama est accessible
            try:
                test_connection = requests.get("http://localhost:11434/api/version", timeout=5)
                if test_connection.status_code != 200:
                    self.logger.error(f"API Ollama non accessible: {test_connection.status_code}")
                    print(f"ERREUR - API Ollama non accessible: {test_connection.status_code}")
                    return False
                
                version_info = test_connection.json()
                version = version_info.get('version', 'inconnue')
                self.logger.info(f"Ollama API version: {version}")
                print(f"DEBUG - Ollama API version: {version}")
            except requests.exceptions.ConnectionError:
                self.logger.error("Impossible de se connecter à l'API Ollama (service non démarré?)")
                print("ERREUR CRITIQUE - Impossible de se connecter à l'API Ollama. Vérifiez que le service Ollama est démarré.")
                return False
            except Exception as e:
                self.logger.error(f"Erreur lors de la vérification de l'API Ollama: {e}")
                print(f"ERREUR - Erreur lors de la vérification de l'API Ollama: {e}")
                return False
            
            # Liste des modèles supportés et disponibles en fallback
            supported_models = ["llama3", "mistral", "phi3", "phi3:mini", "phi", "codellama"]
            
            # Essayer d'abord le modèle configuré
            try:
                response = requests.post(
                    "http://localhost:11434/api/show",
                    json={"name": self.model},
                    timeout=5
                )
                
                if response.status_code == 200:
                    model_info = response.json()
                    model_name = model_info.get('name', 'N/A')
                    model_size = model_info.get('size', 'N/A')
                    self.logger.info(f"Modèle {self.model} disponible: {model_name} ({model_size} taille)")
                    print(f"DEBUG - Modèle {self.model} disponible: {model_name}")
                    return True
                
                # Si le modèle spécifié n'est pas disponible, essayer des alternatives
                if response.status_code == 404:
                    self.logger.warning(f"Modèle {self.model} non trouvé, recherche d'alternatives...")
                    print(f"AVERTISSEMENT - Modèle {self.model} non trouvé, recherche d'alternatives...")
                    
                    # Obtenir la liste des modèles installés
                    installed_models = []
                    try:
                        list_response = requests.get("http://localhost:11434/api/tags", timeout=5)
                        if list_response.status_code == 200:
                            models_data = list_response.json()
                            installed_models = [model.get('name') for model in models_data.get('models', [])]
                            print(f"DEBUG - Modèles installés: {', '.join(installed_models)}")
                    except Exception as e:
                        print(f"AVERTISSEMENT - Impossible de lister les modèles: {e}")
                    
                    # Chercher une alternative parmi les modèles supportés
                    for alt_model in supported_models:
                        if alt_model in installed_models or alt_model == self.model:
                            continue  # Sauter le modèle courant ou déjà vérifié
                            
                        try:
                            alt_response = requests.post(
                                "http://localhost:11434/api/show",
                                json={"name": alt_model},
                                timeout=5
                            )
                            
                            if alt_response.status_code == 200:
                                # Mettre à jour le modèle
                                self.model = alt_model
                                alt_model_info = alt_response.json()
                                self.logger.info(f"Utilisation du modèle alternatif {alt_model}")
                                print(f"INFO - Utilisation du modèle alternatif {alt_model}")
                                return True
                        except Exception:
                            continue  # Passer au modèle suivant en cas d'erreur
                    
                    # Aucune alternative trouvée
                    self.logger.error("Aucun modèle LLM disponible")
                    print(f"ERREUR - Aucun modèle disponible. Installez un modèle avec 'ollama pull {self.model}'")
                    return False
                    
                else:
                    # Autre erreur
                    self.logger.warning(f"Modèle {self.model} non disponible: {response.text}")
                    print(f"ERREUR - Modèle {self.model} non disponible: {response.text}")
                    return False
                    
            except requests.exceptions.ConnectionError as e:
                self.logger.error(f"Erreur de connexion à l'API Ollama: {e}")
                print(f"ERREUR CRITIQUE - Impossible de se connecter à l'API Ollama: {e}")
                return False
            except Exception as e:
                self.logger.error(f"Erreur lors de la vérification du modèle: {e}")
                print(f"ERREUR - Vérification du modèle échouée: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors de la vérification du modèle: {e}")
            print(f"ERREUR CRITIQUE - Erreur inattendue lors de la vérification du modèle: {e}")
            return False
    
    # Commandes de l'interface de chat
    def _help_command(self):
        """Affiche l'aide des commandes disponibles"""
        return """
Commandes disponibles:
/help - Affiche cette aide
/clear - Efface l'historique de la conversation
/status - Affiche l'état du modèle
/model - Affiche les informations sur le modèle utilisé
"""
    
    def _clear_command(self):
        """Efface l'historique de la conversation"""
        self.conversation_history = []
        return "Historique de conversation effacé."
    
    def _status_command(self):
        """Affiche l'état du modèle"""
        return f"Modèle actif: {self.model}\nNombre de messages dans l'historique: {len(self.conversation_history)}"
    
    def _model_command(self):
        """Affiche les informations sur le modèle utilisé"""
        return f"Modèle: {self.model}\nTempérature: {self.temperature}\nMaximum de tokens: {self.max_tokens}"

    def _handle_simple_question(self, message):
        """
        Gère les questions simples et courantes sans passer par le modèle principal.
        
        Args:
            message (str): Le message de l'utilisateur
            
        Returns:
            str: La réponse si c'est une question simple
        """
        # Normaliser le message
        message = message.lower().strip()
        message = message.replace("?", "").replace("!", "").replace(",", "")
        
        # Vérifier l'état de la conversation
        if self.current_context["state"] == "greeting":
            if "cava" in message or "ça va" in message:
                self.current_context["state"] = "ready"
                return "Je vais très bien, merci ! Comment puis-je vous aider aujourd'hui ?"
        
        # Questions simples et leurs réponses
        simple_questions = {
            # Salutations
            "salut": "Bonjour ! Comment puis-je vous aider ?",
            "hey": "Bonjour ! Comment puis-je vous aider ?",
            "hi": "Bonjour ! Comment puis-je vous aider ?",
            "hello": "Bonjour ! Comment puis-je vous aider ?",
            "bonjour": "Bonjour ! Comment puis-je vous aider ?",
            
            # Comment ça va
            "ça va": "Oui, merci ! Comment puis-je vous aider ?",
            "cava": "Oui, merci ! Comment puis-je vous aider ?",
            "cavva": "Oui, merci ! Comment puis-je vous aider ?",
            "cv": "Oui, merci ! Comment puis-je vous aider ?",
            "comment cv": "Oui, merci ! Comment puis-je vous aider ?",
            "comment ça va": "Oui, merci ! Comment puis-je vous aider ?",
            "comment vas tu": "Oui, merci ! Comment puis-je vous aider ?",
            "comment allez vous": "Oui, merci ! Comment puis-je vous aider ?",
            
            # Remerciements
            "merci": "Je vous en prie !",
            "merci beaucoup": "Je vous en prie !",
            "thanks": "Je vous en prie !",
            "thank you": "Je vous en prie !",
            
            # Au revoir
            "au revoir": "Au revoir ! N'hésitez pas si vous avez d'autres questions.",
            "bye": "Au revoir ! N'hésitez pas si vous avez d'autres questions.",
            "goodbye": "Au revoir ! N'hésitez pas si vous avez d'autres questions.",
            "a plus": "Au revoir ! N'hésitez pas si vous avez d'autres questions.",
            "a bientot": "Au revoir ! N'hésitez pas si vous avez d'autres questions."
        }
        
        # Vérifier si le message correspond à une question simple
        for question, response in simple_questions.items():
            if question in message or message in question:
                return response
        
        # Vérifier les variations avec des espaces et les combinaisons
        words = message.split()
        for word in words:
            if word in simple_questions:
                return simple_questions[word]
        
        # Vérifier les combinaisons de questions simples
        if any(word in message for word in ["salut", "bonjour", "hey", "hi", "hello"]) and \
           any(word in message for word in ["cava", "cv", "cavva", "ça va", "comment"]):
            return "Bonjour ! Je vais très bien, merci ! Comment puis-je vous aider ?"
        
        return None
    
    def _get_technical_default_response(self, message):
        """
        Génère une réponse par défaut pour les questions techniques.
        
        Args:
            message (str): Le message de l'utilisateur
            
        Returns:
            str: Une réponse appropriée
        """
        message = message.lower()
        
        if "contrat" in message:
            return """Je peux vous aider à créer un contrat. Pour commencer, j'ai besoin de quelques informations :
1. Quel type de contrat souhaitez-vous créer ? (ex: commercial, de travail, de location)
2. Avez-vous déjà un modèle de base ou souhaitez-vous en créer un nouveau ?
3. Quelles sont les parties impliquées dans ce contrat ?

Je peux vous guider dans la création de votre contrat étape par étape."""
            
        elif "proposition" in message:
            return """Je peux vous aider à rédiger une proposition commerciale. Pour vous aider au mieux, j'ai besoin de savoir :
1. Quel type de proposition souhaitez-vous créer ?
2. Avez-vous déjà un modèle existant ?
3. Quels sont les éléments clés à inclure dans cette proposition ?

Je peux vous aider à structurer votre proposition de manière professionnelle."""
            
        elif "document" in message:
            return """Je peux vous aider à créer ou gérer des documents. Pour mieux vous aider, pourriez-vous préciser :
1. Quel type de document souhaitez-vous créer ?
2. Avez-vous déjà un modèle existant ?
3. Quelles sont les informations principales à inclure ?

Je peux vous guider dans la création de votre document."""
            
        else:
            return """Je peux vous aider à créer et gérer des documents. Pour commencer, j'ai besoin de savoir :
1. Quel type de document souhaitez-vous créer ?
2. Avez-vous déjà un modèle existant ?
3. Quelles sont vos exigences spécifiques ?

Je peux vous guider dans la création de votre document étape par étape."""

    def generate_contract(self, contract_type, details=None):
        """
        Génère directement un contrat avec des valeurs par défaut.
        
        Args:
            contract_type (str): Type de contrat à générer
            details (dict): Détails optionnels pour personnaliser le contrat
            
        Returns:
            str: Le contrat généré
        """
        # Valeurs par défaut
        default_details = {
            "date": "DATE DU JOUR",
            "parties": {
                "client": "NOM DU CLIENT",
                "fournisseur": "NOM DE L'ENTREPRISE"
            },
            "montant": "MONTANT À DÉFINIR",
            "duree": "DURÉE À DÉFINIR",
            "garantie": "12 mois",
            "conditions": "Conditions standard",
            "signatures": "SIGNATURES"
        }
        
        # Mettre à jour avec les détails fournis
        if details:
            default_details.update(details)
        
        # Préparer le prompt pour la génération
        prompt = f"""Génère un contrat de {contract_type} professionnel en français avec les informations suivantes :

Type de contrat : {contract_type}
Date : {default_details['date']}
Client : {default_details['parties']['client']}
Fournisseur : {default_details['parties']['fournisseur']}
Montant : {default_details['montant']}
Durée : {default_details['duree']}
Garantie : {default_details['garantie']}
Conditions : {default_details['conditions']}

Instructions :
1. Génère un contrat complet et professionnel
2. Utilise un langage juridique approprié
3. Inclus toutes les clauses nécessaires
4. Structure le document de manière claire
5. Ajoute des espaces pour les signatures

Format de sortie souhaité :
- Titre en majuscules
- Sections numérotées
- Clauses détaillées
- Espaces pour les signatures
"""
        
        # Préparer la requête pour Ollama
        params = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": self.num_predict,
                "num_ctx": self.num_ctx,
                "repeat_penalty": 1.1,
                "seed": self.seed,
                "num_thread": self.num_thread,
                "num_gpu": self.num_gpu,
                "stop": self.stop,
                "echo": self.echo
            }
        }

        try:
            # Envoyer la requête à Ollama
            response = requests.post(self.api_url, json=params, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                if "response" in result:
                    return self._clean_response(result["response"])
                return "Erreur : Format de réponse invalide"
            else:
                return f"Erreur : Impossible de générer le contrat. Code d'erreur : {response.status_code}"

        except Exception as e:
            return f"Erreur lors de la génération du contrat : {str(e)}"

    def _normalize_input(self, text):
        """
        Normalise le texte d'entrée pour une meilleure tolérance aux erreurs.
        
        Args:
            text (str): Le texte à normaliser
            
        Returns:
            str: Le texte normalisé
        """
        if not text:
            return ""
            
        # Convertir en minuscules et supprimer les espaces superflus
        text = text.lower().strip()
        
        # Gestion immédiate des cas spéciaux très courants pour les entrées numériques
        # Ces vérifications doivent être prioritaires pour éviter les problèmes de normalisation
        if text == "1" or text == "1." or text == "un" or text == "option 1":
            return "1"
        elif text == "2" or text == "2." or text == "deux" or text == "option 2":
            return "2"
        elif text == "3" or text == "3." or text == "trois" or text == "option 3":
            return "3"
        elif text in ["oui", "yes", "ouai", "ok", "bien", "bien sûr", "d'accord"]:
            return "oui"
        elif text in ["non", "no", "nope", "pas maintenant"]:
            return "non"
        
        # Pour les phrases plus longues qui concernent un aperçu
        if "voir un aperçu" in text or "aperçu du document" in text:
            return "3"
        
        # Pour les phrases concernant l'utilisation d'un document tel quel
        if "utiliser tel quel" in text or "utiliser le document" in text:
            return "2"
        
        # Pour les phrases concernant le remplissage d'un document avec des informations
        if "remplir" in text or "remplir avec des informations" in text:
            return "1"
        
        # Dictionnaire des corrections courantes
        corrections = {
            # Accents et caractères spéciaux
            'é': 'e', 'è': 'e', 'ê': 'e',
            'à': 'a', 'â': 'a',
            'î': 'i', 'ï': 'i',
            'ô': 'o', 'ö': 'o',
            'û': 'u', 'ü': 'u',
            'ç': 'c',
            
            # Choix d'options
            '1': '1',
            'un': '1',
            'premier': '1',
            'option 1': '1',
            
            '2': '2',
            'deux': '2',
            'deuxieme': '2',
            'deuxième': '2',
            'option 2': '2',
            
            '3': '3',
            'trois': '3',
            'troisieme': '3',
            'troisième': '3',
            'option 3': '3',
            
            # Erreurs de frappe courantes
            'model': 'modele',
            'models': 'modele',
            'template': 'modele',
            'templates': 'modele',
            'oui': 'oui',
            'non': 'non',
            'modif': 'modifier',
            'edit': 'modifier',
            'use': 'utiliser',
            'apply': 'utiliser',
            'autre': 'autre',
            'ret': 'retour',
            'back': 'retour',
            'cancel': 'annuler',
            
            # Variations de réponses
            'existant': 'modele',
            'existante': 'modele',
            'existent': 'modele',
            'exiastnt': 'modele',
            'exiastnte': 'modele',
            'exisan': 'modele',
            'modèle': 'modele',
            'model': 'modele',
            'modl': 'modele',
            'models': 'modele',
            'modls': 'modele',
            'modle': 'modele',
            'mdl': 'modele',
            'modéle': 'modele',
            
            # Variations pour nouveau
            'nouvo': 'nouveau',
            'nouveaux': 'nouveau',
            'noueau': 'nouveau',
            'nv': 'nouveau',
            'nvx': 'nouveau',
            'neuf': 'nouveau',
            'create': 'nouveau',
            'creer': 'nouveau',
            'créer': 'nouveau',
            'cr': 'nouveau',
            'nouveau': 'nouveau',
            'new': 'nouveau',
            
            # Variations de contrats
            'contrat': 'contrat',
            'conrat': 'contrat',
            'contra': 'contrat',
            'contart': 'contrat',
            'accord': 'contrat',
            'convention': 'contrat',
            
            # Variations de lettres
            'lettre': 'lettre',
            'letre': 'lettre',
            'letr': 'lettre',
            'lttre': 'lettre',
            'courrier': 'lettre',
            'mail': 'lettre',
            
            # Variations de rapports
            'rapport': 'rapport',
            'raport': 'rapport',
            'rapor': 'rapport',
            'rport': 'rapport',
            'compte-rendu': 'rapport',
            'compterendu': 'rapport',
            'bilan': 'rapport',
            
            # Catégories
            'juridique': 'juridique',
            'jurid': 'juridique',
            'juri': 'juridique',
            'legal': 'juridique',
            'droit': 'juridique',
            
            'commercial': 'commercial',
            'comm': 'commercial',
            'com': 'commercial',
            'vente': 'commercial',
            'marketing': 'commercial',
            
            'administratif': 'administratif',
            'admin': 'administratif',
            'administration': 'administratif',
            'paperasse': 'administratif',
            
            'ressources humaines': 'ressources humaines',
            'ressource': 'ressources humaines',
            'humain': 'ressources humaines',
            'rh': 'ressources humaines',
            'personnel': 'ressources humaines',
            
            'fiscal': 'fiscales',
            'fiscales': 'fiscales',
            'fisc': 'fiscales',
            'impot': 'fiscales',
            'taxe': 'fiscales',
            'impôt': 'fiscales',
            'taxes': 'fiscales',
            
            'correspondance': 'correspondances',
            'correspondances': 'correspondances',
            'lettre': 'correspondances',
            'courrier': 'correspondances',
            'message': 'correspondances',
            
            'bancaire': 'bancaires',
            'bancaires': 'bancaires',
            'banque': 'bancaires',
            'finance': 'bancaires',
            'financier': 'bancaires',
            
            'corporate': 'corporate',
            'entreprise': 'corporate',
            'societe': 'corporate',
            'société': 'corporate',
            
            'immobilier': 'immobiliers',
            'immobiliers': 'immobiliers',
            'immo': 'immobiliers',
            'propriete': 'immobiliers',
            'propriété': 'immobiliers',
            
            'autre': 'autres',
            'autres': 'autres',
            'divers': 'autres',
            'autre chose': 'autres'
        }
        
        # Chercher d'abord une correspondance exacte
        if text in corrections:
            return corrections[text]
            
        # Ensuite chercher des correspondances partielles
        normalized_text = text
        for old, new in corrections.items():
            if old in text:
                normalized_text = normalized_text.replace(old, new)
                
        # Si le texte normalisé est différent, il y a eu au moins une correction
        if normalized_text != text:
            return normalized_text
        
        # Si aucune correction n'a été appliquée, on supprime juste les caractères spéciaux
        return ''.join(c for c in text if c.isalnum() or c.isspace())

    def _correct_typo(self, user_input, valid_choices):
        """
        Corrige les fautes de frappe dans l'entrée utilisateur.
        
        Args:
            user_input (str): L'entrée de l'utilisateur
            valid_choices (list): Liste des choix valides
            
        Returns:
            str: Le choix corrigé ou l'entrée originale si aucune correction n'est possible
        """
        normalized_input = self._normalize_input(user_input)
        normalized_choices = {self._normalize_input(choice): choice for choice in valid_choices}
        
        # Vérifier si l'entrée normalisée correspond exactement à un choix
        if normalized_input in normalized_choices:
            return normalized_choices[normalized_input]
        
        # Chercher la meilleure correspondance avec un seuil plus bas pour plus de tolérance
        best_match = difflib.get_close_matches(normalized_input, normalized_choices.keys(), n=1, cutoff=0.5)
        if best_match:
            return normalized_choices[best_match[0]]
        
        # Si aucune correspondance n'est trouvée, essayer de trouver une correspondance partielle
        for choice in normalized_choices:
            if normalized_input in choice or choice in normalized_input:
                return normalized_choices[choice]
        
        return user_input

    def _handle_document_request(self, message: str) -> str:
        """
        Gère une demande de document de manière plus intuitive et robuste.
        
        Args:
            message (str): Le message de l'utilisateur
            
        Returns:
            str: La réponse de l'IA
        """
        # Extraire le type de document si présent
        doc_type, doc_category, doc_theme = self._extract_document_info(message)
        
        # Mettre à jour les informations du contexte sans écraser les valeurs existantes
        if doc_type:
            self.current_context["document_type"] = doc_type
        
        # Si une catégorie est spécifiée, la stocker
        if doc_category:
            self.current_context["category"] = doc_category
            
        # Mettre à jour l'état et la dernière action
        self.current_context["last_action"] = "demande_document"
        self.current_context["state"] = "asking_document_type"
        
        # Mettre à jour l'historique de conversation pour que cette demande soit bien traitée
        self.conversation_history.append({
            "role": "assistant",
            "content": """📌 Que souhaitez-vous faire ?

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document

Veuillez choisir une option en tapant 1 ou 2."""
        })
        
        # Retourner le message initial avec une mise en forme claire
        return """📌 Que souhaitez-vous faire ?

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document

Veuillez choisir une option en tapant 1 ou 2."""

    def _handle_user_choice(self, user_input):
        """
        Gère le choix de l'utilisateur pour le type de document avec une meilleure tolérance aux erreurs.
        
        Args:
            user_input (str): L'entrée de l'utilisateur
            
        Returns:
            str: La réponse appropriée
        """
        # Si pas d'entrée, demander de nouveau
        if not user_input or len(user_input.strip()) < 1:
            return """📌 Je n'ai pas compris votre choix.

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document

Veuillez choisir une option en tapant 1 ou 2."""
            
        # Normaliser l'entrée pour gérer les variations et fautes de frappe
        normalized_input = self._normalize_input(user_input)
        
        # Vérifier l'état actuel de la conversation pour déterminer l'étape
        current_state = self.current_context.get("state", "initial")
        
        # --- GESTION DES RETOURS EN ARRIÈRE ---
        if normalized_input in ["retour", "back", "arriere", "annuler", "cancel"]:
            # Retour en fonction de l'état actuel
            if current_state == "choosing_model":
                # Retour à la sélection de catégorie
                self.current_context["state"] = "choosing_category"
                return self._show_available_categories()
            elif current_state == "choosing_category":
                # Retour à la sélection initiale
                self.current_context["state"] = "asking_document_type"
                return self._handle_document_request("document")
            elif current_state == "model_selected":
                # Retour à la sélection de modèle
                self.current_context["state"] = "choosing_model"
                category = self.current_context.get("category", "")
                return self._show_available_models(category)
            else:
                # Par défaut, retour à l'état initial
                self.current_context["state"] = "initial"
                self.current_context["last_action"] = "retour_menu_principal"
                return "📌 Que puis-je faire pour vous ?"
        
        # --- ÉTAPE 1: CHOIX ENTRE MODÈLE EXISTANT OU NOUVEAU DOCUMENT ---
        if current_state == "asking_document_type":
            # Option 1: Utiliser un modèle existant - traiter spécifiquement le "1" et équivalents
            if normalized_input == "1" or normalized_input == "modele" or normalized_input == "existant":
                self.current_context["state"] = "choosing_category"
                self.current_context["last_action"] = "choix_modele_existant"
                return self._show_available_categories()
            
            # Option 2: Créer un nouveau document - traiter spécifiquement le "2" et équivalents
            elif normalized_input == "2" or normalized_input == "nouveau" or normalized_input == "creer":
                self.current_context["state"] = "new_document"
                self.current_context["last_action"] = "choix_nouveau_document"
                
                # Vérifier si la méthode _ask_for_category existe, sinon utiliser _ask_for_new_document_details
                if hasattr(self, '_ask_for_category'):
                    return self._ask_for_category()
                else:
                    return self._ask_for_new_document_details(None, None)
            
            # Si l'entrée n'est pas reconnue, suggérer des options
            return """❓ Je ne comprends pas votre choix. Veuillez réessayer en tapant :

1️⃣ ou "modèle" pour utiliser un modèle existant
2️⃣ ou "nouveau" pour créer un nouveau document"""
        
        # --- ÉTAPE 2: CHOIX DE LA CATÉGORIE ---
        elif current_state == "choosing_category":
            return self._handle_category_selection(user_input)
        
        # --- ÉTAPE 3: CHOIX DU MODÈLE DANS UNE CATÉGORIE ---
        elif current_state == "choosing_model":
            return self._handle_model_selection(user_input)
        
        # --- ÉTAPE 4: ACTIONS POUR LE MODÈLE SÉLECTIONNÉ ---
        elif current_state == "model_selected":
            return self._handle_model_actions(user_input)
        
        # --- ÉTAPE 5: CRÉATION D'UN NOUVEAU DOCUMENT ---
        elif current_state == "new_document":
            # Vérifier si une catégorie a déjà été choisie
            if self.current_context.get("category"):
                doc_type = self.current_context.get("document_type")
                return self._ask_for_new_document_details(
                    self.current_context["category"], 
                    doc_type
                )
            else:
                # Si pas de catégorie, on la demande
                return self._handle_category_selection(user_input)
        
        # --- PAR DÉFAUT: RÉPONSE SI ÉTAT NON RECONNU ---
        return """❓ Je ne suis pas sûr de comprendre votre demande. Que souhaitez-vous faire ?

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document

Ou tapez 'retour' pour revenir au menu principal."""

    def _handle_category_selection(self, message):
        """
        Gère la sélection d'une catégorie par l'utilisateur avec meilleure tolérance aux erreurs.
        
        Args:
            message (str): Le message de l'utilisateur
            
        Returns:
            str: La réponse appropriée
        """
        # Normaliser l'entrée
        normalized_input = self._normalize_input(message)
        
        # Mettre à jour last_action
        self.current_context["last_action"] = "selection_categorie"
        
        # Vérifier si l'utilisateur veut revenir en arrière
        if normalized_input in ["retour", "back", "arriere", "annuler", "cancel"]:
            self.current_context["state"] = "asking_document_type"
            return self._handle_document_request("document")
        
        # Vérifier si l'utilisateur a tapé un numéro
        try:
            # Tentative de conversion en entier
            index = int(normalized_input) - 1
            if 0 <= index < len(self.document_types):
                category = self.document_types[index].lower()
                self.current_context["category"] = category
                self.current_context["state"] = "choosing_model"
                return self._show_available_models(category)
            else:
                # Numéro hors limites
                return f"""❌ Numéro de catégorie invalide.

Veuillez choisir un numéro entre 1 et {len(self.document_types)}, ou taper le nom de la catégorie.
Ou tapez 'retour' pour revenir au menu précédent."""
                
        except ValueError:
            # Si ce n'est pas un numéro, recherche par nom avec correction
            
            # Créer une liste des noms normalisés pour la recherche
            normalized_categories = [self._normalize_input(cat) for cat in self.document_types]
            
            # 1. Vérifier la correspondance exacte
            if normalized_input in normalized_categories:
                index = normalized_categories.index(normalized_input)
                category = self.document_types[index].lower()
                self.current_context["category"] = category
                self.current_context["state"] = "choosing_model"
                return self._show_available_models(category)
            
            # 2. Vérifier si le terme est contenu dans un nom de catégorie
            matching_categories = []
            for i, cat in enumerate(normalized_categories):
                if normalized_input in cat or cat in normalized_input:
                    matching_categories.append((i, self.document_types[i]))
            
            # Si une seule correspondance trouvée, la sélectionner
            if len(matching_categories) == 1:
                category = matching_categories[0][1].lower()
                self.current_context["category"] = category
                self.current_context["state"] = "choosing_model"
                return self._show_available_models(category)
            
            # Si plusieurs correspondances, proposer les options
            elif len(matching_categories) > 1:
                options = "\n".join([f"{i+1}. {cat}" for i, (_, cat) in enumerate(matching_categories)])
                return f"""J'ai trouvé plusieurs catégories qui correspondent à "{message}":

{options}

Veuillez choisir un numéro, ou tapez 'retour'."""
            
            # 3. Utiliser la correction des fautes
            corrected_category = self._correct_typo(normalized_input, self.document_types)
            if corrected_category in self.document_types:
                # Suggérer la correction
                return f"""Voulez-vous dire "{corrected_category}" ? 

Tapez "oui" pour confirmer, ou choisissez parmi :
{chr(10).join([f"{i+1}️⃣ {cat}" for i, cat in enumerate(self.document_types)])}"""
        
        # Si aucune correspondance n'est trouvée
        return f"""❌ Type de document non reconnu.

Veuillez choisir parmi :
{chr(10).join([f"{i+1}️⃣ {cat}" for i, cat in enumerate(self.document_types)])}

Ou tapez 'retour' pour revenir au menu précédent."""

    def _handle_model_selection(self, message):
        """
        Gère la sélection d'un document par l'utilisateur parmi ceux disponibles
        dans l'onglet Modèles.
        
        Args:
            message (str): Le message de l'utilisateur
            
        Returns:
            str: La réponse appropriée
        """
        # Normaliser l'entrée
        normalized_input = self._normalize_input(message)
        
        # Mettre à jour last_action
        self.current_context["last_action"] = "selection_modele"
        
        # Vérifier si l'utilisateur veut revenir en arrière
        if normalized_input in ["retour", "back", "arriere", "annuler", "cancel"]:
            self.current_context["state"] = "choosing_category"
            return self._show_available_categories()
        
        # Vérifier si l'utilisateur a confirmé une suggestion
        if normalized_input in ["oui", "yes", "ouai", "ok", "d'accord", "daccord"]:
            # Si nous avions proposé une correction et que l'utilisateur l'a confirmée
            if self.current_context.get("suggested_model"):
                selected_model = self.current_context["suggested_model"]
                self.current_context["model"] = selected_model
                self.current_context["state"] = "model_selected"
                # Effacer la suggestion après utilisation
                self.current_context.pop("suggested_model", None)
                
                # Construire le chemin complet du document sélectionné
                category = self.current_context.get("category", "")
                model_path = os.path.join(self.models_path, category, selected_model)
                
                return f"""✅ Vous avez choisi le document "{selected_model}".

📂 Chemin: {model_path}

Que souhaitez-vous faire maintenant ?
1️⃣ Remplir le document avec des informations spécifiques
2️⃣ Utiliser le document tel quel
3️⃣ Voir un aperçu du document"""
        
        # Vérifier la catégorie actuelle
        category = self.current_context.get("category")
        if not category:
            self.current_context["state"] = "choosing_category"
            return self._show_available_categories()
        
        # Récupérer les modèles disponibles directement depuis le dossier
        models = self._find_available_models(category)
        
        # Option pour créer un nouveau modèle
        create_new_option = "Créer un nouveau modèle"
        models_with_custom = models.copy()
        if create_new_option not in models:
            models_with_custom.append(create_new_option)
        
        # Si aucun modèle n'est disponible
        if not models:
            return f"""❌ Aucun document n'est disponible dans le dossier "{category}".

Souhaitez-vous :
1️⃣ Choisir un autre type de document
2️⃣ Créer un nouveau document dans cette catégorie

Ou tapez 'retour' pour revenir au menu précédent."""
        
        # Vérifier si l'utilisateur a choisi l'option "Créer un nouveau modèle"
        if normalized_input in ["nouveau", "creer", "créer", "new"] or \
           normalized_input == self._normalize_input(create_new_option) or \
           message == str(len(models_with_custom)):
            self.current_context["state"] = "new_document"
            return self._ask_for_new_document_details(category, None)
        
        # Vérifier si l'utilisateur a tapé un numéro
        try:
            index = int(normalized_input) - 1
            if 0 <= index < len(models_with_custom):
                selected_model = models_with_custom[index]
                
                # Si c'est l'option de création de nouveau document
                if selected_model == create_new_option:
                    self.current_context["state"] = "new_document"
                    return self._ask_for_new_document_details(category, None)
                
                # Sinon, c'est un modèle existant
                self.current_context["model"] = selected_model
                self.current_context["state"] = "model_selected"
                
                # Construire le chemin complet du document sélectionné
                model_path = os.path.join(self.models_path, category, selected_model)
                
                return f"""✅ Vous avez choisi le document "{selected_model}".

📂 Chemin: {model_path}

Que souhaitez-vous faire maintenant ?
1️⃣ Remplir le document avec des informations spécifiques
2️⃣ Utiliser le document tel quel
3️⃣ Voir un aperçu du document"""
            else:
                return f"""❌ Numéro de document invalide.

Veuillez choisir un numéro entre 1 et {len(models_with_custom)}.
Ou tapez 'retour' pour revenir au menu précédent."""
                
        except ValueError:
            # Si ce n'est pas un numéro, recherche par nom
            
            # 1. Vérifier les correspondances partielles
            matching_models = []
            for i, model in enumerate(models_with_custom):
                model_lower = model.lower()
                if normalized_input in model_lower or any(term in model_lower for term in normalized_input.split()):
                    matching_models.append((i, model))
            
            # Si une seule correspondance trouvée, la sélectionner
            if len(matching_models) == 1:
                selected_model = matching_models[0][1]
                
                # Si c'est l'option de création de nouveau document
                if selected_model == create_new_option:
                    self.current_context["state"] = "new_document"
                    return self._ask_for_new_document_details(category, None)
                
                # Sinon, c'est un modèle existant
                self.current_context["model"] = selected_model
                self.current_context["state"] = "model_selected"
                
                # Construire le chemin complet du document sélectionné
                model_path = os.path.join(self.models_path, category, selected_model)
                
                return f"""✅ Vous avez choisi le document "{selected_model}".

📂 Chemin: {model_path}

Que souhaitez-vous faire maintenant ?
1️⃣ Remplir le document avec des informations spécifiques
2️⃣ Utiliser le document tel quel
3️⃣ Voir un aperçu du document"""
            
            # Si plusieurs correspondances, proposer les options
            elif len(matching_models) > 1:
                options = "\n".join([f"{i+1}️⃣ {model}" for i, (_, model) in enumerate(matching_models)])
                return f"""📌 J'ai trouvé plusieurs documents qui correspondent à "{message}":

{options}

Veuillez choisir un numéro, ou tapez 'retour'."""
            
            # 2. Utiliser la correction des fautes de frappe
            corrected_model = self._correct_typo(normalized_input, models_with_custom)
            if corrected_model in models_with_custom:
                # Stocker la suggestion pour confirmation
                self.current_context["suggested_model"] = corrected_model
                
                return f"""📝 Voulez-vous dire "{corrected_model}" ? 

Tapez "oui" pour confirmer, ou choisissez parmi :
{chr(10).join([f"{i+1}️⃣ {model}" for i, model in enumerate(models_with_custom)])}"""
        
        # Si aucune correspondance n'est trouvée
        return f"""❌ Document non trouvé. 

Veuillez choisir parmi :
{chr(10).join([f"{i+1}️⃣ {model}" for i, model in enumerate(models_with_custom)])}

Ou tapez 'retour' pour revenir à la liste des types de documents."""

    def _show_available_categories(self):
        """
        Affiche les types de documents disponibles dans l'onglet Types.
        
        Returns:
            str: Message formaté avec les catégories
        """
        # Vérifier si le dossier de modèles existe
        if not os.path.exists(self.models_path):
            os.makedirs(self.models_path, exist_ok=True)
            self.logger.info(f"Répertoire '{self.models_path}' créé")
            
        # Mettre à jour les catégories disponibles
        self._update_available_models()
        
        # Liste des catégories (dossiers de types de documents)
        categories = []
        
        # Parcourir les dossiers physiques dans data/documents/types
        try:
            # Obtenir la liste des dossiers (catégories)
            category_dirs = [d for d in os.listdir(self.models_path) 
                            if os.path.isdir(os.path.join(self.models_path, d))]
            
            # Si aucune catégorie n'est trouvée
            if not category_dirs:
                return """📂 Aucun type de document n'a été trouvé.

Pour ajouter des types de documents, veuillez créer des dossiers dans le répertoire:
data/documents/types/

Exemples:
- data/documents/types/Juridique
- data/documents/types/Commercial
- data/documents/types/Administratif"""
            
            # Formater la liste des catégories
            for i, category in enumerate(category_dirs):
                # Obtenir le nombre de modèles dans cette catégorie
                model_count = len(self._find_available_models(category))
                emoji = self._get_category_emoji(category)
                description = self._get_category_description(category)
                
                # Ajouter à la liste avec formatage
                categories.append(f"{i+1}️⃣ {emoji} **{category}** - {description} ({model_count} modèles)")
            
            # Construire le message final
            return f"""📂 Types de documents disponibles dans l'onglet Types :

{chr(10).join(categories)}

Veuillez choisir une catégorie en tapant son numéro ou son nom.
Ou tapez 'retour' pour revenir au menu précédent."""
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des catégories: {e}")
            return """❌ Une erreur s'est produite lors de la récupération des types de documents.

Veuillez vérifier que le répertoire data/documents/types existe et est accessible.
Vous pouvez taper 'retour' pour revenir au menu précédent."""

    def _get_category_emoji(self, category):
        """
        Retourne l'emoji approprié pour une catégorie.
        
        Args:
            category (str): La catégorie
            
        Returns:
            str: L'emoji correspondant
        """
        emojis = {
            "juridique": "⚖️",
            "commercial": "💼",
            "administratif": "📋",
            "fiscal": "💰",
            "rh": "👥",
            "ressources humaines": "👥",
            "bancaire": "🏦",
            "bancaires": "🏦",
            "immobilier": "🏢",
            "immobiliers": "🏢",
            "technique": "🔧",
            "marketing": "📢",
            "corporate": "🏛️",
            "correspondances": "✉️",
            "contrat": "📜",
            "contrats": "📜",
            "autre": "📄",
            "autres": "📄"
        }
        return emojis.get(category.lower(), "📄")

    def _get_category_description(self, category):
        """
        Retourne une description courte pour une catégorie.
        
        Args:
            category (str): La catégorie
            
        Returns:
            str: La description de la catégorie
        """
        descriptions = {
            "juridique": "Contrats, conventions et documents légaux",
            "commercial": "Devis, propositions et documents commerciaux",
            "administratif": "Lettres, rapports et documents administratifs",
            "fiscal": "Documents fiscaux et comptables",
            "fiscales": "Documents fiscaux et comptables",
            "rh": "Documents liés aux ressources humaines",
            "ressources humaines": "Documents liés aux ressources humaines",
            "bancaire": "Documents bancaires et financiers",
            "bancaires": "Documents bancaires et financiers", 
            "immobilier": "Documents liés à l'immobilier",
            "immobiliers": "Documents liés à l'immobilier",
            "technique": "Documents techniques et spécifications",
            "marketing": "Documents marketing et communication",
            "corporate": "Documents d'entreprise et corporate",
            "correspondances": "Lettres et correspondances professionnelles",
            "contrat": "Contrats et accords",
            "contrats": "Contrats et accords",
            "autre": "Documents divers",
            "autres": "Documents divers"
        }
        return descriptions.get(category.lower(), "Documents divers")

    def _show_available_models(self, category):
        """
        Affiche les modèles disponibles dans la catégorie sélectionnée.
        
        Args:
            category (str): La catégorie sélectionnée
            
        Returns:
            str: La liste des modèles disponibles avec formatage amélioré
        """
        # Vérifier si la catégorie est valide
        if not category:
            return "❌ Erreur: Catégorie non spécifiée. Veuillez choisir une catégorie."
            
        # Mettre à jour le contexte
        self.current_context["state"] = "choosing_model"
        self.current_context["last_action"] = "affichage_modeles"
        self.current_context["category"] = category
        
        # Trouver les modèles disponibles directement depuis le dossier
        models = self._find_available_models(category)
        
        # Si aucun modèle n'est disponible
        if not models:
            return f"""❌ Aucun modèle n'est disponible dans la catégorie "{category}".

Souhaitez-vous :
1️⃣ Choisir une autre catégorie
2️⃣ Créer un nouveau document dans cette catégorie

Ou tapez 'retour' pour revenir au menu précédent."""
        
        # Ajouter une option pour créer un nouveau modèle personnalisé
        models_with_custom = models.copy()
        models_with_custom.append("Créer un nouveau modèle")
        
        # Formater la liste des modèles avec numéros et icônes
        models_list = []
        for i, model in enumerate(models_with_custom):
            # Obtenir l'extension du fichier pour choisir l'emoji approprié
            if i == len(models_with_custom) - 1:
                # Option pour créer un nouveau modèle
                emoji = "✏️"
            else:
                # Déterminer l'emoji en fonction de l'extension
                if model.lower().endswith('.docx'):
                    emoji = "📝"
                elif model.lower().endswith('.pdf'):
                    emoji = "📄"
                elif model.lower().endswith('.txt'):
                    emoji = "📋"
                elif model.lower().endswith('.rtf'):
                    emoji = "📃"
                else:
                    emoji = "📄"
            
            models_list.append(f"{i+1}️⃣ {emoji} {model}")
        
        # Préparer le message avec la catégorie et la présentation
        category_emoji = self._get_category_emoji(category)
        category_path = os.path.join(self.models_path, category)
        
        return f"""📜 Documents disponibles dans le dossier "{category}" {category_emoji} :

{chr(10).join(models_list)}

📂 Chemin: {category_path}

Veuillez choisir un document en tapant son numéro ou son nom.
Ou tapez 'retour' pour revenir à la liste des types de documents."""

    def _handle_model_actions(self, message):
        """
        Gère les actions possibles après qu'un document a été sélectionné.
        
        Args:
            message (str): Le message de l'utilisateur
            
        Returns:
            str: La réponse appropriée
        """
        # Normaliser l'entrée pour la recherche
        normalized_input = self._normalize_input(message)
        
        # Variables du contexte actuelles
        category = self.current_context.get("category", "")
        selected_model = self.current_context.get("model", "")
        last_action = self.current_context.get("last_action", "")
        
        # Vérifier que le modèle et la catégorie sont définis
        if not category or not selected_model:
            self.current_context["state"] = "choosing_category"
            return self._show_available_categories()
        
        # Chemin complet vers le document
        model_path = os.path.join(self.models_path, category, selected_model)
        
        # Vérifier si l'utilisateur confirme l'ouverture du document après "Utiliser tel quel"
        if last_action == "utiliser_document" and normalized_input in ["oui", "yes", "ok", "bien", "d'accord", "ouai"]:
            return f"""✅ J'ouvre le document "{selected_model}" pour vous.

📂 Vous pouvez le trouver à: {model_path}

Avez-vous besoin d'autre chose ?"""
        
        # Vérifier si l'utilisateur refuse l'ouverture du document
        if last_action == "utiliser_document" and normalized_input in ["non", "no", "pas maintenant"]:
            return f"""D'accord, je n'ouvrirai pas le document.

Que souhaitez-vous faire maintenant ?
1️⃣ Remplir ce document avec vos informations
2️⃣ Revenir à la liste des modèles
3️⃣ Choisir un autre document"""
        
        # Vérifier si l'utilisateur fournit des informations pour remplir le document
        if last_action == "remplir_document":
            # Stocker les informations fournies dans le contexte
            if "form_info" not in self.current_context:
                self.current_context["form_info"] = []
            
            self.current_context["form_info"].append(message)
            
            return f"""✅ J'ai bien noté les informations suivantes: 

"{message}"

Voulez-vous ajouter d'autres informations ? Si oui, tapez-les maintenant.
Sinon, tapez 'compléter' pour que je remplisse le document avec ces informations."""
        
        # Actions standard (première action)
        if normalized_input in ["1", "remplir", "informations", "specifiques", "personnaliser"]:
            self.current_context["last_action"] = "remplir_document"
            return f"""📝 Très bien, je vais vous aider à remplir le document "{selected_model}".

Quelles informations souhaitez-vous inclure ?
(Ex: noms, dates, montants, termes spécifiques...)"""
            
        elif normalized_input in ["2", "utiliser", "tel quel"]:
            self.current_context["last_action"] = "utiliser_document"
            return f"""✅ Le document "{selected_model}" est prêt à être utilisé tel quel.

📂 Chemin complet: {model_path}

Souhaitez-vous l'ouvrir maintenant ?
(Tapez 'oui' pour ouvrir ou 'non' pour revenir aux options)"""
            
        elif normalized_input in ["3", "apercu", "aperçu", "voir", "preview", "voir un apercu", "voir un aperçu", "apercu du document", "aperçu du document", "voir apercu", "voir aperçu"]:
            self.current_context["last_action"] = "afficher_apercu"
            
            # Vérifier si le fichier existe
            if os.path.exists(model_path):
                try:
                    # Lire les premiers Ko du fichier selon son type
                    if model_path.endswith('.txt'):
                        with open(model_path, 'r', encoding='utf-8') as f:
                            content = f.read(1000)  # Premiers 1000 caractères
                        
                        # Formater l'aperçu
                        preview = f"""📄 **Aperçu de {selected_model}**

```
{content}
```

... (contenu tronqué)

Que souhaitez-vous faire maintenant ?
1️⃣ Remplir ce document avec vos informations
2️⃣ Utiliser ce document tel quel
3️⃣ Revenir à la liste des modèles"""
                        return preview
                    else:
                        # Pour les autres types de fichiers (non texte)
                        return f"""📄 Le document "{selected_model}" est un fichier de type {os.path.splitext(model_path)[1]}.

Je ne peux pas afficher un aperçu direct de ce format, mais vous pouvez l'utiliser tel quel.

Que souhaitez-vous faire maintenant ?
1️⃣ Remplir ce document avec vos informations
2️⃣ Utiliser ce document tel quel
3️⃣ Revenir à la liste des modèles"""
                
                except Exception as e:
                    self.logger.error(f"Erreur lors de la lecture du fichier: {e}")
                    return f"""❌ Je n'ai pas pu lire le contenu du document "{selected_model}".

Que souhaitez-vous faire maintenant ?
1️⃣ Remplir ce document avec vos informations
2️⃣ Utiliser ce document tel quel
3️⃣ Revenir à la liste des modèles"""
            else:
                return f"""❌ Le document "{selected_model}" n'existe pas à l'emplacement attendu.

Veuillez vérifier le chemin: {model_path}

Souhaitez-vous :
1️⃣ Choisir un autre document
2️⃣ Créer un nouveau document"""
        
        else:
            # Si l'entrée n'est pas reconnue, afficher les options disponibles
            return f"""❓ Je n'ai pas compris votre choix. Pour le document "{selected_model}", vous pouvez :

1️⃣ Remplir le document avec des informations spécifiques
2️⃣ Utiliser le document tel quel
3️⃣ Voir un aperçu du document

Ou tapez 'retour' pour revenir à la liste des modèles."""

    def _ask_for_new_document_details(self, category, doc_type):
        """
        Pose des questions pour générer un document si aucun modèle n'existe.
        
        Args:
            category (str): La catégorie de documents
            doc_type (str): Le type de document
            
        Returns:
            str: Message demandant les détails
        """
        # Mettre à jour le contexte pour la création d'un nouveau document
        self._update_context("new_document", category=category, doc_type=doc_type)
        
        if doc_type:
            return f"""📝 Je vais vous aider à créer un nouveau {doc_type}.

Pour commencer, j'ai besoin de quelques informations essentielles :

1. Quel est l'objectif du document ?
   (ex: prestation de services, maintenance, location...)

2. Qui sont les parties impliquées ?
   (ex: client, fournisseur, prestataire...)

3. Quels sont les termes clés ?
   (ex: durée, paiement, responsabilités...)

Pour chaque question, répondez avec une phrase simple et claire.
Ou tapez 'retour' pour revenir au menu précédent."""
        else:
            return f"""📝 Je vais vous aider à créer un nouveau document.

Pour commencer, j'ai besoin de quelques informations essentielles :

1. Quel type de document souhaitez-vous créer ?
   (ex: contrat, lettre, rapport...)

2. Quel est l'objectif principal ?
   (ex: proposition commerciale, réclamation, compte-rendu...)

3. Quelles sont les parties impliquées ?
   (ex: client, fournisseur, prestataire...)

Pour chaque question, répondez avec une phrase simple et claire.
Ou tapez 'retour' pour revenir au menu précédent."""
        
    def _load_document_templates(self):
        """Charge les modèles de documents depuis le répertoire templates"""
        try:
            # Chemin vers les modèles
            templates_path = os.path.join("data", "documents", "templates", "templates.json")
            
            if os.path.exists(templates_path):
                with open(templates_path, "r", encoding="utf-8") as f:
                    templates = json.load(f)
                
                # Organiser les templates par catégorie
                for tmpl in templates:
                    category = tmpl.get("category", "Autre").capitalize()
                    if category not in self.templates_by_category:
                        self.templates_by_category[category] = []
                    self.templates_by_category[category].append(tmpl)
                
                # Extraire les types de documents uniques
                self.document_types = list(set(tmpl.get("type", "Autre").capitalize() 
                                             for tmpl in templates))
                self.document_types.sort()
                
                self.logger.info(f"Templates chargés depuis {templates_path}")
            else:
                self.logger.warning(f"Fichier templates.json non trouvé")
                
                # Créer quelques catégories par défaut
                default_categories = ["Juridique", "Commercial", "Administratif", 
                                     "Ressources Humaines", "Fiscal", "Correspondance", 
                                     "Bancaire", "Corporate", "Immobilier"]
                                     
                for category in default_categories:
                    if category not in self.templates_by_category:
                        self.templates_by_category[category] = []
                
                # Créer quelques types de documents par défaut
                self.document_types = ["Contrat", "Lettre", "Attestation", "Facture", 
                                     "Convention", "Procès-verbal", "Rapport", 
                                     "Déclaration", "Formulaire"]
            
            # Mettre à jour les types de documents basés sur les catégories
            for category in self.templates_by_category:
                self.logger.info(f"{len(self.templates_by_category[category])} modèles trouvés pour la catégorie '{category}'")
            
            self.logger.info(f"Mise à jour des types de documents terminée: {len(self.document_types)} types trouvés")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des templates: {e}")
            # Créer des types par défaut en cas d'erreur
            self.document_types = ["Contrat", "Lettre", "Attestation", "Facture"]

