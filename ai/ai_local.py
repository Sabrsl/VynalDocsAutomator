import requests
import logging
import json
import tkinter as tk
from tkinter import messagebox
import sys
import time

logger = logging.getLogger('AI.Local')

def demarrer_conversation():
    """
    Démarre l'interface graphique de conversation avec l'IA.
    """
    try:
        from gui import main
        main()
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'interface graphique : {e}")
        messagebox.showerror("Erreur", "Impossible de démarrer l'interface graphique. Veuillez vérifier que tous les modules sont installés.")
        sys.exit(1)

def ouvrir_formulaire_modele(contenu):
    """
    Analyse le contenu d'un document pour extraire les variables à compléter.
    """
    try:
        # Appeler l'API Ollama avec streaming
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": f"Identifie les variables à compléter dans ce texte. Pour chaque variable, écris une ligne avec le format:\nVARIABLE: nom_variable | DESCRIPTION: description de la variable\n\nTexte:\n{contenu}\n\n---FIN---",
                "stream": True,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.85,
                    "num_predict": 1024,
                    "frequency_penalty": 0.1,
                    "stop": ["\n\n\n", "###", "```"],
                    "timeout": 20
                }
            }
        )

        # Traiter la réponse ligne par ligne
        full_response = ""
        for line in response.iter_lines():
            if line:
                full_response += line.decode('utf-8').strip() + "\n"

        # Extraire les variables du texte
        variables = {}
        for line in full_response.split('\n'):
            line = line.strip()
            if not line or line == "---FIN---":
                continue
                
            if '|' not in line or 'VARIABLE:' not in line or 'DESCRIPTION:' not in line:
                continue
                
            var_part, desc_part = line.split('|', 1)
            var_name = var_part.replace('VARIABLE:', '').strip()
            description = desc_part.replace('DESCRIPTION:', '').strip()
            
            if var_name and description:
                variables[var_name] = {
                    "description": description
                }

        return variables

    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur API Ollama: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        return {}

def generer_document(prompt, callback=None):
    """
    Génère un document à partir d'un prompt avec streaming en temps réel.
    
    Args:
        prompt (str): Le prompt pour générer le document
        callback (callable, optional): Fonction de callback pour l'affichage en temps réel
        
    Returns:
        str: Le document généré
    """
    try:
        if not prompt or len(prompt.strip()) < 2:
            return "Le prompt est trop court. Veuillez fournir plus de détails."
        
        # Préparer le contexte
        context = f"""Tu es un expert en rédaction de documents professionnels. 
        Génère un document basé sur la demande suivante : {prompt}
        Le document doit être en français, professionnel et bien structuré."""
        
        # Appeler l'API Ollama avec streaming
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": context,
                "stream": True,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.85,
                    "num_predict": 1024,
                    "frequency_penalty": 0.1,
                    "stop": ["\n\n\n", "###", "```"],
                    "timeout": 20,
                    "num_ctx": 2048,
                    "num_thread": 6,
                    "num_gpu": 1,
                    "repetition_penalty": 1.1
                }
            },
            timeout=60,
            stream=True
        )
        
        if response.status_code == 200:
            full_response = ""
            buffer = ""
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            chunk_text = chunk["response"]
                            buffer += chunk_text
                            full_response += chunk_text
                            
                            # Appeler le callback pour l'affichage en temps réel
                            if callback:
                                callback(chunk_text)
                            
                            # Vérifier si on a une phrase complète
                            if any(punct in chunk_text for punct in [".", "!", "?", "\n"]):
                                buffer = ""
                                
                    except json.JSONDecodeError:
                        continue
            
            return full_response
        else:
            logger.error(f"Erreur API Ollama: {response.text}")
            return "Erreur lors de la génération du document. Veuillez réessayer."
            
    except requests.exceptions.Timeout:
        logger.error("Timeout lors de la génération du document")
        return "La génération du document a pris trop de temps. Veuillez réessayer avec une demande plus simple."
    except requests.exceptions.ConnectionError:
        logger.error("Erreur de connexion à Ollama")
        return "Impossible de se connecter au service. Vérifiez que Ollama est en cours d'exécution."
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return "Une erreur inattendue s'est produite. Veuillez réessayer."

if __name__ == "__main__":
    # Démarrer uniquement l'interface graphique
    demarrer_conversation() 