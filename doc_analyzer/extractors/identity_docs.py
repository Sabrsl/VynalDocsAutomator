#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'extraction des documents d'identité pour Vynal Docs Automator
Ce module permet d'extraire les informations pertinentes des documents d'identité.

Types de documents traités:
- Cartes nationales d'identité (formats par pays)
- Passeports
- Cartes de séjour et visas
- Titres de résidence
- Identifiants fiscaux
- Cartes professionnelles
"""

import re
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import cv2
import numpy as np
from doc_analyzer.utils.text_processor import TextProcessor
from ..utils.validators import validate_id_number, validate_date, validate_name

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("pytesseract non disponible, fonctionnalités OCR limitées")

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
    logging.warning("spacy non disponible, NER limité")

from ..utils.text_processor import preprocess_text, clean_text

# Configuration du logger
logger = logging.getLogger("VynalDocsAutomator.DocAnalyzer.IdentityDocs")

class IdentityDocExtractor:
    """
    Classe pour l'extraction des informations des documents d'identité
    """
    
    # Types de documents d'identité reconnus
    DOC_TYPES = {
        "cni": ["carte nationale d'identité", "cni", "identité", "carte d'identité", "carte d'identite"],
        "passport": ["passeport", "passport"],
        "residence": ["carte de séjour", "titre de séjour", "carte séjour", "titre séjour", "permis de résidence"],
        "visa": ["visa", "visa de séjour", "visa d'entrée"],
        "tax_id": ["numéro fiscal", "identifiant fiscal", "carte fiscale", "nif", "numéro d'immatriculation fiscale"],
        "professional_card": ["carte professionnelle", "licence professionnelle", "permis d'exercice"]
    }
    
    # Types de documents par pays
    COUNTRY_SPECIFIC_DOCS = {
        "fr": ["cni", "passeport", "titre de séjour"],
        "ma": ["cni", "passeport", "carte de séjour"],
        "sn": ["cni", "passeport", "carte de résident"],
        "ci": ["cni", "passeport", "carte de résident"],
        "cm": ["cni", "passeport", "carte de séjour"],
        "dz": ["cni", "passeport", "carte de résidence"],
        "tn": ["cni", "passeport", "carte de séjour"]
    }
    
    def __init__(self, resources_path=None, ocr_enabled=True):
        """
        Initialisation de l'extracteur de documents d'identité
        
        Args:
            resources_path (str, optional): Chemin vers les ressources spécifiques
            ocr_enabled (bool): Activer la reconnaissance optique de caractères
        """
        self.logger = logger
        self.ocr_enabled = ocr_enabled and OCR_AVAILABLE
        
        # Chemin vers les ressources
        self.resources_path = resources_path
        if not self.resources_path:
            # Chemin par défaut relatif au module
            self.resources_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "resources"
            )
        
        # Chargement des patterns spécifiques aux documents d'identité
        self.patterns = self._load_patterns()
        self.logger.info("Extracteur de documents d'identité initialisé")
    
    def _load_patterns(self):
        """
        Charge les patterns regex spécifiques aux différents types de documents d'identité
        
        Returns:
            dict: Dictionnaire de patterns par type de document
        """
        patterns = {}
        
        # Patterns pour les numéros de documents (France)
        patterns["fr"] = {
            "cni_number": re.compile(
                r"(?:№|N°|No|Numéro)?\s*(?:CNI|Carte)?\s*:?\s*([0-9]{12}|[0-9]{4}\s*[0-9]{4}\s*[0-9]{4})",
                re.IGNORECASE
            ),
            "passport_number": re.compile(
                r"(?:№|N°|No|Numéro)?\s*(?:Passeport)?\s*:?\s*([0-9]{2}\s*[A-Z]{2}\s*[0-9]{5}|[0-9]{9})",
                re.IGNORECASE
            ),
            "residence_number": re.compile(
                r"(?:№|N°|No|Numéro)?\s*(?:Titre)?\s*:?\s*([A-Z]{3}\s*[0-9]{10})",
                re.IGNORECASE
            )
        }
        
        # Patterns pour les numéros de documents (Maroc)
        patterns["ma"] = {
            "cni_number": re.compile(
                r"(?:№|N°|No|Numéro|رقم)?\s*(?:CIN|Carte|بطاقة)?\s*:?\s*([A-Z]{1,2}[0-9]{5,6})",
                re.IGNORECASE
            ),
            "passport_number": re.compile(
                r"(?:№|N°|No|Numéro|رقم)?\s*(?:Passeport|جواز)?\s*:?\s*([A-Z]{1,2}[0-9]{6,7})",
                re.IGNORECASE
            )
        }
        
        # Patterns pour les numéros de documents (Sénégal)
        patterns["sn"] = {
            "cni_number": re.compile(
                r"(?:№|N°|No|Numéro)?\s*(?:CNI|Carte)?\s*:?\s*([0-9]{13}|[0-9]{1,2}\s*[0-9]{3}\s*[0-9]{4}\s*[0-9]{2})",
                re.IGNORECASE
            ),
            "passport_number": re.compile(
                r"(?:№|N°|No|Numéro)?\s*(?:Passeport)?\s*:?\s*([A-Z]{1,2}[0-9]{6,7})",
                re.IGNORECASE
            )
        }
        
        # Patterns pour les numéros de documents (Côte d'Ivoire)
        patterns["ci"] = {
            "cni_number": re.compile(
                r"(?:№|N°|No|Numéro)?\s*(?:CNI|Carte)?\s*:?\s*([A-Z][0-9]{9}|C-[0-9]{9})",
                re.IGNORECASE
            ),
            "passport_number": re.compile(
                r"(?:№|N°|No|Numéro)?\s*(?:Passeport)?\s*:?\s*([0-9]{7,10})",
                re.IGNORECASE
            )
        }
        
        # Patterns génériques
        patterns["generic"] = {
            "name": re.compile(
                r"(?:Nom|Nom et prénom|الاسم|Name)s?\s*:?\s*([A-ZÀ-Ö\s]{2,50})",
                re.IGNORECASE
            ),
            "firstname": re.compile(
                r"(?:Prénom|الاسم الشخصي|First Name|Prénoms?)s?\s*:?\s*([A-ZÀ-Ö\s]{2,50})",
                re.IGNORECASE
            ),
            "birth_date": re.compile(
                r"(?:Date de naissance|تاريخ الازدياد|Born on|Né\(e\) le)\s*:?\s*([0-9]{1,2}[-./][0-9]{1,2}[-./][0-9]{2,4})",
                re.IGNORECASE
            ),
            "birth_place": re.compile(
                r"(?:Lieu de naissance|مكان الازدياد|Place of Birth|Né\(e\) à)\s*:?\s*([A-ZÀ-Ö\s]{2,50})",
                re.IGNORECASE
            ),
            "issue_date": re.compile(
                r"(?:Date d['e]émission|Délivré[e]? le|تاريخ الإصدار|Issue Date)\s*:?\s*([0-9]{1,2}[-./][0-9]{1,2}[-./][0-9]{2,4})",
                re.IGNORECASE
            ),
            "expiry_date": re.compile(
                r"(?:Date d['e]expiration|Valable jusqu['e]au|تاريخ انتهاء الصلاحية|Expiry Date|Valid Until)\s*:?\s*([0-9]{1,2}[-./][0-9]{1,2}[-./][0-9]{2,4})",
                re.IGNORECASE
            ),
            "nationality": re.compile(
                r"(?:Nationalité|الجنسية|Nationality)\s*:?\s*([A-ZÀ-Ö\s]{3,30})",
                re.IGNORECASE
            ),
            "gender": re.compile(
                r"(?:Sexe|الجنس|Gender|Sex)\s*:?\s*([MF]|[HF]|Male|Female|Homme|Femme|ذكر|أنثى)",
                re.IGNORECASE
            ),
            "authority": re.compile(
                r"(?:Autorité|Délivré par|سلطة الإصدار|Issuing Authority)\s*:?\s*([A-ZÀ-Ö\s]{3,50})",
                re.IGNORECASE
            ),
            "address": re.compile(
                r"(?:Adresse|Domicile|العنوان|Address|Résidence)\s*:?\s*([A-ZÀ-Ö0-9\s,\.]{5,100})",
                re.IGNORECASE
            ),
            "profession": re.compile(
                r"(?:Profession|المهنة|Occupation)\s*:?\s*([A-ZÀ-Ö\s]{3,50})",
                re.IGNORECASE
            ),
            "father_name": re.compile(
                r"(?:Fils? de|اسم الأب|Son of)\s*:?\s*([A-ZÀ-Ö\s]{2,50})",
                re.IGNORECASE
            ),
            "mother_name": re.compile(
                r"(?:et de|اسم الأم|and of)\s*:?\s*([A-ZÀ-Ö\s]{2,50})",
                re.IGNORECASE
            )
        }
        
        # Patterns pour les numéros fiscaux
        patterns["tax_ids"] = {
            "fr_nif": re.compile(r"(?:№|N°|No|Numéro fiscal|Identifiant fiscal)\s*:?\s*([0-9]{13,15})", re.IGNORECASE),
            "ma_nif": re.compile(r"(?:№|N°|No|Identifiant fiscal)\s*:?\s*([0-9]{7,10})", re.IGNORECASE),
            "sn_ninea": re.compile(r"(?:NINEA)\s*:?\s*([0-9]{7}[A-Z][0-9]{3})", re.IGNORECASE),
            "ci_cc": re.compile(r"(?:Compte contribuable)\s*:?\s*([0-9]{10,12})", re.IGNORECASE)
        }
        
        # Patterns pour les cartes professionnelles
        patterns["professional"] = {
            "lawyer_card": re.compile(r"(?:Avocat|Barreau)\s*:?\s*N°\s*([0-9]{1,6})", re.IGNORECASE),
            "doctor_card": re.compile(r"(?:Médecin|Ordre des médecins)\s*:?\s*N°\s*([0-9]{1,7})", re.IGNORECASE),
            "accountant_card": re.compile(r"(?:Expert[-\s]comptable|Ordre des experts[-\s]comptables)\s*:?\s*N°\s*([0-9]{1,6})", re.IGNORECASE)
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
    
    def extract(self, text=None, image_path=None):
        """
        Point d'entrée principal pour l'extraction des informations d'un document d'identité
        
        Args:
            text (str, optional): Texte du document si déjà extrait
            image_path (str, optional): Chemin vers l'image du document
            
        Returns:
            dict: Informations extraites du document
        """
        if not text and not image_path:
            self.logger.error("Aucune donnée fournie pour l'extraction (texte ou image)")
            return None
        
        # Si seulement l'image est fournie, tenter une extraction OCR
        if not text and image_path and self.ocr_enabled:
            text = self.extract_text_from_image(image_path)
            
            if not text:
                self.logger.warning("Échec de l'extraction OCR, impossible de continuer")
                return None
        
        # Détection du type de document et du pays
        doc_type, country = self.detect_document_type(text, image_path)
        
        # Extraction des informations à partir du texte
        result = self.extract_from_text(text, doc_type, country)
        
        return result
    
    def extract_text_from_image(self, image_path):
        """
        Extrait le texte d'une image en utilisant OCR
        
        Args:
            image_path (str): Chemin vers l'image du document
            
        Returns:
            str: Texte extrait de l'image ou None si échec
        """
        if not self.ocr_enabled:
            self.logger.warning("OCR non activé ou non disponible")
            return None
        
        try:
            # Chargement de l'image
            img = cv2.imread(image_path)
            if img is None:
                self.logger.error(f"Impossible de charger l'image: {image_path}")
                return None
                
            # Prétraitement de l'image pour améliorer l'OCR
            # Conversion en niveaux de gris
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Amélioration du contraste par égalisation d'histogramme
            enhanced = cv2.equalizeHist(gray)
            
            # Réduction du bruit par flou gaussien
            denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)
            
            # Configuration de l'OCR - inclure plusieurs langues pour les documents multilingues
            custom_config = r'--oem 3 --psm 3 -l fra+eng+ara+deu+spa'
            
            # Extraction du texte
            text = pytesseract.image_to_string(denoised, config=custom_config)
            
            if not text or len(text.strip()) < 10:
                # Si peu de texte, essayer sans prétraitement
                text = pytesseract.image_to_string(img, config=custom_config)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'OCR de l'image: {e}")
            return None
    
    def detect_document_type(self, text, image_path=None):
        """
        Détecte le type de document d'identité à partir du texte et/ou de l'image
        
        Args:
            text (str): Texte extrait du document
            image_path (str, optional): Chemin vers l'image du document
            
        Returns:
            tuple: (type de document, pays d'origine)
        """
        doc_type = None
        country = None
        
        # Vérification des mots-clés dans le texte
        text_lower = text.lower()
        
        # Détection du pays
        if "république française" in text_lower or "frança" in text_lower:
            country = "fr"
        elif "royaume du maroc" in text_lower or "المملكة المغربية" in text_lower:
            country = "ma"
        elif "république du sénégal" in text_lower:
            country = "sn"
        elif "république de côte d'ivoire" in text_lower:
            country = "ci"
        elif "république du cameroun" in text_lower:
            country = "cm"
        elif "république algérienne" in text_lower or "الجمهورية الجزائرية" in text_lower:
            country = "dz"
        elif "république tunisienne" in text_lower or "الجمهورية التونسية" in text_lower:
            country = "tn"
        
        # Détection du type de document
        for type_name, keywords in self.DOC_TYPES.items():
            for keyword in keywords:
                if keyword in text_lower:
                    doc_type = type_name
                    break
            if doc_type:
                break
        
        # Si le type n'est pas détecté par les mots-clés, essayer de détecter par les patterns
        if not doc_type:
            # Vérifier les numéros de documents spécifiques aux pays
            if country and country in self.patterns:
                for pattern_name, pattern in self.patterns[country].items():
                    if pattern.search(text):
                        # Extraire le type de document à partir du nom du pattern
                        if "cni" in pattern_name:
                            doc_type = "cni"
                        elif "passport" in pattern_name:
                            doc_type = "passport"
                        elif "residence" in pattern_name:
                            doc_type = "residence"
                        break
        
        # Si toujours pas détecté et que l'OCR est activé, analyser l'image
        if (not doc_type or not country) and image_path and self.ocr_enabled and os.path.exists(image_path):
            try:
                # Utiliser l'analyse d'image pour détecter le type de document
                # Cela pourrait inclure la reconnaissance de couleurs, formats, etc.
                img = cv2.imread(image_path)
                if img is not None:
                    # Analyse des dimensions (ratio largeur/hauteur)
                    height, width = img.shape[:2]
                    ratio = width / height
                    
                    # Analyser la couleur dominante
                    average_color = cv2.mean(img)[:3]  # BGR
                    
                    # Passeport: généralement format carnet
                    if not doc_type:
                        if 1.4 <= ratio <= 1.5:
                            doc_type = "passport"
                        # CNI: généralement format carte de crédit
                        elif 1.55 <= ratio <= 1.6:
                            doc_type = "cni"
                    
                    # Si le pays n'est pas détecté, essayer de déduire à partir des couleurs
                    if not country:
                        # Ces valeurs sont approximatives et nécessiteraient un ajustement plus précis
                        b, g, r = average_color
                        # Bleu foncé: passeport français
                        if b > 120 and r < 60 and g < 70:
                            country = "fr"
                        # Rouge/bordeaux: passeport marocain
                        elif r > 120 and b < 60 and g < 70:
                            country = "ma"
                        # Vert: CNI algérienne
                        elif g > 120 and r < 70 and b < 70:
                            country = "dz"
            except Exception as e:
                self.logger.warning(f"Erreur lors de l'analyse de l'image: {e}")
        
        # Valeurs par défaut si non détectées
        if not doc_type:
            doc_type = "unknown"
        if not country:
            country = "unknown"
            
        return doc_type, country
    
    def extract_from_text(self, text, doc_type=None, country=None):
        """
        Extrait les informations d'identité à partir du texte
        
        Args:
            text (str): Texte du document
            doc_type (str, optional): Type de document si déjà connu
            country (str, optional): Pays d'origine si déjà connu
            
        Returns:
            dict: Informations d'identité extraites
        """
        # Prétraitement du texte
        clean = TextProcessor.clean_text(text)
        processed = TextProcessor.preprocess_text(clean)
        
        # Détection du type de document et du pays si non spécifiés
        if not doc_type or not country:
            detected_type, detected_country = self.detect_document_type(processed)
            doc_type = doc_type or detected_type
            country = country or detected_country
        
        # Initialisation du résultat
        result = {
            "document_type": doc_type,
            "country": country,
            "document_number": None,
            "personal_info": {
                "last_name": None,
                "first_name": None,
                "birth_date": None,
                "birth_place": None,
                "gender": None,
                "nationality": None,
                "address": None,
                "profession": None
            },
            "document_info": {
                "issue_date": None,
                "expiry_date": None,
                "issuing_authority": None
            },
            "additional_info": {}
        }
        
        # Extraction du numéro de document selon le type et le pays
        result["document_number"] = self.extract_document_number(processed, doc_type, country)
        
        # Extraction des informations personnelles génériques
        generic_patterns = self.patterns.get("generic", {})
        
        # Nom de famille
        if "name" in generic_patterns:
            name_match = generic_patterns["name"].search(processed)
            if name_match:
                result["personal_info"]["last_name"] = validate_name(name_match.group(1))
        
        # Prénom
        if "firstname" in generic_patterns:
            firstname_match = generic_patterns["firstname"].search(processed)
            if firstname_match:
                result["personal_info"]["first_name"] = validate_name(firstname_match.group(1))
        
        # Date de naissance
        if "birth_date" in generic_patterns:
            birth_date_match = generic_patterns["birth_date"].search(processed)
            if birth_date_match:
                result["personal_info"]["birth_date"] = validate_date(birth_date_match.group(1))
        
        # Lieu de naissance
        if "birth_place" in generic_patterns:
            birth_place_match = generic_patterns["birth_place"].search(processed)
            if birth_place_match:
                result["personal_info"]["birth_place"] = birth_place_match.group(1).strip().title()
        
        # Genre
        if "gender" in generic_patterns:
            gender_match = generic_patterns["gender"].search(processed)
            if gender_match:
                gender_raw = gender_match.group(1).upper()
                if gender_raw in ["M", "H", "MALE", "HOMME", "ذكر"]:
                    result["personal_info"]["gender"] = "M"
                elif gender_raw in ["F", "FEMALE", "FEMME", "أنثى"]:
                    result["personal_info"]["gender"] = "F"
        
        # Nationalité
        if "nationality" in generic_patterns:
            nationality_match = generic_patterns["nationality"].search(processed)
            if nationality_match:
                result["personal_info"]["nationality"] = nationality_match.group(1).strip().title()
        
        # Adresse
        if "address" in generic_patterns:
            address_match = generic_patterns["address"].search(processed)
            if address_match:
                result["personal_info"]["address"] = address_match.group(1).strip()
        
        # Profession
        if "profession" in generic_patterns:
            profession_match = generic_patterns["profession"].search(processed)
            if profession_match:
                result["personal_info"]["profession"] = profession_match.group(1).strip().title()
        
        # Informations sur le document
        # Date d'émission
        if "issue_date" in generic_patterns:
            issue_date_match = generic_patterns["issue_date"].search(processed)
            if issue_date_match:
                result["document_info"]["issue_date"] = validate_date(issue_date_match.group(1))
        
        # Date d'expiration
        if "expiry_date" in generic_patterns:
            expiry_date_match = generic_patterns["expiry_date"].search(processed)
            if expiry_date_match:
                result["document_info"]["expiry_date"] = validate_date(expiry_date_match.group(1))
        
        # Autorité émettrice
        if "authority" in generic_patterns:
            authority_match = generic_patterns["authority"].search(processed)
            if authority_match:
                result["document_info"]["issuing_authority"] = authority_match.group(1).strip()
        
        # Informations supplémentaires
        # Nom du père
        if "father_name" in generic_patterns:
            father_match = generic_patterns["father_name"].search(processed)
            if father_match:
                result["additional_info"]["father_name"] = validate_name(father_match.group(1))
        
        # Nom de la mère
        if "mother_name" in generic_patterns:
            mother_match = generic_patterns["mother_name"].search(processed)
            if mother_match:
                result["additional_info"]["mother_name"] = validate_name(mother_match.group(1))
        
        # Vérifier si le document est un identifiant fiscal
        if doc_type == "tax_id":
            result = self.extract_tax_id_info(processed, result, country)
        
        # Vérifier si le document est une carte professionnelle
        elif doc_type == "professional_card":
            result = self.extract_professional_card_info(processed, result)
        
        # Utiliser spaCy pour l'extraction avancée si disponible
        if SPACY_AVAILABLE:
            self.extract_with_spacy(processed, result)
        
        return result
    
    def extract_document_number(self, text: str, doc_type: str, country: str) -> Optional[str]:
        """
        Extrait le numéro du document en fonction de son type et du pays
        
        Args:
            text: Texte du document
            doc_type: Type de document
            country: Code pays
            
        Returns:
            str: Numéro de document extrait ou None si non trouvé
        """
        if not text or not doc_type or not country:
            return None
            
        # Sélectionner les patterns appropriés selon le pays et le type de document
        if country in self.patterns:
            country_patterns = self.patterns[country]
            
            # Pour les CNI
            if doc_type == "cni":
                if "cni_number" in country_patterns:
                    match = country_patterns["cni_number"].search(text)
                    if match:
                        number = match.group(1)
                        # Nettoyer le numéro (enlever les espaces)
                        return number.replace(" ", "")
                        
            # Pour les passeports
            elif doc_type == "passport":
                if "passport_number" in country_patterns:
                    match = country_patterns["passport_number"].search(text)
                    if match:
                        number = match.group(1)
                        # Nettoyer le numéro (enlever les espaces)
                        return number.replace(" ", "")
                        
            # Pour les titres de séjour
            elif doc_type == "residence":
                if "residence_number" in country_patterns:
                    match = country_patterns["residence_number"].search(text)
                    if match:
                        number = match.group(1)
                        # Nettoyer le numéro (enlever les espaces)
                        return number.replace(" ", "")
        
        # Si aucun pattern spécifique n'a fonctionné, essayer les patterns génériques
        generic_patterns = [
            # CNI française
            r'(?:№|N°|No|Numéro)\s*(?:CNI|Carte)?\s*:?\s*([0-9]{12}|[0-9]{4}\s*[0-9]{4}\s*[0-9]{4})',
            # CIN marocaine
            r'(?:№|N°|No|Numéro|CIN)\s*:?\s*([A-Z]{1,2}[0-9]{5,6})',
            # Passeport générique
            r'(?:№|N°|No|Numéro)\s*(?:Passeport)?\s*:?\s*([A-Z0-9]{7,9})',
            # Numéro générique
            r'(?:№|N°|No|Numéro)\s*:?\s*([A-Z0-9]{6,14})'
        ]
        
        for pattern in generic_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number = match.group(1)
                # Nettoyer le numéro (enlever les espaces)
                return number.replace(" ", "")
                
        return None
    
    def extract_tax_id_info(self, text, result, country):
        """
        Extrait les informations spécifiques aux identifiants fiscaux
        
        Args:
            text (str): Texte du document
            result (dict): Résultat actuel de l'extraction
            country (str): Pays d'origine
            
        Returns:
            dict: Résultat avec informations fiscales ajoutées
        """
        # Patterns pour les identifiants fiscaux selon les pays
        tax_patterns = self.patterns.get("tax_ids", {})
        
        # France
        if country == "fr" and tax_patterns.get("fr_nif"):
            match = tax_patterns["fr_nif"].search(text)
            if match:
                result["document_number"] = match.group(1).strip()
                result["additional_info"]["tax_type"] = "Numéro fiscal français"
        
        # Maroc
        elif country == "ma" and tax_patterns.get("ma_nif"):
            match = tax_patterns["ma_nif"].search(text)
            if match:
                result["document_number"] = match.group(1).strip()
                result["additional_info"]["tax_type"] = "Identifiant fiscal marocain"
        
        # Sénégal
        elif country == "sn" and tax_patterns.get("sn_ninea"):
            match = tax_patterns["sn_ninea"].search(text)
            if match:
                result["document_number"] = match.group(1).strip()
                result["additional_info"]["tax_type"] = "NINEA sénégalais"
        
        # Côte d'Ivoire
        elif country == "ci" and tax_patterns.get("ci_cc"):
            match = tax_patterns["ci_cc"].search(text)
            if match:
                result["document_number"] = match.group(1).strip()
                result["additional_info"]["tax_type"] = "Compte contribuable ivoirien"
        
        # Centre des impôts ou administration fiscale
        center_match = re.search(
            r"(?:Centre\s+des\s+impôts|Direction\s+des\s+impôts|Administration\s+fiscale)\s*(?:de|:)?\s*([A-ZÀ-Ö\s]{3,50})",
            text,
            re.IGNORECASE
        )
        if center_match:
            result["document_info"]["issuing_authority"] = center_match.group(1).strip()
        
        return result

    def extract_with_spacy(self, text, result):
        """
        Enrichit les résultats d'extraction avec une analyse NLP spécifique aux documents d'identité
        
        Args:
            text (str): Texte à analyser
            result (dict): Résultats d'extraction à enrichir
            
        Returns:
            None: Modifie directement le dictionnaire result
        """
        try:
            # Analyse du texte avec spaCy
            doc = nlp(text)
            
            # Extraction des entités nommées avec contexte
            for ent in doc.ents:
                # Personnes (titulaire du document)
                if ent.label_ == "PER" and len(ent.text) > 3:
                    context_before = text[max(0, ent.start_char - 50):ent.start_char].lower()
                    if not result["personal_info"]["last_name"] or "titulaire" in context_before:
                        name_parts = ent.text.strip().split()
                        if len(name_parts) >= 2:
                            if all(part[0].isupper() for part in name_parts):
                                result["personal_info"]["last_name"] = name_parts[-1]
                                result["personal_info"]["first_name"] = " ".join(name_parts[:-1])
                
                # Lieux (ville de naissance, autorité émettrice)
                elif ent.label_ == "LOC":
                    context_before = text[max(0, ent.start_char - 50):ent.start_char].lower()
                    if "né" in context_before or "naissance" in context_before:
                        if not result["personal_info"]["birth_place"]:
                            result["personal_info"]["birth_place"] = ent.text.strip()
                    elif "délivré" in context_before or "émis" in context_before:
                        if not result["document_info"]["issuing_authority"]:
                            result["document_info"]["issuing_authority"] = ent.text.strip()
                
                # Dates (naissance, émission, expiration)
                elif ent.label_ == "DATE":
                    date_text = ent.text
                    context_before = text[max(0, ent.start_char - 50):ent.start_char].lower()
                    
                    date_patterns = [
                        r'(\d{1,2}[-./]\d{1,2}[-./]\d{2,4})',
                        r'(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})'
                    ]
                    
                    for pattern in date_patterns:
                        date_match = re.search(pattern, date_text)
                        if date_match:
                            date_value = validate_date(date_match.group(1))
                            
                            if date_value:
                                if "né" in context_before or "naissance" in context_before:
                                    result["personal_info"]["birth_date"] = date_value
                                elif "délivré" in context_before or "émission" in context_before:
                                    result["document_info"]["issue_date"] = date_value
                                elif "expire" in context_before or "valable" in context_before:
                                    result["document_info"]["expiry_date"] = date_value
                            break
                
                # Organisations (autorités émettrices)
                elif ent.label_ == "ORG":
                    context_before = text[max(0, ent.start_char - 50):ent.start_char].lower()
                    if "délivré" in context_before or "émis" in context_before:
                        if not result["document_info"]["issuing_authority"]:
                            result["document_info"]["issuing_authority"] = ent.text.strip()
            
            # Analyse supplémentaire pour les numéros de document
            for token in doc:
                if token.like_num:
                    context_before = text[max(0, token.idx - 30):token.idx].lower()
                    # Vérifier si c'est un numéro de document
                    if any(term in context_before for term in ["n°", "numéro", "document", "carte", "passeport"]):
                        if not result["document_number"]:
                            result["document_number"] = token.text.strip()
        
        except Exception as e:
            self.logger.warning(f"Erreur lors de l'enrichissement NLP: {e}")
            # Ne pas lever l'exception pour maintenir la robustesse