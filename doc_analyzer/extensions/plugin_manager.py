"""
Gestionnaire de plugins pour l'analyseur de documents
"""

import os
import sys
import logging
import importlib
import inspect
from typing import Dict, Any, List, Optional, Type, Callable
import json
import yaml
from pathlib import Path

logger = logging.getLogger("VynalDocsAutomator.Extensions.PluginManager")

class PluginInterface:
    """Interface de base pour les plugins"""
    
    VERSION = "1.0.0"
    AUTHOR = "Unknown"
    DEPENDENCIES = []
    
    @classmethod
    def get_plugin_info(cls) -> Dict[str, Any]:
        """
        Retourne les informations du plugin
        
        Returns:
            Dict[str, Any]: Informations du plugin
        """
        return {
            "name": cls.__name__,
            "version": getattr(cls, "VERSION", "1.0.0"),
            "description": cls.__doc__ or "Pas de description",
            "author": getattr(cls, "AUTHOR", "Anonyme"),
            "dependencies": getattr(cls, "DEPENDENCIES", [])
        }
    
    def initialize(self, config: dict = None) -> bool:
        """Initialise le plugin"""
        raise NotImplementedError
    
    def cleanup(self) -> bool:
        """Nettoie les ressources du plugin"""
        raise NotImplementedError

