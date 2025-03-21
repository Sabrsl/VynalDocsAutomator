#!/bin/bash

echo "Installation de VynalDocsAutomator..."
echo

# Détecter le système d'exploitation
OS="$(uname -s)"
echo "Système détecté : $OS"

# Fonction pour vérifier si Tesseract est installé avec les langues requises
check_tesseract() {
    echo "Vérification de l'installation de Tesseract..."
    
    # Vérifier si tesseract est installé
    if ! command -v tesseract &> /dev/null; then
        return 1
    fi
    
    # Vérifier la version
    if ! tesseract --version 2>&1 | grep -q "tesseract"; then
        return 1
    fi
    
    # Vérifier les langues installées
    LANGS=$(tesseract --list-langs 2>&1)
    if ! echo "$LANGS" | grep -q "fra" || ! echo "$LANGS" | grep -q "eng"; then
        return 1
    fi
    
    echo "Tesseract est déjà installé avec les langues requises"
    return 0
}

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Python n'est pas installé. Veuillez installer Python 3.8 ou supérieur."
    case $OS in
        "Linux")
            echo "Sur Ubuntu/Debian : sudo apt-get install python3"
            echo "Sur Fedora : sudo dnf install python3"
            ;;
        "Darwin")
            echo "Sur macOS : brew install python3"
            echo "Ou téléchargez depuis https://www.python.org/downloads/"
            ;;
    esac
    exit 1
fi

# Vérifier la version de Python
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
    echo "Python 3.8 ou supérieur est requis. Version actuelle : $PYTHON_VERSION"
    exit 1
fi

# Créer l'environnement virtuel
echo "Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances Python
echo "Installation des packages Python..."
pip install --upgrade pip
pip install pytesseract pdf2image Pillow opencv-python numpy customtkinter python-docx reportlab

# Installer Tesseract selon le système d'exploitation
echo "Vérification/Installation de Tesseract..."

# Vérifier d'abord si Tesseract est déjà installé
if ! check_tesseract; then
    case $OS in
        "Linux")
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y tesseract tesseract-langpack-fra tesseract-langpack-eng
            else
                echo "Système non supporté. Veuillez installer Tesseract manuellement."
                exit 1
            fi
            ;;
        "Darwin")
            if ! command -v brew &> /dev/null; then
                echo "Installation de Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install tesseract
            brew install tesseract-lang
            ;;
    esac
    
    # Vérifier que l'installation a réussi
    if ! check_tesseract; then
        echo "Erreur : L'installation de Tesseract a échoué"
        exit 1
    fi
fi

# Créer le fichier de configuration
mkdir -p config
cat > config/installation.json << EOL
{
    "first_run": false,
    "tesseract_installed": true,
    "python_packages_installed": true,
    "installation_date": "$(date -Iseconds)"
}
EOL

echo
echo "Installation terminée avec succès !"
echo "Vous pouvez maintenant lancer l'application avec 'python main.py'"

# Rendre le script exécutable
chmod +x main.py 