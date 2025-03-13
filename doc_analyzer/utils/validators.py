#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de validation pour Vynal Docs Automator
Fournit des fonctions pour valider les données extraites des documents
et s'assurer qu'elles sont conformes aux formats attendus.
"""

import re
import datetime
import logging
from typing import Dict, Any, Optional, Union, List, Tuple

# Configuration du logger
logger = logging.getLogger("Vynal Docs Automator.doc_analyzer.utils.validators")

def validate_date(date_str: str) -> Optional[str]:
    """
    Valide et normalise une chaîne de date au format ISO (YYYY-MM-DD).
    
    Args:
        date_str (str): Chaîne contenant une date à valider
        
    Returns:
        str: Date normalisée au format ISO ou None si invalide
    """
    if not date_str:
        return None
    
    # Nettoyage de la chaîne
    date_str = date_str.strip()
    
    # Patterns de dates courants
    date_patterns = [
        # JJ/MM/AAAA ou JJ-MM-AAAA
        (r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})', lambda d, m, y: f"{y}-{m.zfill(2)}-{d.zfill(2)}"),
        # JJ/MM/AA ou JJ-MM-AA
        (r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{2})', lambda d, m, y: f"20{y}-{m.zfill(2)}-{d.zfill(2)}" 
         if int(y) < 50 else f"19{y}-{m.zfill(2)}-{d.zfill(2)}"),
        # AAAA/MM/JJ ou AAAA-MM-JJ (format ISO)
        (r'(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})', lambda y, m, d: f"{y}-{m.zfill(2)}-{d.zfill(2)}")
    ]
    
    # Essayer chaque pattern
    for pattern, formatter in date_patterns:
        match = re.match(pattern, date_str)
        if match:
            try:
                # Appliquer le formateur avec les groupes capturés
                iso_date = formatter(*match.groups())
                
                # Vérifier que la date est valide
                year, month, day = map(int, iso_date.split('-'))
                datetime.date(year, month, day)  # Lève ValueError si date invalide
                
                return iso_date
            except (ValueError, TypeError) as e:
                logger.debug(f"Date invalide ({date_str}): {e}")
                continue
    
    # Si aucun pattern ne correspond, essayer de parser avec datetime
    for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"]:
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    logger.warning(f"Format de date non reconnu: {date_str}")
    return None


def validate_amount(amount_str: str) -> Optional[float]:
    """
    Valide et normalise un montant financier.
    
    Args:
        amount_str (str): Chaîne contenant un montant à valider
        
    Returns:
        float: Montant normalisé ou None si invalide
    """
    if not amount_str:
        return None
    
    # Nettoyage de la chaîne
    amount_str = amount_str.strip()
    
    # Supprimer les espaces et caractères non numériques sauf . et ,
    cleaned = re.sub(r'[^\d.,]', '', amount_str)
    
    # Convertir la virgule en point (standard décimal)
    cleaned = cleaned.replace(',', '.')
    
    # Gérer les cas avec plusieurs points (prendre le dernier comme décimal)
    if cleaned.count('.') > 1:
        parts = cleaned.split('.')
        cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
    
    try:
        amount = float(cleaned)
        
        # Vérifier que le montant est dans une plage raisonnable
        if amount < 0:
            logger.warning(f"Montant négatif détecté: {amount}")
            return None
        
        if amount > 1e10:  # 10 milliards
            logger.warning(f"Montant suspicieusement élevé: {amount}")
            # On peut quand même le retourner, c'est juste un avertissement
        
        return amount
    except ValueError:
        logger.warning(f"Format de montant non reconnu: {amount_str}")
        return None


def validate_name(name_str: str) -> Optional[str]:
    """
    Valide et normalise un nom de personne.
    
    Args:
        name_str (str): Chaîne contenant un nom à valider
        
    Returns:
        str: Nom normalisé ou None si invalide
    """
    if not name_str:
        return None
    
    # Nettoyage de la chaîne
    name_str = name_str.strip()
    
    # Supprimer les titres courants
    titles = [
        r'^M\.', r'^Mme\.', r'^Mlle\.', r'^Dr\.', r'^Pr\.', 
        r'^Monsieur\s+', r'^Madame\s+', r'^Mademoiselle\s+',
        r'^Docteur\s+', r'^Professeur\s+'
    ]
    
    for title in titles:
        name_str = re.sub(title, '', name_str, flags=re.IGNORECASE)
    
    # Vérifier que le nom n'est pas trop court
    if len(name_str) < 2:
        logger.warning(f"Nom trop court: {name_str}")
        return None
    
    # Vérifier qu'il ne contient pas trop de chiffres ou symboles
    if re.search(r'[\d\W]{3,}', name_str):
        logger.warning(f"Le nom contient trop de chiffres ou symboles: {name_str}")
        return None
    
    # Normaliser la casse (chaque mot commence par une majuscule)
    normalized = ' '.join(word.capitalize() for word in name_str.split())
    
    # Cas spécial pour les noms composés avec trait d'union
    normalized = re.sub(r'(\w+)-(\w+)', lambda m: f"{m.group(1).capitalize()}-{m.group(2).capitalize()}", normalized)
    
    # Cas spécial pour les préfixes de noms (exemple: "de", "van", "von", "el")
    prefixes = ['de', 'du', 'des', 'von', 'van', 'el', 'al', 'ben', 'ibn', 'da', 'di', 'le', 'la']
    for prefix in prefixes:
        normalized = re.sub(rf'\s{prefix}\s+(\w)', lambda m: f" {prefix} {m.group(1).upper()}", normalized, flags=re.IGNORECASE)
    
    return normalized


def validate_entity(entity_str: str) -> Optional[str]:
    """
    Valide et normalise un nom d'entité (personne ou organisation).
    
    Args:
        entity_str (str): Chaîne contenant un nom d'entité à valider
        
    Returns:
        str: Entité normalisée ou None si invalide
    """
    if not entity_str:
        return None
    
    # Nettoyage de la chaîne
    entity_str = entity_str.strip()
    
    # Vérifier que l'entité n'est pas trop courte
    if len(entity_str) < 2:
        logger.warning(f"Nom d'entité trop court: {entity_str}")
        return None
    
    # Normaliser la casse
    if entity_str.isupper() and len(entity_str) > 3:
        # Si tout en majuscules, convertir en title case
        normalized = ' '.join(word.capitalize() for word in entity_str.lower().split())
    else:
        # Sinon, garder la casse originale
        normalized = entity_str
    
    # Remplacer les caractères de formatage superflus
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = normalized.replace('_', ' ').replace('/', ' / ')
    
    return normalized


def validate_id_number(id_str: str, doc_type: str = None, country: str = None) -> Optional[str]:
    """
    Valide un numéro d'identification selon son type et son pays d'origine.
    
    Args:
        id_str (str): Chaîne contenant un numéro à valider
        doc_type (str, optional): Type de document d'identité
        country (str, optional): Code pays
        
    Returns:
        str: Numéro normalisé ou None si invalide
    """
    if not id_str:
        return None
    
    # Nettoyage de la chaîne
    id_str = re.sub(r'\s', '', id_str).upper()
    
    # Validation selon le type et le pays
    if doc_type == "cni":
        if country == "fr":
            # CNI française: 12 chiffres
            if re.match(r'^\d{12}$', id_str):
                return id_str
        elif country == "ma":
            # CNI marocaine: 1-2 lettres suivies de 5-6 chiffres
            if re.match(r'^[A-Z]{1,2}\d{5,6}$', id_str):
                return id_str
        elif country == "sn":
            # CNI sénégalaise: 13 chiffres ou format numérique avec espaces
            if re.match(r'^\d{13}$', id_str):
                return id_str
        elif country == "ci":
            # CNI ivoirienne: C + 9 chiffres
            if re.match(r'^C\d{9}$', id_str):
                return id_str
    
    elif doc_type == "passport":
        if country == "fr":
            # Passeport français: 9 caractères (2 chiffres, 2 lettres, 5 chiffres)
            if re.match(r'^\d{2}[A-Z]{2}\d{5}$', id_str):
                return id_str
        elif country in ["ma", "sn", "ci", "cm", "dz", "tn"]:
            # Passeport standard: lettre(s) + chiffres
            if re.match(r'^[A-Z]{1,2}\d{6,7}$', id_str):
                return id_str
    
    elif doc_type == "tax_id":
        if country == "fr":
            # Numéro fiscal français: 13 chiffres
            if re.match(r'^\d{13}$', id_str):
                return id_str
        elif country == "ma":
            # Identifiant fiscal marocain
            if re.match(r'^\d{7,10}$', id_str):
                return id_str
    
    # SIRET/SIREN français
    if id_str.isdigit() and len(id_str) in [9, 14]:
        if len(id_str) == 9:  # SIREN
            return id_str
        elif len(id_str) == 14:  # SIRET
            return id_str
    
    # Si aucune validation spécifique n'est possible, retourner tel quel
    logger.debug(f"Aucune validation spécifique pour: {id_str} (type={doc_type}, pays={country})")
    return id_str


def validate_email(email_str: str) -> Optional[str]:
    """
    Valide une adresse email.
    
    Args:
        email_str (str): Chaîne contenant une adresse email à valider
        
    Returns:
        str: Email normalisé ou None si invalide
    """
    if not email_str:
        return None
    
    # Nettoyage de la chaîne
    email_str = email_str.strip().lower()
    
    # Validation avec regex (simple)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, email_str):
        return email_str
    
    logger.warning(f"Format d'email invalide: {email_str}")
    return None


def validate_phone(phone_str: str, country_code: str = None) -> Optional[str]:
    """
    Valide et normalise un numéro de téléphone au format international.
    
    Args:
        phone_str (str): Chaîne contenant un numéro à valider
        country_code (str, optional): Code pays pour le formatage (fr, ma, etc.)
        
    Returns:
        str: Numéro de téléphone normalisé ou None si invalide
    """
    if not phone_str:
        return None
    
    # Nettoyage de la chaîne (supprimer les caractères non numériques sauf +)
    cleaned = re.sub(r'[^\d+]', '', phone_str)
    
    # Si le pays est spécifié, adapter la validation
    if country_code:
        country_code = country_code.lower()
        
        # France
        if country_code == 'fr':
            # Format national (0X XX XX XX XX) -> international (+33 X XX XX XX XX)
            if cleaned.startswith('0') and len(cleaned) == 10:
                return '+33' + cleaned[1:]
            # Format international déjà
            elif cleaned.startswith('+33') and len(cleaned) == 12:
                return cleaned
        
        # Maroc
        elif country_code == 'ma':
            # Format national (0X XX XX XX XX) -> international (+212 X XX XX XX XX)
            if cleaned.startswith('0') and len(cleaned) == 10:
                return '+212' + cleaned[1:]
            # Format international déjà
            elif cleaned.startswith('+212') and len(cleaned) in [13, 14]:
                return cleaned
        
        # Autres pays africains (exemples)
        elif country_code == 'sn':  # Sénégal
            if cleaned.startswith('0') and len(cleaned) == 9:
                return '+221' + cleaned[1:]
            elif cleaned.startswith('+221'):
                return cleaned
        
        elif country_code == 'ci':  # Côte d'Ivoire
            if cleaned.startswith('0') and len(cleaned) == 10:
                return '+225' + cleaned[1:]
            elif cleaned.startswith('+225'):
                return cleaned
    
    # Si aucune validation spécifique au pays n'est possible
    # Format international générique
    if cleaned.startswith('+') and len(cleaned) >= 10:
        return cleaned
    
    # Format national générique (convertir en international)
    if cleaned.startswith('0') and len(cleaned) >= 9:
        # Par défaut, considérer comme français si non spécifié
        prefix = '+33'
        if country_code == 'ma':
            prefix = '+212'
        elif country_code == 'sn':
            prefix = '+221'
        elif country_code == 'ci':
            prefix = '+225'
        
        return prefix + cleaned[1:]
    
    logger.warning(f"Format de téléphone non reconnu: {phone_str}")
    return None


def validate_address(address_str: str) -> Optional[str]:
    """
    Valide et normalise une adresse postale.
    
    Args:
        address_str (str): Chaîne contenant une adresse à valider
        
    Returns:
        str: Adresse normalisée ou None si invalide
    """
    if not address_str:
        return None
    
    # Nettoyage de la chaîne
    address_str = address_str.strip()
    
    # Vérifier que l'adresse n'est pas trop courte
    if len(address_str) < 10:
        logger.warning(f"Adresse trop courte: {address_str}")
        return None
    
    # Normaliser les retours à la ligne
    normalized = re.sub(r'\s*[\r\n]+\s*', ', ', address_str)
    
    # Normaliser les espaces multiples
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Vérifier la présence d'un code postal
    has_postal_code = bool(re.search(r'\b\d{4,5}\b', normalized))
    
    if not has_postal_code:
        logger.debug(f"Pas de code postal détecté dans l'adresse: {normalized}")
        # On peut quand même retourner l'adresse, c'est juste un avertissement
    
    return normalized


def validate_siret(siret_str: str) -> Optional[str]:
    """
    Valide un numéro SIRET français avec l'algorithme de Luhn.
    
    Args:
        siret_str (str): Chaîne contenant un SIRET à valider
        
    Returns:
        str: SIRET normalisé ou None si invalide
    """
    if not siret_str:
        return None
    
    # Nettoyage de la chaîne
    cleaned = re.sub(r'\s', '', siret_str)
    
    # Vérifier le format
    if not re.match(r'^\d{14}$', cleaned):
        logger.warning(f"Format SIRET invalide: {siret_str}")
        return None
    
    # Algorithme de Luhn pour la validation
    total = 0
    for i, digit in enumerate(cleaned):
        n = int(digit)
        # Pour les positions paires, multiplier par 2
        if i % 2 == 0:
            n = n * 2
            if n > 9:
                n = n - 9
        total += n
    
    # Si le total est divisible par 10, le SIRET est valide
    if total % 10 == 0:
        return cleaned
    else:
        logger.warning(f"SIRET invalide (échec de l'algorithme de Luhn): {siret_str}")
        return None


def validate_vat_number(vat_str: str, country_code: str = None) -> Optional[str]:
    """
    Valide un numéro de TVA intracommunautaire.
    
    Args:
        vat_str (str): Chaîne contenant un numéro de TVA à valider
        country_code (str, optional): Code pays pour validation spécifique
        
    Returns:
        str: Numéro de TVA normalisé ou None si invalide
    """
    if not vat_str:
        return None
    
    # Nettoyage de la chaîne
    cleaned = re.sub(r'\s', '', vat_str).upper()
    
    # Format standard: 2 lettres (code pays) suivies de chiffres/lettres
    vat_pattern = r'^[A-Z]{2}[0-9A-Z]{2,12}$'
    if not re.match(vat_pattern, cleaned):
        logger.warning(f"Format TVA intracommunautaire invalide: {vat_str}")
        return None
    
    # Vérification spécifique par pays
    country = cleaned[:2]
    number = cleaned[2:]
    
    # France (FR + SIREN)
    if country == 'FR':
        if not re.match(r'^\d{11}$', number) and not re.match(r'^[A-Z0-9]{2}\d{9}$', number):
            logger.warning(f"Format TVA française invalide: {vat_str}")
            return None
    
    # D'autres validations spécifiques pourraient être ajoutées ici
    
    return cleaned


def validate_iban(iban_str: str) -> Optional[str]:
    """
    Valide un IBAN (International Bank Account Number).
    
    Args:
        iban_str (str): Chaîne contenant un IBAN à valider
        
    Returns:
        str: IBAN normalisé ou None si invalide
    """
    if not iban_str:
        return None
    
    # Nettoyage de la chaîne
    cleaned = re.sub(r'\s', '', iban_str).upper()
    
    # Format de base: code pays (2 lettres) + chiffre de contrôle (2 chiffres) + BBAN
    iban_pattern = r'^[A-Z]{2}\d{2}[A-Z0-9]{4,30}$'
    if not re.match(iban_pattern, cleaned):
        logger.warning(f"Format IBAN invalide: {iban_str}")
        return None
    
    # Validation plus avancée (algorithme mod-97)
    # Mettre les 4 premiers caractères à la fin
    rearranged = cleaned[4:] + cleaned[:4]
    
    # Convertir les lettres en chiffres (A=10, B=11, ..., Z=35)
    numerical = ''
    for char in rearranged:
        if char.isalpha():
            numerical += str(ord(char) - ord('A') + 10)
        else:
            numerical += char
    
    # Vérifier mod-97
    if int(numerical) % 97 != 1:
        logger.warning(f"IBAN invalide (échec de l'algorithme mod-97): {iban_str}")
        return None
    
    return cleaned


def validate_bic(bic_str: str) -> Optional[str]:
    """
    Valide un code BIC/SWIFT bancaire.
    
    Args:
        bic_str (str): Chaîne contenant un BIC à valider
        
    Returns:
        str: BIC normalisé ou None si invalide
    """
    if not bic_str:
        return None
    
    # Nettoyage de la chaîne
    cleaned = re.sub(r'\s', '', bic_str).upper()
    
    # Format: 4 lettres (code banque) + 2 lettres (code pays) + 2 caractères (code lieu)
    # + 3 caractères optionnels (code branche)
    bic_pattern = r'^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?$'
    if re.match(bic_pattern, cleaned):
        return cleaned
    
    logger.warning(f"Format BIC invalide: {bic_str}")
    return None


def validate_field(field_value: Any, field_type: str, **kwargs) -> Tuple[Any, bool]:
    """
    Valide un champ selon son type et retourne sa valeur normalisée et un indicateur de validité.
    
    Args:
        field_value: Valeur à valider
        field_type: Type de champ ('name', 'email', 'phone', etc.)
        **kwargs: Arguments supplémentaires spécifiques au type de champ
    
    Returns:
        tuple: (valeur normalisée, indicateur de validité)
    """
    if field_value is None:
        return None, False
    
    # Convertir en chaîne si nécessaire
    if not isinstance(field_value, str):
        field_value = str(field_value)
    
    # Sélectionner la méthode de validation appropriée
    validators = {
        'name': validate_name,
        'entity': validate_entity,
        'date': validate_date,
        'amount': validate_amount,
        'id_number': validate_id_number,
        'email': validate_email,
        'phone': validate_phone,
        'address': validate_address,
        'siret': validate_siret,
        'vat_number': validate_vat_number,
        'iban': validate_iban,
        'bic': validate_bic
    }
    
    # Fonction de validation par défaut (retourne la valeur telle quelle)
    default_validator = lambda x, **kw: x.strip() if isinstance(x, str) else x
    
    # Obtenir la fonction de validation appropriée
    validator = validators.get(field_type, default_validator)
    
    # Appliquer la validation
    validated = validator(field_value, **kwargs)
    
    # Retourner la valeur validée et un booléen indiquant si la validation a réussi
    return validated, validated is not None


def validate_document_data(data: Dict[str, Any], doc_type: str = None) -> Dict[str, Any]:
    """
    Valide l'ensemble des données extraites d'un document.
    
    Args:
        data (dict): Données à valider
        doc_type (str, optional): Type de document pour validation spécifique
        
    Returns:
        dict: Données validées et normalisées
    """
    if not data:
        return {}
    
    validated = {}
    
    # Valider les champs de premier niveau
    for key, value in data.items():
        if key in ['id', 'type', 'source', 'format', 'language']:
            validated[key] = value
    
    # Valider les informations personnelles
    if 'personal_info' in data and isinstance(data['personal_info'], dict):
        validated['personal_info'] = {}
        personal_info = data['personal_info']
        
        field_types = {
            'last_name': 'name',
            'first_name': 'name',
            'birth_date': 'date',
            'birth_place': 'entity',
            'gender': lambda x: x.upper() if x in ['M', 'F'] else None,
            'nationality': 'entity',
            'email': 'email',
            'phone': 'phone',
            'address': 'address'
        }
        
        for field, value in personal_info.items():
            if field in field_types:
                validator = field_types[field]
                if callable(validator):
                    validated_value = validator(value)
                else:
                    validated_value, _ = validate_field(value, validator)
                if validated_value is not None:
                    validated['personal_info'][field] = validated_value
    
    # Valider les informations professionnelles
    if 'professional_info' in data and isinstance(data['professional_info'], dict):
        validated['professional_info'] = {}
        prof_info = data['professional_info']
        
        field_types = {
            'company': 'entity',
            'position': lambda x: x.strip().title() if x else None,
            'siret': 'siret',
            'vat_number': 'vat_number',
            'company_address': 'address',
            'professional_email': 'email',
            'professional_phone': 'phone'
        }
        
        for field, value in prof_info.items():
            if field in field_types:
                validator = field_types[field]
                if callable(validator):
                    validated_value = validator(value)
                else:
                    validated_value, _ = validate_field(value, validator)
                if validated_value is not None:
                    validated['professional_info'][field] = validated_value
    
    # Valider les informations bancaires
    if 'banking_info' in data and isinstance(data['banking_info'], dict):
        validated['banking_info'] = {}
        banking_info = data['banking_info']
        
        field_types = {
            'iban': 'iban',
            'bic': 'bic',
            'bank_name': 'entity',
            'account_number': lambda x: re.sub(r'\s', '', x) if x else None
        }
        
        for field, value in banking_info.items():
            if field in field_types:
                validator = field_types[field]
                if callable(validator):
                    validated_value = validator(value)
                else:
                    validated_value, _ = validate_field(value, validator)
                if validated_value is not None:
                    validated['banking_info'][field] = validated_value
    
    # Valider les montants financiers
    if 'amounts' in data and isinstance(data['amounts'], dict):
        validated['amounts'] = {}
        amounts = data['amounts']
        
        for field, value in amounts.items():
            validated_value, _ = validate_field(value, 'amount')
            if validated_value is not None:
                validated['amounts'][field] = validated_value
    
    # Valider les dates
    if 'dates' in data and isinstance(data['dates'], dict):
        validated['dates'] = {}
        dates = data['dates']
        
        for field, value in dates.items():
            if field.endswith('_date'):
                validated_value, _ = validate_field(value, 'date')
                if validated_value is not None:
                    validated['dates'][field] = validated_value
            else:
                validated['dates'][field] = value
    
    # Traitement spécifique selon le type de document
    if doc_type:
        # Validation spécifique pour les contrats
        if doc_type == 'contract':
            pass  # Ajouter des validations spécifiques aux contrats si nécessaire
        
        # Validation spécifique pour les factures
        elif doc_type == 'invoice':
            pass  # Ajouter des validations spécifiques aux factures si nécessaire
        
        # Validation spécifique pour les documents d'identité
        elif doc_type in ['id_card', 'passport', 'residence_permit']:
            # Vérifier la cohérence des dates
            if 'dates' in validated and 'issue_date' in validated['dates'] and 'expiry_date' in validated['dates']:
                issue = validated['dates']['issue_date']
                expiry = validated['dates']['expiry_date']
                
                if issue and expiry:
                    try:
                        issue_date = datetime.datetime.strptime(issue, "%Y-%m-%d")
                        expiry_date = datetime.datetime.strptime(expiry, "%Y-%m-%d")
                        
                        # Vérifier que la date d'expiration est postérieure à la date d'émission
                        if expiry_date <= issue_date:
                            logger.warning(f"Date d'expiration ({expiry}) antérieure à la date d'émission ({issue})")
                            validated['dates']['expiry_date'] = None
                    except ValueError:
                        pass
    
    return validated


def validate_extraction_results(extraction_results: Dict[str, Any], confidence_threshold: float = 0.5) -> Dict[str, Any]:
    """
    Valide les résultats d'extraction, en filtrant les résultats selon le seuil de confiance.
    
    Args:
        extraction_results (dict): Résultats d'extraction avec scores de confiance
        confidence_threshold (float): Seuil de confiance minimum pour accepter un résultat
        
    Returns:
        dict: Résultats validés
    """
    if not extraction_results or 'data' not in extraction_results:
        return {}
    
    validated = {
        'data': {},
        'metadata': extraction_results.get('metadata', {})
    }
    
    data = extraction_results['data']
    confidence_scores = extraction_results.get('confidence', {})
    
    # Valider chaque section des données
    for section, section_data in data.items():
        if not section_data:
            continue
        
        # Vérifier si la section a un score de confiance
        section_confidence = confidence_scores.get(section, 1.0)  # Par défaut, considérer comme confiant
        
        # Si le score de confiance est suffisant
        if section_confidence >= confidence_threshold:
            # Valider selon le type de section
            if section == 'personal_info':
                validated['data'][section] = {}
                for field, value in section_data.items():
                    field_confidence = confidence_scores.get(f"{section}.{field}", section_confidence)
                    if field_confidence >= confidence_threshold:
                        validated_value, is_valid = validate_field(value, field)
                        if is_valid:
                            validated['data'][section][field] = validated_value
            
            elif section == 'amounts':
                validated['data'][section] = {}
                for field, value in section_data.items():
                    field_confidence = confidence_scores.get(f"{section}.{field}", section_confidence)
                    if field_confidence >= confidence_threshold:
                        validated_value = validate_amount(value)
                        if validated_value is not None:
                            validated['data'][section][field] = validated_value
            
            elif section == 'dates':
                validated['data'][section] = {}
                for field, value in section_data.items():
                    field_confidence = confidence_scores.get(f"{section}.{field}", section_confidence)
                    if field_confidence >= confidence_threshold:
                        validated_value = validate_date(value)
                        if validated_value is not None:
                            validated['data'][section][field] = validated_value
            
            else:
                # Pour les autres sections, copier les données après validation générique
                validated['data'][section] = {}
                for field, value in section_data.items():
                    field_confidence = confidence_scores.get(f"{section}.{field}", section_confidence)
                    if field_confidence >= confidence_threshold:
                        if isinstance(value, str):
                            validated_value = value.strip()
                            if validated_value:
                                validated['data'][section][field] = validated_value
                        else:
                            validated['data'][section][field] = value
    
    # Ajouter les méta-informations sur la validation
    validated['validation'] = {
        'timestamp': datetime.datetime.now().isoformat(),
        'threshold_used': confidence_threshold,
        'fields_total': count_fields(data),
        'fields_validated': count_fields(validated['data'])
    }
    
    return validated


def count_fields(data: Dict[str, Any]) -> int:
    """
    Compte le nombre total de champs dans les données.
    
    Args:
        data (dict): Données à analyser
        
    Returns:
        int: Nombre total de champs
    """
    count = 0
    
    if not data:
        return count
    
    for section, section_data in data.items():
        if isinstance(section_data, dict):
            count += len(section_data)
        elif isinstance(section_data, list):
            count += len(section_data)
        else:
            count += 1
    
    return count


def validate_coordinates(x: Union[int, float], y: Union[int, float], 
                        max_x: int, max_y: int) -> Tuple[int, int]:
    """
    Valide les coordonnées dans une image ou un document.
    
    Args:
        x (int/float): Coordonnée X à valider
        y (int/float): Coordonnée Y à valider
        max_x (int): Valeur maximale pour X
        max_y (int): Valeur maximale pour Y
        
    Returns:
        tuple: Coordonnées validées (x, y)
    """
    try:
        x_val = int(float(x))
        y_val = int(float(y))
        
        # S'assurer que les coordonnées sont dans les limites
        x_val = max(0, min(x_val, max_x))
        y_val = max(0, min(y_val, max_y))
        
        return x_val, y_val
    except (ValueError, TypeError):
        return 0, 0


def validate_merge_data(form_data: Dict[str, Any], extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide et fusionne les données de formulaire avec les données extraites.
    
    Args:
        form_data (dict): Données saisies dans le formulaire
        extracted_data (dict): Données extraites automatiquement
        
    Returns:
        dict: Données fusionnées et validées
    """
    merged = {}
    
    # Copier d'abord les données de formulaire (prioritaires)
    for key, value in form_data.items():
        if isinstance(value, str):
            cleaned_value = value.strip()
            if cleaned_value:
                merged[key] = cleaned_value
        elif value is not None:
            merged[key] = value
    
    # Ajouter les données extraites seulement si le champ n'existe pas déjà
    for key, value in extracted_data.items():
        if key not in merged:
            if isinstance(value, str):
                cleaned_value = value.strip()
                if cleaned_value:
                    merged[key] = cleaned_value
            elif value is not None:
                merged[key] = value
    
    # Validation spécifique des champs importants
    field_types = {
        'nom': 'name',
        'prenom': 'name',
        'nom_societe': 'entity',
        'email': 'email',
        'telephone': 'phone',
        'adresse': 'address',
        'code_postal': lambda x: x.strip() if re.match(r'^\d{4,5}$', x.strip()) else None,
        'ville': 'entity',
        'date_naissance': 'date',
        'siret': 'siret',
        'iban': 'iban',
        'montant': 'amount',
        'date_document': 'date'
    }
    
    # Valider chaque champ selon son type
    validated = {}
    for key, value in merged.items():
        field_type = field_types.get(key)
        if field_type:
            if callable(field_type):
                validated_value = field_type(value)
            else:
                validated_value, _ = validate_field(value, field_type)
            
            if validated_value is not None:
                validated[key] = validated_value
        else:
            validated[key] = value
    
    return validated


