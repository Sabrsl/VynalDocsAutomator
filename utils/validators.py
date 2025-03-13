#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitaires de validation pour les données extraites des documents
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional, List

def validate_date(date_str: str) -> Optional[str]:
    """
    Valide et formate une date
    
    Args:
        date_str: Chaîne de caractères contenant la date
    
    Returns:
        str: Date formatée (YYYY-MM-DD) ou None si invalide
    """
    try:
        # Essayer différents formats de date courants
        formats = [
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d.%m.%Y"
        ]
        
        for fmt in formats:
            try:
                date = datetime.strptime(date_str.strip(), fmt)
                return date.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        return None
    except Exception:
        return None

def validate_amount(amount_str: str) -> Optional[float]:
    """
    Valide et convertit un montant
    
    Args:
        amount_str: Chaîne de caractères contenant le montant
    
    Returns:
        float: Montant converti ou None si invalide
    """
    try:
        # Nettoyer la chaîne
        clean_str = amount_str.strip()
        
        # Supprimer les symboles de devise et les espaces
        clean_str = re.sub(r'[€$£\s]', '', clean_str)
        
        # Remplacer la virgule par un point
        clean_str = clean_str.replace(',', '.')
        
        # Convertir en float
        amount = float(clean_str)
        
        # Vérifier que le montant est positif
        if amount < 0:
            return None
            
        return round(amount, 2)
    except Exception:
        return None

def validate_name(name_str: str) -> Optional[str]:
    """
    Valide et nettoie un nom
    
    Args:
        name_str: Chaîne de caractères contenant le nom
    
    Returns:
        str: Nom nettoyé ou None si invalide
    """
    try:
        # Nettoyer la chaîne
        clean_str = name_str.strip()
        
        # Vérifier que le nom n'est pas vide
        if not clean_str:
            return None
            
        # Vérifier que le nom ne contient que des lettres, espaces et caractères spéciaux courants
        if not re.match(r'^[a-zA-ZÀ-ÿ\s\-\']+$', clean_str):
            return None
            
        return clean_str
    except Exception:
        return None

def validate_entity(entity_str: str) -> Optional[str]:
    """
    Valide et nettoie un nom d'entité (société, organisation)
    
    Args:
        entity_str: Chaîne de caractères contenant le nom de l'entité
    
    Returns:
        str: Nom d'entité nettoyé ou None si invalide
    """
    try:
        # Nettoyer la chaîne
        clean_str = entity_str.strip()
        
        # Vérifier que le nom n'est pas vide
        if not clean_str:
            return None
            
        # Vérifier que le nom ne contient que des caractères valides
        if not re.match(r'^[a-zA-ZÀ-ÿ0-9\s\-\'\.]+$', clean_str):
            return None
            
        return clean_str
    except Exception:
        return None

def validate_id_number(id_str: str) -> Optional[str]:
    """
    Valide et nettoie un numéro d'identification
    
    Args:
        id_str: Chaîne de caractères contenant le numéro d'identification
    
    Returns:
        str: Numéro d'identification nettoyé ou None si invalide
    """
    try:
        # Nettoyer la chaîne
        clean_str = id_str.strip()
        
        # Vérifier que le numéro n'est pas vide
        if not clean_str:
            return None
            
        # Vérifier que le numéro ne contient que des caractères valides
        if not re.match(r'^[A-Z0-9\-\/]+$', clean_str):
            return None
            
        return clean_str
    except Exception:
        return None

def validate_email(email_str: str) -> Optional[str]:
    """
    Valide et nettoie une adresse email
    
    Args:
        email_str: Chaîne de caractères contenant l'adresse email
    
    Returns:
        str: Adresse email nettoyée ou None si invalide
    """
    try:
        # Nettoyer la chaîne
        clean_str = email_str.strip().lower()
        
        # Vérifier le format de l'email
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', clean_str):
            return None
            
        return clean_str
    except Exception:
        return None

def validate_phone(phone_str: str) -> Optional[str]:
    """
    Valide et nettoie un numéro de téléphone
    
    Args:
        phone_str: Chaîne de caractères contenant le numéro de téléphone
    
    Returns:
        str: Numéro de téléphone nettoyé ou None si invalide
    """
    try:
        # Nettoyer la chaîne
        clean_str = re.sub(r'[^\d+]', '', phone_str.strip())
        
        # Vérifier que le numéro n'est pas vide
        if not clean_str:
            return None
            
        # Vérifier que le numéro commence par + ou 0
        if not clean_str.startswith(('+', '0')):
            return None
            
        # Vérifier la longueur minimale
        if len(clean_str) < 10:
            return None
            
        return clean_str
    except Exception:
        return None

