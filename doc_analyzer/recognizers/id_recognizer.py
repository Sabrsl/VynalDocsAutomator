#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de reconnaissance des identifiants pour Vynal Docs Automator
Ce module fournit des fonctionnalités pour détecter et extraire différents types d'identifiants
(cartes d'identité, passeports, documents fiscaux, etc.) dans les documents.
"""

import re
import os
import logging
import json
from typing import Dict, List, Tuple, Optional, Any
import spacy

# Configuration du logger
logger = logging.getLogger("VynalDocsAutomator.Recognizers.IDRecognizer")

class IDRecognizer:
    """
    Classe pour la reconnaissance et l'extraction des différents types d'identifiants
    dans les documents.
    """
    
    # Types d'identifiants supportés
    ID_TYPES = {
        "personal": [
            "cni",          # Carte nationale d'identité
            "passport",     # Passeport
            "residence",    # Titre de séjour/carte de résidence
            "visa"          # Visa
        ],
        "fiscal": [
            "tax_id",       # Identifiant fiscal
            "vat",          # Numéro de TVA
            "siret",        # SIRET (France)
            "siren",        # SIREN (France)
            "ninea",        # NINEA (Sénégal)
            "rc"            # Registre de commerce
        ],
        "social": [
            "ssn",          # Numéro de sécurité sociale
            "health_id",    # Identifiant d'assurance maladie
            "benefits_id"   # Identifiant d'allocations
        ],
        "professional": [
            "pro_license",  # Licence professionnelle
            "bar_id",       # Numéro de barreau (avocats)
            "medical_id",   # Identifiant médical
            "accounting_id" # Identifiant d'expert-comptable
        ]
    }
    
    # Patterns par pays pour les différents types d'IDs
    COUNTRY_PATTERNS = {
        "fr": {  # France
            "cni": r"(?i)(?:№|N°|No|Numéro)?\s*(?:CNI|Carte)?\s*:?\s*([0-9]{12}|[0-9]{4}\s*[0-9]{4}\s*[0-9]{4})",
            "passport": r"(?i)(?:№|N°|No|Numéro)?\s*(?:Passeport)?\s*:?\s*([0-9]{2}\s*[A-Z]{2}\s*[0-9]{5}|[0-9]{9})",
            "ssn": r"(?i)(?:sécurité sociale|sécu|ss|nir)\s*:?\s*([1-2][0-9]{2}(?:0[1-9]|1[0-2])(?:2[AB]|[0-9]{2})[0-9]{3}[0-9]{3})",
            "siret": r"(?i)(?:siret)\s*:?\s*([0-9]{3}\s*[0-9]{3}\s*[0-9]{3}\s*[0-9]{5}|[0-9]{14})",
            "siren": r"(?i)(?:siren)\s*:?\s*([0-9]{3}\s*[0-9]{3}\s*[0-9]{3}|[0-9]{9})",
            "tax_id": r"(?i)(?:numéro fiscal|identifiant fiscal)\s*:?\s*([0-9]{13,15})"
        },
        "ma": {  # Maroc
            "cni": r"(?i)(?:№|N°|No|رقم|CIN)\s*:?\s*([A-Z]{1,2}[0-9]{5,6})",
            "passport": r"(?i)(?:№|N°|No|جواز|Passeport)\s*:?\s*([A-Z][A-Z0-9]{7,8})",
            "tax_id": r"(?i)(?:identifiant fiscal|IF)\s*:?\s*([0-9]{7,10})"
        },
        "sn": {  # Sénégal
            "cni": r"(?i)(?:№|N°|No|CNI)\s*:?\s*([0-9]{13}|[0-9]{1,2}\s*[0-9]{3}\s*[0-9]{4}\s*[0-9]{2})",
            "ninea": r"(?i)(?:NINEA)\s*:?\s*([0-9]{7}[A-Z][0-9]{3})"
        },
        "ci": {  # Côte d'Ivoire
            "cni": r"(?i)(?:№|N°|No|CNI)\s*:?\s*([A-Z][0-9]{9}|C-[0-9]{9})",
            "tax_id": r"(?i)(?:compte contribuable)\s*:?\s*([0-9]{10,12})"
        },
        # Patterns génériques pour tout pays
        "generic": {
            "vat": r"(?i)(?:TVA|TVA intra|VAT|VAT number)\s*:?\s*([A-Z]{2}[0-9A-Z\s]{2,12})"
        }
    }
    
    def __init__(self, resources_path=None):
        """
        Initialisation du reconnaisseur d'identifiants
        
        Args:
            resources_path (str, optional): Chemin vers les ressources (formats d'IDs)
        """
        self.logger = logger
        
        # Chemin vers les ressources
        self.resources_path = resources_path
        if not self.resources_path:
            # Chemin par défaut relatif au module
            self.resources_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "resources"
            )
        
        # Chargement des formats d'identifiants
        self.formats = self._load_id_formats()
        
        # Chargement du modèle spaCy si disponible
        try:
            self.nlp = spacy.load("fr_core_news_sm")
        except:
            self.logger.warning("Modèle spaCy non disponible, certaines fonctionnalités seront limitées")
            self.nlp = None
        
        self.logger.info("IDRecognizer initialisé")
    
    def _load_id_formats(self) -> Dict[str, Any]:
        """
        Charge les formats d'identifiants depuis le fichier de ressources
        
        Returns:
            dict: Dictionnaire des formats d'identifiants par pays et type
        """
        formats = {}
        try:
            formats_file = os.path.join(self.resources_path, "reference_data", "id_formats.json")
            if os.path.exists(formats_file):
                with open(formats_file, 'r', encoding='utf-8') as f:
                    formats = json.load(f)
                self.logger.info(f"Formats d'identifiants chargés: {len(formats)} pays configurés")
            else:
                self.logger.warning(f"Fichier de formats d'identifiants non trouvé: {formats_file}")
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des formats d'identifiants: {e}")
        
        return formats
    
    def detect_id_type(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Détecte le type d'identifiant dans le texte
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            tuple: (type d'identifiant, pays) ou None si non détecté
        """
        # Normalisation du texte pour la détection
        normalized_text = self._normalize_text(text)
        
        # Détection du pays
        country = self._detect_country(normalized_text)
        
        # Itération sur les patterns par pays
        country_patterns = self.COUNTRY_PATTERNS.get(country, {})
        
        # Ajouter les patterns génériques
        for id_type, pattern in self.COUNTRY_PATTERNS.get("generic", {}).items():
            if id_type not in country_patterns:
                country_patterns[id_type] = pattern
        
        # Recherche des patterns
        for id_type, pattern in country_patterns.items():
            if re.search(pattern, normalized_text):
                return id_type, country
        
        # Si aucun pattern spécifique n'est trouvé, vérifier avec des approches génériques
        # Mots-clés associés aux types d'identifiants
        id_keywords = {
            "cni": ["carte nationale", "identité", "identity card", "cni", "cin"],
            "passport": ["passeport", "passport", "جواز"],
            "siret": ["siret", "numéro d'entreprise"],
            "tax_id": ["fiscal", "impôt", "contribuable"],
            "ssn": ["sécurité sociale", "sécu", "social security"]
        }
        
        # Recherche par mots-clés
        for id_type, keywords in id_keywords.items():
            for keyword in keywords:
                if keyword.lower() in normalized_text.lower():
                    # Rechercher un format numérique ou alphanumerique à proximité
                    context = self._extract_context_around(normalized_text, keyword.lower(), 50)
                    id_number = self._extract_potential_id(context)
                    if id_number:
                        return id_type, country or "generic"
        
        return None
    
    def extract_id_number(self, text: str, id_type: str = None, country: str = None) -> Optional[str]:
        """
        Extrait le numéro d'identifiant du texte
        
        Args:
            text (str): Texte à analyser
            id_type (str, optional): Type d'identifiant à rechercher
            country (str, optional): Pays de l'identifiant
            
        Returns:
            str: Numéro d'identifiant extrait ou None si non trouvé
        """
        normalized_text = self._normalize_text(text)
        
        # Si le type et le pays ne sont pas spécifiés, les détecter
        if not id_type or not country:
            detected = self.detect_id_type(normalized_text)
            if detected:
                id_type, country = detected
            else:
                return None
        
        # Utiliser le pattern spécifique au type et au pays
        pattern = None
        
        # Rechercher dans les patterns spécifiques au pays
        if country in self.COUNTRY_PATTERNS and id_type in self.COUNTRY_PATTERNS[country]:
            pattern = self.COUNTRY_PATTERNS[country][id_type]
        
        # Si non trouvé, rechercher dans les patterns génériques
        if not pattern and id_type in self.COUNTRY_PATTERNS.get("generic", {}):
            pattern = self.COUNTRY_PATTERNS["generic"][id_type]
        
        # Si un pattern est trouvé, l'utiliser pour extraire l'identifiant
        if pattern:
            match = re.search(pattern, normalized_text)
            if match:
                id_number = match.group(1)
                # Nettoyer le numéro (supprimer les espaces)
                id_number = re.sub(r'\s+', '', id_number)
                
                # Valider le format si possible
                if self._validate_id_format(id_number, id_type, country):
                    return id_number
        
        # Approche générique si aucun pattern spécifique n'a fonctionné
        # Rechercher des séquences alphanumériques qui pourraient être des identifiants
        id_number = self._extract_potential_id(normalized_text)
        if id_number:
            return id_number
        
        return None
    
    def extract_all_ids(self, text: str) -> Dict[str, Dict[str, str]]:
        """
        Extrait tous les identifiants possibles du texte
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            dict: Dictionnaire de tous les identifiants trouvés par catégorie
        """
        normalized_text = self._normalize_text(text)
        results = {}
        
        # Détection du pays le plus probable
        country = self._detect_country(normalized_text)
        
        # Parcourir tous les pays configurés
        for current_country in list(self.COUNTRY_PATTERNS.keys()) + ["generic"]:
            if current_country == "generic":
                continue  # Les patterns génériques sont traités avec chaque pays
            
            # Priorité au pays détecté
            if current_country != country and country is not None:
                continue
            
            country_patterns = self.COUNTRY_PATTERNS.get(current_country, {})
            # Ajouter les patterns génériques
            for id_type, pattern in self.COUNTRY_PATTERNS.get("generic", {}).items():
                if id_type not in country_patterns:
                    country_patterns[id_type] = pattern
            
            # Rechercher tous les types d'identifiants
            for id_type, pattern in country_patterns.items():
                match = re.search(pattern, normalized_text)
                if match:
                    id_number = match.group(1)
                    # Nettoyer le numéro
                    id_number = re.sub(r'\s+', '', id_number)
                    
                    # Regrouper par catégorie
                    category = self._get_category_for_type(id_type)
                    
                    if category not in results:
                        results[category] = {}
                    
                    results[category][id_type] = {
                        "number": id_number,
                        "country": current_country if current_country != "generic" else None
                    }
        
        return results
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalise le texte pour améliorer la détection
        
        Args:
            text (str): Texte à normaliser
            
        Returns:
            str: Texte normalisé
        """
        # Supprimer les retours à la ligne pour simplifier les regex
        normalized = re.sub(r'\r\n|\r|\n', ' ', text)
        
        # Normaliser les espaces multiples
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Supprimer les caractères spéciaux superflus (sauf ceux utiles pour les identifiants)
        normalized = re.sub(r'[^\w\s\-\/.,:;+#@*&()[\]{}№°]', '', normalized)
        
        return normalized
    
    def _detect_country(self, text: str) -> Optional[str]:
        """
        Détecte le pays d'origine le plus probable du document
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            str: Code pays détecté ou None
        """
        # Mots-clés par pays
        country_keywords = {
            "fr": ["france", "république française", "république francaise", "français", "francais"],
            "ma": ["maroc", "royaume du maroc", "marocain", "المملكة المغربية", "المغرب"],
            "sn": ["sénégal", "senegal", "république du sénégal", "république du senegal"],
            "ci": ["côte d'ivoire", "cote d'ivoire", "république de côte d'ivoire", "ivoirien"],
            "cm": ["cameroun", "cameroon", "république du cameroun", "republic of cameroon"],
            "dz": ["algérie", "algerie", "république algérienne", "الجزائر", "الجمهورية الجزائرية"],
            "tn": ["tunisie", "tunisia", "république tunisienne", "الجمهورية التونسية", "تونس"]
        }
        
        # Recherche par mots-clés
        text_lower = text.lower()
        for country, keywords in country_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return country
        
        # Si aucun pays n'est détecté explicitement, essayer de détecter par les identifiants
        for country, patterns in self.COUNTRY_PATTERNS.items():
            if country == "generic":
                continue
                
            for _, pattern in patterns.items():
                if re.search(pattern, text):
                    return country
        
        # Utiliser le modèle spaCy pour détecter les entités géopolitiques si disponible
        if self.nlp:
            doc = self.nlp(text[:min(len(text), 5000)])  # Limiter pour des raisons de performance
            for ent in doc.ents:
                if ent.label_ == "GPE":  # Entité géopolitique
                    country_name = ent.text.lower()
                    # Mapping des noms de pays vers les codes
                    country_map = {
                        "france": "fr",
                        "maroc": "ma",
                        "sénégal": "sn", "senegal": "sn",
                        "côte d'ivoire": "ci", "cote d'ivoire": "ci",
                        "cameroun": "cm", "cameroon": "cm",
                        "algérie": "dz", "algerie": "dz",
                        "tunisie": "tn", "tunisia": "tn"
                    }
                    if country_name in country_map:
                        return country_map[country_name]
        
        return None
    
    def _extract_context_around(self, text: str, keyword: str, window_size: int = 50) -> str:
        """
        Extrait le contexte autour d'un mot-clé
        
        Args:
            text (str): Texte complet
            keyword (str): Mot-clé
            window_size (int): Taille de la fenêtre de contexte
            
        Returns:
            str: Texte du contexte
        """
        keyword_pos = text.lower().find(keyword.lower())
        if keyword_pos == -1:
            return ""
        
        start = max(0, keyword_pos - window_size)
        end = min(len(text), keyword_pos + len(keyword) + window_size)
        
        return text[start:end]
    
    def _extract_potential_id(self, text: str) -> Optional[str]:
        """
        Extrait un potentiel identifiant du texte en utilisant des heuristiques générales
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            str: Identifiant potentiel ou None
        """
        # Patterns généraux pour les identifiants
        # Numéros avec ou sans lettres, séparés ou non par des espaces/tirets
        patterns = [
            # Pattern pour des numéros de 7 à 20 caractères avec possibles séparateurs
            r"(?:№|N°|No|Numéro)?\s*:?\s*([A-Z0-9][\- A-Z0-9]{5,18}[A-Z0-9])",
            # Pattern pour des codes alphanumériques structurés
            r"([A-Z]{1,3}[\- ]?[0-9]{4,10})",
            # Pattern pour des combinaisons de groupes alphanumériques
            r"([0-9]{2,4}[\- ]?[A-Z]{1,3}[\- ]?[0-9]{2,6})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                id_number = match.group(1)
                # Nettoyer le numéro
                id_number = re.sub(r'\s+', '', id_number)
                return id_number
        
        return None
    
    def _validate_id_format(self, id_number: str, id_type: str, country: str) -> bool:
        """
        Valide le format d'un identifiant
        
        Args:
            id_number (str): Numéro d'identifiant
            id_type (str): Type d'identifiant
            country (str): Pays de l'identifiant
            
        Returns:
            bool: True si le format est valide, False sinon
        """
        # Vérifier les formats connus
        if country in self.formats and id_type in self.formats[country]:
            format_info = self.formats[country][id_type]
            
            # Vérifier la longueur
            if "length" in format_info:
                expected_length = format_info["length"]
                if len(id_number) != expected_length:
                    return False
            
            # Vérifier le pattern
            if "pattern" in format_info:
                pattern = format_info["pattern"]
                if not re.match(pattern, id_number):
                    return False
            
            # Vérifier l'algorithme de validation si disponible
            if "validation" in format_info:
                validation_type = format_info["validation"]
                if validation_type == "luhn" and not self._validate_luhn(id_number):
                    return False
                # Autres algorithmes de validation pourraient être ajoutés ici
        
        # Si aucune validation spécifique n'est disponible ou si toutes les validations passent
        return True
    
    def _validate_luhn(self, number: str) -> bool:
        """
        Valide un numéro avec l'algorithme de Luhn (utilisé pour certains IDs)
        
        Args:
            number (str): Numéro à valider
            
        Returns:
            bool: True si le numéro est valide selon l'algorithme de Luhn
        """
        # Supprimer tous les caractères non numériques
        digits = re.sub(r'\D', '', number)
        
        if not digits:
            return False
        
        # Convertir en liste d'entiers
        digits = [int(d) for d in digits]
        
        # Algorithme de Luhn
        checksum = 0
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:  # positions impaires (en partant de la droite)
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        
        return checksum % 10 == 0
    
    def _get_category_for_type(self, id_type: str) -> str:
        """
        Détermine la catégorie d'un type d'identifiant
        
        Args:
            id_type (str): Type d'identifiant
            
        Returns:
            str: Catégorie de l'identifiant
        """
        for category, types in self.ID_TYPES.items():
            if id_type in types:
                return category
        return "other"

# Fonction utilitaire autonome
def extract_ids_from_text(text: str) -> Dict[str, Dict[str, str]]:
    """
    Fonction utilitaire pour extraire les identifiants d'un texte
    
    Args:
        text (str): Texte à analyser
        
    Returns:
        dict: Dictionnaire des identifiants trouvés
    """
    recognizer = IDRecognizer()
    return recognizer.extract_all_ids(text)


if __name__ == "__main__":
    # Test de la classe avec un exemple
    sample_text = """
    République Française
    Carte Nationale d'Identité N°: 1234 5678 9012
    Nom: DUPONT
    Prénom: Jean
    Né le: 15/01/1980 à Paris
    
    SIRET: 123 456 789 00012
    N° TVA Intracommunautaire: FR12345678900
    """
    
    recognizer = IDRecognizer()
    
    print("Test de détection de type d'ID:")
    id_info = recognizer.detect_id_type(sample_text)
    if id_info:
        print(f"Type d'ID détecté: {id_info[0]}, Pays: {id_info[1]}")
    else:
        print("Aucun ID détecté")
    
    print("\nTest d'extraction du numéro d'ID:")
    cni = recognizer.extract_id_number(sample_text, "cni", "fr")
    print(f"CNI: {cni}")
    
    print("\nTest d'extraction de tous les IDs:")
    all_ids = recognizer.extract_all_ids(sample_text)
    for category, ids in all_ids.items():
        print(f"Catégorie: {category}")
        for id_type, details in ids.items():
            print(f"  {id_type}: {details['number']} (Pays: {details['country']})")