def check_data_consistency(data: Dict[str, Any]) -> List[str]:
    """
    Vérifie la cohérence des données et retourne une liste d'avertissements.
    
    Args:
        data (dict): Données à vérifier
        
    Returns:
        list: Liste des avertissements
    """
    warnings = []
    
    # Vérifier la cohérence des montants
    if 'amounts' in data and isinstance(data['amounts'], dict):
        amounts = data['amounts']
        
        # Vérifier HT + TVA = TTC
        if 'montant_ht' in amounts and 'tva' in amounts and 'montant_ttc' in amounts:
            try:
                ht = float(amounts['montant_ht'])
                tva = float(amounts['tva'])
                ttc = float(amounts['montant_ttc'])
                
                # Tolérance de 0.1 euro pour les erreurs d'arrondi
                if abs((ht + tva) - ttc) > 0.1:
                    warnings.append(f"Incohérence de montants: HT ({ht}) + TVA ({tva}) ≠ TTC ({ttc})")
            except (ValueError, TypeError):
                warnings.append("Impossible de vérifier la cohérence des montants (valeurs non numériques)")
    
    # Vérifier la cohérence des dates
    if 'dates' in data and isinstance(data['dates'], dict):
        dates = data['dates']
        
        # Vérifier date_debut < date_fin
        if 'date_debut' in dates and 'date_fin' in dates:
            date_debut = dates['date_debut']
            date_fin = dates['date_fin']
            
            if date_debut and date_fin:
                try:
                    debut = datetime.datetime.strptime(date_debut, "%Y-%m-%d")
                    fin = datetime.datetime.strptime(date_fin, "%Y-%m-%d")
                    
                    if debut >= fin:
                        warnings.append(f"Date de début ({date_debut}) postérieure ou égale à la date de fin ({date_fin})")
                except ValueError:
                    warnings.append("Impossible de vérifier la cohérence des dates (format invalide)")
    
    # Vérifier l'âge si date de naissance présente
    if 'personal_info' in data and isinstance(data['personal_info'], dict):
        if 'birth_date' in data['personal_info']:
            birth_date = data['personal_info']['birth_date']
            
            if birth_date:
                try:
                    birth = datetime.datetime.strptime(birth_date, "%Y-%m-%d")
                    now = datetime.datetime.now()
                    age = now.year - birth.year - ((now.month, now.day) < (birth.month, birth.day))
                    
                    if age < 0:
                        warnings.append(f"Date de naissance dans le futur: {birth_date}")
                    elif age > 120:
                        warnings.append(f"Âge improbable ({age} ans): {birth_date}")
                except ValueError:
                    warnings.append("Impossible de vérifier l'âge (format de date invalide)")
    
    return warnings