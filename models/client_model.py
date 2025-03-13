#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Clients Model for Vynal Docs Automator

Ce module gère les données des clients, notamment le chargement depuis
un fichier JSON, la validation, la sauvegarde et les opérations CRUD.
"""

import os
import json
import logging
import uuid
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger("VynalDocsAutomator.ClientsModel")

class ClientsModel:
    """
    ClientsModel gère les données clients pour Vynal Docs Automator.

    Attributes:
        clients: Liste des clients.
        base_dir: Répertoire de base de l'application.
        data_dir: Répertoire de stockage des clients.
        file_path: Chemin complet vers le fichier JSON des clients.
        config: (Optionnel) Dictionnaire de configuration, pouvant contenir
                des paramètres comme "max_recent_activities" si nécessaire.
    """
    
    def __init__(self, base_dir: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialise le modèle des clients.

        Args:
            base_dir: Répertoire de base de l'application.
            config: Dictionnaire de configuration optionnel.
        """
        self.config = config or {}
        self.base_dir = base_dir
        self.data_dir = os.path.join(self.base_dir, "data", "clients")
        os.makedirs(self.data_dir, exist_ok=True)
        self.file_path = os.path.join(self.data_dir, "clients.json")
        self.clients: List[Dict[str, Any]] = []
        self.load_clients()
    
    def load_clients(self) -> None:
        """
        Charge les données clients depuis le fichier JSON.
        """
        if not os.path.exists(self.file_path):
            # Crée un fichier vide s'il n'existe pas.
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
            self.clients = []
            logger.info("Clients file created: %s", self.file_path)
            return
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.clients = json.load(f)
            self._validate_clients()
            logger.info("%d clients loaded", len(self.clients))
        except json.JSONDecodeError as e:
            logger.error("JSON decode error while loading clients: %s", e)
            backup_file = f"{self.file_path}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.copy2(self.file_path, backup_file)
            logger.info("Backup created for corrupted clients file: %s", backup_file)
            self.clients = []
        except Exception as e:
            logger.error("Error loading clients: %s", e)
            self.clients = []
    
    def _validate_clients(self) -> None:
        """
        Valide et corrige les données clients pour s'assurer qu'elles sont conformes.
        Seuls les enregistrements de type dictionnaire contenant au moins un 'id',
        un 'name' et un 'email' sont conservés.
        """
        valid_clients = []
        for client in self.clients:
            if not isinstance(client, dict):
                logger.warning("Ignored client (not a dict): %s", client)
                continue
            if not client.get('id') or not client.get('name') or not client.get('email'):
                logger.warning("Ignored client (missing required fields): %s", client)
                continue
            valid_client = {
                'id': client.get('id'),
                'name': client.get('name', '').strip(),
                'company': client.get('company', '').strip(),
                'email': client.get('email', '').strip(),
                'phone': client.get('phone', '').strip(),
                'address': client.get('address', '').strip(),
                'created_at': client.get('created_at', datetime.now().isoformat()),
                'updated_at': client.get('updated_at', datetime.now().isoformat())
            }
            valid_clients.append(valid_client)
        
        # Si des corrections ont été apportées, sauvegarder la version corrigée.
        if len(valid_clients) != len(self.clients):
            logger.info("Client data corrected: %d -> %d", len(self.clients), len(valid_clients))
            self.clients = valid_clients
            self.save_clients()
        else:
            self.clients = valid_clients
    
    def save_clients(self) -> bool:
        """
        Sauvegarde les données clients dans le fichier JSON.

        Returns:
            True si l'opération réussit, False sinon.
        """
        try:
            temp_file = f"{self.file_path}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.clients, f, indent=2, ensure_ascii=False)
            if os.path.exists(self.file_path):
                os.replace(temp_file, self.file_path)
            else:
                os.rename(temp_file, self.file_path)
            logger.info("%d clients saved", len(self.clients))
            return True
        except Exception as e:
            logger.error("Error saving clients: %s", e)
            return False
    
    def add_client(self, client_data: Dict[str, Any]) -> Optional[str]:
        """
        Ajoute un nouveau client.

        Args:
            client_data: Dictionnaire contenant les informations du client.

        Returns:
            L'ID du client ajouté, ou None en cas d'erreur.
        """
        if 'name' not in client_data or not client_data['name'].strip():
            logger.warning("Attempt to add client without a name")
            return None
        if 'email' not in client_data or not client_data['email'].strip():
            logger.warning("Attempt to add client without an email")
            return None
        
        # Vérifier si un client existe déjà avec le même email
        existing = next((c for c in self.clients if c.get('email') == client_data.get('email')), None)
        if existing:
            logger.warning("Client with email %s already exists", client_data.get('email'))
            return None
        
        client_id = str(uuid.uuid4())
        new_client = {
            'id': client_id,
            'name': client_data.get('name', '').strip(),
            'company': client_data.get('company', '').strip(),
            'email': client_data.get('email', '').strip(),
            'phone': client_data.get('phone', '').strip(),
            'address': client_data.get('address', '').strip(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self.clients.append(new_client)
        self.save_clients()
        logger.info("Client added: %s (ID: %s)", new_client.get('name'), client_id)
        return client_id
    
    def update_client(self, client_id: str, client_data: Dict[str, Any]) -> bool:
        """
        Met à jour un client existant.

        Args:
            client_id: ID du client à mettre à jour.
            client_data: Nouvelles données du client.

        Returns:
            True si la mise à jour réussit, False sinon.
        """
        if 'name' not in client_data or not client_data['name'].strip():
            logger.warning("Attempt to update client without a name")
            return False
        if 'email' not in client_data or not client_data['email'].strip():
            logger.warning("Attempt to update client without an email")
            return False
        
        index = next((i for i, c in enumerate(self.clients) if c.get('id') == client_id), None)
        if index is None:
            logger.warning("Client with ID %s not found", client_id)
            return False
        
        # Vérifier si l'email est déjà utilisé par un autre client
        if any(c.get('email') == client_data.get('email') and c.get('id') != client_id for c in self.clients):
            logger.warning("Email %s already used by another client", client_data.get('email'))
            return False
        
        existing = self.clients[index]
        updated_client = {
            'id': client_id,
            'name': client_data.get('name', '').strip(),
            'company': client_data.get('company', '').strip(),
            'email': client_data.get('email', '').strip(),
            'phone': client_data.get('phone', '').strip(),
            'address': client_data.get('address', '').strip(),
            'created_at': existing.get('created_at', datetime.now().isoformat()),
            'updated_at': datetime.now().isoformat()
        }
        self.clients[index] = updated_client
        self.save_clients()
        logger.info("Client updated: %s (ID: %s)", updated_client.get('name'), client_id)
        return True
    
    def delete_client(self, client_id: str) -> bool:
        """
        Supprime un client.

        Args:
            client_id: ID du client à supprimer.

        Returns:
            True si la suppression réussit, False sinon.
        """
        client = next((c for c in self.clients if c.get('id') == client_id), None)
        if client is None:
            logger.warning("Client with ID %s not found", client_id)
            return False
        self.clients = [c for c in self.clients if c.get('id') != client_id]
        self.save_clients()
        logger.info("Client deleted: %s (ID: %s)", client.get('name'), client_id)
        return True
    
    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un client par son ID.

        Args:
            client_id: ID du client.

        Returns:
            Une copie des données du client, ou None si non trouvé.
        """
        client = next((c for c in self.clients if c.get('id') == client_id), None)
        return client.copy() if client else None
    
    def get_all_clients(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les clients.

        Returns:
            Une liste de copies de tous les clients.
        """
        return [c.copy() for c in self.clients]
    
    def search_clients(self, query: str) -> List[Dict[str, Any]]:
        """
        Recherche des clients par nom, entreprise ou email.

        Args:
            query: Terme de recherche.

        Returns:
            Une liste de clients correspondant au terme recherché.
        """
        query = query.lower()
        results = []
        for client in self.clients:
            if (query in client.get('name', '').lower() or
                query in client.get('company', '').lower() or
                query in client.get('email', '').lower()):
                results.append(client.copy())
        return results

# Si besoin, vous pouvez ajouter ici des méthodes supplémentaires liées aux activités,
# à la sauvegarde, l'import/export ou la migration des données clients.
