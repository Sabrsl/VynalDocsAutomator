#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'extraction des contrats pour Vynal Docs Automator
Ce module permet d'extraire les informations pertinentes des différents types de contrats.

Types de contrats traités:
- Contrats de prestation de services
- Contrats de vente/achat de biens
- Contrats de distribution/franchise
- Contrats de licence/propriété intellectuelle
- Contrats de travail/collaboration
- Contrats d'agent commercial
- Conditions générales (vente, utilisation, service)
"""

import re
import os
import logging
from datetime import datetime
import spacy

from ..utils.text_processor import preprocess_text, clean_text
from ..utils.validators import validate_amount, validate_date, validate_entity

# Configuration du logger
logger = logging.getLogger("Vynal Docs Automator.doc_analyzer.contracts")

# Chargement du modèle spaCy (un modèle léger)
try:
    nlp = spacy.load("fr_core_news_sm")
except OSError:
    logger.warning("Modèle fr_core_news_sm non trouvé. Tentative de téléchargement...")
    from spacy.cli import download
    download("fr_core_news_sm")
    nlp = spacy.load("fr_core_news_sm")
except Exception as e:
    logger.error(f"Erreur lors du chargement du modèle spaCy: {e}")
    # Fallback sur un modèle vide si nécessaire
    nlp = spacy.blank("fr")

class ContractExtractor:
    """
    Classe pour l'extraction des informations des contrats
    """
    
    # Types de contrats reconnus
    CONTRACT_TYPES = {
        "service": ["prestation de service", "contrat de service", "services", "prestations"],
        "sale": ["vente", "achat", "acquisition", "cession de bien"],
        "distribution": ["distribution", "franchise", "concession"],
        "license": ["licence", "propriété intellectuelle", "brevet", "marque", "droit d'auteur"],
        "employment": ["travail", "embauche", "collaboration", "emploi", "cdd", "cdi"],
        "commercial_agent": ["agent commercial", "mandat commercial", "représentation commerciale"],
        "terms": ["conditions générales", "cgv", "cgu", "conditions d'utilisation"]
    }
    
    def __init__(self, resources_path=None):
        """
        Initialisation de l'extracteur de contrats
        
        Args:
            resources_path (str, optional): Chemin vers les ressources spécifiques aux contrats
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
        
        # Chargement des patterns spécifiques aux contrats
        self.patterns = self._load_patterns()
        self.logger.info("Extracteur de contrats initialisé")
    
    def _load_patterns(self):
        """
        Charge les patterns regex spécifiques aux différents types de contrats
        
        Returns:
            dict: Dictionnaire de patterns par type de contrat
        """
        patterns = {}
        
        # Patterns pour les dates
        patterns["dates"] = {
            "date_debut": re.compile(
                r"(date\s+d[e']\s*(?:début|commencement|effet|entrée\s+en\s+vigueur)[\s:]+)([0-9]{1,2}[\s./\-]+[0-9]{1,2}[\s./\-]+[0-9]{2,4})",
                re.IGNORECASE
            ),
            "date_fin": re.compile(
                r"(date\s+d[e']\s*(?:fin|expiration|terme|cessation)[\s:]+)([0-9]{1,2}[\s./\-]+[0-9]{1,2}[\s./\-]+[0-9]{2,4})",
                re.IGNORECASE
            ),
            "duree": re.compile(
                r"(?:durée|période)[\s:]*(?:de|du\s+contrat|d[e']\s*engagement)\s*(?:est|:|\s+fixée\s+à)?\s*(?:d[e'])?\s*([0-9]+)\s*(an|mois|semaine|jour)s?",
                re.IGNORECASE
            )
        }
        
        # Patterns pour les montants
        patterns["amounts"] = {
            "prix": re.compile(
                r"(?:prix|montant|coût|rémunération|honoraires?)[\s:]*(?:fixé[e]?|convenu[e]?|est|s[']élève[nt]?|de|:)?\s*(?:à)?\s*(?:la\s+somme\s+de)?\s*((?:[0-9]{1,3}(?:\s|\.|,)?)+)(?:\s*|\.|,)(?:€|EUR|euros?|F\s*CFA|XOF|MAD|DZD|XAF)",
                re.IGNORECASE
            ),
            "taux_horaire": re.compile(
                r"(?:taux\s+horaire|prix\s+de\s+l[']heure|tarif\s+horaire)[\s:]*(?:fixé[e]?|convenu[e]?|est|s[']élève[nt]?|de|:)?\s*(?:à)?\s*((?:[0-9]{1,3}(?:\s|\.|,)?)+)(?:\s*|\.|,)(?:€|EUR|euros?|F\s*CFA|XOF|MAD|DZD|XAF)(?:\s*/\s*h(?:eure)?)?",
                re.IGNORECASE
            )
        }
        
        # Patterns pour les parties contractantes
        patterns["parties"] = {
            "client": re.compile(
                r"(?:client|acheteur|acquéreur|bénéficiaire|employeur|mandant)[\s:]*(?:,|\s+:)?\s*(?:la\s+société)?\s*[«"]?([^,\n\r:]{3,50})[»"]?",
                re.IGNORECASE
            ),
            "prestataire": re.compile(
                r"(?:prestataire|vendeur|cédant|fournisseur|employé|mandataire|agent)[\s:]*(?:,|\s+:)?\s*(?:la\s+société)?\s*[«"]?([^,\n\r:]{3,50})[»"]?",
                re.IGNORECASE
            )
        }
        
        # Patterns pour le paiement
        patterns["payment"] = {
            "mode_paiement": re.compile(
                r"(?:paiement|règlement)[\s:]*(?:s[']\s*effectue[ra]?|sera\s+effectué|est\s+réalisé)?\s*par\s+([^,\n\r\.]{3,50})",
                re.IGNORECASE
            ),
            "delai_paiement": re.compile(
                r"(?:délai\s+de\s+paiement|paiement\s+sous|règlement\s+sous)[\s:]*(?:est|fixé\s+à|de|sous|dans\s+un\s+délai\s+de)?\s*([0-9]+)\s*(jour|mois|semaine)s?",
                re.IGNORECASE
            )
        }
        
        # Patterns pour les obligations
        patterns["obligations"] = {
            "confidentialite": re.compile(
                r"(?:confidentialité|clause\s+de\s+confidentialité)[\s:]*\s*([^\.]{10,500}?)(?:\.|$)",
                re.IGNORECASE
            ),
            "non_concurrence": re.compile(
                r"(?:non[\s-]concurrence|clause\s+de\s+non[\s-]concurrence)[\s:]*\s*([^\.]{10,500}?)(?:\.|$)",
                re.IGNORECASE
            )
        }
        
        # Tentative de chargement des patterns supplémentaires depuis les fichiers
        try:
            patterns_dir = os.path.join(self.resources_path, "patterns")
            if os.path.exists(patterns_dir):
                # Ici, on pourrait charger des patterns supplémentaires depuis les fichiers
                pass
        except Exception as e:
            self.logger.warning(f"Impossible de charger les patterns supplémentaires: {e}")
        
        return patterns
    
    def extract(self, text, contract_type=None):
        """
        Extrait les informations d'un contrat
        
        Args:
            text (str): Texte du contrat à analyser
            contract_type (str, optional): Type de contrat si déjà connu
            
        Returns:
            dict: Dictionnaire contenant toutes les informations extraites
        """
        # Prétraitement du texte
        clean = clean_text(text)
        processed = preprocess_text(clean)
        
        # Détection du type de contrat si non spécifié
        if not contract_type:
            contract_type = self.detect_contract_type(processed)
        
        # Analyse avec spaCy
        doc = nlp(processed)
        
        # Résultat de l'extraction
        result = {
            "type": contract_type,
            "dates": self.extract_dates(processed),
            "parties": self.extract_parties(processed, doc),
            "amounts": self.extract_amounts(processed),
            "payment": self.extract_payment_info(processed),
            "obligations": self.extract_obligations(processed)
        }
        
        # Extraction spécifique selon le type de contrat
        if contract_type:
            specific_data = self.extract_specific_data(processed, doc, contract_type)
            result.update(specific_data)
        
        # Validation des données extraites
        result = self.validate_extracted_data(result)
        
        return result
    
    def detect_contract_type(self, text):
        """
        Détecte le type de contrat à partir du texte
        
        Args:
            text (str): Texte du contrat
            
        Returns:
            str: Type de contrat détecté ou None si indéterminé
        """
        # Vérification du nom ou titre du document
        title_match = re.search(r"(?:^|\n)([^.\n]{5,100})(?:\r?\n|\.|$)", text, re.IGNORECASE)
        title = title_match.group(1).lower() if title_match else ""
        
        # Recherche des mots-clés dans le titre et le début du document
        first_500_chars = text[:500].lower()
        document_start = text[:2000].lower()
        
        # Scores par type de contrat
        scores = {contract_type: 0 for contract_type in self.CONTRACT_TYPES}
        
        # Analyse des mots-clés dans le titre et le début du document
        for contract_type, keywords in self.CONTRACT_TYPES.items():
            for keyword in keywords:
                # Points pour les occurrences dans le titre (plus important)
                if keyword in title:
                    scores[contract_type] += 5
                
                # Points pour les occurrences dans les premiers 500 caractères
                if keyword in first_500_chars:
                    scores[contract_type] += 3
                
                # Points pour les occurrences dans les premiers 2000 caractères
                elif keyword in document_start:
                    scores[contract_type] += 1
        
        # Recherche du type avec le score le plus élevé
        max_score = max(scores.values()) if scores else 0
        if max_score > 0:
            # Retourner le type avec le score le plus élevé (ou le premier en cas d'égalité)
            for contract_type, score in scores.items():
                if score == max_score:
                    return contract_type
        
        # Type indéterminé
        return None
    
    def extract_dates(self, text):
        """
        Extrait les dates importantes du contrat
        
        Args:
            text (str): Texte du contrat
            
        Returns:
            dict: Dates extraites (début, fin, durée)
        """
        dates = {
            "date_debut": None,
            "date_fin": None,
            "duree": None,
            "duree_unite": None
        }
        
        # Extraction de la date de début
        date_debut_match = self.patterns["dates"]["date_debut"].search(text)
        if date_debut_match:
            date_str = date_debut_match.group(2)
            dates["date_debut"] = validate_date(date_str)
        
        # Extraction de la date de fin
        date_fin_match = self.patterns["dates"]["date_fin"].search(text)
        if date_fin_match:
            date_str = date_fin_match.group(2)
            dates["date_fin"] = validate_date(date_str)
        
        # Extraction de la durée
        duree_match = self.patterns["dates"]["duree"].search(text)
        if duree_match:
            try:
                duree = int(duree_match.group(1))
                unite = duree_match.group(2).lower()
                dates["duree"] = duree
                dates["duree_unite"] = unite
            except (ValueError, IndexError):
                pass
        
        return dates
    
    def extract_parties(self, text, doc):
        """
        Extrait les informations sur les parties contractantes
        
        Args:
            text (str): Texte du contrat
            doc (spacy.Doc): Document spaCy analysé
            
        Returns:
            dict: Informations sur les parties
        """
        parties = {
            "client": None,
            "prestataire": None,
            "signataires": []
        }
        
        # Extraction du client
        client_match = self.patterns["parties"]["client"].search(text)
        if client_match:
            parties["client"] = client_match.group(1).strip()
        
        # Extraction du prestataire
        prestataire_match = self.patterns["parties"]["prestataire"].search(text)
        if prestataire_match:
            parties["prestataire"] = prestataire_match.group(1).strip()
        
        # Recherche des entités nommées pour les signataires
        signataires = []
        # Recherche des noms de personnes à proximité des mots liés à la signature
        signature_sections = re.finditer(r"(?:signat(?:ure|aire)|fait\s+à)", text, re.IGNORECASE)
        
        for match in signature_sections:
            start_pos = max(0, match.start() - 50)
            end_pos = min(len(text), match.end() + 200)
            signature_context = text[start_pos:end_pos]
            
            # Analyse du contexte de signature avec spaCy
            signature_doc = nlp(signature_context)
            
            for ent in signature_doc.ents:
                if ent.label_ == "PER":  # Entité de type personne
                    signataire = ent.text.strip()
                    if signataire and signataire not in signataires:
                        signataires.append(signataire)
        
        parties["signataires"] = signataires
        
        return parties
    
    def extract_amounts(self, text):
        """
        Extrait les montants financiers du contrat
        
        Args:
            text (str): Texte du contrat
            
        Returns:
            dict: Montants extraits
        """
        amounts = {
            "prix": None,
            "prix_total": None,
            "taux_horaire": None,
            "devise": "EUR"  # Par défaut
        }
        
        # Détection de la devise
        if re.search(r"F\s*CFA|XOF", text, re.IGNORECASE):
            amounts["devise"] = "XOF"
        elif re.search(r"MAD", text, re.IGNORECASE):
            amounts["devise"] = "MAD"
        elif re.search(r"DZD", text, re.IGNORECASE):
            amounts["devise"] = "DZD"
        elif re.search(r"XAF", text, re.IGNORECASE):
            amounts["devise"] = "XAF"
        
        # Extraction du prix
        prix_match = self.patterns["amounts"]["prix"].search(text)
        if prix_match:
            prix_str = prix_match.group(1)
            amounts["prix"] = validate_amount(prix_str)
        
        # Extraction du taux horaire
        taux_match = self.patterns["amounts"]["taux_horaire"].search(text)
        if taux_match:
            taux_str = taux_match.group(1)
            amounts["taux_horaire"] = validate_amount(taux_str)
        
        # Calcul du prix total si possible (à partir d'autres informations)
        # Ce calcul dépend du type de contrat et serait implémenté dans une méthode spécifique
        
        return amounts
    
    def extract_payment_info(self, text):
        """
        Extrait les informations de paiement
        
        Args:
            text (str): Texte du contrat
            
        Returns:
            dict: Informations de paiement
        """
        payment = {
            "mode_paiement": None,
            "delai_paiement": None,
            "delai_unite": None,
            "echeancier": None
        }
        
        # Extraction du mode de paiement
        mode_match = self.patterns["payment"]["mode_paiement"].search(text)
        if mode_match:
            payment["mode_paiement"] = mode_match.group(1).strip()
        
        # Extraction du délai de paiement
        delai_match = self.patterns["payment"]["delai_paiement"].search(text)
        if delai_match:
            try:
                delai = int(delai_match.group(1))
                unite = delai_match.group(2).lower()
                payment["delai_paiement"] = delai
                payment["delai_unite"] = unite
            except (ValueError, IndexError):
                pass
        
        # Recherche d'un échéancier de paiement
        echeancier_match = re.search(
            r"(?:échéancier|calendrier\s+de\s+paiement|paiement\s+échelonné)[\s:]*([^\.]{10,500}?)(?:\.|$)", 
            text, 
            re.IGNORECASE
        )
        if echeancier_match:
            payment["echeancier"] = echeancier_match.group(1).strip()
        
        return payment
    
    def extract_obligations(self, text):
        """
        Extrait les clauses d'obligations importantes
        
        Args:
            text (str): Texte du contrat
            
        Returns:
            dict: Clauses d'obligations
        """
        obligations = {
            "confidentialite": None,
            "non_concurrence": None,
            "resiliation": None
        }
        
        # Extraction de la clause de confidentialité
        conf_match = self.patterns["obligations"]["confidentialite"].search(text)
        if conf_match:
            obligations["confidentialite"] = conf_match.group(1).strip()
        
        # Extraction de la clause de non-concurrence
        nc_match = self.patterns["obligations"]["non_concurrence"].search(text)
        if nc_match:
            obligations["non_concurrence"] = nc_match.group(1).strip()
        
        # Extraction de la clause de résiliation
        resil_match = re.search(
            r"(?:résiliation|rupture|fin\s+du\s+contrat)[\s:]*([^\.]{10,500}?)(?:\.|$)", 
            text, 
            re.IGNORECASE
        )
        if resil_match:
            obligations["resiliation"] = resil_match.group(1).strip()
        
        return obligations
    
    def extract_specific_data(self, text, doc, contract_type):
        """
        Extrait des données spécifiques selon le type de contrat
        
        Args:
            text (str): Texte du contrat
            doc (spacy.Doc): Document spaCy analysé
            contract_type (str): Type de contrat
            
        Returns:
            dict: Données spécifiques au type de contrat
        """
        specific_data = {}
        
        if contract_type == "service":
            # Extraction des informations spécifiques aux contrats de service
            services_match = re.search(
                r"(?:services|prestations)[\s:]*(?:suivants?|:)?\s*([^\.]{10,500}?)(?:\.|$)", 
                text, 
                re.IGNORECASE
            )
            if services_match:
                specific_data["description_services"] = services_match.group(1).strip()
        
        elif contract_type == "sale":
            # Extraction des informations spécifiques aux contrats de vente
            product_match = re.search(
                r"(?:bien|produit|objet\s+de\s+la\s+vente)[\s:]*(?:suivants?|:)?\s*([^\.]{10,300}?)(?:\.|$)", 
                text, 
                re.IGNORECASE
            )
            if product_match:
                specific_data["description_produit"] = product_match.group(1).strip()
            
            livraison_match = re.search(
                r"(?:livraison|délai\s+de\s+livraison)[\s:]*(?:[^\.]{5,200}?)\s*([0-9]+)\s*(jour|mois|semaine)s?", 
                text, 
                re.IGNORECASE
            )
            if livraison_match:
                try:
                    specific_data["delai_livraison"] = int(livraison_match.group(1))
                    specific_data["delai_livraison_unite"] = livraison_match.group(2).lower()
                except (ValueError, IndexError):
                    pass
        
        elif contract_type == "employment":
            # Extraction des informations spécifiques aux contrats de travail
            poste_match = re.search(
                r"(?:poste|fonction|emploi)[\s:]*(?:de|d['\s])?\s*([^,\.\n\r]{3,50})", 
                text, 
                re.IGNORECASE
            )
            if poste_match:
                specific_data["poste"] = poste_match.group(1).strip()
            
            periode_essai_match = re.search(
                r"(?:période\s+d['\s]essai|essai)[\s:]*(?:de|est\s+fixée\s+à)?\s*([0-9]+)\s*(jour|mois|semaine)s?", 
                text, 
                re.IGNORECASE
            )
            if periode_essai_match:
                try:
                    specific_data["periode_essai"] = int(periode_essai_match.group(1))
                    specific_data["periode_essai_unite"] = periode_essai_match.group(2).lower()
                except (ValueError, IndexError):
                    pass
            
            # Extraction du lieu de travail
            lieu_match = re.search(
                r"(?:lieu\s+de\s+travail|lieu\s+d['\s]exécution)[\s:]*(?:est|situé[e]?\s+à)?\s*(?:à)?\s*([^,\.\n\r]{3,50})", 
                text, 
                re.IGNORECASE
            )
            if lieu_match:
                specific_data["lieu_travail"] = lieu_match.group(1).strip()
        
        # Autres types de contrats pourraient être traités ici...
        
        return specific_data
    
    def validate_extracted_data(self, data):
        """
        Valide et nettoie les données extraites
        
        Args:
            data (dict): Dictionnaire de données extraites
            
        Returns:
            dict: Données validées et nettoyées
        """
        # Validation des entités (personnes, organisations)
        if data.get("parties", {}).get("client"):
            data["parties"]["client"] = validate_entity(data["parties"]["client"])
        
        if data.get("parties", {}).get("prestataire"):
            data["parties"]["prestataire"] = validate_entity(data["parties"]["prestataire"])
        
        # Validation des montants
        if data.get("amounts", {}).get("prix") is not None:
            # S'assurer que le prix est un nombre
            try:
                data["amounts"]["prix"] = float(data["amounts"]["prix"])
            except (ValueError, TypeError):
                data["amounts"]["prix"] = None
        
        # Nettoyage des textes longs
        for section in ["obligations"]:
            if section in data:
                for key, value in data[section].items():
                    if value and isinstance(value, str):
                        # Nettoyage des textes longs (élimination des espaces multiples, etc.)
                        data[section][key] = " ".join(value.split())
        
        return data


