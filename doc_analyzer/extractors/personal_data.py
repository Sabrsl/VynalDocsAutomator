#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'extraction des données personnelles pour Vynal Docs Automator
Ce module permet d'extraire les informations personnelles de différents types de documents.

Types de données extraites:
- Identité (noms, prénoms, dates de naissance, etc.)
- Coordonnées (adresses, téléphones, emails)
- Informations professionnelles
- Données bancaires
- Données contextuelles (relations, rôles)
"""

import re
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set
import json
import csv

# Tentative d'importation des dépendances optionnelles
try:
    import spacy
    SPACY_AVAILABLE = True
    # Chargement du modèle spaCy (un modèle léger)
    try:
        nlp = spacy.load("fr_core_news_sm")
    except OSError:
        logging.warning("Modèle fr_core_news_sm non trouvé. Tentative de téléchargement...")
        from spacy.cli import download
        download("fr_core_news_sm")
        nlp = spacy.load("fr_core_news_sm")
    except Exception as e:
        logging.error(f"Erreur lors du chargement du modèle spaCy: {e}")
        # Fallback sur un modèle vide si nécessaire
        nlp = spacy.blank("fr")
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spacy non disponible, capacités d'extraction limitées")

# Configuration du logger
logger = logging.getLogger("VynalDocsAutomator.DocAnalyzer.PersonalData")

class PersonalDataExtractor:
    """
    Classe pour l'extraction des données personnelles de documents divers
    """
    
    def __init__(self, resources_path=None):
        """
        Initialisation de l'extracteur de données personnelles
        
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
        
        # Initialisation des données d'anonymisation
        self.anonymization_config = self._load_anonymization_config()
        
        self.logger.info("Extracteur de données personnelles initialisé")
    
    def _load_patterns(self):
        """
        Charge les patterns regex spécifiques aux données personnelles
        
        Returns:
            dict: Dictionnaire de patterns par type de donnée
        """
        patterns = {}
        
        # Patterns pour les noms et prénoms
        patterns["name"] = {
            "full_name": re.compile(
                r"(?:M(?:onsieur|me|lle)|Dr|Me|Pr)?\.?\s*([A-ZÀ-Ö][a-zà-ö]+(?:[-'\s][A-ZÀ-Ö][a-zà-ö]+)*)\s+([A-ZÀ-Ö\s]+(?:[-'\s][A-ZÀ-Ö]+)*)",
                re.UNICODE
            ),
            "first_name": re.compile(
                r"(?:prénom|prénoms?|first\s+name|given\s+name)s?\s*:?\s*([A-ZÀ-Ö][a-zà-ö]+(?:[-'\s][A-ZÀ-Ö][a-zà-ö]+)*)",
                re.IGNORECASE | re.UNICODE
            ),
            "last_name": re.compile(
                r"(?:nom|noms?|last\s+name|surname|family\s+name|nom\s+de\s+famille)s?\s*:?\s*([A-ZÀ-Ö\s]+(?:[-'\s][A-ZÀ-Ö]+)*)",
                re.IGNORECASE | re.UNICODE
            )
        }
        
        # Patterns pour les dates de naissance
        patterns["birth"] = {
            "birth_date": re.compile(
                r"(?:né(?:e)?\s+le|date\s+de\s+naissance|birth\s+date|born\s+on)\s*:?\s*(\d{1,2}[-./]\d{1,2}[-./]\d{2,4}|\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{2,4})",
                re.IGNORECASE | re.UNICODE
            ),
            "birth_place": re.compile(
                r"(?:né(?:e)?\s+à|lieu\s+de\s+naissance|birth\s+place|place\s+of\s+birth)\s*:?\s*([A-ZÀ-Ö][a-zà-ö]+(?:[-'\s][A-ZÀ-Ö][a-zà-ö]+)*(?:\s+\([A-Z0-9]+\))?)",
                re.IGNORECASE | re.UNICODE
            ),
            "nationality": re.compile(
                r"(?:nationalité|nationality|citoyenneté|citizenship)\s*:?\s*([A-ZÀ-Ö][a-zà-ö]+(?:[-'\s][A-ZÀ-Ö][a-zà-ö]+)*)",
                re.IGNORECASE | re.UNICODE
            )
        }
        
        # Patterns pour les adresses
        patterns["address"] = {
            "postal_address": re.compile(
                r"(?:adresse|domicile|address|résid(?:ence|ant)|demeurant\s+à)\s*:?\s*([0-9]+[\s,]+(?:rue|avenue|boulevard|chemin|place|impasse|allée|route|voie)[\s,]+[A-ZÀ-Ö0-9\s,\.'-]+)",
                re.IGNORECASE | re.UNICODE
            ),
            "postal_code": re.compile(
                r"(?:\s|^)(\d{5})(?:\s|$)",
                re.UNICODE
            ),
            "city": re.compile(
                r"(?:\d{5})?(?:\s|[,\-])([A-ZÀ-Ö][a-zà-ö]+(?:[-'\s][A-ZÀ-Ö][a-zà-ö]+)*)",
                re.UNICODE
            ),
            "country": re.compile(
                r"(?:pays|country|nation)\s*:?\s*([A-ZÀ-Ö][a-zà-ö]+(?:[-'\s][A-ZÀ-Ö][a-zà-ö]+)*)",
                re.IGNORECASE | re.UNICODE
            )
        }
        
        # Patterns pour les numéros de téléphone
        patterns["phone"] = {
            "french_mobile": re.compile(
                r"(?:0|\+33|00\s*33)\s*[67]\s*(?:\d\s*){8}",
                re.UNICODE
            ),
            "french_landline": re.compile(
                r"(?:0|\+33|00\s*33)\s*[1-5]\s*(?:\d\s*){8}",
                re.UNICODE
            ),
            "international": re.compile(
                r"\+\d{1,3}\s*(?:\d\s*){6,12}",
                re.UNICODE
            ),
            "african_numbers": {
                "ma": re.compile(r"(?:0|\+212|00\s*212)\s*[5-7]\s*(?:\d\s*){8}", re.UNICODE),  # Maroc
                "sn": re.compile(r"(?:0|\+221|00\s*221)\s*[7-8]\s*(?:\d\s*){8}", re.UNICODE),  # Sénégal
                "ci": re.compile(r"(?:0|\+225|00\s*225)\s*(?:[0-5]|[07])\s*(?:\d\s*){7}", re.UNICODE),  # Côte d'Ivoire
                "cm": re.compile(r"(?:0|\+237|00\s*237)\s*(?:[2368])\s*(?:\d\s*){7}", re.UNICODE),  # Cameroun
                "dz": re.compile(r"(?:0|\+213|00\s*213)\s*[5-7]\s*(?:\d\s*){8}", re.UNICODE),  # Algérie
                "tn": re.compile(r"(?:0|\+216|00\s*216)\s*[2-9]\s*(?:\d\s*){7}", re.UNICODE)   # Tunisie
            }
        }
        
        # Patterns pour les emails
        patterns["email"] = {
            "standard": re.compile(
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                re.UNICODE
            )
        }
        
        # Patterns pour les identifiants
        patterns["ids"] = {
            "fr_ssn": re.compile(
                r"(?:1|2)\s?\d{2}\s?(?:0[1-9]|1[0-2])\s?(?:2[AB]|[0-9]{2})\s?\d{3}\s?\d{3}\s?\d{2}",
                re.UNICODE
            ),  # Sécurité sociale française
            "fr_siret": re.compile(
                r"\d{3}\s*\d{3}\s*\d{3}\s*\d{5}",
                re.UNICODE
            ),  # SIRET français
            "various_id_numbers": re.compile(
                r"(?:numéro|n°|number|id)[\s:]*([A-Z0-9]{4,}(?:-[A-Z0-9]+)*)",
                re.IGNORECASE | re.UNICODE
            )
        }
        
        # Patterns pour les données bancaires
        patterns["banking"] = {
            "iban": re.compile(
                r"[A-Z]{2}\d{2}[\s]?(?:\d{4}[\s]?){4,7}",
                re.UNICODE
            ),
            "bic": re.compile(
                r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?",
                re.UNICODE
            ),
            "card_number": re.compile(
                r"(?:\d[\s-]*){13,19}",
                re.UNICODE
            ),
            "account_references": re.compile(
                r"(?:compte|account|référence)[\s:]*([A-Z0-9]{5,}(?:[-\s][A-Z0-9]+)*)",
                re.IGNORECASE | re.UNICODE
            )
        }
        
        # Patterns pour les données professionnelles
        patterns["professional"] = {
            "job_title": re.compile(
                r"(?:profession|métier|occupation|job|poste|fonction|title)[\s:]*([A-ZÀ-Öa-zà-ö\s\(\)]{3,30})",
                re.IGNORECASE | re.UNICODE
            ),
            "company": re.compile(
                r"(?:société|company|entreprise|organization|organisation|employeur|employer)[\s:]*([A-ZÀ-Ö][A-ZÀ-Öa-zà-ö0-9\s\(\)\.,&'-]{2,50})",
                re.IGNORECASE | re.UNICODE
            ),
            "professional_id": re.compile(
                r"(?:numéro\s+professionnel|licence|matricule|professional\s+id)[\s:]*([A-Z0-9]{3,20}(?:[-\s][A-Z0-9]+)*)",
                re.IGNORECASE | re.UNICODE
            )
        }
        
        # Patterns pour les relations
        patterns["relations"] = {
            "relational_terms": re.compile(
                r"(?:époux|épouse|conjoint|mari|femme|concubin|partenaire|père|mère|fils|fille|enfant|parent|spouse|husband|wife|partner|father|mother|child|parent)[\s:]*(de|of|avec|with)[\s:]*(.*?)(?:,|\.|;|et|$)",
                re.IGNORECASE | re.UNICODE
            ),
            "business_relations": re.compile(
                r"(?:représentant|mandataire|directeur|gérant|président|administrateur|associé|actionnaire|representative|director|manager|partner|shareholder)[\s:]*(de|of|chez|at)[\s:]*(.*?)(?:,|\.|;|et|$)",
                re.IGNORECASE | re.UNICODE
            )
        }
        
        # Tentative de chargement des patterns supplémentaires depuis les fichiers
        try:
            patterns_dir = os.path.join(self.resources_path, "patterns")
            if os.path.exists(patterns_dir):
                # Ici, on pourrait charger des patterns supplémentaires depuis des fichiers
                pass
        except Exception as e:
            self.logger.warning(f"Impossible de charger les patterns supplémentaires: {e}")
        
        return patterns
    
    def _load_reference_data(self):
        """
        Charge les données de référence pour la validation et l'enrichissement
        
        Returns:
            dict: Dictionnaire de données de référence
        """
        reference_data = {
            "countries": set(),
            "cities": set(),
            "job_titles": set(),
            "name_prefixes": {"M.", "Mme", "Dr", "Me", "Pr", "Mlle"},
            "name_particles": {"de", "du", "d'", "von", "van", "le", "la", "l'", "el", "al", "bin", "ben"}
        }
        
        # Tentative de chargement des données de référence depuis les fichiers
        try:
            ref_dir = os.path.join(self.resources_path, "reference_data")
            
            # Chargement des pays
            countries_file = os.path.join(ref_dir, "countries.txt")
            if os.path.exists(countries_file):
                with open(countries_file, 'r', encoding='utf-8') as f:
                    reference_data["countries"] = {line.strip() for line in f if line.strip()}
            
            # Chargement des villes
            cities_file = os.path.join(ref_dir, "cities.txt")
            if os.path.exists(cities_file):
                with open(cities_file, 'r', encoding='utf-8') as f:
                    reference_data["cities"] = {line.strip() for line in f if line.strip()}
            
            # Chargement des intitulés de poste
            jobs_file = os.path.join(ref_dir, "job_titles.txt")
            if os.path.exists(jobs_file):
                with open(jobs_file, 'r', encoding='utf-8') as f:
                    reference_data["job_titles"] = {line.strip() for line in f if line.strip()}
        
        except Exception as e:
            self.logger.warning(f"Erreur lors du chargement des données de référence: {e}")
        
        return reference_data
    
    def _load_anonymization_config(self):
        """
        Charge la configuration d'anonymisation
        
        Returns:
            dict: Configuration d'anonymisation
        """
        config = {
            "anonymize_by_default": False,
            "fields_to_anonymize": ["banking", "ids"],
            "anonymization_method": "masking",  # masking, pseudonymization, redaction
            "masking_char": "X"
        }
        
        # Tentative de chargement de la configuration depuis un fichier
        try:
            config_file = os.path.join(self.resources_path, "config", "anonymization.json")
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    config.update(loaded_config)
        except Exception as e:
            self.logger.warning(f"Erreur lors du chargement de la configuration d'anonymisation: {e}")
        
        return config
    
    def extract(self, text, anonymize=False):
        """
        Extrait toutes les données personnelles d'un texte
        
        Args:
            text (str): Texte à analyser
            anonymize (bool): Indique si les données sensibles doivent être anonymisées
            
        Returns:
            dict: Données personnelles extraites
        """
        # Prétraitement du texte
        text = self._preprocess_text(text)
        
        # Initialisation du résultat
        result = {
            "identity": self.extract_identity(text),
            "contact": self.extract_contact_info(text),
            "professional": self.extract_professional_info(text),
            "ids": self.extract_ids(text),
            "banking": self.extract_banking_info(text),
            "relations": self.extract_relations(text),
            "metadata": {
                "extraction_date": datetime.now().isoformat(),
                "confidence_scores": {}
            }
        }
        
        # Enrichissement avec l'analyse NLP si disponible
        if SPACY_AVAILABLE:
            self._enrich_with_nlp(text, result)
        
        # Calcul des scores de confiance
        result["metadata"]["confidence_scores"] = self._calculate_confidence_scores(result)
        
        # Anonymisation si demandée
        if anonymize or self.anonymization_config["anonymize_by_default"]:
            result = self._anonymize_data(result)
        
        return result
    
    def _preprocess_text(self, text):
        """
        Prétraite le texte pour améliorer l'extraction
        
        Args:
            text (str): Texte à prétraiter
            
        Returns:
            str: Texte prétraité
        """
        # Suppression des caractères spéciaux problématiques
        text = re.sub(r'[^\w\s\.,;:\'\"!?@#&\(\)\[\]\{\}\-/\\<>%€$£¥+\*=|°²³_]', ' ', text)
        
        # Normalisation des espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Conversion de certains caractères spéciaux
        replacements = {
            'œ': 'oe',
            'Œ': 'OE',
            'æ': 'ae',
            'Æ': 'AE'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text
    
    def extract_identity(self, text):
        """
        Extrait les informations d'identité (nom, prénom, date de naissance, etc.)
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            dict: Informations d'identité extraites
        """
        identity = {
            "first_name": None,
            "last_name": None,
            "full_name": None,
            "birth_date": None,
            "birth_place": None,
            "gender": None,
            "nationality": None,
            "civil_status": None
        }
        
        # Extraction du nom complet (prénom + nom)
        full_name_match = self.patterns["name"]["full_name"].search(text)
        if full_name_match:
            # Le groupe 1 est le prénom, le groupe 2 est le nom
            first_name = full_name_match.group(1).strip()
            last_name = full_name_match.group(2).strip()
            
            identity["first_name"] = first_name
            identity["last_name"] = last_name
            identity["full_name"] = f"{first_name} {last_name}"
        
        # Extraction du prénom séparé
        if not identity["first_name"]:
            first_name_match = self.patterns["name"]["first_name"].search(text)
            if first_name_match:
                identity["first_name"] = first_name_match.group(1).strip()
        
        # Extraction du nom séparé
        if not identity["last_name"]:
            last_name_match = self.patterns["name"]["last_name"].search(text)
            if last_name_match:
                identity["last_name"] = last_name_match.group(1).strip()
        
        # Construction du nom complet si on a séparément le prénom et le nom
        if identity["first_name"] and identity["last_name"] and not identity["full_name"]:
            identity["full_name"] = f"{identity['first_name']} {identity['last_name']}"
        
        # Extraction de la date de naissance
        birth_date_match = self.patterns["birth"]["birth_date"].search(text)
        if birth_date_match:
            raw_date = birth_date_match.group(1).strip()
            # Normalisation de la date
            identity["birth_date"] = self._normalize_date(raw_date)
        
        # Extraction du lieu de naissance
        birth_place_match = self.patterns["birth"]["birth_place"].search(text)
        if birth_place_match:
            identity["birth_place"] = birth_place_match.group(1).strip()
        
        # Extraction de la nationalité
        nationality_match = self.patterns["birth"]["nationality"].search(text)
        if nationality_match:
            identity["nationality"] = nationality_match.group(1).strip()
        
        # Détermination du genre (à partir du texte)
        gender_indicators = {
            "male": ["monsieur", "m.", "mr", "homme", "masculin", "male", "né le"],
            "female": ["madame", "mme", "mlle", "ms", "mrs", "miss", "femme", "féminin", "female", "née le"]
        }
        
        text_lower = text.lower()
        for gender, indicators in gender_indicators.items():
            for indicator in indicators:
                if re.search(r'\b' + re.escape(indicator) + r'\b', text_lower):
                    identity["gender"] = "M" if gender == "male" else "F"
                    break
            if identity["gender"]:
                break
        
        # Détermination de l'état civil
        civil_status_indicators = {
            "single": ["célibataire", "single"],
            "married": ["marié", "mariée", "married", "époux", "épouse"],
            "divorced": ["divorcé", "divorcée", "divorced"],
            "widowed": ["veuf", "veuve", "widowed", "widower", "widow"],
            "separated": ["séparé", "séparée", "separated"],
            "partnered": ["pacsé", "pacsée", "en concubinage", "partnered", "civil partner"]
        }
        
        for status, indicators in civil_status_indicators.items():
            for indicator in indicators:
                if re.search(r'\b' + re.escape(indicator) + r'\b', text_lower):
                    identity["civil_status"] = status
                    break
            if identity["civil_status"]:
                break
        
        return identity
    
    def extract_contact_info(self, text):
        """
        Extrait les informations de contact (adresse, téléphone, email)
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            dict: Informations de contact extraites
        """
        contact = {
            "address": {
                "full_address": None,
                "street": None,
                "postal_code": None,
                "city": None,
                "country": None
            },
            "phone_numbers": [],
            "email": None
        }
        
        # Extraction de l'adresse complète
        address_match = self.patterns["address"]["postal_address"].search(text)
        if address_match:
            contact["address"]["full_address"] = address_match.group(1).strip()
            
            # Tentative d'extraction des composants de l'adresse
            address_parts = contact["address"]["full_address"]
            
            # Extraction de la rue
            street_match = re.search(r"([0-9]+\s+(?:bis|ter|quater)?\s*(?:rue|avenue|boulevard|chemin|place|impasse|allée|route|voie)[\s,]+[A-ZÀ-Ö0-9\s,\.'-]+)", address_parts, re.IGNORECASE | re.UNICODE)
            if street_match:
                contact["address"]["street"] = street_match.group(1).strip()
        
        # Extraction du code postal (recherche indépendante)
        postal_code_match = self.patterns["address"]["postal_code"].search(text)
        if postal_code_match:
            contact["address"]["postal_code"] = postal_code_match.group(1).strip()
        
        # Extraction de la ville (recherche indépendante ou à proximité du code postal)
        city_match = None
        if contact["address"]["postal_code"]:
            # Recherche de la ville après le code postal
            city_match = re.search(
                r'' + re.escape(contact["address"]["postal_code"]) + r'\s+([A-ZÀ-Ö][a-zà-ö]+(?:[-\s][A-ZÀ-Ö][a-zà-ö]+)*)',
                text,
                re.UNICODE
            )
        
        if not city_match:
            # Recherche générique de la ville
            city_match = self.patterns["address"]["city"].search(text)
        
        if city_match:
            contact["address"]["city"] = city_match.group(1).strip()
        
        # Extraction du pays
        country_match = self.patterns["address"]["country"].search(text)
        if country_match:
            contact["address"]["country"] = country_match.group(1).strip()
        
        # Extraction des numéros de téléphone
        # Téléphone portable français
        for mobile_match in self.patterns["phone"]["french_mobile"].finditer(text):
            phone = self._normalize_phone_number(mobile_match.group(0), "mobile", "fr")
            if phone and phone not in contact["phone_numbers"]:
                contact["phone_numbers"].append(phone)
        
        # Téléphone fixe français
        for landline_match in self.patterns["phone"]["french_landline"].finditer(text):
            phone = self._normalize_phone_number(landline_match.group(0), "landline", "fr")
            if phone and phone not in contact["phone_numbers"]:
                contact["phone_numbers"].append(phone)
        
        # Téléphones internationaux
        for int_match in self.patterns["phone"]["international"].finditer(text):
            phone = self._normalize_phone_number(int_match.group(0), "international")
            if phone and phone not in contact["phone_numbers"]:
                contact["phone_numbers"].append(phone)
        
        # Téléphones africains spécifiques
        for country_code, pattern in self.patterns["phone"]["african_numbers"].items():
            for match in pattern.finditer(text):
                phone = self._normalize_phone_number(match.group(0), "mobile", country_code)
                if phone and phone not in contact["phone_numbers"]:
                    contact["phone_numbers"].append(phone)
        
        # Extraction de l'email
        email_match = self.patterns["email"]["standard"].search(text)
        if email_match:
            contact["email"] = email_match.group(0)
        
        return contact
    
    def extract_professional_info(self, text):
        """
        Extrait les informations professionnelles
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            dict: Informations professionnelles extraites
        """
        professional = {
            "job_title": None,
            "company": None,
            "professional_id": None,
            "department": None,
            "industry": None
        }
        
        # Extraction du titre professionnel
        job_title_match = self.patterns["professional"]["job_title"].search(text)
        if job_title_match:
            professional["job_title"] = job_title_match.group(1).strip()
        
        # Extraction de l'entreprise
        company_match = self.patterns["professional"]["company"].search(text)
        if company_match:
            professional["company"] = company_match.group(1).strip()
        
        # Extraction de l'identifiant professionnel
        prof_id_match = self.patterns["professional"]["professional_id"].search(text)
        if prof_id_match:
            professional["professional_id"] = prof_id_match.group(1).strip()
        
        # Recherche du département ou service (patterns plus spécifiques)
        department_pattern = re.compile(
            r"(?:département|service|division|direction|pôle|department|division|unit)[\s:]*([A-ZÀ-Öa-zà-ö\s\(\)]{3,30})",
            re.IGNORECASE | re.UNICODE
        )
        
        department_match = department_pattern.search(text)
        if department_match:
            professional["department"] = department_match.group(1).strip()
        
        # Recherche du secteur d'activité
        industry_pattern = re.compile(
            r"(?:secteur|industrie|domaine d'activité|sector|industry|field)[\s:]*([A-ZÀ-Öa-zà-ö\s\(\)]{3,30})",
            re.IGNORECASE | re.UNICODE
        )
        
        industry_match = industry_pattern.search(text)
        if industry_match:
            professional["industry"] = industry_match.group(1).strip()
        
        return professional
    
    def extract_ids(self, text):
        """
        Extrait les identifiants personnels (numéro de sécurité sociale, etc.)
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            dict: Identifiants extraits
        """
        ids = {
            "ssn": None,
            "siret": None,
            "other_ids": []
        }
        
        # Extraction du numéro de sécurité sociale française
        ssn_match = self.patterns["ids"]["fr_ssn"].search(text)
        if ssn_match:
            ids["ssn"] = self._normalize_id(ssn_match.group(0), "ssn")
        
        # Extraction du SIRET
        siret_match = self.patterns["ids"]["fr_siret"].search(text)
        if siret_match:
            ids["siret"] = self._normalize_id(siret_match.group(0), "siret")
        
        # Extraction d'autres identifiants
        for id_match in self.patterns["ids"]["various_id_numbers"].finditer(text):
            id_value = id_match.group(1).strip()
            if id_value and id_value not in ids["other_ids"]:
                ids["other_ids"].append(id_value)
        
        return ids
    
    def extract_banking_info(self, text):
        """
        Extrait les informations bancaires
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            dict: Informations bancaires extraites
        """
        banking = {
            "iban": None,
            "bic": None,
            "card_number": None,
            "account_references": []
        }
        
        # Extraction de l'IBAN
        iban_match = self.patterns["banking"]["iban"].search(text)
        if iban_match:
            banking["iban"] = self._normalize_banking_id(iban_match.group(0), "iban")
        
        # Extraction du BIC
        bic_match = self.patterns["banking"]["bic"].search(text)
        if bic_match:
            banking["bic"] = bic_match.group(0).strip()
        
        # Extraction du numéro de carte bancaire
        card_match = self.patterns["banking"]["card_number"].search(text)
        if card_match:
            banking["card_number"] = self._normalize_banking_id(card_match.group(0), "card")
        
        # Extraction des références de compte
        for ref_match in self.patterns["banking"]["account_references"].finditer(text):
            ref_value = ref_match.group(1).strip()
            if ref_value and ref_value not in banking["account_references"]:
                banking["account_references"].append(ref_value)
        
        return banking
    
    def extract_relations(self, text):
        """
        Extrait les relations entre personnes et entités
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            dict: Relations extraites
        """
        relations = {
            "personal_relations": [],
            "business_relations": []
        }
        
        # Extraction des relations personnelles
        for relation_match in self.patterns["relations"]["relational_terms"].finditer(text):
            relation_type = relation_match.group(0).split()[0].lower()
            relation_target = relation_match.group(3).strip()
            
            if relation_target:
                relation = {
                    "type": relation_type,
                    "target": relation_target
                }
                
                if relation not in relations["personal_relations"]:
                    relations["personal_relations"].append(relation)
        
        # Extraction des relations professionnelles
        for relation_match in self.patterns["relations"]["business_relations"].finditer(text):
            relation_type = relation_match.group(0).split()[0].lower()
            relation_target = relation_match.group(3).strip()
            
            if relation_target:
                relation = {
                    "type": relation_type,
                    "target": relation_target
                }
                
                if relation not in relations["business_relations"]:
                    relations["business_relations"].append(relation)
        
        return relations
    
    def _normalize_date(self, date_str):
        """
        Normalise une date au format ISO (YYYY-MM-DD)
        
        Args:
            date_str (str): Date à normaliser
            
        Returns:
            str: Date normalisée ou None si impossible
        """
        try:
            # Gestion des formats numériques (JJ/MM/AAAA, JJ-MM-AAAA, etc.)
            if re.match(r'\d{1,2}[-./]\d{1,2}[-./]\d{2,4}', date_str):
                # Détecter le séparateur
                separator = '/' if '/' in date_str else '-' if '-' in date_str else '.'
                
                day, month, year = date_str.split(separator)
                day = int(day)
                month = int(month)
                
                # Correction de l'année si format à 2 chiffres
                year = int(year)
                if year < 100:
                    year = 2000 + year if year < 30 else 1900 + year
                
                # Validation de base
                if not (1 <= day <= 31 and 1 <= month <= 12):
                    return None
                
                return f"{year:04d}-{month:02d}-{day:02d}"
            
            # Gestion des formats textuels (JJ Mois AAAA)
            month_names = {
                "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
                "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
            }
            
            match = re.match(r'(\d{1,2})\s+([a-zéûô]+)\s+(\d{2,4})', date_str, re.IGNORECASE)
            if match:
                day = int(match.group(1))
                month_str = match.group(2).lower()
                year = int(match.group(3))
                
                if month_str in month_names:
                    month = month_names[month_str]
                    
                    # Correction de l'année si format à 2 chiffres
                    if year < 100:
                        year = 2000 + year if year < 30 else 1900 + year
                    
                    # Validation de base
                    if not (1 <= day <= 31 and 1 <= month <= 12):
                        return None
                    
                    return f"{year:04d}-{month:02d}-{day:02d}"
            
            return date_str  # Retour tel quel si format non reconnu
            
        except (ValueError, IndexError):
            return None
    
    def _normalize_phone_number(self, phone_str, phone_type="unknown", country_code="unknown"):
        """
        Normalise un numéro de téléphone au format international
        
        Args:
            phone_str (str): Numéro de téléphone à normaliser
            phone_type (str): Type de téléphone (mobile, landline, international)
            country_code (str): Code pays ISO
            
        Returns:
            str: Numéro normalisé ou None si impossible
        """
        # Supprimer tous les caractères non numériques sauf le +
        phone_digits = ''.join(c for c in phone_str if c.isdigit() or c == '+')
        
        # Si le numéro commence par un 0 et n'a pas de code pays
        if phone_digits.startswith('0') and not phone_digits.startswith('+'):
            # Mapper les codes pays
            country_prefixes = {
                "fr": "+33",
                "ma": "+212",
                "sn": "+221",
                "ci": "+225",
                "cm": "+237",
                "dz": "+213",
                "tn": "+216"
            }
            
            # Appliquer le préfixe international approprié
            if country_code in country_prefixes:
                phone_digits = country_prefixes[country_code] + phone_digits[1:]
            else:
                # Par défaut, on suppose France
                phone_digits = "+33" + phone_digits[1:]
        
        # Si le numéro commence par 00, le remplacer par +
        if phone_digits.startswith('00'):
            phone_digits = '+' + phone_digits[2:]
        
        # Format de vérification basique
        if not phone_digits.startswith('+') or len(phone_digits) < 10:
            return None
        
        # Construction d'un format lisible +XX X XX XX XX XX
        parts = []
        parts.append(phone_digits[:3])  # Code pays (+33, +212, etc.)
        
        remaining = phone_digits[3:]
        
        # Formatage en groupes de 2 chiffres
        for i in range(0, len(remaining), 2):
            parts.append(remaining[i:i+2])
        
        return ' '.join(parts)
    
    def _normalize_id(self, id_str, id_type):
        """
        Normalise un identifiant en supprimant les espaces et caractères de formatage
        
        Args:
            id_str (str): Identifiant à normaliser
            id_type (str): Type d'identifiant (ssn, siret, etc.)
            
        Returns:
            str: Identifiant normalisé
        """
        # Supprimer tous les caractères non alphanumériques
        id_clean = ''.join(c for c in id_str if c.isalnum())
        
        # Validations spécifiques selon le type
        if id_type == "ssn" and len(id_clean) == 15:
            # Format NIR (sécu française) : 1 85 12 75 123 456 78
            return f"{id_clean[0:1]} {id_clean[1:3]} {id_clean[3:5]} {id_clean[5:7]} {id_clean[7:10]} {id_clean[10:13]} {id_clean[13:15]}"
        
        elif id_type == "siret" and len(id_clean) == 14:
            # Format SIRET : 123 456 789 12345
            return f"{id_clean[0:3]} {id_clean[3:6]} {id_clean[6:9]} {id_clean[9:14]}"
        
        # Par défaut, retourner simplement la version nettoyée
        return id_clean
    
    def _normalize_banking_id(self, id_str, id_type):
        """
        Normalise un identifiant bancaire
        
        Args:
            id_str (str): Identifiant à normaliser
            id_type (str): Type d'identifiant (iban, card, etc.)
            
        Returns:
            str: Identifiant normalisé
        """
        # Supprimer tous les caractères non alphanumériques
        id_clean = ''.join(c for c in id_str if c.isalnum())
        
        if id_type == "iban":
            # Format IBAN : FRXX XXXX XXXX XXXX XXXX XXXX XXX
            formatted = ""
            for i in range(0, len(id_clean), 4):
                formatted += id_clean[i:i+4] + " "
            return formatted.strip()
        
        elif id_type == "card":
            # Format carte bancaire : XXXX XXXX XXXX XXXX
            if len(id_clean) >= 16:
                return f"{id_clean[0:4]} {id_clean[4:8]} {id_clean[8:12]} {id_clean[12:16]}"
        
        # Par défaut, retourner simplement la version nettoyée
        return id_clean
    
    def _enrich_with_nlp(self, text, result):
        """
        Enrichit les résultats d'extraction avec une analyse NLP
        
        Args:
            text (str): Texte à analyser
            result (dict): Résultats d'extraction à enrichir
            
        Returns:
            None: Modifie directement le dictionnaire result
        """
        try:
            # Analyse du texte avec spaCy
            doc = nlp(text)
            
            # Extraction des entités nommées
            for ent in doc.ents:
                # Personnes
                if ent.label_ == "PER" and len(ent.text) > 3:
                    if not result["identity"]["full_name"]:
                        name_parts = ent.text.strip().split()
                        if len(name_parts) >= 2:
                            # Considérer le dernier mot comme nom de famille
                            result["identity"]["last_name"] = name_parts[-1]
                            # Et le reste comme prénom(s)
                            result["identity"]["first_name"] = " ".join(name_parts[:-1])
                            result["identity"]["full_name"] = ent.text.strip()
                
                # Organisations
                elif ent.label_ == "ORG" and len(ent.text) > 3:
                    if not result["professional"]["company"]:
                        result["professional"]["company"] = ent.text.strip()
                
                # Lieux
                elif ent.label_ == "LOC" and len(ent.text) > 2:
                    # Si c'est probablement une ville
                    if ent.text.strip() in self.reference_data["cities"] or ent.text[0].isupper():
                        if not result["contact"]["address"]["city"]:
                            result["contact"]["address"]["city"] = ent.text.strip()
                    
                    # Si c'est probablement un pays
                    elif ent.text.strip() in self.reference_data["countries"]:
                        if not result["contact"]["address"]["country"]:
                            result["contact"]["address"]["country"] = ent.text.strip()
                
                # Dates non détectées par les regex
                elif ent.label_ == "DATE":
                    date_text = ent.text
                    date_match = re.search(r'(\d{1,2}[-./]\d{1,2}[-./]\d{2,4})', date_text)
                    if date_match and not result["identity"]["birth_date"]:
                        context_before = text[max(0, ent.start_char - 30):ent.start_char]
                        if re.search(r'né|naissance|birth|born', context_before, re.IGNORECASE):
                            result["identity"]["birth_date"] = self._normalize_date(date_match.group(1))
        
        except Exception as e:
            self.logger.warning(f"Erreur lors de l'enrichissement NLP: {e}")
    
    def _calculate_confidence_scores(self, result):
        """
        Calcule les scores de confiance pour chaque catégorie d'extraction
        
        Args:
            result (dict): Résultats d'extraction
            
        Returns:
            dict: Scores de confiance par catégorie
        """
        confidence = {}
        
        # Score pour l'identité
        identity_score = 0
        identity_fields = 0
        
        for field, value in result["identity"].items():
            if value:
                identity_fields += 1
                # Différentes pondérations selon le champ
                if field in ["first_name", "last_name", "full_name"]:
                    identity_score += 1.5
                elif field in ["birth_date", "birth_place"]:
                    identity_score += 1.2
                else:
                    identity_score += 1
        
        if identity_fields > 0:
            confidence["identity"] = min(1.0, identity_score / (identity_fields + 2))
        else:
            confidence["identity"] = 0.0
        
        # Score pour les contacts
        contact_score = 0
        contact_fields = 0
        
        # Adresse
        address_score = 0
        address_fields = 0
        for field, value in result["contact"]["address"].items():
            if value:
                address_fields += 1
                address_score += 1
        
        if address_fields > 0:
            contact_score += address_score / address_fields
            contact_fields += 1
        
        # Téléphones
        if result["contact"]["phone_numbers"]:
            contact_score += 1
            contact_fields += 1
        
        # Email
        if result["contact"]["email"]:
            contact_score += 1
            contact_fields += 1
        
        if contact_fields > 0:
            confidence["contact"] = min(1.0, contact_score / contact_fields)
        else:
            confidence["contact"] = 0.0
        
        # Score pour les informations professionnelles
        professional_score = 0
        professional_fields = 0
        
        for field, value in result["professional"].items():
            if value:
                professional_fields += 1
                professional_score += 1
        
        if professional_fields > 0:
            confidence["professional"] = min(1.0, professional_score / professional_fields)
        else:
            confidence["professional"] = 0.0
        
        # Score pour les identifiants
        ids_score = 0
        ids_fields = 0
        
        if result["ids"]["ssn"]:
            ids_score += 2
            ids_fields += 1
        
        if result["ids"]["siret"]:
            ids_score += 1.5
            ids_fields += 1
        
        if result["ids"]["other_ids"]:
            ids_score += len(result["ids"]["other_ids"]) * 0.5
            ids_fields += 1
        
        if ids_fields > 0:
            confidence["ids"] = min(1.0, ids_score / (ids_fields + 1))
        else:
            confidence["ids"] = 0.0
        
        # Score pour les informations bancaires
        banking_score = 0
        banking_fields = 0
        
        if result["banking"]["iban"]:
            banking_score += 2
            banking_fields += 1
        
        if result["banking"]["bic"]:
            banking_score += 1.5
            banking_fields += 1
        
        if result["banking"]["card_number"]:
            banking_score += 1.5
            banking_fields += 1
        
        if result["banking"]["account_references"]:
            banking_score += len(result["banking"]["account_references"]) * 0.5
            banking_fields += 1
        
        if banking_fields > 0:
            confidence["banking"] = min(1.0, banking_score / (banking_fields + 1))
        else:
            confidence["banking"] = 0.0
        
        # Score pour les relations
        relations_score = 0
        relations_fields = 0
        
        if result["relations"]["personal_relations"]:
            relations_score += len(result["relations"]["personal_relations"]) * 0.7
            relations_fields += 1
        
        if result["relations"]["business_relations"]:
            relations_score += len(result["relations"]["business_relations"]) * 0.7
            relations_fields += 1
        
        if relations_fields > 0:
            confidence["relations"] = min(1.0, relations_score / (relations_fields + 1))
        else:
            confidence["relations"] = 0.0
        
        # Score global
        confidence["overall"] = sum(confidence.values()) / len(confidence) if confidence else 0.0
        
        return confidence
    
    def _anonymize_data(self, result):
        """
        Anonymise les données sensibles dans les résultats d'extraction
        
        Args:
            result (dict): Résultats d'extraction
            
        Returns:
            dict: Résultats avec données sensibles anonymisées
        """
        # Copie des résultats pour ne pas modifier l'original
        anonymized = result.copy()
        
        # Déterminer quels champs anonymiser
        fields_to_anonymize = self.anonymization_config["fields_to_anonymize"]
        
        # Anonymisation par masquage (remplacer par des X)
        if self.anonymization_config["anonymization_method"] == "masking":
            mask_char = self.anonymization_config["masking_char"]
            
            # Anonymisation des identifiants
            if "ids" in fields_to_anonymize and "ids" in anonymized:
                if anonymized["ids"]["ssn"]:
                    anonymized["ids"]["ssn"] = self._mask_string(anonymized["ids"]["ssn"], preserve_format=True)
                
                if anonymized["ids"]["siret"]:
                    anonymized["ids"]["siret"] = self._mask_string(anonymized["ids"]["siret"], preserve_format=True)
                
                anonymized["ids"]["other_ids"] = [self._mask_string(id_val) for id_val in anonymized["ids"]["other_ids"]]
            
            # Anonymisation des données bancaires
            if "banking" in fields_to_anonymize and "banking" in anonymized:
                if anonymized["banking"]["iban"]:
                    anonymized["banking"]["iban"] = self._mask_iban(anonymized["banking"]["iban"])
                
                if anonymized["banking"]["card_number"]:
                    anonymized["banking"]["card_number"] = self._mask_card_number(anonymized["banking"]["card_number"])
                
                anonymized["banking"]["account_references"] = [self._mask_string(ref) for ref in anonymized["banking"]["account_references"]]
            
            # Anonymisation des téléphones
            if "phone" in fields_to_anonymize and "contact" in anonymized:
                anonymized["contact"]["phone_numbers"] = [self._mask_phone_number(phone) for phone in anonymized["contact"]["phone_numbers"]]
        
        # Anonymisation par pseudonymisation (remplacer par des valeurs factices mais cohérentes)
        elif self.anonymization_config["anonymization_method"] == "pseudonymization":
            # Implémentation à développer
            pass
        
        # Anonymisation par suppression (remplacer par None ou [])
        elif self.anonymization_config["anonymization_method"] == "redaction":
            if "ids" in fields_to_anonymize and "ids" in anonymized:
                anonymized["ids"] = {"ssn": None, "siret": None, "other_ids": []}
            
            if "banking" in fields_to_anonymize and "banking" in anonymized:
                anonymized["banking"] = {"iban": None, "bic": None, "card_number": None, "account_references": []}
            
            if "phone" in fields_to_anonymize and "contact" in anonymized:
                anonymized["contact"]["phone_numbers"] = []
        
        # Ajouter une métadonnée d'anonymisation
        anonymized["metadata"]["anonymized"] = True
        anonymized["metadata"]["anonymization_method"] = self.anonymization_config["anonymization_method"]
        
        return anonymized
    
    def _mask_string(self, text, preserve_format=False):
        """
        Masque une chaîne de caractères en remplaçant par des X
        
        Args:
            text (str): Texte à masquer
            preserve_format (bool): Conserver la mise en forme (espaces, etc.)
            
        Returns:
            str: Texte masqué
        """
        mask_char = self.anonymization_config["masking_char"]
        
        if preserve_format:
            # Conserver les caractères de formatage (espaces, tirets, etc.)
            masked = ""
            for char in text:
                if char.isalnum():
                    masked += mask_char
                else:
                    masked += char
            return masked
        else:
            # Remplacer toute la chaîne
            return mask_char * len(text)
    
    def _mask_iban(self, iban):
        """
        Masque un IBAN en préservant le code pays et les 4 derniers caractères
        
        Args:
            iban (str): IBAN à masquer
            
        Returns:
            str: IBAN masqué
        """
        mask_char = self.anonymization_config["masking_char"]
        
        # Supprimer les espaces
        iban_clean = iban.replace(" ", "")
        
        # Garder le code pays (2 premiers caractères)
        country_code = iban_clean[:2]
        
        # Masquer le reste sauf les 4 derniers caractères
        masked_middle = mask_char * (len(iban_clean) - 6)
        last_four = iban_clean[-4:]
        
        masked_iban = country_code + masked_middle + last_four
        
        # Reformater avec des espaces tous les 4 caractères
        formatted = ""
        for i in range(0, len(masked_iban), 4):
            formatted += masked_iban[i:i+4] + " "
        
        return formatted.strip()
    
    def _mask_card_number(self, card_number):
        """
        Masque un numéro de carte bancaire en préservant les 4 derniers chiffres
        
        Args:
            card_number (str): Numéro de carte à masquer
            
        Returns:
            str: Numéro de carte masqué
        """
        mask_char = self.anonymization_config["masking_char"]
        
        # Supprimer les espaces
        card_clean = card_number.replace(" ", "")
        
        # Garder les 4 derniers chiffres
        masked = mask_char * (len(card_clean) - 4) + card_clean[-4:]
        
        # Reformater avec des espaces tous les 4 caractères
        formatted = ""
        for i in range(0, len(masked), 4):
            formatted += masked[i:i+4] + " "
        
        return formatted.strip()
    
    def _mask_phone_number(self, phone_number):
        """
        Masque un numéro de téléphone en préservant le code pays et les 2 derniers chiffres
        
        Args:
            phone_number (str): Numéro de téléphone à masquer
            
        Returns:
            str: Numéro de téléphone masqué
        """
        mask_char = self.anonymization_config["masking_char"]
        
        # Extraire le code pays (généralement +XX)
        parts = phone_number.split(" ")
        
        if not parts:
            return mask_char * len(phone_number)
        
        country_code = parts[0]
        
        # Garder les 2 derniers chiffres
        last_part = parts[-1] if len(parts) > 1 else ""
        
        # Masquer le reste
        masked_parts = [country_code] + [mask_char * len(part) for part in parts[1:-1]]
        
        if last_part:
            masked_parts.append(last_part)
        
        return " ".join(masked_parts)


# Fonction d'extraction autonome pour utilisation directe
def extract_personal_data(text, anonymize=False):
    """
    Fonction autonome pour extraire les données personnelles d'un texte
    
    Args:
        text (str): Texte à analyser
        anonymize (bool): Indique si les données sensibles doivent être anonymisées
        
    Returns:
        dict: Données personnelles extraites
    """
    extractor = PersonalDataExtractor()
    return extractor.extract(text, anonymize)


if __name__ == "__main__":
    # Test de la classe avec un exemple de texte
    import argparse
    
    parser = argparse.ArgumentParser(description="Extracteur de données personnelles")
    parser.add_argument("--file", help="Fichier texte à analyser")
    parser.add_argument("--text", help="Texte à analyser directement")
    parser.add_argument("--anonymize", action="store_true", help="Anonymiser les données sensibles")
    args = parser.parse_args()
    
    # Configurer le logger pour le test
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    extractor = PersonalDataExtractor()
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
        Numéro de téléphone : 06 12 34 56 78
        Email : jean.dupont@email.com
        
        Et
        
        La société ABC Consulting, SIRET 123 456 789 00012, dont le siège social est situé 45 Rue du Commerce,
        75015, Paris, représentée par Madame Marie MARTIN en sa qualité de Directrice Générale,
        
        Il a été convenu ce qui suit :
        
        ...
        
        Coordonnées bancaires du prestataire :
        IBAN : FR76 3000 4000 0100 0123 4567 890
        BIC : BNPAFRPP
        
        Fait à Paris, le 10/01/2023
        """
    
    # Extraction des données
    result = extractor.extract(sample_text, anonymize=args.anonymize)
    
    # Affichage des résultats
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))