import os
import sys
from pathlib import Path

def detect_encoding(file_path):
    try:
        print(f"\n{'='*50}")
        print(f"Analyse de {file_path}")
        print(f"{'='*50}")
        
        # Vérifier si le fichier existe
        if not os.path.exists(file_path):
            print(f"❌ Le fichier n'existe pas")
            return None
            
        # Lire les premiers octets
        with open(file_path, "rb") as f:
            raw = f.read()
            print(f"Taille du fichier: {len(raw)} octets")
            print(f"Premiers 20 octets: {raw[:20]}")
            
            # Vérifier si c'est un fichier binaire
            if raw.startswith(b'\xff\xd8\xff') or raw.startswith(b'\x89PNG') or raw.startswith(b'PK\x03\x04'):
                print("⚠️ Ce fichier semble être un fichier binaire (image, zip, etc.)")
                return None
            
            # Essayer différents encodages
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    print(f"✅ Le fichier est valide en {encoding}")
                    print(f"Premiers 100 caractères: {content[:100]}")
                    return encoding
                except UnicodeDecodeError as e:
                    print(f"❌ Échec avec {encoding}: {str(e)}")
                    continue
            print("❌ Le fichier n'est pas un fichier texte valide")
            return None
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        return None

def check_critical_files():
    """Vérifie les fichiers critiques qui pourraient causer le problème"""
    critical_files = [
        "config/installation.json",
        "config/config.json",
        "config/security.json",
        "data/clients.json",
        "data/models.json",
        "data/documents.json",
        "ai/model.py",
        "ai/api.py",
        "ai/server_manager.py",
        "ai/chat_interface.py",
        "ai/dashboard_integration.py"
    ]
    
    print("\nVérification des fichiers critiques:")
    for file_path in critical_files:
        detect_encoding(file_path)

def check_directory(directory):
    """Vérifie tous les fichiers dans un répertoire"""
    print(f"\nVérification du répertoire: {directory}")
    if not os.path.exists(directory):
        print(f"❌ Le répertoire {directory} n'existe pas")
        return
        
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.json', '.txt', '.csv', '.yaml', '.yml', '.ini', '.py')):
                file_path = os.path.join(root, file)
                detect_encoding(file_path)

def main():
    print("Démarrage de la vérification d'encodage...")
    
    # Vérifier d'abord les fichiers critiques
    check_critical_files()
    
    # Vérifier les répertoires principaux
    directories = [
        "config",
        "data",
        "logs",
        "assets",
        "ai"
    ]
    
    for directory in directories:
        check_directory(directory)

if __name__ == "__main__":
    main() 