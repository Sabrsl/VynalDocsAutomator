"""
Modèle d'administration pour l'application Vynal Docs Automator
Gère les données et les opérations liées à l'interface d'administration
"""

import logging
import os
import json
import time
import shutil
import hashlib
import threading
import sqlite3
from datetime import datetime, timedelta
import psutil
import platform

logger = logging.getLogger("VynalDocsAutomator.Admin.Model")

class AdminModel:
    """
    Modèle pour l'interface d'administration
    Fournit les méthodes pour manipuler les données administratives
    """
    
    def __init__(self, app_model=None):
        """
        Initialise le modèle d'administration
        
        Args:
            app_model: Modèle principal de l'application
        """
        self.app_model = app_model
        
        # Configuration
        self.base_dir = os.path.join(os.path.expanduser("~"), ".vynal_docs_automator")
        self.admin_dir = os.path.join(self.base_dir, "admin")
        
        # Répertoires de données
        self.data_dir = os.path.join(self.admin_dir, "data")
        self.logs_dir = os.path.join(self.admin_dir, "logs")
        self.backup_dir = os.path.join(self.admin_dir, "backups")
        self.temp_dir = os.path.join(self.admin_dir, "temp")
        
        # Fichiers de données
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.activities_file = os.path.join(self.data_dir, "activities.json")
        self.alerts_file = os.path.join(self.data_dir, "alerts.json")
        self.stats_file = os.path.join(self.data_dir, "statistics.json")
        self.db_file = os.path.join(self.data_dir, "admin.db")
        
        # Variables d'état
        self.system_alerts = []
        self.admin_activities = []
        self.start_time = datetime.now()
        self.last_backup_time = None
        self.current_user = None
        
        # Mutex pour les opérations concurrentes
        self.users_lock = threading.Lock()
        self.activities_lock = threading.Lock()
        self.alerts_lock = threading.Lock()
        
        # Initialisation
        self._init_directories()
        self._init_data_files()
        self._init_database()
        
        # Charger les données
        self._load_data()
        
        logger.info("Modèle d'administration initialisé")
    
    def _init_directories(self):
        """
        Initialise les répertoires nécessaires
        """
        directories = [self.data_dir, self.logs_dir, self.backup_dir, self.temp_dir]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Répertoire créé/vérifié: {directory}")
    
    def _init_data_files(self):
        """
        Initialise les fichiers de données
        """
        # Créer des structures vides si les fichiers n'existent pas
        if not os.path.exists(self.users_file):
            admin_user = {
                "id": "usr_001",
                "email": "admin@example.com",
                "password": self._hash_password("admin123"),  # Mot de passe temporaire
                "first_name": "Admin",
                "last_name": "Système",
                "role": "admin",
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "last_login": None
            }
            self._save_json([admin_user], self.users_file)
            logger.info("Fichier utilisateurs créé avec utilisateur admin par défaut")
        
        if not os.path.exists(self.activities_file):
            self._save_json([], self.activities_file)
            logger.debug("Fichier activités créé")
        
        if not os.path.exists(self.alerts_file):
            self._save_json([], self.alerts_file)
            logger.debug("Fichier alertes créé")
        
        if not os.path.exists(self.stats_file):
            stats = {
                "last_backup": None,
                "last_integrity_check": None,
                "last_optimization": None,
                "user_count": 1,
                "document_count": 0,
                "template_count": 0,
                "activity_count": 0
            }
            self._save_json(stats, self.stats_file)
            logger.debug("Fichier statistiques créé")
    
    def _init_database(self):
        """
        Initialise la base de données SQLite pour les données complexes ou volumineuses
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Table des journaux système (pour une meilleure performance avec de grands volumes)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                source TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT
            )
            ''')
            
            # Table des métriques système (pour les statistiques historiques)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cpu_usage REAL,
                memory_usage REAL,
                disk_usage REAL,
                active_users INTEGER,
                response_time REAL
            )
            ''')
            
            # Table des actions administratives (pour audit)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                details TEXT,
                ip_address TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Base de données initialisée")
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
            # Continuer malgré l'erreur pour ne pas bloquer l'application
    
    def _load_data(self):
        """
        Charge les données depuis les fichiers
        """
        try:
            # Charger les alertes système
            self.system_alerts = self._load_json(self.alerts_file) or []
            
            # Charger les activités récentes
            self.admin_activities = self._load_json(self.activities_file) or []
            
            # Charger les statistiques
            stats = self._load_json(self.stats_file) or {}
            if "last_backup" in stats and stats["last_backup"]:
                self.last_backup_time = datetime.fromisoformat(stats["last_backup"])
            
            logger.info("Données administratives chargées")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données: {e}")
    
    def _save_json(self, data, filepath):
        """
        Sauvegarde des données au format JSON
        
        Args:
            data: Données à sauvegarder
            filepath: Chemin du fichier
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde JSON ({filepath}): {e}")
            return False
    
    def _load_json(self, filepath):
        """
        Charge des données depuis un fichier JSON
        
        Args:
            filepath: Chemin du fichier
            
        Returns:
            dict/list: Données chargées ou None en cas d'erreur
        """
        try:
            if not os.path.exists(filepath):
                return None
                
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement JSON ({filepath}): {e}")
            return None
    
    def _hash_password(self, password):
        """
        Hache un mot de passe avec salt
        
        Args:
            password: Mot de passe en clair
            
        Returns:
            str: Mot de passe haché
        """
        # Salt fixe pour la démo (dans une implémentation réelle, utilisez un salt aléatoire par utilisateur)
        salt = "vynal_docs_salt"
        salted = password + salt
        
        # Utiliser SHA-256 pour le hachage
        hashed = hashlib.sha256(salted.encode()).hexdigest()
        return hashed
    
    def verify_password(self, password, hashed_password):
        """
        Vérifie si un mot de passe correspond à sa version hachée
        
        Args:
            password: Mot de passe en clair
            hashed_password: Mot de passe haché
            
        Returns:
            bool: True si le mot de passe est correct, False sinon
        """
        return self._hash_password(password) == hashed_password
    
    #-----------------------
    # Gestion des utilisateurs
    #-----------------------
    
    def get_users(self):
        """
        Récupère la liste des utilisateurs
        
        Returns:
            list: Liste des utilisateurs
        """
        with self.users_lock:
            return self._load_json(self.users_file) or []
    
    def get_user_by_id(self, user_id):
        """
        Récupère un utilisateur par son ID
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            dict: Utilisateur ou None si non trouvé
        """
        users = self.get_users()
        for user in users:
            if user.get("id") == user_id:
                return user
        return None
    
    def get_user_by_email(self, email):
        """
        Récupère un utilisateur par son email
        
        Args:
            email: Email de l'utilisateur
            
        Returns:
            dict: Utilisateur ou None si non trouvé
        """
        users = self.get_users()
        for user in users:
            if user.get("email") == email:
                return user
        return None
    
    def add_user(self, user_data):
        """
        Ajoute un nouvel utilisateur
        
        Args:
            user_data: Données de l'utilisateur
            
        Returns:
            bool: True si l'ajout a réussi, False sinon
        """
        # Vérifier les données requises
        required_fields = ["email", "password"]
        if not all(field in user_data for field in required_fields):
            logger.error(f"Données utilisateur incomplètes")
            return False
        
        with self.users_lock:
            # Vérifier si l'email est déjà utilisé
            existing_user = self.get_user_by_email(user_data["email"])
            if existing_user:
                logger.error(f"L'email {user_data['email']} est déjà utilisé")
                return False
            
            # Générer un ID si non fourni
            if "id" not in user_data:
                user_data["id"] = self.generate_user_id()
            
            # Hacher le mot de passe
            if "password" in user_data:
                user_data["password"] = self._hash_password(user_data["password"])
            
            # Ajouter les champs par défaut
            user_data.setdefault("role", "user")
            user_data.setdefault("is_active", True)
            user_data.setdefault("created_at", datetime.now().isoformat())
            
            # Ajouter l'utilisateur
            users = self.get_users()
            users.append(user_data)
            
            # Sauvegarder
            success = self._save_json(users, self.users_file)
            
            if success:
                # Mettre à jour les statistiques
                self.update_statistics("user_count", len(users))
                
                # Journaliser l'action
                self.add_activity(
                    "Nouvel utilisateur créé",
                    f"Email: {user_data['email']}, Rôle: {user_data['role']}",
                    "user",
                    user_data['id']
                )
            
            return success
    
    def update_user(self, user_data):
        """
        Met à jour un utilisateur existant
        
        Args:
            user_data: Données de l'utilisateur à mettre à jour
            
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        # Vérifier l'ID
        if "id" not in user_data:
            logger.error("ID utilisateur manquant")
            return False
        
        with self.users_lock:
            users = self.get_users()
            
            # Trouver l'utilisateur
            for i, user in enumerate(users):
                if user.get("id") == user_data["id"]:
                    # Si le mot de passe est fourni et non haché, le hacher
                    if "password" in user_data and len(user_data["password"]) < 40:
                        user_data["password"] = self._hash_password(user_data["password"])
                    
                    # Préserver les champs non modifiés
                    for key in user:
                        if key not in user_data:
                            user_data[key] = user[key]
                    
                    # Mettre à jour l'horodatage
                    user_data["updated_at"] = datetime.now().isoformat()
                    
                    # Remplacer l'utilisateur
                    users[i] = user_data
                    
                    # Sauvegarder
                    success = self._save_json(users, self.users_file)
                    
                    if success:
                        # Journaliser l'action
                        self.add_activity(
                            "Utilisateur mis à jour",
                            f"ID: {user_data['id']}, Email: {user_data.get('email')}",
                            "user",
                            user_data['id']
                        )
                    
                    return success
            
            logger.error(f"Utilisateur avec ID {user_data['id']} non trouvé")
            return False
    
    def delete_user(self, user_id):
        """
        Supprime un utilisateur
        
        Args:
            user_id: ID de l'utilisateur à supprimer
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        with self.users_lock:
            users = self.get_users()
            
            # Trouver l'utilisateur
            user_to_delete = None
            for user in users:
                if user.get("id") == user_id:
                    user_to_delete = user
                    break
            
            if not user_to_delete:
                logger.error(f"Utilisateur avec ID {user_id} non trouvé")
                return False
            
            # Vérifier qu'il reste au moins un administrateur
            if user_to_delete.get("role") == "admin" and len([u for u in users if u.get("role") == "admin"]) <= 1:
                logger.error("Impossible de supprimer le dernier administrateur")
                return False
            
            # Supprimer l'utilisateur
            users.remove(user_to_delete)
            
            # Sauvegarder
            success = self._save_json(users, self.users_file)
            
            if success:
                # Mettre à jour les statistiques
                self.update_statistics("user_count", len(users))
                
                # Journaliser l'action
                self.add_activity(
                    "Utilisateur supprimé",
                    f"ID: {user_id}, Email: {user_to_delete.get('email')}",
                    "user",
                    user_id
                )
            
            return success
    
    def generate_user_id(self):
        """
        Génère un nouvel ID utilisateur unique
        
        Returns:
            str: ID utilisateur
        """
        users = self.get_users()
        
        # Trouver le plus grand ID
        max_id = 0
        for user in users:
            if "id" in user and user["id"].startswith("usr_"):
                try:
                    id_num = int(user["id"][4:])
                    max_id = max(max_id, id_num)
                except ValueError:
                    pass
        
        # Générer le nouvel ID
        return f"usr_{max_id + 1:03d}"
    
    def authenticate_user(self, email, password):
        """
        Authentifie un utilisateur
        
        Args:
            email: Email de l'utilisateur
            password: Mot de passe
            
        Returns:
            dict: Utilisateur authentifié ou None si échec
        """
        user = self.get_user_by_email(email)
        
        if not user:
            logger.warning(f"Tentative de connexion avec email inconnu: {email}")
            return None
        
        if not user.get("is_active", True):
            logger.warning(f"Tentative de connexion avec compte désactivé: {email}")
            return None
        
        if not self.verify_password(password, user.get("password", "")):
            logger.warning(f"Tentative de connexion avec mot de passe incorrect: {email}")
            return None
        
        # Mettre à jour la date de dernière connexion
        user["last_login"] = datetime.now().isoformat()
        self.update_user(user)
        
        # Définir l'utilisateur courant
        self.current_user = user
        
        # Journaliser la connexion
        self.add_admin_action(user["id"], "login", f"Connexion réussie pour {email}")
        
        # Retourner une copie sans le mot de passe
        user_copy = user.copy()
        if "password" in user_copy:
            del user_copy["password"]
        
        return user_copy
    
    def logout_user(self):
        """
        Déconnecte l'utilisateur courant
        
        Returns:
            bool: True si la déconnexion a réussi
        """
        if self.current_user:
            user_id = self.current_user["id"]
            self.add_admin_action(user_id, "logout", "Déconnexion")
            self.current_user = None
            return True
        return False
    
    #-----------------------
    # Activités et journalisation
    #-----------------------
    
    def add_activity(self, description, details=None, activity_type="admin", user_id=None):
        """
        Ajoute une activité au journal
        
        Args:
            description: Description de l'activité
            details: Détails supplémentaires
            activity_type: Type d'activité ('admin', 'user', 'system', etc.)
            user_id: ID de l'utilisateur associé
            
        Returns:
            dict: Activité créée
        """
        with self.activities_lock:
            # Créer l'activité
            activity = {
                "id": f"act_{int(time.time())}_{os.urandom(4).hex()}",
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "type": activity_type
            }
            
            if details:
                activity["details"] = details
            
            if user_id:
                activity["user_id"] = user_id
            elif self.current_user:
                activity["user_id"] = self.current_user["id"]
                activity["user"] = f"{self.current_user.get('first_name', '')} {self.current_user.get('last_name', '')}".strip()
            
            # Ajouter à la liste locale
            self.admin_activities.append(activity)
            
            # Limiter la taille de la liste en mémoire
            if len(self.admin_activities) > 1000:
                self.admin_activities = self.admin_activities[-1000:]
            
            # Charger toutes les activités
            activities = self._load_json(self.activities_file) or []
            activities.append(activity)
            
            # Limiter la taille du fichier
            if len(activities) > 10000:
                activities = activities[-10000:]
            
            # Sauvegarder
            self._save_json(activities, self.activities_file)
            
            # Mettre à jour les statistiques
            self.update_statistics("activity_count", len(activities))
            
            return activity
    
    def get_recent_activities(self, activity_type=None, limit=50, user_id=None):
        """
        Récupère les activités récentes
        
        Args:
            activity_type: Type d'activité à filtrer
            limit: Nombre maximum d'activités à récupérer
            user_id: ID de l'utilisateur à filtrer
            
        Returns:
            list: Liste des activités récentes
        """
        try:
            # Utiliser la liste en mémoire si possible
            activities = self.admin_activities.copy()
            
            # Filtrer par type si demandé
            if activity_type:
                activities = [a for a in activities if a.get("type") == activity_type]
            
            # Filtrer par utilisateur si demandé
            if user_id:
                activities = [a for a in activities if a.get("user_id") == user_id]
            
            # Trier par date (plus récente en premier)
            activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Limiter le nombre de résultats
            return activities[:limit]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des activités: {e}")
            return []
    
    def add_admin_action(self, user_id, action_type, details, ip_address=None):
        """
        Ajoute une action administrative à la base de données (pour audit)
        
        Args:
            user_id: ID de l'utilisateur
            action_type: Type d'action
            details: Détails de l'action
            ip_address: Adresse IP de l'utilisateur
            
        Returns:
            bool: True si l'ajout a réussi
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO admin_actions (timestamp, user_id, action_type, details, ip_address) VALUES (?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), user_id, action_type, details, ip_address)
            )
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de l'ajout d'une action administrative: {e}")
            return False
    
    def get_admin_actions(self, user_id=None, action_type=None, start_date=None, end_date=None, limit=100):
        """
        Récupère les actions administratives pour audit
        
        Args:
            user_id: ID de l'utilisateur à filtrer
            action_type: Type d'action à filtrer
            start_date: Date de début
            end_date: Date de fin
            limit: Nombre maximum d'actions à récupérer
            
        Returns:
            list: Liste des actions administratives
        """
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM admin_actions WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if action_type:
                query += " AND action_type = ?"
                params.append(action_type)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convertir en liste de dictionnaires
            result = [dict(row) for row in rows]
            
            conn.close()
            return result
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de la récupération des actions administratives: {e}")
            return []
    
    def add_system_log(self, level, source, message, details=None):
        """
        Ajoute une entrée au journal système
        
        Args:
            level: Niveau de log ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            source: Source du log
            message: Message du log
            details: Détails supplémentaires
            
        Returns:
            bool: True si l'ajout a réussi
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO system_logs (timestamp, level, source, message, details) VALUES (?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), level, source, message, details)
            )
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de l'ajout d'un log système: {e}")
            return False
    
    def get_system_logs(self, level=None, source=None, date_from=None, date_to=None, search_text=None, limit=1000):
        """
        Récupère les logs système
        
        Args:
            level: Niveau de log à filtrer
            source: Source à filtrer
            date_from: Date de début
            date_to: Date de fin
            search_text: Texte à rechercher
            limit: Nombre maximum de logs à récupérer
            
        Returns:
            list: Liste des logs système
        """
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM system_logs WHERE 1=1"
            params = []
            
            if level:
                query += " AND level = ?"
                params.append(level)
            
            if source:
                query += " AND source = ?"
                params.append(source)
            
            if date_from:
                query += " AND timestamp >= ?"
                params.append(date_from.isoformat())
            
            if date_to:
                query += " AND timestamp <= ?"
                params.append(date_to.isoformat())
            
            if search_text:
                query += " AND (message LIKE ? OR details LIKE ?)"
                params.extend([f"%{search_text}%", f"%{search_text}%"])
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convertir en liste de dictionnaires
            result = [dict(row) for row in rows]
            
            conn.close()
            return result
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de la récupération des logs système: {e}")
            return []
    
    #-----------------------
    # Alertes système
    #-----------------------
    
    def add_system_alert(self, title, message, level="info", action=None):
        """
        Ajoute une alerte système
        
        Args:
            title: Titre de l'alerte
            message: Message détaillé
            level: Niveau de l'alerte ('info', 'warning', 'critical')
            action: Action possible (texte du bouton)
            
        Returns:
            dict: Alerte créée
        """
        with self.alerts_lock:
            # Créer l'alerte
            alert = {
                "id": f"alt_{int(time.time())}_{os.urandom(4).hex()}",
                "title": title,
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "is_read": False
            }
            
            # Vérifier s'il existe déjà une alerte similaire
            for i, existing_alert in enumerate(self.system_alerts):
                if existing_alert.get("title") == title and existing_alert.get("level") == level:
                    # Mettre à jour l'alerte existante
                    alert["id"] = existing_alert["id"]  # Conserver l'ID
                    self.system_alerts[i] = alert
                    break
            else:
                # Ajouter la nouvelle alerte
                self.system_alerts.append(alert)
            
            # Limiter le nombre d'alertes
            if len(self.system_alerts) > 100:
                self.system_alerts = sorted(
                    self.system_alerts,
                    key=lambda x: x.get("timestamp", ""),
                    reverse=True
                )[:100]
            
            # Sauvegarder
            self._save_json(self.system_alerts, self.alerts_file)
            
            # Journaliser
            self.add_system_log(
                "WARNING" if level in ["warning", "critical"] else "INFO",
                "System",
                f"Alerte système: {title}",
                message
            )
            
            return alert
    
    def mark_alert_as_read(self, alert_id):
        """
        Marque une alerte comme lue
        
        Args:
            alert_id: ID de l'alerte
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        with self.alerts_lock:
            for i, alert in enumerate(self.system_alerts):
                if alert.get("id") == alert_id:
                    # Marquer comme lue
                    self.system_alerts[i]["is_read"] = True
                    
                    # Sauvegarder
                    self._save_json(self.system_alerts, self.alerts_file)
                    return True
            
            return False
    
    def delete_alert(self, alert_id):
        """
        Supprime une alerte
        
        Args:
            alert_id: ID de l'alerte
            
        Returns:
            bool: True si la suppression a réussi
        """
        with self.alerts_lock:
            for i, alert in enumerate(self.system_alerts):
                if alert.get("id") == alert_id:
                    # Supprimer l'alerte
                    del self.system_alerts[i]
                    
                    # Sauvegarder
                    self._save_json(self.system_alerts, self.alerts_file)
                    return True
            
            return False
    
    def get_active_alerts(self, level=None):
        """
        Récupère les alertes actives
        
        Args:
            level: Niveau des alertes à filtrer
            
        Returns:
            list: Liste des alertes actives
        """
        # Filtrer par niveau si demandé
        if level:
            return [alert for alert in self.system_alerts if alert.get("level") == level]
        
        return self.system_alerts
    
    #-----------------------
    # Surveillance système
    #-----------------------
    
    def record_system_metrics(self):
        """
        Enregistre les métriques système actuelles
        
        Returns:
            dict: Métriques enregistrées
        """
        try:
            # Récupérer les métriques
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Nombre d'utilisateurs actifs (simulé pour la démo)
            active_users = 1  # Remplacer par une vraie valeur
            
            # Temps de réponse moyen (simulé pour la démo)
            response_time = 0.2  # Remplacer par une vraie valeur
            
            # Enregistrer dans la base de données
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO system_metrics (timestamp, cpu_usage, memory_usage, disk_usage, active_users, response_time) VALUES (?, ?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), cpu_usage, memory_usage, disk_usage, active_users, response_time)
            )
            
            conn.commit()
            conn.close()
            
            # Retourner les métriques
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "active_users": active_users,
                "response_time": response_time
            }
            
            # Vérifier les seuils critiques
            self.check_critical_thresholds(metrics)
            
            return metrics
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des métriques système: {e}")
            return None
    
    def check_critical_thresholds(self, metrics):
        """
        Vérifie si les métriques dépassent des seuils critiques et génère des alertes
        
        Args:
            metrics: Métriques à vérifier
        """
        try:
            # Seuil CPU
            if metrics["cpu_usage"] > 80:
                self.add_system_alert(
                    "Utilisation CPU élevée",
                    f"L'utilisation du CPU est de {metrics['cpu_usage']}%, ce qui peut affecter les performances.",
                    "warning"
                )
            
            # Seuil mémoire
            if metrics["memory_usage"] > 85:
                self.add_system_alert(
                    "Mémoire faible",
                    f"Utilisation de la mémoire: {metrics['memory_usage']}%. Pensez à fermer des applications inutilisées.",
                    "warning"
                )
            
            # Seuil disque
            if metrics["disk_usage"] > 90:
                self.add_system_alert(
                    "Espace disque faible",
                    f"Il reste seulement {100 - metrics['disk_usage']}% d'espace disque libre.",
                    "critical" if metrics["disk_usage"] > 95 else "warning"
                )
            
            # Seuil temps de réponse
            if metrics["response_time"] > 1.0:
                self.add_system_alert(
                    "Temps de réponse élevé",
                    f"Le temps de réponse moyen est de {metrics['response_time']:.2f} secondes.",
                    "warning"
                )
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des seuils critiques: {e}")
    
    def get_system_metrics(self, period="day"):
        """
        Récupère les métriques système pour une période donnée
        
        Args:
            period: Période ('hour', 'day', 'week', 'month')
            
        Returns:
            list: Liste des métriques
        """
        try:
            # Déterminer la date de début
            now = datetime.now()
            if period == "hour":
                start_date = now - timedelta(hours=1)
            elif period == "day":
                start_date = now - timedelta(days=1)
            elif period == "week":
                start_date = now - timedelta(weeks=1)
            elif period == "month":
                start_date = now - timedelta(days=30)
            else:
                start_date = now - timedelta(days=1)  # Par défaut: 1 jour
            
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Limiter le nombre de points pour éviter de surcharger l'interface
            if period == "hour":
                interval = "5 minutes"
                max_points = 12
            elif period == "day":
                interval = "1 hour"
                max_points = 24
            elif period == "week":
                interval = "4 hours"
                max_points = 42
            else:  # month
                interval = "1 day"
                max_points = 30
            
            # Requête avec échantillonnage
            query = f"""
            WITH numbered_rows AS (
                SELECT
                    timestamp,
                    cpu_usage,
                    memory_usage,
                    disk_usage,
                    active_users,
                    response_time,
                    ROW_NUMBER() OVER (ORDER BY timestamp DESC) as row_num
                FROM
                    system_metrics
                WHERE
                    timestamp >= ?
            )
            SELECT * FROM numbered_rows
            WHERE (row_num - 1) % (CAST((SELECT COUNT(*) FROM numbered_rows) AS REAL) / ? + 1) < 1
            ORDER BY timestamp
            """
            
            cursor.execute(query, (start_date.isoformat(), max_points))
            rows = cursor.fetchall()
            
            # Convertir en liste de dictionnaires
            result = [dict(row) for row in rows]
            
            conn.close()
            return result
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de la récupération des métriques système: {e}")
            return []
    
    def get_system_info(self):
        """
        Récupère les informations système actuelles
        
        Returns:
            dict: Informations système
        """
        try:
            # Informations générales
            info = {
                "os_name": platform.system(),
                "os_version": platform.version(),
                "os_release": platform.release(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
                
                # Ressources système
                "cpu_count": psutil.cpu_count(logical=False),
                "cpu_threads": psutil.cpu_count(logical=True),
                "cpu_usage": psutil.cpu_percent(interval=0.1),
                
                # Mémoire
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "memory_used": psutil.virtual_memory().used,
                "memory_percent": psutil.virtual_memory().percent,
                
                # Disque
                "disk_total": psutil.disk_usage('/').total,
                "disk_free": psutil.disk_usage('/').free,
                "disk_used": psutil.disk_usage('/').used,
                "disk_percent": psutil.disk_usage('/').percent,
                
                # Application
                "app_uptime": (datetime.now() - self.start_time).total_seconds(),
                "app_version": getattr(self.app_model, 'version', "1.0.0"),
                "app_start_time": self.start_time.isoformat()
            }
            
            return info
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des informations système: {e}")
            return {}
    
    #-----------------------
    # Opérations système
    #-----------------------
    
    def perform_backup(self, backup_type="full"):
        """
        Effectue une sauvegarde des données
        
        Args:
            backup_type: Type de sauvegarde ('full', 'incremental')
            
        Returns:
            dict: Informations sur la sauvegarde effectuée
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{backup_type}_{timestamp}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Créer un fichier zip
            with shutil.ZipFile(backup_path, 'w', shutil.ZIP_DEFLATED) as zipf:
                # Ajouter les fichiers de données
                data_files = [self.users_file, self.activities_file, self.alerts_file, self.stats_file]
                for file in data_files:
                    if os.path.exists(file):
                        zipf.write(file, os.path.basename(file))
                
                # Ajouter la base de données
                if os.path.exists(self.db_file):
                    conn = sqlite3.connect(self.db_file)
                    # Créer une sauvegarde de la base de données
                    backup_db = os.path.join(self.temp_dir, "admin_backup.db")
                    with open(backup_db, 'wb') as f:
                        for line in conn.iterdump():
                            f.write(f"{line}\n".encode('utf-8'))
                    conn.close()
                    
                    # Ajouter la sauvegarde au zip
                    zipf.write(backup_db, "admin.db")
                    
                    # Supprimer le fichier temporaire
                    os.remove(backup_db)
                
                # Si c'est une sauvegarde complète, ajouter d'autres dossiers
                if backup_type == "full" and hasattr(self.app_model, 'data_dir'):
                    app_data_dir = self.app_model.data_dir
                    
                    # Parcourir le répertoire des données de l'application
                    for root, dirs, files in os.walk(app_data_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Exclure les très gros fichiers ou les fichiers temporaires
                            if os.path.getsize(file_path) < 100 * 1024 * 1024:  # 100 Mo max
                                # Chemin relatif dans le zip
                                rel_path = os.path.relpath(file_path, os.path.dirname(app_data_dir))
                                zipf.write(file_path, os.path.join("app_data", rel_path))
            
            # Mettre à jour la date de dernière sauvegarde
            self.last_backup_time = datetime.now()
            self.update_statistics("last_backup", self.last_backup_time.isoformat())
            
            # Nettoyer les anciennes sauvegardes
            self.cleanup_old_backups()
            
            # Journaliser
            self.add_activity("Sauvegarde effectuée", f"Type: {backup_type}, Fichier: {backup_filename}")
            
            return {
                "type": backup_type,
                "file": backup_filename,
                "path": backup_path,
                "size": os.path.getsize(backup_path),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            self.add_system_alert(
                "Échec de la sauvegarde",
                f"Une erreur est survenue: {e}",
                "critical"
            )
            return None
    
    def restore_backup(self, backup_file):
        """
        Restaure une sauvegarde
        
        Args:
            backup_file: Chemin du fichier de sauvegarde
            
        Returns:
            bool: True si la restauration a réussi
        """
        try:
            # Vérifier que le fichier existe
            if not os.path.exists(backup_file):
                logger.error(f"Fichier de sauvegarde non trouvé: {backup_file}")
                return False
            
            # Créer un répertoire temporaire pour la restauration
            restore_dir = os.path.join(self.temp_dir, f"restore_{int(time.time())}")
            os.makedirs(restore_dir, exist_ok=True)
            
            # Extraire la sauvegarde
            with shutil.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(restore_dir)
            
            # Restaurer les fichiers de données
            data_files = {
                "users.json": self.users_file,
                "activities.json": self.activities_file,
                "alerts.json": self.alerts_file,
                "statistics.json": self.stats_file
            }
            
            for src_name, dest_path in data_files.items():
                src_path = os.path.join(restore_dir, src_name)
                if os.path.exists(src_path):
                    # Créer le répertoire de destination si nécessaire
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    # Copier le fichier
                    shutil.copy2(src_path, dest_path)
            
            # Restaurer la base de données
            db_backup = os.path.join(restore_dir, "admin.db")
            if os.path.exists(db_backup):
                # Sauvegarder la base de données actuelle
                if os.path.exists(self.db_file):
                    shutil.copy2(self.db_file, f"{self.db_file}.bak")
                
                # Restaurer depuis la sauvegarde
                shutil.copy2(db_backup, self.db_file)
            
            # Restaurer les données de l'application si présentes
            app_data_dir = os.path.join(restore_dir, "app_data")
            if os.path.exists(app_data_dir) and hasattr(self.app_model, 'data_dir'):
                # Parcourir les fichiers restaurés
                for root, dirs, files in os.walk(app_data_dir):
                    rel_path = os.path.relpath(root, app_data_dir)
                    # Créer les répertoires nécessaires
                    if rel_path != '.':
                        os.makedirs(os.path.join(self.app_model.data_dir, rel_path), exist_ok=True)
                    
                    # Copier les fichiers
                    for file in files:
                        src_file = os.path.join(root, file)
                        dest_file = os.path.join(self.app_model.data_dir, rel_path, file)
                        shutil.copy2(src_file, dest_file)
            
            # Recharger les données
            self._load_data()
            
            # Nettoyer le répertoire temporaire
            shutil.rmtree(restore_dir)
            
            # Journaliser
            self.add_activity("Sauvegarde restaurée", f"Fichier: {os.path.basename(backup_file)}")
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la restauration: {e}")
            self.add_system_alert(
                "Échec de la restauration",
                f"Une erreur est survenue: {e}",
                "critical"
            )
            return False
    
    def cleanup_old_backups(self):
        """
        Nettoie les anciennes sauvegardes en fonction des paramètres
        
        Returns:
            int: Nombre de sauvegardes supprimées
        """
        try:
            # Récupérer le nombre maximum de sauvegardes à conserver
            max_backups = 5  # Par défaut
            stats = self._load_json(self.stats_file) or {}
            if "backup_count" in stats:
                try:
                    max_backups = int(stats["backup_count"])
                except ValueError:
                    pass
            
            # Lister toutes les sauvegardes
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith("backup_") and file.endswith(".zip"):
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # Trier par date (plus ancien en premier)
            backup_files.sort(key=lambda x: x[1])
            
            # Supprimer les plus anciennes
            deleted_count = 0
            if len(backup_files) > max_backups:
                for file_path, _ in backup_files[:-max_backups]:
                    os.remove(file_path)
                    deleted_count += 1
            
            return deleted_count
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des anciennes sauvegardes: {e}")
            return 0
    
    def get_backups(self):
        """
        Récupère la liste des sauvegardes disponibles
        
        Returns:
            list: Liste des sauvegardes
        """
        try:
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.startswith("backup_") and file.endswith(".zip"):
                    file_path = os.path.join(self.backup_dir, file)
                    
                    # Extraire le type de la sauvegarde
                    backup_type = "unknown"
                    if "_full_" in file:
                        backup_type = "full"
                    elif "_incremental_" in file:
                        backup_type = "incremental"
                    
                    # Extraire la date
                    timestamp = os.path.getmtime(file_path)
                    date = datetime.fromtimestamp(timestamp)
                    
                    backups.append({
                        "filename": file,
                        "type": backup_type,
                        "date": date.isoformat(),
                        "size": os.path.getsize(file_path),
                        "path": file_path
                    })
            
            # Trier par date (plus récent en premier)
            backups.sort(key=lambda x: x["date"], reverse=True)
            
            return backups
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des sauvegardes: {e}")
            return []
    
    def check_integrity(self):
        """
        Vérifie l'intégrité des données
        
        Returns:
            dict: Résultat de la vérification
        """
        try:
            start_time = time.time()
            issues = []
            
            # Vérifier les fichiers JSON
            json_files = [
                ("Utilisateurs", self.users_file),
                ("Activités", self.activities_file),
                ("Alertes", self.alerts_file),
                ("Statistiques", self.stats_file)
            ]
            
            for label, file_path in json_files:
                if not os.path.exists(file_path):
                    issues.append(f"Fichier manquant: {label} ({file_path})")
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    issues.append(f"Fichier JSON corrompu: {label} ({e})")
            
            # Vérifier la base de données
            try:
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                
                # Vérifier les tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                expected_tables = ["system_logs", "system_metrics", "admin_actions"]
                for table in expected_tables:
                    if table not in tables:
                        issues.append(f"Table manquante dans la base de données: {table}")
                
                # Vérifier PRAGMA integrity_check
                cursor.execute("PRAGMA integrity_check;")
                integrity_result = cursor.fetchone()[0]
                if integrity_result != "ok":
                    issues.append(f"Intégrité de la base de données compromise: {integrity_result}")
                
                conn.close()
            except sqlite3.Error as e:
                issues.append(f"Erreur de base de données: {e}")
            
            # Vérifier les références entre utilisateurs et activités
            try:
                users = self.get_users()
                user_ids = [user.get("id") for user in users]
                
                activities = self._load_json(self.activities_file) or []
                for activity in activities:
                    if "user_id" in activity and activity["user_id"] not in user_ids:
                        issues.append(f"Activité avec référence utilisateur invalide: {activity.get('id')}")
            except Exception as e:
                issues.append(f"Erreur lors de la vérification des références: {e}")
            
            # Mettre à jour les statistiques
            self.update_statistics("last_integrity_check", datetime.now().isoformat())
            
            # Journaliser
            self.add_activity(
                "Vérification d'intégrité effectuée",
                f"Résultat: {len(issues)} problèmes trouvés"
            )
            
            # Générer un rapport
            return {
                "success": len(issues) == 0,
                "issues": issues,
                "checked_files": len(json_files) + 1,  # +1 pour la base de données
                "duration": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'intégrité: {e}")
            return {
                "success": False,
                "issues": [f"Erreur critique: {e}"],
                "timestamp": datetime.now().isoformat()
            }
    
    def optimize_database(self):
        """
        Optimise la base de données
        
        Returns:
            bool: True si l'optimisation a réussi
        """
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Exécuter VACUUM pour compacter la base de données
            cursor.execute("VACUUM;")
            
            # Reconstruire les index
            cursor.execute("REINDEX;")
            
            conn.commit()
            conn.close()
            
            # Mettre à jour les statistiques
            self.update_statistics("last_optimization", datetime.now().isoformat())
            
            # Journaliser
            self.add_activity("Base de données optimisée", "VACUUM et REINDEX effectués")
            
            return True
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de l'optimisation de la base de données: {e}")
            return False
    
    def clean_temp_files(self):
        """
        Nettoie les fichiers temporaires
        
        Returns:
            int: Nombre de fichiers supprimés
        """
        try:
            count = 0
            
            # Nettoyer le répertoire temporaire
            for item in os.listdir(self.temp_dir):
                item_path = os.path.join(self.temp_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                        count += 1
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        count += 1
                except Exception as e:
                    logger.warning(f"Erreur lors de la suppression de {item_path}: {e}")
            
            # Journaliser
            self.add_activity("Nettoyage des fichiers temporaires", f"{count} éléments supprimés")
            
            return count
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des fichiers temporaires: {e}")
            return 0
    
    #-----------------------
    # Statistiques
    #-----------------------
    
    def update_statistics(self, key, value):
        """
        Met à jour une statistique
        
        Args:
            key: Clé de la statistique
            value: Valeur
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        try:
            # Charger les statistiques
            stats = self._load_json(self.stats_file) or {}
            
            # Mettre à jour
            stats[key] = value
            
            # Sauvegarder
            return self._save_json(stats, self.stats_file)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des statistiques: {e}")
            return False
    
    def get_statistics(self):
        """
        Récupère toutes les statistiques
        
        Returns:
            dict: Statistiques
        """
        return self._load_json(self.stats_file) or {}
    
    def get_usage_statistics(self, period="month"):
        """
        Récupère les statistiques d'utilisation
        
        Args:
            period: Période ('day', 'week', 'month', 'year')
            
        Returns:
            dict: Statistiques d'utilisation
        """
        try:
            # Déterminer la date de début
            now = datetime.now()
            if period == "day":
                start_date = now - timedelta(days=1)
            elif period == "week":
                start_date = now - timedelta(weeks=1)
            elif period == "month":
                start_date = now - timedelta(days=30)
            elif period == "year":
                start_date = now - timedelta(days=365)
            else:
                start_date = now - timedelta(days=30)  # Par défaut: 30 jours
            
            # Convertir en chaîne ISO
            start_date_str = start_date.isoformat()
            
            # Initialiser les résultats
            results = {
                "activities": 0,
                "users": 0,
                "logins": 0,
                "documents": 0,
                "errors": 0,
                "chart_data": []
            }
            
            # Activités récentes
            activities = self._load_json(self.activities_file) or []
            recent_activities = [a for a in activities if a.get("timestamp", "") >= start_date_str]
            results["activities"] = len(recent_activities)
            
            # Compter les activités par type
            activity_types = {}
            for activity in recent_activities:
                activity_type = activity.get("type", "unknown")
                activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
            
            results["activity_types"] = activity_types
            
            # Utilisateurs récents
            users = self.get_users()
            for user in users:
                if user.get("last_login") and user.get("last_login") >= start_date_str:
                    results["users"] += 1
            
            # Connexions (depuis les actions admin)
            try:
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                
                # Compter les connexions
                cursor.execute(
                    "SELECT COUNT(*) FROM admin_actions WHERE action_type = 'login' AND timestamp >= ?",
                    (start_date_str,)
                )
                results["logins"] = cursor.fetchone()[0]
                
                # Compter les erreurs
                cursor.execute(
                    "SELECT COUNT(*) FROM system_logs WHERE level IN ('ERROR', 'CRITICAL') AND timestamp >= ?",
                    (start_date_str,)
                )
                results["errors"] = cursor.fetchone()[0]
                
                conn.close()
            except sqlite3.Error as e:
                logger.error(f"Erreur lors de la récupération des statistiques de connexion: {e}")
            
            # Données pour graphique (activités par jour)
            if len(recent_activities) > 0:
                # Définir l'intervalle en fonction de la période
                if period == "day":
                    interval = "hour"
                    format_str = "%Y-%m-%d %H:00"
                elif period == "week":
                    interval = "day"
                    format_str = "%Y-%m-%d"
                else:  # month ou year
                    interval = "day"
                    format_str = "%Y-%m-%d"
                
                # Regrouper les activités par intervalle
                activity_data = {}
                for activity in recent_activities:
                    try:
                        timestamp = datetime.fromisoformat(activity["timestamp"])
                        
                        if interval == "hour":
                            key = timestamp.replace(minute=0, second=0, microsecond=0).strftime(format_str)
                        elif interval == "day":
                            key = timestamp.replace(hour=0, minute=0, second=0, microsecond=0).strftime(format_str)
                        else:
                            key = timestamp.replace(hour=0, minute=0, second=0, microsecond=0).strftime(format_str)
                        
                        if key not in activity_data:
                            activity_data[key] = 0
                        activity_data[key] += 1
                    except (ValueError, TypeError):
                        pass
                
                # Convertir en liste de points pour le graphique
                chart_data = [{"date": k, "count": v} for k, v in activity_data.items()]
                chart_data.sort(key=lambda x: x["date"])
                
                results["chart_data"] = chart_data
            
            # Documents (si disponible via le modèle principal)
            if hasattr(self.app_model, 'documents'):
                results["documents"] = len(self.app_model.documents)
            
            return results
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques d'utilisation: {e}")
            return {"error": str(e)}
    
    #-----------------------
    # Configuration et intégration
    #-----------------------
    
    def get_config(self, key, default=None):
        """
        Récupère une valeur de configuration
        
        Args:
            key: Clé de configuration (peut utiliser la notation pointée, ex: 'app.name')
            default: Valeur par défaut si la clé n'existe pas
            
        Returns:
            any: Valeur de configuration
        """
        if hasattr(self.app_model, 'config') and hasattr(self.app_model.config, 'get'):
            return self.app_model.config.get(key, default)
        return default
    
    def set_config(self, key, value):
        """
        Définit une valeur de configuration
        
        Args:
            key: Clé de configuration
            value: Valeur
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        if hasattr(self.app_model, 'config') and hasattr(self.app_model.config, 'update'):
            return self.app_model.config.update(key, value)
        return False
    
    def reset_config(self):
        """
        Réinitialise la configuration aux valeurs par défaut
        
        Returns:
            bool: True si la réinitialisation a réussi
        """
        if hasattr(self.app_model, 'config') and hasattr(self.app_model.config, 'reset'):
            return self.app_model.config.reset()
        return False
    
    def import_data(self, filepath, data_type, options=None):
        """
        Importe des données depuis un fichier
        
        Args:
            filepath: Chemin du fichier à importer
            data_type: Type de données ('users', 'templates', 'documents', etc.)
            options: Options d'importation
            
        Returns:
            dict: Résultat de l'importation
        """
        try:
            if not os.path.exists(filepath):
                return {"success": False, "error": "Fichier non trouvé", "imported": 0}
            
            options = options or {}
            imported = 0
            errors = []
            
            # Importer selon le type de données
            if data_type == "users":
                # Lire le fichier
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not isinstance(data, list):
                    return {"success": False, "error": "Format invalide, liste attendue", "imported": 0}
                
                # Importer chaque utilisateur
                for user_data in data:
                    try:
                        # Vérifier les champs requis
                        if "email" not in user_data:
                            errors.append(f"Utilisateur sans email ignoré")
                            continue
                        
                        # Vérifier si l'utilisateur existe déjà
                        existing_user = self.get_user_by_email(user_data["email"])
                        if existing_user:
                            if options.get("overwrite"):
                                # Mettre à jour l'utilisateur existant
                                user_data["id"] = existing_user["id"]
                                if "password" not in user_data and "password" in existing_user:
                                    user_data["password"] = existing_user["password"]
                                
                                if self.update_user(user_data):
                                    imported += 1
                                else:
                                    errors.append(f"Erreur lors de la mise à jour de {user_data['email']}")
                            else:
                                errors.append(f"Utilisateur existant ignoré: {user_data['email']}")
                        else:
                            # Créer un nouvel utilisateur
                            if "password" not in user_data:
                                user_data["password"] = "changeme"  # Mot de passe temporaire
                            
                            if self.add_user(user_data):
                                imported += 1
                            else:
                                errors.append(f"Erreur lors de la création de {user_data['email']}")
                    except Exception as e:
                        errors.append(f"Erreur pour {user_data.get('email', 'utilisateur inconnu')}: {e}")
            
            # Ajouter d'autres types d'importation selon les besoins
            else:
                return {"success": False, "error": f"Type d'importation non pris en charge: {data_type}", "imported": 0}
            
            # Journaliser
            self.add_activity(
                f"Importation de {data_type}",
                f"Fichier: {os.path.basename(filepath)}, {imported} éléments importés"
            )
            
            return {
                "success": imported > 0,
                "imported": imported,
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'importation: {e}")
            return {"success": False, "error": str(e), "imported": 0}
    
    def export_data(self, data_type, options=None):
        """
        Exporte des données vers un fichier
        
        Args:
            data_type: Type de données ('users', 'activities', 'logs', etc.)
            options: Options d'exportation
            
        Returns:
            dict: Résultat de l'exportation avec le chemin du fichier
        """
        try:
            options = options or {}
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Déterminer le format et le répertoire
            format_ext = options.get("format", "json")
            export_dir = os.path.join(self.temp_dir, "exports")
            os.makedirs(export_dir, exist_ok=True)
            
            filename = f"export_{data_type}_{timestamp}.{format_ext}"
            filepath = os.path.join(export_dir, filename)
            
            exported = 0
            
            # Exporter selon le type de données
            if data_type == "users":
                users = self.get_users()
                
                # Filtrer les champs sensibles si demandé
                if options.get("exclude_sensitive", True):
                    for user in users:
                        if "password" in user:
                            del user["password"]
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(users, f, ensure_ascii=False, indent=2, default=str)
                
                exported = len(users)
            
            elif data_type == "activities":
                activities = self._load_json(self.activities_file) or []
                
                # Filtrer par date si demandé
                if "start_date" in options:
                    start_date = options["start_date"]
                    activities = [a for a in activities if a.get("timestamp", "") >= start_date]
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(activities, f, ensure_ascii=False, indent=2, default=str)
                
                exported = len(activities)
            
            elif data_type == "logs":
                # Récupérer les logs de la base de données
                logs = self.get_system_logs(
                    level=options.get("level"),
                    source=options.get("source"),
                    date_from=options.get("start_date"),
                    date_to=options.get("end_date"),
                    search_text=options.get("search"),
                    limit=options.get("limit", 10000)
                )
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, ensure_ascii=False, indent=2, default=str)
                
                exported = len(logs)
            
            # Ajouter d'autres types d'exportation selon les besoins
            else:
                return {"success": False, "error": f"Type d'exportation non pris en charge: {data_type}", "exported": 0}
            
            # Journaliser
            self.add_activity(
                f"Exportation de {data_type}",
                f"Fichier: {filename}, {exported} éléments exportés"
            )
            
            return {
                "success": True,
                "exported": exported,
                "file": filename,
                "path": filepath,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation: {e}")
            return {"success": False, "error": str(e), "exported": 0}
    
    #-----------------------
    # Utilitaires
    #-----------------------
    
    def format_size(self, size_bytes):
        """
        Formate une taille en octets en une chaîne lisible
        
        Args:
            size_bytes: Taille en octets
            
        Returns:
            str: Taille formatée
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def format_duration(self, seconds):
        """
        Formate une durée en secondes en une chaîne lisible
        
        Args:
            seconds: Durée en secondes
            
        Returns:
            str: Durée formatée
        """
        if seconds < 60:
            return f"{seconds:.1f} secondes"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f} heures"
        else:
            days = seconds / 86400
            return f"{days:.1f} jours"
    
    def get_app_version(self):
        """
        Récupère la version de l'application
        
        Returns:
            str: Version de l'application
        """
        # Essayer différentes sources
        if hasattr(self.app_model, 'version'):
            return self.app_model.version
        
        if hasattr(self.app_model, 'config') and hasattr(self.app_model.config, 'get'):
            return self.app_model.config.get('app.version', '1.0.0')
        
        # Valeur par défaut
        return "1.0.0"
    
    def is_update_available(self):
        """
        Vérifie si une mise à jour est disponible
        
        Returns:
            dict: Informations sur la mise à jour ou None si aucune mise à jour
        """
        # Cette méthode est une simulation
        # Dans une implémentation réelle, vous feriez une requête à un serveur de mise à jour
        
        # Pour la démo, simuler une mise à jour disponible une fois de temps en temps
        import random
        if random.random() < 0.2:  # 20% de chance
            current_version = self.get_app_version()
            
            # Simuler une nouvelle version
            version_parts = current_version.split('.')
            new_version = f"{version_parts[0]}.{version_parts[1]}.{int(version_parts[2]) + 1}"
            
            return {
                "current_version": current_version,
                "new_version": new_version,
                "release_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                "changes": [
                    "Améliorations de l'interface utilisateur",
                    "Correction de bugs",
                    "Nouvelles fonctionnalités"
                ],
                "download_url": "https://example.com/download"
            }
        
        return None#!/usr/bin/env python3
# -*- coding: utf-8 -*-

