#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de reconnaissance et validation d'adresses pour Vynal Docs Automator
Ce module permet d'identifier, extraire et normaliser les adresses postales
dans différents formats et contextes, avec support des spécificités régionales.
"""

import re
import os
import logging
import json
from typing import Dict, List, Optional, Tuple, Union, Any
import unicodedata

# Configuration du logger
logger = logging.getLogger("VynalDocsAutomator.DocAnalyzer.AddressRecognizer")

class AddressRecognizer:
    """
    Classe responsable de la reconnaissance et validation des adresses postales
    """
    
    def __init__(self, resources_path=None):
        """
        Initialisation du reconnaisseur d'adresses
        
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
        
        self.logger.info("Reconnaisseur d'adresses initialisé")
    
    def _load_patterns(self) -> Dict[str, Any]:
        """
        Charge les patterns regex pour la reconnaissance d'adresses
        
        Returns:
            dict: Dictionnaire de patterns par type et pays
        """
        patterns = {}
        
        # Patterns génériques (internationaux)
        patterns["generic"] = {
            # Pattern pour détecter une adresse complète
            "full_address": re.compile(
                r"(?:adresse|address|domicile|résid(?:ence|ant)|demeurant\s+(?:à|au)|situé\s+(?:à|au))[\s:]*([^\n]{5,150}?)(?:\n|$|(?:\s{2,}))",
                re.IGNORECASE | re.UNICODE
            ),
            
            # Pattern pour un numéro et nom de rue
            "street": re.compile(
                r"(?:\s|^)(\d+\s*(?:bis|ter|quater)?\s*(?:,|\.|\s)\s*(?:rue|avenue|boulevard|bd|bvd|blvd|chemin|route|cours|place|impasse|allée|voie|quai|passage|square|hameau|rond[- ]point|r\.p\.|lotissement|résidence|cité|domaine|lieu[- ]dit|zone|parc|clos)(?:[^\d\n]{1,60}))",
                re.IGNORECASE | re.UNICODE
            ),
            
            # Pattern pour extraire une boîte postale
            "po_box": re.compile(
                r"(?:bo[îi]te\s+postale|b\.?p\.?|post\s+office\s+box|p\.?o\.?\s*box)\s*[n°]?\s*(\d+)",
                re.IGNORECASE | re.UNICODE
            ),
            
            # Pattern pour extraire un code postal générique
            "postal_code": re.compile(
                r"(?:\s|^)(\d{4,7})(?:\s|$)",
                re.UNICODE
            ),
            
            # Pattern pour extraire une ville
            "city": re.compile(
                r"(?:^|\s|\d)([A-ZÀ-Ö][a-zà-ö]+(?:[-'\s][A-ZÀ-Ö][a-zà-ö]+)*(?:\s+(?:Cedex|cedex)(?:\s+\d+)?)?)",
                re.UNICODE
            ),
            
            # Pattern pour extraire un pays
            "country": re.compile(
                r"(?:pays|country|état|nation)\s*:?\s*([A-ZÀ-Ö][a-zà-ö]+(?:[-'\s][A-ZÀ-Ö][a-zà-ö]+)*)",
                re.IGNORECASE | re.UNICODE
            )
        }
        
        # Patterns spécifiques à la France
        patterns["fr"] = {
            # Code postal français (5 chiffres)
            "postal_code": re.compile(
                r"(?:\s|^)(\d{5})(?:\s|$)",
                re.UNICODE
            ),
            
            # Pattern spécifique pour les CEDEX
            "cedex": re.compile(
                r"(?:\s|^)(\d{5})\s+([A-ZÀ-Ö][a-zà-ö]+(?:[-'\s][A-ZÀ-Ö][a-zà-ö]+)*)\s+(?:CEDEX|Cedex|cedex)(?:\s+(\d+))?",
                re.UNICODE
            ),
            
            # Complément d'adresse français (étage, bâtiment, etc.)
            "address_complement": re.compile(
                r"(?:bâtiment|bat\.|bât\.|immeuble|résidence|rés\.|escalier|esc\.|étage|appartement|appt?\.)\s+([A-Za-z0-9]{1,10})",
                re.IGNORECASE | re.UNICODE
            )
        }
        
        # Patterns spécifiques au Maroc
        patterns["ma"] = {
            # Code postal marocain (5 chiffres)
            "postal_code": re.compile(
                r"(?:\s|^)(\d{5})(?:\s|$)",
                re.UNICODE
            )
        }
        
        # Patterns spécifiques au Sénégal
        patterns["sn"] = {
            # Code postal sénégalais (5 chiffres commençant par 1-8)
            "postal_code": re.compile(
                r"(?:\s|^)([1-8]\d{4})(?:\s|$)",
                re.UNICODE
            )
        }
        
        # Patterns spécifiques à la Côte d'Ivoire
        patterns["ci"] = {
            # Abidjan spécifiques (communes numérotées)
            "abidjan_commune": re.compile(
                r"(?:abidjan|commune)\s+(\d{1,2})",
                re.IGNORECASE | re.UNICODE
            ),
            
            # Boîtes postales (très courantes en CI)
            "po_box": re.compile(
                r"(?:bo[îi]te\s+postale|b\.?p\.?)\s*[n°]?\s*(\d+)(?:\s+([A-ZÀ-Ö][a-zà-ö]+(?:[-'\s][A-ZÀ-Ö][a-zà-ö]+)*))?",
                re.IGNORECASE | re.UNICODE
            )
        }
        
        # Patterns spécifiques au Cameroun
        patterns["cm"] = {
            # Boîtes postales (très courantes au Cameroun)
            "po_box": re.compile(
                r"(?:bo[îi]te\s+postale|b\.?p\.?)\s*[n°]?\s*(\d+)(?:\s+([A-ZÀ-Ö][a-zà-ö]+(?:[-'\s][A-ZÀ-Ö][a-zà-ö]+)*))?",
                re.IGNORECASE | re.UNICODE
            )
        }
        
        # Tentative de chargement des patterns supplémentaires depuis les fichiers
        try:
            patterns_file = os.path.join(self.resources_path, "patterns", "address_patterns.json")
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    additional_patterns = json.load(f)
                    
                    # Conversion des patterns chargés en objets regex
                    for country, country_patterns in additional_patterns.items():
                        if country not in patterns:
                            patterns[country] = {}
                            
                        for pattern_name, pattern_str in country_patterns.items():
                            patterns[country][pattern_name] = re.compile(pattern_str, re.IGNORECASE | re.UNICODE)
        except Exception as e:
            self.logger.warning(f"Impossible de charger les patterns supplémentaires: {e}")
        
        return patterns
    
    def _load_reference_data(self) -> Dict[str, Any]:
        """
        Charge les données de référence pour la validation d'adresses
        
        Returns:
            dict: Dictionnaire de données de référence
        """
        reference_data = {
            "countries": set(),
            "cities": {
                "fr": set(),
                "ma": set(),
                "sn": set(),
                "ci": set(),
                "cm": set(),
                "dz": set(),
                "tn": set()
            },
            "postal_code_formats": {
                "fr": r"^\d{5}$",
                "ma": r"^\d{5}$",
                "sn": r"^[1-8]\d{4}$",
                "ci": r"^\d{4}$",
                "cm": r"^\d{3,5}$",
                "dz": r"^\d{5}$",
                "tn": r"^\d{4}$"
            },
            "address_keywords": {
                "fr": ["rue", "avenue", "boulevard", "place", "impasse", "allée", "route", 
                      "chemin", "quai", "cours", "square", "résidence", "lotissement"],
                "ma": ["rue", "avenue", "boulevard", "place", "quartier", "hay", "résidence", 
                      "lotissement", "immeuble", "شارع", "زنقة", "حي", "إقامة"],
                "sn": ["rue", "avenue", "boulevard", "route", "place", "cité", "quartier", "villa"],
                "ci": ["rue", "avenue", "boulevard", "place", "quartier", "commune", "cité", "carrefour"],
                "cm": ["rue", "avenue", "boulevard", "route", "carrefour", "quartier", "lieu-dit"]
            },
            "address_formats": {
                "fr": {
                    "order": ["street_number", "street_name", "postal_code", "city"],
                    "separators": [" ", ", ", "\n"]
                },
                "ma": {
                    "order": ["street_number", "street_name", "district", "postal_code", "city"],
                    "separators": [" ", ", ", "\n"]
                },
                "ci": {
                    "order": ["street_name", "district", "po_box", "city"],
                    "separators": [" ", ", ", "\n"]
                }
            },
            "substitutions": {
                "cities": {
                    "casablanca": "Casablanca",
                    "rabat": "Rabat",
                    "abidjan": "Abidjan",
                    "dakar": "Dakar",
                    "yaounde": "Yaoundé",
                    "douala": "Douala"
                },
                "countries": {
                    "france": "France", 
                    "maroc": "Maroc", 
                    "morocco": "Maroc", 
                    "senegal": "Sénégal", 
                    "cote d'ivoire": "Côte d'Ivoire", 
                    "ivory coast": "Côte d'Ivoire", 
                    "cameroun": "Cameroun", 
                    "cameroon": "Cameroun"
                }
            }
        }
        
        # Tentative de chargement des données de référence depuis les fichiers
        try:
            ref_dir = os.path.join(self.resources_path, "reference_data")
            
            # Chargement des pays
            countries_file = os.path.join(ref_dir, "countries.txt")
            if os.path.exists(countries_file):
                with open(countries_file, 'r', encoding='utf-8') as f:
                    reference_data["countries"] = {line.strip() for line in f if line.strip()}
            
            # Chargement des villes par pays
            for country_code in reference_data["cities"]:
                cities_file = os.path.join(ref_dir, f"cities_{country_code}.txt")
                if os.path.exists(cities_file):
                    with open(cities_file, 'r', encoding='utf-8') as f:
                        reference_data["cities"][country_code] = {line.strip() for line in f if line.strip()}
        
        except Exception as e:
            self.logger.warning(f"Erreur lors du chargement des données de référence: {e}")
        
        return reference_data
    
    def recognize_address(self, text: str, country_code: str = None) -> Dict[str, Any]:
        """
        Reconnait et extrait les adresses d'un texte
        
        Args:
            text (str): Texte à analyser
            country_code (str, optional): Code pays pour appliquer des règles spécifiques
            
        Returns:
            dict: Adresse extraite avec ses composants
        """
        # Prétraitement du texte
        text = self._preprocess_text(text)
        
        # Détection du pays si non spécifié
        detected_country = self._detect_country(text)
        country_code = country_code or detected_country
        
        # Initialisation du résultat
        result = {
            "full_address": None,
            "street_number": None,
            "street_name": None,
            "address_complement": None,
            "po_box": None,
            "district": None,
            "postal_code": None,
            "city": None,
            "state": None,  # Région/État/Province
            "country": None,
            "country_code": country_code,
            "confidence_score": 0.0,
            "normalized_address": None
        }
        
        # Extraction de l'adresse complète
        full_address_match = self.patterns["generic"]["full_address"].search(text)
        if full_address_match:
            result["full_address"] = full_address_match.group(1).strip()
            # Analyse des composants de l'adresse complète
            if result["full_address"]:
                self._parse_address_components(result["full_address"], result, country_code)
        
        # Si pas d'adresse complète identifiée, extraction composant par composant
        if not result["full_address"]:
            self._extract_address_components(text, result, country_code)
        
        # Normalisation de l'adresse
        if self._has_minimum_components(result):
            result["normalized_address"] = self._normalize_address(result)
        
        # Calcul du score de confiance
        result["confidence_score"] = self._calculate_confidence_score(result)
        
        return result
    
    def _preprocess_text(self, text: str) -> str:
        """
        Prétraite le texte pour améliorer la reconnaissance d'adresses
        
        Args:
            text (str): Texte à prétraiter
            
        Returns:
            str: Texte prétraité
        """
        # Normalisation des caractères (suppression des accents superflus)
        text = unicodedata.normalize('NFKD', text)
        
        # Normalisation des retours à la ligne
        text = re.sub(r'(\r\n|\r)', '\n', text)
        
        # Normalisation des espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Normalisation des abréviations courantes
        abbreviations = {
            r'\bave\b': 'avenue',
            r'\bavenue\b': 'avenue',
            r'\bbd\b': 'boulevard',
            r'\bblvd\b': 'boulevard',
            r'\bbvd\b': 'boulevard',
            r'\bbat\.?\b': 'bâtiment',
            r'\bappt\.?\b': 'appartement',
            r'\bapt\.?\b': 'appartement',
            r'\bch\.?\b': 'chemin',
            r'\bpl\.?\b': 'place',
            r'\bst\.?\b': 'saint',
            r'\bste\.?\b': 'sainte',
            r'\bimp\.?\b': 'impasse',
            r'\brte\.?\b': 'route',
            r'\besclr?\.?\b': 'escalier',
            r'\bétg?\.?\b': 'étage'
        }
        
        for abbr, full in abbreviations.items():
            text = re.sub(abbr, full, text, flags=re.IGNORECASE)
        
        return text
    
    def _detect_country(self, text: str) -> Optional[str]:
        """
        Détecte le code pays à partir du texte
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            str: Code pays détecté ou None
        """
        text_lower = text.lower()
        
        # Détection par mention explicite de pays
        country_match = self.patterns["generic"]["country"].search(text)
        if country_match:
            country_name = country_match.group(1).strip().lower()
            
            # Normalisation du nom de pays
            for key, value in self.reference_data["substitutions"]["countries"].items():
                if country_name == key.lower():
                    country_name = value.lower()
                    break
            
            # Mapping des noms de pays vers les codes
            country_mapping = {
                "france": "fr",
                "maroc": "ma",
                "sénégal": "sn",
                "senegal": "sn",
                "côte d'ivoire": "ci",
                "cote d'ivoire": "ci",
                "cameroun": "cm",
                "algérie": "dz",
                "algerie": "dz",
                "tunisie": "tn"
            }
            
            if country_name in country_mapping:
                return country_mapping[country_name]
        
        # Détection par format de code postal
        for country_code, pattern in self.reference_data["postal_code_formats"].items():
            # Création d'un regex à partir du pattern
            postal_regex = re.compile(pattern)
            # Recherche de tous les codes postaux correspondants
            matches = postal_regex.findall(text)
            if matches:
                return country_code
        
        # Détection par mots-clés spécifiques au pays
        country_indicators = {
            "fr": ["france", "cedex", "département"],
            "ma": ["maroc", "morocco", "casablanca", "rabat", "tanger", "hay", "quartier"],
            "sn": ["sénégal", "senegal", "dakar", "thiès", "thies"],
            "ci": ["côte d'ivoire", "cote d'ivoire", "ivory coast", "abidjan", "commune"],
            "cm": ["cameroun", "cameroon", "yaoundé", "yaounde", "douala"]
        }
        
        for country_code, indicators in country_indicators.items():
            for indicator in indicators:
                if re.search(r'\b' + re.escape(indicator) + r'\b', text_lower):
                    return country_code
        
        # Détection par les villes connues
        for country_code, cities in self.reference_data["cities"].items():
            for city in cities:
                if re.search(r'\b' + re.escape(city.lower()) + r'\b', text_lower):
                    return country_code
        
        # Pas de pays détecté clairement
        return None
    
    def _parse_address_components(self, address: str, result: Dict[str, Any], country_code: str):
        """
        Analyse les composants d'une adresse complète
        
        Args:
            address (str): Adresse complète
            result (dict): Dictionnaire de résultats à compléter
            country_code (str): Code pays
        """
        # Extraction du code postal
        postal_pattern = self.patterns.get(country_code, {}).get("postal_code", self.patterns["generic"]["postal_code"])
        postal_match = postal_pattern.search(address)
        if postal_match:
            result["postal_code"] = postal_match.group(1)
        
        # Extraction de la rue
        street_match = self.patterns["generic"]["street"].search(address)
        if street_match:
            street = street_match.group(1).strip()
            
            # Tentative d'extraction du numéro de rue
            number_match = re.match(r'(\d+\s*(?:bis|ter|quater)?)[,\s.]', street)
            if number_match:
                result["street_number"] = number_match.group(1).strip()
                # Extraction du nom de rue (reste après le numéro)
                result["street_name"] = street[number_match.end():].strip()
            else:
                result["street_name"] = street
        
        # Extraction de la ville
        city_match = self.patterns["generic"]["city"].search(address)
        if city_match:
            city = city_match.group(1).strip()
            
            # Normaliser le nom de la ville
            city_lower = city.lower()
            for key, value in self.reference_data["substitutions"]["cities"].items():
                if city_lower == key:
                    city = value
                    break
            
            result["city"] = city
        
        # Extraction des informations spécifiques au pays
        if country_code == "fr":
            # CEDEX pour la France
            cedex_match = self.patterns["fr"].get("cedex", re.compile("")).search(address)
            if cedex_match:
                result["postal_code"] = cedex_match.group(1)
                result["city"] = cedex_match.group(2) + " CEDEX"
                if cedex_match.group(3):  # Numéro de CEDEX
                    result["city"] += " " + cedex_match.group(3)
            
            # Complément d'adresse français
            complement_match = self.patterns["fr"].get("address_complement", re.compile("")).search(address)
            if complement_match:
                result["address_complement"] = complement_match.group(0)
        
        elif country_code in ["ci", "cm", "sn"]:
            # Boîte postale pour les pays africains
            po_box_pattern = self.patterns.get(country_code, {}).get("po_box", self.patterns["generic"]["po_box"])
            po_box_match = po_box_pattern.search(address)
            if po_box_match:
                result["po_box"] = f"BP {po_box_match.group(1)}"
                if po_box_match.groups() > 1 and po_box_match.group(2):
                    # Si la ville est incluse dans la BP
                    result["city"] = po_box_match.group(2)
        
        elif country_code == "ci":
            # Communes d'Abidjan
            commune_match = self.patterns["ci"].get("abidjan_commune", re.compile("")).search(address)
            if commune_match:
                district = f"Commune {commune_match.group(1)}"
                if result["city"] and result["city"].lower() == "abidjan":
                    result["district"] = district
                else:
                    result["district"] = district
                    result["city"] = "Abidjan"
    
    def _extract_address_components(self, text: str, result: Dict[str, Any], country_code: str):
        """
        Extrait les composants d'adresse individuellement
        
        Args:
            text (str): Texte à analyser
            result (dict): Dictionnaire de résultats à compléter
            country_code (str): Code pays
        """
        # Extraction de la rue
        street_match = self.patterns["generic"]["street"].search(text)
        if street_match:
            street = street_match.group(1).strip()
            
            # Tentative d'extraction du numéro de rue
            number_match = re.match(r'(\d+\s*(?:bis|ter|quater)?)[,\s.]', street)
            if number_match:
                result["street_number"] = number_match.group(1).strip()
                # Extraction du nom de rue (reste après le numéro)
                result["street_name"] = street[number_match.end():].strip()
            else:
                result["street_name"] = street
        
        # Extraction du code postal
        postal_pattern = self.patterns.get(country_code, {}).get("postal_code", self.patterns["generic"]["postal_code"])
        postal_match = postal_pattern.search(text)
        if postal_match:
            result["postal_code"] = postal_match.group(1)
        
        # Extraction de la ville
        city_match = None
        
        # Si on a un code postal, chercher la ville après celui-ci
        if result["postal_code"]:
            postal_city_pattern = re.compile(
                r'' + re.escape(result["postal_code"]) + r'\s+([A-ZÀ-Ö][a-zà-ö]+(?:[-\s][A-ZÀ-Ö][a-zà-ö]+)*)',
                re.UNICODE
            )
            city_match = postal_city_pattern.search(text)
        
        # Si pas trouvé, utiliser le pattern générique
        if not city_match:
            city_match = self.patterns["generic"]["city"].search(text)
        
        if city_match:
            city = city_match.group(1).strip()
            
            # Normaliser le nom de la ville
            city_lower = city.lower()
            for key, value in self.reference_data["substitutions"]["cities"].items():
                if city_lower == key:
                    city = value
                    break
            
            result["city"] = city
        
        # Extraction du pays
        country_match = self.patterns["generic"]["country"].search(text)
        if country_match:
            country_name = country_match.group(1).strip()
            
            # Normalisation du nom de pays
            country_lower = country_name.lower()
            for key, value in self.reference_data["substitutions"]["countries"].items():
                if country_lower == key:
                    country_name = value
                    break
            
            result["country"] = country_name
        
        # Extraction des informations spécifiques au pays
        if country_code == "fr":
            # CEDEX pour la France
            cedex_match = self.patterns["fr"].get("cedex", re.compile("")).search(text)
            if cedex_match:
                result["postal_code"] = cedex_match.group(1)
                result["city"] = cedex_match.group(2) + " CEDEX"
                if cedex_match.group(3):  # Numéro de CEDEX
                    result["city"] += " " + cedex_match.group(3)
            
            # Complément d'adresse français
            complement_match = self.patterns["fr"].get("address_complement", re.compile("")).search(text)
            if complement_match:
                result["address_complement"] = complement_match.group(0)
        
        elif country_code in ["ci", "cm", "sn"]:
            # Boîte postale pour les pays africains
            po_box_pattern = self.patterns.get(country_code, {}).get("po_box", self.patterns["generic"]["po_box"])
            po_box_match = po_box_pattern.search(text)
            if po_box_match:
                result["po_box"] = f"BP {po_box_match.group(1)}"
                if len(po_box_match.groups()) > 1 and po_box_match.group(2):
                    # Si la ville est incluse dans la BP
                    result["city"] = po_box_match.group(2)
        
        elif country_code == "ci":
            # Communes d'Abidjan
            commune_match = self.patterns["ci"].get("abidjan_commune", re.compile("")).search(text)
            if commune_match:
                district = f"Commune {commune_match.group(1)}"
                if result["city"] and result["city"].lower() == "abidjan":
                    result["district"] = district
                else:
                    result["district"] = district
                    result["city"] = "Abidjan"
        
        # Si on a des composants mais pas d'adresse complète, reconstruire
        if self._has_minimum_components(result) and not result["full_address"]:
            result["full_address"] = self._reconstruct_address(result)
    
    def _has_minimum_components(self, result: Dict[str, Any]) -> bool:
        """
        Vérifie si les composants minimums pour une adresse valide sont présents
        
        Args:
            result (dict): Résultat de l'extraction
            
        Returns:
            bool: True si les composants minimums sont présents
        """
        # Une adresse a besoin au minimum d'une rue ou d'une BP ET d'une ville
        has_street = result["street_name"] is not None
        has_po_box = result["po_box"] is not None
        has_city = result["city"] is not None
        
        return (has_street or has_po_box) and has_city
    
    def _normalize_address(self, result: Dict[str, Any]) -> str:
        """
        Normalise l'adresse selon les conventions du pays
        
        Args:
            result (dict): Résultat de l'extraction
            
        Returns:
            str: Adresse normalisée
        """
        country_code = result["country_code"]
        
        # Utilisation du format d'adresse du pays si disponible
        if country_code in self.reference_data["address_formats"]:
            address_format = self.reference_data["address_formats"][country_code]
            components = []
            
            for component in address_format["order"]:
                if component == "street_number" and result["street_number"]:
                    if result["street_name"]:
                        # Joindre le numéro et le nom de rue
                        components.append(f"{result['street_number']} {result['street_name']}")
                    else:
                        components.append(result["street_number"])
                        
                elif component == "street_name" and result["street_name"] and not result["street_number"]:
                    # Seulement si pas déjà ajouté avec le numéro
                    components.append(result["street_name"])
                
                elif component == "district" and result["district"]:
                    components.append(result["district"])
                
                elif component == "address_complement" and result["address_complement"]:
                    components.append(result["address_complement"])
                
                elif component == "po_box" and result["po_box"]:
                    components.append(result["po_box"])
                
                elif component == "postal_code" and result["postal_code"] and result["city"]:
                    # Format français: code postal + ville
                    if country_code == "fr":
                        components.append(f"{result['postal_code']} {result['city']}")
                    else:
                        components.append(result["postal_code"])
                
                elif component == "city" and result["city"] and not (country_code == "fr" and result["postal_code"]):
                    # Seulement si pas déjà ajouté avec le code postal pour la France
                    components.append(result["city"])
            
            # Ajouter le pays si présent et pas déjà inclus dans le format
            if result["country"] and "country" not in address_format["order"]:
                components.append(result["country"])
            
            # Joindre les composants avec le séparateur approprié (par défaut, virgule + espace)
            separator = address_format.get("separators", [", "])[0]
            return separator.join(components)
        
        # Format par défaut si pas de format spécifique au pays
        components = []
        
        if result["street_number"] and result["street_name"]:
            components.append(f"{result['street_number']} {result['street_name']}")
        elif result["street_name"]:
            components.append(result["street_name"])
        
        if result["address_complement"]:
            components.append(result["address_complement"])
        
        if result["po_box"]:
            components.append(result["po_box"])
        
        if result["district"]:
            components.append(result["district"])
        
        if result["postal_code"] and result["city"]:
            components.append(f"{result['postal_code']} {result['city']}")
        elif result["city"]:
            components.append(result["city"])
        
        if result["state"]:
            components.append(result["state"])
        
        if result["country"]:
            components.append(result["country"])
        
        return ", ".join(components)
    
    def _reconstruct_address(self, result: Dict[str, Any]) -> str:
        """
        Reconstruit une adresse complète à partir des composants
        
        Args:
            result (dict): Résultat de l'extraction
            
        Returns:
            str: Adresse reconstruite
        """
        # Similaire à normalize_address mais avec moins de formatage spécifique
        components = []
        
        if result["street_number"] and result["street_name"]:
            components.append(f"{result['street_number']} {result['street_name']}")
        elif result["street_name"]:
            components.append(result["street_name"])
        
        if result["address_complement"]:
            components.append(result["address_complement"])
        
        if result["po_box"]:
            components.append(result["po_box"])
        
        if result["district"]:
            components.append(result["district"])
        
        if result["postal_code"] and result["city"]:
            components.append(f"{result['postal_code']} {result['city']}")
        elif result["city"]:
            components.append(result["city"])
        
        if result["state"]:
            components.append(result["state"])
        
        if result["country"]:
            components.append(result["country"])
        
        return ", ".join(components)
    
    def _calculate_confidence_score(self, result: Dict[str, Any]) -> float:
        """
        Calcule un score de confiance pour l'adresse extraite
        
        Args:
            result (dict): Résultat de l'extraction
            
        Returns:
            float: Score de confiance entre 0 et 1
        """
        score = 0.0
        total_weight = 0.0
        
        # Poids des différents composants
        weights = {
            "full_address": 1.0,
            "street_name": 0.7,
            "street_number": 0.3,
            "postal_code": 0.6,
            "city": 0.7,
            "po_box": 0.5,
            "country": 0.3,
            "state": 0.2,
            "district": 0.2,
            "address_complement": 0.1
        }
        
        # Calcul pondéré
        for component, weight in weights.items():
            if result[component]:
                # Composant présent
                score += weight
            total_weight += weight
        
        # Bonus si l'adresse a les composants minimums
        if self._has_minimum_components(result):
            score += 0.5
            total_weight += 0.5
        
        # Bonus si le code postal est valide pour le pays
        if result["postal_code"] and result["country_code"]:
            postal_format = self.reference_data["postal_code_formats"].get(result["country_code"])
            if postal_format and re.match(postal_format, result["postal_code"]):
                score += 0.3
                total_weight += 0.3
        
        # Bonus si la ville est dans la liste de référence pour le pays
        if result["city"] and result["country_code"]:
            cities = self.reference_data["cities"].get(result["country_code"], set())
            if result["city"] in cities:
                score += 0.3
                total_weight += 0.3
        
        # Calcul final normalisé
        if total_weight > 0:
            return min(1.0, score / total_weight)
        return 0.0
    
    def validate_address(self, address: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide une adresse extraite et détecte les éventuels problèmes
        
        Args:
            address (dict): Adresse à valider
            
        Returns:
            dict: Résultat de la validation avec problèmes détectés
        """
        validation_result = {
            "is_valid": False,
            "issues": [],
            "suggestions": []
        }
        
        # Vérification des composants minimums
        if not self._has_minimum_components(address):
            validation_result["issues"].append("missing_components")
            
            # Suggestions pour les composants manquants
            if not address["street_name"] and not address["po_box"]:
                validation_result["suggestions"].append("Adresse incomplète: ligne d'adresse manquante")
            
            if not address["city"]:
                validation_result["suggestions"].append("Adresse incomplète: ville manquante")
        
        # Vérification du code postal si présent
        if address["postal_code"] and address["country_code"]:
            postal_format = self.reference_data["postal_code_formats"].get(address["country_code"])
            if postal_format and not re.match(postal_format, address["postal_code"]):
                validation_result["issues"].append("invalid_postal_code")
                validation_result["suggestions"].append(f"Format de code postal invalide pour {address['country_code']}")
        
        # Vérification de la ville si présente
        if address["city"] and address["country_code"]:
            cities = self.reference_data["cities"].get(address["country_code"], set())
            if cities and address["city"] not in cities:
                # Vérifier si c'est juste un problème de casse ou d'accent
                city_normalized = address["city"].lower()
                found = False
                for city in cities:
                    if city.lower() == city_normalized:
                        validation_result["suggestions"].append(f"Ville trouvée mais mal orthographiée: {city} au lieu de {address['city']}")
                        found = True
                        break
                
                if not found:
                    validation_result["issues"].append("unknown_city")
        
        # Vérification globale
        if address["confidence_score"] < 0.5:
            validation_result["issues"].append("low_confidence")
        
        # L'adresse est valide s'il n'y a pas de problèmes critiques
        if not validation_result["issues"] or (
            len(validation_result["issues"]) == 1 and "unknown_city" in validation_result["issues"]):
            validation_result["is_valid"] = True
        
        return validation_result
    
    def find_addresses(self, text: str) -> List[Dict[str, Any]]:
        """
        Trouve toutes les adresses dans un texte
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            list: Liste des adresses trouvées
        """
        # Prétraitement du texte
        text = self._preprocess_text(text)
        
        # Découpage du texte en paragraphes
        paragraphs = re.split(r'\n\s*\n', text)
        
        addresses = []
        
        # Recherche dans chaque paragraphe
        for paragraph in paragraphs:
            # Vérification des marqueurs d'adresse
            address_markers = ["adresse", "address", "domicile", "résidence", "situé à", "demeurant"]
            has_marker = any(re.search(r'\b' + re.escape(marker) + r'\b', paragraph, re.IGNORECASE) for marker in address_markers)
            
            # Vérification de la présence de rue, code postal ou ville
            has_street = self.patterns["generic"]["street"].search(paragraph)
            has_postal = self.patterns["generic"]["postal_code"].search(paragraph)
            has_city = self.patterns["generic"]["city"].search(paragraph)
            
            # Si le paragraphe contient des indices d'adresse
            if has_marker or (has_street and (has_postal or has_city)):
                result = self.recognize_address(paragraph)
                
                # Si l'adresse a un score de confiance suffisant
                if result["confidence_score"] >= 0.4:
                    addresses.append(result)
        
        # Recherche d'adresses complètes dans le texte entier
        full_address_matches = self.patterns["generic"]["full_address"].finditer(text)
        for match in full_address_matches:
            address_text = match.group(1)
            # Éviter les doublons en vérifiant si cette adresse est déjà dans les résultats
            is_duplicate = False
            for existing in addresses:
                if existing["full_address"] and address_text in existing["full_address"]:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                result = self.recognize_address(address_text)
                if result["confidence_score"] >= 0.4:
                    addresses.append(result)
        
        # Tri par score de confiance
        addresses.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        return addresses
    
    def compare_addresses(self, address1: Dict[str, Any], address2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare deux adresses et évalue leur similarité
        
        Args:
            address1 (dict): Première adresse
            address2 (dict): Deuxième adresse
            
        Returns:
            dict: Résultat de la comparaison avec score de similarité
        """
        comparison = {
            "match_score": 0.0,
            "matching_components": [],
            "differing_components": [],
            "is_same_address": False
        }
        
        # Composants à comparer
        components = [
            "street_number", "street_name", "postal_code", "city", 
            "po_box", "district", "state", "country"
        ]
        
        matches = 0
        total_comparisons = 0
        
        for component in components:
            val1 = address1.get(component)
            val2 = address2.get(component)
            
            # Si les deux composants sont présents, les comparer
            if val1 and val2:
                total_comparisons += 1
                
                # Normalisation pour la comparaison
                val1_norm = val1.lower().strip()
                val2_norm = val2.lower().strip()
                
                if val1_norm == val2_norm:
                    matches += 1
                    comparison["matching_components"].append(component)
                else:
                    # Calcul de similarité pour les différences minimes
                    similarity = self._calculate_string_similarity(val1_norm, val2_norm)
                    if similarity > 0.8:  # Seuil de tolérance pour les variations minimes
                        matches += similarity
                        comparison["matching_components"].append(component)
                    else:
                        comparison["differing_components"].append({
                            "component": component,
                            "value1": val1,
                            "value2": val2
                        })
            # Si un seul composant est présent
            elif val1 or val2:
                # Pour les composants optionnels comme state, ne pas pénaliser
                if component not in ["state", "district", "address_complement"]:
                    total_comparisons += 1
                    comparison["differing_components"].append({
                        "component": component,
                        "value1": val1,
                        "value2": val2
                    })
        
        # Calcul du score global
        if total_comparisons > 0:
            comparison["match_score"] = matches / total_comparisons
        
        # Détermination si c'est la même adresse
        # Les composants critiques sont la rue/BP et la ville
        has_same_street = (
            "street_name" in comparison["matching_components"] or
            "po_box" in comparison["matching_components"]
        )
        has_same_city = "city" in comparison["matching_components"]
        
        comparison["is_same_address"] = has_same_street and has_same_city and comparison["match_score"] >= 0.7
        
        return comparison
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """
        Calcule la similarité entre deux chaînes
        
        Args:
            str1 (str): Première chaîne
            str2 (str): Deuxième chaîne
            
        Returns:
            float: Score de similarité entre 0 et 1
        """
        # Méthode simple: ratio de caractères identiques en position
        if not str1 or not str2:
            return 0.0
        
        # Normalisation
        str1 = ''.join(c.lower() for c in str1 if c.isalnum())
        str2 = ''.join(c.lower() for c in str2 if c.isalnum())
        
        # Algorithme de distance de Levenshtein simplifié
        m, n = len(str1), len(str2)
        
        # Matrice de distance
        d = [[0 for _ in range(n+1)] for _ in range(m+1)]
        
        # Initialisation
        for i in range(m+1):
            d[i][0] = i
        for j in range(n+1):
            d[0][j] = j
        
        # Calcul de la distance
        for j in range(1, n+1):
            for i in range(1, m+1):
                if str1[i-1] == str2[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    d[i][j] = min(
                        d[i-1][j] + 1,    # Suppression
                        d[i][j-1] + 1,    # Insertion
                        d[i-1][j-1] + 1   # Substitution
                    )
        
        # Conversion en similarité
        max_len = max(m, n)
        if max_len == 0:
            return 1.0
        
        distance = d[m][n]
        similarity = 1.0 - (distance / max_len)
        
        return similarity
    
    def get_address_format_example(self, country_code: str) -> str:
        """
        Renvoie un exemple du format d'adresse pour un pays
        
        Args:
            country_code (str): Code du pays
            
        Returns:
            str: Exemple de format d'adresse
        """
        examples = {
            "fr": "Numéro + Nom de rue\nCode postal + Ville\nFrance",
            "ma": "Numéro + Nom de rue\nQuartier\nCode postal + Ville\nMaroc",
            "ci": "Numéro + Nom de rue\nQuartier / Commune\nBP XXXX Ville\nCôte d'Ivoire",
            "sn": "Numéro + Nom de rue\nQuartier\nBP XXXX Ville\nSénégal",
            "cm": "Numéro + Nom de rue\nQuartier\nBP XXXX Ville\nCameroun"
        }
        
        return examples.get(country_code, "Format international:\nNuméro + Nom de rue\nCode postal + Ville\nPays")
    
    def standardize_address(self, address: Dict[str, Any], target_format: str = "international") -> str:
        """
        Standardise une adresse selon un format cible
        
        Args:
            address (dict): Adresse à standardiser
            target_format (str): Format cible (international, local, postal)
            
        Returns:
            str: Adresse standardisée
        """
        if target_format == "international":
            components = []
            
            # Première ligne: numéro + rue
            if address["street_number"] and address["street_name"]:
                components.append(f"{address['street_number']} {address['street_name']}")
            elif address["street_name"]:
                components.append(address["street_name"])
            elif address["po_box"]:
                components.append(address["po_box"])
            
            # Deuxième ligne: complément d'adresse
            if address["address_complement"]:
                components.append(address["address_complement"])
            
            # Troisième ligne: district/quartier
            if address["district"]:
                components.append(address["district"])
            
            # Quatrième ligne: code postal + ville
            if address["postal_code"] and address["city"]:
                components.append(f"{address['postal_code']} {address['city']}")
            elif address["city"]:
                components.append(address["city"])
            
            # Cinquième ligne: état/province si pertinent
            if address["state"]:
                components.append(address["state"])
            
            # Sixième ligne: pays (toujours inclus en format international)
            if address["country"]:
                components.append(address["country"].upper())
            elif address["country_code"]:
                # Mapping des codes pays vers les noms
                country_names = {
                    "fr": "FRANCE",
                    "ma": "MAROC",
                    "sn": "SENEGAL",
                    "ci": "COTE D'IVOIRE",
                    "cm": "CAMEROUN",
                    "dz": "ALGERIE",
                    "tn": "TUNISIE"
                }
                components.append(country_names.get(address["country_code"], address["country_code"].upper()))
            
            return "\n".join(components)
        
        elif target_format == "local":
            # Format local adapté au pays
            country_code = address["country_code"]
            
            if country_code == "fr":
                components = []
                
                # Première ligne: civilité + nom (si disponible)
                if "recipient" in address and address["recipient"]:
                    components.append(address["recipient"])
                
                # Deuxième ligne: numéro + rue
                if address["street_number"] and address["street_name"]:
                    components.append(f"{address['street_number']} {address['street_name']}")
                elif address["street_name"]:
                    components.append(address["street_name"])
                
                # Troisième ligne: complément d'adresse
                if address["address_complement"]:
                    components.append(address["address_complement"])
                
                # Quatrième ligne: code postal + ville
                if address["postal_code"] and address["city"]:
                    components.append(f"{address['postal_code']} {address['city']}")
                elif address["city"]:
                    components.append(address["city"])
                
                return "\n".join(components)
            
            elif country_code in ["ci", "cm", "sn"]:
                components = []
                
                # Première ligne: civilité + nom (si disponible)
                if "recipient" in address and address["recipient"]:
                    components.append(address["recipient"])
                
                # Deuxième ligne: numéro + rue
                if address["street_number"] and address["street_name"]:
                    components.append(f"{address['street_number']} {address['street_name']}")
                elif address["street_name"]:
                    components.append(address["street_name"])
                
                # Troisième ligne: quartier/district
                if address["district"]:
                    components.append(address["district"])
                
                # Quatrième ligne: BP + ville
                if address["po_box"] and address["city"]:
                    components.append(f"{address['po_box']} {address['city']}")
                elif address["po_box"]:
                    components.append(address["po_box"])
                elif address["city"]:
                    components.append(address["city"])
                
                return "\n".join(components)
            
            else:
                # Par défaut, utiliser le format international
                return self.standardize_address(address, "international")
        
        elif target_format == "postal":
            # Format postal (compact pour enveloppes)
            components = []
            
            # Première ligne: destinataire (si disponible)
            if "recipient" in address and address["recipient"]:
                components.append(address["recipient"])
            
            # Deuxième ligne: numéro + rue
            if address["street_number"] and address["street_name"]:
                components.append(f"{address['street_number']} {address['street_name']}")
            elif address["street_name"]:
                components.append(address["street_name"])
            elif address["po_box"]:
                components.append(address["po_box"])
            
            # Troisième ligne: code postal + ville
            postal_city = ""
            if address["postal_code"]:
                postal_city += address["postal_code"] + " "
            if address["city"]:
                postal_city += address["city"]
            
            if postal_city:
                components.append(postal_city)
            
            # Quatrième ligne: pays (si international)
            if address["country"]:
                components.append(address["country"].upper())
            
            return "\n".join(components)
        
        # Format non reconnu, utiliser le format international
        return self.standardize_address(address, "international")


# Fonction autonome pour utilisation directe
def extract_address(text, country_code=None):
    """
    Fonction autonome pour extraire une adresse d'un texte
    
    Args:
        text (str): Texte à analyser
        country_code (str, optional): Code pays pour des règles spécifiques
        
    Returns:
        dict: Adresse extraite ou None si aucune adresse trouvée
    """
    recognizer = AddressRecognizer()
    addresses = recognizer.find_addresses(text)
    
    if addresses:
        return addresses[0]  # Retourner l'adresse avec le meilleur score
    else:
        # Essayer une extraction directe
        return recognizer.recognize_address(text, country_code)


if __name__ == "__main__":
    # Test de la classe avec un exemple de texte
    import argparse
    
    parser = argparse.ArgumentParser(description="Reconnaisseur d'adresses")
    parser.add_argument("--file", help="Fichier texte à analyser")
    parser.add_argument("--text", help="Texte à analyser directement")
    parser.add_argument("--country", help="Code pays (fr, ma, sn, etc.)")
    args = parser.parse_args()
    
    # Configurer le logger pour le test
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    recognizer = AddressRecognizer()
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
        
        Et
        
        La société ABC Consulting, dont le siège social est situé 45 Rue du Commerce,
        75015, Paris, représentée par Madame Marie MARTIN en sa qualité de Directrice Générale,
        
        Adresse de livraison : 18 boulevard Haussmann, 75009 Paris, France
        
        ...
        
        Pour toute correspondance, veuillez écrire à :
        BP 5678, Abidjan, Commune 8, Côte d'Ivoire
        
        Fait à Paris, le 10/01/2023
        """
    
    # Extraction des adresses
    addresses = recognizer.find_addresses(sample_text)
    
    print(f"Adresses trouvées: {len(addresses)}")
    
    # Affichage des résultats
    for i, address in enumerate(addresses):
        print(f"\nAdresse {i+1}:")
        print(f"Score de confiance: {address['confidence_score']:.2f}")
        print(f"Adresse complète: {address['full_address']}")
        print(f"Rue: {address['street_number']} {address['street_name']}")
        print(f"Ville: {address['city']}")
        if address['postal_code']:
            print(f"Code postal: {address['postal_code']}")
        if address['country']:
            print(f"Pays: {address['country']}")
        
        # Formats standardisés
        print("\nFormat international:")
        print(recognizer.standardize_address(address, "international"))
        
        print("\nFormat local:")
        print(recognizer.standardize_address(address, "local"))