def validate_address(address_str: str) -> Optional[str]:
    """
    Valide et nettoie une adresse
    
    Args:
        address_str: Chaîne de caractères contenant l'adresse
    
    Returns:
        str: Adresse nettoyée ou None si invalide
    """
    try:
        # Nettoyer la chaîne
        clean_str = address_str.strip()
        
        # Vérifier que l'adresse n'est pas vide
        if not clean_str:
            return None
            
        # Vérifier que l'adresse ne contient que des caractères valides
        if not re.match(r'^[a-zA-ZÀ-ÿ0-9\s\-\'\.\,]+$', clean_str):
            return None
            
        return clean_str
    except Exception:
        return None

def validate_siret(siret_str: str) -> Optional[str]:
    """
    Valide et nettoie un numéro SIRET
    
    Args:
        siret_str: Chaîne de caractères contenant le numéro SIRET
    
    Returns:
        str: Numéro SIRET nettoyé ou None si invalide
    """
    try:
        # Nettoyer la chaîne
        clean_str = re.sub(r'[^\d]', '', siret_str.strip())
        
        # Vérifier que le numéro fait 14 chiffres
        if len(clean_str) != 14:
            return None
            
        return clean_str
    except Exception:
        return None

def validate_vat_number(vat_str: str) -> Optional[str]:
    """
    Valide et nettoie un numéro de TVA
    
    Args:
        vat_str: Chaîne de caractères contenant le numéro de TVA
    
    Returns:
        str: Numéro de TVA nettoyé ou None si invalide
    """
    try:
        # Nettoyer la chaîne
        clean_str = vat_str.strip().upper()
        
        # Vérifier le format du numéro de TVA
        if not re.match(r'^[A-Z]{2}[0-9A-Z]{8,12}$', clean_str):
            return None
            
        return clean_str
    except Exception:
        return None

def validate_iban(iban_str: str) -> Optional[str]:
    """
    Valide et nettoie un numéro IBAN
    
    Args:
        iban_str: Chaîne de caractères contenant le numéro IBAN
    
    Returns:
        str: Numéro IBAN nettoyé ou None si invalide
    """
    try:
        # Nettoyer la chaîne
        clean_str = re.sub(r'[^\dA-Z]', '', iban_str.strip().upper())
        
        # Vérifier la longueur minimale
        if len(clean_str) < 15:
            return None
            
        return clean_str
    except Exception:
        return None

def validate_bic(bic_str: str) -> Optional[str]:
    """
    Valide et nettoie un code BIC
    
    Args:
        bic_str: Chaîne de caractères contenant le code BIC
    
    Returns:
        str: Code BIC nettoyé ou None si invalide
    """
    try:
        # Nettoyer la chaîne
        clean_str = bic_str.strip().upper()
        
        # Vérifier le format du code BIC
        if not re.match(r'^[A-Z]{6}[0-9A-Z]{2}([0-9A-Z]{3})?$', clean_str):
            return None
            
        return clean_str
    except Exception:
        return None

def validate_field(field_name: str, field_value: Any) -> Optional[Any]:
    """
    Valide un champ en fonction de son nom
    
    Args:
        field_name: Nom du champ à valider
        field_value: Valeur du champ à valider
    
    Returns:
        Any: Valeur validée ou None si invalide
    """
    validators = {
        'date': validate_date,
        'amount': validate_amount,
        'name': validate_name,
        'entity': validate_entity,
        'id_number': validate_id_number,
        'email': validate_email,
        'phone': validate_phone,
        'address': validate_address,
        'siret': validate_siret,
        'vat_number': validate_vat_number,
        'iban': validate_iban,
        'bic': validate_bic
    }
    
    # Déterminer le type de validation à appliquer
    field_type = None
    if 'date' in field_name.lower():
        field_type = 'date'
    elif any(x in field_name.lower() for x in ['montant', 'amount', 'prix', 'total', 'tva']):
        field_type = 'amount'
    elif 'email' in field_name.lower() or 'mail' in field_name.lower():
        field_type = 'email'
    elif 'phone' in field_name.lower() or 'tel' in field_name.lower():
        field_type = 'phone'
    elif 'address' in field_name.lower() or 'adresse' in field_name.lower():
        field_type = 'address'
    elif 'siret' in field_name.lower():
        field_type = 'siret'
    elif 'tva' in field_name.lower():
        field_type = 'vat_number'
    elif 'iban' in field_name.lower():
        field_type = 'iban'
    elif 'bic' in field_name.lower():
        field_type = 'bic'
    elif 'name' in field_name.lower() or 'nom' in field_name.lower():
        field_type = 'name'
    elif 'company' in field_name.lower() or 'société' in field_name.lower():
        field_type = 'entity'
    elif 'id' in field_name.lower() or 'numéro' in field_name.lower():
        field_type = 'id_number'
    
    # Appliquer la validation appropriée
    if field_type and field_type in validators:
        return validators[field_type](str(field_value))
    
    return field_value

