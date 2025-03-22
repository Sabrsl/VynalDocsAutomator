#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test direct pour la génération de documents
"""

import os
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Fonction de remplacement de variables simplifiée
def replace_variables(template, values):
    """Remplace les variables dans un template"""
    result = template
    
    # Pour chaque variable, faire un remplacement direct
    for var_name, value in values.items():
        # S'assurer que la valeur est une chaîne
        value_str = str(value) if value is not None else ""
        
        # Format 1: {variable}
        result = result.replace(f"{{{var_name}}}", value_str)
        
        # Format 2: {{variable}}
        result = result.replace(f"{{{{{var_name}}}}}", value_str)
    
    return result

def test_document_generation():
    """Test de génération de document"""
    print("\n===== TEST DE GÉNÉRATION DE DOCUMENT =====")
    
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
        print("\nContenu du template:")
        print("-" * 40)
        print(content)
        print("-" * 40)
    except Exception as e:
        print(f"ERREUR lors de la lecture du template: {e}")
        return
    
    # Tester la fonction de remplacement de variables simplifiée
    try:
        print("\n----- Test: replace_variables simplifié -----")
        result = replace_variables(content, variables)
        
        # Afficher le résultat
        print("\nDocument généré:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        
        # Vérifier que les variables ont été remplacées
        missing_vars = []
        for var_name in variables.keys():
            if f"{{{var_name}}}" in result:
                missing_vars.append(var_name)
                
        if missing_vars:
            print(f"AVERTISSEMENT: Certaines variables n'ont pas été remplacées: {missing_vars}")
        else:
            print("✅ Toutes les variables ont été remplacées avec succès!")
            
        # Enregistrer le résultat
        output_path = os.path.join("data", "documents", "outputs", f"test_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Document enregistré: {output_path}")
    except Exception as e:
        print(f"ERREUR lors du test: {e}")
    
    print("\n===== TEST TERMINÉ =====")

if __name__ == "__main__":
    test_document_generation() 