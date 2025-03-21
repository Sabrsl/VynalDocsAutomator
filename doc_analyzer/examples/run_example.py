"""
Script d'exécution de l'exemple d'analyse de document
"""

import os
import sys
import logging
from pathlib import Path
from pprint import pprint

# Ajouter le répertoire parent au path pour l'import
sys.path.append(str(Path(__file__).parent.parent.parent))

from doc_analyzer.examples.enhanced_analysis_example import main

def setup_logging():
    """Configure le logging pour l'exemple"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('example_analysis.log')
        ]
    )

def ensure_directories():
    """Crée les répertoires nécessaires"""
    directories = ['exports', 'plugins', 'error_logs']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def print_separator(message=""):
    """Affiche un séparateur avec un message optionnel"""
    print("\n" + "="*80)
    if message:
        print(message.center(80))
        print("="*80)

if __name__ == "__main__":
    print_separator("EXEMPLE D'ANALYSE DE DOCUMENT")
    
    # Configuration
    setup_logging()
    ensure_directories()
    
    try:
        # Exécuter l'exemple
        main()
        
        # Afficher les résultats exportés
        print_separator("FICHIERS GÉNÉRÉS")
        
        for directory in ['exports', 'plugins', 'error_logs']:
            print(f"\n{directory.upper()}:")
            path = Path(directory)
            if path.exists():
                for file in path.glob('*'):
                    print(f"- {file.name}")
        
        print_separator("EXEMPLE TERMINÉ AVEC SUCCÈS")
        
    except Exception as e:
        print_separator("ERREUR")
        print(f"Une erreur est survenue: {e}")
        sys.exit(1) 