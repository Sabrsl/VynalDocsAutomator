#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de correspondance client pour Vynal Docs Automator
Fournit des fonctionnalités pour rechercher des clients correspondants
aux données extraites des documents et effectuer des correspondances.
"""

import re
import logging
import difflib
from typing import Dict, Any, List, Tuple, Optional, Union

# Importation des modules internes
from ..config import get_config

# Configuration du logger
logger = logging.getLogger("Vynal Docs Automator.doc_analyzer.ui.client_matcher")

class ClientMatcher:
    """
    Classe pour la recherche et la correspondance de clients
    """
    
    def __init__(self, clients_db: List[Dict[str, Any]] = None):
        """
        Initialise le module de correspondance client
        
        Args:
            clients_db (list, optional): Base de données des clients
        """
        self.clients_db = clients_db or []
        self.config = get_config()
        
        # Configuration du matcher
        self.match_config = self.config.get_section("ui").get("client_matcher", {})
        self.match_threshold = self.match_config.get("match_threshold", 0.7)
        self.max_results = self.match_config.get("max_results", 5)
        self.search_fields = self.match_config.get("search_fields", ["name", "email", "phone", "company"])
        
        # Stockage des derniers résultats
        self.last_results = []
        
        logger.info("Module de correspondance client initialisé")
    
    def search_clients(self, query: str) -> List[Tuple[Dict[str, Any], float]]:
        """
        Recherche des clients correspondant à une requête textuelle
        
        Args:
            query (str): Texte de recherche
            
        Returns:
            list: Liste de tuples (client, score) triés par score décroissant
        """
        if not query or not self.clients_db:
            self.last_results = []
            return []
        
        # Nettoyer la requête
        query = query.lower().strip()
        if not query:
            self.last_results = []
            return []
        
        # Calculer les scores pour chaque client
        matches = []
        for client in self.clients_db:
            score = self._calculate_match_score(client, query)
            if score >= self.match_threshold:
                matches.append((client, score))
        
        # Trier par score décroissant et limiter le nombre de résultats
        matches.sort(key=lambda x: x[1], reverse=True)
        matches = matches[:self.max_results]
        
        # Sauvegarder les résultats
        self.last_results = matches
        
        return matches
    
    def _calculate_match_score(self, client: Dict[str, Any], query: str) -> float:
        """
        Calcule un score de correspondance entre un client et une requête
        
        Args:
            client (dict): Données du client
            query (str): Texte de recherche
            
        Returns:
            float: Score de correspondance (0-1)
        """
        max_score = 0
        
        # Recherche dans les champs spécifiés
        for field in self.search_fields:
            if field in client and client[field]:
                field_value = str(client[field]).lower()
                
                # Correspondance exacte
                if query == field_value:
                    return 1.0
                
                # Correspondance de sous-chaîne
                if query in field_value:
                    # Le score dépend de la longueur relative
                    score = len(query) / len(field_value)
                    max_score = max(max_score, score)
                
                # Correspondance approximative avec difflib
                similarity = difflib.SequenceMatcher(None, query, field_value).ratio()
                max_score = max(max_score, similarity)
        
        return max_score
    
    def find_matching_clients(self, extracted_data: Dict[str, Any]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Recherche des clients correspondant aux données extraites
        
        Args:
            extracted_data (dict): Données extraites du document
            
        Returns:
            list: Liste de tuples (client, score) triés par score décroissant
        """
        matches = []
        
        # Si pas de données extraites ou pas de clients
        if not extracted_data or not self.clients_db:
            return []
        
        # Extraire les informations d'identification potentielles
        identifiers = self._extract_identifiers(extracted_data)
        
        # Si pas d'identifiants, retourner une liste vide
        if not identifiers:
            return []
        
        # Calculer les scores pour chaque client
        for client in self.clients_db:
            score = self._calculate_client_match_score(client, identifiers)
            if score >= self.match_threshold:
                matches.append((client, score))
        
        # Trier par score décroissant et limiter le nombre de résultats
        matches.sort(key=lambda x: x[1], reverse=True)
        matches = matches[:self.max_results]
        
        # Sauvegarder les résultats
        self.last_results = matches
        
        return matches
    
    def _extract_identifiers(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extrait les informations d'identification des données
        
        Args:
            data (dict): Données extraites
            
        Returns:
            dict: Informations d'identification
        """
        identifiers = {}
        
        # Parcourir les sections potentielles
        for section_name in ["personal_info", "professional_info", "parties", "document_info"]:
            section = data.get(section_name, {})
            if not section:
                continue
            
            # Extraire les champs d'identification
            for field in ["name", "first_name", "last_name", "email", "phone", "company"]:
                if field in section and section[field]:
                    identifiers[field] = str(section[field]).lower()
        
        # Traitement spécial pour les champs de nom
        if "first_name" in identifiers and "last_name" in identifiers:
            identifiers["full_name"] = f"{identifiers['first_name']} {identifiers['last_name']}".strip()
        
        # Rechercher directement dans toutes les sections pour certains champs clés
        self._find_fields_in_any_section(data, identifiers, ["email", "phone", "siret", "company"])
        
        return identifiers
    
    def _find_fields_in_any_section(self, data: Dict[str, Any], identifiers: Dict[str, str], fields: List[str]):
        """
        Recherche des champs spécifiques dans toutes les sections des données
        
        Args:
            data (dict): Données extraites
            identifiers (dict): Dictionnaire des identifiants à compléter
            fields (list): Liste des champs à rechercher
        """
        for section_name, section in data.items():
            if not isinstance(section, dict):
                continue
            
            for field in fields:
                # Ne pas écraser les valeurs déjà trouvées
                if field in identifiers and identifiers[field]:
                    continue
                
                if field in section and section[field]:
                    identifiers[field] = str(section[field]).lower()
                else:
                    # Recherche récursive dans les sous-sections
                    for sub_key, sub_value in section.items():
                        if isinstance(sub_value, dict) and field in sub_value and sub_value[field]:
                            identifiers[field] = str(sub_value[field]).lower()
                            break
    
    def _calculate_client_match_score(self, client: Dict[str, Any], identifiers: Dict[str, str]) -> float:
        """
        Calcule un score de correspondance entre un client et des identifiants
        
        Args:
            client (dict): Données du client
            identifiers (dict): Identifiants extraits
            
        Returns:
            float: Score de correspondance (0-1)
        """
        # Initialiser le score et les poids
        total_score = 0
        total_weight = 0
        
        # Poids des différents champs
        weights = {
            "email": 10,       # Email (identifiant fort)
            "phone": 8,        # Téléphone (identifiant fort)
            "siret": 10,       # SIRET (identifiant fort)
            "name": 7,         # Nom complet
            "full_name": 7,    # Nom complet (first_name + last_name)
            "first_name": 3,   # Prénom (partiel)
            "last_name": 4,    # Nom de famille (partiel)
            "company": 6       # Nom de l'entreprise
        }
        
        # Correspondances exactes pour certains identifiants forts
        for field in ["email", "phone", "siret"]:
            if field in identifiers and field in client and identifiers[field] and client[field]:
                # Normaliser les valeurs pour comparaison
                id_value = self._normalize_field(field, identifiers[field])
                client_value = self._normalize_field(field, str(client[field]).lower())
                
                # Si correspondance exacte pour un identifiant fort, score élevé
                if id_value == client_value:
                    return 0.95  # Quasiment certain
        
        # Champs de texte avec comparaison plus nuancée
        for field, weight in weights.items():
            # Vérifier que les deux valeurs existent
            id_value = identifiers.get(field, "")
            
            # Pour le champ 'name', essayer différentes combinaisons dans le client
            if field == "name":
                client_value = client.get("name", "").lower()
                if not client_value:
                    # Essayer de combiner first_name et last_name
                    first = client.get("first_name", "").lower()
                    last = client.get("last_name", "").lower()
                    if first or last:
                        client_value = f"{first} {last}".strip()
            elif field == "full_name":
                # Pour full_name, chercher dans le name du client
                client_value = client.get("name", "").lower()
                if not client_value:
                    # Ou combiner first_name et last_name
                    first = client.get("first_name", "").lower()
                    last = client.get("last_name", "").lower()
                    if first or last:
                        client_value = f"{first} {last}".strip()
            else:
                client_value = client.get(field, "").lower()
            
            # Si l'une des valeurs est manquante, ignorer
            if not id_value or not client_value:
                continue
            
            # Normaliser les valeurs pour comparaison
            id_value = self._normalize_field(field, id_value)
            client_value = self._normalize_field(field, client_value)
            
            # Calculer la similarité
            similarity = difflib.SequenceMatcher(None, id_value, client_value).ratio()
            
            # Pour les champs importants comme email et téléphone, être plus strict
            if field in ["email", "phone", "siret"]:
                # Vérifier que la similarité est très élevée
                if similarity >= 0.9:
                    score = similarity * weight
                else:
                    score = 0  # Pas de score partiel pour ces champs
            else:
                # Score pondéré pour les autres champs
                score = similarity * weight
            
            # Ajouter au score total
            total_score += score
            total_weight += weight
        
        # Calculer le score final normalisé
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 0
        
        return final_score
    
    def _normalize_field(self, field: str, value: str) -> str:
        """
        Normalise un champ pour la comparaison
        
        Args:
            field (str): Nom du champ
            value (str): Valeur à normaliser
            
        Returns:
            str: Valeur normalisée
        """
        if not value:
            return ""
        
        # Traitement selon le type de champ
        if field == "email":
            # Normaliser les emails (tout en minuscules, supprimer les espaces)
            return value.lower().strip().replace(" ", "")
        
        elif field == "phone":
            # Normaliser les numéros de téléphone (supprimer tous les non-chiffres)
            normalized = re.sub(r'\D', '', value)
            
            # Gérer les préfixes internationaux
            if normalized.startswith("33") and len(normalized) > 9:
                normalized = "0" + normalized[2:]
            
            return normalized
        
        elif field in ["name", "first_name", "last_name", "full_name", "company"]:
            # Normaliser les noms (minuscules, supprimer les caractères spéciaux)
            normalized = re.sub(r'[^\w\s]', '', value).lower()
            
            # Supprimer les espaces multiples
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            
            return normalized
        
        elif field == "siret":
            # Normaliser les SIRET (supprimer tous les non-chiffres)
            return re.sub(r'\D', '', value)
        
        # Par défaut, retourner la valeur en minuscules sans espaces excessifs
        return re.sub(r'\s+', ' ', value.lower()).strip()
    
    def get_best_match(self, extracted_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Récupère le client avec la meilleure correspondance
        
        Args:
            extracted_data (dict): Données extraites du document
            
        Returns:
            dict/None: Client avec la meilleure correspondance ou None
        """
        matches = self.find_matching_clients(extracted_data)
        
        if not matches:
            return None
        
        # Récupérer le client avec le score le plus élevé
        best_match = matches[0]
        
        # Vérifier que le score est suffisamment élevé
        if best_match[1] >= 0.8:  # Seuil de confiance élevé
            return best_match[0]
        
        return None
    
    def update_clients_db(self, clients_db: List[Dict[str, Any]]):
        """
        Met à jour la base de données des clients
        
        Args:
            clients_db (list): Nouvelle base de données des clients
        """
        self.clients_db = clients_db or []
        logger.info(f"Base de données clients mise à jour ({len(self.clients_db)} clients)")
    
    def add_client(self, client: Dict[str, Any]) -> bool:
        """
        Ajoute un nouveau client à la base de données
        
        Args:
            client (dict): Données du client
            
        Returns:
            bool: True si le client a été ajouté, False sinon
        """
        # Vérifier si le client existe déjà
        for existing_client in self.clients_db:
            # Vérifier par ID si disponible
            if "id" in existing_client and "id" in client and existing_client["id"] == client["id"]:
                return False
            
            # Vérifier par email si disponible
            if "email" in existing_client and "email" in client and existing_client["email"] and client["email"]:
                if existing_client["email"].lower() == client["email"].lower():
                    return False
        
        # Ajouter le client
        self.clients_db.append(client)
        return True
    
    def update_client(self, client: Dict[str, Any]) -> bool:
        """
        Met à jour un client existant
        
        Args:
            client (dict): Données mises à jour du client
            
        Returns:
            bool: True si le client a été mis à jour, False sinon
        """
        # Vérifier que le client a un ID
        if "id" not in client:
            return False
        
        # Rechercher le client
        for i, existing_client in enumerate(self.clients_db):
            if "id" in existing_client and existing_client["id"] == client["id"]:
                # Mettre à jour le client
                self.clients_db[i] = client
                return True
        
        return False
    
    def remove_client(self, client_id: str) -> bool:
        """
        Supprime un client de la base de données
        
        Args:
            client_id (str): ID du client à supprimer
            
        Returns:
            bool: True si le client a été supprimé, False sinon
        """
        # Rechercher le client
        for i, client in enumerate(self.clients_db):
            if "id" in client and client["id"] == client_id:
                # Supprimer le client
                del self.clients_db[i]
                return True
        
        return False


# Fonctions utilitaires pour utilisation directe
def find_matching_clients(extracted_data: Dict[str, Any], clients_db: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], float]]:
    """
    Recherche des clients correspondant aux données extraites
    
    Args:
        extracted_data (dict): Données extraites du document
        clients_db (list): Base de données des clients
        
    Returns:
        list: Liste de tuples (client, score) triés par score décroissant
    """
    matcher = ClientMatcher(clients_db)
    return matcher.find_matching_clients(extracted_data)

def get_best_client_match(extracted_data: Dict[str, Any], clients_db: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Récupère le client avec la meilleure correspondance
    
    Args:
        extracted_data (dict): Données extraites du document
        clients_db (list): Base de données des clients
        
    Returns:
        dict/None: Client avec la meilleure correspondance ou None
    """
    matcher = ClientMatcher(clients_db)
    return matcher.get_best_match(extracted_data)