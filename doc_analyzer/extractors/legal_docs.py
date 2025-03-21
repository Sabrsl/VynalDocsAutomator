#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de modèle de documents juridiques pour Vynal Docs Automator
Ce module définit les structures de données et les méthodes pour représenter
et manipuler différents types de documents juridiques (actes, procédures, contrats).
"""

import os
import json
import datetime
import uuid
import re
from enum import Enum
from typing import Dict, List, Optional, Any, Union

# Définition des types de documents juridiques
class LegalDocumentType(Enum):
    """Types de documents juridiques supportés"""
    
    # Documents d'avocats
    COURT_PROCEDURE = "procedure_judiciaire"  # Assignations, conclusions, mémoires, requêtes
    PROCEDURAL_ACT = "acte_procedural"        # Référés, expertises, PV de comparution
    LEGAL_CORRESPONDENCE = "correspondance_juridique"  # Lettres de mission, mises en demeure
    
    # Documents de notaires
    AUTHENTIC_DEED = "acte_authentique"       # Ventes immobilières, contrats de mariage, testaments
    CONTRACT_DEED = "acte_contractuel"        # Baux commerciaux, compromis de vente
    PATRIMONIAL_DOCUMENT = "document_patrimonial"  # Inventaires successoraux, certificats d'hérédité
    
    # Contrats généraux
    SERVICE_CONTRACT = "contrat_prestation_service"
    SALES_CONTRACT = "contrat_vente"
    DISTRIBUTION_CONTRACT = "contrat_distribution"
    IP_CONTRACT = "contrat_propriete_intellectuelle"
    EMPLOYMENT_CONTRACT = "contrat_travail"
    COMMERCIAL_AGENT_CONTRACT = "contrat_agent_commercial"
    GENERAL_CONDITIONS = "conditions_generales"
    
    # Autres documents juridiques
    CORPORATE_DOCUMENT = "document_societaire"     # Statuts, PV, rapports
    ADMINISTRATIVE_DOCUMENT = "document_administratif"  # Formulaires officiels, autorisations
    FINANCIAL_DOCUMENT = "document_financier"      # Contrats de prêt, garanties
    
    # Document inconnu
    UNKNOWN = "inconnu"


class DocumentStatus(Enum):
    """Statuts possibles d'un document juridique"""
    DRAFT = "brouillon"
    PENDING = "en_attente"
    SIGNED = "signe"
    REGISTERED = "enregistre"
    NOTIFIED = "notifie"
    EXPIRED = "expire"
    CANCELED = "annule"
    ARCHIVED = "archive"


class DocumentRole(Enum):
    """Rôles des parties dans un document juridique"""
    AUTHOR = "auteur"             # Rédacteur/Émetteur du document
    RECIPIENT = "destinataire"     # Destinataire principal
    SIGNATORY = "signataire"       # Signataire
    BENEFICIARY = "beneficiaire"   # Bénéficiaire
    PLAINTIFF = "demandeur"        # Demandeur/Requérant (procédures)
    DEFENDANT = "defendeur"        # Défendeur
    WITNESS = "temoin"             # Témoin
    AUTHORITY = "autorite"         # Autorité compétente
    OTHER = "autre"                # Autre rôle


