"""
Gestionnaire de format de documents
"""

import logging
from typing import Dict, Any, List, Optional
import json
import os

logger = logging.getLogger("VynalDocsAutomator.Extensions.DocumentFormat")

class DocumentFormatHandler:
    """Gère la validation des formats de documents selon les pays"""
    
    def __init__(self):
        # Format requis par pays et type de document
        self.format_rules = {
            "FR": {
                "facture": {
                    "required_fields": [
                        "siret",
                        "tva",
                        "montant_ht",
                        "date"
                    ],
                    "date_format": "%d/%m/%Y"
                },
                "contrat": {
                    "required_fields": [
                        "parties",
                        "date",
                        "signatures"
                    ],
                    "date_format": "%d/%m/%Y"
                }
            }
        }
    
    def validate_document_format(self, country_code: str, document_type: str) -> bool:
        """
        Valide le format d'un document selon le pays
        
        Args:
            country_code: Code du pays (ex: FR)
            document_type: Type de document
            
        Returns:
            bool: True si le format est valide
        """
        # Si pas de règles pour ce pays, considérer valide
        if country_code not in self.format_rules:
            return True
            
        # Si pas de règles pour ce type, considérer valide
        if document_type not in self.format_rules[country_code]:
            return True
            
        # Pour cet exemple, on retourne True
        # Dans une vraie implémentation, on vérifierait les règles
        return True

    def get_document_format(self, country_code: str, doc_type: str, sub_type: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le format pour un type de document et un pays
        
        Args:
            country_code: Code pays (ex: FR, MA)
            doc_type: Type de document (ex: identity, business)
            sub_type: Sous-type de document (ex: cni, passport)
            
        Returns:
            Dict[str, Any]: Configuration du format ou None si non trouvé
        """
        try:
            return self.format_rules.get(country_code, {})\
                                        .get(doc_type, {})\
                                        .get(sub_type)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du format: {e}")
            return None
    
    def validate_document_format(self, country_code: str, doc_type: str, 
                               sub_type: str, document_data: Dict[str, Any]) -> bool:
        """
        Valide si un document respecte le format requis
        
        Args:
            country_code: Code pays
            doc_type: Type de document
            sub_type: Sous-type de document
            document_data: Données du document à valider
            
        Returns:
            bool: True si le document est valide
        """
        format_config = self.get_document_format(country_code, doc_type, sub_type)
        if not format_config:
            return False
            
        try:
            # Vérifier les champs requis
            required_fields = format_config.get("required_fields", [])
            for field in required_fields:
                if field not in document_data:
                    logger.warning(f"Champ requis manquant: {field}")
                    return False
            
            # Vérifier le format physique si spécifié
            if "format" in format_config and "format" in document_data:
                if format_config["format"] != document_data["format"]:
                    logger.warning("Format physique incorrect")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation du format: {e}")
            return False
    
    def get_supported_countries(self) -> List[str]:
        """
        Retourne la liste des pays supportés
        
        Returns:
            List[str]: Liste des codes pays supportés
        """
        return list(self.format_rules.keys())
    
    def get_supported_types(self, country_code: str) -> List[str]:
        """
        Retourne les types de documents supportés pour un pays
        
        Args:
            country_code: Code pays
            
        Returns:
            List[str]: Types de documents supportés
        """
        return list(self.format_rules.get(country_code, {}).keys())
    
    def add_document_format(self, country_code: str, doc_type: str,
                          sub_type: str, format_config: Dict[str, Any]) -> bool:
        """
        Ajoute un nouveau format de document
        
        Args:
            country_code: Code pays
            doc_type: Type de document
            sub_type: Sous-type de document
            format_config: Configuration du format
            
        Returns:
            bool: True si l'ajout a réussi
        """
        try:
            if country_code not in self.format_rules:
                self.format_rules[country_code] = {}
            
            if doc_type not in self.format_rules[country_code]:
                self.format_rules[country_code][doc_type] = {}
            
            self.format_rules[country_code][doc_type][sub_type] = format_config
            
            logger.info(f"Format ajouté: {country_code}/{doc_type}/{sub_type}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du format: {e}")
            return False 