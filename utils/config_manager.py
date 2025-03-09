#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de gestion de configuration pour l'application Vynal Docs Automator.
Permet de charger, sauvegarder et accéder aux paramètres de configuration de l'application.
"""

import os
import json
import logging
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger("VynalDocsAutomator.ConfigManager")

class ConfigManager:
    """
    Gestionnaire de configuration pour l'application.
    Gère le chargement, la sauvegarde et l'accès aux paramètres de configuration.
    
    Attributes:
        config_file (str): Chemin vers le fichier de configuration
        config (dict): Configuration actuelle
        default_config (dict): Configuration par défaut
        base_dir (str): Répertoire de base de l'application
        data_dir (str): Répertoire des données de l'application
    """
    
    def __init__(self, config_file: str = None):
        """
        Initialise le gestionnaire de configuration.
        
        Args:
            config_file (str, optional): Chemin vers le fichier de configuration.
                Si None, utilise le fichier par défaut dans le répertoire de données.
        """
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        
        # S'assurer que le répertoire de données existe
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Définir le fichier de configuration
        if config_file is None:
            self.config_file = os.path.join(self.data_dir, "config.json")
        else:
            self.config_file = config_file
        
        # Configuration par défaut
        self.default_config = {
            "app": {
                "name": "Vynal Docs Automator",
                "version": "1.0.0",
                "theme": "dark",
                "language": "fr",
                "company_name": "Vynal Agency LTD",
                "company_logo": "",
                "auto_save": True,
                "save_interval": 5
            },
            "paths": {
                "documents": os.path.join(self.data_dir, "documents"),
                "templates": os.path.join(self.data_dir, "templates"),
                "clients": os.path.join(self.data_dir, "clients"),
                "backup": os.path.join(self.data_dir, "backup")
            },
            "security": {
                "require_password": False,
                "password_hash": "",
                "auto_lock": False,
                "lock_time": 10
            },
            "document": {
                "default_format": "pdf",
                "filename_pattern": "{document_type}_{client_name}_{date}",
                "date_format": "%Y-%m-%d"
            },
            "users": [
                {
                    "username": "admin",
                    "display_name": "Administrateur",
                    "role": "admin",
                    "password_hash": "",
                    "created_at": datetime.now().isoformat()
                }
            ],
            "ui": {
                "font_size": "medium",
                "show_tooltips": True,
                "enable_animations": True,
                "sidebar_width": 200
            },
            "logging": {
                "level": "INFO",
                "retention_days": 30,
                "max_files": 10,
                "log_user_actions": True
            }
        }
        
        # Charger la configuration
        self.config = self.load_config()
        
        logger.info("ConfigManager initialisé")
    
    def load_config(self) -> Dict[str, Any]:
        """
        Charge la configuration depuis le fichier.
        Si le fichier n'existe pas ou est invalide, utilise la configuration par défaut.
        
        Returns:
            Dict[str, Any]: Configuration chargée
        """
        if not os.path.exists(self.config_file):
            logger.info(f"Fichier de configuration {self.config_file} n'existe pas, création avec valeurs par défaut")
            self.save_config(self.default_config)
            return self.default_config.copy()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Fusionner récursivement avec les valeurs par défaut pour les clés manquantes
            merged_config = self._recursive_merge(self.default_config.copy(), config)
            
            logger.info(f"Configuration chargée depuis {self.config_file}")
            return merged_config
        
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de format JSON dans le fichier de configuration: {e}")
            # Faire une sauvegarde du fichier corrompu
            backup_file = f"{self.config_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.copyfile(self.config_file, backup_file)
            logger.info(f"Fichier de configuration corrompu sauvegardé sous {backup_file}")
            return self.default_config.copy()
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
            return self.default_config.copy()
    
    def _recursive_merge(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fusionne récursivement deux dictionnaires, en préservant les valeurs de base
        lorsqu'elles ne sont pas présentes dans la superposition.
        
        Args:
            base: Dictionnaire de base
            overlay: Dictionnaire de superposition
        
        Returns:
            Dict[str, Any]: Dictionnaire fusionné
        """
        for key, value in overlay.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._recursive_merge(base[key], value)
            else:
                base[key] = value
        return base
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """
        Sauvegarde la configuration dans le fichier.
        
        Args:
            config (Dict[str, Any], optional): Configuration à sauvegarder.
                Si None, utilise la configuration actuelle.
        
        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        if config is None:
            config = self.config
        
        try:
            # S'assurer que le répertoire existe
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Utiliser un fichier temporaire pour éviter la corruption en cas d'erreur
            temp_file = f"{self.config_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Remplacer le fichier original par le temporaire
            if os.path.exists(self.config_file):
                os.replace(temp_file, self.config_file)
            else:
                os.rename(temp_file, self.config_file)
            
            logger.info(f"Configuration sauvegardée dans {self.config_file}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration via une clé de type "section.sous_section.paramètre".
        
        Args:
            key (str): Clé de configuration au format "section.sous_section.paramètre"
            default (Any, optional): Valeur par défaut si la clé n'existe pas
        
        Returns:
            Any: Valeur de configuration ou valeur par défaut
        
        Example:
            get("app.theme") retourne la valeur de config["app"]["theme"]
        """
        parts = key.split('.')
        current = self.config
        
        try:
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            return current
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        Définit une valeur de configuration via une clé de type "section.sous_section.paramètre".
        
        Args:
            key (str): Clé de configuration au format "section.sous_section.paramètre"
            value (Any): Nouvelle valeur
        
        Returns:
            bool: True si la valeur a été définie, False sinon
        
        Example:
            set("app.theme", "dark") défini config["app"]["theme"] = "dark"
        """
        parts = key.split('.')
        current = self.config
        
        try:
            # Naviguer à travers la hiérarchie de la configuration
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                if not isinstance(current[part], dict):
                    # Si le chemin existe mais n'est pas un dictionnaire, convertir en dictionnaire
                    current[part] = {}
                current = current[part]
            
            # Définir la valeur
            current[parts[-1]] = value
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la définition de la configuration {key}: {e}")
            return False
    
    def update(self, config_dict: Dict[str, Any]) -> bool:
        """
        Met à jour plusieurs valeurs de configuration.
        
        Args:
            config_dict (Dict[str, Any]): Dictionnaire avec des clés de type "section.sous_section.paramètre"
        
        Returns:
            bool: True si toutes les valeurs ont été mises à jour, False sinon
        """
        success = True
        
        for key, value in config_dict.items():
            if not self.set(key, value):
                success = False
        
        return success
    
    def save(self) -> bool:
        """
        Sauvegarde la configuration actuelle.
        
        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        return self.save_config(self.config)
    
    def reset_to_defaults(self) -> bool:
        """
        Réinitialise la configuration aux valeurs par défaut.
        
        Returns:
            bool: True si la réinitialisation a réussi, False sinon
        """
        self.config = self.default_config.copy()
        success = self.save()
        logger.info("Configuration réinitialisée aux valeurs par défaut")
        return success
    
    def get_all(self) -> Dict[str, Any]:
        """
        Récupère toute la configuration.
        
        Returns:
            Dict[str, Any]: Configuration complète
        """
        return self.config.copy()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Récupère une section complète de la configuration.
        
        Args:
            section (str): Nom de la section (ex: "app", "paths")
        
        Returns:
            Dict[str, Any]: Section de configuration ou dictionnaire vide si non trouvée
        """
        return self.config.get(section, {}).copy()
    
    def backup_config(self) -> Optional[str]:
        """
        Crée une sauvegarde du fichier de configuration actuel.
        
        Returns:
            Optional[str]: Chemin de la sauvegarde ou None en cas d'erreur
        """
        try:
            backup_dir = os.path.join(self.data_dir, "backup")
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_file = os.path.join(
                backup_dir, 
                f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            shutil.copy2(self.config_file, backup_file)
            logger.info(f"Sauvegarde de la configuration créée: {backup_file}")
            return backup_file
        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
            return None
    
    def restore_config(self, backup_file: str) -> bool:
        """
        Restaure une configuration à partir d'une sauvegarde.
        
        Args:
            backup_file (str): Chemin vers le fichier de sauvegarde
        
        Returns:
            bool: True si la restauration a réussi, False sinon
        """
        try:
            if not os.path.exists(backup_file):
                logger.error(f"Fichier de sauvegarde non trouvé: {backup_file}")
                return False
            
            # Faire une sauvegarde du fichier actuel avant restauration
            current_backup = self.backup_config()
            
            # Restaurer la sauvegarde
            shutil.copy2(backup_file, self.config_file)
            
            # Recharger la configuration
            self.config = self.load_config()
            
            logger.info(f"Configuration restaurée depuis {backup_file}")
            logger.info(f"Ancienne configuration sauvegardée dans {current_backup}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la restauration de la configuration: {e}")
            return False
    
    def get_backup_list(self) -> List[Dict[str, str]]:
        """
        Récupère la liste des sauvegardes de configuration disponibles.
        
        Returns:
            List[Dict[str, str]]: Liste des informations sur les sauvegardes
        """
        backup_dir = os.path.join(self.data_dir, "backup")
        backups = []
        
        if os.path.exists(backup_dir):
            for file in os.listdir(backup_dir):
                if file.startswith("config_backup_") and file.endswith(".json"):
                    file_path = os.path.join(backup_dir, file)
                    
                    try:
                        # Extraire la date de la sauvegarde du nom de fichier
                        date_str = file.replace("config_backup_", "").replace(".json", "")
                        date_obj = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                        
                        backups.append({
                            "file": file,
                            "path": file_path,
                            "date": date_obj.strftime("%d/%m/%Y %H:%M:%S"),
                            "size": os.path.getsize(file_path)
                        })
                    except:
                        pass
        
        # Trier par date décroissante (plus récent en premier)
        backups.sort(key=lambda x: x["date"], reverse=True)
        return backups
    
    def import_config(self, file_path: str) -> bool:
        """
        Importe une configuration depuis un fichier JSON externe.
        
        Args:
            file_path (str): Chemin vers le fichier JSON à importer
        
        Returns:
            bool: True si l'importation a réussi, False sinon
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"Fichier de configuration à importer non trouvé: {file_path}")
                return False
            
            # Lire le fichier à importer
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Vérifier que c'est bien une configuration valide
            if not isinstance(imported_config, dict):
                logger.error(f"Le fichier importé ne contient pas une configuration valide: {file_path}")
                return False
            
            # Fusionner avec les valeurs par défaut pour éviter les valeurs manquantes
            merged_config = self._recursive_merge(self.default_config.copy(), imported_config)
            
            # Sauvegarder l'ancienne configuration
            self.backup_config()
            
            # Mettre à jour la configuration
            self.config = merged_config
            self.save()
            
            logger.info(f"Configuration importée depuis {file_path}")
            return True
            
        except json.JSONDecodeError:
            logger.error(f"Le fichier {file_path} n'est pas un JSON valide")
            return False
        
        except Exception as e:
            logger.error(f"Erreur lors de l'importation de la configuration: {e}")
            return False
    
    def export_config(self, file_path: str) -> bool:
        """
        Exporte la configuration actuelle vers un fichier JSON.
        
        Args:
            file_path (str): Chemin où exporter la configuration
        
        Returns:
            bool: True si l'exportation a réussi, False sinon
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration exportée vers {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation de la configuration: {e}")
            return False