def validate_document_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide toutes les données d'un document
    
    Args:
        data: Dictionnaire contenant les données du document
    
    Returns:
        Dict[str, Any]: Données validées
    """
    validated_data = {}
    
    for field_name, field_value in data.items():
        validated_value = validate_field(field_name, field_value)
        if validated_value is not None:
            validated_data[field_name] = validated_value
    
    return validated_data

def validate_extraction_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide les résultats d'une extraction de données
    
    Args:
        results: Dictionnaire contenant les résultats de l'extraction
    
    Returns:
        Dict[str, Any]: Résultats validés
    """
    validated_results = {}
    
    for field_name, field_value in results.items():
        validated_value = validate_field(field_name, field_value)
        if validated_value is not None:
            validated_results[field_name] = validated_value
    
    return validated_results

def validate_coordinates(coords: Dict[str, float]) -> Optional[Dict[str, float]]:
    """
    Valide des coordonnées (x, y) dans un document
    
    Args:
        coords: Dictionnaire contenant les coordonnées x et y
    
    Returns:
        Dict[str, float]: Coordonnées validées ou None si invalides
    """
    try:
        if not isinstance(coords, dict) or 'x' not in coords or 'y' not in coords:
            return None
            
        x = float(coords['x'])
        y = float(coords['y'])
        
        if x < 0 or y < 0:
            return None
            
        return {'x': x, 'y': y}
    except Exception:
        return None

def validate_merge_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide et fusionne des données de différentes sources
    
    Args:
        data: Dictionnaire contenant les données à fusionner
    
    Returns:
        Dict[str, Any]: Données fusionnées et validées
    """
    merged_data = {}
    
    for field_name, field_value in data.items():
        if isinstance(field_value, list):
            # Si plusieurs valeurs, prendre la première valide
            for value in field_value:
                validated_value = validate_field(field_name, value)
                if validated_value is not None:
                    merged_data[field_name] = validated_value
                    break
        else:
            # Si une seule valeur, la valider directement
            validated_value = validate_field(field_name, field_value)
            if validated_value is not None:
                merged_data[field_name] = validated_value
    
    return merged_data

def check_data_consistency(data: Dict[str, Any]) -> List[str]:
    """
    Vérifie la cohérence des données extraites
    
    Args:
        data: Dictionnaire contenant les données à vérifier
    
    Returns:
        List[str]: Liste des incohérences trouvées
    """
    inconsistencies = []
    
    # Vérifier la cohérence des dates
    if 'date' in data and 'due_date' in data:
        date = validate_date(data['date'])
        due_date = validate_date(data['due_date'])
        if date and due_date and due_date < date:
            inconsistencies.append("La date d'échéance est antérieure à la date du document")
    
    # Vérifier la cohérence des montants
    if 'amount' in data and 'vat_amount' in data:
        amount = validate_amount(data['amount'])
        vat_amount = validate_amount(data['vat_amount'])
        if amount and vat_amount and vat_amount > amount:
            inconsistencies.append("Le montant de TVA est supérieur au montant total")
    
    # Vérifier la cohérence des coordonnées client
    if 'client_email' in data and 'client_phone' in data:
        email = validate_email(data['client_email'])
        phone = validate_phone(data['client_phone'])
        if not email and not phone:
            inconsistencies.append("Aucun moyen de contact valide pour le client")
    
    return inconsistencies 