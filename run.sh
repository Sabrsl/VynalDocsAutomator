#!/bin/bash

echo "Démarrage de VynalDocsAutomator..."

# Vérifier si le fichier de configuration existe
if [ ! -f "config/installation.json" ]; then
    echo "Premier lancement détecté. Installation requise..."
    chmod +x install.sh
    ./install.sh
    if [ $? -ne 0 ]; then
        echo "Erreur lors de l'installation."
        read -p "Appuyez sur Entrée pour continuer..."
        exit 1
    fi
fi

# Activer l'environnement virtuel s'il existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Lancer l'application
python main.py
if [ $? -ne 0 ]; then
    echo "Une erreur s'est produite lors de l'exécution."
    read -p "Appuyez sur Entrée pour continuer..."
    exit 1
fi 