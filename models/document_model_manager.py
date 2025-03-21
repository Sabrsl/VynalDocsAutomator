#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire de modèles de documents
Gère la création, la sélection et la correction des modèles de documents
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from difflib import get_close_matches

logger = logging.getLogger("VynalDocsAutomator.DocumentModelManager")

class DocumentModelManager:
    """Gestionnaire de modèles de documents"""
    
    def __init__(self, models_path: str = "data/documents/types"):
        """
        Initialise le gestionnaire de modèles.
        
        Args:
            models_path (str): Chemin vers le répertoire des modèles
        """
        self.models_path = models_path
        self.categories: Dict[str, List[str]] = {}
        self.available_models: Dict[str, List[str]] = {}
        self.current_context: Dict = {
            "state": "initial",
            "category": None,
            "model": None,
            "last_action": None
        }
        
        # Dictionnaire de correction des fautes de frappe courantes
        self.typo_corrections = {
            # Accents et caractères spéciaux normalisés
            'é': 'e', 'è': 'e', 'ê': 'e',
            'à': 'a', 'â': 'a',
            'î': 'i', 'ï': 'i',
            'ô': 'o', 'ö': 'o',
            'û': 'u', 'ü': 'u',
            'ç': 'c',
            
            # Variations de "modèle"
            "modele": "modèle",
            "mdèle": "modèle",
            "modl": "modèle",
            "modèl": "modèle",
            "modle": "modèle",
            "model": "modèle",
            
            # Variations de "nouveau"
            "nouvo": "nouveau",
            "nvo": "nouveau",
            "nvx": "nouveau",
            "nouveaux": "nouveau",
            "noueau": "nouveau",
            
            # Variations de catégories
            "juridik": "juridique",
            "jurdik": "juridique",
            "jurdique": "juridique",
            "jurid": "juridique",
            "juri": "juridique",
            "legal": "juridique",
            
            "comercial": "commercial",
            "comerical": "commercial",
            "comm": "commercial",
            "com": "commercial",
            "vente": "commercial",
            
            "admin": "administratif",
            "administration": "administratif",
            
            "ressource": "ressources humaines",
            "humain": "ressources humaines",
            "rh": "ressources humaines",
            
            "fisc": "fiscales",
            "fiscal": "fiscales",
            "impot": "fiscales",
            "taxe": "fiscales",
            
            "correspondance": "correspondances",
            "lettre": "correspondances",
            "courrier": "correspondances",
            
            "bancaire": "bancaires",
            "banque": "bancaires",
            "finance": "bancaires",
            
            "entreprise": "corporate",
            "societe": "corporate",
            
            "immobilier": "immobiliers",
            "immo": "immobiliers",
            "propriete": "immobiliers",
            
            "autre": "autres",
            "divers": "autres",
            
            # Variations numériques
            "un": "1",
            "premier": "1",
            "deux": "2",
            "deuxieme": "2",
            "trois": "3",
            "troisieme": "3",
            
            # Mots de navigation
            "retour": "retour",
            "back": "retour",
            "annuler": "annuler",
            "cancel": "annuler",
            "quitter": "quitter",
            "exit": "quitter"
        }
        
        # Charger les catégories et modèles
        self._load_categories()
        self._update_available_models()
        
        logger.info("DocumentModelManager initialisé")
    
    def _load_categories(self) -> None:
        """Charge les catégories depuis le fichier de configuration."""
        try:
            templates_file = os.path.join(self.models_path, "templates.json")
            if os.path.exists(templates_file):
                with open(templates_file, "r", encoding="utf-8") as f:
                    templates = json.load(f)
                
                # Organiser les templates par catégorie
                for template in templates:
                    category = template.get("category", "").lower()
                    if category:
                        if category not in self.categories:
                            self.categories[category] = []
                        self.categories[category].append(template.get("name", ""))
                
                logger.info("Catégories chargées avec succès")
            else:
                logger.warning("Fichier templates.json non trouvé")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des catégories : {e}")
            self.categories = {}
    
    def _update_available_models(self) -> None:
        """Met à jour la liste des modèles disponibles."""
        try:
            self.available_models = {}
            
            # Explorer les dossiers de catégories
            for category_dir in os.listdir(self.models_path):
                category_path = os.path.join(self.models_path, category_dir)
                if os.path.isdir(category_path):
                    category = category_dir.lower()
                    if category not in self.available_models:
                        self.available_models[category] = []
                    
                    # Ajouter les fichiers de modèles
                    for file in os.listdir(category_path):
                        if file.endswith(('.docx', '.pdf', '.txt')):
                            self.available_models[category].append(file)
            
            logger.info("Liste des modèles mise à jour avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des modèles : {e}")
            self.available_models = {}
    
    def _normalize_input(self, text: str) -> str:
        """
        Normalise l'entrée utilisateur.
        
        Args:
            text (str): Texte à normaliser
            
        Returns:
            str: Texte normalisé
        """
        if not text:
            return ""
            
        # Convertir en minuscules et supprimer les espaces superflus
        text = text.lower().strip()
        
        # Vérifier d'abord une correspondance exacte dans les corrections
        if text in self.typo_corrections:
            return self.typo_corrections[text]
            
        # Appliquer les corrections pour les sous-chaînes
        for old, new in self.typo_corrections.items():
            text = text.replace(old, new)
        
        # Supprimer les caractères spéciaux restants, 
        # mais conserver les espaces pour les noms de fichiers multi-mots
        text = ''.join(c for c in text if c.isalnum() or c.isspace())
        
        return text.strip()
    
    def _correct_typo(self, text: str, options: List[str]) -> str:
        """
        Corrige les fautes de frappe dans le texte.
        
        Args:
            text (str): Texte à corriger
            options (List[str]): Liste des options valides
            
        Returns:
            str: Texte corrigé ou texte original si aucune correction trouvée
        """
        # Normaliser le texte
        normalized_text = self._normalize_input(text)
        
        # Normaliser les options pour permettre une comparaison équitable
        normalized_options = {self._normalize_input(opt): opt for opt in options}
        
        # Vérifier si le texte normalisé correspond exactement à une option normalisée
        if normalized_text in normalized_options:
            return normalized_options[normalized_text]
        
        # Vérifier si le texte normalisé est une sous-chaîne d'une option normalisée
        for norm_opt, original_opt in normalized_options.items():
            if normalized_text in norm_opt or norm_opt in normalized_text:
                return original_opt
        
        # Utiliser difflib pour trouver la meilleure correspondance avec un seuil plus bas
        matches = get_close_matches(normalized_text, normalized_options.keys(), n=1, cutoff=0.6)
        if matches:
            return normalized_options[matches[0]]
            
        # Si numérique, tenter de l'interpréter comme un index
        if normalized_text.isdigit():
            index = int(normalized_text) - 1  # Indexation à partir de 1 pour l'utilisateur
            if 0 <= index < len(options):
                return options[index]
                
        # Si tout échoue, retourner le texte original
        return text
    
    def _get_category_emoji(self, category: str) -> str:
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
            "technique": "🔧",
            "marketing": "📢",
            "autre": "📄"
        }
        return emojis.get(category.lower(), "📄")
    
    def get_available_categories(self) -> str:
        """
        Retourne la liste des catégories disponibles.
        
        Returns:
            str: Message formaté avec les catégories
        """
        if not self.categories:
            return "❌ Aucune catégorie n'est disponible pour le moment."
        
        categories_list = []
        for category in self.categories:
            emoji = self._get_category_emoji(category)
            categories_list.append(f"{emoji} {category.capitalize()}")
        
        return f"""📌 Voici les catégories de modèles disponibles :

{chr(10).join(categories_list)}

Veuillez choisir une catégorie en tapant son nom."""
    
    def get_available_models(self, category: str) -> str:
        """
        Retourne la liste des modèles disponibles dans une catégorie.
        
        Args:
            category (str): La catégorie
            
        Returns:
            str: Message formaté avec les modèles
        """
        models = self.available_models.get(category.lower(), [])
        if not models:
            return f"""❌ Aucun modèle n'est disponible dans la catégorie {category}.
Voulez-vous revenir à la liste des catégories ? (oui/non)"""
        
        models_list = "\n".join(f"{i+1}️⃣ {model}" for i, model in enumerate(models))
        return f"""📌 Modèles disponibles dans {category} :

{models_list}

Tapez le numéro du modèle que vous souhaitez utiliser."""
    
    def handle_user_input(self, user_input: str) -> Tuple[str, Optional[str]]:
        """
        Gère l'entrée utilisateur et retourne une réponse appropriée.
        
        Args:
            user_input (str): L'entrée de l'utilisateur
            
        Returns:
            Tuple[str, Optional[str]]: (Message de réponse, État suivant)
        """
        # Vérifier si l'entrée est vide
        if not user_input or not user_input.strip():
            return "Je n'ai pas compris votre demande. Comment puis-je vous aider ?", self.current_context.get("state", "initial")
            
        normalized_input = self._normalize_input(user_input)
        
        # S'assurer que last_action est initialisé
        if "last_action" not in self.current_context:
            self.current_context["last_action"] = None
            
        # Tracer l'entrée normalisée pour le débogage
        logger.debug(f"Entrée normalisée: '{normalized_input}' (originale: '{user_input}')")
        logger.debug(f"État actuel: {self.current_context.get('state', 'initial')}")
        logger.debug(f"Dernière action: {self.current_context.get('last_action', 'none')}")
        
        # Gérer les salutations et questions générales
        if normalized_input in ["bonjour", "salut", "cava", "cava?", "ca va", "ca va?", "comment allez-vous", "comment allez vous"]:
            self.current_context["state"] = "initial"
            self.current_context["last_action"] = "greeting"
            return "Bonjour ! Je suis là pour vous aider à créer des documents. Que souhaitez-vous faire ?", "initial"
        
        # Gérer les commandes de navigation
        if normalized_input in ["retour", "back", "arriere", "annuler", "cancel"]:
            # Revenir à l'état précédent
            prev_state = self.current_context.get("state", "initial")
            
            if prev_state == "choosing_model":
                # Si on était en train de choisir un modèle, revenir à la sélection de catégorie
                self.current_context["state"] = "choosing_category"
                self.current_context["last_action"] = "retour_categories"
                return "D'accord, revenons à la liste des catégories.\n\n" + self.get_available_categories(), "choosing_category"
            elif prev_state == "choosing_category":
                # Si on était en train de choisir une catégorie, revenir au menu initial
                self.current_context["state"] = "initial"
                self.current_context["last_action"] = "retour_initial"
                return """D'accord, revenons au début. Que souhaitez-vous faire ?

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document""", "initial"
            else:
                # Sinon, revenir au tout début
                self.current_context["state"] = "initial"
                self.current_context["last_action"] = "retour_initial"
                return "D'accord, revenons au début. Comment puis-je vous aider ?", "initial"
        
        # Gérer la demande de document (nouvelle ou répétée)
        if "document" in normalized_input or "modele" in normalized_input or "creer" in normalized_input or "nouveau" in normalized_input:
            if self.current_context.get("state") not in ["choosing_category", "choosing_model", "model_selected"]:
                # Réinitialiser l'état pour une nouvelle demande
                self.current_context["state"] = "initial"
                self.current_context["last_action"] = "document_request"
                return """📌 Quel type de document souhaitez-vous ?

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document

Veuillez choisir une option en tapant 1 ou 2.""", "initial"
        
        # Gérer la sélection de catégorie
        if self.current_context["state"] == "choosing_category":
            try:
                # Essayer d'interpréter comme un numéro de catégorie
                index = int(normalized_input) - 1
                if 0 <= index < len(self.categories):
                    category = list(self.categories.keys())[index]
                    self.current_context["category"] = category
                    self.current_context["last_action"] = "category_selected"
                    return f"Parfait ! Voici les modèles disponibles dans la catégorie {category} :\n\n{self.get_available_models(category)}", "choosing_model"
                else:
                    self.current_context["last_action"] = "invalid_category"
                    return f"❌ Je ne trouve pas la catégorie numéro {normalized_input}. Veuillez choisir un numéro entre 1 et {len(self.categories)}.", "choosing_category"
            except ValueError:
                # Si ce n'est pas un numéro, essayer de corriger la faute de frappe
                corrected_category = self._correct_typo(normalized_input, list(self.categories.keys()))
                if corrected_category in self.categories:
                    self.current_context["category"] = corrected_category
                    self.current_context["last_action"] = "category_selected"
                    return f"Je comprends que vous voulez la catégorie {corrected_category}. Voici les modèles disponibles :\n\n{self.get_available_models(corrected_category)}", "choosing_model"
                
                # Vérifier si c'est un choix de type de document initial
                if normalized_input in ["1", "modele", "existant"]:
                    self.current_context["state"] = "choosing_category"
                    self.current_context["last_action"] = "use_existing"
                    return "D'accord, vous voulez utiliser un modèle existant. Voici les catégories disponibles :\n\n" + self.get_available_categories(), "choosing_category"
                elif normalized_input in ["2", "nouveau", "nvx", "nv", "nveaux", "creer"]:
                    self.current_context["state"] = "new_document"
                    self.current_context["last_action"] = "create_new"
                    return "Je vais vous aider à créer un nouveau document. Voici les catégories disponibles :\n\n" + self.get_available_categories(), "new_document"
                
                self.current_context["last_action"] = "invalid_category"
                return "❌ Je ne trouve pas cette catégorie. Voici les catégories disponibles :\n\n" + self.get_available_categories(), "choosing_category"
        
        # Gérer la sélection de modèle
        if self.current_context["state"] == "choosing_model":
            try:
                index = int(normalized_input) - 1
                category = self.current_context["category"]
                models = self.available_models.get(category.lower(), [])
                
                if not models:
                    self.current_context["state"] = "choosing_category"
                    self.current_context["last_action"] = "no_models"
                    return f"❌ Aucun modèle n'est disponible dans la catégorie {category}. Veuillez choisir une autre catégorie :\n\n" + self.get_available_categories(), "choosing_category"
                
                if 0 <= index < len(models):
                    self.current_context["model"] = models[index]
                    self.current_context["last_action"] = "model_selected"
                    return f"✅ Excellent choix ! Je vais créer un document avec le modèle {models[index]}.", "model_selected"
                else:
                    self.current_context["last_action"] = "invalid_model"
                    return f"❌ Je ne trouve pas le modèle numéro {normalized_input}. Veuillez choisir un numéro entre 1 et {len(models)}.", "choosing_model"
            except ValueError:
                # Si ce n'est pas un numéro, essayer de corriger la faute de frappe
                category = self.current_context["category"]
                models = self.available_models.get(category.lower(), [])
                
                if not models:
                    self.current_context["state"] = "choosing_category"
                    self.current_context["last_action"] = "no_models"
                    return f"❌ Aucun modèle n'est disponible dans la catégorie {category}. Veuillez choisir une autre catégorie :\n\n" + self.get_available_categories(), "choosing_category"
                
                corrected_model = self._correct_typo(normalized_input, models)
                if corrected_model in models:
                    self.current_context["model"] = corrected_model
                    self.current_context["last_action"] = "model_selected"
                    return f"✅ J'ai compris que vous voulez le modèle {corrected_model}. Je vais l'utiliser pour créer votre document.", "model_selected"
                
                self.current_context["last_action"] = "invalid_model"
                return "❌ Je ne comprends pas ce choix. Veuillez choisir un numéro de la liste ou tapez 'retour' pour revenir aux catégories.", "choosing_model"
        
        # Traitement du choix initial (état initial ou après une erreur)
        if self.current_context["state"] in ["initial", None]:
            # Vérifier les choix pour utiliser un modèle existant
            if normalized_input in ["1", "un", "modele", "existant", "modèle", "modèl", "mdèle", "existants", "utiliser"]:
                self.current_context["state"] = "choosing_category"
                self.current_context["last_action"] = "use_existing"
                return "D'accord, vous voulez utiliser un modèle existant. Voici les catégories disponibles :\n\n" + self.get_available_categories(), "choosing_category"
            # Vérifier les choix pour créer un nouveau document
            elif normalized_input in ["2", "deux", "nouveau", "nvx", "nv", "nveaux", "creer", "créer", "nouvelle"]:
                self.current_context["state"] = "new_document"
                self.current_context["last_action"] = "create_new"
                return "Je vais vous aider à créer un nouveau document. Voici les catégories disponibles :\n\n" + self.get_available_categories(), "new_document"
            
            # Réagir à une demande générale de document
            if "document" in normalized_input or "modele" in normalized_input or "contrat" in normalized_input or "aide" in normalized_input:
                self.current_context["last_action"] = "help_request"
                return """📌 Je peux vous aider avec vos documents. Que souhaitez-vous faire ?

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document

Veuillez choisir une option en tapant 1 ou 2.""", "initial"
        
        # Si on arrive ici, c'est que l'entrée n'a pas été reconnue
        self.current_context["last_action"] = "invalid_choice"
        
        # Message d'aide contextuel en fonction de l'état actuel
        if self.current_context["state"] == "choosing_category":
            return f"""❓ Je ne suis pas sûr de comprendre votre choix. 
            
Voici les catégories disponibles :
{chr(10).join([f"{i+1}. {cat}" for i, cat in enumerate(self.categories.keys())])}

Veuillez choisir une catégorie en tapant son numéro ou son nom, ou 'retour' pour revenir au menu précédent.""", "choosing_category"
        elif self.current_context["state"] == "choosing_model":
            category = self.current_context.get("category", "")
            models = self.available_models.get(category.lower(), [])
            return f"""❓ Je ne suis pas sûr de comprendre votre choix.
            
Voici les modèles disponibles dans la catégorie {category} :
{chr(10).join([f"{i+1}. {model}" for i, model in enumerate(models)])}

Veuillez choisir un modèle en tapant son numéro ou son nom, ou 'retour' pour revenir à la liste des catégories.""", "choosing_model"
        elif self.current_context["state"] == "new_document":
            return """❓ Je n'ai pas bien compris. Pour créer un nouveau document, j'ai besoin de plus d'informations.

Quel type de document souhaitez-vous créer ? Par exemple :
- Un contrat
- Une lettre
- Un rapport
- Une facture

Ou tapez 'retour' pour revenir au menu précédent.""", "new_document"
        else:
            # Message générique si l'état n'est pas reconnu
            return """❓ Je ne suis pas sûr de comprendre votre demande. Voici les options disponibles :

1️⃣ Utiliser un modèle existant
2️⃣ Créer un nouveau document

Que souhaitez-vous faire ?""", "initial" 