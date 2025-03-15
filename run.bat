@echo off
setlocal

:: Ajouter le répertoire courant au PYTHONPATH
set PYTHONPATH=%CD%;%PYTHONPATH%

:: Lancer l'application
python main.py

endlocal 