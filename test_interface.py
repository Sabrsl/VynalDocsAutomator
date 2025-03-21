#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import customtkinter as ctk
from admin import start_admin

class MockModel:
    """Modèle simulé pour les tests"""
    def __init__(self):
        self.base_dir = "test_data"
        self.admin_dir = "test_data/admin"
        self.logs_dir = "test_data/logs"
        self.data_dir = "test_data/data"
        self.current_user = {
            "username": "Admin Test",
            "role": "Administrateur"
        }

def main():
    # Configurer le thème
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Créer la fenêtre principale
    root = ctk.CTk()
    root.title("Test Interface Admin")
    root.geometry("1200x800")
    
    # Créer le modèle simulé
    mock_model = MockModel()
    
    # Démarrer l'interface admin
    admin = start_admin(root, mock_model)
    
    # Lancer la boucle principale
    root.mainloop()

if __name__ == "__main__":
    main() 