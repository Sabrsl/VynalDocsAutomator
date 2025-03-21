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
from functools import lru_cache
from utils.cache_manager import CacheManager
from utils.lazy_loader import LazyModelLoader, ModelType, ModelMetadata

logger = logging.getLogger("VynalDocsAutomator.ClientsModel")

class ClientsModel:
    """
    ClientsModel gère les données clients pour Vynal Docs Automator.

    Attributes:
        clients: Liste des clients.
        base_dir: Répertoire de base de l'application.
        data_dir: Répertoire de stockage des clients.
        file_path: Chemin complet vers le fichier JSON des clients.
        config: (Optionnel) Dictionnaire de configuration.
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
        
        # Initialisation avec chargement paresseux
        self._clients = None
        
        # Initialisation des gestionnaires de cache
        self.cache_manager = CacheManager()
        self.lazy_loader = LazyModelLoader(
            cache_ttl=self.config.get('cache_ttl', 3600),
            max_cache_size=self.config.get('max_cache_size', 1000)
        )
        
        # Enregistrement des callbacks pour le chargement différé
        self.lazy_loader.register_callbacks(
            ModelType.CLIENT,
            self._load_client_by_id,
            self._load_client_metadata
        )
        
    def _create_metadata(self, client: Dict[str, Any]) -> ModelMetadata:
        """Crée les métadonnées pour un client."""
        return ModelMetadata(
            id=str(client['id']),
            name=client['name'],
            type=ModelType.CLIENT,
            created_at=client['created_at'],
            updated_at=client['updated_at'],
            summary=f"{client['name']} - {client.get('company', '')}"
        )
        
    def _load_client_metadata(self) -> List[ModelMetadata]:
        """Charge les métadonnées des clients."""
        clients = self._load_clients()
        return [self._create_metadata(client) for client in clients]
        
    def _load_client_by_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Charge un client spécifique par son ID."""
        client = next((c for c in self._load_clients() if c.get('id') == client_id), None)
        return client.copy() if client else None
    
    @property
    def clients(self) -> List[Dict[str, Any]]:
        """Liste des clients avec chargement différé."""
        if self._clients is None:
            self._clients = self._load_clients()
        return self._clients
    
    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un client par son ID avec chargement différé.
        
        Args:
            client_id: ID du client
            
        Returns:
            Données du client ou None si non trouvé
        """
        # Vérifie d'abord les métadonnées
        metadata = self.lazy_loader.get_metadata(ModelType.CLIENT, client_id)
        if not metadata:
            return None
            
        # Charge les données complètes si nécessaire
        return self.lazy_loader.get_model(ModelType.CLIENT, client_id)
    
    def search_clients(self, query: str) -> List[Dict[str, Any]]:
        """
        Recherche des clients avec optimisation.
        
        Args:
            query: Terme de recherche
            
        Returns:
            Liste des clients correspondants
        """
        # Charge d'abord les métadonnées
        metadata_list = self.lazy_loader.load_metadata(ModelType.CLIENT)
        query = query.lower()
        
        # Filtre sur les métadonnées
        matching_ids = [
            meta.id for meta in metadata_list
            if query in meta.name.lower() or query in meta.summary.lower()
        ]
        
        # Charge les données complètes uniquement pour les correspondances
        results = []
        for client_id in matching_ids:
            client = self.lazy_loader.get_model(ModelType.CLIENT, client_id)
            if client:
                results.append(client)
                
        return results
    
    def _load_clients(self) -> List[Dict[str, Any]]:
        """Charge les clients depuis le fichier JSON."""
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
            return []
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                clients = json.load(f)
            self._validate_clients(clients)
            return clients
        except Exception as e:
            logger.error("Error loading clients: %s", e)
            return []
    
    def _validate_clients(self, clients: List[Dict[str, Any]]) -> None:
        """Valide et corrige les données clients."""
        valid_clients = []
        for client in clients:
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
        
        if len(valid_clients) != len(clients):
            logger.info("Client data corrected: %d -> %d", len(clients), len(valid_clients))
            self._save_clients(valid_clients)
        clients[:] = valid_clients
    
    def _save_clients(self, clients: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Sauvegarde les clients dans le fichier JSON."""
        if clients is None:
            clients = self.clients
        
        try:
            temp_file = f"{self.file_path}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(clients, f, indent=2, ensure_ascii=False)
            if os.path.exists(self.file_path):
                os.replace(temp_file, self.file_path)
            else:
                os.rename(temp_file, self.file_path)
            logger.info("%d clients saved", len(clients))
            return True
        except Exception as e:
            logger.error("Error saving clients: %s", e)
            return False
    
    def add_client(self, client_data: Dict[str, Any]) -> Optional[str]:
        """Ajoute un nouveau client avec mise en cache."""
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
        self._save_clients()
        
        # Invalider les caches
        self.cache_manager.invalidate("clients", "all")
        self.get_client.cache_clear()
        self.search_clients.cache_clear()
        
        logger.info("Client added: %s (ID: %s)", new_client.get('name'), client_id)
        return client_id
    
    def update_client(self, client_id: str, client_data: Dict[str, Any]) -> bool:
        """Met à jour un client existant avec mise en cache."""
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
        self._save_clients()
        
        # Invalider les caches
        self.cache_manager.invalidate("clients", "all")
        self.cache_manager.invalidate("clients", client_id)
        self.get_client.cache_clear()
        self.search_clients.cache_clear()
        
        logger.info("Client updated: %s (ID: %s)", updated_client.get('name'), client_id)
        return True
    
    def delete_client(self, client_id: str) -> bool:
        """Supprime un client avec invalidation du cache."""
        client = next((c for c in self.clients if c.get('id') == client_id), None)
        if client is None:
            logger.warning("Client with ID %s not found", client_id)
            return False
        
        self.clients[:] = [c for c in self.clients if c.get('id') != client_id]
        self._save_clients()
        
        # Invalider les caches
        self.cache_manager.invalidate("clients", "all")
        self.cache_manager.invalidate("clients", client_id)
        self.get_client.cache_clear()
        self.search_clients.cache_clear()
        
        logger.info("Client deleted: %s (ID: %s)", client.get('name'), client_id)
        return True
    
    def get_all_clients(self) -> List[Dict[str, Any]]:
        """Récupère tous les clients avec mise en cache."""
        return [c.copy() for c in self.clients]
    
    def cleanup(self):
        """Nettoie les ressources du modèle."""
        # Nettoyer les caches
        self.cache_manager.cleanup()
        self.get_client.cache_clear()
        self.search_clients.cache_clear()

# Si besoin, vous pouvez ajouter ici des méthodes supplémentaires liées aux activités,
# à la sauvegarde, l'import/export ou la migration des données clients.
