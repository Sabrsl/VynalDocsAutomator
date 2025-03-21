"""
Script pour corriger les problèmes dans ai/model_patch.py
"""

import re
import os

# Charger le contenu du fichier
file_path = "ai/model_patch.py"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Corriger la signature de _get_llama_response
content = re.sub(
    r'def _get_llama_response\(self, message: str\) -> Dict\[str, Any\]:',
    'def _get_llama_response(self, message: str) -> str:',
    content
)

# 2. Corriger la documentation de retour
content = re.sub(
    r'str: La réponse avec les métadonnées',
    'str: La réponse générée',
    content
)

# 3. Corriger le corps de la méthode _get_llama_response
body_replacement = """
        try:
            # Vérifier si Ollama est disponible
            if not should_use_ollama():
                logger.warning("Ollama n'est pas disponible. Utilisation d'une réponse par défaut.")
                return "Je suis désolé, je ne peux pas répondre à cette question pour le moment."
                
            # Créer un prompt adapté
            prompt = f"L'utilisateur me dit: {message}. Je suis un assistant spécialisé dans la gestion de documents. Je dois répondre de façon concise et précise."
            
            # Appeler l'API Ollama
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model if hasattr(self, 'model') else "llama3",
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                    "max_tokens": 300
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "Je ne comprends pas votre question.")
            else:
                return "Je suis désolé, je rencontre des difficultés techniques."
                
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à Llama dans _get_llama_response: {e}")
            return "Je suis désolé, une erreur technique m'empêche de répondre correctement."
"""

pattern = r'def _get_llama_response\(self, message: str\).*?try:.*?normalized_input.*?current_state.*?if normalized_input.*?return \{.*?}'
content = re.sub(pattern, f'def _get_llama_response(self, message: str) -> str:\n        """\n        Obtient une réponse pour les interactions de base avec l\'utilisateur.\n        \n        Args:\n            message (str): Le message de l\'utilisateur\n            \n        Returns:\n            str: La réponse générée\n        """{body_replacement}', content, flags=re.DOTALL)

# 4. Supprimer les définitions de fonctions en double après le return AIModel
content = re.sub(
    r'return AIModel\s*\n\s*def _convert_form_info_to_variables.*?def get_model_path.*?return None',
    'return AIModel',
    content,
    flags=re.DOTALL
)

# Écrire le contenu corrigé
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Corrections appliquées avec succès à", file_path) 