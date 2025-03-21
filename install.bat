@echo off
echo Installation de VynalDocsAutomator...
echo.

:: Vérifier si Python est installé
python --version > nul 2>&1
if errorlevel 1 (
    echo Python n'est pas installé. Veuillez installer Python 3.8 ou supérieur.
    echo Téléchargez Python depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Créer l'environnement virtuel
echo Création de l'environnement virtuel...
python -m venv venv
call venv\Scripts\activate.bat

:: Lancer l'installation
echo Lancement de l'installation...
python setup.py

if errorlevel 1 (
    echo Une erreur s'est produite lors de l'installation.
    pause
    exit /b 1
)

echo.
echo Installation terminée avec succès !
echo Vous pouvez maintenant lancer l'application avec 'python main.py'
pause 