class LegalDocumentModel:
    """
    Modèle de document juridique
    Représente la structure et les métadonnées d'un document juridique
    """
    
    def __init__(self, 
                 doc_type: Union[LegalDocumentType, str] = LegalDocumentType.UNKNOWN,
                 title: str = None,
                 reference: str = None):
        """
        Initialisation d'un document juridique
        
        Args:
            doc_type: Type de document juridique
            title: Titre du document
            reference: Référence unique du document
        """
        # Conversion du type en énumération si fourni en string
        if isinstance(doc_type, str):
            try:
                self.doc_type = LegalDocumentType(doc_type)
            except ValueError:
                self.doc_type = LegalDocumentType.UNKNOWN
        else:
            self.doc_type = doc_type
        
        # Identifiant unique du document
        self.id = str(uuid.uuid4())
        
        # Métadonnées de base
        self.title = title or f"Document {self.doc_type.value}"
        self.reference = reference or f"REF-{self.id[:8]}"
        self.creation_date = datetime.datetime.now().isoformat()
        self.last_modified = self.creation_date
        self.status = DocumentStatus.DRAFT
        self.language = "fr"  # Par défaut: français
        
        # Données spécifiques au contenu
        self.content_fields = {}
        self.metadata = {}
        
        # Parties impliquées (personnes, entités)
        self.parties = []
        
        # Dates importantes
        self.important_dates = {
            "creation": self.creation_date,
            "signature": None,
            "expiration": None,
            "effective": None
        }
        
        # Chemins des fichiers associés
        self.files = {
            "main_document": None,
            "attachments": []
        }
        
        # Initialiser les champs spécifiques au type de document
        self._initialize_type_specific_fields()
    
    def _initialize_type_specific_fields(self):
        """
        Initialise les champs spécifiques en fonction du type de document
        """
        # Champs spécifiques selon le type de document
        specific_fields = {}
        
        # Documents d'avocats
        if self.doc_type == LegalDocumentType.COURT_PROCEDURE:
            specific_fields = {
                "juridiction": None,
                "numero_role": None,
                "date_audience": None,
                "objet_procedure": None,
                "decision": None
            }
        
        elif self.doc_type == LegalDocumentType.PROCEDURAL_ACT:
            specific_fields = {
                "type_acte": None,
                "date_signification": None,
                "huissier": None
            }
        
        elif self.doc_type == LegalDocumentType.LEGAL_CORRESPONDENCE:
            specific_fields = {
                "type_correspondance": None,
                "urgence": False,
                "delai_reponse": None
            }
        
        # Documents de notaires
        elif self.doc_type == LegalDocumentType.AUTHENTIC_DEED:
            specific_fields = {
                "type_acte": None,
                "minutier": None,
                "frais": None,
                "date_enregistrement": None
            }
        
        elif self.doc_type == LegalDocumentType.CONTRACT_DEED:
            specific_fields = {
                "duree": None,
                "montant": None,
                "conditions_resolutoires": None
            }
        
        elif self.doc_type == LegalDocumentType.PATRIMONIAL_DOCUMENT:
            specific_fields = {
                "patrimoine_concerne": None,
                "valeur_estimee": None
            }
        
        # Contrats
        elif self.doc_type in [
            LegalDocumentType.SERVICE_CONTRACT, 
            LegalDocumentType.SALES_CONTRACT,
            LegalDocumentType.DISTRIBUTION_CONTRACT,
            LegalDocumentType.IP_CONTRACT,
            LegalDocumentType.EMPLOYMENT_CONTRACT,
            LegalDocumentType.COMMERCIAL_AGENT_CONTRACT
        ]:
            specific_fields = {
                "duree_contrat": None,
                "montant": None,
                "delai_paiement": None,
                "modalites_resiliation": None,
                "clauses_specifiques": []
            }
            
            # Champs supplémentaires selon le type de contrat
            if self.doc_type == LegalDocumentType.SERVICE_CONTRACT:
                specific_fields.update({
                    "services": [],
                    "livrables": [],
                    "delais_execution": None
                })
            
            elif self.doc_type == LegalDocumentType.SALES_CONTRACT:
                specific_fields.update({
                    "biens": [],
                    "prix_unitaires": {},
                    "conditions_livraison": None,
                    "garanties": None
                })
            
            elif self.doc_type == LegalDocumentType.EMPLOYMENT_CONTRACT:
                specific_fields.update({
                    "poste": None,
                    "salaire": None,
                    "duree_travail": None,
                    "lieu_travail": None,
                    "avantages": [],
                    "periode_essai": None,
                    "convention_collective": None
                })
        
        # Mise à jour des champs de contenu avec les champs spécifiques
        self.content_fields.update(specific_fields)
    
    def add_party(self, name: str, role: Union[DocumentRole, str], details: Dict[str, Any] = None):
        """
        Ajoute une partie (personne ou entité) au document
        
        Args:
            name: Nom de la partie
            role: Rôle de la partie dans le document
            details: Détails supplémentaires sur la partie
        """
        # Conversion du rôle en énumération si fourni en string
        if isinstance(role, str):
            try:
                role = DocumentRole(role)
            except ValueError:
                role = DocumentRole.OTHER
        
        # Initialisation des détails si non fournis
        if details is None:
            details = {}
        
        party = {
            "name": name,
            "role": role.value,
            "details": details
        }
        
        self.parties.append(party)
    
    def set_status(self, status: Union[DocumentStatus, str]):
        """
        Met à jour le statut du document
        
        Args:
            status: Nouveau statut
        """
        # Conversion du statut en énumération si fourni en string
        if isinstance(status, str):
            try:
                self.status = DocumentStatus(status)
            except ValueError:
                self.status = DocumentStatus.DRAFT
        else:
            self.status = status
        
        # Mise à jour de la date de modification
        self.last_modified = datetime.datetime.now().isoformat()
    
    def set_important_date(self, date_type: str, date_value: Union[str, datetime.datetime]):
        """
        Définit une date importante pour le document
        
        Args:
            date_type: Type de date (signature, expiration, effective, etc.)
            date_value: Valeur de la date (ISO string ou datetime)
        """
        # Conversion en ISO string si datetime
        if isinstance(date_value, datetime.datetime):
            date_value = date_value.isoformat()
        
        self.important_dates[date_type] = date_value
        self.last_modified = datetime.datetime.now().isoformat()
    
    def update_content_field(self, field_name: str, value: Any):
        """
        Met à jour un champ de contenu
        
        Args:
            field_name: Nom du champ
            value: Nouvelle valeur
        """
        self.content_fields[field_name] = value
        self.last_modified = datetime.datetime.now().isoformat()
    
    def update_metadata(self, metadata: Dict[str, Any]):
        """
        Met à jour les métadonnées du document
        
        Args:
            metadata: Nouvelles métadonnées
        """
        self.metadata.update(metadata)
        self.last_modified = datetime.datetime.now().isoformat()
    
    def set_main_document_file(self, file_path: str):
        """
        Définit le fichier principal du document
        
        Args:
            file_path: Chemin vers le fichier
        """
        self.files["main_document"] = file_path
        self.last_modified = datetime.datetime.now().isoformat()
    
    def add_attachment(self, file_path: str, description: str = None):
        """
        Ajoute une pièce jointe au document
        
        Args:
            file_path: Chemin vers le fichier
            description: Description de la pièce jointe
        """
        attachment = {
            "file_path": file_path,
            "description": description,
            "added_date": datetime.datetime.now().isoformat()
        }
        
        self.files["attachments"].append(attachment)
        self.last_modified = datetime.datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit le modèle en dictionnaire
        
        Returns:
            Dict: Représentation du document en dictionnaire
        """
        # Conversion des énumérations en strings
        doc_dict = {
            "id": self.id,
            "doc_type": self.doc_type.value,
            "title": self.title,
            "reference": self.reference,
            "creation_date": self.creation_date,
            "last_modified": self.last_modified,
            "status": self.status.value,
            "language": self.language,
            "content_fields": self.content_fields,
            "metadata": self.metadata,
            "parties": self.parties,
            "important_dates": self.important_dates,
            "files": self.files
        }
        
        return doc_dict
    
    def to_json(self) -> str:
        """
        Convertit le modèle en JSON
        
        Returns:
            str: Représentation JSON du document
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LegalDocumentModel':
        """
        Crée une instance à partir d'un dictionnaire
        
        Args:
            data: Dictionnaire contenant les données du document
            
        Returns:
            LegalDocumentModel: Instance du modèle
        """
        doc = cls(doc_type=data.get("doc_type", LegalDocumentType.UNKNOWN.value),
                 title=data.get("title"),
                 reference=data.get("reference"))
        
        # Mise à jour des attributs de base
        doc.id = data.get("id", doc.id)
        doc.creation_date = data.get("creation_date", doc.creation_date)
        doc.last_modified = data.get("last_modified", doc.last_modified)
        doc.language = data.get("language", doc.language)
        
        # Mise à jour du statut
        status_value = data.get("status")
        if status_value:
            doc.set_status(status_value)
        
        # Mise à jour des champs structurés
        doc.content_fields = data.get("content_fields", {})
        doc.metadata = data.get("metadata", {})
        doc.parties = data.get("parties", [])
        doc.important_dates = data.get("important_dates", doc.important_dates)
        doc.files = data.get("files", doc.files)
        
        return doc
    
    @classmethod
    def from_json(cls, json_str: str) -> 'LegalDocumentModel':
        """
        Crée une instance à partir d'une chaîne JSON
        
        Args:
            json_str: Chaîne JSON contenant les données du document
            
        Returns:
            LegalDocumentModel: Instance du modèle
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def save_to_file(self, file_path: str) -> bool:
        """
        Sauvegarde le modèle dans un fichier JSON
        
        Args:
            file_path: Chemin du fichier de destination
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du document: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, file_path: str) -> Optional['LegalDocumentModel']:
        """
        Charge le modèle depuis un fichier JSON
        
        Args:
            file_path: Chemin du fichier source
            
        Returns:
            LegalDocumentModel: Instance chargée ou None si erreur
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_str = f.read()
            return cls.from_json(json_str)
        except Exception as e:
            print(f"Erreur lors du chargement du document: {e}")
            return None


class LegalDocumentFactory:
    """Fabrique pour créer des documents juridiques de différents types"""
    
    @staticmethod
    def create_document(doc_type: Union[LegalDocumentType, str], title: str = None, 
                        reference: str = None) -> LegalDocumentModel:
        """
        Crée un document juridique du type spécifié
        
        Args:
            doc_type: Type de document à créer
            title: Titre du document
            reference: Référence du document
        
        Returns:
            LegalDocumentModel: Instance du modèle créé
        """
        return LegalDocumentModel(doc_type=doc_type, title=title, reference=reference)
    
    @staticmethod
    def create_court_procedure(title: str, jurisdiction: str = None, 
                             procedure_object: str = None) -> LegalDocumentModel:
        """
        Crée un document de procédure judiciaire
        
        Args:
            title: Titre du document
            jurisdiction: Juridiction concernée
            procedure_object: Objet de la procédure
        
        Returns:
            LegalDocumentModel: Document de procédure judiciaire
        """
        doc = LegalDocumentModel(doc_type=LegalDocumentType.COURT_PROCEDURE, title=title)
        
        if jurisdiction:
            doc.update_content_field("juridiction", jurisdiction)
        
        if procedure_object:
            doc.update_content_field("objet_procedure", procedure_object)
        
        return doc
    
    @staticmethod
    def create_contract(contract_type: LegalDocumentType, title: str, 
                      amount: float = None, duration: str = None) -> LegalDocumentModel:
        """
        Crée un contrat du type spécifié
        
        Args:
            contract_type: Type de contrat
            title: Titre du contrat
            amount: Montant du contrat
            duration: Durée du contrat
        
        Returns:
            LegalDocumentModel: Document de contrat
        """
        # Vérifier que le type est bien un type de contrat
        valid_contract_types = [
            LegalDocumentType.SERVICE_CONTRACT,
            LegalDocumentType.SALES_CONTRACT,
            LegalDocumentType.DISTRIBUTION_CONTRACT,
            LegalDocumentType.IP_CONTRACT,
            LegalDocumentType.EMPLOYMENT_CONTRACT,
            LegalDocumentType.COMMERCIAL_AGENT_CONTRACT
        ]
        
        if contract_type not in valid_contract_types:
            contract_type = LegalDocumentType.SERVICE_CONTRACT
        
        doc = LegalDocumentModel(doc_type=contract_type, title=title)
        
        if amount is not None:
            doc.update_content_field("montant", amount)
        
        if duration:
            doc.update_content_field("duree_contrat", duration)
        
        return doc
    
    @staticmethod
    def create_notarial_deed(title: str, deed_type: str = None, 
                           registration_date: str = None) -> LegalDocumentModel:
        """
        Crée un acte notarié authentique
        
        Args:
            title: Titre de l'acte
            deed_type: Type d'acte
            registration_date: Date d'enregistrement
        
        Returns:
            LegalDocumentModel: Document d'acte notarié
        """
        doc = LegalDocumentModel(doc_type=LegalDocumentType.AUTHENTIC_DEED, title=title)
        
        if deed_type:
            doc.update_content_field("type_acte", deed_type)
        
        if registration_date:
            doc.update_content_field("date_enregistrement", registration_date)
        
        return doc


class LegalDocsExtractor:
    """
    Extracteur de données pour les documents juridiques
    """
    
    def __init__(self):
        self.document_model = None
        self.factory = LegalDocumentFactory()
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extrait les informations juridiques d'un texte
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dict[str, Any]: Données extraites
        """
        # Détecter le type de document
        doc_type = self._detect_document_type(text)
        
        # Créer le modèle de document approprié
        self.document_model = self.factory.create_document(doc_type)
        
        # Extraire les informations de base
        self._extract_basic_info(text)
        
        # Extraire les parties
        self._extract_parties(text)
        
        # Extraire les dates importantes
        self._extract_dates(text)
        
        # Extraire les informations spécifiques au type
        self._extract_type_specific_info(text)
        
        # Retourner les résultats
        return self.document_model.to_dict()
    
    def _detect_document_type(self, text: str) -> LegalDocumentType:
        """Détecte le type de document juridique"""
        text = text.lower()
        
        # Mots-clés pour chaque type de document
        keywords = {
            LegalDocumentType.COURT_PROCEDURE: [
                "tribunal", "assignation", "conclusions", "requête", "procédure"
            ],
            LegalDocumentType.AUTHENTIC_DEED: [
                "acte authentique", "notaire", "par-devant", "minute"
            ],
            LegalDocumentType.SERVICE_CONTRACT: [
                "contrat de prestation", "services", "prestataire"
            ],
            LegalDocumentType.SALES_CONTRACT: [
                "contrat de vente", "vendeur", "acquéreur", "prix de vente"
            ],
            LegalDocumentType.EMPLOYMENT_CONTRACT: [
                "contrat de travail", "employeur", "salarié", "rémunération"
            ]
        }
        
        # Compter les occurrences de mots-clés
        scores = {doc_type: 0 for doc_type in LegalDocumentType}
        for doc_type, words in keywords.items():
            for word in words:
                if word in text:
                    scores[doc_type] += 1
        
        # Retourner le type avec le plus haut score
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return LegalDocumentType.UNKNOWN
    
    def _extract_basic_info(self, text: str):
        """Extrait les informations de base"""
        # Extraire le titre
        title_match = re.search(r"^(.+?)(?:\n|$)", text)
        if title_match:
            self.document_model.title = title_match.group(1).strip()
        
        # Extraire la référence
        ref_match = re.search(r"[Rr][ée]f[ée]rence.*?[:]\s*([^\n]+)", text)
        if ref_match:
            self.document_model.reference = ref_match.group(1).strip()
    
    def _extract_parties(self, text: str):
        """Extrait les informations sur les parties"""
        # Patterns pour différentes parties
        patterns = {
            "ENTRE": DocumentRole.AUTHOR,
            "ET": DocumentRole.RECIPIENT,
            "POUR": DocumentRole.BENEFICIARY,
            "REPRÉSENTÉ PAR": DocumentRole.SIGNATORY
        }
        
        for keyword, role in patterns.items():
            pattern = f"{keyword}[:\\s]+([^\\n]+)(?:\\n|$)"
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                party_name = match.group(1).strip()
                self.document_model.add_party(party_name, role)
    
    def _extract_dates(self, text: str):
        """Extrait les dates importantes"""
        # Pattern pour les dates (format JJ/MM/AAAA ou JJ-MM-AAAA)
        date_pattern = r"(\d{1,2}[-/]\d{1,2}[-/]\d{4})"
        
        # Patterns spécifiques
        date_keywords = {
            "date de signature": "signature",
            "fait le": "signature",
            "en date du": "effective",
            "expire le": "expiration"
        }
        
        for keyword, date_type in date_keywords.items():
            pattern = f"{keyword}.*?{date_pattern}"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                self.document_model.set_important_date(date_type, date_str)
    
    def _extract_type_specific_info(self, text: str):
        """Extrait les informations spécifiques au type de document"""
        if self.document_model.doc_type == LegalDocumentType.COURT_PROCEDURE:
            self._extract_court_procedure_info(text)
        elif self.document_model.doc_type == LegalDocumentType.SERVICE_CONTRACT:
            self._extract_service_contract_info(text)
        elif self.document_model.doc_type == LegalDocumentType.EMPLOYMENT_CONTRACT:
            self._extract_employment_contract_info(text)
    
    def _extract_court_procedure_info(self, text: str):
        """Extrait les informations spécifiques aux procédures judiciaires"""
        # Extraire la juridiction
        jurisdiction_match = re.search(r"TRIBUNAL.*?(?:\n|$)", text, re.IGNORECASE)
        if jurisdiction_match:
            self.document_model.update_content_field("juridiction", jurisdiction_match.group(0).strip())
        
        # Extraire le numéro de rôle
        role_match = re.search(r"RG.*?(\d+)", text)
        if role_match:
            self.document_model.update_content_field("numero_role", role_match.group(1))
    
    def _extract_service_contract_info(self, text: str):
        """Extrait les informations spécifiques aux contrats de service"""
        # Extraire les services
        services_section = re.search(r"SERVICES.*?\n(.*?)(?:\n\n|\Z)", text, re.DOTALL | re.IGNORECASE)
        if services_section:
            services = [s.strip() for s in services_section.group(1).split("\n") if s.strip()]
            self.document_model.update_content_field("services", services)
        
        # Extraire le montant
        amount_match = re.search(r"montant.*?(\d+(?:[.,]\d+)?)\s*(?:€|EUR)", text, re.IGNORECASE)
        if amount_match:
            amount = float(amount_match.group(1).replace(",", "."))
            self.document_model.update_content_field("montant", amount)
    
    def _extract_employment_contract_info(self, text: str):
        """Extrait les informations spécifiques aux contrats de travail"""
        # Extraire le poste
        position_match = re.search(r"poste.*?[:]\s*([^\n]+)", text, re.IGNORECASE)
        if position_match:
            self.document_model.update_content_field("poste", position_match.group(1).strip())
        
        # Extraire le salaire
        salary_match = re.search(r"salaire.*?(\d+(?:[.,]\d+)?)\s*(?:€|EUR)", text, re.IGNORECASE)
        if salary_match:
            salary = float(salary_match.group(1).replace(",", "."))
            self.document_model.update_content_field("salaire", salary)
        
        # Extraire la durée du travail
        hours_match = re.search(r"durée.*?travail.*?(\d+).*?heures", text, re.IGNORECASE)
        if hours_match:
            self.document_model.update_content_field("duree_travail", f"{hours_match.group(1)}h")


# Exemples d'utilisation
if __name__ == "__main__":
    # Exemple de texte juridique
    example_text = """
    CONTRAT DE TRAVAIL À DURÉE INDÉTERMINÉE
    
    ENTRE:
    La société ACME SARL, au capital de 50000€
    
    ET:
    M. Jean DUPONT
    
    Poste: Développeur Senior
    Salaire: 45000€ brut annuel
    Durée du travail: 35 heures
    
    Fait le 15/03/2024
    """
    
    # Créer un extracteur
    extractor = LegalDocsExtractor()
    
    # Extraire les informations
    result = extractor.extract(example_text)
    
    # Afficher les résultats
    print("Résultats de l'extraction:")
    print(json.dumps(result, indent=2, ensure_ascii=False))