#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour la génération de documents
Pour vérifier le bon fonctionnement du système de remplacement de variables
"""

import os
import sys
import logging
from datetime import datetime

# Configurer le logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# S'assurer que le module ai est accessible
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer le processeur de documents
from ai.document_processor import AIDocumentProcessor

def test_document_generation():
    """Test complet de génération de document"""
    print("\n===== TEST DE GÉNÉRATION DE DOCUMENT =====")
    
    # Créer une instance du processeur
    processor = AIDocumentProcessor()
    
    # Chemin du template
    template_path = os.path.join("data", "templates", "test_template.txt")
    
    # Vérifier que le template existe
    if not os.path.exists(template_path):
        print(f"ERREUR: Le template {template_path} n'existe pas!")
        return
        
    print(f"Utilisation du template: {template_path}")
    
    # Variables à remplacer
    variables = {
        "date": datetime.now().strftime("%d/%m/%Y"),
        "nom": "Dupont",
        "prenom": "Jean",
        "email": "jean.dupont@example.com",
        "telephone": "01 23 45 67 89",
        "adresse": "123 rue des Exemples",
        "code_postal": "75000",
        "ville": "Paris"
    }
    
    print(f"Variables à remplacer: {variables}")
    
    # Lire le template
    content = ""
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"Template lu: {len(content)} caractères")
    except Exception as e:
        print(f"ERREUR lors de la lecture du template: {e}")
        return
    
    # Tester uniquement le replace_variables
    try:
        print("\n----- Test 1: replace_variables -----")
        result1 = processor.replace_variables(content, variables)
        
        # Afficher le résultat
        print("\nDocument généré:")
        print("-" * 40)
        print(result1)
        print("-" * 40)
        
        # Vérifier que les variables ont été remplacées
        missing_vars = []
        for var_name in variables.keys():
            if f"{{{var_name}}}" in result1:
                missing_vars.append(var_name)
                
        if missing_vars:
            print(f"AVERTISSEMENT: Certaines variables n'ont pas été remplacées: {missing_vars}")
        else:
            print("✅ Toutes les variables ont été remplacées avec succès!")
            
        # Enregistrer le résultat
        output_path = os.path.join("data", "documents", "outputs", f"test_replace_variables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result1)
        print(f"Document enregistré: {output_path}")
    except Exception as e:
        print(f"ERREUR lors du test replace_variables: {e}")
    
    # Tester generate_final_document
    try:
        print("\n----- Test 2: generate_final_document -----")
        result2 = processor.generate_final_document(template_path, variables)
        
        # Afficher le résultat
        print("\nDocument généré:")
        print("-" * 40)
        print(result2)
        print("-" * 40)
        
        # Vérifier que les variables ont été remplacées
        missing_vars = []
        for var_name in variables.keys():
            if f"{{{var_name}}}" in result2:
                missing_vars.append(var_name)
                
        if missing_vars:
            print(f"AVERTISSEMENT: Certaines variables n'ont pas été remplacées: {missing_vars}")
        else:
            print("✅ Toutes les variables ont été remplacées avec succès!")
            
        # Enregistrer le résultat
        output_path = os.path.join("data", "documents", "outputs", f"test_generate_final_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result2)
        print(f"Document enregistré: {output_path}")
    except Exception as e:
        print(f"ERREUR lors du test generate_final_document: {e}")
    
    print("\n===== TESTS TERMINÉS =====")

if __name__ == "__main__":
    test_document_generation() 