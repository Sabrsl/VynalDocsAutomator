@echo off
echo Démarrage de VynalDocsAutomator...

:: Vérifier si le fichier de configuration existe
if not exist "config\installation.json" (
    echo Premier lancement détecté. Installation requise...
    call install.bat
    if errorlevel 1 (
        echo Erreur lors de l'installation.
        pause
        exit /b 1
    )
)

:: Lancer l'application
python main.py
if errorlevel 1 (
    echo Une erreur s'est produite lors de l'exécution.
    pause
    exit /b 1
) 