# Fonction d'extraction autonome pour utilisation directe
def extract_contract_data(text, contract_type=None):
    """
    Fonction autonome pour extraire les données d'un contrat
    
    Args:
        text (str): Texte du contrat
        contract_type (str, optional): Type de contrat si connu
        
    Returns:
        dict: Informations extraites du contrat
    """
    extractor = ContractExtractor()
    return extractor.extract(text, contract_type)


if __name__ == "__main__":
    # Test de la classe avec un exemple de contrat
    test_text = """
    CONTRAT DE PRESTATION DE SERVICES
    
    Entre les soussignés :
    
    La société ABC Consulting, représentée par M. Jean Dupont, agissant en qualité de Directeur,
    ci-après dénommée "le Prestataire",
    
    Et
    
    La société XYZ Corp, représentée par Mme Marie Martin, agissant en qualité de Gérante,
    ci-après dénommée "le Client",
    
    Il a été convenu ce qui suit :
    
    Article 1 - Objet du contrat
    Le Prestataire s'engage à fournir au Client les services suivants : conseil en stratégie digitale,
    développement de site web et formation des équipes.
    
    Article 2 - Durée du contrat
    Le présent contrat est conclu pour une durée de 12 mois à compter de sa date de signature.
    La date de début d'effet est fixée au 01/03/2025.
    
    Article 3 - Prix et modalités de paiement
    Le prix des prestations est fixé à 5000 euros.
    Le paiement s'effectue par virement bancaire sous 30 jours suivant la réception de facture.
    
    Article 4 - Confidentialité
    Les parties s'engagent à maintenir confidentielles toutes les informations et documents de
    nature confidentielle dont elles pourraient avoir connaissance à l'occasion de l'exécution
    du présent contrat.
    
    Fait à Paris, le 15/02/2025
    
    Pour le Prestataire,                       Pour le Client,
    Jean Dupont                                Marie Martin
    """
    
    extractor = ContractExtractor()
    result = extractor.extract(test_text)
    
    print("Type de contrat détecté:", result["type"])
    print("Dates:", result["dates"])
    print("Parties:", result["parties"])
    print("Montants:", result["amounts"])
    print("Paiement:", result["payment"])
    print("Obligations:", result["obligations"])