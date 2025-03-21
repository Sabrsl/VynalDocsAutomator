import json
import os
import requests
from typing import Dict, Optional, Any
from datetime import datetime

class DocumentProcessor:
    def __init__(self, database_path: str = "data/clients.json"):
        self.database_path = database_path
        self.cache = {}
        self.stats = {
            'processed_docs': 0,
            'successful_processes': 0,
            'failed_processes': 0,
            'avg_processing_time': 0,
            'last_process_time': None,
            'cache_hits': 0,
            'cache_misses': 0
        }
        self._initialize_stats()

    def _initialize_stats(self):
        """Initialise ou charge les statistiques depuis un fichier"""
        stats_file = "data/processor_stats.json"
        try:
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    saved_stats = json.load(f)
                    self.stats.update(saved_stats)
        except Exception:
            # En cas d'erreur, on garde les stats par défaut
            pass

    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du processeur
        
        Returns:
            Dict[str, Any]: Statistiques d'utilisation
        """
        return self.stats

    def clear_cache(self) -> None:
        """Vide le cache du processeur"""
        self.cache.clear()

    def _update_stats(self, success: bool, processing_time: float):
        """
        Met à jour les statistiques après un traitement
        
        Args:
            success (bool): Si le traitement a réussi
            processing_time (float): Temps de traitement en secondes
        """
        self.stats['processed_docs'] += 1
        if success:
            self.stats['successful_processes'] += 1
        else:
            self.stats['failed_processes'] += 1

        # Mise à jour du temps moyen (moyenne mobile)
        if self.stats['avg_processing_time'] == 0:
            self.stats['avg_processing_time'] = processing_time
        else:
            self.stats['avg_processing_time'] = (
                0.7 * self.stats['avg_processing_time'] + 
                0.3 * processing_time
            )
        
        self.stats['last_process_time'] = datetime.now().isoformat()

        # Sauvegarder les stats périodiquement
        if self.stats['processed_docs'] % 10 == 0:  # Tous les 10 documents
            self._save_stats()

    def _save_stats(self):
        """Sauvegarde les statistiques dans un fichier"""
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/processor_stats.json", 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception:
            # Échec silencieux - la sauvegarde n'est pas critique
            pass

    def search_client(self, client_name: str) -> Optional[Dict[str, Any]]:
        """
        Recherche un client dans la base de données clients.

        Args:
            client_name (str): Nom du client à rechercher.

        Returns:
            dict or None: Informations du client trouvé, sinon None.
        """
        try:
            with open(self.database_path, "r", encoding="utf-8") as f:
                clients = json.load(f)
            
            # Recherche approximative (tolérance aux fautes)
            for client in clients:
                if client_name.lower() in client["nom"].lower():
                    return client
            
            return None
        except Exception as e:
            print(f"Erreur lors de la recherche du client: {e}")
            return None

    def extract_variables_from_document(self, document_text: str) -> Dict[str, str]:
        """
        Analyse un document brut et extrait les informations personnalisables.

        Args:
            document_text (str): Texte du document à analyser.

        Returns:
            dict: Variables détectées dans le document.
        """
        # Recherche basique des variables entre << >>
        import re
        variables = {}
        pattern = r"<<([^>]+)>>"
        matches = re.findall(pattern, document_text)
        
        for match in matches:
            variables[match] = "??"
            
        return variables

    def complete_variables(self, variables: Dict[str, str], client_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Remplit les variables détectées avec les données du client.

        Args:
            variables (dict): Variables détectées dans le document.
            client_data (dict): Données du client.

        Returns:
            dict: Variables complétées.
        """
        completed_variables = {}
        
        # Mapping des clés du document vers les clés client
        key_mapping = {
            "nom": "nom",
            "adresse": "adresse",
            "telephone": "téléphone",
            "email": "email",
            "entreprise": "entreprise"
        }

        for key, value in variables.items():
            if value == "??":
                mapped_key = key_mapping.get(key.lower(), key)
                if mapped_key in client_data:
                    completed_variables[key] = client_data[mapped_key]
                else:
                    completed_variables[key] = f"<<{key}>>"  # Garde la variable pour demande ultérieure
            else:
                completed_variables[key] = value

        return completed_variables

    def replace_variables_in_document(self, document_text: str, variables: Dict[str, str]) -> str:
        """
        Remplace les variables dans le document par leurs valeurs.

        Args:
            document_text (str): Texte du document original.
            variables (dict): Variables avec leurs valeurs.

        Returns:
            str: Document personnalisé.
        """
        result = document_text
        for key, value in variables.items():
            result = result.replace(f"<<{key}>>", value)
        return result

    def process_document(self, document_text: str, client_name: str) -> tuple[str, Dict[str, str]]:
        """
        Traite un document complet avec toutes les étapes.

        Args:
            document_text (str): Texte du document à traiter.
            client_name (str): Nom du client.

        Returns:
            tuple: (document_final, variables_manquantes)
        """
        start_time = datetime.now()
        success = False
        
        try:
            # Vérifier le cache
            cache_key = f"{document_text[:100]}_{client_name}"
            if cache_key in self.cache:
                self.stats['cache_hits'] += 1
                return self.cache[cache_key]

            self.stats['cache_misses'] += 1

            # 1. Recherche du client
            client_data = self.search_client(client_name)
            if not client_data:
                processing_time = (datetime.now() - start_time).total_seconds()
                self._update_stats(False, processing_time)
                return document_text, {}

            # 2. Extraction des variables
            variables = self.extract_variables_from_document(document_text)

            # 3. Complétion avec les données client
            completed_variables = self.complete_variables(variables, client_data)

            # 4. Identification des variables manquantes
            missing_variables = {
                k: v for k, v in completed_variables.items() 
                if v.startswith("<<") and v.endswith(">>")
            }

            # 5. Génération du document avec les variables disponibles
            processed_document = self.replace_variables_in_document(document_text, completed_variables)

            # Mettre en cache le résultat
            result = (processed_document, missing_variables)
            self.cache[cache_key] = result

            success = True
            return result

        finally:
            # Mettre à jour les statistiques
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_stats(success, processing_time) 