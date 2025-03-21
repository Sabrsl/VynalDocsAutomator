import os
import sys
import subprocess
import json
import logging
from pathlib import Path
import platform
import tempfile
import datetime
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VynalDocsAutomator.Setup")

# Configuration selon le système d'exploitation
SYSTEM = platform.system()
TESSERACT_MIRRORS = [
    "https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe",
    "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.5.0.20241111.exe"
]

def check_tesseract_installed():
    """Vérifie silencieusement si Tesseract est déjà installé"""
    logger.info("Vérification de l'installation de Tesseract...")
    
    # Vérifier d'abord dans le PATH système
    tesseract_in_path = shutil.which("tesseract")
    if tesseract_in_path:
        try:
            # Vérifier que Tesseract fonctionne
            result = subprocess.run(["tesseract", "--version"], 
                                 capture_output=True, 
                                 text=True,
                                 creationflags=subprocess.CREATE_NO_WINDOW if SYSTEM == "Windows" else 0)
            if "tesseract" in result.stdout.lower():
                logger.info(f"Tesseract trouvé dans le PATH: {tesseract_in_path}")
                return True
        except Exception as e:
            logger.debug(f"Erreur lors de la vérification de Tesseract dans le PATH: {e}")
    
    if SYSTEM == "Windows":
        # Vérifier dans Program Files
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(tesseract_path):
            try:
                result = subprocess.run([tesseract_path, "--version"], 
                                     capture_output=True, 
                                     text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                if "tesseract" in result.stdout.lower():
                    logger.info(f"Tesseract trouvé dans Program Files")
                    return True
            except Exception as e:
                logger.debug(f"Erreur lors de la vérification dans Program Files: {e}")
    
    logger.info("Tesseract n'est pas trouvé ou n'est pas fonctionnel")
    return False

def install_tesseract():
    """Installe Tesseract selon le système d'exploitation"""
    logger.info("Installation de Tesseract...")
    
    # Vérifier si Tesseract est déjà installé
    if check_tesseract_installed():
        return True
    
    if SYSTEM == "Windows":
        return install_tesseract_windows()
    elif SYSTEM == "Linux":
        return install_tesseract_linux()
    elif SYSTEM == "Darwin":
        return install_tesseract_macos()
    else:
        logger.error(f"Système d'exploitation non supporté: {SYSTEM}")
        return False

def install_tesseract_windows():
    """Installation de Tesseract sous Windows"""
    try:
        # Télécharger l'installateur
        temp_dir = tempfile.gettempdir()
        installer_path = os.path.join(temp_dir, "tesseract_installer.exe")
        
        # Essayer chaque miroir jusqu'à ce qu'un téléchargement réussisse
        download_success = False
        for url in TESSERACT_MIRRORS:
            logger.info(f"Tentative de téléchargement depuis {url}...")
            try:
                import urllib.request
                urllib.request.urlretrieve(url, installer_path)
                download_success = True
                break
            except Exception as e:
                logger.warning(f"Échec du téléchargement depuis {url}: {e}")
                continue
        
        if not download_success:
            logger.error("Impossible de télécharger Tesseract depuis tous les miroirs")
            return False
        
        # Créer le fichier de configuration
        create_tesseract_config()
        
        # Installer Tesseract avec élévation des privilèges
        logger.info("Installation de Tesseract (nécessite des droits administrateur)...")
        try:
            command = f'powershell.exe Start-Process "{installer_path}" -ArgumentList "/SILENT,/NORESTART,/LOADINF=tesseract_config.inf" -Verb RunAs -Wait'
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur lors de l'installation silencieuse: {e}")
            logger.info("Tentative d'installation interactive (nécessite des droits administrateur)...")
            command = f'powershell.exe Start-Process "{installer_path}" -Verb RunAs -Wait'
            subprocess.run(command, shell=True, check=True)
        
        # Ajouter au PATH
        add_tesseract_to_windows_path()
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'installation de Tesseract: {e}")
        return False

def install_tesseract_linux():
    """Installation de Tesseract sous Linux"""
    try:
        if subprocess.call(["which", "apt-get"]) == 0:
            subprocess.check_call(["sudo", "apt-get", "update"])
            subprocess.check_call([
                "sudo", "apt-get", "install", "-y",
                "tesseract-ocr",
                "tesseract-ocr-fra",
                "tesseract-ocr-eng"
            ])
        elif subprocess.call(["which", "dnf"]) == 0:
            subprocess.check_call([
                "sudo", "dnf", "install", "-y",
                "tesseract",
                "tesseract-langpack-fra",
                "tesseract-langpack-eng"
            ])
        else:
            logger.error("Gestionnaire de paquets non supporté")
            return False
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de l'installation de Tesseract: {e}")
        return False

def install_tesseract_macos():
    """Installation de Tesseract sous macOS"""
    try:
        if subprocess.call(["which", "brew"]) != 0:
            logger.info("Installation de Homebrew...")
            subprocess.check_call(["/bin/bash", "-c", 
                "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"])
        
        subprocess.check_call(["brew", "install", "tesseract"])
        subprocess.check_call(["brew", "install", "tesseract-lang"])
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de l'installation de Tesseract: {e}")
        return False

def create_tesseract_config():
    """Crée le fichier de configuration pour l'installation silencieuse sous Windows"""
    if SYSTEM == "Windows":
        config_content = """
[Setup]
Lang=default
Dir=C:\Program Files\Tesseract-OCR
Group=Tesseract-OCR
NoIcons=0
SetupType=custom
Components=main,fra,eng
Tasks=
"""
        with open("tesseract_config.inf", "w") as f:
            f.write(config_content)

def add_tesseract_to_windows_path():
    """Ajoute Tesseract au PATH système sous Windows"""
    if SYSTEM == "Windows":
        try:
            import winreg
            tesseract_path = r"C:\Program Files\Tesseract-OCR"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                0, winreg.KEY_ALL_ACCESS)
            current_path = winreg.QueryValueEx(key, "Path")[0]
            if tesseract_path not in current_path:
                new_path = current_path + ";" + tesseract_path
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                winreg.CloseKey(key)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout au PATH: {e}")
            return False

def create_first_run_file():
    """Crée un fichier indiquant que l'installation est terminée"""
    config = {
        "first_run": False,
        "tesseract_installed": True,
        "installation_date": str(datetime.datetime.now())
    }
    os.makedirs("config", exist_ok=True)
    with open("config/installation.json", "w") as f:
        json.dump(config, f, indent=4)

def main():
    """Fonction principale d'installation"""
    logger.info("Démarrage de l'installation de VynalDocsAutomator...")
    
    if not install_tesseract():
        return False
    
    create_first_run_file()
    
    logger.info("Installation terminée avec succès!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 