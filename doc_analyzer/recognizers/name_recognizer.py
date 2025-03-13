#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de reconnaissance et analyse de noms pour Vynal Docs Automator
Ce module permet d'identifier, extraire et normaliser les noms de personnes
dans différents formats et contextes, avec support des spécificités culturelles.
"""

import re
import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from enum import Enum
import unicodedata

# Configuration du logger
logger = logging.getLogger("VynalDocsAutomator.DocAnalyzer.NameRecognizer")

# Importation conditionnelle de spaCy pour la NER
try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load("fr_core_news_sm")
    except OSError:
        logger.warning("Modèle fr_core_news_sm non trouvé. Tentative de téléchargement...")
        from spacy.cli import download
        download("fr_core_news_sm")
        nlp = spacy.load("fr_core_news_sm")
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle spaCy: {e}")
        nlp = spacy.blank("fr")
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy non disponible, fonctionnalités NER limitées")

class NameType(Enum):
    """Types de noms supportés"""
    PERSON = "person"                  # Nom de personne physique
    COMPANY = "company"                # Nom d'entreprise
    ORGANIZATION = "organization"      # Nom d'organisation, association
    ADMINISTRATION = "administration"  # Nom d'administration publique
    PLACE = "place"                    # Nom de lieu (ville, bâtiment)
    UNKNOWN = "unknown"                # Type inconnu


class NameRecognizer:
    """
    Classe responsable de la reconnaissance et analyse des noms
    """
    
    def __init__(self, resources_path=None):
        """
        Initialisation du reconnaisseur de noms
        
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
        
        self.logger.info("Reconnaisseur de noms initialisé")
    
    def _load_patterns(self) -> Dict[str, Any]:
        """
        Charge les patterns regex pour la reconnaissance de noms
        
        Returns:
            dict: Dictionnaire de patterns par type
        """
        patterns = {
            # Patterns pour les noms de personnes
            "person": {
                # Nom complet avec titre: M. Jean DUPONT
                "full_name_with_title": re.compile(
                    r"(?:M(?:r|onsieur|me|adame|lle|ademoiselle)|Dr|Me|Pr|Prof)\.?\s+([A-ZÀ-Ö][a-zà-ö\-]+(?:\s+[A-ZÀ-Ö][a-zà-ö\-]+)*)\s+([A-ZÀ-Ö\s\-]+)",
                    re.UNICODE
                ),
                # Nom complet sans titre: Jean DUPONT, en tenant compte des particules
                "full_name": re.compile(
                    r"([A-ZÀ-Ö][a-zà-ö\-]+(?:\s+(?:d[eu]|l[ae]|von|van|el|al|bin|ben|Mac|Mc|de\s+la|du)\s+)?(?:[A-ZÀ-Ö][a-zà-ö\-]+)*)\s+([A-ZÀ-Ö\s\-]+)",
                    re.UNICODE
                ),
                # Prénom seul: indiqué explicitement
                "first_name": re.compile(
                    r"(?:prénom|prénoms?|first\s+name|given\s+name)s?\s*:?\s*([A-ZÀ-Ö][a-zà-ö\-]+(?:\s+[A-ZÀ-Ö][a-zà-ö\-]+)*)",
                    re.IGNORECASE | re.UNICODE
                ),
                # Nom de famille seul: indiqué explicitement
                "last_name": re.compile(
                    r"(?:nom|noms?|last\s+name|surname|family\s+name|nom\s+de\s+famille)s?\s*:?\s*([A-ZÀ-Ö\s\-]+)",
                    re.IGNORECASE | re.UNICODE
                ),
                # Signature en fin de document
                "signature": re.compile(
                    r"(?:signé|signature|fait\s+à.*?le.*?)[^\n]*\n\s*([A-ZÀ-Ö][a-zà-ö\-]+(?:\s+[A-ZÀ-Ö][a-zà-ö\-]+)*(?:\s+[A-ZÀ-Ö\s\-]+)?)",
                    re.IGNORECASE | re.UNICODE
                )
            },
            
            # Patterns pour les noms d'entreprises
            "company": {
                # Entreprise avec forme juridique: DUPONT CONSULTING SAS
                "with_legal_form": re.compile(
                    r"([A-Z0-9\s\.\-\&\']{2,50})\s+(S\.?A\.?(?:S|RL)?|S\.?A\.?R\.?L|E\.?U\.?R\.?L|S\.?N\.?C|S\.?C\.?I|S\.?A\.?S\.?U|E\.?I|GMBH|LLC|LTD|INC|CORP|\&\s+CIE|\&\s+CO)",
                    re.UNICODE
                ),
                # Entreprise mentionnée explicitement
                "explicit_mention": re.compile(
                    r"(?:société|company|entreprise|sté)\s*:?\s*([A-Z0-9][A-Z0-9\s\.\-\&\']{2,50}(?:\s+(?:S\.?A\.?(?:S|RL)?|S\.?A\.?R\.?L|E\.?U\.?R\.?L|S\.?N\.?C|S\.?C\.?I|S\.?A\.?S\.?U|E\.?I|GMBH|LLC|LTD|INC|CORP))?)",
                    re.IGNORECASE | re.UNICODE
                )
            },
            
            # Patterns pour les organisations et associations
            "organization": {
                # Organisation explicite
                "explicit_mention": re.compile(
                    r"(?:association|organisation|organization|ong|ngo|fondation|foundation|syndicat|union|fédération|federation)\s*:?\s*([A-Z0-9][A-Za-z0-9\s\.\-\&\']{2,60})",
                    re.IGNORECASE | re.UNICODE
                )
            },
            
            # Patterns pour les administrations
            "administration": {
                # Administration publique
                "public_admin": re.compile(
                    r"(?:ministère|ministry|préfecture|mairie|commune|département|région|direction|agence|office|commission|autorité|authority)\s+(?:d[eu]|des|de\s+la|du|of|for|the)?\s+([A-Z][A-Za-z\s\-\']{2,60})",
                    re.IGNORECASE | re.UNICODE
                )
            }
        }
        
        # Tentative de chargement des patterns supplémentaires depuis les fichiers
        try:
            patterns_file = os.path.join(self.resources_path, "patterns", "name_patterns.json")
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    additional_patterns = json.load(f)
                    
                    # Conversion des patterns chargés en objets regex
                    for category, category_patterns in additional_patterns.items():
                        if category not in patterns:
                            patterns[category] = {}
                            
                        for pattern_name, pattern_str in category_patterns.items():
                            patterns[category][pattern_name] = re.compile(pattern_str, re.IGNORECASE | re.UNICODE)
        except Exception as e:
            self.logger.warning(f"Impossible de charger les patterns supplémentaires: {e}")
        
        return patterns
    
    def _load_reference_data(self) -> Dict[str, Any]:
        """
        Charge les données de référence pour la validation des noms
        
        Returns:
            dict: Dictionnaire de données de référence
        """
        reference_data = {
            # Titres et civilités par langue
            "titles": {
                "fr": {
                    "male": ["M.", "Monsieur", "Mr", "Dr", "Pr", "Professeur", "Docteur", "Maître", "Me"],
                    "female": ["Mme", "Madame", "Mlle", "Mademoiselle", "Dr", "Pr", "Professeure", "Docteure", "Maître", "Me"]
                },
                "en": {
                    "male": ["Mr", "Mr.", "Mister", "Dr", "Prof.", "Professor", "Doctor", "Sir", "Master"],
                    "female": ["Mrs", "Mrs.", "Ms", "Ms.", "Miss", "Dr", "Prof.", "Professor", "Doctor", "Lady", "Madam"]
                }
            },
            
            # Particules de noms par langue
            "particles": {
                "fr": ["de", "du", "des", "le", "la", "l'", "d'", "de la", "du"],
                "nl": ["van", "van der", "van den", "van de"],
                "de": ["von", "von der", "zu", "von und zu"],
                "es": ["de", "del", "de la", "de los", "de las"],
                "it": ["di", "da", "del", "della", "dei", "degli", "delle"],
                "ar": ["al", "el", "bin", "ben", "ibn"]
            },
            
            # Formes juridiques par pays
            "legal_forms": {
                "fr": ["SA", "SARL", "SAS", "SASU", "EURL", "SNC", "SCS", "SCA", "SCOP", "SCI", "GIE", "EI", "EIRL", "Association"],
                "uk": ["Ltd", "PLC", "LLP", "LP", "CIC"],
                "us": ["Inc", "LLC", "Corp", "LP", "LLP", "PLLC"],
                "de": ["GmbH", "AG", "KG", "OHG", "GbR", "e.V."],
                "ma": ["SA", "SARL", "SNC", "SCS", "GIE"]
            },
            
            # Liste des prénoms courants
            "first_names": set(),
            
            # Liste des noms de famille courants
            "last_names": set()
        }
        
        # Tentative de chargement des données de référence depuis les fichiers
        try:
            ref_dir = os.path.join(self.resources_path, "reference_data")
            
            # Chargement des prénoms
            first_names_file = os.path.join(ref_dir, "first_names.txt")
            if os.path.exists(first_names_file):
                with open(first_names_file, 'r', encoding='utf-8') as f:
                    reference_data["first_names"] = {line.strip() for line in f if line.strip()}
            
            # Chargement des noms de famille
            last_names_file = os.path.join(ref_dir, "last_names.txt")
            if os.path.exists(last_names_file):
                with open(last_names_file, 'r', encoding='utf-8') as f:
                    reference_data["last_names"] = {line.strip() for line in f if line.strip()}
        
        except Exception as e:
            self.logger.warning(f"Erreur lors du chargement des données de référence: {e}")
        
        return reference_data
    
    def recognize_names(self, text: str) -> List[Dict[str, Any]]:
        """
        Reconnait et extrait tous les noms d'un texte
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            list: Liste des noms trouvés avec leurs métadonnées
        """
        # Prétraitement du texte
        text = self._preprocess_text(text)
        
        # Liste pour stocker tous les noms trouvés
        found_names = []
        
        # Extraction par type de nom
        for name_type in ["person", "company", "organization", "administration"]:
            names = self._extract_names_by_type(text, name_type)
            found_names.extend(names)
        
        # Extraction avec spaCy si disponible
        if SPACY_AVAILABLE:
            spacy_names = self._extract_names_with_spacy(text)
            
            # Filtrer les doublons potentiels
            for spacy_name in spacy_names:
                # Vérifier si ce nom n'est pas déjà dans les résultats
                if not self._is_duplicate(found_names, spacy_name):
                    found_names.append(spacy_name)
        
        # Tri par score de confiance
        found_names.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        return found_names
    
    def _extract_names_by_type(self, text: str, name_type: str) -> List[Dict[str, Any]]:
        """
        Extrait les noms d'un type spécifique à partir d'un texte
        
        Args:
            text (str): Texte à analyser
            name_type (str): Type de nom à extraire
            
        Returns:
            list: Liste des noms trouvés avec leurs métadonnées
        """
        found_names = []
        
        # Récupérer les patterns pour ce type
        type_patterns = self.patterns.get(name_type, {})
        
        for pattern_name, pattern in type_patterns.items():
            matches = pattern.finditer(text)
            
            for match in matches:
                # Récupérer le contexte (30 caractères avant et après)
                start_pos = max(0, match.start() - 30)
                end_pos = min(len(text), match.end() + 30)
                context = text[start_pos:end_pos]
                
                # Extraire la valeur selon le type de pattern
                name_value = ""
                name_components = {}
                
                if name_type == "person":
                    if pattern_name == "full_name_with_title" and match.groups() >= 2:
                        # Récupérer le titre, prénom et nom
                        full_match = match.group(0)
                        title_match = re.match(r"(M(?:r|onsieur|me|adame|lle|ademoiselle)|Dr|Me|Pr|Prof)\.?", full_match)
                        title = title_match.group(1) if title_match else ""
                        
                        first_name = match.group(1)
                        last_name = match.group(2)
                        
                        name_value = f"{first_name} {last_name}".strip()
                        name_components = {
                            "title": title,
                            "first_name": first_name,
                            "last_name": last_name
                        }
                    
                    elif pattern_name == "full_name" and match.groups() >= 2:
                        first_name = match.group(1)
                        last_name = match.group(2)
                        
                        name_value = f"{first_name} {last_name}".strip()
                        name_components = {
                            "first_name": first_name,
                            "last_name": last_name
                        }
                    
                    elif pattern_name == "first_name":
                        name_value = match.group(1)
                        name_components = {
                            "first_name": name_value
                        }
                    
                    elif pattern_name == "last_name":
                        name_value = match.group(1)
                        name_components = {
                            "last_name": name_value
                        }
                    
                    elif pattern_name == "signature":
                        signature = match.group(1).strip()
                        
                        # Tenter de distinguer prénom et nom dans la signature
                        parts = signature.split()
                        if len(parts) >= 2:
                            # Heuristique: le dernier mot est généralement le nom de famille
                            first_name = " ".join(parts[:-1])
                            last_name = parts[-1]
                            
                            name_value = signature
                            name_components = {
                                "first_name": first_name,
                                "last_name": last_name
                            }
                        else:
                            name_value = signature
                
                else:  # Entreprise, organisation ou administration
                    name_value = match.group(1).strip()
                
                # Si on a trouvé un nom valide
                if name_value:
                    # Normaliser le nom
                    name_value = self._normalize_name(name_value, name_type)
                    
                    # Déterminer le type de nom
                    name_type_enum = self._determine_name_type(name_value, name_type, context)
                    
                    # Créer l'entrée
                    name_data = {
                        "value": name_value,
                        "type": name_type_enum.value,
                        "confidence_score": self._calculate_confidence(name_value, name_type_enum, pattern_name, context),
                        "context": context,
                        "components": name_components,
                        "metadata": {}
                    }
                    
                    # Ajouter des métadonnées spécifiques
                    self._add_specific_metadata(name_data, name_value, name_type_enum)
                    
                    # Vérifier si ce n'est pas un doublon
                    if not self._is_duplicate(found_names, name_data):
                        found_names.append(name_data)
        
        return found_names
    
    def _extract_names_with_spacy(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrait les noms à l'aide de l'analyse spaCy (NER)
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            list: Liste des noms trouvés avec leurs métadonnées
        """
        found_names = []
        
        try:
            # Analyse du texte avec spaCy
            doc = nlp(text)
            
            # Extraction des entités nommées
            for ent in doc.ents:
                # Déterminer le type de nom
                name_type_enum = None
                
                if ent.label_ == "PER":
                    name_type_enum = NameType.PERSON
                elif ent.label_ == "ORG":
                    # Distinguer entreprise et organisation
                    if self._is_likely_company(ent.text):
                        name_type_enum = NameType.COMPANY
                    else:
                        name_type_enum = NameType.ORGANIZATION
                elif ent.label_ in ["GPE", "LOC"] and self._is_likely_administration(ent.text):
                    name_type_enum = NameType.ADMINISTRATION
                elif ent.label_ == "LOC":
                    name_type_enum = NameType.PLACE
                
                # Si on a un type de nom valide
                if name_type_enum and len(ent.text) > 2:
                    # Récupérer le contexte (30 caractères avant et après)
                    start_pos = max(0, ent.start_char - 30)
                    end_pos = min(len(text), ent.end_char + 30)
                    context = text[start_pos:end_pos]
                    
                    # Normaliser le nom
                    name_value = self._normalize_name(ent.text, name_type_enum.value)
                    
                    # Créer l'entrée
                    name_data = {
                        "value": name_value,
                        "type": name_type_enum.value,
                        "confidence_score": 0.7,  # Score de base pour les entités spaCy
                        "context": context,
                        "components": {},
                        "metadata": {
                            "source": "spacy_ner",
                            "entity_label": ent.label_
                        }
                    }
                    
                    # Pour les personnes, tenter de distinguer prénom et nom
                    if name_type_enum == NameType.PERSON:
                        parts = name_value.split()
                        if len(parts) >= 2:
                            # Heuristique: le dernier mot est généralement le nom de famille
                            first_name = " ".join(parts[:-1])
                            last_name = parts[-1]
                            
                            name_data["components"] = {
                                "first_name": first_name,
                                "last_name": last_name
                            }
                    
                    # Ajouter des métadonnées spécifiques
                    self._add_specific_metadata(name_data, name_value, name_type_enum)
                    
                    found_names.append(name_data)
        
        except Exception as e:
            self.logger.warning(f"Erreur lors de l'extraction des noms avec spaCy: {e}")
        
        return found_names
    
    def _preprocess_text(self, text: str) -> str:
        """
        Prétraite le texte pour améliorer la reconnaissance des noms
        
        Args:
            text (str): Texte à prétraiter
            
        Returns:
            str: Texte prétraité
        """
        # Normalisation des retours à la ligne
        text = re.sub(r'(\r\n|\r)', '\n', text)
        
        # Normalisation des espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Conversion en forme normalisée Unicode (pour les accents)
        text = unicodedata.normalize('NFC', text)
        
        return text
    
    def _normalize_name(self, name: str, name_type: str) -> str:
        """
        Normalise un nom selon son type
        
        Args:
            name (str): Nom à normaliser
            name_type (str): Type de nom
            
        Returns:
            str: Nom normalisé
        """
        # Supprimer les espaces en début et fin
        name = name.strip()
        
        if name_type == "person":
            # Pour les personnes, formater correctement les noms
            parts = name.split()
            normalized_parts = []
            
            for i, part in enumerate(parts):
                part = part.strip()
                
                # Les particules restent en minuscules
                is_particle = False
                for lang, particles in self.reference_data["particles"].items():
                    if part.lower() in particles:
                        normalized_parts.append(part.lower())
                        is_particle = True
                        break
                
                if not is_particle:
                    # Le premier mot est généralement le prénom: première lettre en majuscule
                    if i == 0:
                        normalized_parts.append(part.capitalize())
                    # Les noms de famille sont souvent en majuscules dans les documents officiels
                    elif i == len(parts) - 1 or all(c.isupper() for c in part if c.isalpha()):
                        normalized_parts.append(part.upper())
                    else:
                        normalized_parts.append(part.capitalize())
            
            return " ".join(normalized_parts)
        
        elif name_type in ["company", "organization"]:
            # Pour les entreprises et organisations, maintenir les majuscules
            if name.isupper():
                return name
            else:
                # Si ce n'est pas tout en majuscules, normaliser les mots
                parts = name.split()
                normalized_parts = []
                
                for part in parts:
                    # Les formes juridiques restent telles quelles
                    is_legal_form = False
                    for country, forms in self.reference_data["legal_forms"].items():
                        if part.upper() in forms:
                            normalized_parts.append(part.upper())
                            is_legal_form = True
                            break
                    
                    if not is_legal_form:
                        # Normaliser avec première lettre en majuscule
                        normalized_parts.append(part.capitalize())
                
                return " ".join(normalized_parts)
        
        elif name_type == "administration":
            # Pour les administrations, première lettre de chaque mot en majuscule
            return " ".join(word.capitalize() for word in name.split())
        
        # Par défaut, retourner le nom tel quel
        return name
    
    def _determine_name_type(self, name: str, source_type: str, context: str = None) -> NameType:
        """
        Détermine le type de nom précis
        
        Args:
            name (str): Nom
            source_type (str): Type de source dont est issu le nom
            context (str, optional): Contexte textuel
            
        Returns:
            NameType: Type de nom
        """
        # Mapping direct
        type_mapping = {
            "person": NameType.PERSON,
            "company": NameType.COMPANY,
            "organization": NameType.ORGANIZATION,
            "administration": NameType.ADMINISTRATION,
            "place": NameType.PLACE
        }
        
        if source_type in type_mapping:
            return type_mapping[source_type]
        
        # Analyse du contexte et du nom pour déterminer le type
        if context:
            context_lower = context.lower()
            
            # Indices pour les personnes
            if any(term in context_lower for term in ["monsieur", "madame", "né le", "née le", "mr", "mrs", "ms"]):
                return NameType.PERSON
            
            # Indices pour les entreprises
            if any(term in context_lower for term in ["société", "entreprise", "company", "siret", "siren", "rcs"]):
                return NameType.COMPANY
            
            # Indices pour les organisations
            if any(term in context_lower for term in ["association", "organisation", "organization", "syndicat", "fédération"]):
                return NameType.ORGANIZATION
            
            # Indices pour les administrations
            if any(term in context_lower for term in ["ministère", "préfecture", "mairie", "direction", "agence", "autorité"]):
                return NameType.ADMINISTRATION
        
        # Analyse du nom lui-même
        name_lower = name.lower()
        
        # Vérifier s'il y a une forme juridique dans le nom
        for country, forms in self.reference_data["legal_forms"].items():
            if any(form.lower() in name_lower for form in forms):
                return NameType.COMPANY
        
        # Si le nom contient des termes administratifs
        admin_terms = ["ministère", "ministry", "préfecture", "mairie", "commune", "département", "région"]
        if any(term in name_lower for term in admin_terms):
            return NameType.ADMINISTRATION
        
        # Par défaut (si incertain)
        return NameType.UNKNOWN
    
    def _calculate_confidence(self, name: str, name_type: NameType, pattern_name: str, context: str = None) -> float:
        """
        Calcule un score de confiance pour le nom extrait
        
        Args:
            name (str): Nom
            name_type (NameType): Type de nom
            pattern_name (str): Nom du pattern utilisé
            context (str, optional): Contexte textuel
            
        Returns:
            float: Score de confiance entre 0 et 1
        """
        score = 0.5  # Score de base
        
        # Bonus selon le type de pattern utilisé
        if name_type == NameType.PERSON:
            if pattern_name == "full_name_with_title":
                score += 0.3  # Confiance élevée pour les noms avec titre
            elif pattern_name == "full_name":
                score += 0.2  # Bonne confiance pour les noms complets
            elif pattern_name in ["first_name", "last_name"]:
                score += 0.1  # Confiance moyenne pour les noms partiels
            elif pattern_name == "signature":
                score += 0.15  # Confiance modérée pour les signatures
        
        elif name_type in [NameType.COMPANY, NameType.ORGANIZATION]:
            if pattern_name == "with_legal_form":
                score += 0.3  # Confiance élevée pour les noms avec forme juridique
            elif pattern_name == "explicit_mention":
                score += 0.2  # Bonne confiance pour les mentions explicites
        
        elif name_type == NameType.ADMINISTRATION:
            if pattern_name == "public_admin":
                score += 0.25  # Bonne confiance pour les administrations
        
        # Bonus pour la longueur du nom (évite les faux positifs courts)
        if len(name) > 3:
            score += 0.05
        if len(name) > 8:
            score += 0.05
        
        # Vérification dans les listes de référence pour les personnes
        if name_type == NameType.PERSON and "components" in name:
            components = name.get("components", {})
            
            if "first_name" in components and components["first_name"] in self.reference_data["first_names"]:
                score += 0.1  # Bonus si le prénom est dans la liste de référence
            
            if "last_name" in components and components["last_name"] in self.reference_data["last_names"]:
                score += 0.1  # Bonus si le nom de famille est dans la liste de référence
        
        # Vérification du contexte
        if context:
            context_lower = context.lower()
            
            # Contexte validant le type de nom
            if name_type == NameType.PERSON and any(term in context_lower for term in ["monsieur", "madame", "né le", "née le"]):
                score += 0.1
            elif name_type == NameType.COMPANY and any(term in context_lower for term in ["société", "entreprise", "siret"]):
                score += 0.1
            elif name_type == NameType.ORGANIZATION and any(term in context_lower for term in ["association", "organisation", "statuts"]):
                score += 0.1
            elif name_type == NameType.ADMINISTRATION and any(term in context_lower for term in ["ministère", "préfecture", "public"]):
                score += 0.1
        
        # Plafonner à 1.0
        return min(1.0, score)
    
    def _is_duplicate(self, found_names: List[Dict[str, Any]], name_data: Dict[str, Any]) -> bool:
        """
        Vérifie si un nom est déjà dans la liste des noms trouvés
        
        Args:
            found_names (list): Liste des noms trouvés
            name_data (dict): Données du nom à vérifier
            
        Returns:
            bool: True si le nom est un doublon
        """
        # Normalisation du nom pour la comparaison
        name_norm = self._normalize_for_comparison(name_data["value"])
        
        for found_name in found_names:
            found_name_norm = self._normalize_for_comparison(found_name["value"])
            
            # Vérifier la similarité
            if self._calculate_name_similarity(name_norm, found_name_norm) > 0.8:
                return True
        
        return False
    
    def _normalize_for_comparison(self, name: str) -> str:
        """
        Normalise un nom pour la comparaison (suppression des accents, majuscules, etc.)
        
        Args:
            name (str): Nom à normaliser
            
        Returns:
            str: Nom normalisé pour comparaison
        """
        # Convertir en minuscules
        name = name.lower()
        
        # Supprimer les accents
        name = ''.join(c for c in unicodedata.normalize('NFD', name) if not unicodedata.combining(c))
        
        # Supprimer les caractères non alphanumériques
        name = re.sub(r'[^a-z0-9\s]', '', name)
        
        # Supprimer les mots courants et particules
        particles = sum([particles for lang, particles in self.reference_data["particles"].items()], [])
        name_parts = name.split()
        name_parts = [part for part in name_parts if part not in particles]
        
        # Supprimer les titres de civilité
        titles = []
        for lang, title_dict in self.reference_data["titles"].items():
            titles.extend(title_dict["male"])
            titles.extend(title_dict["female"])
        
        titles = [title.lower() for title in titles]
        name_parts = [part for part in name_parts if part not in titles]
        
        return ' '.join(name_parts)
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calcule la similarité entre deux noms
        
        Args:
            name1 (str): Premier nom
            name2 (str): Deuxième nom
            
        Returns:
            float: Score de similarité entre 0 et 1
        """
        # Si les noms sont identiques
        if name1 == name2:
            return 1.0
        
        # Si l'un des noms est vide
        if not name1 or not name2:
            return 0.0
        
        # Diviser en mots
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        # Intersection et union des mots
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        # Coefficient de Jaccard (similarité entre ensembles)
        if union:
            return len(intersection) / len(union)
        return 0.0
    
    def _is_likely_company(self, name: str) -> bool:
        """
        Détermine si un nom est probablement celui d'une entreprise
        
        Args:
            name (str): Nom à vérifier
            
        Returns:
            bool: True si le nom est probablement celui d'une entreprise
        """
        name_lower = name.lower()
        
        # Vérifier la présence de formes juridiques
        for country, forms in self.reference_data["legal_forms"].items():
            if any(form.lower() in name_lower for form in forms):
                return True
        
        # Vérifier les suffixes courants d'entreprise
        company_suffixes = ["inc", "llc", "ltd", "corp", "company", "co", "& co", "group", "holding", "enterprise"]
        if any(suffix in name_lower for suffix in company_suffixes):
            return True
        
        # Vérifier si le nom contient des termes typiques d'entreprise
        company_terms = ["consulting", "solutions", "services", "technologies", "systems", "consulting", "partners"]
        if any(term in name_lower for term in company_terms):
            return True
        
        return False
    
    def _is_likely_administration(self, name: str) -> bool:
        """
        Détermine si un nom est probablement celui d'une administration
        
        Args:
            name (str): Nom à vérifier
            
        Returns:
            bool: True si le nom est probablement celui d'une administration
        """
        name_lower = name.lower()
        
        # Termes administratifs courants
        admin_terms = ["ministère", "ministry", "préfecture", "mairie", "commune", "département", 
                      "région", "direction", "agence", "office", "commission", "autorité", "authority"]
        
        return any(term in name_lower for term in admin_terms)
    
    def _add_specific_metadata(self, name_data: Dict[str, Any], name_value: str, name_type: NameType):
        """
        Ajoute des métadonnées spécifiques à un nom selon son type
        
        Args:
            name_data (dict): Données du nom à enrichir
            name_value (str): Valeur du nom
            name_type (NameType): Type de nom
        """
        if name_type == NameType.PERSON:
            # Pour les personnes, détecter le genre
            components = name_data.get("components", {})
            
            if "title" in components:
                title = components["title"].lower()
                
                # Détection du genre par le titre
                for lang, titles in self.reference_data["titles"].items():
                    if title in [t.lower() for t in titles["male"]]:
                        name_data["metadata"]["gender"] = "M"
                        break
                    elif title in [t.lower() for t in titles["female"]]:
                        name_data["metadata"]["gender"] = "F"
                        break
            
            # Détection de la structure du nom
            if "first_name" in components and "last_name" in components:
                first_name = components["first_name"]
                last_name = components["last_name"]
                
                # Vérifier les particules
                last_name_parts = last_name.split()
                particles = []
                
                for lang, lang_particles in self.reference_data["particles"].items():
                    for part in last_name_parts:
                        if part.lower() in lang_particles:
                            particles.append(part.lower())
                
                if particles:
                    name_data["metadata"]["particles"] = particles
                
                # Format d'affichage recommandé
                name_data["metadata"]["display_format"] = f"{first_name} {last_name}"
                name_data["metadata"]["formal_format"] = last_name
                
                if "title" in components:
                    name_data["metadata"]["formal_format"] = f"{components['title']} {last_name}"
        
        elif name_type == NameType.COMPANY:
            # Pour les entreprises, identifier la forme juridique
            legal_form = None
            
            # Séparation du nom de la forme juridique
            name_parts = name_value.split()
            if name_parts:
                last_part = name_parts[-1].upper()
                
                for country, forms in self.reference_data["legal_forms"].items():
                    if last_part in forms:
                        legal_form = last_part
                        name_data["metadata"]["legal_form"] = legal_form
                        name_data["metadata"]["possible_country"] = country
                        
                        # Nom commercial sans la forme juridique
                        name_data["metadata"]["trade_name"] = " ".join(name_parts[:-1])
                        break
    
    def find_names_by_type(self, text: str, name_type: NameType) -> List[Dict[str, Any]]:
        """
        Recherche des noms d'un type spécifique dans le texte
        
        Args:
            text (str): Texte à analyser
            name_type (NameType): Type de nom à rechercher
            
        Returns:
            list: Liste des noms du type demandé
        """
        # Récupérer tous les noms
        all_names = self.recognize_names(text)
        
        # Filtrer par type
        filtered_names = [name_data for name_data in all_names if name_data["type"] == name_type.value]
        
        return filtered_names
    
    def extract_best_name(self, text: str, name_type: NameType = None) -> Optional[Dict[str, Any]]:
        """
        Extrait le meilleur nom du type spécifié dans le texte
        
        Args:
            text (str): Texte à analyser
            name_type (NameType, optional): Type de nom à rechercher
            
        Returns:
            dict: Meilleur nom trouvé ou None si aucun
        """
        # Récupérer tous les noms
        all_names = self.recognize_names(text)
        
        # Si aucun nom trouvé
        if not all_names:
            return None
        
        # Filtrer par type si demandé
        if name_type:
            filtered_names = [name_data for name_data in all_names if name_data["type"] == name_type.value]
            
            # Si aucun nom après filtrage
            if not filtered_names:
                return None
            
            # Retourner celui avec le meilleur score de confiance
            return max(filtered_names, key=lambda x: x["confidence_score"])
        
        # Sinon, retourner simplement le nom avec le meilleur score
        return max(all_names, key=lambda x: x["confidence_score"])
    
    def format_name(self, name_data: Dict[str, Any], format_type: str = "standard") -> str:
        """
        Formate un nom selon un format spécifique
        
        Args:
            name_data (dict): Données du nom à formater
            format_type (str): Type de formatage (standard, formal, initial)
            
        Returns:
            str: Nom formaté
        """
        name_type = name_data["type"]
        
        if name_type == NameType.PERSON.value:
            components = name_data.get("components", {})
            
            if "first_name" in components and "last_name" in components:
                first_name = components["first_name"]
                last_name = components["last_name"]
                
                if format_type == "standard":
                    return f"{first_name} {last_name}"
                
                elif format_type == "formal":
                    # Format formel (avec titre éventuel)
                    if "title" in components:
                        return f"{components['title']} {last_name}"
                    else:
                        return last_name
                
                elif format_type == "initial":
                    # Format avec initiales pour le prénom
                    initials = ''.join(word[0] + '.' for word in first_name.split())
                    return f"{initials} {last_name}"
                
                elif format_type == "full":
                    # Format complet avec titre
                    if "title" in components:
                        return f"{components['title']} {first_name} {last_name}"
                    else:
                        return f"{first_name} {last_name}"
            
            # Si on n'a pas les composants, retourner la valeur telle quelle
            return name_data["value"]
        
        elif name_type == NameType.COMPANY.value:
            # Pour les entreprises, formats selon le besoin
            if format_type == "standard":
                return name_data["value"]
            
            elif format_type == "trade_name" and "metadata" in name_data and "trade_name" in name_data["metadata"]:
                # Juste le nom commercial sans la forme juridique
                return name_data["metadata"]["trade_name"]
            
            elif format_type == "legal":
                # Format légal complet avec forme juridique
                if "metadata" in name_data and "legal_form" in name_data["metadata"]:
                    trade_name = name_data["metadata"].get("trade_name", name_data["value"])
                    legal_form = name_data["metadata"]["legal_form"]
                    return f"{trade_name} {legal_form}"
            
            # Par défaut, retourner le nom tel quel
            return name_data["value"]
        
        # Pour les autres types, retourner le nom tel quel
        return name_data["value"]
    
    def extract_persons_with_roles(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrait les personnes avec leurs rôles éventuels dans le document
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            list: Liste des personnes avec leurs rôles
        """
        # Récupérer toutes les personnes
        persons = self.find_names_by_type(text, NameType.PERSON)
        
        # Enrichir avec les rôles
        for person in persons:
            context = person.get("context", "")
            
            # Recherche de rôles dans le contexte
            role_patterns = [
                (r"en (?:qualité|sa qualité) de ([^,\.;]+)", "role"),
                (r"(?:agissant|agissant comme|agissant en tant que) ([^,\.;]+)", "role"),
                (r"(?:représent(?:é|ée|ée|ant)|mandataire) (?:par|de) ([^,\.;]+)", "representing"),
                (r"(?:président|directeur|gérant|administrateur|secrétaire|trésorier|directeur général|PDG) ([^,\.;]+)", "position")
            ]
            
            for pattern, role_type in role_patterns:
                role_match = re.search(pattern, context, re.IGNORECASE)
                if role_match:
                    role = role_match.group(1).strip()
                    
                    if "metadata" not in person:
                        person["metadata"] = {}
                    
                    person["metadata"]["role_type"] = role_type
                    person["metadata"]["role"] = role
                    break
        
        return persons
    
    def link_persons_to_organizations(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Établit des liens entre les personnes et les organisations mentionnées
        
        Args:
            text (str): Texte à analyser
            
        Returns:
            dict: Dictionnaire des organisations avec leurs personnes associées
        """
        # Récupérer toutes les personnes et organisations
        persons = self.find_names_by_type(text, NameType.PERSON)
        companies = self.find_names_by_type(text, NameType.COMPANY)
        organizations = self.find_names_by_type(text, NameType.ORGANIZATION)
        
        # Fusionner entreprises et organisations
        all_orgs = companies + organizations
        
        # Dictionnaire des liens
        links = {}
        
        # Pour chaque organisation
        for org in all_orgs:
            org_name = org["value"]
            org_context = org.get("context", "")
            
            # Liste des personnes liées
            org_persons = []
            
            # Pour chaque personne
            for person in persons:
                person_context = person.get("context", "")
                
                # Vérifier si l'organisation est mentionnée dans le contexte de la personne
                if org_name in person_context:
                    # Rechercher le rôle de la personne par rapport à l'organisation
                    role_patterns = [
                        (r"(?:représent(?:é|ée|ée|ant)|mandataire) (?:par|de) [^,\.;]+ (?:pour|de) " + re.escape(org_name), "representative"),
                        (r"(?:président|directeur|gérant|administrateur|secrétaire|trésorier) (?:de|d'|du|des|de la) " + re.escape(org_name), "executive"),
                        (r"(?:employé|salarié|membre) (?:de|d'|du|des|de la) " + re.escape(org_name), "employee")
                    ]
                    
                    role = None
                    for pattern, role_type in role_patterns:
                        if re.search(pattern, person_context, re.IGNORECASE):
                            role = role_type
                            break
                    
                    # Si un rôle est trouvé ou si le nom de la personne apparaît dans le contexte de l'organisation
                    if role or person["value"] in org_context:
                        # Copier les données de la personne
                        person_copy = person.copy()
                        
                        # Ajouter le rôle s'il a été trouvé
                        if role:
                            if "metadata" not in person_copy:
                                person_copy["metadata"] = {}
                            person_copy["metadata"]["org_role"] = role
                        
                        org_persons.append(person_copy)
            
            # Si des personnes sont liées à cette organisation
            if org_persons:
                links[org_name] = org_persons
        
        return links


# Fonction autonome pour utilisation directe
def extract_names(text, name_type=None):
    """
    Fonction autonome pour extraire les noms d'un texte
    
    Args:
        text (str): Texte à analyser
        name_type (str, optional): Type de nom à rechercher
        
    Returns:
        list: Liste des noms trouvés
    """
    recognizer = NameRecognizer()
    
    # Convertir le type si spécifié
    name_type_enum = None
    if name_type:
        try:
            name_type_enum = NameType[name_type.upper()]
        except (KeyError, AttributeError):
            # Essayer de mapper le nom
            type_mapping = {
                "personne": NameType.PERSON,
                "person": NameType.PERSON,
                "societe": NameType.COMPANY,
                "entreprise": NameType.COMPANY,
                "company": NameType.COMPANY,
                "organisation": NameType.ORGANIZATION,
                "organization": NameType.ORGANIZATION,
                "admin": NameType.ADMINISTRATION,
                "administration": NameType.ADMINISTRATION,
                "lieu": NameType.PLACE,
                "place": NameType.PLACE
            }
            
            name_type_lower = name_type.lower()
            for key, value in type_mapping.items():
                if key in name_type_lower:
                    name_type_enum = value
                    break
    
    # Si un type a été spécifié et trouvé
    if name_type and name_type_enum:
        return recognizer.find_names_by_type(text, name_type_enum)
    
    # Sinon, extraire tous les noms
    return recognizer.recognize_names(text)


if __name__ == "__main__":
    # Test de la classe avec un exemple de texte
    import argparse
    
    parser = argparse.ArgumentParser(description="Reconnaisseur de noms")
    parser.add_argument("--file", help="Fichier texte à analyser")
    parser.add_argument("--text", help="Texte à analyser directement")
    parser.add_argument("--type", help="Type de nom à rechercher")
    args = parser.parse_args()
    
    # Configurer le logger pour le test
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    recognizer = NameRecognizer()
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
        
        La société ABC Consulting, SARL au capital de 50.000 euros, dont le siège social est situé
        45 Rue du Commerce, 75015, Paris, immatriculée au RCS de Paris sous le numéro 123 456 789,
        représentée par Madame Marie MARTIN en sa qualité de Directrice Générale,
        ci-après dénommée "le Prestataire",
        
        Et
        
        Monsieur Jean DUPONT, né le 15/04/1980 à Paris (75), demeurant 123 Avenue de la République,
        75011 Paris, agissant en qualité de gérant de la société XYZ Solutions SAS,
        ci-après dénommé "le Client",
        
        Il a été convenu ce qui suit :
        
        ...
        
        Pour l'Association des Experts en Informatique, le président Pierre DURAND certifie l'exactitude
        des informations contenues dans ce document.
        
        Fait à Paris, le 10/01/2023
        
        La Mairie de Paris confirme la validité de ce document.
        
        Marie MARTIN                                Jean DUPONT
        """
    
    # Extraction des noms
    name_type_enum = None
    if args.type:
        try:
            name_type_enum = NameType[args.type.upper()]
        except KeyError:
            print(f"Type de nom non reconnu: {args.type}")
            print(f"Types disponibles: {', '.join([t.name for t in NameType])}")
            exit(1)
    
    if name_type_enum:
        names = recognizer.find_names_by_type(sample_text, name_type_enum)
    else:
        names = recognizer.recognize_names(sample_text)
    
    print(f"Noms trouvés: {len(names)}")
    
    # Affichage des résultats
    for i, name_data in enumerate(names):
        print(f"\nNom {i+1}:")
        print(f"Valeur: {name_data['value']}")
        print(f"Type: {name_data['type']}")
        print(f"Score de confiance: {name_data['confidence_score']:.2f}")
        
        if "components" in name_data and name_data["components"]:
            print("Composants:")
            for key, value in name_data["components"].items():
                print(f"  {key}: {value}")
        
        if "metadata" in name_data and name_data["metadata"]:
            print("Métadonnées:")
            for key, value in name_data["metadata"].items():
                print(f"  {key}: {value}")
        
        print(f"Contexte: ...{name_data['context']}...")
        
        # Formatage pour démonstration
        if name_data["type"] == NameType.PERSON.value and "components" in name_data:
            print(f"Format standard: {recognizer.format_name(name_data, 'standard')}")
            print(f"Format formel: {recognizer.format_name(name_data, 'formal')}")
            print(f"Format initiales: {recognizer.format_name(name_data, 'initial')}")
    
    # Affichage des liens personnes-organisations
    if not args.type or args.type.upper() in ["PERSON", "COMPANY", "ORGANIZATION"]:
        print("\n--- Liens personnes-organisations ---")
        links = recognizer.link_persons_to_organizations(sample_text)
        
        for org_name, persons in links.items():
            print(f"\nOrganisation: {org_name}")
            print("Personnes liées:")
            for person in persons:
                person_name = person["value"]
                role = person.get("metadata", {}).get("org_role", "non spécifié")
                print(f"  - {person_name} (rôle: {role})")