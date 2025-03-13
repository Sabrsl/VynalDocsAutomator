#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modèle principal de l'application Vynal Docs Automator
Contient les fonctionnalités de base et la gestion des données
"""

import os
import json
import logging
import uuid
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from utils.cache_manager import CacheManager
import time
import threading

logger = logging.getLogger("VynalDocsAutomator.AppModel")

class AppModel:
    """
    Modèle principal contenant les données et la logique métier de l'application
    
    Attributes:
        config: Gestionnaire de configuration de l'application
        cache_manager: Gestionnaire de cache pour les données
        clients: Liste des clients
        templates: Liste des modèles de documents
        documents: Liste des documents
        recent_activities: Liste des activités récentes
        paths: Dictionnaire des chemins vers les différents répertoires
    """
    
    def __init__(self, config_manager):
        """
        Initialise le modèle de l'application
        
        Args:
            config_manager: Gestionnaire de configuration de l'application
        """
        self.config = config_manager
        self.cache_manager = CacheManager()
        self.clients = []
        self.templates = []
        self.documents = []
        self.recent_activities = []
        
        # Obtenir le répertoire de base pour le stockage des données
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        
        # Chemins des dossiers de données
        self.paths = {
            'clients': os.path.join(self.data_dir, "clients"),
            'templates': os.path.join(self.data_dir, "templates"),
            'documents': os.path.join(self.data_dir, "documents"),
            'backup': os.path.join(self.data_dir, "backup")
        }
        
        # S'assurer que les dossiers existent
        for path in self.paths.values():
            os.makedirs(path, exist_ok=True)
        
        # Initialiser le gestionnaire de cache avec les paramètres optimisés
        self.cache_manager = CacheManager()
        
        # Cache pour les requêtes fréquentes
        self._document_type_cache = {}
        self._client_document_cache = {}
        self._search_cache = {}
        
        # Paramètres de performance
        self._bulk_load_size = 50  # Nombre de documents à charger par lot
        self._cache_cleanup_interval = 300  # Intervalle de nettoyage du cache en secondes
        
        # Démarrer le nettoyage périodique du cache
        self._start_cache_cleanup()
        
        # Charger les données
        self.load_all_data()
        
        logger.info("AppModel initialisé")
    
    def _start_cache_cleanup(self):
        """Démarre le nettoyage périodique du cache"""
        def cleanup():
            while True:
                try:
                    self.cache_manager.cleanup()
                    self._cleanup_local_caches()
                    time.sleep(self._cache_cleanup_interval)
                except Exception as e:
                    logger.error(f"Erreur lors du nettoyage du cache: {e}")
                    time.sleep(60)  # Attendre avant de réessayer
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_local_caches(self):
        """Nettoie les caches locaux"""
        current_time = time.time()
        
        # Nettoyer le cache des types de documents
        self._document_type_cache = {
            k: v for k, v in self._document_type_cache.items()
            if current_time - v.get('timestamp', 0) < 3600
        }
        
        # Nettoyer le cache des documents par client
        self._client_document_cache = {
            k: v for k, v in self._client_document_cache.items()
            if current_time - v.get('timestamp', 0) < 1800
        }
        
        # Nettoyer le cache de recherche
        self._search_cache = {
            k: v for k, v in self._search_cache.items()
            if current_time - v.get('timestamp', 0) < 300
        }
    
    def load_all_data(self) -> None:
        """
        Charge toutes les données nécessaires au démarrage
        """
        try:
            self.load_clients()
            self.load_templates()
            self.load_documents()
            self.load_recent_activities()
            
            logger.info("Toutes les données ont été chargées")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données: {e}")
            logger.info("Utilisation de données par défaut")
    
    def add_activity(self, activity_type: str, description: str) -> None:
        """
        Ajoute une activité récente
        
        Args:
            activity_type: Type d'activité (ex: 'client', 'document', 'template')
            description: Description de l'activité
        """
        activity = {
            'id': str(uuid.uuid4()),
            'type': activity_type,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }
        
        self.recent_activities.insert(0, activity)
        
        # Limiter à un nombre configurable d'activités récentes
        max_activities = self.config.get("max_recent_activities", 50)
        if len(self.recent_activities) > max_activities:
            self.recent_activities = self.recent_activities[:max_activities]
        
        # Sauvegarder les activités
        self.save_recent_activities()
        
        logger.info(f"Nouvelle activité ajoutée: {description}")
    
    # ---- Gestion des clients ----
    
    def load_clients(self) -> None:
        """
        Charge les données clients depuis le fichier
        """
        client_file = os.path.join(self.paths['clients'], "clients.json")
        
        if not os.path.exists(client_file):
            # Créer un fichier vide
            with open(client_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            
            self.clients = []
            logger.info("Fichier clients.json créé")
            return
        
        try:
            with open(client_file, 'r', encoding='utf-8') as f:
                self.clients = json.load(f)
            
            # Validation des données clients
            self._validate_clients()
            
            logger.info(f"{len(self.clients)} clients chargés")
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de format JSON lors du chargement des clients: {e}")
            # Créer un backup du fichier corrompu
            if os.path.exists(client_file):
                backup_file = f"{client_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                shutil.copy2(client_file, backup_file)
                logger.info(f"Sauvegarde du fichier clients corrompu créée: {backup_file}")
            self.clients = []
        except Exception as e:
            logger.error(f"Erreur lors du chargement des clients: {e}")
            self.clients = []
    
    def _validate_clients(self) -> None:
        """
        Valide et corrige les données clients pour s'assurer qu'elles sont conformes
        """
        valid_clients = []
        
        for client in self.clients:
            # Vérifier que c'est un dictionnaire
            if not isinstance(client, dict):
                logger.warning(f"Client ignoré car ce n'est pas un dictionnaire: {client}")
                continue
            
            # Vérifier la présence des champs obligatoires
            if not client.get('id') or not client.get('name') or not client.get('email'):
                logger.warning(f"Client ignoré car il manque des champs obligatoires: {client}")
                continue
            
            # S'assurer que tous les champs nécessaires sont présents
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
        
        self.clients = valid_clients
        
        # Si des corrections ont été apportées, sauvegarder les données
        if len(valid_clients) != len(self.clients):
            logger.info(f"Données clients corrigées: {len(self.clients)} -> {len(valid_clients)}")
            self.save_clients()
    
    def save_clients(self) -> bool:
        """
        Sauvegarde les données clients dans le fichier
        
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        client_file = os.path.join(self.paths['clients'], "clients.json")
        
        try:
            # Créer un fichier temporaire d'abord
            temp_file = f"{client_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.clients, f, indent=2, ensure_ascii=False)
            
            # Remplacer l'ancien fichier par le nouveau
            if os.path.exists(client_file):
                os.replace(temp_file, client_file)
            else:
                os.rename(temp_file, client_file)
            
            logger.info(f"{len(self.clients)} clients sauvegardés")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des clients: {e}")
            return False
    
    def add_client(self, client_data: Dict[str, Any]) -> Optional[str]:
        """
        Ajoute un nouveau client
        
        Args:
            client_data: Dictionnaire avec les données du client
        
        Returns:
            str: ID du client ajouté ou None en cas d'erreur
        """
        # Vérification des champs obligatoires
        if 'name' not in client_data or not client_data['name'].strip():
            logger.warning("Tentative d'ajout d'un client sans nom")
            return None
        
        if 'email' not in client_data or not client_data['email'].strip():
            logger.warning("Tentative d'ajout d'un client sans email")
            return None
        
        # Vérifier si le client existe déjà (par email)
        existing = next((c for c in self.clients if c.get('email') == client_data.get('email')), None)
        
        if existing:
            logger.warning(f"Client avec email {client_data.get('email')} existe déjà")
            return None
        
        # Générer un ID unique
        client_id = str(uuid.uuid4())
        
        # Nettoyer et valider les données
        clean_data = {
            'id': client_id,
            'name': client_data.get('name', '').strip(),
            'company': client_data.get('company', '').strip(),
            'email': client_data.get('email', '').strip(),
            'phone': client_data.get('phone', '').strip(),
            'address': client_data.get('address', '').strip(),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Ajouter à la liste
        self.clients.append(clean_data)
        
        # Sauvegarder
        self.save_clients()
        
        # Ajouter l'activité
        self.add_activity('client', f"Nouveau client ajouté: {clean_data.get('name')}")
        
        logger.info(f"Client ajouté: {clean_data.get('name')} (ID: {client_id})")
        return client_id
    
    def update_client(self, client_id: str, client_data: Dict[str, Any]) -> bool:
        """
        Met à jour un client existant
        
        Args:
            client_id: ID du client à mettre à jour
            client_data: Nouvelles données du client
        
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        # Vérification des champs obligatoires
        if 'name' not in client_data or not client_data['name'].strip():
            logger.warning("Tentative de mise à jour d'un client sans nom")
            return False
        
        if 'email' not in client_data or not client_data['email'].strip():
            logger.warning("Tentative de mise à jour d'un client sans email")
            return False
        
        # Trouver le client
        client_index = next((i for i, c in enumerate(self.clients) if c.get('id') == client_id), None)
        
        if client_index is None:
            logger.warning(f"Client avec ID {client_id} non trouvé")
            return False
        
        # Vérifier si l'email est déjà utilisé par un autre client
        existing_email = next((c for c in self.clients if c.get('email') == client_data.get('email') and c.get('id') != client_id), None)
        if existing_email:
            logger.warning(f"Email {client_data.get('email')} déjà utilisé par un autre client")
            return False
        
        # Obtenir les données existantes
        existing_data = self.clients[client_index]
        
        # Mettre à jour les données
        updated_data = {
            'id': client_id,
            'name': client_data.get('name', '').strip(),
            'company': client_data.get('company', '').strip(),
            'email': client_data.get('email', '').strip(),
            'phone': client_data.get('phone', '').strip(),
            'address': client_data.get('address', '').strip(),
            'created_at': existing_data.get('created_at', datetime.now().isoformat()),
            'updated_at': datetime.now().isoformat()
        }
        
        # Remplacer le client
        self.clients[client_index] = updated_data
        
        # Sauvegarder
        self.save_clients()
        
        # Ajouter l'activité
        self.add_activity('client', f"Client mis à jour: {updated_data.get('name')}")
        
        logger.info(f"Client mis à jour: {updated_data.get('name')} (ID: {client_id})")
        return True
    
    def delete_client(self, client_id: str) -> bool:
        """
        Supprime un client
        
        Args:
            client_id: ID du client à supprimer
        
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        # Trouver le client
        client = next((c for c in self.clients if c.get('id') == client_id), None)
        
        if client is None:
            logger.warning(f"Client avec ID {client_id} non trouvé")
            return False
        
        # Vérifier si des documents sont liés à ce client
        linked_docs = [d for d in self.documents if d.get('client_id') == client_id]
        if linked_docs:
            logger.warning(f"Client avec ID {client_id} a {len(linked_docs)} documents liés")
            # Mettre à jour les documents pour enlever la référence au client
            for doc in linked_docs:
                doc['client_id'] = None
                doc['updated_at'] = datetime.now().isoformat()
            
            # Sauvegarder les documents mis à jour
            self.save_documents()
        
        # Supprimer le client
        self.clients = [c for c in self.clients if c.get('id') != client_id]
        
        # Sauvegarder
        self.save_clients()
        
        # Ajouter l'activité
        self.add_activity('client', f"Client supprimé: {client.get('name')}")
        
        logger.info(f"Client supprimé: {client.get('name')} (ID: {client_id})")
        return True
    
    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un client avec mise en cache"""
        # Essayer de récupérer depuis le cache
        cached_client = self.cache_manager.get("clients", client_id)
        if cached_client is not None:
            return cached_client

        # Si pas dans le cache, chercher dans la liste
        client = next((c for c in self.clients if c.get('id') == client_id), None)
        if client is not None:
            # Mettre en cache pour les prochaines fois
            self.cache_manager.set("clients", client_id, client)
        return client
    
    def get_all_clients(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les clients
        
        Returns:
            list: Liste de tous les clients (copie pour éviter les modifications involontaires)
        """
        return [c.copy() for c in self.clients]
    
    def search_clients(self, query: str) -> List[Dict[str, Any]]:
        """
        Recherche des clients par nom, entreprise ou email
        
        Args:
            query: Terme de recherche
        
        Returns:
            list: Liste des clients correspondant à la recherche
        """
        query = query.lower()
        results = []
        
        for client in self.clients:
            if (query in client.get('name', '').lower() or
                query in client.get('company', '').lower() or
                query in client.get('email', '').lower()):
                results.append(client.copy())
        
        return results
    
    # ---- Gestion des modèles de documents ----
    
    def load_templates(self) -> None:
        """
        Charge les modèles de documents
        """
        template_file = os.path.join(self.paths['templates'], "templates.json")
        
        if not os.path.exists(template_file):
            # Créer un fichier vide
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            
            self.templates = []
            logger.info("Fichier templates.json créé")
            return
        
        try:
            # Lire le fichier
            with open(template_file, 'r', encoding='utf-8') as f:
                self.templates = json.load(f)
            
            # Validation des données des modèles
            self._validate_templates()
            
            logger.info(f"{len(self.templates)} modèles chargés")
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de format JSON lors du chargement des modèles: {e}")
            # Créer un backup du fichier corrompu
            if os.path.exists(template_file):
                backup_file = f"{template_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                shutil.copy2(template_file, backup_file)
                logger.info(f"Sauvegarde du fichier templates corrompu créée: {backup_file}")
            self.templates = []
        except Exception as e:
            logger.error(f"Erreur lors du chargement des modèles: {e}")
            self.templates = []
    
    def _validate_templates(self) -> None:
        """
        Valide et corrige les données des modèles pour s'assurer qu'elles sont conformes
        """
        valid_templates = []
        
        for template in self.templates:
            try:
                # Vérifier que c'est un dictionnaire
                if not isinstance(template, dict):
                    logger.warning(f"Modèle ignoré car ce n'est pas un dictionnaire: {template}")
                    continue
                
                # Vérifier la présence des champs obligatoires
                if not template.get('id') or not template.get('name') or not template.get('content'):
                    logger.warning(f"Modèle ignoré car il manque des champs obligatoires: {template}")
                    continue
                
                # S'assurer que tous les champs nécessaires sont présents
                valid_template = {
                    'id': template.get('id'),
                    'name': template.get('name', '').strip(),
                    'type': template.get('type', '').strip().lower(),
                    'description': template.get('description', '').strip(),
                    'content': template.get('content', ''),
                    'variables': template.get('variables', []),
                    'created_at': template.get('created_at', datetime.now().isoformat()),
                    'updated_at': template.get('updated_at', datetime.now().isoformat())
                }
                
                # S'assurer que variables est une liste
                if not isinstance(valid_template['variables'], list):
                    valid_template['variables'] = []
                
                # S'assurer que le contenu est une chaîne de caractères
                if not isinstance(valid_template['content'], str):
                    valid_template['content'] = str(valid_template['content'])
                
                valid_templates.append(valid_template)
            except Exception as e:
                logger.error(f"Erreur lors de la validation d'un modèle: {e}")
                continue
        
        self.templates = valid_templates
        
        # Si des corrections ont été apportées, sauvegarder les données
        if len(valid_templates) != len(self.templates):
            logger.info(f"Données des modèles corrigées: {len(self.templates)} -> {len(valid_templates)}")
            self.save_templates()
    
    def save_templates(self):
        """
        Sauvegarde les modèles dans le fichier JSON
        
        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        try:
            # Créer le chemin du fichier temporaire
            temp_file = os.path.join(self.paths['templates'], 'templates_temp.json')
            final_file = os.path.join(self.paths['templates'], 'templates.json')
            
            # S'assurer que le dossier existe
            os.makedirs(self.paths['templates'], exist_ok=True)
            
            # Sauvegarder dans un fichier temporaire
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=4)
            
            # Si le fichier final existe, le supprimer
            if os.path.exists(final_file):
                os.remove(final_file)
            
            # Renommer le fichier temporaire
            os.rename(temp_file, final_file)
            
            logger.info("Modèles sauvegardés avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des modèles: {e}")
            # Nettoyer le fichier temporaire s'il existe
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return False
    
    def add_template(self, template_data: Dict[str, Any]) -> Optional[str]:
        """
        Ajoute un nouveau modèle de document
        
        Args:
            template_data: Données du modèle
        
        Returns:
            str: ID du modèle ajouté ou None en cas d'erreur
        """
        # Vérification des champs obligatoires
        if 'name' not in template_data or not template_data['name'].strip():
            logger.warning("Tentative d'ajout d'un modèle sans nom")
            return None
        
        if 'content' not in template_data or not template_data['content'].strip():
            logger.warning("Tentative d'ajout d'un modèle sans contenu")
            return None
        
        # Générer un ID unique
        template_id = str(uuid.uuid4())
        
        # Nettoyer et valider les données
        clean_data = {
            'id': template_id,
            'name': template_data.get('name', '').strip(),
            'type': template_data.get('type', '').strip().lower(),
            'description': template_data.get('description', '').strip(),
            'content': template_data.get('content', '').strip(),
            'variables': template_data.get('variables', []),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # S'assurer que variables est une liste
        if not isinstance(clean_data['variables'], list):
            clean_data['variables'] = []
        
        # Ajouter à la liste
        self.templates.append(clean_data)
        
        # Sauvegarder
        self.save_templates()
        
        # Ajouter l'activité
        self.add_activity('template', f"Nouveau modèle créé: {clean_data.get('name')}")
        
        logger.info(f"Modèle ajouté: {clean_data.get('name')} (ID: {template_id})")
        return template_id
    
    def update_template(self, template_id: str, template_data: Dict[str, Any]) -> bool:
        """
        Met à jour un modèle existant
        
        Args:
            template_id: ID du modèle à mettre à jour
            template_data: Nouvelles données du modèle
        
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        try:
            # Vérification des champs obligatoires
            if 'name' not in template_data or not template_data['name'].strip():
                logger.warning("Tentative de mise à jour d'un modèle sans nom")
                return False
            
            if 'content' not in template_data or not template_data['content'].strip():
                logger.warning("Tentative de mise à jour d'un modèle sans contenu")
                return False
            
            # Trouver le modèle
            template_index = next((i for i, t in enumerate(self.templates) if t.get('id') == template_id), None)
            
            if template_index is None:
                logger.warning(f"Modèle avec ID {template_id} non trouvé")
                return False
            
            # Obtenir les données existantes
            existing_data = self.templates[template_index]
            
            # Mettre à jour les données
            updated_data = {
                'id': template_id,
                'name': template_data.get('name', '').strip(),
                'type': template_data.get('type', '').strip().lower(),
                'description': template_data.get('description', '').strip(),
                'content': template_data.get('content', '').strip(),
                'variables': template_data.get('variables', existing_data.get('variables', [])),
                'created_at': existing_data.get('created_at', datetime.now().isoformat()),
                'updated_at': datetime.now().isoformat()
            }
            
            # S'assurer que variables est une liste
            if not isinstance(updated_data['variables'], list):
                updated_data['variables'] = []
            
            # Remplacer le modèle
            self.templates[template_index] = updated_data
            
            # Sauvegarder
            if not self.save_templates():
                logger.error("Échec de la sauvegarde des modèles")
                return False
            
            # Ajouter l'activité
            self.add_activity('template', f"Modèle mis à jour: {updated_data.get('name')}")
            
            logger.info(f"Modèle mis à jour: {updated_data.get('name')} (ID: {template_id})")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du modèle: {e}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """
        Supprime un modèle
        
        Args:
            template_id: ID du modèle à supprimer
        
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        # Trouver le modèle
        template = next((t for t in self.templates if t.get('id') == template_id), None)
        
        if template is None:
            logger.warning(f"Modèle avec ID {template_id} non trouvé")
            return False
        
        # Vérifier si des documents sont liés à ce modèle
        linked_docs = [d for d in self.documents if d.get('template_id') == template_id]
        if linked_docs:
            logger.warning(f"Modèle avec ID {template_id} a {len(linked_docs)} documents liés")
            # On pourrait soit refuser la suppression, soit mettre à jour les documents
            
            # Mettre à jour les documents pour enlever la référence au modèle
            for doc in linked_docs:
                doc['template_id'] = None
                doc['updated_at'] = datetime.now().isoformat()
            
            # Sauvegarder les documents mis à jour
            self.save_documents()
        
        # Supprimer le modèle
        self.templates = [t for t in self.templates if t.get('id') != template_id]
        
        # Sauvegarder
        self.save_templates()
        
        # Ajouter l'activité
        self.add_activity('template', f"Modèle supprimé: {template.get('name')}")
        
        logger.info(f"Modèle supprimé: {template.get('name')} (ID: {template_id})")
        return True
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un template avec mise en cache"""
        cached_template = self.cache_manager.get("templates", template_id)
        if cached_template is not None:
            return cached_template

        template = next((t for t in self.templates if t["id"] == template_id), None)
        if template is not None:
            self.cache_manager.set("templates", template_id, template)
        return template
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les modèles
        
        Returns:
            list: Liste de tous les modèles
        """
        return [t.copy() for t in self.templates]
    
    def search_templates(self, query: str) -> List[Dict[str, Any]]:
        """
        Recherche des modèles par nom, type ou description
        
        Args:
            query: Terme de recherche
        
        Returns:
            list: Liste des modèles correspondant à la recherche
        """
        query = query.lower()
        results = []
        
        for template in self.templates:
            if (query in template.get('name', '').lower() or
                query in template.get('type', '').lower() or
                query in template.get('description', '').lower()):
                results.append(template.copy())
        
        return results
    
    def extract_variables_from_template(self, template_id: str) -> List[str]:
        """
        Extrait les variables d'un modèle en analysant son contenu
        
        Args:
            template_id: ID du modèle
        
        Returns:
            list: Liste des variables trouvées dans le contenu
        """
        import re
        
        template = self.get_template(template_id)
        if not template:
            return []
        
        content = template.get('content', '')
        
        # Recherche toutes les occurrences de {variable}
        variables = re.findall(r'{([^{}]*)}', content)
        
        # Supprimer les doublons et trier
        return sorted(list(set(variables)))
    
    def update_template_variables(self, template_id: str) -> bool:
        """
        Met à jour la liste des variables d'un modèle en analysant son contenu
        
        Args:
            template_id: ID du modèle
        
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        # Trouver le modèle
        template_index = next((i for i, t in enumerate(self.templates) if t.get('id') == template_id), None)
        
        if template_index is None:
            logger.warning(f"Modèle avec ID {template_id} non trouvé")
            return False
        
        # Extraire les variables du contenu
        variables = self.extract_variables_from_template(template_id)
        
        # Mettre à jour le modèle
        self.templates[template_index]['variables'] = variables
        self.templates[template_index]['updated_at'] = datetime.now().isoformat()
        
        # Sauvegarder
        self.save_templates()
        
        logger.info(f"Variables du modèle mises à jour: {len(variables)} variables trouvées")
        return True
    
    # ---- Gestion des documents générés ----
    
    def load_documents(self) -> None:
        """
        Charge les documents générés
        """
        document_file = os.path.join(self.paths['documents'], "documents.json")
        
        if not os.path.exists(document_file):
            # Créer un fichier vide
            with open(document_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            
            self.documents = []
            logger.info("Fichier documents.json créé")
            return
        
        try:
            with open(document_file, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
            
            # Validation des données des documents
            self._validate_documents()
            
            logger.info(f"{len(self.documents)} documents chargés")
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de format JSON lors du chargement des documents: {e}")
            # Créer un backup du fichier corrompu
            if os.path.exists(document_file):
                backup_file = f"{document_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                shutil.copy2(document_file, backup_file)
                logger.info(f"Sauvegarde du fichier documents corrompu créée: {backup_file}")
            self.documents = []
        except Exception as e:
            logger.error(f"Erreur lors du chargement des documents: {e}")
            self.documents = []
    
    def _validate_documents(self) -> None:
        """
        Valide et corrige les données des documents pour s'assurer qu'elles sont conformes
        """
        valid_documents = []
        
        for document in self.documents:
            # Vérifier que c'est un dictionnaire
            if not isinstance(document, dict):
                logger.warning(f"Document ignoré car ce n'est pas un dictionnaire: {document}")
                continue
            
            # Vérifier la présence des champs obligatoires
            if not document.get('id') or not document.get('title'):
                logger.warning(f"Document ignoré car il manque des champs obligatoires: {document}")
                continue
            
            # Vérifier l'existence du fichier associé
            file_path = document.get('file_path', '')
            if file_path and not os.path.exists(file_path):
                logger.warning(f"Fichier non trouvé pour le document {document.get('id')}: {file_path}")
                # On garde le document même si le fichier est manquant
            
            # S'assurer que tous les champs nécessaires sont présents
            valid_document = {
                'id': document.get('id'),
                'title': document.get('title', '').strip(),
                'type': document.get('type', '').strip(),
                'date': document.get('date', datetime.now().strftime('%Y-%m-%d')),
                'description': document.get('description', '').strip(),
                'template_id': document.get('template_id'),
                'client_id': document.get('client_id'),
                'file_path': document.get('file_path', ''),
                'variables': document.get('variables', {}),
                'created_at': document.get('created_at', datetime.now().isoformat()),
                'updated_at': document.get('updated_at', datetime.now().isoformat())
            }
            
            # S'assurer que variables est un dictionnaire
            if not isinstance(valid_document['variables'], dict):
                valid_document['variables'] = {}
            
            valid_documents.append(valid_document)
        
        self.documents = valid_documents
        
        # Si des corrections ont été apportées, sauvegarder les données
        if len(valid_documents) != len(self.documents):
            logger.info(f"Données des documents corrigées: {len(self.documents)} -> {len(valid_documents)}")
            self.save_documents()
    
    def save_documents(self) -> bool:
        """
        Sauvegarde les documents générés
        
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        document_file = os.path.join(self.paths['documents'], "documents.json")
        
        try:
            # Créer un fichier temporaire d'abord
            temp_file = f"{document_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
            
            # Remplacer l'ancien fichier par le nouveau
            if os.path.exists(document_file):
                os.replace(temp_file, document_file)
            else:
                os.rename(temp_file, document_file)
            
            logger.info(f"{len(self.documents)} documents sauvegardés")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des documents: {e}")
            return False
    
    def add_document(self, document_data: Dict[str, Any]) -> Optional[str]:
        """
        Ajoute un nouveau document
        
        Args:
            document_data: Données du document
        
        Returns:
            str: ID du document ajouté ou None en cas d'erreur
        """
        # Vérification des champs obligatoires
        if 'title' not in document_data or not document_data['title'].strip():
            logger.warning("Tentative d'ajout d'un document sans titre")
            return None
        
        # Générer un ID unique
        document_id = str(uuid.uuid4())
        
        # Nettoyer et valider les données
        clean_data = {
            'id': document_id,
            'title': document_data.get('title', '').strip(),
            'type': document_data.get('type', '').strip(),
            'date': document_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'description': document_data.get('description', '').strip(),
            'template_id': document_data.get('template_id'),
            'client_id': document_data.get('client_id'),
            'file_path': document_data.get('file_path', ''),
            'variables': document_data.get('variables', {}),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # S'assurer que variables est un dictionnaire
        if not isinstance(clean_data['variables'], dict):
            clean_data['variables'] = {}
        
        # Vérifier que les IDs référencés existent
        if clean_data['template_id'] and not self.get_template(clean_data['template_id']):
            logger.warning(f"Modèle référencé introuvable: {clean_data['template_id']}")
            # On garde quand même la référence
        
        if clean_data['client_id'] and not self.get_client(clean_data['client_id']):
            logger.warning(f"Client référencé introuvable: {clean_data['client_id']}")
            # On garde quand même la référence
        
        # Vérifier que le fichier existe
        if clean_data['file_path'] and not os.path.exists(clean_data['file_path']):
            logger.warning(f"Fichier non trouvé: {clean_data['file_path']}")
            # On garde quand même le chemin
        
        # Ajouter à la liste
        self.documents.append(clean_data)
        
        # Sauvegarder
        self.save_documents()
        
        # Ajouter l'activité
        self.add_activity('document', f"Nouveau document créé: {clean_data.get('title')}")
        
        logger.info(f"Document ajouté: {clean_data.get('title')} (ID: {document_id})")
        return document_id
    
    def update_document(self, document_id: str, document_data: Dict[str, Any]) -> bool:
        """
        Met à jour un document existant
        
        Args:
            document_id: ID du document à mettre à jour
            document_data: Nouvelles données du document
        
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        # Vérification des champs obligatoires
        if 'title' not in document_data or not document_data['title'].strip():
            logger.warning("Tentative de mise à jour d'un document sans titre")
            return False
        
        # Trouver le document
        document_index = next((i for i, d in enumerate(self.documents) if d.get('id') == document_id), None)
        
        if document_index is None:
            logger.warning(f"Document avec ID {document_id} non trouvé")
            return False
        
        # Obtenir les données existantes
        existing_data = self.documents[document_index]
        
        # Mettre à jour les données
        updated_data = {
            'id': document_id,
            'title': document_data.get('title', '').strip(),
            'type': document_data.get('type', existing_data.get('type', '')).strip(),
            'date': document_data.get('date', existing_data.get('date', datetime.now().strftime('%Y-%m-%d'))),
            'description': document_data.get('description', existing_data.get('description', '')).strip(),
            'template_id': document_data.get('template_id', existing_data.get('template_id')),
            'client_id': document_data.get('client_id', existing_data.get('client_id')),
            'file_path': document_data.get('file_path', existing_data.get('file_path', '')),
            'variables': document_data.get('variables', existing_data.get('variables', {})),
            'created_at': existing_data.get('created_at', datetime.now().isoformat()),
            'updated_at': datetime.now().isoformat()
        }
        
        # S'assurer que variables est un dictionnaire
        if not isinstance(updated_data['variables'], dict):
            updated_data['variables'] = {}
        
        # Remplacer le document
        self.documents[document_index] = updated_data
        
        # Sauvegarder
        self.save_documents()
        
        # Ajouter l'activité
        self.add_activity('document', f"Document mis à jour: {updated_data.get('title')}")
        
        logger.info(f"Document mis à jour: {updated_data.get('title')} (ID: {document_id})")
        return True
    
    def delete_document(self, document_id: str, delete_file: bool = True) -> bool:
        """
        Supprime un document
        
        Args:
            document_id: ID du document à supprimer
            delete_file: Si True, supprime aussi le fichier associé
        
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        # Trouver le document
        document = next((d for d in self.documents if d.get('id') == document_id), None)
        
        if document is None:
            logger.warning(f"Document avec ID {document_id} non trouvé")
            return False
        
        # Supprimer le fichier associé si demandé
        file_path = document.get('file_path', '')
        if delete_file and file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Fichier supprimé: {file_path}")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du fichier: {e}")
                # On continue quand même avec la suppression du document
        
        # Supprimer le document
        self.documents = [d for d in self.documents if d.get('id') != document_id]
        
        # Sauvegarder
        self.save_documents()
        
        # Ajouter l'activité
        self.add_activity('document', f"Document supprimé: {document.get('title')}")
        
        logger.info(f"Document supprimé: {document.get('title')} (ID: {document_id})")
        return True
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un document avec mise en cache optimisée"""
        # Vérifier d'abord le cache
        cached_document = self.cache_manager.get("documents", document_id)
        if cached_document is not None:
            return cached_document.copy()  # Retourner une copie pour éviter les modifications accidentelles

        # Si pas dans le cache, chercher dans la liste
        document = next((d for d in self.documents if d["id"] == document_id), None)
        if document is not None:
            # Mettre en cache pour les prochaines fois
            self.cache_manager.set("documents", document_id, document)
            return document.copy()
        
        return None
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les documents
        
        Returns:
            list: Liste de tous les documents
        """
        return [d.copy() for d in self.documents]
    
    def search_documents(self, query: str, filters: Dict = None) -> List[Dict[str, Any]]:
        """Recherche des documents avec mise en cache et filtres"""
        # Créer une clé de cache unique
        cache_key = f"search_{query}_{hash(str(filters))}" if filters else f"search_{query}"
        
        # Vérifier le cache de recherche
        cache_entry = self._search_cache.get(cache_key)
        if cache_entry and time.time() - cache_entry['timestamp'] < 300:
            return cache_entry['results']

        # Effectuer la recherche
        query = query.lower()
        results = []
        
        for doc in self.documents:
            # Vérifier d'abord les filtres si présents
            if filters:
                if not self._document_matches_filters(doc, filters):
                    continue
            
            # Effectuer la recherche
            if (query in doc.get("title", "").lower() or
                query in doc.get("content", "").lower() or
                query in doc.get("description", "").lower()):
                results.append(doc.copy())

        # Mettre en cache les résultats
        self._search_cache[cache_key] = {
            'results': results,
            'timestamp': time.time()
        }
        
        return results
    
    def _document_matches_filters(self, document: Dict, filters: Dict) -> bool:
        """Vérifie si un document correspond aux filtres"""
        for key, value in filters.items():
            if key not in document or document[key] != value:
                return False
        return True

    def get_document_types(self) -> List[str]:
        """Récupère tous les types de documents uniques avec mise en cache"""
        cache_key = "document_types"
        cache_entry = self._document_type_cache.get(cache_key)
        
        if cache_entry and time.time() - cache_entry['timestamp'] < 3600:
            return cache_entry['types']

        # Extraire les types uniques
        types = sorted(list(set(d.get("type", "") for d in self.documents if d.get("type"))))
        
        # Mettre en cache
        self._document_type_cache[cache_key] = {
            'types': types,
            'timestamp': time.time()
        }
        
        return types

    # ---- Gestion des activités récentes ----
    
    def load_recent_activities(self) -> None:
        """
        Charge les activités récentes
        """
        activity_file = os.path.join(self.data_dir, "activities.json")
        
        if not os.path.exists(activity_file):
            # Créer un fichier vide
            with open(activity_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            
            self.recent_activities = []
            logger.info("Fichier activities.json créé")
            return
        
        try:
            with open(activity_file, 'r', encoding='utf-8') as f:
                self.recent_activities = json.load(f)
            
            # Validation des activités
            self._validate_activities()
            
            logger.info(f"{len(self.recent_activities)} activités chargées")
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de format JSON lors du chargement des activités: {e}")
            # Créer un backup du fichier corrompu
            if os.path.exists(activity_file):
                backup_file = f"{activity_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                shutil.copy2(activity_file, backup_file)
                logger.info(f"Sauvegarde du fichier activities corrompu créée: {backup_file}")
            self.recent_activities = []
        except Exception as e:
            logger.error(f"Erreur lors du chargement des activités: {e}")
            self.recent_activities = []
    
    def _validate_activities(self) -> None:
        """
        Valide et corrige les données des activités pour s'assurer qu'elles sont conformes
        """
        valid_activities = []
        
        for activity in self.recent_activities:
            # Vérifier que c'est un dictionnaire
            if not isinstance(activity, dict):
                continue
            
            # S'assurer que tous les champs nécessaires sont présents
            valid_activity = {
                'id': activity.get('id', str(uuid.uuid4())),
                'type': activity.get('type', 'unknown'),
                'description': activity.get('description', ''),
                'timestamp': activity.get('timestamp', datetime.now().isoformat())
            }
            
            valid_activities.append(valid_activity)
        
        # Limiter le nombre d'activités
        max_activities = self.config.get("max_recent_activities", 50)
        if len(valid_activities) > max_activities:
            valid_activities = valid_activities[:max_activities]
        
        self.recent_activities = valid_activities
        
        # Si des corrections ont été apportées, sauvegarder les données
        if len(valid_activities) != len(self.recent_activities):
            logger.info(f"Données des activités corrigées: {len(self.recent_activities)} -> {len(valid_activities)}")
            self.save_recent_activities()
    
    def save_recent_activities(self) -> bool:
        """
        Sauvegarde les activités récentes
        
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        activity_file = os.path.join(self.data_dir, "activities.json")
        
        try:
            # Créer un fichier temporaire d'abord
            temp_file = f"{activity_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.recent_activities, f, indent=2, ensure_ascii=False)
            
            # Remplacer l'ancien fichier par le nouveau
            if os.path.exists(activity_file):
                os.replace(temp_file, activity_file)
            else:
                os.rename(temp_file, activity_file)
            
            logger.info(f"{len(self.recent_activities)} activités sauvegardées")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des activités: {e}")
            # Nettoyer le fichier temporaire s'il existe
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return False
    
    def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère les activités récentes
        
        Args:
            limit: Nombre maximum d'activités à récupérer
        
        Returns:
            list: Liste des activités récentes
        """
        return self.recent_activities[:limit]
    
    def clear_activities(self) -> bool:
        """
        Efface toutes les activités récentes
        
        Returns:
            bool: True si l'opération a réussi, False sinon
        """
        self.recent_activities = []
        return self.save_recent_activities()
    
    # ---- Fonctions de sauvegarde et restauration ----
    
    def create_backup(self, backup_dir: str = None) -> Optional[str]:
        """
        Crée une sauvegarde complète des données
        
        Args:
            backup_dir: Dossier où créer la sauvegarde (si None, utilise le dossier par défaut)
        
        Returns:
            str: Chemin de la sauvegarde créée ou None en cas d'erreur
        """
        try:
            # Utiliser le dossier de sauvegarde par défaut si non spécifié
            if backup_dir is None:
                backup_dir = self.paths['backup']
            
            # S'assurer que le dossier existe
            os.makedirs(backup_dir, exist_ok=True)
            
            # Nom du dossier de sauvegarde avec la date et l'heure
            backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = os.path.join(backup_dir, f"backup_{backup_time}")
            os.makedirs(backup_folder, exist_ok=True)
            
            # Sauvegarder d'abord toutes les données
            self.save_clients()
            self.save_templates()
            self.save_documents()
            self.save_recent_activities()
            
            # Copier les fichiers de données
            shutil.copy2(os.path.join(self.paths['clients'], "clients.json"), 
                       os.path.join(backup_folder, "clients.json"))
            
            shutil.copy2(os.path.join(self.paths['templates'], "templates.json"), 
                       os.path.join(backup_folder, "templates.json"))
            
            shutil.copy2(os.path.join(self.paths['documents'], "documents.json"), 
                       os.path.join(backup_folder, "documents.json"))
            
            shutil.copy2(os.path.join(self.data_dir, "activities.json"), 
                       os.path.join(backup_folder, "activities.json"))
            
            # Copier la configuration
            config_file = os.path.join(self.data_dir, "config.json")
            if os.path.exists(config_file):
                shutil.copy2(config_file, os.path.join(backup_folder, "config.json"))
            
            # Ajouter l'activité
            self.add_activity('system', f"Sauvegarde créée: backup_{backup_time}")
            
            logger.info(f"Sauvegarde complète créée dans {backup_folder}")
            return backup_folder
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la sauvegarde: {e}")
            return None
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Restaure les données à partir d'une sauvegarde
        
        Args:
            backup_path: Chemin vers le dossier de sauvegarde
        
        Returns:
            bool: True si la restauration a réussi, False sinon
        """
        try:
            if not os.path.exists(backup_path) or not os.path.isdir(backup_path):
                logger.error(f"Dossier de sauvegarde non trouvé: {backup_path}")
                return False
            
            # Vérifier que les fichiers nécessaires existent
            required_files = ["clients.json", "templates.json", "documents.json", "activities.json"]
            for file in required_files:
                if not os.path.exists(os.path.join(backup_path, file)):
                    logger.error(f"Fichier manquant dans la sauvegarde: {file}")
                    return False
            
            # Créer des sauvegardes temporaires des fichiers actuels
            temp_backup = self.create_backup()
            if not temp_backup:
                logger.error("Impossible de créer une sauvegarde temporaire avant restauration")
                return False
            
            # Restaurer les fichiers
            shutil.copy2(os.path.join(backup_path, "clients.json"), 
                       os.path.join(self.paths['clients'], "clients.json"))
            
            shutil.copy2(os.path.join(backup_path, "templates.json"), 
                       os.path.join(self.paths['templates'], "templates.json"))
            
            shutil.copy2(os.path.join(backup_path, "documents.json"), 
                       os.path.join(self.paths['documents'], "documents.json"))
            
            shutil.copy2(os.path.join(backup_path, "activities.json"), 
                       os.path.join(self.data_dir, "activities.json"))
            
            # Restaurer la configuration si présente
            config_backup = os.path.join(backup_path, "config.json")
            if os.path.exists(config_backup):
                shutil.copy2(config_backup, os.path.join(self.data_dir, "config.json"))
                # Recharger la configuration
                self.config.load_config()
            
            # Recharger les données
            self.load_all_data()
            
            # Ajouter l'activité
            self.add_activity('system', f"Sauvegarde restaurée depuis: {os.path.basename(backup_path)}")
            
            logger.info(f"Données restaurées depuis {backup_path}")
            logger.info(f"Sauvegarde temporaire créée dans {temp_backup}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la restauration des données: {e}")
            return False
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des sauvegardes disponibles
        
        Returns:
            list: Liste des informations sur les sauvegardes
        """
        backups = []
        
        try:
            backup_dir = self.paths['backup']
            if not os.path.exists(backup_dir):
                return backups
            
            for item in os.listdir(backup_dir):
                item_path = os.path.join(backup_dir, item)
                
                # Vérifier que c'est un dossier de sauvegarde
                if os.path.isdir(item_path) and item.startswith("backup_"):
                    try:
                        # Extraire la date de la sauvegarde
                        date_str = item.replace("backup_", "")
                        date_obj = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                        
                        # Vérifier que les fichiers essentiels sont présents
                        has_clients = os.path.exists(os.path.join(item_path, "clients.json"))
                        has_templates = os.path.exists(os.path.join(item_path, "templates.json"))
                        has_documents = os.path.exists(os.path.join(item_path, "documents.json"))
                        
                        if has_clients and has_templates and has_documents:
                            backups.append({
                                "name": item,
                                "path": item_path,
                                "date": date_obj.strftime("%d/%m/%Y %H:%M:%S"),
                                "timestamp": date_obj.timestamp()
                            })
                    except:
                        # Ignorer les dossiers qui ne suivent pas le format
                        pass
            
            # Trier par date décroissante (plus récent en premier)
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste des sauvegardes: {e}")
        
        return backups
    
    # ---- Fonctions supplémentaires ----
    
    def export_data(self, export_dir: str, what: str = "all") -> bool:
        """
        Exporte les données dans des fichiers JSON
        
        Args:
            export_dir: Dossier où exporter les données
            what: Ce qu'il faut exporter ("all", "clients", "templates", "documents")
        
        Returns:
            bool: True si l'exportation a réussi, False sinon
        """
        try:
            # S'assurer que le dossier existe
            os.makedirs(export_dir, exist_ok=True)
            
            success = True
            
            # Exporter les clients
            if what in ["all", "clients"]:
                clients_file = os.path.join(export_dir, "clients_export.json")
                with open(clients_file, 'w', encoding='utf-8') as f:
                    json.dump(self.clients, f, indent=2, ensure_ascii=False)
                logger.info(f"Clients exportés vers {clients_file}")
            
            # Exporter les modèles
            if what in ["all", "templates"]:
                templates_file = os.path.join(export_dir, "templates_export.json")
                with open(templates_file, 'w', encoding='utf-8') as f:
                    json.dump(self.templates, f, indent=2, ensure_ascii=False)
                logger.info(f"Modèles exportés vers {templates_file}")
            
            # Exporter les documents
            if what in ["all", "documents"]:
                documents_file = os.path.join(export_dir, "documents_export.json")
                with open(documents_file, 'w', encoding='utf-8') as f:
                    json.dump(self.documents, f, indent=2, ensure_ascii=False)
                logger.info(f"Documents exportés vers {documents_file}")
            
            # Ajouter l'activité
            self.add_activity('system', f"Données exportées vers {export_dir}")
            
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation des données: {e}")
            return False
    
    def import_data(self, import_dir: str, what: str = "all", overwrite: bool = False) -> Dict[str, int]:
        """
        Importe des données depuis des fichiers JSON
        
        Args:
            import_dir: Dossier contenant les fichiers à importer
            what: Ce qu'il faut importer ("all", "clients", "templates", "documents")
            overwrite: Si True, remplace les données existantes; sinon, ajoute aux données existantes
        
        Returns:
            Dict[str, int]: Statistiques d'importation (nombre d'éléments ajoutés/mis à jour)
        """
        stats = {
            "clients_added": 0,
            "clients_updated": 0,
            "templates_added": 0,
            "templates_updated": 0,
            "documents_added": 0,
            "documents_updated": 0
        }
        
        try:
            # Importer les clients
            if what in ["all", "clients"]:
                clients_file = os.path.join(import_dir, "clients_export.json")
                if os.path.exists(clients_file):
                    with open(clients_file, 'r', encoding='utf-8') as f:
                        imported_clients = json.load(f)
                    
                    if overwrite:
                        # Remplacer tous les clients
                        self.clients = imported_clients
                        stats["clients_updated"] = len(imported_clients)
                    else:
                        # Ajouter ou mettre à jour les clients
                        existing_ids = {c.get('id'): i for i, c in enumerate(self.clients) if 'id' in c}
                        
                        for client in imported_clients:
                            client_id = client.get('id')
                            if client_id and client_id in existing_ids:
                                # Mettre à jour le client existant
                                self.clients[existing_ids[client_id]] = client
                                stats["clients_updated"] += 1
                            else:
                                # Ajouter le client
                                self.clients.append(client)
                                stats["clients_added"] += 1
                    
                    self.save_clients()
                    logger.info(f"Clients importés: {stats['clients_added']} ajoutés, {stats['clients_updated']} mis à jour")
            
            # Importer les modèles
            if what in ["all", "templates"]:
                templates_file = os.path.join(import_dir, "templates_export.json")
                if os.path.exists(templates_file):
                    with open(templates_file, 'r', encoding='utf-8') as f:
                        imported_templates = json.load(f)
                    
                    if overwrite:
                        # Remplacer tous les modèles
                        self.templates = imported_templates
                        stats["templates_updated"] = len(imported_templates)
                    else:
                        # Ajouter ou mettre à jour les modèles
                        existing_ids = {t.get('id'): i for i, t in enumerate(self.templates) if 'id' in t}
                        
                        for template in imported_templates:
                            template_id = template.get('id')
                            if template_id and template_id in existing_ids:
                                # Mettre à jour le modèle existant
                                self.templates[existing_ids[template_id]] = template
                                stats["templates_updated"] += 1
                            else:
                                # Ajouter le modèle
                                self.templates.append(template)
                                stats["templates_added"] += 1
                    
                    self.save_templates()
                    logger.info(f"Modèles importés: {stats['templates_added']} ajoutés, {stats['templates_updated']} mis à jour")
            
            # Importer les documents
            if what in ["all", "documents"]:
                documents_file = os.path.join(import_dir, "documents_export.json")
                if os.path.exists(documents_file):
                    with open(documents_file, 'r', encoding='utf-8') as f:
                        imported_documents = json.load(f)
                    
                    if overwrite:
                        # Remplacer tous les documents
                        self.documents = imported_documents
                        stats["documents_updated"] = len(imported_documents)
                    else:
                        # Ajouter ou mettre à jour les documents
                        existing_ids = {d.get('id'): i for i, d in enumerate(self.documents) if 'id' in d}
                        
                        for document in imported_documents:
                            document_id = document.get('id')
                            if document_id and document_id in existing_ids:
                                # Mettre à jour le document existant
                                self.documents[existing_ids[document_id]] = document
                                stats["documents_updated"] += 1
                            else:
                                # Ajouter le document
                                self.documents.append(document)
                                stats["documents_added"] += 1
                    
                    self.save_documents()
                    logger.info(f"Documents importés: {stats['documents_added']} ajoutés, {stats['documents_updated']} mis à jour")
            
            # Ajouter l'activité
            self.add_activity('system', f"Données importées depuis {import_dir}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors de l'importation des données: {e}")
            return stats
    
    def migrate_legacy_data(self) -> bool:
        """
        Migre les anciennes données vers le nouveau format
        
        Returns:
            bool: True si la migration a réussi, False sinon
        """
        try:
            # Vérification et migration des IDs clients
            updated_clients = False
            for client in self.clients:
                if 'id' in client and not isinstance(client['id'], str):
                    # Convertir les anciens IDs numériques en UUID
                    client['id'] = str(uuid.uuid4())
                    updated_clients = True
                elif 'id' not in client:
                    client['id'] = str(uuid.uuid4())
                    updated_clients = True
            
            if updated_clients:
                self.save_clients()
                logger.info("Migration des données clients effectuée")
            
            # Vérification et migration des IDs de modèles
            updated_templates = False
            for template in self.templates:
                if 'id' in template and not isinstance(template['id'], str):
                    template['id'] = str(uuid.uuid4())
                    updated_templates = True
                elif 'id' not in template:
                    template['id'] = str(uuid.uuid4())
                    updated_templates = True
            
            if updated_templates:
                self.save_templates()
                logger.info("Migration des données de modèles effectuée")
            
            # Vérification et migration des IDs de documents
            updated_documents = False
            for document in self.documents:
                if 'id' in document and not isinstance(document['id'], str):
                    document['id'] = str(uuid.uuid4())
                    updated_documents = True
                elif 'id' not in document:
                    document['id'] = str(uuid.uuid4())
                    updated_documents = True
            
            if updated_documents:
                self.save_documents()
                logger.info("Migration des données de documents effectuée")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la migration des données: {e}")
            return False
    
    def generate_statistics(self) -> Dict[str, Any]:
        """
        Génère des statistiques sur les données de l'application
        
        Returns:
            Dict[str, Any]: Statistiques générées
        """
        stats = {
            "clients": {
                "count": len(self.clients),
                "with_company": sum(1 for c in self.clients if c.get('company')),
                "without_company": sum(1 for c in self.clients if not c.get('company')),
            },
            "templates": {
                "count": len(self.templates),
                "by_type": {}
            },
            "documents": {
                "count": len(self.documents),
                "by_type": {},
                "by_month": {}
            }
        }
        
        # Statistiques des modèles par type
        for template in self.templates:
            template_type = template.get('type', 'unknown')
            if template_type not in stats["templates"]["by_type"]:
                stats["templates"]["by_type"][template_type] = 0
            stats["templates"]["by_type"][template_type] += 1
        
        # Statistiques des documents par type
        for document in self.documents:
            doc_type = document.get('type', 'unknown')
            if doc_type not in stats["documents"]["by_type"]:
                stats["documents"]["by_type"][doc_type] = 0
            stats["documents"]["by_type"][doc_type] += 1
            
            # Statistiques par mois (format YYYY-MM)
            try:
                date = document.get('date', '')
                if date:
                    month = date[:7]  # YYYY-MM
                    if month not in stats["documents"]["by_month"]:
                        stats["documents"]["by_month"][month] = 0
                    stats["documents"]["by_month"][month] += 1
            except:
                pass
        
        # Trier les mois chronologiquement
        stats["documents"]["by_month"] = dict(sorted(stats["documents"]["by_month"].items()))
        
        return stats

    def cleanup(self) -> bool:
        """
        Nettoie les ressources et le cache
        
        Returns:
            bool: True si le nettoyage s'est bien passé, False sinon
        """
        logger.info("Début du nettoyage de l'application")
        success = True
        
        try:
            # Sauvegarder toutes les données
            if not self.save_clients():
                logger.error("Erreur lors de la sauvegarde des clients")
                success = False
            
            if not self.save_templates():
                logger.error("Erreur lors de la sauvegarde des modèles")
                success = False
            
            if not self.save_documents():
                logger.error("Erreur lors de la sauvegarde des documents")
                success = False
            
            if not self.save_recent_activities():
                logger.error("Erreur lors de la sauvegarde des activités récentes")
                success = False
            
            # Nettoyer les fichiers temporaires
            temp_files = []
            for root, _, files in os.walk(self.data_dir):
                for file in files:
                    if file.endswith('.tmp'):
                        temp_files.append(os.path.join(root, file))
            
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                    logger.info(f"Fichier temporaire supprimé: {temp_file}")
                except OSError as e:
                    logger.warning(f"Impossible de supprimer le fichier temporaire {temp_file}: {e}")
                    success = False
            
            # Ajouter une activité de fermeture
            self.add_activity('system', 'Application fermée proprement')
            
            logger.info("Nettoyage de l'application terminé avec succès" if success else "Nettoyage de l'application terminé avec des erreurs")
            return success
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage de l'application: {e}")
            return False

    def auto_fill_document(self, template_id: str, client_id: str, extracted_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Auto-remplit un document avec les données extraites
        
        Args:
            template_id: ID du modèle de document
            client_id: ID du client
            extracted_data: Données extraites du document
        
        Returns:
            Dict[str, Any]: Données du document auto-rempli ou None en cas d'erreur
        """
        try:
            # Récupérer le modèle et le client
            template = self.get_template(template_id)
            client = self.get_client(client_id)
            
            if not template or not client:
                logger.error("Modèle ou client non trouvé")
                return None
            
            # Créer l'objet document
            document_id = f"doc_{len(self.documents) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Fusionner les données extraites avec les données du client
            document_data = {
                "id": document_id,
                "title": f"{template.get('type', 'Document')} - {client.get('name', 'Client')}",
                "type": template.get("type", ""),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "template_id": template_id,
                "client_id": client_id,
                "variables": {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Mapper les champs extraits aux variables du modèle
            field_mapping = self.config.get("auto_fill.field_mapping", {})
            for var_name, possible_names in field_mapping.items():
                # Chercher une correspondance dans les données extraites
                for name in possible_names:
                    if name in extracted_data:
                        document_data["variables"][var_name] = extracted_data[name]
                        break
            
            # Ajouter les données du client
            document_data["variables"].update({
                "client_name": client.get("name", ""),
                "client_company": client.get("company", ""),
                "client_email": client.get("email", ""),
                "client_phone": client.get("phone", ""),
                "client_address": client.get("address", "")
            })
            
            # Ajouter le document
            self.documents.append(document_data)
            self.save_documents()
            
            # Ajouter l'activité
            self.add_activity("document", f"Document auto-rempli: {document_data['title']}")
            
            logger.info(f"Document auto-rempli créé: {document_id}")
            return document_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'auto-remplissage du document: {e}")
            return None