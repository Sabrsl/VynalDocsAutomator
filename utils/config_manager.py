"""
Module de gestion de configuration pour l'application Vynal Docs Automator.
Permet de charger, sauvegarder et accéder aux paramètres de configuration de l'application.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("VynalDocsAutomator.ConfigManager")

class ConfigManager:
    """
    Gestionnaire de configuration pour l'application.
    Gère le chargement, la sauvegarde et l'accès aux paramètres de configuration.
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
            "app_name": "Vynal Docs Automator",
            "version": "1.0.0",
            "theme": "system",
            "language": "fr",
            "backup_frequency": "daily",
            "max_recent_activities": 50,
            "document_output_dir": os.path.join(self.data_dir, "documents"),
            "default_format": "pdf",
            "logging": {
                "log_level": "INFO",
                "log_file": os.path.join(self.base_dir, "logs", "app.log"),
                "max_size": 5242880,  # 5 MB
                "backup_count": 3
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
            
            # Fusionner avec les valeurs par défaut pour les clés manquantes
            merged_config = self.default_config.copy()
            merged_config.update(config)
            
            logger.info(f"Configuration chargée depuis {self.config_file}")
            return merged_config
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
            return self.default_config.copy()
    
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
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration sauvegardée dans {self.config_file}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration.
        
        Args:
            key (str): Clé de configuration à récupérer
            default (Any, optional): Valeur par défaut si la clé n'existe pas
        
        Returns:
            Any: Valeur de configuration ou valeur par défaut
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Définit une valeur de configuration.
        
        Args:
            key (str): Clé de configuration à définir
            value (Any): Nouvelle valeur
        """
        self.config[key] = value
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        Met à jour plusieurs valeurs de configuration.
        
        Args:
            config_dict (Dict[str, Any]): Dictionnaire de configurations à mettre à jour
        """
        self.config.update(config_dict)
    
    def save(self) -> bool:
        """
        Sauvegarde la configuration actuelle.
        
        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        return self.save_config(self.config)
    
    def reset(self) -> None:
        """
        Réinitialise la configuration aux valeurs par défaut.
        """
        self.config = self.default_config.copy()
        self.save()
        logger.info("Configuration réinitialisée aux valeurs par défaut")
    
    def get_all(self) -> Dict[str, Any]:
        """
        Récupère toute la configuration.
        
        Returns:
            Dict[str, Any]: Configuration complète
        """
        return self.config.copy()
    
    def get_nested(self, *keys: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration imbriquée.
        
        Args:
            *keys: Séquence de clés pour accéder à la valeur imbriquée
            default: Valeur par défaut si le chemin n'existe pas
        
        Returns:
            Any: Valeur imbriquée ou valeur par défaut
        
        Example:
            get_nested('logging', 'log_level', default='INFO')
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value


# Exemple d'utilisation
if __name__ == "__main__":
    # Configurer le logging basique pour les tests
    logging.basicConfig(level=logging.INFO)
    
    # Créer un gestionnaire de configuration
    config_manager = ConfigManager()
    
    # Afficher la configuration
    print("Configuration complète:")
    print(json.dumps(config_manager.get_all(), indent=2))
    
    # Accéder à des valeurs spécifiques
    print(f"Nom de l'application: {config_manager.get('app_name')}")
    print(f"Niveau de log: {config_manager.get_nested('logging', 'log_level')}")
    
    # Modifier une valeur
    config_manager.set('theme', 'dark')
    print(f"Nouveau thème: {config_manager.get('theme')}")
    
    # Sauvegarder les modifications
    config_manager.save()