#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de reconnaissance et validation de numéros de téléphone pour Vynal Docs Automator
Ce module permet d'identifier, extraire et normaliser les numéros de téléphone
dans différents formats et contextes, avec support des spécificités régionales.
"""

import re
import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from enum import Enum

# Configuration du logger
logger = logging.getLogger("VynalDocsAutomator.DocAnalyzer.PhoneRecognizer")

class PhoneType(Enum):
    """Types de numéros de téléphone supportés"""
    MOBILE = "mobile"              # Téléphone mobile
    LANDLINE = "landline"          # Téléphone fixe
    FAX = "fax"                    # Numéro de fax
    VOIP = "voip"                  # Téléphonie IP
    TOLL_FREE = "toll_free"        # Numéro gratuit / vert
    PREMIUM = "premium"            # Numéro surtaxé
    INTERNATIONAL = "international"  # Format international non catégorisé
    UNKNOWN = "unknown"            # Type inconnu


class PhoneRecognizer:
    """
    Classe responsable de la reconnaissance et validation des numéros de téléphone
    """
    
    def __init__(self, resources_path=None):
        """
        Initialisation du reconnaisseur de numéros de téléphone
        
        Args:
            resources_path (str, optional): Chemin vers les ressources spécifiques
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
        
        # Chargement des patterns et des données de référence
        self.patterns = self._load_patterns()
        self.reference_data = self._load_reference_data()
        
        self.logger.info("Reconnaisseur de numéros de téléphone initialisé")
    
    def _load_patterns(self) -> Dict[str, Any]:
        """
        Charge les patterns regex pour la reconnaissance des numéros de téléphone
        
        Returns:
            dict: Dictionnaire de patterns par pays et type
        """
        patterns = {
            # Patterns génériques internationaux
            "international": {
                # Format international général: +XX X XX XX XX XX
                "general": re.compile(
                    r'\+\d{1,4}[\s.-]?\d{1,4}[\s.-]?\d{1,4}[\s.-]?\d{1,4}[\s.-]?\d{1,4}',
                    re.UNICODE
                ),
                # E.164 strict: +XXXXXXXXXX (pas d'espace, que des chiffres)
                "e164": re.compile(
                    r'\+\d{7,15}',
                    re.UNICODE
                )
            },
            
            # Patterns pour la France
            "fr": {
                # Mobile: 06 XX XX XX XX ou 07 XX XX XX XX
                "mobile": re.compile(
                    r'(?:0|\+33|00\s*33)[\s.-]?[67][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
                    re.UNICODE
                ),
                # Fixe: 01-05 XX XX XX XX
                "landline": re.compile(
                    r'(?:0|\+33|00\s*33)[\s.-]?[1-5][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
                    re.UNICODE
                ),
                # Numéro vert: 08 00 XX XX XX
                "toll_free": re.compile(
                    r'(?:0|\+33|00\s*33)[\s.-]?[8][\s.-]?0[\s.-]?0[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
                    re.UNICODE
                ),
                # Numéro surtaxé: 08 9X XX XX XX
                "premium": re.compile(
                    r'(?:0|\+33|00\s*33)[\s.-]?[8][\s.-]?9[\s.-]?\d{1}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
                    re.UNICODE
                )
            },
            
            # Patterns pour le Maroc
            "ma": {
                # Mobile: 06 XX XX XX XX
                "mobile": re.compile(
                    r'(?:0|\+212|00\s*212)[\s.-]?[67][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
                    re.UNICODE
                ),
                # Fixe: 05 XX XX XX XX
                "landline": re.compile(
                    r'(?:0|\+212|00\s*212)[\s.-]?[5][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
                    re.UNICODE
                )
            },
            
            # Patterns pour le Sénégal
            "sn": {
                # Mobile et fixe: 7X XXX XX XX
                "general": re.compile(
                    r'(?:0|\+221|00\s*221)[\s.-]?[7-8][\s.-]?\d{1}[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}',
                    re.UNICODE
                )
            },
            
            # Patterns pour la Côte d'Ivoire
            "ci": {
                # Mobile et fixe: XX XX XX XX XX
                "general": re.compile(
                    r'(?:0|\+225|00\s*225)[\s.-]?(?:[0-5]|[07])[\s.-]?\d{1}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
                    re.UNICODE
                )
            },
            
            # Patterns pour le Cameroun
            "cm": {
                # Mobile et fixe: X XX XX XX XX
                "general": re.compile(
                    r'(?:0|\+237|00\s*237)[\s.-]?(?:[2368])[\s.-]?\d{1}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
                    re.UNICODE
                )
            },
            
            # Patterns pour l'Algérie
            "dz": {
                # Mobile et fixe: 0X XX XX XX XX
                "general": re.compile(
                    r'(?:0|\+213|00\s*213)[\s.-]?[5-7][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
                    re.UNICODE
                )
            },
            
            # Patterns pour la Tunisie
            "tn": {
                # Mobile et fixe: XX XXX XXX
                "general": re.compile(
                    r'(?:0|\+216|00\s*216)[\s.-]?[2-9][\s.-]?\d{1}[\s.-]?\d{3}[\s.-]?\d{3}',
                    re.UNICODE
                )
            },
            
            # Patterns spécifiques pour les fax (souvent précédés de "Fax:")
            "fax": re.compile(
                r'(?:fax|télécopie|télécopieur)[\s:.-]*(\+?\d[\d\s.-]{6,20})',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Pattern pour numéros avec libellés (Tél., Mobile, etc.)
            "labeled": re.compile(
                r'(?:t[ée]l(?:[ée]phone)?|mobile|portable|fixe|bureau|domicile|direct)[\s:.-]*(\+?\d[\d\s.-]{6,20})',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Pattern générique pour capter les numéros sans contexte particulier
            "generic": re.compile(
                r'(?<![a-zA-Z0-9])(?:\+\d{1,4}[\s.-]?)?(?:\(?\d{1,4}\)?[\s.-]?)?(?:\d{2,4}[\s.-]?){2,5}\d{2,4}(?![a-zA-Z0-9])',
                re.UNICODE
            )
        }
        
        # Tentative de chargement des patterns supplémentaires depuis les fichiers
        try:
            patterns_file = os.path.join(self.resources_path, "patterns", "phone_patterns.json")
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    additional_patterns = json.load(f)
                    
                    # Conversion des patterns chargés en objets regex
                    for category, category_patterns in additional_patterns.items():
                        if isinstance(category_patterns, dict):
                            if category not in patterns:
                                patterns[category] = {}
                                
                            for pattern_name, pattern_str in category_patterns.items():
                                patterns[category][pattern_name] = re.compile(pattern_str, re.UNICODE)
                        else:
                            patterns[category] = re.compile(category_patterns, re.UNICODE)
        except Exception as e:
            self.logger.warning(f"Impossible de charger les patterns supplémentaires: {e}")
        
        return patterns
    
    def _load_reference_data(self) -> Dict[str, Any]:
        """
        Charge les données de référence pour la validation des numéros
        
        Returns:
            dict: Dictionnaire de données de référence
        """
        reference_data = {
            # Préfixes internationaux par pays
            "country_codes": {
                "fr": "33",
                "ma": "212",
                "sn": "221",
                "ci": "225",
                "cm": "237",
                "dz": "213",
                "tn": "216",
                "be": "32",
                "ch": "41",
                "ca": "1",
                "us": "1",
                "gb": "44",
                "de": "49",
                "es": "34",
                "it": "39"
            },
            
            # Validations spécifiques par pays
            "phone_formats": {
                "fr": {
                    "mobile": {
                        "length": 10,
                        "prefix": ["06", "07"],
                        "format": r"^0[67]\d{8}$"
                    },
                    "landline": {
                        "length": 10,
                        "prefix": ["01", "02", "03", "04", "05"],
                        "format": r"^0[1-5]\d{8}$"
                    },
                    "toll_free": {
                        "prefix": ["0800", "0801", "0802", "0803", "0804", "0805"],
                        "format": r"^0[8][0-5]\d{7}$"
                    },
                    "premium": {
                        "prefix": ["0890", "0891", "0892", "0893", "0897", "0898", "0899"],
                        "format": r"^0[8][9][0-9]\d{6}$"
                    }
                },
                "ma": {
                    "mobile": {
                        "length": 10,
                        "prefix": ["06", "07"],
                        "format": r"^0[67]\d{8}$"
                    },
                    "landline": {
                        "length": 10,
                        "prefix": ["05"],
                        "format": r"^0[5]\d{8}$"
                    }
                },
                "sn": {
                    "mobile": {
                        "prefix": ["77", "78"],
                        "format": r"^(?:0|\+221|00221)?[78]\d{8}$"
                    },
                    "landline": {
                        "prefix": ["33", "30"],
                        "format": r"^(?:0|\+221|00221)?[33]\d{8}$"
                    }
                }
            },
            
            # Formats d'affichage par pays
            "display_formats": {
                "fr": {
                    "national": "0X XX XX XX XX",
                    "international": "+33 X XX XX XX XX"
                },
                "ma": {
                    "national": "0X XX XX XX XX",
                    "international": "+212 X XX XX XX XX"
                },
                "sn": {
                    "national": "XX XXX XX XX",
                    "international": "+221 XX XXX XX XX"
                },
                "ci": {
                    "national": "XX XX XX XX XX",
                    "international": "+225 XX XX XX XX XX"
                },
                "cm": {
                    "national": "XXX XX XX XX",
                    "international": "+237 XXX XX XX XX"
                }
            }
        }
        
        # Tentative de chargement des données de référence depuis les fichiers
        try:
            ref_file = os.path.join(self.resources_path, "reference_data", "phone_formats.json")
            if os.path.exists(ref_file):
                with open(ref_file, 'r', encoding='utf-8') as f:
                    additional_data = json.load(f)
                    
                    # Fusion des données
                    for category, data in additional_data.items():
                        if category in reference_data:
                            if isinstance(data, dict) and isinstance(reference_data[category], dict):
                                self._merge_dicts(reference_data[category], data)
                            else:
                                reference_data[category] = data
                        else:
                            reference_data[category] = data
        
        except Exception as e:
            self.logger.warning(f"Erreur lors du chargement des données de référence: {e}")
        
        return reference_data
    
    def _merge_dicts(self, d1, d2):
        """
        Fusionne récursivement deux dictionnaires
        
        Args:
            d1: Premier dictionnaire (cible)
            d2: Deuxième dictionnaire (source)
        """
        for k, v in d2.items():
            if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
                self._merge_dicts(d1[k], v)
            else:
                d1[k] = v
    
    def recognize_phones(self, text: str) -> List[Dict[str, Any]]:
        """
        Reconnait et extrait tous les numéros de téléphone d'un texte
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            list: Liste des numéros trouvés avec leurs métadonnées
        """
        # Prétraitement du texte
        text = self._preprocess_text(text)
        
        # Liste pour stocker tous les numéros trouvés
        found_phones = []
        
        # Détecter d'abord les numéros avec labels (fax, tél, etc.)
        labeled_phones = self._extract_labeled_phones(text)
        found_phones.extend(labeled_phones)
        
        # Pour chaque pays, appliquer les patterns spécifiques
        for country_code, country_patterns in self.patterns.items():
            # Ignorer les patterns non-spécifiques aux pays
            if country_code not in self.reference_data["country_codes"]:
                continue
                
            # Appliquer les patterns par type pour ce pays
            if isinstance(country_patterns, dict):
                for phone_type, pattern in country_patterns.items():
                    phones = self._extract_phones_with_pattern(text, pattern, country_code, phone_type)
                    found_phones.extend(phones)
            else:
                # Si c'est un pattern unique pour le pays
                phones = self._extract_phones_with_pattern(text, country_patterns, country_code, "general")
                found_phones.extend(phones)
        
        # Appliquer les patterns internationaux
        for phone_type, pattern in self.patterns["international"].items():
            phones = self._extract_phones_with_pattern(text, pattern, None, phone_type)
            found_phones.extend(phones)
        
        # Appliquer le pattern générique pour capter les numéros restants
        generic_phones = self._extract_phones_with_pattern(text, self.patterns["generic"], None, "generic")
        
        # Filtrer les numéros génériques qui ne sont pas des doublons
        for phone in generic_phones:
            if not self._is_duplicate(found_phones, phone["value"]):
                found_phones.append(phone)
        
        # Tri par score de confiance
        found_phones.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        return found_phones
    
    def _extract_labeled_phones(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrait les numéros avec labels explicites (Tél, Fax, etc.)
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            list: Liste des numéros avec labels
        """
        labeled_phones = []
        
        # Extraction des fax
        fax_matches = self.patterns["fax"].finditer(text)
        for match in fax_matches:
            phone_number = match.group(1).strip()
            
            # Récupérer le contexte (30 caractères avant et après)
            start_pos = max(0, match.start() - 30)
            end_pos = min(len(text), match.end() + 30)
            context = text[start_pos:end_pos]
            
            # Déterminer le pays
            country_code = self._determine_country(phone_number, context)
            
            # Normaliser le numéro
            normalized_number = self._normalize_phone(phone_number, country_code)
            
            if normalized_number:
                phone_data = {
                    "value": normalized_number,
                    "raw_value": phone_number,
                    "type": PhoneType.FAX.value,
                    "country": country_code,
                    "confidence_score": 0.9,  # Score élevé car label explicite
                    "context": context,
                    "is_valid": self.validate_phone(normalized_number, country_code, PhoneType.FAX)["is_valid"],
                    "metadata": {
                        "has_label": True,
                        "label_type": "fax"
                    }
                }
                
                labeled_phones.append(phone_data)
        
        # Extraction des autres labels (tél, mobile, etc.)
        label_matches = self.patterns["labeled"].finditer(text)
        for match in label_matches:
            phone_number = match.group(1).strip()
            label = match.group(0).split(':')[0].strip().lower()
            
            # Récupérer le contexte
            start_pos = max(0, match.start() - 30)
            end_pos = min(len(text), match.end() + 30)
            context = text[start_pos:end_pos]
            
            # Déterminer le pays
            country_code = self._determine_country(phone_number, context)
            
            # Déterminer le type de téléphone
            phone_type = self._determine_phone_type(phone_number, label, country_code)
            
            # Normaliser le numéro
            normalized_number = self._normalize_phone(phone_number, country_code)
            
            if normalized_number:
                phone_data = {
                    "value": normalized_number,
                    "raw_value": phone_number,
                    "type": phone_type.value,
                    "country": country_code,
                    "confidence_score": 0.85,  # Score élevé car label explicite
                    "context": context,
                    "is_valid": self.validate_phone(normalized_number, country_code, phone_type)["is_valid"],
                    "metadata": {
                        "has_label": True,
                        "label_type": label
                    }
                }
                
                labeled_phones.append(phone_data)
        
        return labeled_phones
    
    def _extract_phones_with_pattern(self, text: str, pattern: re.Pattern, country_code: Optional[str], 
                                     pattern_type: str) -> List[Dict[str, Any]]:
        """
        Extrait les numéros correspondant à un pattern spécifique
        
        Args:
            text (str): Texte à analyser
            pattern (re.Pattern): Pattern à appliquer
            country_code (str, optional): Code pays du pattern
            pattern_type (str): Type de pattern (mobile, landline, etc.)
            
        Returns:
            list: Liste des numéros trouvés
        """
        found_phones = []
        
        matches = pattern.finditer(text)
        for match in matches:
            # Récupérer le numéro (groupe 1 si disponible, sinon groupe 0)
            phone_number = match.group(1) if match.groups() else match.group(0)
            phone_number = phone_number.strip()
            
            # Récupérer le contexte
            start_pos = max(0, match.start() - 30)
            end_pos = min(len(text), match.end() + 30)
            context = text[start_pos:end_pos]
            
            # Déterminer le pays si non spécifié
            detected_country = self._determine_country(phone_number, context) if not country_code else country_code
            
            # Déterminer le type de téléphone
            phone_type = self._determine_phone_type(phone_number, pattern_type, detected_country)
            
            # Normaliser le numéro
            normalized_number = self._normalize_phone(phone_number, detected_country)
            
            if normalized_number:
                # Vérifier que ce n'est pas un doublon
                if not self._is_duplicate(found_phones, normalized_number):
                    phone_data = {
                        "value": normalized_number,
                        "raw_value": phone_number,
                        "type": phone_type.value,
                        "country": detected_country,
                        "confidence_score": self._calculate_confidence(phone_number, phone_type, pattern_type, detected_country, context),
                        "context": context,
                        "is_valid": self.validate_phone(normalized_number, detected_country, phone_type)["is_valid"],
                        "metadata": {}
                    }
                    
                    found_phones.append(phone_data)
        
        return found_phones
    
    def _preprocess_text(self, text: str) -> str:
        """
        Prétraite le texte pour améliorer la reconnaissance des numéros
        
        Args:
            text (str): Texte à prétraiter
            
        Returns:
            str: Texte prétraité
        """
        # Normalisation des retours à la ligne
        text = re.sub(r'(\r\n|\r)', '\n', text)
        
        # Normalisation des espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Uniformisation des séparateurs de numéros
        text = text.replace('−', '-')  # Tiret long en tiret normal
        text = text.replace('‐', '-')  # Tiret court en tiret normal
        
        # Normalisation des indicatifs de format international
        text = re.sub(r'00\s*(\d{1,3})', r'+\1', text)  # 00XX en +XX
        
        return text
    
    def _determine_country(self, phone_number: str, context: str = None) -> str:
        """
        Détermine le pays d'origine d'un numéro de téléphone
        
        Args:
            phone_number (str): Numéro de téléphone
            context (str, optional): Contexte textuel
            
        Returns:
            str: Code pays
        """
        # Recherche d'un préfixe international au format +XX
        intl_match = re.match(r'\+(\d{1,4})', phone_number)
        if intl_match:
            country_prefix = intl_match.group(1)
            
            # Recherche du pays correspondant à ce préfixe
            for country, prefix in self.reference_data["country_codes"].items():
                if country_prefix == prefix or country_prefix.startswith(prefix):
                    return country
        
        # Recherche d'indices dans le contexte
        if context:
            context_lower = context.lower()
            
            # Mots-clés par pays
            country_keywords = {
                "fr": ["france", "français", "française"],
                "ma": ["maroc", "marocain", "marocaine"],
                "sn": ["sénégal", "sénégalais", "sénégalaise"],
                "ci": ["côte d'ivoire", "ivoirien", "ivoirienne"],
                "cm": ["cameroun", "camerounais", "camerounaise"],
                "dz": ["algérie", "algérien", "algérienne"],
                "tn": ["tunisie", "tunisien", "tunisienne"]
            }
            
            for country, keywords in country_keywords.items():
                for keyword in keywords:
                    if keyword in context_lower:
                        return country
        
        # Format spécifique à la France (0X XX XX XX XX)
        if re.match(r'^0[1-9](\s|-|\.)?', phone_number):
            return "fr"
        
        # Par défaut, retourner un code inconnu
        return "unknown"
    
    def _determine_phone_type(self, phone_number: str, pattern_type: str, country_code: str) -> PhoneType:
        """
        Détermine le type de numéro de téléphone
        
        Args:
            phone_number (str): Numéro de téléphone
            pattern_type (str): Type de pattern utilisé pour la détection
            country_code (str): Code pays
            
        Returns:
            PhoneType: Type de numéro
        """
        # Conversion des patterns en types
        if pattern_type == "mobile":
            return PhoneType.MOBILE
        elif pattern_type == "landline":
            return PhoneType.LANDLINE
        elif pattern_type == "fax":
            return PhoneType.FAX
        elif pattern_type == "toll_free":
            return PhoneType.TOLL_FREE
        elif pattern_type == "premium":
            return PhoneType.PREMIUM
        elif pattern_type in ["e164", "general"]:
            return PhoneType.INTERNATIONAL
        
        # Analyse du numéro lui-même
        clean_number = re.sub(r'[\s.-]', '', phone_number)
        
        # Vérification basée sur le pays
        if country_code == "fr":
            if clean_number.startswith("+33"):
                clean_number = "0" + clean_number[3:]
            
            if clean_number.startswith("06") or clean_number.startswith("07"):
                return PhoneType.MOBILE
            elif clean_number.startswith("01") or clean_number.startswith("02") or \
                 clean_number.startswith("03") or clean_number.startswith("04") or \
                 clean_number.startswith("05"):
                return PhoneType.LANDLINE
            elif clean_number.startswith("080"):
                return PhoneType.TOLL_FREE
            elif clean_number.startswith("089"):
                return PhoneType.PREMIUM
        
        elif country_code == "ma":
            if clean_number.startswith("+212"):
                clean_number = "0" + clean_number[4:]
            
            if clean_number.startswith("06") or clean_number.startswith("07"):
                return PhoneType.MOBILE
            elif clean_number.startswith("05"):
                return PhoneType.LANDLINE
        
        # Format international
        if phone_number.startswith("+"):
            return PhoneType.INTERNATIONAL
        
        # Par défaut
        return PhoneType.UNKNOWN
    
    def _normalize_phone(self, phone_number: str, country_code: str) -> Optional[str]:
        """
        Normalise un numéro de téléphone au format international
        
        Args:
            phone_number (str): Numéro de téléphone
            country_code (str): Code pays
            
        Returns:
            str: Numéro normalisé ou None si impossible
        """
        # Nettoyage initial du numéro
        clean_number = re.sub(r'[^\d+]', '', phone_number)  # Garder uniquement les chiffres et le +
        
        # Traiter selon le format
        if clean_number.startswith('+'):
            # Déjà au format international, juste nettoyage
            return clean_number
        
        # Format national, conversion vers international
        if country_code != "unknown" and country_code in self.reference_data["country_codes"]:
            country_prefix = self.reference_data["country_codes"][country_code]
            
            # Différents formats nationaux par pays
            if country_code == "fr":
                if clean_number.startswith('0'):
                    return f"+{country_prefix}{clean_number[1:]}"
            
            elif country_code == "ma":
                if clean_number.startswith('0'):
                    return f"+{country_prefix}{clean_number[1:]}"
            
            elif country_code in ["sn", "ci", "cm", "dz", "tn"]:
                # Suppression du 0 initial si présent
                if clean_number.startswith('0'):
                    clean_number = clean_number[1:]
                
                return f"+{country_prefix}{clean_number}"
            
            # Fallback: préfixe international + numéro
            return f"+{country_prefix}{clean_number}"
        
        # Si le pays est inconnu mais le numéro semble complet
        if len(clean_number) >= 8:
            # Tenter de déduire le pays
            if clean_number.startswith('0033') or clean_number.startswith('0033'):
                return f"+33{clean_number[4:]}"
            elif clean_number.startswith('00212') or clean_number.startswith('0212'):
                return f"+212{clean_number[5:]}"
            elif clean_number.startswith('06') or clean_number.startswith('07'):
                return f"+33{clean_number[1:]}"  # Hypothèse: numéro français
        
        # Pas de normalisation possible
        return None
    
    def _is_duplicate(self, found_phones: List[Dict[str, Any]], phone_number: str) -> bool:
        """
        Vérifie si un numéro est déjà dans la liste des numéros trouvés
        
        Args:
            found_phones (list): Liste des numéros trouvés
            phone_number (str): Numéro à vérifier
            
        Returns:
            bool: True si le numéro est un doublon
        """
        # Normalisation pour la comparaison
        clean_number = re.sub(r'[^\d+]', '', phone_number)
        
        # Supprimer le + pour la comparaison
        if clean_number.startswith('+'):
            clean_number = clean_number[1:]
        
        for found_phone in found_phones:
            found_clean = re.sub(r'[^\d+]', '', found_phone["value"])
            
            # Supprimer le + pour la comparaison
            if found_clean.startswith('+'):
                found_clean = found_clean[1:]
                
            # Si les numéros nettoyés correspondent
            if clean_number == found_clean:
                return True
            
            # Si l'un est un préfixe de l'autre (pour gérer les formats partiels)
            if len(clean_number) > 7 and len(found_clean) > 7:
                # Comparer les derniers chiffres (généralement les plus spécifiques)
                if clean_number[-8:] == found_clean[-8:]:
                    return True
        
        return False
    
    def _calculate_confidence(self, phone_number: str, phone_type: PhoneType, pattern_type: str, 
                             country_code: str, context: str = None) -> float:
        """
        Calcule un score de confiance pour le numéro extrait
        
        Args:
            phone_number (str): Numéro de téléphone
            phone_type (PhoneType): Type de numéro
            pattern_type (str): Type de pattern utilisé
            country_code (str): Code pays
            context (str, optional): Contexte textuel
            
        Returns:
            float: Score de confiance entre 0 et 1
        """
        score = 0.5  # Score de base
        
        # Bonus selon le type de pattern
        if pattern_type in ["mobile", "landline", "toll_free", "premium"]:
            score += 0.2  # Confiance élevée pour les patterns spécifiques
        elif pattern_type == "general":
            score += 0.1  # Confiance moyenne pour les patterns généraux
        elif pattern_type == "e164":
            score += 0.2  # Confiance élevée pour les formats E.164
        elif pattern_type == "generic":
            score += 0.0  # Pas de bonus pour les patterns génériques
        
        # Bonus pour la longueur du numéro
        clean_number = re.sub(r'[^\d+]', '', phone_number)
        if len(clean_number) >= 10:
            score += 0.1  # Bonus pour les numéros de longueur standard
        
        # Bonus pour les numéros avec préfixe international
        if clean_number.startswith('+'):
            score += 0.1
        
        # Vérification de la validité du numéro selon les règles du pays
        if country_code != "unknown":
            validation_result = self.validate_phone(clean_number, country_code, phone_type)
            if validation_result["is_valid"]:
                score += 0.1
        
        # Analyse du contexte
        if context:
            context_lower = context.lower()
            
            # Bonus si le contexte mentionne explicitement un téléphone
            phone_indicators = ["téléphone", "tél", "tel", "phone", "mobile", "portable", "appeler", "contacter"]
            if any(indicator in context_lower for indicator in phone_indicators):
                score += 0.1
            
            # Bonus spécifiques selon le type de téléphone
            if phone_type == PhoneType.MOBILE and any(term in context_lower for term in ["mobile", "portable", "gsm"]):
                score += 0.1
            elif phone_type == PhoneType.LANDLINE and any(term in context_lower for term in ["fixe", "domicile", "bureau"]):
                score += 0.1
            elif phone_type == PhoneType.FAX and "fax" in context_lower:
                score += 0.1
        
        # Plafonner à 1.0
        return min(1.0, score)
    
    def validate_phone(self, phone_number: str, country_code: str, phone_type: PhoneType) -> Dict[str, Any]:
        """
        Valide un numéro de téléphone selon les règles du pays
        
        Args:
            phone_number (str): Numéro de téléphone
            country_code (str): Code pays
            phone_type (PhoneType): Type de numéro
            
        Returns:
            dict: Résultat de la validation avec informations détaillées
        """
        result = {
            "is_valid": False,
            "issues": [],
            "details": {}
        }
        
        # Nettoyage du numéro
        clean_number = re.sub(r'[^\d+]', '', phone_number)
        
        # Vérification de base: longueur minimale
        if len(clean_number) < 8:
            result["issues"].append("too_short")
            return result
        
        # Format international
        if clean_number.startswith('+'):
            # Vérifier que le préfixe international correspond au pays
            if country_code != "unknown" and country_code in self.reference_data["country_codes"]:
                expected_prefix = self.reference_data["country_codes"][country_code]
                if not clean_number.startswith(f"+{expected_prefix}"):
                    result["issues"].append("wrong_country_prefix")
        
        # Validation spécifique par pays
        if country_code in self.reference_data["phone_formats"]:
            country_formats = self.reference_data["phone_formats"][country_code]
            
            # Convertir en format national pour la validation
            national_number = clean_number
            if clean_number.startswith('+'):
                # Supprimer le préfixe international
                prefix = self.reference_data["country_codes"].get(country_code, "")
                if clean_number.startswith(f"+{prefix}"):
                    # Pour la France et le Maroc, ajouter le 0 initial
                    if country_code in ["fr", "ma"]:
                        national_number = "0" + clean_number[len(prefix)+1:]
                    else:
                        national_number = clean_number[len(prefix)+1:]
            
            # Validation selon le type de téléphone
            phone_type_str = phone_type.value
            
            if phone_type_str in country_formats:
                type_format = country_formats[phone_type_str]
                
                # Vérification du format par regex
                if "format" in type_format:
                    format_pattern = type_format["format"]
                    if not re.match(format_pattern, national_number):
                        result["issues"].append("invalid_format")
                
                # Vérification de la longueur
                if "length" in type_format and len(national_number) != type_format["length"]:
                    result["issues"].append("wrong_length")
                
                # Vérification du préfixe
                if "prefix" in type_format:
                    valid_prefix = False
                    for prefix in type_format["prefix"]:
                        if national_number.startswith(prefix):
                            valid_prefix = True
                            break
                    
                    if not valid_prefix:
                        result["issues"].append("invalid_prefix")
            
            # Si aucun format spécifique pour ce type mais qu'il y a un format "general"
            elif "general" in country_formats:
                general_format = country_formats["general"]
                
                # Vérification du format général
                if "format" in general_format and not re.match(general_format["format"], national_number):
                    result["issues"].append("invalid_format")
        
        # Validation de base pour les pays sans règles spécifiques
        else:
            # Vérifier que le numéro contient uniquement des chiffres (et éventuellement un +)
            if not re.match(r'^\+?\d+', clean_number):
                result["issues"].append("invalid_characters")
            
            # Vérifier que la longueur est raisonnable (entre 8 et 15 chiffres)
            digit_count = len(re.sub(r'[^\d]', '', clean_number))
            if digit_count < 8:
                result["issues"].append("too_short")
            elif digit_count > 15:
                result["issues"].append("too_long")
        
        # Le numéro est valide s'il n'y a pas de problèmes
        result["is_valid"] = len(result["issues"]) == 0
        
        return result
    
    def format_phone(self, phone_number: str, country_code: str = None, format_type: str = "international") -> str:
        """
        Formate un numéro de téléphone selon un format spécifique
        
        Args:
            phone_number (str): Numéro de téléphone
            country_code (str, optional): Code pays
            format_type (str): Type de formatage (international, national, e164)
            
        Returns:
            str: Numéro formaté
        """
        # Nettoyage du numéro
        clean_number = re.sub(r'[^\d+]', '', phone_number)
        
        # Déterminer le pays si non spécifié
        if not country_code or country_code == "unknown":
            # Tenter de déterminer à partir du préfixe international
            if clean_number.startswith('+'):
                for country, prefix in self.reference_data["country_codes"].items():
                    if clean_number.startswith(f"+{prefix}"):
                        country_code = country
                        break
            
            # Si toujours inconnu, utiliser "fr" par défaut
            if not country_code or country_code == "unknown":
                country_code = "fr"
        
        # Format E.164 (compact, sans espace, avec +)
        if format_type == "e164":
            if clean_number.startswith('+'):
                return clean_number
            else:
                # Convertir en format international
                if country_code in self.reference_data["country_codes"]:
                    prefix = self.reference_data["country_codes"][country_code]
                    
                    # Supprimer le 0 initial si présent (pour les numéros français, marocains, etc.)
                    if clean_number.startswith('0'):
                        clean_number = clean_number[1:]
                    
                    return f"+{prefix}{clean_number}"
                else:
                    return clean_number  # Impossible de normaliser
        
        # Format international (avec espaces)
        elif format_type == "international":
            # Utiliser le format d'affichage du pays si disponible
            if country_code in self.reference_data["display_formats"]:
                display_format = self.reference_data["display_formats"][country_code]["international"]
                
                # Normaliser d'abord en E.164
                e164 = self.format_phone(phone_number, country_code, "e164")
                
                # Retirer le préfixe international pour le formatage
                prefix = self.reference_data["country_codes"].get(country_code, "")
                prefix_str = f"+{prefix}"
                
                if e164.startswith(prefix_str):
                    digits = e164[len(prefix_str):]
                    
                    # Remplacer les X dans le format par les chiffres du numéro
                    formatted = display_format
                    for digit in digits:
                        formatted = formatted.replace('X', digit, 1)
                    
                    # Si le numéro est plus long que le format, ajouter les chiffres restants
                    extra_digits = digits[formatted.count('X'):]
                    if extra_digits:
                        formatted = formatted.replace('X', '') + ' ' + ' '.join(extra_digits)
                    
                    return formatted
            
            # Format générique: groupes de 2 chiffres séparés par des espaces
            if clean_number.startswith('+'):
                parts = [clean_number[0:3]]  # Préfixe international (+XX)
                
                for i in range(3, len(clean_number), 2):
                    parts.append(clean_number[i:i+2])
                
                return ' '.join(parts)
            else:
                # Convertir d'abord en format international
                return self.format_phone(self.format_phone(phone_number, country_code, "e164"), country_code, "international")
        
        # Format national (spécifique au pays)
        elif format_type == "national":
            # Utiliser le format d'affichage du pays si disponible
            if country_code in self.reference_data["display_formats"]:
                display_format = self.reference_data["display_formats"][country_code]["national"]
                
                # Normaliser d'abord en E.164
                e164 = self.format_phone(phone_number, country_code, "e164")
                
                # Retirer le préfixe international pour le formatage
                prefix = self.reference_data["country_codes"].get(country_code, "")
                prefix_str = f"+{prefix}"
                
                if e164.startswith(prefix_str):
                    # Convertir en format national (ajouter 0 pour certains pays)
                    if country_code in ["fr", "ma"]:
                        national_digits = "0" + e164[len(prefix_str):]
                    else:
                        national_digits = e164[len(prefix_str):]
                    
                    # Remplacer les X dans le format par les chiffres du numéro
                    formatted = display_format
                    for digit in national_digits:
                        formatted = formatted.replace('X', digit, 1)
                    
                    return formatted
            
            # Format générique: convertir en e164 puis retirer le préfixe international
            e164 = self.format_phone(phone_number, country_code, "e164")
            
            # Retirer le préfixe international
            prefix = self.reference_data["country_codes"].get(country_code, "")
            if e164.startswith(f"+{prefix}"):
                national = e164[len(prefix)+1:]
                
                # Ajouter le 0 initial pour certains pays
                if country_code in ["fr", "ma"]:
                    national = "0" + national
                
                # Formatter en groupes de 2 chiffres
                parts = []
                for i in range(0, len(national), 2):
                    parts.append(national[i:i+2])
                
                return ' '.join(parts)
        
        # Par défaut, retourner le numéro nettoyé
        return clean_number
    
    def get_phone_metadata(self, phone_number: str, country_code: str = None) -> Dict[str, Any]:
        """
        Récupère des métadonnées pour un numéro de téléphone
        
        Args:
            phone_number (str): Numéro de téléphone
            country_code (str, optional): Code pays
            
        Returns:
            dict: Métadonnées du numéro
        """
        # Nettoyage et normalisation
        clean_number = re.sub(r'[^\d+]', '', phone_number)
        
        # Déterminer le pays si non spécifié
        if not country_code or country_code == "unknown":
            # Tenter de déterminer à partir du préfixe international
            if clean_number.startswith('+'):
                for country, prefix in self.reference_data["country_codes"].items():
                    if clean_number.startswith(f"+{prefix}"):
                        country_code = country
                        break
        
        # Déterminer le type de téléphone
        phone_type = self._determine_phone_type(clean_number, "general", country_code)
        
        # Valider le numéro
        validation_result = self.validate_phone(clean_number, country_code, phone_type)
        
        # Préparer les métadonnées
        metadata = {
            "country": country_code,
            "country_name": self._get_country_name(country_code),
            "type": phone_type.value,
            "formats": {
                "e164": self.format_phone(phone_number, country_code, "e164"),
                "international": self.format_phone(phone_number, country_code, "international"),
                "national": self.format_phone(phone_number, country_code, "national")
            },
            "validation": validation_result
        }
        
        # Ajouter des informations spécifiques selon le pays
        if country_code == "fr":
            # Déterminer la région en France (basé sur l'indicatif)
            if clean_number.startswith('+33'):
                region_code = clean_number[3:4]
            elif clean_number.startswith('0'):
                region_code = clean_number[1:2]
            else:
                region_code = None
            
            if region_code:
                region_map = {
                    "1": "Île-de-France",
                    "2": "Nord-Ouest",
                    "3": "Nord-Est",
                    "4": "Sud-Est",
                    "5": "Sud-Ouest",
                    "6": "Mobile",
                    "7": "Mobile",
                    "8": "Numéro spécial",
                    "9": "VoIP/Internet"
                }
                
                metadata["region"] = region_map.get(region_code)
        
        return metadata
    
    def _get_country_name(self, country_code: str) -> str:
        """
        Récupère le nom complet d'un pays à partir de son code
        
        Args:
            country_code (str): Code pays
            
        Returns:
            str: Nom du pays
        """
        country_names = {
            "fr": "France",
            "ma": "Maroc",
            "sn": "Sénégal",
            "ci": "Côte d'Ivoire",
            "cm": "Cameroun",
            "dz": "Algérie",
            "tn": "Tunisie",
            "be": "Belgique",
            "ch": "Suisse",
            "ca": "Canada",
            "us": "États-Unis",
            "gb": "Royaume-Uni",
            "de": "Allemagne",
            "es": "Espagne",
            "it": "Italie"
        }
        
        return country_names.get(country_code, "Pays inconnu")
    
    def find_phones_by_type(self, text: str, phone_type: PhoneType, country_code: str = None) -> List[Dict[str, Any]]:
        """
        Recherche des numéros d'un type spécifique dans le texte
        
        Args:
            text (str): Texte à analyser
            phone_type (PhoneType): Type de numéro à rechercher
            country_code (str, optional): Code pays pour filtrer les résultats
            
        Returns:
            list: Liste des numéros du type demandé
        """
        # Récupérer tous les numéros
        all_phones = self.recognize_phones(text)
        
        # Filtrer par type
        filtered_phones = [phone_data for phone_data in all_phones if phone_data["type"] == phone_type.value]
        
        # Filtrer par pays si demandé
        if country_code:
            filtered_phones = [phone_data for phone_data in filtered_phones if phone_data["country"] == country_code]
        
        return filtered_phones
    
    def extract_best_phone(self, text: str, phone_type: PhoneType = None, country_code: str = None) -> Optional[Dict[str, Any]]:
        """
        Extrait le meilleur numéro du type spécifié dans le texte
        
        Args:
            text (str): Texte à analyser
            phone_type (PhoneType, optional): Type de numéro à rechercher
            country_code (str, optional): Code pays pour filtrer les résultats
            
        Returns:
            dict: Meilleur numéro trouvé ou None si aucun
        """
        # Récupérer tous les numéros
        all_phones = self.recognize_phones(text)
        
        # Si aucun numéro trouvé
        if not all_phones:
            return None
        
        # Filtrer par type si demandé
        if phone_type:
            filtered_phones = [phone_data for phone_data in all_phones if phone_data["type"] == phone_type.value]
            
            # Filtrer par pays si demandé
            if country_code:
                filtered_phones = [phone_data for phone_data in filtered_phones if phone_data["country"] == country_code]
            
            # Si aucun numéro après filtrage
            if not filtered_phones:
                return None
            
            # Retourner celui avec le meilleur score de confiance
            return max(filtered_phones, key=lambda x: x["confidence_score"])
        
        # Si pas de type spécifié, filtrer seulement par pays si demandé
        if country_code:
            filtered_phones = [phone_data for phone_data in all_phones if phone_data["country"] == country_code]
            
            # Si aucun numéro après filtrage
            if not filtered_phones:
                return None
            
            # Retourner celui avec le meilleur score de confiance
            return max(filtered_phones, key=lambda x: x["confidence_score"])
        
        # Sinon, retourner simplement le numéro avec le meilleur score
        return max(all_phones, key=lambda x: x["confidence_score"])


# Fonction autonome pour utilisation directe
def extract_phones(text, phone_type=None, country_code=None):
    """
    Fonction autonome pour extraire les numéros de téléphone d'un texte
    
    Args:
        text (str): Texte à analyser
        phone_type (str, optional): Type de numéro à rechercher
        country_code (str, optional): Code pays pour filtrer les résultats
        
    Returns:
        list: Liste des numéros trouvés
    """
    recognizer = PhoneRecognizer()
    
    # Convertir le type si spécifié
    phone_type_enum = None
    if phone_type:
        try:
            phone_type_enum = PhoneType[phone_type.upper()]
        except (KeyError, AttributeError):
            # Essayer de mapper le nom
            type_mapping = {
                "mobile": PhoneType.MOBILE,
                "portable": PhoneType.MOBILE,
                "gsm": PhoneType.MOBILE,
                "fixe": PhoneType.LANDLINE,
                "landline": PhoneType.LANDLINE,
                "fax": PhoneType.FAX,
                "gratuit": PhoneType.TOLL_FREE,
                "vert": PhoneType.TOLL_FREE,
                "toll_free": PhoneType.TOLL_FREE,
                "surtaxe": PhoneType.PREMIUM,
                "premium": PhoneType.PREMIUM,
                "international": PhoneType.INTERNATIONAL
            }
            
            phone_type_lower = phone_type.lower()
            for key, value in type_mapping.items():
                if key in phone_type_lower:
                    phone_type_enum = value
                    break
    
    # Si un type a été spécifié et trouvé
    if phone_type and phone_type_enum:
        return recognizer.find_phones_by_type(text, phone_type_enum, country_code)
    
    # Sinon, extraire tous les numéros
    phones = recognizer.recognize_phones(text)
    
    # Filtrer par pays si demandé
    if country_code:
        phones = [phone for phone in phones if phone["country"] == country_code]
    
    return phones


if __name__ == "__main__":
    # Test de la classe avec un exemple de texte
    import argparse
    
    parser = argparse.ArgumentParser(description="Reconnaisseur de numéros de téléphone")
    parser.add_argument("--file", help="Fichier texte à analyser")
    parser.add_argument("--text", help="Texte à analyser directement")
    parser.add_argument("--type", help="Type de numéro à rechercher")
    parser.add_argument("--country", help="Code pays (fr, ma, sn, etc.)")
    args = parser.parse_args()
    
    # Configurer le logger pour le test
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    recognizer = PhoneRecognizer()
    sample_text = ""
    
    # Lecture depuis un fichier
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                sample_text = f.read()
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier: {e}")
            exit(1)
    # Utilisation du texte fourni en argument
    elif args.text:
        sample_text = args.text
    # Texte d'exemple
    else:
        sample_text = """
        Contrat de prestation de services
        
        Entre les soussignés :
        
        Monsieur Jean DUPONT, né le 15/04/1980 à Paris (75), demeurant 123 Avenue de la République, 75011 Paris,
        Téléphone : 06 12 34 56 78
        Email : jean.dupont@email.com
        
        Et
        
        La société ABC Consulting, dont le siège social est situé 45 Rue du Commerce,
        75015, Paris, représentée par Madame Marie MARTIN en sa qualité de Directrice Générale,
        Tél: 01.45.67.89.10
        Fax: +33 1 45 67 89 11
        
        Pour toute assistance technique, appelez notre service client au 0800 123 456.
        Pour les réclamations, composez le 08 92 68 31 41.
        
        Notre représentant au Maroc peut être joint au +212 5 22 22 22 22.
        Notre bureau au Sénégal: +221 77 333 44 55
        
        Fait à Paris, le 10/01/2023
        """
    
    # Extraction des numéros
    phone_type_enum = None
    if args.type:
        try:
            phone_type_enum = PhoneType[args.type.upper()]
        except KeyError:
            print(f"Type de numéro non reconnu: {args.type}")
            print(f"Types disponibles: {', '.join([t.name for t in PhoneType])}")
            exit(1)
    
    if phone_type_enum:
        phones = recognizer.find_phones_by_type(sample_text, phone_type_enum, args.country)
    else:
        phones = recognizer.recognize_phones(sample_text)
        
        # Filtrer par pays si demandé
        if args.country:
            phones = [phone for phone in phones if phone["country"] == args.country]
    
    print(f"Numéros trouvés: {len(phones)}")
    
    # Affichage des résultats
    for i, phone_data in enumerate(phones):
        print(f"\nNuméro {i+1}:")
        print(f"Valeur: {phone_data['value']}")
        print(f"Valeur brute: {phone_data['raw_value']}")
        print(f"Type: {phone_data['type']}")
        print(f"Pays: {phone_data['country']}")
        print(f"Score de confiance: {phone_data['confidence_score']:.2f}")
        print(f"Valide: {phone_data['is_valid']}")
        
        if "metadata" in phone_data and phone_data["metadata"]:
            print("Métadonnées:")
            for key, value in phone_data["metadata"].items():
                print(f"  {key}: {value}")
        
        print(f"Contexte: ...{phone_data['context']}...")
        
        # Formatage pour démonstration
        metadata = recognizer.get_phone_metadata(phone_data["value"], phone_data["country"])
        print("Formats disponibles:")
        for format_name, formatted in metadata["formats"].items():
            print(f"  {format_name}: {formatted}")
        
        if "region" in metadata:
            print(f"Région: {metadata['region']}")