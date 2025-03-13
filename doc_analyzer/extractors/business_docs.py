#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extracteur spécialisé pour les documents commerciaux et propositions
Module permettant d'extraire les informations pertinentes des documents commerciaux
comme les devis, factures, propositions commerciales, etc.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..config import EXTRACTOR_CONFIG

logger = logging.getLogger("VynalDocsAutomator.DocAnalyzer.BusinessDocs")

class BusinessDocExtractor:
    """
    Extracteur spécialisé pour les documents commerciaux
    Permet d'identifier et d'extraire les informations clés des documents commerciaux
    """
    
    def __init__(self):
        """Initialise l'extracteur de documents commerciaux"""
        self.config = EXTRACTOR_CONFIG["business_docs"]
        
        # Patterns spécifiques pour les différents types de documents et champs
        self._init_patterns()
        
        logger.info("BusinessDocExtractor initialized")
    
    def _init_patterns(self):
        """Initialise tous les patterns d'extraction spécifiques"""
        # Types de documents commerciaux
        self.business_type_patterns = {
            "devis": [
                r'(?i)\bdevis\b',
                r'(?i)\bestimation\b',
                r'(?i)\bquotation\b',
                r'(?i)\bestimate\b',
                r'(?i)\bproposition\s+de\s+prix\b'
            ],
            "facture": [
                r'(?i)\bfacture\b',
                r'(?i)\binvoice\b',
                r'(?i)\bmemoire\s+d\'honoraires\b',
                r'(?i)\bnote\s+d\'honoraires\b'
            ],
            "proposition_commerciale": [
                r'(?i)\bproposition\s+commerciale\b',
                r'(?i)\boffre\s+commerciale\b',
                r'(?i)\bproposition\s+de\s+service\b',
                r'(?i)\bcommercial\s+proposal\b'
            ],
            "bon_commande": [
                r'(?i)\bbon\s+de\s+commande\b',
                r'(?i)\bpurchase\s+order\b',
                r'(?i)\border\s+form\b'
            ],
            "contrat_prestation": [
                r'(?i)\bcontrat\s+de\s+prestation\b',
                r'(?i)\bservice\s+agreement\b',
                r'(?i)\bcontrat\s+de\s+service\b'
            ],
            "avenant": [
                r'(?i)\bavenant\b',
                r'(?i)\baddendum\b',
                r'(?i)\bamendment\b'
            ],
            "relance": [
                r'(?i)\brelance\b',
                r'(?i)\brappel\s+de\s+paiement\b',
                r'(?i)\breminder\b'
            ]
        }
        
        # Références document
        self.reference_patterns = [
            r'(?i)référence\s*:?\s*([A-Z0-9-_/]+)',
            r'(?i)ref\s*\.?\s*:?\s*([A-Z0-9-_/]+)',
            r'(?i)n°\s*:?\s*([A-Z0-9-_/]+)',
            r'(?i)(?:numéro|no|n°)\s+(?:de\s+)?(?:devis|facture|commande|contrat|proposition)\s*:?\s*([A-Z0-9-_/]+)'
        ]
        
        # Dates
        self.date_patterns = [
            r'(?i)date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?i)(?:fait|émis)\s+(?:à|le)\s+.+?\s+le\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?i)en date du\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        # Montants
        self.amount_patterns = {
            "montant_ht": [
                r'(?i)(?:total|montant)\s+(?:h\.?t\.?|hors\s+taxes?)\s*:?\s*(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{2})?)\s*(?:€|EUR|euros)',
                r'(?i)prix\s+(?:h\.?t\.?|hors\s+taxes?)\s*:?\s*(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{2})?)\s*(?:€|EUR|euros)'
            ],
            "montant_ttc": [
                r'(?i)(?:total|montant)\s+(?:t\.?t\.?c\.?|toutes\s+taxes)\s*:?\s*(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{2})?)\s*(?:€|EUR|euros)',
                r'(?i)prix\s+(?:t\.?t\.?c\.?|toutes\s+taxes)\s*:?\s*(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{2})?)\s*(?:€|EUR|euros)'
            ],
            "tva": [
                r'(?i)(?:montant|total)\s+(?:de\s+la\s+)?tva\s*:?\s*(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{2})?)\s*(?:€|EUR|euros)',
                r'(?i)tva\s*\(\s*\d+(?:[,.]\d+)?%\s*\)\s*:?\s*(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{2})?)\s*(?:€|EUR|euros)'
            ],
            "taux_tva": [
                r'(?i)taux\s+(?:de\s+)?tva\s*:?\s*(\d{1,2}(?:[,.]\d{1,2})?)\s*%',
                r'(?i)tva\s*\(\s*(\d{1,2}(?:[,.]\d{1,2})?)\s*%\s*\)'
            ],
            "remise": [
                r'(?i)remise\s*:?\s*(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{2})?)\s*(?:€|EUR|euros)',
                r'(?i)discount\s*:?\s*(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{2})?)\s*(?:€|EUR|euros)'
            ],
            "acompte": [
                r'(?i)acompte\s*:?\s*(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{2})?)\s*(?:€|EUR|euros)',
                r'(?i)down payment\s*:?\s*(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{2})?)\s*(?:€|EUR|euros)'
            ],
            "solde": [
                r'(?i)solde\s*:?\s*(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{2})?)\s*(?:€|EUR|euros)',
                r'(?i)balance\s*:?\s*(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{2})?)\s*(?:€|EUR|euros)'
            ]
        }
        
        # Conditions commerciales
        self.condition_patterns = {
            "validite": [
                r'(?i)(?:validité|validite)\s*:?\s*(\d+\s+(?:jours?|mois))',
                r'(?i)offre valable\s+(\d+\s+(?:jours?|mois))',
                r'(?i)devis valable\s+(\d+\s+(?:jours?|mois))'
            ],
            "paiement": [
                r'(?i)conditions\s+de\s+paiement\s*:?\s*([^,.\n]{3,100})',
                r'(?i)modalités\s+de\s+paiement\s*:?\s*([^,.\n]{3,100})',
                r'(?i)paiement\s+(?:à|a)\s+([^,.\n]{3,100})',
                r'(?i)règlement\s*:?\s*([^,.\n]{3,100})'
            ],
            "livraison": [
                r'(?i)délai\s+de\s+livraison\s*:?\s*([^,.\n]{3,100})',
                r'(?i)livraison\s+(?:sous|en|dans)\s+([^,.\n]{3,100})',
                r'(?i)délai\s+d\'exécution\s*:?\s*([^,.\n]{3,100})'
            ],
            "garantie": [
                r'(?i)garantie\s*:?\s*([^,.\n]{3,100})',
                r'(?i)durée\s+de\s+garantie\s*:?\s*([^,.\n]{3,100})'
            ]
        }
        
        # Informations émetteur et destinataire
        self.sender_patterns = {
            "company": [
                r'(?i)société\s*:?\s*([A-Z][^,\n]{3,50})',
                r'(?i)émetteur\s*:?\s*([A-Z][^,\n]{3,50})',
                r'(?i)fournisseur\s*:?\s*([A-Z][^,\n]{3,50})'
            ],
            "contact": [
                r'(?i)contact\s*:?\s*([A-Z][^,\n]{3,50})',
                r'(?i)consultant\s*:?\s*([A-Z][^,\n]{3,50})',
                r'(?i)commercial\s*:?\s*([A-Z][^,\n]{3,50})'
            ],
            "siret": [
                r'(?i)siret\s*:?\s*(\d{3}\s*\d{3}\s*\d{3}\s*\d{5}|\d{14})',
                r'(?i)siren\s*:?\s*(\d{3}\s*\d{3}\s*\d{3}|\d{9})'
            ],
            "tva_intra": [
                r'(?i)(?:tva\s+intra(?:communautaire)?|n°\s+tva|vat\s+number)\s*:?\s*([A-Z]{2}[0-9A-Z\s]{2,})'
            ]
        }
        
        self.recipient_patterns = {
            "company": [
                r'(?i)client\s*:?\s*([A-Z][^,\n]{3,50})',
                r'(?i)destinataire\s*:?\s*([A-Z][^,\n]{3,50})',
                r'(?i)acheteur\s*:?\s*([A-Z][^,\n]{3,50})'
            ],
            "contact": [
                r'(?i)à l\'attention de\s*:?\s*([A-Z][^,\n]{3,50})',
                r'(?i)contact client\s*:?\s*([A-Z][^,\n]{3,50})',
                r'(?i)adressé à\s*:?\s*([A-Z][^,\n]{3,50})'
            ]
        }
        
        # Patterns pour la détection de tableaux
        self.table_headers_patterns = [
            r'(?i)désignation.*?(?:quantité|qté).*?(?:prix|montant|p\.u\.)',
            r'(?i)description.*?(?:quantité|qté).*?(?:prix|montant|p\.u\.)',
            r'(?i)articles?.*?(?:quantité|qté).*?(?:prix|montant|p\.u\.)',
            r'(?i)prestation.*?(?:quantité|qté).*?(?:prix|montant|p\.u\.)'
        ]
    
    def extract(self, text_content: str, file_path: str = None) -> Dict[str, Any]:
        """
        Extrait les informations des documents commerciaux
        
        Args:
            text_content: Contenu texte du document
            file_path: Chemin du fichier original (pour analyse d'image si nécessaire)
            
        Returns:
            dict: Données extraites du document commercial
        """
        data = {}
        
        # Prétraitement du texte
        cleaned_text = self._preprocess_text(text_content)
        
        # Extraire le type de document commercial
        business_type = self.extract_business_type(cleaned_text)
        if business_type:
            data["business_type"] = business_type
        
        # Extraire les références
        reference = self.extract_reference(cleaned_text)
        if reference:
            data["reference"] = reference
        
        # Extraire les coordonnées de l'émetteur
        sender = self.extract_sender(cleaned_text)
        if sender:
            data["sender"] = sender
        
        # Extraire les coordonnées du destinataire
        recipient = self.extract_recipient(cleaned_text)
        if recipient:
            data["recipient"] = recipient
        
        # Extraire la date du document
        doc_date = self.extract_doc_date(cleaned_text)
        if doc_date:
            data["date"] = doc_date
        
        # Extraire les montants
        amounts = self.extract_amounts(cleaned_text)
        if amounts:
            data["amounts"] = amounts
        
        # Extraire les produits/services
        products = self.extract_products(cleaned_text)
        if products:
            data["products"] = products
        
        # Extraire les conditions
        conditions = self.extract_conditions(cleaned_text)
        if conditions:
            data["conditions"] = conditions
        
        return data
    
    def _preprocess_text(self, text: str) -> str:
        """
        Prétraite le texte pour améliorer l'extraction
        
        Args:
            text: Texte à prétraiter
            
        Returns:
            str: Texte prétraité
        """
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Normaliser les sauts de ligne
        text = re.sub(r'(\r\n|\r|\n)+', '\n', text)
        
        # Remplacer les tabulations par des espaces
        text = text.replace('\t', '    ')
        
        return text
    
    def extract_business_type(self, text: str) -> Optional[str]:
        """
        Extrait le type de document commercial
        
        Args:
            text: Texte à analyser
            
        Returns:
            str/None: Type de document commercial ou None
        """
        # Compter les occurrences de chaque type
        type_scores = {doc_type: 0 for doc_type in self.business_type_patterns}
        
        for doc_type, patterns in self.business_type_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                type_scores[doc_type] += len(matches)
        
        # Sélectionner le type avec le plus d'occurrences
        max_score = 0
        max_type = None
        
        for doc_type, score in type_scores.items():
            if score > max_score:
                max_score = score
                max_type = doc_type
        
        # Si aucun type spécifique n'est trouvé mais que c'est un document commercial
        if max_score == 0:
            if any(keyword in text.lower() for keyword in self.config["keywords"]):
                return "document_commercial_general"
            return None
        
        return max_type
    
    def extract_reference(self, text: str) -> Optional[str]:
        """
        Extrait la référence du document
        
        Args:
            text: Texte à analyser
            
        Returns:
            str/None: Référence du document ou None
        """
        for pattern in self.reference_patterns:
            matches = re.search(pattern, text)
            if matches:
                # Nettoyer la référence
                ref = matches.group(1).strip()
                
                # Vérifier que la référence n'est pas trop longue ou trop courte
                if 2 <= len(ref) <= 30:
                    return ref
        
        return None
    
    def extract_sender(self, text: str) -> Dict[str, str]:
        """
        Extrait les coordonnées de l'émetteur
        
        Args:
            text: Texte à analyser
            
        Returns:
            dict: Coordonnées de l'émetteur
        """
        sender = {}
        
        # Extraction pour chaque type d'information
        for info_type, patterns in self.sender_patterns.items():
            for pattern in patterns:
                matches = re.search(pattern, text)
                if matches:
                    value = matches.group(1).strip()
                    if value:
                        sender[info_type] = value
                        break  # Passer au type d'information suivant
        
        return sender
    
    def extract_recipient(self, text: str) -> Dict[str, str]:
        """
        Extrait les coordonnées du destinataire
        
        Args:
            text: Texte à analyser
            
        Returns:
            dict: Coordonnées du destinataire
        """
        recipient = {}
        
        # Extraction pour chaque type d'information
        for info_type, patterns in self.recipient_patterns.items():
            for pattern in patterns:
                matches = re.search(pattern, text)
                if matches:
                    value = matches.group(1).strip()
                    if value:
                        recipient[info_type] = value
                        break  # Passer au type d'information suivant
        
        return recipient
    
    def extract_doc_date(self, text: str) -> Optional[str]:
        """
        Extrait la date du document
        
        Args:
            text: Texte à analyser
            
        Returns:
            str/None: Date du document ou None
        """
        for pattern in self.date_patterns:
            matches = re.search(pattern, text)
            if matches:
                date_str = matches.group(1).strip()
                
                # Normalisation de la date
                try:
                    # Détection du format de la date
                    if re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', date_str):
                        day, month, year = map(int, date_str.split('/'))
                    elif re.match(r'\d{1,2}-\d{1,2}-\d{2,4}', date_str):
                        day, month, year = map(int, date_str.split('-'))
                    else:
                        return date_str  # Retourner la date telle quelle
                    
                    # Correction de l'année si nécessaire (format 2 chiffres)
                    if year < 100:
                        year = 2000 + year if year < 30 else 1900 + year
                    
                    # Normalisation au format ISO (YYYY-MM-DD)
                    return f"{year:04d}-{month:02d}-{day:02d}"
                except (ValueError, IndexError):
                    # Si la normalisation échoue, retourner la date telle quelle
                    return date_str
        
        return None
    
    def extract_amounts(self, text: str) -> Dict[str, str]:
        """
        Extrait les montants financiers du document
        
        Args:
            text: Texte à analyser
            
        Returns:
            dict: Dictionnaire des montants trouvés
        """
        amounts = {}
        
        # Extraction pour chaque type de montant
        for amount_type, patterns in self.amount_patterns.items():
            for pattern in patterns:
                matches = re.search(pattern, text)
                if matches:
                    # Nettoyer le montant (enlever les espaces, normaliser la virgule)
                    amount = matches.group(1).strip().replace(' ', '').replace(',', '.')
                    
                    # Pour les taux, on peut garder le pourcentage tel quel
                    if amount_type == "taux_tva":
                        amounts[amount_type] = amount
                    else:
                        # Vérifier que c'est bien un nombre
                        try:
                            float(amount)  # Juste pour vérifier
                            amounts[amount_type] = amount
                        except ValueError:
                            continue  # Ignorer si ce n'est pas un nombre valide
                    
                    break  # Passer au type de montant suivant
        
        # Calculs automatiques si possible
        if "montant_ht" in amounts and "taux_tva" in amounts and "montant_ttc" not in amounts:
            try:
                # Calculer le montant TTC
                montant_ht = float(amounts["montant_ht"])
                taux_tva = float(amounts["taux_tva"])
                montant_ttc = montant_ht * (1 + taux_tva / 100)
                amounts["montant_ttc"] = f"{montant_ttc:.2f}"
                
                # Calculer le montant de TVA
                montant_tva = montant_ht * (taux_tva / 100)
                amounts["tva"] = f"{montant_tva:.2f}"
            except (ValueError, KeyError):
                pass
        
        # Si on a montant_ht et montant_ttc, on peut calculer la TVA
        elif "montant_ht" in amounts and "montant_ttc" in amounts and "tva" not in amounts:
            try:
                montant_ht = float(amounts["montant_ht"])
                montant_ttc = float(amounts["montant_ttc"])
                montant_tva = montant_ttc - montant_ht
                amounts["tva"] = f"{montant_tva:.2f}"
                
                # Calculer le taux de TVA
                if montant_ht > 0:
                    taux_tva = (montant_tva / montant_ht) * 100
                    amounts["taux_tva"] = f"{taux_tva:.2f}"
            except (ValueError, KeyError):
                pass
        
        return amounts
    
    def extract_products(self, text: str) -> List[Dict[str, str]]:
        """
        Extrait les produits/services du document
        
        Args:
            text: Texte à analyser
            
        Returns:
            list: Liste des produits/services
        """
        products = []
        
        # Détection de tableaux
        table_section = None
        for pattern in self.table_headers_patterns:
            headers_match = re.search(pattern, text)
            if headers_match:
                # Trouver la position de l'en-tête
                header_pos = headers_match.start()
                
                # Récupérer tout ce qui suit jusqu'à une séparation claire (double saut de ligne ou total)
                end_section_match = re.search(r'\n\s*\n|\bTOTAL\b', text[header_pos:], re.IGNORECASE)
                if end_section_match:
                    end_pos = header_pos + end_section_match.start()
                else:
                    end_pos = len(text)
                
                table_section = text[header_pos:end_pos]
                break
        
        if table_section:
            # Décomposer en lignes
            lines = table_section.split('\n')
            
            # Ignorer la première ligne (en-tête)
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                
                # Essayer d'extraire les informations de la ligne
                # Différentes approches selon le format du tableau
                
                # 1. Format avec espaces/tabulations comme séparateurs
                parts = re.split(r'\s{2,}|\t', line)
                if len(parts) >= 2:
                    product = {"description": parts[0].strip()}
                    
                    # Recherche des montants et quantités
                    for part in parts[1:]:
                        # Essayer d'extraire la quantité
                        qty_match = re.search(r'(?<!\S)(\d+(?:[,.]\d+)?)(?:$|\s)', part)
                        if qty_match and "quantity" not in product:
                            product["quantity"] = qty_match.group(1).replace(',', '.')
                            continue
                        
                        # Essayer d'extraire un prix
                        price_match = re.search(r'(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{2})?)\s*(?:€|EUR|euros?)?', part)
                        if price_match:
                            price = price_match.group(1).replace(' ', '').replace(',', '.')
                            
                            # Déterminer s'il s'agit d'un prix unitaire ou total
                            if "price_unit" not in product:
                                product["price_unit"] = price
                            elif "price_total" not in product:
                                product["price_total"] = price
                    
                    # Si on a le prix unitaire et la quantité mais pas le total, le calculer
                    if "price_unit" in product and "quantity" in product and "price_total" not in product:
                        try:
                            unit_price = float(product["price_unit"])
                            quantity = float(product["quantity"])
                            total_price = unit_price * quantity
                            product["price_total"] = f"{total_price:.2f}"
                        except (ValueError, KeyError):
                            pass
                    
                    products.append(product)
                
                # 2. Format avec reconaissance basée sur les patterns d'un prix et d'une quantité
                else:
                    # Essayer d'extraire la quantité
                    qty_match = re.search(r'(?<!\S)(\d+(?:[,.]\d+)?)\s*(?:unités?|pcs?|exemplaires?)', line)
                    
                    # Essayer d'extraire un prix
                    price_match = re.search(r'(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{2})?)\s*(?:€|EUR|euros?)', line)
                    
                    if qty_match or price_match:
                        # Enlever la quantité et le prix de la description
                        description = line
                        if qty_match:
                            description = description.replace(qty_match.group(0), '')
                        if price_match:
                            description = description.replace(price_match.group(0), '')
                        
                        # Créer le produit
                        product = {"description": description.strip()}
                        
                        if qty_match:
                            product["quantity"] = qty_match.group(1).replace(',', '.')
                        
                        if price_match:
                            price = price_match.group(1).replace(' ', '').replace(',', '.')
                            product["price_total"] = price
                        
                        products.append(product)
        
        return products
    
    def extract_conditions(self, text: str) -> Dict[str, str]:
        """
        Extrait les conditions commerciales du document
        
        Args:
            text: Texte à analyser
            
        Returns:
            dict: Dictionnaire des conditions
        """
        conditions = {}
        
        # Extraction pour chaque type de condition
        for condition_type, patterns in self.condition_patterns.items():
            for pattern in patterns:
                matches = re.search(pattern, text)
                if matches:
                    value = matches.group(1).strip()
                    conditions[condition_type] = value
                    break  # Passer au type de condition suivant
        
        # Chercher les conditions particulières (section dédiée)
        condition_section_match = re.search(r'(?i)(?:conditions|modalités)\s+(?:particulières|générales|de vente).*?:(.*?)(?:\n\s*\n|\Z)', text, re.DOTALL)
        if condition_section_match:
            condition_text = condition_section_match.group(1).strip()
            if len(condition_text) > 10:  # Ignorer les sections trop courtes
                conditions["conditions_particulieres"] = condition_text
        
        return conditions
    
    def get_client_info(self, text: str) -> Dict[str, str]:
        """
        Méthode utilitaire pour récupérer les informations client du document
        Combine les résultats de l'extraction du destinataire avec d'autres extractions
        
        Args:
            text: Texte à analyser
            
        Returns:
            dict: Informations client extraites
        """
        client_info = {}
        
        # Récupérer les infos du destinataire
        recipient = self.extract_recipient(text)
        if recipient:
            # Mapper les champs
            if "contact" in recipient:
                client_info["name"] = recipient["contact"]
            if "company" in recipient:
                client_info["company"] = recipient["company"]
        
        # Chercher une adresse email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            client_info["email"] = email_match.group(0)
        
        # Chercher un numéro de téléphone (format international et local)
        phone_patterns = [
            r'(?:\+33|0)\s*[1-9](?:[\s.-]?\d{2}){4}',  # Format français
            r'(?:\+\d{1,3}|00\d{1,3})\s*\d(?:[\s.-]?\d{2,3}){3,4}',  # Format international
            r'0\d[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}'  # Format français sans +33
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                # Normaliser le format du téléphone
                phone = phone_match.group(0)
                # Supprimer les caractères de formatage
                phone = re.sub(r'[\s.-]', '', phone)
                client_info["phone"] = phone
                break
        
        # Chercher une adresse postale
        # C'est complexe, donc on recherche des patterns comme un code postal
        address_patterns = [
            r'\b\d{5}\s+[A-ZÉÈÀÊÂÔÛÙÏÜË][A-ZÉÈÀÊÂÔÛÙÏÜËa-zéèàêâôûùïüë\s-]+',  # Code postal + ville France
            r'\b[A-Za-z0-9\s,.-]{10,60}\n\s*\d{5}\s+[A-ZÉÈÀÊÂÔÛÙÏÜË][A-ZÉÈÀÊÂÔÛÙÏÜËa-zéèàêâôûùïüë\s-]+'  # Adresse + CP + ville
        ]
        
        for pattern in address_patterns:
            address_match = re.search(pattern, text, re.MULTILINE)
            if address_match:
                client_info["address"] = address_match.group(0).replace('\n', ' ')
                break
        
        return client_info
    
    def detect_language(self, text: str) -> str:
        """
        Détecte la langue principale du document
        
        Args:
            text: Texte à analyser
            
        Returns:
            str: Code de langue détecté ('fr', 'en', etc.)
        """
        # Mots spécifiques à chaque langue
        language_markers = {
            'fr': ['devis', 'facture', 'montant', 'total', 'client', 'entreprise', 'société', 'euros', 'règlement', 'tva', 'hors taxes', 'toutes taxes'],
            'en': ['quote', 'quotation', 'invoice', 'amount', 'total', 'customer', 'company', 'business', 'payment', 'vat', 'tax', 'excl', 'incl']
        }
        
        # Compter les occurrences
        scores = {lang: 0 for lang in language_markers}
        
        for lang, markers in language_markers.items():
            for marker in markers:
                pattern = r'\b' + re.escape(marker) + r'\b'
                matches = re.finditer(pattern, text.lower())
                count = sum(1 for _ in matches)
                scores[lang] += count
        
        # Retourner la langue avec le score le plus élevé, ou 'fr' par défaut
        max_score = 0
        detected_lang = 'fr'  # Default
        
        for lang, score in scores.items():
            if score > max_score:
                max_score = score
                detected_lang = lang
        
        return detected_lang
    
    def extract_payment_info(self, text: str) -> Dict[str, str]:
        """
        Extrait les informations de paiement (coordonnées bancaires, etc.)
        
        Args:
            text: Texte à analyser
            
        Returns:
            dict: Informations de paiement extraites
        """
        payment_info = {}
        
        # IBAN
        iban_match = re.search(r'(?i)iban\s*:?\s*([A-Z]{2}\d{2}(?:\s*[0-9A-Z]{4}){4,7})', text)
        if iban_match:
            # Nettoyer l'IBAN (supprimer les espaces)
            iban = re.sub(r'\s', '', iban_match.group(1))
            payment_info["iban"] = iban
        
        # BIC/SWIFT
        bic_match = re.search(r'(?i)(?:bic|swift)\s*:?\s*([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)', text)
        if bic_match:
            payment_info["bic"] = bic_match.group(1)
        
        # RIB
        rib_pattern = r'(?i)rib\s*:?\s*(?:(?:banque|code banque)\s*:?\s*(\d{5}))?\s*(?:(?:guichet|code guichet)\s*:?\s*(\d{5}))?\s*(?:(?:compte|numéro de compte)\s*:?\s*([A-Z0-9]{11}))?\s*(?:clé\s*:?\s*(\d{2}))?'
        rib_match = re.search(rib_pattern, text)
        if rib_match:
            rib_components = {}
            components = ["banque", "guichet", "compte", "cle"]
            
            for i, component in enumerate(components):
                if rib_match.group(i+1):
                    rib_components[component] = rib_match.group(i+1)
            
            if rib_components:
                payment_info["rib"] = rib_components
        
        # Mode de paiement mentionné
        payment_methods = {
            "virement": [r'(?i)\bvirement\b', r'(?i)\btransfert bancaire\b', r'(?i)\bwire transfer\b'],
            "cheque": [r'(?i)\bch[èe]que\b', r'(?i)\bch[èe]que bancaire\b', r'(?i)\bcheck\b'],
            "carte": [r'(?i)\bcarte bancaire\b', r'(?i)\bcb\b', r'(?i)\bcredit card\b', r'(?i)\bcard payment\b'],
            "especes": [r'(?i)\bespèces\b', r'(?i)\bcash\b'],
            "prelevement": [r'(?i)\bprélèvement\b', r'(?i)\bprélèvement automatique\b', r'(?i)\bdirect debit\b']
        }
        
        for method, patterns in payment_methods.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    payment_info["mode_paiement"] = method
                    break
            if "mode_paiement" in payment_info:
                break
        
        return payment_info
    
    def extract_tax_info(self, text: str) -> Dict[str, Any]:
        """
        Extrait les informations fiscales détaillées du document
        
        Args:
            text: Texte à analyser
            
        Returns:
            dict: Informations fiscales extraites
        """
        tax_info = {}
        
        # Détection de la mention d'auto-entrepreneur ou micro-entreprise
        ae_patterns = [
            r'(?i)auto-entrepreneur',
            r'(?i)auto entrepreneur',
            r'(?i)micro-entreprise',
            r'(?i)micro entreprise'
        ]
        
        for pattern in ae_patterns:
            if re.search(pattern, text):
                tax_info["regime"] = "auto_entrepreneur"
                break
        
        # Détection de la mention d'exonération de TVA (article 293B)
        tva_exoneration_patterns = [
            r'(?i)TVA\s+non\s+applicable.*?(?:art|article).*?293\s*B',
            r'(?i)exon[ée]r[ée]\s+de\s+TVA',
            r'(?i)TVA\s+exon[ée]r[ée]e?'
        ]
        
        for pattern in tva_exoneration_patterns:
            if re.search(pattern, text):
                tax_info["tva_exoneree"] = True
                break
        
        # Détail des taux de TVA
        tva_details = []
        tva_rates_patterns = [
            r'(?i)TVA\s+(?:\d{1,2}[,.]\d{1,2}|\d{1,2})%\s*:?\s*(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{1,2})?)\s*(?:€|EUR|euros?)',
            r'(?i)TVA\s*:?\s*(?:\d{1,2}[,.]\d{1,2}|\d{1,2})%\s*:?\s*(\d{1,3}(?:\s?\d{3})*(?:[,.]\d{1,2})?)\s*(?:€|EUR|euros?)'
        ]
        
        for pattern in tva_rates_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                full_match = match.group(0)
                amount = match.group(1).replace(' ', '').replace(',', '.')
                
                # Extraire le taux de TVA
                rate_match = re.search(r'(\d{1,2}[,.]\d{1,2}|\d{1,2})%', full_match)
                if rate_match:
                    rate = rate_match.group(1).replace(',', '.')
                    tva_details.append({
                        "taux": rate,
                        "montant": amount
                    })
        
        if tva_details:
            tax_info["details_tva"] = tva_details
        
        return tax_info
    
    def extract_document_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extrait les métadonnées générales du document
        
        Args:
            text: Texte à analyser
            
        Returns:
            dict: Métadonnées extraites du document
        """
        metadata = {}
        
        # Langue du document
        metadata["language"] = self.detect_language(text)
        
        # Longueur du document
        metadata["text_length"] = len(text)
        
        # Présence de tableaux
        has_table = False
        for pattern in self.table_headers_patterns:
            if re.search(pattern, text):
                has_table = True
                break
        metadata["has_table"] = has_table
        
        # Entête et pied de page potentiels
        # On suppose que les 5 premières lignes peuvent contenir l'entête
        lines = text.split('\n')
        if len(lines) > 5:
            metadata["header"] = '\n'.join(lines[:5])
            metadata["footer"] = '\n'.join(lines[-3:])
        
        return metadata
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide et nettoie les données extraites
        
        Args:
            data: Données extraites brutes
            
        Returns:
            dict: Données validées et nettoyées
        """
        validated = {}
        
        # Copier les champs valides
        for key, value in data.items():
            # Ignorer les valeurs vides
            if value is None or (isinstance(value, (dict, list)) and len(value) == 0):
                continue
                
            # Valider les montants numériques
            if key == "amounts":
                validated_amounts = {}
                for amount_type, amount_value in value.items():
                    try:
                        # Pour les taux, on accepte des valeurs jusqu'à 100
                        if amount_type == "taux_tva":
                            float_value = float(amount_value)
                            if 0 <= float_value <= 100:
                                validated_amounts[amount_type] = amount_value
                        # Pour les autres montants, ils doivent être positifs
                        else:
                            float_value = float(amount_value)
                            if float_value >= 0:
                                validated_amounts[amount_type] = amount_value
                    except (ValueError, TypeError):
                        continue
                
                if validated_amounts:
                    validated["amounts"] = validated_amounts
            
            # Valider les dates
            elif key == "date":
                # On accepte toutes les formats de date, mais on pourrait ajouter
                # une validation plus stricte ici
                validated[key] = value
            
            # Valider les produits
            elif key == "products":
                validated_products = []
                for product in value:
                    if "description" in product and product["description"].strip():
                        validated_product = {"description": product["description"].strip()}
                        
                        # Valider les champs numériques
                        for field in ["quantity", "price_unit", "price_total"]:
                            if field in product:
                                try:
                                    float_value = float(product[field])
                                    if float_value >= 0:
                                        validated_product[field] = product[field]
                                except (ValueError, TypeError):
                                    continue
                        
                        validated_products.append(validated_product)
                
                if validated_products:
                    validated["products"] = validated_products
            
            # Valider les autres champs (copie simple)
            else:
                validated[key] = value
        
        return validated
    
    def get_confidence_scores(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcule des scores de confiance pour chaque catégorie d'information extraite
        
        Args:
            data: Données extraites
            
        Returns:
            dict: Scores de confiance par catégorie
        """
        confidence = {}
        
        # Score pour le type de document
        if "business_type" in data:
            confidence["business_type"] = 0.9  # Score élevé si détecté
        
        # Score pour les montants
        if "amounts" in data:
            amounts = data["amounts"]
            if "montant_ht" in amounts and "tva" in amounts and "montant_ttc" in amounts:
                # Vérifier la cohérence: montant_ht + tva = montant_ttc (à une petite marge près)
                try:
                    ht = float(amounts["montant_ht"])
                    tva = float(amounts["tva"])
                    ttc = float(amounts["montant_ttc"])
                    
                    if abs((ht + tva) - ttc) < 0.1:  # Marge de 0.1€
                        confidence["amounts"] = 0.95  # Très confiant si cohérent
                    else:
                        confidence["amounts"] = 0.7  # Moins confiant si incohérent
                except (ValueError, KeyError):
                    confidence["amounts"] = 0.8  # Score moyen
            else:
                confidence["amounts"] = 0.7  # Score moyen
        
        # Score pour la date
        if "date" in data:
            confidence["date"] = 0.85  # Score élevé
        
        # Score pour les produits
        if "products" in data:
            # Plus de produits = plus de confiance
            num_products = len(data["products"])
            if num_products > 5:
                confidence["products"] = 0.9
            elif num_products > 2:
                confidence["products"] = 0.8
            else:
                confidence["products"] = 0.7
        
        # Score global
        total_score = sum(confidence.values()) / max(1, len(confidence))
        confidence["overall"] = min(0.95, total_score)  # Plafonné à 0.95
        
        return confidence

    def extract_client_company_info(self, text: str) -> Dict[str, str]:
        """
        Extrait spécifiquement les informations de l'entreprise cliente
        (utile pour la création de fiche client)
        
        Args:
            text: Texte à analyser
            
        Returns:
            dict: Informations de l'entreprise cliente
        """
        company_info = {}
        
        # Récupérer le nom de l'entreprise (de l'extraction du destinataire)
        recipient = self.extract_recipient(text)
        if recipient and "company" in recipient:
            company_info["name"] = recipient["company"]
        
        # Chercher le numéro SIRET/SIREN
        siret_pattern = r'(?i)(?:siret|siren)(?:\s+:|\s*:|\s+du\s+client|\s+destinataire)?\s*:?\s*(\d{3}\s*\d{3}\s*\d{3}\s*\d{5}|\d{3}\s*\d{3}\s*\d{3}|\d{14}|\d{9})'
        siret_match = re.search(siret_pattern, text)
        if siret_match:
            siret = re.sub(r'\s', '', siret_match.group(1))
            if len(siret) >= 14:
                company_info["siret"] = siret
            elif len(siret) >= 9:
                company_info["siren"] = siret
        
        # Chercher le numéro de TVA intracommunautaire
        tva_pattern = r'(?i)(?:n°\s+tva|tva\s+intracommunautaire|vat\s+number)(?:\s+:|\s*:|\s+client|\s+destinataire)?\s*:?\s*([A-Z]{2}[0-9A-Z\s]{2,})'
        tva_match = re.search(tva_pattern, text)
        if tva_match:
            tva = re.sub(r'\s', '', tva_match.group(1))
            company_info["tva_intra"] = tva
        
        # Chercher la forme juridique (SARL, SAS, etc.)
        form_patterns = [
            r'(?i)(SARL|SAS|SA|EURL|SNC|SCI|SASU|EI)\s+([A-Z][A-Za-z0-9\s&]+)',
            r'(?i)([A-Z][A-Za-z0-9\s&]+)\s+(SARL|SAS|SA|EURL|SNC|SCI|SASU|EI)\b'
        ]
        
        for pattern in form_patterns:
            form_match = re.search(pattern, text)
            if form_match:
                if form_match.group(1).upper() in ["SARL", "SAS", "SA", "EURL", "SNC", "SCI", "SASU", "EI"]:
                    company_info["forme_juridique"] = form_match.group(1).upper()
                    if "name" not in company_info:
                        company_info["name"] = form_match.group(2).strip()
                else:
                    company_info["forme_juridique"] = form_match.group(2).upper()
                    if "name" not in company_info:
                        company_info["name"] = form_match.group(1).strip()
                break
        
        # Chercher l'adresse de l'entreprise (si pas déjà extraite dans client_info)
        address_patterns = [
            r'(?i)adresse\s+(?:client|destinataire|de\s+(?:facturation|livraison))\s*:?\s*([A-Za-z0-9\s,.-]{10,100})',
            r'(?i)(?:client|destinataire)\s*:?\s*[^\n]{0,50}\n([A-Za-z0-9\s,.-]{10,100})'
        ]
        
        for pattern in address_patterns:
            address_match = re.search(pattern, text)
            if address_match:
                company_info["address"] = address_match.group(1).strip()
                break
        
        return company_info