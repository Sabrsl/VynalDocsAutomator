@echo off
setlocal

:: Ajouter le répertoire courant au PYTHONPATH
set PYTHONPATH=%CD%;%PYTHONPATH%

:: Vérifier si les répertoires nécessaires existent
if not exist "data" mkdir data
if not exist "data\clients" mkdir data\clients
if not exist "data\documents" mkdir data\documents
if not exist "data\templates" mkdir data\templates
if not exist "logs" mkdir logs
if not exist "temp_docs" mkdir temp_docs

:: Lancer l'application
python main.py

endlocal 