"""
Script pour corriger le problème avec _show_available_categories dans ai/model_patch.py
"""

import re
import os

# Fonction _show_available_categories à insérer dans la fonction patch_ai_model
show_available_categories_func = """
    def _show_available_categories(self):
        \"\"\"
        Affiche les catégories disponibles en utilisant _get_available_categories.
        \"\"\"
        try:
            # Obtenir les catégories disponibles
            categories = self._get_available_categories()
            
            if not categories:
                return \"\"\"❌ Je n'ai trouvé aucune catégorie de documents.
                
Veuillez contacter l'administrateur système.\"\"\"
            
            # Construire le message de réponse
            response = "📂 Voici les catégories de documents disponibles :\\n\\n"
            for i, category in enumerate(categories, 1):
                response += f"{i}️⃣ {category}\\n"
            
            response += "\\nVeuillez choisir une catégorie en tapant son numéro ou son nom."
            
            # Mettre à jour le contexte
            self.current_context["state"] = "choosing_category"
            self.current_context["last_action"] = "afficher_categories"
            self.current_context["available_categories"] = categories
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des catégories: {e}")
            logger.error(traceback.format_exc())
            return \"\"\"❌ Une erreur s'est produite lors de la récupération des catégories.
            
Veuillez réessayer ou contacter l'administrateur système.\"\"\"
"""

file_path = "ai/model_patch.py"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Rechercher la section où les fonctions sont définies dans patch_ai_model, juste après la définition de enhanced_normalize_input
pattern = r'def enhanced_normalize_input\(self, text\):.*?return result\.strip\(\)'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Insertion point juste après la fonction enhanced_normalize_input
    insertion_point = match.end()
    # Insérer la fonction _show_available_categories
    updated_content = content[:insertion_point] + "\n" + show_available_categories_func + content[insertion_point:]
    
    # Écrire le contenu mis à jour
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("_show_available_categories ajouté avec succès à", file_path)
else:
    print("Impossible de trouver le point d'insertion pour _show_available_categories") 