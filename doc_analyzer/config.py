#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de configuration pour Vynal Docs Automator
Gère les paramètres de configuration du système d'analyse et traitement de documents
"""

import os
import json
import logging
import platform
from typing import Dict, Any, Optional, List, Tuple, Union

# Configuration du logger
logger = logging.getLogger("Vynal Docs Automator.doc_analyzer.config")

# Chemin vers le répertoire du module
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# Chemin par défaut du fichier de configuration
DEFAULT_CONFIG_PATH = os.path.join(MODULE_DIR, 'config', 'default_config.json')

# Chemin vers le répertoire de ressources
RESOURCES_DIR = os.path.join(MODULE_DIR, 'resources')

# Configuration par défaut des extracteurs
EXTRACTOR_CONFIG = {
    "business_docs": {
        "enabled": True,
        "keywords": ["devis", "facture", "proposition", "commercial", "offre", "contrat", 
                     "prix", "total", "montant", "client", "prestataire"],
        "extraction_depth": "full",  # Options: 'basic', 'standard', 'full'
        "confidence_threshold": 0.6,
        "extract_tables": True,
        "extract_metadata": True
    },
    "contracts": {
        "enabled": True,
        "extraction_depth": "full",
        "confidence_threshold": 0.7,
        "extract_parties": True,
        "extract_clauses": True,
        "extract_signatures": True
    },
    "identity_docs": {
        "enabled": True,
        "ocr_enabled": True,
        "extraction_depth": "full",
        "confidence_threshold": 0.8,
        "supported_countries": ["fr", "ma", "sn", "ci", "cm", "dz", "tn"]
    },
    "legal_docs": {
        "enabled": True,
        "extraction_depth": "standard",
        "confidence_threshold": 0.7,
        "extract_parties": True,
        "extract_dates": True
    }
}

# Configuration de l'OCR
OCR_CONFIG = {
    "engine": "tesseract",  # Options: 'tesseract', 'azure', 'google'
    "tesseract_path": None,  # Chemin vers l'exécutable Tesseract (détecté automatiquement si None)
    "language": "fra+eng",  # Langues pour Tesseract
    "preprocess_images": True,
    "dpi": 300,
    "output_type": "text",  # Options: 'text', 'hocr', 'pdf'
    "timeout": 30,  # Timeout en secondes
    "api_keys": {
        "azure": None,
        "google": None
    }
}

# Configuration de l'interface utilisateur
UI_CONFIG = {
    "auto_fill_dialog": {
        "window_title": "Remplissage Automatique",
        "window_width": 800,
        "window_height": 600,
        "min_width": 640,
        "min_height": 480,
        "animation_enabled": True,
        "theme": "system",  # Options: 'system', 'light', 'dark'
        "font_size": 11,
        "max_suggestions": 5,
        "show_confidence": True,
        "confirmation_required": True
    },
    "client_matcher": {
        "match_threshold": 0.7,  # Seuil de correspondance minimum
        "max_results": 5,  # Nombre maximum de résultats
        "search_fields": ["name", "email", "phone", "company"],
        "quick_add_enabled": True
    }
}

# Configuration générale
GENERAL_CONFIG = {
    "language": "fr",  # Langue par défaut
    "log_level": "INFO",  # Niveau de log
    "temp_dir": None,  # Répertoire temporaire (par défaut: system temp)
    "backup_enabled": True,  # Activer les sauvegardes
    "backup_interval": 60,  # Intervalle de sauvegarde en minutes
    "max_file_size": 20,  # Taille maximum des fichiers en Mo
    "supported_formats": [".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".doc", ".docx", ".txt"],
    "preferred_extractors": {},  # Extracteurs préférés par type de document
    "performance_mode": "balanced"  # Options: 'speed', 'balanced', 'accuracy'
}

# Configuration de l'analyse
ANALYZER_CONFIG = {
    "document_types": {
        "business": ["devis", "facture", "proposition_commerciale", "bon_commande"],
        "contract": ["contrat_prestation", "contrat_vente", "contrat_distribution", "contrat_licence", "contrat_travail"],
        "legal": ["procuration", "pouvoir", "attestation", "declaration", "pv_assemblee"],
        "id": ["cni", "passeport", "titre_sejour", "visa"]
    },
    "extraction_timeout": 60,  # Timeout pour l'extraction en secondes
    "max_document_size": 20 * 1024 * 1024,  # 20 Mo
    "min_text_length": 50,  # Longueur minimale de texte pour tenter l'analyse
    "parallel_processing": True,  # Traitement parallèle
    "max_workers": 4,  # Nombre maximum de workers pour le traitement parallèle
    "save_temp_files": False,  # Sauvegarder les fichiers temporaires
    "confidence_levels": {
        "high": 0.8,
        "medium": 0.6,
        "low": 0.4
    }
}

# Supprimer la configuration OCR
DEFAULT_CONFIG = {
    "version": "1.0.0",
    "language": "fr",
    "output_dir": "output",
    "temp_dir": "temp",
    "log_level": "INFO",
    "max_workers": 4,
    "timeout": 300,
    "retry_attempts": 3,
    "retry_delay": 5,
    "cleanup_temp": True,
    "save_intermediate": False,
    "validation": {
        "strict_mode": True,
        "auto_correct": False,
        "confidence_threshold": 0.8
    },
    "extraction": {
        "parallel": True,
        "batch_size": 10,
        "timeout": 60
    }
}

class Config:
    """
    Classe de gestion de la configuration du système
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialise la configuration
        
        Args:
            config_path (str, optional): Chemin vers le fichier de configuration personnalisé
        """
        self.logger = logger
        
        # Configuration par défaut
        self.config = {
            "extractor": EXTRACTOR_CONFIG,
            "ocr": OCR_CONFIG,
            "ui": UI_CONFIG,
            "general": GENERAL_CONFIG,
            "analyzer": ANALYZER_CONFIG
        }
        
        # Charger la configuration par défaut depuis le fichier JSON
        if os.path.exists(DEFAULT_CONFIG_PATH):
            self._load_config(DEFAULT_CONFIG_PATH)
        
        # Charger la configuration personnalisée si spécifiée
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
        
        # Détecter les chemins et paramètres système
        self._detect_system_params()
        
        self.logger.info("Configuration initialisée")
    
    def _load_config(self, config_path: str):
        """
        Charge la configuration depuis un fichier JSON
        
        Args:
            config_path (str): Chemin vers le fichier de configuration
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                custom_config = json.load(f)
            
            # Fusionner la configuration chargée avec la configuration actuelle
            self._merge_config(custom_config)
            
            self.logger.info(f"Configuration chargée depuis {config_path}")
        
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration depuis {config_path}: {e}")
    
    def _merge_config(self, custom_config: Dict[str, Any]):
        """
        Fusionne une configuration personnalisée avec la configuration actuelle
        
        Args:
            custom_config (dict): Configuration personnalisée à fusionner
        """
        # Fonction récursive pour fusionner les dictionnaires
        def merge_dicts(source, override):
            for key, value in override.items():
                if key in source and isinstance(source[key], dict) and isinstance(value, dict):
                    merge_dicts(source[key], value)
                else:
                    source[key] = value
        
        # Fusionner chaque section de la configuration
        for section, values in custom_config.items():
            if section in self.config:
                if isinstance(self.config[section], dict) and isinstance(values, dict):
                    merge_dicts(self.config[section], values)
                else:
                    self.config[section] = values
            else:
                self.config[section] = values
    
    def _detect_system_params(self):
        """
        Détecte et configure les paramètres spécifiques au système
        """
        # Détecter le système d'exploitation
        system = platform.system().lower()
        
        # Détecter le chemin de Tesseract selon le système d'exploitation
        if self.config["ocr"]["tesseract_path"] is None:
            if system == "windows":
                # Chemins courants sur Windows
                potential_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
                ]
                for path in potential_paths:
                    if os.path.exists(path):
                        self.config["ocr"]["tesseract_path"] = path
                        break
            elif system in ["linux", "darwin"]:  # Linux ou macOS
                # Sur Linux/macOS, Tesseract est généralement dans le PATH
                self.config["ocr"]["tesseract_path"] = "tesseract"
        
        # Configurer le répertoire temporaire
        if self.config["general"]["temp_dir"] is None:
            import tempfile
            self.config["general"]["temp_dir"] = tempfile.gettempdir()
        
        # Ajuster les paramètres selon les ressources système
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        
        # Ajuster le nombre de workers
        if self.config["analyzer"]["parallel_processing"]:
            self.config["analyzer"]["max_workers"] = min(cpu_count, self.config["analyzer"]["max_workers"])
        
        # Adapter les paramètres de performance
        performance_mode = self.config["general"]["performance_mode"]
        if performance_mode == "speed":
            self.config["extractor"]["business_docs"]["extraction_depth"] = "basic"
            self.config["extractor"]["contracts"]["extraction_depth"] = "standard"
            self.config["ocr"]["preprocess_images"] = False
        elif performance_mode == "accuracy":
            self.config["extractor"]["business_docs"]["extraction_depth"] = "full"
            self.config["extractor"]["contracts"]["extraction_depth"] = "full"
            self.config["ocr"]["preprocess_images"] = True
            self.config["ocr"]["dpi"] = 450
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Récupère une valeur de configuration à partir de son chemin d'accès
        
        Args:
            key_path (str): Chemin d'accès à la valeur (format: "section.key.subkey")
            default (any, optional): Valeur par défaut si le chemin n'existe pas
            
        Returns:
            any: Valeur de configuration ou valeur par défaut
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Définit une valeur de configuration
        
        Args:
            key_path (str): Chemin d'accès à la valeur (format: "section.key.subkey")
            value (any): Nouvelle valeur
            
        Returns:
            bool: True si la valeur a été définie, False sinon
        """
        keys = key_path.split('.')
        config = self.config
        
        # Naviguer jusqu'au parent de la valeur à définir
        for key in keys[:-1]:
            if key not in config or not isinstance(config[key], dict):
                config[key] = {}
            config = config[key]
        
        # Définir la valeur
        config[keys[-1]] = value
        return True
    
    def save(self, config_path: str) -> bool:
        """
        Sauvegarde la configuration actuelle dans un fichier JSON
        
        Args:
            config_path (str): Chemin vers le fichier de configuration
            
        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        try:
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Configuration sauvegardée dans {config_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
            return False
    
    def reset_to_defaults(self):
        """
        Réinitialise la configuration aux valeurs par défaut
        """
        self.config = {
            "extractor": EXTRACTOR_CONFIG,
            "ocr": OCR_CONFIG,
            "ui": UI_CONFIG,
            "general": GENERAL_CONFIG,
            "analyzer": ANALYZER_CONFIG
        }
        
        # Détecter à nouveau les paramètres système
        self._detect_system_params()
        
        self.logger.info("Configuration réinitialisée aux valeurs par défaut")
    
    def get_all(self) -> Dict[str, Any]:
        """
        Récupère l'ensemble de la configuration
        
        Returns:
            dict: Configuration complète
        """
        return self.config
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Récupère une section complète de la configuration
        
        Args:
            section (str): Nom de la section
            
        Returns:
            dict: Section de configuration ou dictionnaire vide si la section n'existe pas
        """
        return self.config.get(section, {})
    
    def update_section(self, section: str, values: Dict[str, Any]) -> bool:
        """
        Met à jour une section complète de la configuration
        
        Args:
            section (str): Nom de la section
            values (dict): Nouvelles valeurs
            
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        if section not in self.config:
            self.config[section] = {}
        
        # Fonction récursive pour fusionner les dictionnaires
        def merge_dicts(source, override):
            for key, value in override.items():
                if key in source and isinstance(source[key], dict) and isinstance(value, dict):
                    merge_dicts(source[key], value)
                else:
                    source[key] = value
        
        # Fusionner les valeurs
        merge_dicts(self.config[section], values)
        
        return True
    
    def get_resources_path(self, resource_type: str = None) -> str:
        """
        Récupère le chemin vers un type de ressource
        
        Args:
            resource_type (str, optional): Type de ressource (patterns, models, dictionaries, etc.)
            
        Returns:
            str: Chemin vers le répertoire de ressources
        """
        if resource_type:
            path = os.path.join(RESOURCES_DIR, resource_type)
            os.makedirs(path, exist_ok=True)
            return path
        else:
            return RESOURCES_DIR
    
    def get_temp_dir(self) -> str:
        """
        Récupère le répertoire temporaire
        
        Returns:
            str: Chemin vers le répertoire temporaire
        """
        temp_dir = self.get("general.temp_dir")
        if not temp_dir:
            import tempfile
            temp_dir = tempfile.gettempdir()
        
        # Créer un sous-répertoire spécifique à l'application
        app_temp_dir = os.path.join(temp_dir, "vynal_docs_automator")
        os.makedirs(app_temp_dir, exist_ok=True)
        
        return app_temp_dir
    
    def is_extraction_enabled(self, extractor_type: str) -> bool:
        """
        Vérifie si un type d'extracteur est activé
        
        Args:
            extractor_type (str): Type d'extracteur (business_docs, contracts, identity_docs, legal_docs)
            
        Returns:
            bool: True si l'extracteur est activé, False sinon
        """
        return self.get(f"extractor.{extractor_type}.enabled", True)
    
    def is_format_supported(self, file_extension: str) -> bool:
        """
        Vérifie si un format de fichier est pris en charge
        
        Args:
            file_extension (str): Extension de fichier (avec ou sans point)
            
        Returns:
            bool: True si le format est pris en charge, False sinon
        """
        # Normaliser l'extension (ajouter un point si nécessaire)
        if not file_extension.startswith('.'):
            file_extension = '.' + file_extension
        
        supported_formats = self.get("general.supported_formats", [])
        return file_extension.lower() in (fmt.lower() for fmt in supported_formats)
    
    def get_preferred_extractor(self, document_type: str) -> str:
        """
        Récupère l'extracteur préféré pour un type de document
        
        Args:
            document_type (str): Type de document
            
        Returns:
            str: Nom de l'extracteur préféré ou None si aucun n'est spécifié
        """
        preferred_extractors = self.get("general.preferred_extractors", {})
        return preferred_extractors.get(document_type)
    
    def get_confidence_threshold(self, extractor_type: str) -> float:
        """
        Récupère le seuil de confiance pour un type d'extracteur
        
        Args:
            extractor_type (str): Type d'extracteur
            
        Returns:
            float: Seuil de confiance (entre 0 et 1)
        """
        return self.get(f"extractor.{extractor_type}.confidence_threshold", 0.6)
    
    def get_supported_countries(self) -> List[str]:
        """
        Récupère la liste des pays pris en charge pour les documents d'identité
        
        Returns:
            list: Liste des codes pays pris en charge
        """
        return self.get("extractor.identity_docs.supported_countries", ["fr"])
    
    def is_ocr_enabled(self) -> bool:
        """
        Vérifie si l'OCR est activé
        
        Returns:
            bool: True si l'OCR est activé, False sinon
        """
        return self.get("ocr.engine") is not None


# Créer une instance de configuration par défaut
config = Config()

# Exporter la configuration globale
def get_config() -> Config:
    """
    Récupère l'instance de configuration globale
    
    Returns:
        Config: Instance de configuration
    """
    return config

def load_config(config_path: str) -> Config:
    """
    Charge une configuration depuis un fichier et retourne une nouvelle instance
    
    Args:
        config_path (str): Chemin vers le fichier de configuration
        
    Returns:
        Config: Nouvelle instance de configuration
    """
    return Config(config_path)