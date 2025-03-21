"""
Validateur de données avancé
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("VynalDocsAutomator.Extensions.DataValidator")

class AdvancedDataValidator:
    """Validateur avancé pour les données extraites"""
    
    def __init__(self):
        self.country_rules = {}
        
        # Règles par défaut pour la France
        self.country_rules["FR"] = {
            "siret": r"^\d{14}$",
            "siren": r"^\d{9}$",
            "tva": r"^FR\d{2}\d{9}$",
            "phone": r"^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$",
            "postal_code": r"^\d{5}$",
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        }
        
        # Règles de validation par type de données
        self._validation_rules = {
            "email": {
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "max_length": 254
            },
            "phone": {
                "patterns": {
                    "FR": r"^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$",
                    "MA": r"^(?:(?:\+|00)212|0)\s*[5-7](?:[\s.-]*\d{2}){4}$"
                }
            },
            "date": {
                "formats": [
                    "%d/%m/%Y",
                    "%Y-%m-%d",
                    "%d-%m-%Y",
                    "%d.%m.%Y"
                ],
                "min_year": 1900,
                "max_year": datetime.now().year + 100
            },
            "amount": {
                "pattern": r"^-?\d+(?:[.,]\d{1,2})?$",
                "min_value": 0,
                "max_value": 1e9
            }
        }
        
        logger.info("Validateur avancé initialisé")
    
    def add_country_rule(self, country_code: str, field: str, pattern: str):
        """
        Ajoute une règle de validation pour un pays
        
        Args:
            country_code: Code du pays (ex: FR)
            field: Nom du champ à valider
            pattern: Pattern regex de validation
        """
        if country_code not in self.country_rules:
            self.country_rules[country_code] = {}
        
        self.country_rules[country_code][field] = pattern
    
    def validate_data(self, data: Dict[str, Any], country_code: str) -> Tuple[bool, List[str]]:
        """
        Valide les données selon les règles du pays
        
        Args:
            data: Données à valider
            country_code: Code du pays
            
        Returns:
            Tuple[bool, List[str]]: (validité, liste des erreurs)
        """
        errors = []
        
        # Si pas de règles pour ce pays, considérer valide
        if country_code not in self.country_rules:
            return True, []
        
        # Valider chaque champ selon les règles
        rules = self.country_rules[country_code]
        for field, pattern in rules.items():
            if field in data:
                value = str(data[field])
                if not re.match(pattern, value):
                    errors.append(f"Format invalide pour {field}: {value}")
        
        return len(errors) == 0, errors
    
    def _detect_field_type(self, field_name: str) -> Optional[str]:
        """
        Détecte le type d'un champ selon son nom
        
        Args:
            field_name: Nom du champ
            
        Returns:
            str: Type détecté ou None
        """
        field_name = field_name.lower()
        
        if "email" in field_name:
            return "email"
        elif any(x in field_name for x in ["phone", "tel", "mobile"]):
            return "phone"
        elif any(x in field_name for x in ["date", "birth", "expiry"]):
            return "date"
        elif any(x in field_name for x in ["amount", "price", "total", "sum"]):
            return "amount"
        
        return None
    
    def _validate_field(self, field: str, value: Any, field_type: str,
                       country_code: str = None) -> Tuple[bool, Optional[str]]:
        """
        Valide un champ selon son type
        
        Args:
            field: Nom du champ
            value: Valeur à valider
            field_type: Type de données
            country_code: Code pays
            
        Returns:
            Tuple[bool, Optional[str]]: (validité, message d'erreur)
        """
        if value is None:
            return False, "Valeur manquante"
        
        try:
            if field_type == "email":
                return self._validate_email(value)
            elif field_type == "phone":
                return self._validate_phone(value, country_code)
            elif field_type == "date":
                return self._validate_date(value)
            elif field_type == "amount":
                return self._validate_amount(value)
            else:
                # Validation spécifique au pays si disponible
                if country_code and field.lower() in self.country_rules.get(country_code, {}):
                    pattern = self.country_rules[country_code][field.lower()]
                    if not re.match(pattern, str(value)):
                        return False, f"Format invalide pour {country_code}"
                    return True, None
            
            return True, None
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation de {field}: {e}")
            return False, str(e)
    
    def _validate_email(self, value: str) -> Tuple[bool, Optional[str]]:
        """Valide une adresse email"""
        if not isinstance(value, str):
            return False, "L'email doit être une chaîne de caractères"
        
        rules = self._validation_rules["email"]
        
        if len(value) > rules["max_length"]:
            return False, f"L'email ne doit pas dépasser {rules['max_length']} caractères"
        
        if not re.match(rules["pattern"], value):
            return False, "Format d'email invalide"
        
        return True, None
    
    def _validate_phone(self, value: str, country_code: str) -> Tuple[bool, Optional[str]]:
        """Valide un numéro de téléphone"""
        if not isinstance(value, str):
            return False, "Le numéro doit être une chaîne de caractères"
        
        # Nettoyer le numéro
        value = re.sub(r'\s+', '', value)
        
        if country_code and country_code in self._validation_rules["phone"]["patterns"]:
            pattern = self._validation_rules["phone"]["patterns"][country_code]
            if not re.match(pattern, value):
                return False, f"Format invalide pour {country_code}"
        else:
            # Validation générique si pas de pays spécifié
            if not re.match(r'^\+?[\d\s-]{8,}$', value):
                return False, "Format de numéro invalide"
        
        return True, None
    
    def _validate_date(self, value: str) -> Tuple[bool, Optional[str]]:
        """Valide une date"""
        if not isinstance(value, str):
            return False, "La date doit être une chaîne de caractères"
        
        rules = self._validation_rules["date"]
        
        # Essayer tous les formats supportés
        parsed_date = None
        for date_format in rules["formats"]:
            try:
                parsed_date = datetime.strptime(value, date_format)
                break
            except ValueError:
                continue
        
        if not parsed_date:
            return False, "Format de date non reconnu"
        
        # Vérifier l'année
        if not rules["min_year"] <= parsed_date.year <= rules["max_year"]:
            return False, f"L'année doit être entre {rules['min_year']} et {rules['max_year']}"
        
        return True, None
    
    def _validate_amount(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Valide un montant"""
        rules = self._validation_rules["amount"]
        
        # Convertir en chaîne si nécessaire
        if isinstance(value, (int, float)):
            value = str(value)
        
        if not isinstance(value, str):
            return False, "Le montant doit être un nombre"
        
        # Nettoyer la valeur
        value = value.replace(" ", "").replace(",", ".")
        
        if not re.match(rules["pattern"], value):
            return False, "Format de montant invalide"
        
        # Convertir en float pour la validation des limites
        try:
            amount = float(value)
            if not rules["min_value"] <= amount <= rules["max_value"]:
                return False, f"Le montant doit être entre {rules['min_value']} et {rules['max_value']}"
        except ValueError:
            return False, "Montant invalide"
        
        return True, None
    
    def add_validation_rule(self, field_type: str, rule_config: Dict[str, Any]) -> bool:
        """
        Ajoute une nouvelle règle de validation
        
        Args:
            field_type: Type de champ
            rule_config: Configuration de la règle
            
        Returns:
            bool: True si l'ajout a réussi
        """
        try:
            self._validation_rules[field_type] = rule_config
            logger.info(f"Règle de validation ajoutée pour {field_type}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la règle: {e}")
            return False 