class PluginManager:
    """Gère les plugins de l'analyseur"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self.plugins = {}
        Path(plugins_dir).mkdir(parents=True, exist_ok=True)
        
        # Configuration des plugins
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}
        
        # Hooks enregistrés par les plugins
        self._hooks: Dict[str, List[Callable]] = {}
        
        logger.info("Gestionnaire de plugins initialisé")
    
    def _load_plugin_configs(self):
        """Charge la configuration des plugins"""
        config_path = os.path.join(self.plugins_dir, "plugin_config.yaml")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._plugin_configs = yaml.safe_load(f) or {}
                logger.info("Configuration des plugins chargée")
            except Exception as e:
                logger.error(f"Erreur lors du chargement de la configuration: {e}")
                self._plugin_configs = {}
    
    def _save_plugin_configs(self):
        """Sauvegarde la configuration des plugins"""
        config_path = os.path.join(self.plugins_dir, "plugin_config.yaml")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._plugin_configs, f, default_flow_style=False)
            logger.info("Configuration des plugins sauvegardée")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
    
    def discover_plugins(self) -> List[Dict[str, Any]]:
        """
        Découvre les plugins disponibles
        
        Returns:
            List[Dict[str, Any]]: Liste des informations des plugins
        """
        discovered_plugins = []
        
        # Ajouter le répertoire des plugins au path
        if self.plugins_dir not in sys.path:
            sys.path.append(os.path.abspath(self.plugins_dir))
        
        # Parcourir les fichiers Python dans le répertoire
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                try:
                    # Importer le module
                    module = importlib.import_module(module_name)
                    
                    # Chercher les classes de plugin
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and
                            issubclass(obj, PluginInterface) and
                            obj != PluginInterface):
                            plugin_info = obj.get_plugin_info()
                            plugin_info["module"] = module_name
                            discovered_plugins.append(plugin_info)
                
                except Exception as e:
                    logger.error(f"Erreur lors de la découverte du plugin {module_name}: {e}")
        
        return discovered_plugins
    
    def create_plugin_template(self, name: str, author: str = None, description: str = None):
        """
        Crée un template de plugin
        
        Args:
            name: Nom du plugin
            author: Auteur du plugin
            description: Description du plugin
        """
        template = f'''"""
{description or f"Plugin {name} pour l'analyseur de documents"}
"""

from doc_analyzer.extensions.plugin_manager import PluginInterface

class {name.title()}Plugin(PluginInterface):
    """Plugin {name}"""
    
    VERSION = "1.0.0"
    AUTHOR = "{author or 'Unknown'}"
    DEPENDENCIES = []
    
    def __init__(self):
        self._config = None
    
    def initialize(self, config: dict = None) -> bool:
        """Initialise le plugin"""
        self._config = config or {{}}
        return True
    
    def process_document(self, document: dict) -> dict:
        """Traite un document"""
        # TODO: Implémenter le traitement
        return document
    
    def cleanup(self) -> bool:
        """Nettoie les ressources"""
        return True
'''
        
        plugin_path = os.path.join(self.plugins_dir, f"{name.lower()}_plugin.py")
        with open(plugin_path, 'w', encoding='utf-8') as f:
            f.write(template)
    
    def load_plugin(self, plugin_name: str, plugin_class: str, config: Dict = None) -> bool:
        """
        Charge un plugin
        
        Args:
            plugin_name: Nom du plugin
            plugin_class: Nom de la classe du plugin
            config: Configuration du plugin
            
        Returns:
            bool: True si le plugin a été chargé
        """
        try:
            # Pour cet exemple, on simule le chargement
            # Dans une vraie implémentation, on chargerait dynamiquement le module
            plugin = self.plugins.get(plugin_name)
            if plugin:
                plugin.initialize(config)
            return True
        except Exception as e:
            print(f"Erreur lors du chargement du plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Décharge un plugin
        
        Args:
            plugin_name: Nom du plugin
            
        Returns:
            bool: True si le plugin a été déchargé
        """
        try:
            plugin = self.plugins.get(plugin_name)
            if plugin:
                plugin.cleanup()
                del self.plugins[plugin_name]
            return True
        except Exception as e:
            print(f"Erreur lors du déchargement du plugin {plugin_name}: {e}")
            return False
    
    def call_hook(self, hook_name: str, **kwargs) -> Dict[str, Any]:
        """
        Appelle un hook sur tous les plugins actifs
        
        Args:
            hook_name: Nom du hook à appeler
            **kwargs: Arguments à passer au hook
            
        Returns:
            Dict[str, Any]: Résultats des plugins
        """
        results = {}
        for name, plugin in self.plugins.items():
            if hasattr(plugin, hook_name):
                try:
                    hook = getattr(plugin, hook_name)
                    results[name] = hook(**kwargs)
                except Exception as e:
                    print(f"Erreur lors de l'appel du hook {hook_name} sur {name}: {e}")
        return results
    
    def get_active_plugins(self) -> List[str]:
        """
        Retourne la liste des plugins actifs
        
        Returns:
            List[str]: Noms des plugins actifs
        """
        return list(self.plugins.keys())
    
    def register_hook(self, hook_name: str, callback: Callable):
        """
        Enregistre un hook pour un plugin
        
        Args:
            hook_name: Nom du hook
            callback: Fonction de callback
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)
        logger.debug(f"Hook enregistré: {hook_name} -> {callback.__module__}")
    
    def unregister_hook(self, hook_name: str, callback: Callable):
        """
        Supprime un hook
        
        Args:
            hook_name: Nom du hook
            callback: Fonction de callback
        """
        if hook_name in self._hooks:
            self._hooks[hook_name] = [
                h for h in self._hooks[hook_name] if h != callback
            ]
            logger.debug(f"Hook supprimé: {hook_name} -> {callback.__module__}")
    
    def get_loaded_plugins(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des plugins chargés
        
        Returns:
            List[Dict[str, Any]]: Liste des informations des plugins
        """
        return [
            {**plugin.get_plugin_info(), "id": plugin_name}
            for plugin_name, plugin in self.plugins.items()
        ]
    
    def update_plugin_config(self, plugin_name: str,
                           config: Dict[str, Any]) -> bool:
        """
        Met à jour la configuration d'un plugin
        
        Args:
            plugin_name: Nom du plugin
            config: Nouvelle configuration
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        if plugin_name not in self.plugins:
            logger.error(f"Plugin non trouvé: {plugin_name}")
            return False
        
        try:
            # Mettre à jour la config
            self._plugin_configs[plugin_name].update(config)
            self._save_plugin_configs()
            
            # Réinitialiser le plugin avec la nouvelle config
            plugin = self.plugins[plugin_name]
            if not plugin.initialize(self._plugin_configs[plugin_name]):
                logger.error(f"Échec de la réinitialisation du plugin: {plugin_name}")
                return False
            
            logger.info(f"Configuration mise à jour pour {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la configuration: {e}")
            return False 