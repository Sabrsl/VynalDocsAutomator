#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Traitement du texte extrait des documents
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime

class TextProcessor:
    """
    Classe pour le traitement du texte extrait des documents
    """
    
    def __init__(self):
        """
        Initialise le processeur de texte
        """
        # Expressions régulières pour la détection des champs
        self.patterns = {
            'date': [
                r'\b\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}\b',  # Format DD/MM/YYYY
                r'\b\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}\b',    # Format YYYY/MM/DD
                r'\b\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{2,4}\b'
            ],
            'amount': [
                r'\b\d+(?:[.,]\d{2})?\s*€\b',              # Montant avec symbole €
                r'\b\d+(?:[.,]\d{2})?\s*EUR\b',            # Montant avec EUR
                r'\b\d+(?:[.,]\d{2})?\s*euros?\b',         # Montant avec euro(s)
                r'\b\d+(?:[.,]\d{2})?\s*\$?\b'             # Montant simple
            ],
            'email': [
                r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
            ],
            'phone': [
                r'\b(?:\+33|0)\s*[1-9](?:[\s\.-]?\d{2}){4}\b',  # Format français
                r'\b\+?\d{10,}\b'                                # Format international
            ],
            'siret': [
                r'\b\d{14}\b'                                    # Format SIRET
            ],
            'vat': [
                r'\b[A-Z]{2}[0-9A-Z]{8,12}\b'                  # Format TVA
            ],
            'iban': [
                r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b'            # Format IBAN
            ],
            'bic': [
                r'\b[A-Z]{6}[0-9A-Z]{2}(?:[0-9A-Z]{3})?\b'     # Format BIC
            ]
        }
        
        # Mots-clés pour la détection des champs
        self.keywords = {
            'date': ['date', 'daté', 'datée', 'daté le', 'datée le', 'le'],
            'amount': ['montant', 'total', 'prix', 'coût', 'cout', 'somme', 'tva'],
            'email': ['email', 'mail', 'courriel', 'e-mail'],
            'phone': ['téléphone', 'telephone', 'tel', 'mobile', 'portable'],
            'siret': ['siret', 'siren'],
            'vat': ['tva', 'vat', 'taxe'],
            'iban': ['iban', 'compte'],
            'bic': ['bic', 'swift']
        }
    
    def clean_text(self, text: str) -> str:
        """
        Nettoie le texte extrait
        
        Args:
            text: Texte à nettoyer
        
        Returns:
            str: Texte nettoyé
        """
        # Remplacer les sauts de ligne multiples par un seul
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les espaces au début et à la fin
        text = text.strip()
        
        return text
    
    def extract_dates(self, text: str) -> List[str]:
        """
        Extrait les dates du texte
        
        Args:
            text: Texte à analyser
        
        Returns:
            List[str]: Liste des dates trouvées
        """
        dates = []
        for pattern in self.patterns['date']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                dates.append(match.group())
        return dates
    
    def extract_amounts(self, text: str) -> List[str]:
        """
        Extrait les montants du texte
        
        Args:
            text: Texte à analyser
        
        Returns:
            List[str]: Liste des montants trouvés
        """
        amounts = []
        for pattern in self.patterns['amount']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amounts.append(match.group())
        return amounts
    
    def extract_emails(self, text: str) -> List[str]:
        """
        Extrait les adresses email du texte
        
        Args:
            text: Texte à analyser
        
        Returns:
            List[str]: Liste des emails trouvés
        """
        emails = []
        for pattern in self.patterns['email']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                emails.append(match.group())
        return emails
    
    def extract_phones(self, text: str) -> List[str]:
        """
        Extrait les numéros de téléphone du texte
        
        Args:
            text: Texte à analyser
        
        Returns:
            List[str]: Liste des numéros trouvés
        """
        phones = []
        for pattern in self.patterns['phone']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                phones.append(match.group())
        return phones
    
    def extract_sirets(self, text: str) -> List[str]:
        """
        Extrait les numéros SIRET du texte
        
        Args:
            text: Texte à analyser
        
        Returns:
            List[str]: Liste des numéros SIRET trouvés
        """
        sirets = []
        for pattern in self.patterns['siret']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                sirets.append(match.group())
        return sirets
    
    def extract_vat_numbers(self, text: str) -> List[str]:
        """
        Extrait les numéros de TVA du texte
        
        Args:
            text: Texte à analyser
        
        Returns:
            List[str]: Liste des numéros de TVA trouvés
        """
        vat_numbers = []
        for pattern in self.patterns['vat']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                vat_numbers.append(match.group())
        return vat_numbers
    
    def extract_ibans(self, text: str) -> List[str]:
        """
        Extrait les numéros IBAN du texte
        
        Args:
            text: Texte à analyser
        
        Returns:
            List[str]: Liste des numéros IBAN trouvés
        """
        ibans = []
        for pattern in self.patterns['iban']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                ibans.append(match.group())
        return ibans
    
    def extract_bics(self, text: str) -> List[str]:
        """
        Extrait les codes BIC du texte
        
        Args:
            text: Texte à analyser
        
        Returns:
            List[str]: Liste des codes BIC trouvés
        """
        bics = []
        for pattern in self.patterns['bic']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                bics.append(match.group())
        return bics
    
    def find_field_context(self, text: str, field_type: str, value: str) -> Optional[str]:
        """
        Trouve le contexte d'un champ dans le texte
        
        Args:
            text: Texte à analyser
            field_type: Type de champ
            value: Valeur du champ
        
        Returns:
            str: Contexte du champ ou None si non trouvé
        """
        # Trouver la position de la valeur dans le texte
        pos = text.find(value)
        if pos == -1:
            return None
        
        # Définir la taille du contexte (nombre de caractères avant et après)
        context_size = 50
        
        # Extraire le contexte
        start = max(0, pos - context_size)
        end = min(len(text), pos + len(value) + context_size)
        
        # Chercher les mots-clés associés au type de champ
        keywords = self.keywords.get(field_type, [])
        context = text[start:end]
        
        # Vérifier si un mot-clé est présent dans le contexte
        for keyword in keywords:
            if keyword.lower() in context.lower():
                return context
        
        return None
    
    def extract_fields(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extrait tous les champs du texte
        
        Args:
            text: Texte à analyser
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Champs extraits avec leur contexte
        """
        # Nettoyer le texte
        clean_text = self.clean_text(text)
        
        # Extraire les différents types de champs
        fields = {
            'dates': [{'value': date, 'context': self.find_field_context(clean_text, 'date', date)}
                     for date in self.extract_dates(clean_text)],
            'amounts': [{'value': amount, 'context': self.find_field_context(clean_text, 'amount', amount)}
                      for amount in self.extract_amounts(clean_text)],
            'emails': [{'value': email, 'context': self.find_field_context(clean_text, 'email', email)}
                     for email in self.extract_emails(clean_text)],
            'phones': [{'value': phone, 'context': self.find_field_context(clean_text, 'phone', phone)}
                     for phone in self.extract_phones(clean_text)],
            'sirets': [{'value': siret, 'context': self.find_field_context(clean_text, 'siret', siret)}
                     for siret in self.extract_sirets(clean_text)],
            'vat_numbers': [{'value': vat, 'context': self.find_field_context(clean_text, 'vat', vat)}
                          for vat in self.extract_vat_numbers(clean_text)],
            'ibans': [{'value': iban, 'context': self.find_field_context(clean_text, 'iban', iban)}
                    for iban in self.extract_ibans(clean_text)],
            'bics': [{'value': bic, 'context': self.find_field_context(clean_text, 'bic', bic)}
                   for bic in self.extract_bics(clean_text)]
        }
        
        return fields
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyse le texte et extrait toutes les informations pertinentes
        
        Args:
            text: Texte à analyser
        
        Returns:
            Dict[str, Any]: Résultats de l'analyse
        """
        # Extraire les champs
        fields = self.extract_fields(text)
        
        # Organiser les résultats
        results = {
            'text': text,
            'fields': fields,
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'field_counts': {
                    field_type: len(values)
                    for field_type, values in fields.items()
                }
            }
        }
        
        return results 