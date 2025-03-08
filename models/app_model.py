#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modèle principal de l'application Vynal Docs Automator
Contient les fonctionnalités de base et la gestion des données
"""

import os
import json
import logging
from datetime import datetime

logger = logging.getLogger("VynalDocsAutomator.AppModel")

class AppModel:
    """
    Modèle principal contenant les données et la logique métier de l'application
    """
    
    def __init__(self, config_manager):
        """
        Initialise le modèle de l'application
        
        Args:
            config_manager: Gestionnaire de configuration de l'application
        """
        self.config = config_manager
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
        
        # Charger les données
        self.load_all_data()
        
        logger.info("AppModel initialisé")
    
    def load_all_data(self):
        """
        Charge toutes les données nécessaires au démarrage
        """
        self.load_clients()
        self.load_templates()
        self.load_documents()
        self.load_recent_activities()
        
        logger.info("Toutes les données ont été chargées")
    
    def add_activity(self, activity_type, description):
        """
        Ajoute une activité récente
        
        Args:
            activity_type: Type d'activité (ex: 'client', 'document', 'template')
            description: Description de l'activité
        """
        activity = {
            'id': len(self.recent_activities) + 1,
            'type': activity_type,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }
        
        self.recent_activities.insert(0, activity)
        
        # Limiter à 20 activités récentes
        if len(self.recent_activities) > 20:
            self.recent_activities = self.recent_activities[:20]
        
        # Sauvegarder les activités
        self.save_recent_activities()
        
        logger.info(f"Nouvelle activité ajoutée: {description}")
    
    # ---- Gestion des clients ----
    
    def load_clients(self):
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
            
            logger.info(f"{len(self.clients)} clients chargés")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des clients: {e}")
            self.clients = []
    
    def save_clients(self):
        """
        Sauvegarde les données clients dans le fichier
        """
        client_file = os.path.join(self.paths['clients'], "clients.json")
        
        try:
            with open(client_file, 'w', encoding='utf-8') as f:
                json.dump(self.clients, f, indent=2, ensure_ascii=False)
            
            logger.info(f"{len(self.clients)} clients sauvegardés")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des clients: {e}")
            return False
    
    def add_client(self, client_data):
        """
        Ajoute un nouveau client
        
        Args:
            client_data: Dictionnaire avec les données du client
        
        Returns:
            str: ID du client ajouté
        """
        # Vérifier si le client existe déjà (par email)
        existing = next((c for c in self.clients if c.get('email') == client_data.get('email')), None)
        
        if existing:
            logger.warning(f"Client avec email {client_data.get('email')} existe déjà")
            return None
        
        # Générer un ID unique
        client_id = f"client_{len(self.clients) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Ajouter l'ID et la date de création
        client_data['id'] = client_id
        client_data['created_at'] = datetime.now().isoformat()
        client_data['updated_at'] = datetime.now().isoformat()
        
        # Ajouter à la liste
        self.clients.append(client_data)
        
        # Sauvegarder
        self.save_clients()
        
        # Ajouter l'activité
        self.add_activity('client', f"Nouveau client ajouté: {client_data.get('name')}")
        
        logger.info(f"Client ajouté: {client_data.get('name')} (ID: {client_id})")
        return client_id
    
    def update_client(self, client_id, client_data):
        """
        Met à jour un client existant
        
        Args:
            client_id: ID du client à mettre à jour
            client_data: Nouvelles données du client
        
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        # Trouver le client
        client_index = next((i for i, c in enumerate(self.clients) if c.get('id') == client_id), None)
        
        if client_index is None:
            logger.warning(f"Client avec ID {client_id} non trouvé")
            return False
        
        # Mettre à jour les données
        client_data['id'] = client_id  # Assurer que l'ID reste le même
        client_data['created_at'] = self.clients[client_index].get('created_at')  # Conserver la date de création
        client_data['updated_at'] = datetime.now().isoformat()
        
        # Remplacer le client
        self.clients[client_index] = client_data
        
        # Sauvegarder
        self.save_clients()
        
        # Ajouter l'activité
        self.add_activity('client', f"Client mis à jour: {client_data.get('name')}")
        
        logger.info(f"Client mis à jour: {client_data.get('name')} (ID: {client_id})")
        return True
    
    def delete_client(self, client_id):
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
        
        # Supprimer le client
        self.clients = [c for c in self.clients if c.get('id') != client_id]
        
        # Sauvegarder
        self.save_clients()
        
        # Ajouter l'activité
        self.add_activity('client', f"Client supprimé: {client.get('name')}")
        
        logger.info(f"Client supprimé: {client.get('name')} (ID: {client_id})")
        return True
    
    def get_client(self, client_id):
        """
        Récupère un client par son ID
        
        Args:
            client_id: ID du client à récupérer
        
        Returns:
            dict: Données du client ou None si non trouvé
        """
        return next((c for c in self.clients if c.get('id') == client_id), None)
    
    def get_all_clients(self):
        """
        Récupère tous les clients
        
        Returns:
            list: Liste de tous les clients
        """
        return self.clients
    
    # ---- Gestion des modèles de documents ----
    
    def load_templates(self):
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
            with open(template_file, 'r', encoding='utf-8') as f:
                self.templates = json.load(f)
            
            logger.info(f"{len(self.templates)} modèles chargés")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des modèles: {e}")
            self.templates = []
    
    def save_templates(self):
        """
        Sauvegarde les modèles de documents
        """
        template_file = os.path.join(self.paths['templates'], "templates.json")
        
        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=2, ensure_ascii=False)
            
            logger.info(f"{len(self.templates)} modèles sauvegardés")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des modèles: {e}")
            return False
    
    # Les méthodes pour ajouter, mettre à jour et supprimer des modèles suivent le même pattern que pour les clients
    
    # ---- Gestion des documents générés ----
    
    def load_documents(self):
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
            
            logger.info(f"{len(self.documents)} documents chargés")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des documents: {e}")
            self.documents = []
    
    def save_documents(self):
        """
        Sauvegarde les documents générés
        """
        document_file = os.path.join(self.paths['documents'], "documents.json")
        
        try:
            with open(document_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
            
            logger.info(f"{len(self.documents)} documents sauvegardés")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des documents: {e}")
            return False
    
    # Les méthodes pour ajouter, mettre à jour et supprimer des documents suivent le même pattern
    
    # ---- Gestion des activités récentes ----
    
    def load_recent_activities(self):
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
            
            logger.info(f"{len(self.recent_activities)} activités chargées")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des activités: {e}")
            self.recent_activities = []
    
    def save_recent_activities(self):
        """
        Sauvegarde les activités récentes
        """
        activity_file = os.path.join(self.data_dir, "activities.json")
        
        try:
            with open(activity_file, 'w', encoding='utf-8') as f:
                json.dump(self.recent_activities, f, indent=2, ensure_ascii=False)
            
            logger.info(f"{len(self.recent_activities)} activités sauvegardées")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des activités: {e}")
            return False
    
    def get_recent_activities(self, limit=10):
        """
        Récupère les activités récentes
        
        Args:
            limit: Nombre maximum d'activités à récupérer
        
        Returns:
            list: Liste des activités récentes
        """
        return self.recent_activities[:limit]