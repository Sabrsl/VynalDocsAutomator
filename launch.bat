@echo off
REM Script de lancement de Vynal Docs Automator avec écran de démarrage
REM Auteur: Claude
REM Date: 17/03/2025

echo Lancement de Vynal Docs Automator avec écran de démarrage...

REM Vérifier si Python est installé
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python n'est pas installé ou n'est pas dans le PATH.
    echo Veuillez installer Python 3.6 ou supérieur.
    pause
    exit /b 1
)

REM Lancer l'application avec l'écran de démarrage
python main.py --splash

REM En cas d'erreur
if %ERRORLEVEL% neq 0 (
    echo Une erreur s'est produite lors du lancement de l'application.
    pause
)

exit /b 0 