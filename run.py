#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de lancement de Vynal Docs Automator
Configure l'environnement et lance l'application
"""

import os
import sys

def main():
    # Ajouter le répertoire courant au PYTHONPATH
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Importer et lancer l'application
    from main import main
    main()

if __name__ == "__main__":
    main() 