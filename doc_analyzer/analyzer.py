#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Analyseur de documents pour l'extraction automatique de données
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .utils.text_processor import TextProcessor
from .utils.validators import (
    validate_document_data,
    validate_extraction_results,
    check_data_consistency
)

logger = logging.getLogger("VynalDocsAutomator.DocumentAnalyzer")

class DocumentAnalyzer:
    """
    Classe principale pour l'analyse des documents
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise l'analyseur de documents
        
        Args:
            config_path: Chemin vers le fichier de configuration (optionnel)
        """
        self.text_processor = TextProcessor()
        self.config = self._load_config(config_path)
        
        logger.info("DocumentAnalyzer initialisé")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Charge la configuration
        
        Args:
            config_path: Chemin vers le fichier de configuration
        
        Returns:
            Dict[str, Any]: Configuration chargée
        """
        # TODO: Implémenter le chargement de la configuration
        return {
            'auto_fill': {
                'enabled': True,
                'confidence_threshold': 0.8,
                'auto_validate': True,
                'show_preview': True,
                'max_fields': 50
            }
        }
    
    def analyze_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Analyse un document pour en extraire les données
        
        Args:
            file_path: Chemin vers le fichier du document
        
        Returns:
            Dict[str, Any]: Données extraites ou None en cas d'erreur
        """
        try:
            # Vérifier que le fichier existe
            if not os.path.exists(file_path):
                logger.error(f"Fichier non trouvé: {file_path}")
                return None
            
            # Lire le contenu du fichier
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Analyser le texte
            analysis_results = self.text_processor.analyze_text(text)
            
            # Valider les résultats
            validated_results = validate_extraction_results(analysis_results['fields'])
            
            # Vérifier la cohérence des données
            inconsistencies = check_data_consistency(validated_results)
            if inconsistencies:
                logger.warning(f"Incohérences trouvées: {inconsistencies}")
            
            # Organiser les résultats
            results = {
                'file_path': file_path,
                'timestamp': datetime.now().isoformat(),
                'data': validated_results,
                'metadata': analysis_results['metadata'],
                'inconsistencies': inconsistencies
            }
            
            logger.info(f"Document analysé avec succès: {file_path}")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du document: {e}")
            return None
    
    def extract_fields(self, file_path: str) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """
        Extrait les champs d'un document
        
        Args:
            file_path: Chemin vers le fichier du document
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Champs extraits ou None en cas d'erreur
        """
        try:
            # Analyser le document
            results = self.analyze_document(file_path)
            if not results:
                return None
            
            return results['data']
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des champs: {e}")
            return None
    
    def validate_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Valide les données d'un document
        
        Args:
            file_path: Chemin vers le fichier du document
        
        Returns:
            Dict[str, Any]: Résultats de la validation ou None en cas d'erreur
        """
        try:
            # Analyser le document
            results = self.analyze_document(file_path)
            if not results:
                return None
            
            # Valider les données
            validated_data = validate_document_data(results['data'])
            
            # Vérifier la cohérence
            inconsistencies = check_data_consistency(validated_data)
            
            return {
                'file_path': file_path,
                'timestamp': datetime.now().isoformat(),
                'validated_data': validated_data,
                'inconsistencies': inconsistencies
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation du document: {e}")
            return None
    
    def get_field_suggestions(self, file_path: str, field_type: str) -> List[Dict[str, Any]]:
        """
        Obtient des suggestions pour un type de champ spécifique
        
        Args:
            file_path: Chemin vers le fichier du document
            field_type: Type de champ pour lequel obtenir des suggestions
        
        Returns:
            List[Dict[str, Any]]: Liste des suggestions
        """
        try:
            # Analyser le document
            results = self.analyze_document(file_path)
            if not results:
                return []
            
            # Récupérer les champs du type demandé
            fields = results['data'].get(field_type, [])
            
            # Trier les champs par pertinence (basé sur le contexte)
            sorted_fields = sorted(
                fields,
                key=lambda x: len(x.get('context', '')),
                reverse=True
            )
            
            return sorted_fields
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des suggestions: {e}")
            return []
    
    def get_field_confidence(self, field_value: str, field_type: str) -> float:
        """
        Calcule le niveau de confiance pour une valeur de champ
        
        Args:
            field_value: Valeur du champ
            field_type: Type de champ
        
        Returns:
            float: Niveau de confiance entre 0 et 1
        """
        try:
            # Valider la valeur
            validated_value = validate_field(field_type, field_value)
            if validated_value is None:
                return 0.0
            
            # Calculer le niveau de confiance basé sur la validation
            confidence = 0.5  # Base de confiance pour une valeur valide
            
            # Ajuster la confiance en fonction du type de champ
            if field_type == 'date':
                # Plus la date est récente, plus la confiance est élevée
                try:
                    date = datetime.strptime(validated_value, "%Y-%m-%d")
                    years_old = (datetime.now() - date).days / 365
                    confidence += min(0.5, 1.0 - (years_old / 10))
                except:
                    pass
                    
            elif field_type == 'amount':
                # Plus le montant est réaliste, plus la confiance est élevée
                try:
                    amount = float(validated_value)
                    if 0 <= amount <= 1000000:  # Montant réaliste
                        confidence += 0.3
                except:
                    pass
                    
            elif field_type in ['email', 'phone']:
                # Les coordonnées de contact ont une confiance élevée
                confidence += 0.4
                
            elif field_type in ['siret', 'vat_number']:
                # Les identifiants légaux ont une confiance élevée
                confidence += 0.4
            
            return min(1.0, confidence)
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la confiance: {e}")
            return 0.0