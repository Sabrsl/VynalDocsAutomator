#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestionnaire de base de données pour l'application Vynal Docs Automator
Ce module fournit une interface unifiée pour gérer les données de l'application
avec support pour différents types de stockage (JSON, SQLite, etc.)
"""

import os
import json
import logging
import sqlite3
import shutil
from datetime import datetime
import uuid

logger = logging.getLogger("VynalDocsAutomator.DatabaseManager")

class DatabaseManager:
    """
    Gestionnaire de base de données pour l'application
    """
    
    def __init__(self, data_dir=None, storage_type="json"):
        """
        Initialise le gestionnaire de base de données
        
        Args:
            data_dir: Répertoire des données (None = dossier par défaut)
            storage_type: Type de stockage ('json' ou 'sqlite')
        """
        # Si aucun répertoire spécifié, utiliser le dossier par défaut
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
        
        self.data_dir = data_dir
        self.storage_type = storage_type.lower()
        
        # Créer les dossiers nécessaires
        self.clients_dir = os.path.join(data_dir, "clients")
        self.templates_dir = os.path.join(data_dir, "templates")
        self.documents_dir = os.path.join(data_dir, "documents")
        self.backup_dir = os.path.join(data_dir, "backup")
        
        os.makedirs(self.clients_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.documents_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialiser le stockage selon le type choisi
        if self.storage_type == "sqlite":
            self._init_sqlite()
        
        logger.info(f"DatabaseManager initialisé avec stockage {self.storage_type}")
    
    def _init_sqlite(self):
        """
        Initialise le stockage SQLite
        """
        self.db_path = os.path.join(self.data_dir, "vynal_db.sqlite")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        
        # Créer les tables si elles n'existent pas
        self._create_tables()
    
    def _create_tables(self):
        """
        Crée les tables SQLite si elles n'existent pas
        """
        cursor = self.conn.cursor()
        
        # Table des clients
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                company TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                created_at TEXT,
                updated_at TEXT,
                data JSON
            )
        ''')
        
        # Table des modèles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,
                description TEXT,
                content TEXT,
                variables JSON,
                created_at TEXT,
                updated_at TEXT,
                data JSON
            )
        ''')
        
        # Table des documents
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT,
                date TEXT,
                description TEXT,
                template_id TEXT,
                client_id TEXT,
                file_path TEXT,
                variables JSON,
                created_at TEXT,
                updated_at TEXT,
                data JSON,
                FOREIGN KEY (template_id) REFERENCES templates (id),
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        ''')
        
        # Table des activités
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                description TEXT,
                timestamp TEXT,
                data JSON
            )
        ''')
        
        self.conn.commit()
    
    def _generate_id(self, prefix):
        """
        Génère un ID unique avec un préfixe donné
        
        Args:
            prefix: Préfixe de l'ID (ex: 'client', 'template', 'document')
            
        Returns:
            str: ID unique
        """
        unique_id = str(uuid.uuid4()).split('-')[0]  # Première partie de l'UUID
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{prefix}_{timestamp}_{unique_id}"
    
    def close(self):
        """
        Ferme la connexion à la base de données si nécessaire
        """
        if self.storage_type == "sqlite" and hasattr(self, 'conn'):
            self.conn.close()
            logger.info("Connexion SQLite fermée")
    
    # ----- Méthodes pour les clients -----
    
    def get_clients(self):
        """
        Récupère tous les clients
        
        Returns:
            list: Liste des clients
        """
        if self.storage_type == "sqlite":
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM clients ORDER BY name")
            
            clients = []
            for row in cursor.fetchall():
                client = dict(row)
                
                # Traiter les données JSON
                if client['data']:
                    try:
                        extra_data = json.loads(client['data'])
                        # Fusionner les données supplémentaires
                        client.update(extra_data)
                    except:
                        pass
                
                # Supprimer la colonne data
                if 'data' in client:
                    del client['data']
                
                clients.append(client)
            
            return clients
        else:
            # Stockage JSON
            clients_file = os.path.join(self.clients_dir, "clients.json")
            
            if os.path.exists(clients_file):
                try:
                    with open(clients_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture des clients: {e}")
                    return []
            else:
                return []
    
    def get_client(self, client_id):
        """
        Récupère un client par son ID
        
        Args:
            client_id: ID du client
            
        Returns:
            dict: Données du client ou None si non trouvé
        """
        if self.storage_type == "sqlite":
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
            
            row = cursor.fetchone()
            if row:
                client = dict(row)
                
                # Traiter les données JSON
                if client['data']:
                    try:
                        extra_data = json.loads(client['data'])
                        # Fusionner les données supplémentaires
                        client.update(extra_data)
                    except:
                        pass
                
                # Supprimer la colonne data
                if 'data' in client:
                    del client['data']
                
                return client
            else:
                return None
        else:
            # Stockage JSON
            clients = self.get_clients()
            for client in clients:
                if client.get('id') == client_id:
                    return client
            return None
    
    def add_client(self, client_data):
        """
        Ajoute un nouveau client
        
        Args:
            client_data: Données du client
            
        Returns:
            str: ID du client ajouté ou None en cas d'erreur
        """
        try:
            # Vérifier les champs obligatoires
            if 'name' not in client_data:
                logger.error("Champ 'name' manquant pour le client")
                return None
            
            # Générer un ID s'il n'existe pas
            if 'id' not in client_data:
                client_data['id'] = self._generate_id('client')
            
            # Ajouter les horodatages
            now = datetime.now().isoformat()
            if 'created_at' not in client_data:
                client_data['created_at'] = now
            if 'updated_at' not in client_data:
                client_data['updated_at'] = now
            
            if self.storage_type == "sqlite":
                cursor = self.conn.cursor()
                
                # Extraire les champs principaux
                client_id = client_data['id']
                name = client_data['name']
                company = client_data.get('company', '')
                email = client_data.get('email', '')
                phone = client_data.get('phone', '')
                address = client_data.get('address', '')
                created_at = client_data['created_at']
                updated_at = client_data['updated_at']
                
                # Créer une copie pour les données supplémentaires
                data_copy = client_data.copy()
                # Supprimer les champs déjà traités
                for field in ['id', 'name', 'company', 'email', 'phone', 'address', 'created_at', 'updated_at']:
                    if field in data_copy:
                        del data_copy[field]
                
                # Convertir le reste en JSON
                data_json = json.dumps(data_copy) if data_copy else None
                
                # Insérer dans la base de données
                cursor.execute('''
                    INSERT INTO clients (id, name, company, email, phone, address, created_at, updated_at, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (client_id, name, company, email, phone, address, created_at, updated_at, data_json))
                
                self.conn.commit()
            else:
                # Stockage JSON
                clients = self.get_clients()
                clients.append(client_data)
                
                clients_file = os.path.join(self.clients_dir, "clients.json")
                with open(clients_file, 'w', encoding='utf-8') as f:
                    json.dump(clients, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Client ajouté: {client_data['id']} - {client_data['name']}")
            return client_data['id']
        
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du client: {e}")
            return None
    
    def update_client(self, client_id, client_data):
        """
        Met à jour un client existant
        
        Args:
            client_id: ID du client à mettre à jour
            client_data: Nouvelles données
            
        Returns:
            bool: True si mis à jour, False sinon
        """
        try:
            # Vérifier que le client existe
            existing_client = self.get_client(client_id)
            if not existing_client:
                logger.error(f"Client non trouvé: {client_id}")
                return False
            
            # Mettre à jour l'horodatage
            client_data['updated_at'] = datetime.now().isoformat()
            # Conserver l'ID et la date de création
            client_data['id'] = client_id
            if 'created_at' not in client_data and 'created_at' in existing_client:
                client_data['created_at'] = existing_client['created_at']
            
            if self.storage_type == "sqlite":
                cursor = self.conn.cursor()
                
                # Extraire les champs principaux
                name = client_data.get('name', existing_client.get('name', ''))
                company = client_data.get('company', existing_client.get('company', ''))
                email = client_data.get('email', existing_client.get('email', ''))
                phone = client_data.get('phone', existing_client.get('phone', ''))
                address = client_data.get('address', existing_client.get('address', ''))
                updated_at = client_data['updated_at']
                created_at = client_data.get('created_at', existing_client.get('created_at', ''))
                
                # Créer une copie pour les données supplémentaires
                data_copy = client_data.copy()
                # Supprimer les champs déjà traités
                for field in ['id', 'name', 'company', 'email', 'phone', 'address', 'created_at', 'updated_at']:
                    if field in data_copy:
                        del data_copy[field]
                
                # Convertir le reste en JSON
                data_json = json.dumps(data_copy) if data_copy else None
                
                # Mettre à jour dans la base de données
                cursor.execute('''
                    UPDATE clients
                    SET name = ?, company = ?, email = ?, phone = ?, address = ?, 
                        created_at = ?, updated_at = ?, data = ?
                    WHERE id = ?
                ''', (name, company, email, phone, address, created_at, updated_at, data_json, client_id))
                
                self.conn.commit()
            else:
                # Stockage JSON
                clients = self.get_clients()
                
                # Trouver l'index du client
                client_index = None
                for i, client in enumerate(clients):
                    if client.get('id') == client_id:
                        client_index = i
                        break
                
                if client_index is not None:
                    # Remplacer le client
                    clients[client_index] = client_data
                    
                    clients_file = os.path.join(self.clients_dir, "clients.json")
                    with open(clients_file, 'w', encoding='utf-8') as f:
                        json.dump(clients, f, ensure_ascii=False, indent=4)
                else:
                    logger.error(f"Client non trouvé dans la liste: {client_id}")
                    return False
            
            logger.info(f"Client mis à jour: {client_id}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du client: {e}")
            return False
    
    def delete_client(self, client_id):
        """
        Supprime un client
        
        Args:
            client_id: ID du client à supprimer
            
        Returns:
            bool: True si supprimé, False sinon
        """
        try:
            if self.storage_type == "sqlite":
                cursor = self.conn.cursor()
                
                # Vérifier si le client existe
                cursor.execute("SELECT id FROM clients WHERE id = ?", (client_id,))
                if not cursor.fetchone():
                    logger.error(f"Client non trouvé: {client_id}")
                    return False
                
                # Supprimer le client
                cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
                self.conn.commit()
            else:
                # Stockage JSON
                clients = self.get_clients()
                
                # Filtrer pour supprimer le client
                new_clients = [c for c in clients if c.get('id') != client_id]
                
                # Vérifier si un client a été supprimé
                if len(new_clients) == len(clients):
                    logger.error(f"Client non trouvé: {client_id}")
                    return False
                
                # Enregistrer la liste mise à jour
                clients_file = os.path.join(self.clients_dir, "clients.json")
                with open(clients_file, 'w', encoding='utf-8') as f:
                    json.dump(new_clients, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Client supprimé: {client_id}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du client: {e}")
            return False
    
    # ----- Méthodes pour les modèles -----
    
    def get_templates(self):
        """
        Récupère tous les modèles
        
        Returns:
            list: Liste des modèles
        """
        if self.storage_type == "sqlite":
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM templates ORDER BY name")
            
            templates = []
            for row in cursor.fetchall():
                template = dict(row)
                
                # Traiter les données JSON
                if template['variables']:
                    try:
                        template['variables'] = json.loads(template['variables'])
                    except:
                        template['variables'] = []
                else:
                    template['variables'] = []
                
                if template['data']:
                    try:
                        extra_data = json.loads(template['data'])
                        # Fusionner les données supplémentaires
                        template.update(extra_data)
                    except:
                        pass
                
                # Supprimer la colonne data
                if 'data' in template:
                    del template['data']
                
                templates.append(template)
            
            return templates
        else:
            # Stockage JSON
            templates_file = os.path.join(self.templates_dir, "templates.json")
            
            if os.path.exists(templates_file):
                try:
                    with open(templates_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture des modèles: {e}")
                    return []
            else:
                return []
    
    def get_template(self, template_id):
        """
        Récupère un modèle par son ID
        
        Args:
            template_id: ID du modèle
            
        Returns:
            dict: Données du modèle ou None si non trouvé
        """
        if self.storage_type == "sqlite":
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
            
            row = cursor.fetchone()
            if row:
                template = dict(row)
                
                # Traiter les données JSON
                if template['variables']:
                    try:
                        template['variables'] = json.loads(template['variables'])
                    except:
                        template['variables'] = []
                else:
                    template['variables'] = []
                
                if template['data']:
                    try:
                        extra_data = json.loads(template['data'])
                        # Fusionner les données supplémentaires
                        template.update(extra_data)
                    except:
                        pass
                
                # Supprimer la colonne data
                if 'data' in template:
                    del template['data']
                
                return template
            else:
                return None
        else:
            # Stockage JSON
            templates = self.get_templates()
            for template in templates:
                if template.get('id') == template_id:
                    return template
            return None
    
    def add_template(self, template_data):
        """
        Ajoute un nouveau modèle
        
        Args:
            template_data: Données du modèle
            
        Returns:
            str: ID du modèle ajouté ou None en cas d'erreur
        """
        try:
            # Vérifier les champs obligatoires
            if 'name' not in template_data:
                logger.error("Champ 'name' manquant pour le modèle")
                return None
            
            # Générer un ID s'il n'existe pas
            if 'id' not in template_data:
                template_data['id'] = self._generate_id('template')
            
            # Ajouter les horodatages
            now = datetime.now().isoformat()
            if 'created_at' not in template_data:
                template_data['created_at'] = now
            if 'updated_at' not in template_data:
                template_data['updated_at'] = now
            
            # S'assurer que variables est une liste
            if 'variables' not in template_data:
                template_data['variables'] = []
            
            if self.storage_type == "sqlite":
                cursor = self.conn.cursor()
                
                # Extraire les champs principaux
                template_id = template_data['id']
                name = template_data['name']
                template_type = template_data.get('type', '')
                description = template_data.get('description', '')
                content = template_data.get('content', '')
                variables_json = json.dumps(template_data['variables'])
                created_at = template_data['created_at']
                updated_at = template_data['updated_at']
                
                # Créer une copie pour les données supplémentaires
                data_copy = template_data.copy()
                # Supprimer les champs déjà traités
                for field in ['id', 'name', 'type', 'description', 'content', 'variables', 'created_at', 'updated_at']:
                    if field in data_copy:
                        del data_copy[field]
                
                # Convertir le reste en JSON
                data_json = json.dumps(data_copy) if data_copy else None
                
                # Insérer dans la base de données
                cursor.execute('''
                    INSERT INTO templates 
                    (id, name, type, description, content, variables, created_at, updated_at, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (template_id, name, template_type, description, content, variables_json, 
                      created_at, updated_at, data_json))
                
                self.conn.commit()
            else:
                # Stockage JSON
                templates = self.get_templates()
                templates.append(template_data)
                
                templates_file = os.path.join(self.templates_dir, "templates.json")
                with open(templates_file, 'w', encoding='utf-8') as f:
                    json.dump(templates, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Modèle ajouté: {template_data['id']} - {template_data['name']}")
            return template_data['id']
        
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du modèle: {e}")
            return None
    
    def update_template(self, template_id, template_data):
        """
        Met à jour un modèle existant
        
        Args:
            template_id: ID du modèle à mettre à jour
            template_data: Nouvelles données
            
        Returns:
            bool: True si mis à jour, False sinon
        """
        try:
            # Vérifier que le modèle existe
            existing_template = self.get_template(template_id)
            if not existing_template:
                logger.error(f"Modèle non trouvé: {template_id}")
                return False
            
            # Mettre à jour l'horodatage
            template_data['updated_at'] = datetime.now().isoformat()
            # Conserver l'ID et la date de création
            template_data['id'] = template_id
            if 'created_at' not in template_data and 'created_at' in existing_template:
                template_data['created_at'] = existing_template['created_at']
            
            # S'assurer que variables est une liste
            if 'variables' not in template_data:
                template_data['variables'] = existing_template.get('variables', [])
            
            if self.storage_type == "sqlite":
                cursor = self.conn.cursor()
                
                # Extraire les champs principaux
                name = template_data.get('name', existing_template.get('name', ''))
                template_type = template_data.get('type', existing_template.get('type', ''))
                description = template_data.get('description', existing_template.get('description', ''))
                content = template_data.get('content', existing_template.get('content', ''))
                variables_json = json.dumps(template_data['variables'])
                updated_at = template_data['updated_at']
                created_at = template_data.get('created_at', existing_template.get('created_at', ''))
                
                # Créer une copie pour les données supplémentaires
                data_copy = template_data.copy()
                # Supprimer les champs déjà traités
                for field in ['id', 'name', 'type', 'description', 'content', 'variables', 'created_at', 'updated_at']:
                    if field in data_copy:
                        del data_copy[field]
                
                # Convertir le reste en JSON
                data_json = json.dumps(data_copy) if data_copy else None
                
                # Mettre à jour dans la base de données
                cursor.execute('''
                    UPDATE templates
                    SET name = ?, type = ?, description = ?, content = ?, 
                        variables = ?, created_at = ?, updated_at = ?, data = ?
                    WHERE id = ?
                ''', (name, template_type, description, content, variables_json, 
                      created_at, updated_at, data_json, template_id))
                
                self.conn.commit()
            else:
                # Stockage JSON
                templates = self.get_templates()
                
                # Trouver l'index du modèle
                template_index = None
                for i, template in enumerate(templates):
                    if template.get('id') == template_id:
                        template_index = i
                        break
                
                if template_index is not None:
                    # Remplacer le modèle
                    templates[template_index] = template_data
                    
                    templates_file = os.path.join(self.templates_dir, "templates.json")
                    with open(templates_file, 'w', encoding='utf-8') as f:
                        json.dump(templates, f, ensure_ascii=False, indent=4)
                else:
                    logger.error(f"Modèle non trouvé dans la liste: {template_id}")
                    return False
            
            logger.info(f"Modèle mis à jour: {template_id}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du modèle: {e}")
            return False
    
    def delete_template(self, template_id):
        """
        Supprime un modèle
        
        Args:
            template_id: ID du modèle à supprimer
            
        Returns:
            bool: True si supprimé, False sinon
        """
        try:
            if self.storage_type == "sqlite":
                cursor = self.conn.cursor()
                
                # Vérifier si le modèle existe
                cursor.execute("SELECT id FROM templates WHERE id = ?", (template_id,))
                if not cursor.fetchone():
                    logger.error(f"Modèle non trouvé: {template_id}")
                    return False
                
                # Supprimer le modèle
                cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))
                self.conn.commit()
            else:
                # Stockage JSON
                templates = self.get_templates()
                
                # Filtrer pour supprimer le modèle
                new_templates = [t for t in templates if t.get('id') != template_id]
                
                # Vérifier si un modèle a été supprimé
                if len(new_templates) == len(templates):
                    logger.error(f"Modèle non trouvé: {template_id}")
                    return False
                
                # Enregistrer la liste mise à jour
                templates_file = os.path.join(self.templates_dir, "templates.json")
                with open(templates_file, 'w', encoding='utf-8') as f:
                    json.dump(new_templates, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Modèle supprimé: {template_id}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du modèle: {e}")
            return False
    
    # ----- Méthodes pour les documents -----
    
    def get_documents(self):
        """
        Récupère tous les documents
        
        Returns:
            list: Liste des documents
        """
        if self.storage_type == "sqlite":
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY date DESC")
            
            documents = []
            for row in cursor.fetchall():
                document = dict(row)
                
                # Traiter les données JSON
                if document['variables']:
                    try:
                        document['variables'] = json.loads(document['variables'])
                    except:
                        document['variables'] = {}
                else:
                    document['variables'] = {}
                
                if document['data']:
                    try:
                        extra_data = json.loads(document['data'])
                        # Fusionner les données supplémentaires
                        document.update(extra_data)
                    except:
                        pass
                
                # Supprimer la colonne data
                if 'data' in document:
                    del document['data']
                
                documents.append(document)
            
            return documents
        else:
            # Stockage JSON
            documents_file = os.path.join(self.documents_dir, "documents.json")
            
            if os.path.exists(documents_file):
                try:
                    with open(documents_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture des documents: {e}")
                    return []
            else:
                return []
    
    def get_document(self, document_id):
        """
        Récupère un document par son ID
        
        Args:
            document_id: ID du document
            
        Returns:
            dict: Données du document ou None si non trouvé
        """
        if self.storage_type == "sqlite":
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
            
            row = cursor.fetchone()
            if row:
                document = dict(row)
                
                # Traiter les données JSON
                if document['variables']:
                    try:
                        document['variables'] = json.loads(document['variables'])
                    except:
                        document['variables'] = {}
                else:
                    document['variables'] = {}
                
                if document['data']:
                    try:
                        extra_data = json.loads(document['data'])
                        # Fusionner les données supplémentaires
                        document.update(extra_data)
                    except:
                        pass
                
                # Supprimer la colonne data
                if 'data' in document:
                    del document['data']
                
                return document
            else:
                return None
        else:
            # Stockage JSON
            documents = self.get_documents()
            for document in documents:
                if document.get('id') == document_id:
                    return document
            return None
    
    def add_document(self, document_data):
        """
        Ajoute un nouveau document
        
        Args:
            document_data: Données du document
            
        Returns:
            str: ID du document ajouté ou None en cas d'erreur
        """
        try:
            # Vérifier les champs obligatoires
            if 'title' not in document_data:
                logger.error("Champ 'title' manquant pour le document")
                return None
            
            # Générer un ID s'il n'existe pas
            if 'id' not in document_data:
                document_data['id'] = self._generate_id('doc')
            
            # Ajouter les horodatages
            now = datetime.now().isoformat()
            if 'created_at' not in document_data:
                document_data['created_at'] = now
            if 'updated_at' not in document_data:
                document_data['updated_at'] = now
            
            # S'assurer que variables est un dictionnaire
            if 'variables' not in document_data:
                document_data['variables'] = {}
            
            if self.storage_type == "sqlite":
                cursor = self.conn.cursor()
                
                # Extraire les champs principaux
                document_id = document_data['id']
                title = document_data['title']
                doc_type = document_data.get('type', '')
                date = document_data.get('date', now.split('T')[0])  # Date sans l'heure
                description = document_data.get('description', '')
                template_id = document_data.get('template_id', '')
                client_id = document_data.get('client_id', '')
                file_path = document_data.get('file_path', '')
                variables_json = json.dumps(document_data['variables'])
                created_at = document_data['created_at']
                updated_at = document_data['updated_at']
                
                # Créer une copie pour les données supplémentaires
                data_copy = document_data.copy()
                # Supprimer les champs déjà traités
                fields_to_remove = ['id', 'title', 'type', 'date', 'description', 
                                   'template_id', 'client_id', 'file_path', 
                                   'variables', 'created_at', 'updated_at']
                for field in fields_to_remove:
                    if field in data_copy:
                        del data_copy[field]
                
                # Convertir le reste en JSON
                data_json = json.dumps(data_copy) if data_copy else None
                
                # Insérer dans la base de données
                cursor.execute('''
                    INSERT INTO documents 
                    (id, title, type, date, description, template_id, client_id, 
                     file_path, variables, created_at, updated_at, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (document_id, title, doc_type, date, description, template_id, 
                      client_id, file_path, variables_json, created_at, updated_at, data_json))
                
                self.conn.commit()
            else:
                # Stockage JSON
                documents = self.get_documents()
                documents.append(document_data)
                
                documents_file = os.path.join(self.documents_dir, "documents.json")
                with open(documents_file, 'w', encoding='utf-8') as f:
                    json.dump(documents, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Document ajouté: {document_data['id']} - {document_data['title']}")
            return document_data['id']
        
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du document: {e}")
            return None
    
    def update_document(self, document_id, document_data):
        """
        Met à jour un document existant
        
        Args:
            document_id: ID du document à mettre à jour
            document_data: Nouvelles données
            
        Returns:
            bool: True si mis à jour, False sinon
        """
        try:
            # Vérifier que le document existe
            existing_document = self.get_document(document_id)
            if not existing_document:
                logger.error(f"Document non trouvé: {document_id}")
                return False
            
            # Mettre à jour l'horodatage
            document_data['updated_at'] = datetime.now().isoformat()
            # Conserver l'ID et la date de création
            document_data['id'] = document_id
            if 'created_at' not in document_data and 'created_at' in existing_document:
                document_data['created_at'] = existing_document['created_at']
            
            # S'assurer que variables est un dictionnaire
            if 'variables' not in document_data:
                document_data['variables'] = existing_document.get('variables', {})
            
            if self.storage_type == "sqlite":
                cursor = self.conn.cursor()
                
                # Extraire les champs principaux
                title = document_data.get('title', existing_document.get('title', ''))
                doc_type = document_data.get('type', existing_document.get('type', ''))
                date = document_data.get('date', existing_document.get('date', ''))
                description = document_data.get('description', existing_document.get('description', ''))
                template_id = document_data.get('template_id', existing_document.get('template_id', ''))
                client_id = document_data.get('client_id', existing_document.get('client_id', ''))
                file_path = document_data.get('file_path', existing_document.get('file_path', ''))
                variables_json = json.dumps(document_data['variables'])
                updated_at = document_data['updated_at']
                created_at = document_data.get('created_at', existing_document.get('created_at', ''))
                
                # Créer une copie pour les données supplémentaires
                data_copy = document_data.copy()
                # Supprimer les champs déjà traités
                fields_to_remove = ['id', 'title', 'type', 'date', 'description', 
                                   'template_id', 'client_id', 'file_path', 
                                   'variables', 'created_at', 'updated_at']
                for field in fields_to_remove:
                    if field in data_copy:
                        del data_copy[field]
                
                # Convertir le reste en JSON
                data_json = json.dumps(data_copy) if data_copy else None
                
                # Mettre à jour dans la base de données
                cursor.execute('''
                    UPDATE documents
                    SET title = ?, type = ?, date = ?, description = ?, 
                        template_id = ?, client_id = ?, file_path = ?,
                        variables = ?, created_at = ?, updated_at = ?, data = ?
                    WHERE id = ?
                ''', (title, doc_type, date, description, template_id, client_id, 
                      file_path, variables_json, created_at, updated_at, data_json, document_id))
                
                self.conn.commit()
            else:
                # Stockage JSON
                documents = self.get_documents()
                
                # Trouver l'index du document
                document_index = None
                for i, document in enumerate(documents):
                    if document.get('id') == document_id:
                        document_index = i
                        break
                
                if document_index is not None:
                    # Remplacer le document
                    documents[document_index] = document_data
                    
                    documents_file = os.path.join(self.documents_dir, "documents.json")
                    with open(documents_file, 'w', encoding='utf-8') as f:
                        json.dump(documents, f, ensure_ascii=False, indent=4)
                else:
                    logger.error(f"Document non trouvé dans la liste: {document_id}")
                    return False
            
            logger.info(f"Document mis à jour: {document_id}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du document: {e}")
            return False
    
    def delete_document(self, document_id):
        """
        Supprime un document
        
        Args:
            document_id: ID du document à supprimer
            
        Returns:
            bool: True si supprimé, False sinon
        """
        try:
            if self.storage_type == "sqlite":
                cursor = self.conn.cursor()
                
                # Vérifier si le document existe
                cursor.execute("SELECT id, file_path FROM documents WHERE id = ?", (document_id,))
                row = cursor.fetchone()
                if not row:
                    logger.error(f"Document non trouvé: {document_id}")
                    return False
                
                # Récupérer le chemin du fichier pour suppression éventuelle
                file_path = row['file_path'] if row['file_path'] else None
                
                # Supprimer le document
                cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
                self.conn.commit()
                
                # Supprimer le fichier associé si existant
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Fichier associé supprimé: {file_path}")
                    except Exception as e:
                        logger.warning(f"Impossible de supprimer le fichier associé: {e}")
            else:
                # Stockage JSON
                documents = self.get_documents()
                
                # Trouver le document pour récupérer le chemin du fichier
                file_path = None
                for document in documents:
                    if document.get('id') == document_id:
                        file_path = document.get('file_path')
                        break
                
                # Filtrer pour supprimer le document
                new_documents = [d for d in documents if d.get('id') != document_id]
                
                # Vérifier si un document a été supprimé
                if len(new_documents) == len(documents):
                    logger.error(f"Document non trouvé: {document_id}")
                    return False
                
                # Enregistrer la liste mise à jour
                documents_file = os.path.join(self.documents_dir, "documents.json")
                with open(documents_file, 'w', encoding='utf-8') as f:
                    json.dump(new_documents, f, ensure_ascii=False, indent=4)
                
                # Supprimer le fichier associé si existant
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Fichier associé supprimé: {file_path}")
                    except Exception as e:
                        logger.warning(f"Impossible de supprimer le fichier associé: {e}")
            
            logger.info(f"Document supprimé: {document_id}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du document: {e}")
            return False
    
    # ----- Méthodes pour les activités -----
    
    def add_activity(self, activity_type, description, data=None):
        """
        Ajoute une activité dans l'historique
        
        Args:
            activity_type: Type d'activité (client, document, template)
            description: Description de l'activité
            data: Données supplémentaires
            
        Returns:
            str: ID de l'activité ajoutée ou None en cas d'erreur
        """
        try:
            # Créer l'objet activité
            activity_id = self._generate_id('activity')
            timestamp = datetime.now().isoformat()
            
            activity_data = {
                'id': activity_id,
                'type': activity_type,
                'description': description,
                'timestamp': timestamp,
                'data': data
            }
            
            if self.storage_type == "sqlite":
                cursor = self.conn.cursor()
                
                # Convertir les données supplémentaires en JSON
                data_json = json.dumps(data) if data else None
                
                # Insérer dans la base de données
                cursor.execute('''
                    INSERT INTO activities 
                    (id, type, description, timestamp, data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (activity_id, activity_type, description, timestamp, data_json))
                
                self.conn.commit()
            else:
                # Pour le stockage JSON, on ajoute l'activité à une liste
                activities_file = os.path.join(self.data_dir, "activities.json")
                activities = []
                
                # Charger les activités existantes
                if os.path.exists(activities_file):
                    try:
                        with open(activities_file, 'r', encoding='utf-8') as f:
                            activities = json.load(f)
                    except:
                        activities = []
                
                # Ajouter la nouvelle activité
                activities.append(activity_data)
                
                # Limiter le nombre d'activités (par exemple, conserver les 1000 dernières)
                max_activities = 1000
                if len(activities) > max_activities:
                    activities = activities[-max_activities:]
                
                # Enregistrer les activités
                with open(activities_file, 'w', encoding='utf-8') as f:
                    json.dump(activities, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Activité ajoutée: {activity_type} - {description}")
            return activity_id
        
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de l'activité: {e}")
            return None
    
    def get_recent_activities(self, limit=20):
        """
        Récupère les activités récentes
        
        Args:
            limit: Nombre maximum d'activités à récupérer
            
        Returns:
            list: Liste des activités récentes
        """
        try:
            if self.storage_type == "sqlite":
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT * FROM activities 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                
                activities = []
                for row in cursor.fetchall():
                    activity = dict(row)
                    
                    # Traiter les données JSON
                    if activity['data']:
                        try:
                            activity['data'] = json.loads(activity['data'])
                        except:
                            activity['data'] = None
                    
                    activities.append(activity)
                
                return activities
            else:
                # Stockage JSON
                activities_file = os.path.join(self.data_dir, "activities.json")
                
                if os.path.exists(activities_file):
                    try:
                        with open(activities_file, 'r', encoding='utf-8') as f:
                            activities = json.load(f)
                            
                            # Trier par timestamp décroissant
                            activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                            
                            # Limiter le nombre d'activités
                            return activities[:limit]
                    except Exception as e:
                        logger.error(f"Erreur lors de la lecture des activités: {e}")
                
                return []
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des activités: {e}")
            return []
    
    # ----- Méthodes de sauvegarde et restauration -----
    
    def create_backup(self, backup_dir=None):
        """
        Crée une sauvegarde complète de la base de données
        
        Args:
            backup_dir: Répertoire de sauvegarde (None = dossier par défaut)
            
        Returns:
            str: Chemin du répertoire de sauvegarde ou None en cas d'erreur
        """
        try:
            # Utiliser le répertoire de sauvegarde par défaut si non spécifié
            if backup_dir is None:
                backup_dir = self.backup_dir
            
            # Créer un sous-répertoire avec la date
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}")
            os.makedirs(backup_path, exist_ok=True)
            
            if self.storage_type == "sqlite":
                # Créer une copie du fichier SQLite
                if hasattr(self, 'conn'):
                    self.conn.commit()  # S'assurer que toutes les modifications sont enregistrées
                
                # Sauvegarder le fichier de base de données
                shutil.copy2(self.db_path, os.path.join(backup_path, os.path.basename(self.db_path)))
            else:
                # Copier tous les fichiers JSON
                for dir_name, file_name in [
                    (self.clients_dir, "clients.json"),
                    (self.templates_dir, "templates.json"),
                    (self.documents_dir, "documents.json"),
                    (self.data_dir, "activities.json")
                ]:
                    src_file = os.path.join(dir_name, file_name)
                    if os.path.exists(src_file):
                        shutil.copy2(src_file, os.path.join(backup_path, file_name))
            
            logger.info(f"Sauvegarde créée: {backup_path}")
            return backup_path
        
        except Exception as e:
            logger.error(f"Erreur lors de la création de la sauvegarde: {e}")
            return None
    
    def restore_backup(self, backup_path):
        """
        Restaure une sauvegarde de la base de données
        
        Args:
            backup_path: Chemin du répertoire de sauvegarde
            
        Returns:
            bool: True si restaurée, False sinon
        """
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Répertoire de sauvegarde introuvable: {backup_path}")
                return False
            
            if self.storage_type == "sqlite":
                # Fermer la connexion actuelle
                if hasattr(self, 'conn'):
                    self.conn.close()
                
                # Trouver le fichier de base de données dans la sauvegarde
                db_backup = None
                for file in os.listdir(backup_path):
                    if file.endswith('.sqlite'):
                        db_backup = os.path.join(backup_path, file)
                        break
                
                if not db_backup:
                    logger.error("Fichier SQLite non trouvé dans la sauvegarde")
                    return False
                
                # Restaurer le fichier
                shutil.copy2(db_backup, self.db_path)
                
                # Rouvrir la connexion
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
            else:
                # Restaurer les fichiers JSON
                for file_name, dir_name in [
                    ("clients.json", self.clients_dir),
                    ("templates.json", self.templates_dir),
                    ("documents.json", self.documents_dir),
                    ("activities.json", self.data_dir)
                ]:
                    backup_file = os.path.join(backup_path, file_name)
                    if os.path.exists(backup_file):
                        shutil.copy2(backup_file, os.path.join(dir_name, file_name))
            
            logger.info(f"Sauvegarde restaurée depuis: {backup_path}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la restauration de la sauvegarde: {e}")
            return False
    
    # ----- Méthodes d'exportation et d'importation -----
    
    def export_data(self, export_dir=None, data_type="all"):
        """
        Exporte les données dans des fichiers JSON
        
        Args:
            export_dir: Répertoire d'exportation (None = dossier par défaut)
            data_type: Type de données à exporter ('all', 'clients', 'templates', 'documents')
            
        Returns:
            dict: Dictionnaire des chemins des fichiers exportés ou None en cas d'erreur
        """
        try:
            # Utiliser le répertoire d'exportation par défaut si non spécifié
            if export_dir is None:
                export_dir = os.path.join(self.data_dir, "export")
            
            # Créer le répertoire si nécessaire
            os.makedirs(export_dir, exist_ok=True)
            
            # Déterminer quels types de données exporter
            types_to_export = []
            if data_type == "all":
                types_to_export = ["clients", "templates", "documents"]
            elif data_type in ["clients", "templates", "documents"]:
                types_to_export = [data_type]
            else:
                logger.error(f"Type de données non valide: {data_type}")
                return None
            
            # Exporter les données
            exported_files = {}
            
            for data_type in types_to_export:
                if data_type == "clients":
                    clients = self.get_clients()
                    file_path = os.path.join(export_dir, "clients_export.json")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(clients, f, ensure_ascii=False, indent=4)
                    exported_files["clients"] = file_path
                
                elif data_type == "templates":
                    templates = self.get_templates()
                    file_path = os.path.join(export_dir, "templates_export.json")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(templates, f, ensure_ascii=False, indent=4)
                    exported_files["templates"] = file_path
                
                elif data_type == "documents":
                    documents = self.get_documents()
                    file_path = os.path.join(export_dir, "documents_export.json")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(documents, f, ensure_ascii=False, indent=4)
                    exported_files["documents"] = file_path
            
            logger.info(f"Données exportées dans: {export_dir}")
            return exported_files
        
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation des données: {e}")
            return None
    
    def import_data(self, import_files, overwrite=False):
        """
        Importe des données depuis des fichiers JSON
        
        Args:
            import_files: Dictionnaire de chemins de fichiers à importer
            overwrite: Si True, remplace les données existantes; sinon, ajoute aux données existantes
            
        Returns:
            dict: Résumé des données importées ou None en cas d'erreur
        """
        try:
            # Vérifier les fichiers à importer
            for data_type, file_path in import_files.items():
                if data_type not in ["clients", "templates", "documents"]:
                    logger.error(f"Type de données non valide: {data_type}")
                    return None
                
                if not os.path.exists(file_path):
                    logger.error(f"Fichier introuvable: {file_path}")
                    return None
            
            # Importer les données
            import_summary = {
                "clients": {"added": 0, "updated": 0, "skipped": 0},
                "templates": {"added": 0, "updated": 0, "skipped": 0},
                "documents": {"added": 0, "updated": 0, "skipped": 0}
            }
            
            for data_type, file_path in import_files.items():
                # Charger les données depuis le fichier
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)
                
                if data_type == "clients":
                    existing_clients = {c.get('id'): c for c in self.get_clients()} if not overwrite else {}
                    
                    for client in imported_data:
                        client_id = client.get('id')
                        
                        if client_id in existing_clients:
                            if overwrite:
                                # Mettre à jour le client existant
                                self.update_client(client_id, client)
                                import_summary["clients"]["updated"] += 1
                            else:
                                # Ignorer le client existant
                                import_summary["clients"]["skipped"] += 1
                        else:
                            # Ajouter le nouveau client
                            self.add_client(client)
                            import_summary["clients"]["added"] += 1
                
                elif data_type == "templates":
                    existing_templates = {t.get('id'): t for t in self.get_templates()} if not overwrite else {}
                    
                    for template in imported_data:
                        template_id = template.get('id')
                        
                        if template_id in existing_templates:
                            if overwrite:
                                # Mettre à jour le modèle existant
                                self.update_template(template_id, template)
                                import_summary["templates"]["updated"] += 1
                            else:
                                # Ignorer le modèle existant
                                import_summary["templates"]["skipped"] += 1
                        else:
                            # Ajouter le nouveau modèle
                            self.add_template(template)
                            import_summary["templates"]["added"] += 1
                
                elif data_type == "documents":
                    existing_documents = {d.get('id'): d for d in self.get_documents()} if not overwrite else {}
                    
                    for document in imported_data:
                        document_id = document.get('id')
                        
                        if document_id in existing_documents:
                            if overwrite:
                                # Mettre à jour le document existant
                                self.update_document(document_id, document)
                                import_summary["documents"]["updated"] += 1
                            else:
                                # Ignorer le document existant
                                import_summary["documents"]["skipped"] += 1
                        else:
                            # Ajouter le nouveau document
                            self.add_document(document)
                            import_summary["documents"]["added"] += 1
            
            logger.info(f"Données importées avec succès: {import_summary}")
            return import_summary
        
        except Exception as e:
            logger.error(f"Erreur lors de l'importation des données: {e}")
            return None