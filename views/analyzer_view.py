#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue de l'analyseur de documents
"""

import os
import logging
import customtkinter as ctk
from tkinter import filedialog
from typing import Optional, Dict, Any

logger = logging.getLogger("VynalDocsAutomator.AnalyzerView")

class AnalyzerView:
    """Vue de l'analyseur de documents"""
    
    def __init__(self, parent, model):
        """
        Initialise la vue de l'analyseur
        
        Args:
            parent: Widget parent
            model: Modèle de l'application
        """
        self.parent = parent
        self.model = model
        
        # Créer le cadre principal
        self.frame = ctk.CTkFrame(parent)
        
        # En-tête
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.pack(fill=ctk.X, padx=20, pady=(20, 10))
        
        # Titre de la section
        title = ctk.CTkLabel(
            header,
            text="Analyseur de documents",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side=ctk.LEFT)
        
        # Zone de défilement
        self.scroll_frame = ctk.CTkScrollableFrame(self.frame)
        self.scroll_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Créer les composants de l'interface
        self._create_widgets()
        
        # Cacher la vue par défaut
        self.hide()
        
        logger.info("Vue de l'analyseur initialisée")
    
    def _create_widgets(self):
        """Crée les widgets de l'interface"""
        # Zone de sélection des fichiers
        file_frame = ctk.CTkFrame(self.scroll_frame)
        file_frame.pack(fill=ctk.X, pady=10)
        
        # Bouton de sélection des fichiers
        select_button = ctk.CTkButton(
            file_frame,
            text="Sélectionner des fichiers",
            command=self._select_files
        )
        select_button.pack(side=ctk.LEFT, padx=10)
        
        # Liste des fichiers sélectionnés
        self.file_list = ctk.CTkTextbox(
            file_frame,
            height=100,
            state="disabled"
        )
        self.file_list.pack(fill=ctk.X, padx=10, pady=5)
        
        # Bouton d'analyse
        analyze_button = ctk.CTkButton(
            file_frame,
            text="Analyser",
            command=self._analyze_files
        )
        analyze_button.pack(side=ctk.RIGHT, padx=10)
        
        # Zone des résultats
        results_frame = ctk.CTkFrame(self.scroll_frame)
        results_frame.pack(fill=ctk.BOTH, expand=True, pady=10)
        
        # Titre des résultats
        results_title = ctk.CTkLabel(
            results_frame,
            text="Résultats de l'analyse",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        results_title.pack(anchor="w", padx=10, pady=5)
        
        # Zone de texte des résultats
        self.results_text = ctk.CTkTextbox(
            results_frame,
            state="disabled"
        )
        self.results_text.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
    
    def _select_files(self):
        """Ouvre une boîte de dialogue pour sélectionner des fichiers"""
        files = filedialog.askopenfilenames(
            title="Sélectionner des documents",
            filetypes=[
                ("Documents", "*.pdf;*.docx;*.doc;*.txt"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx;*.doc"),
                ("Texte", "*.txt"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if files:
            self.file_list.configure(state="normal")
            self.file_list.delete("1.0", ctk.END)
            for file in files:
                self.file_list.insert(ctk.END, f"{file}\n")
            self.file_list.configure(state="disabled")
            
            self.selected_files = list(files)
    
    def _analyze_files(self):
        """Lance l'analyse des fichiers sélectionnés"""
        if not hasattr(self, 'selected_files') or not self.selected_files:
            self.show_message(
                "Erreur",
                "Veuillez sélectionner des fichiers à analyser",
                "error"
            )
            return
        
        try:
            # Vérifier que le modèle est disponible
            if not self.model:
                raise ValueError("Le modèle n'est pas initialisé")
            
            # Lancer l'analyse
            results = self.model.analyze_documents(self.selected_files)
            
            # Afficher les résultats
            self.results_text.configure(state="normal")
            self.results_text.delete("1.0", ctk.END)
            
            if isinstance(results, dict):
                for file_path, result in results.items():
                    self.results_text.insert(ctk.END, f"Fichier : {file_path}\n")
                    self.results_text.insert(ctk.END, "-" * 50 + "\n")
                    
                    if isinstance(result, dict):
                        for key, value in result.items():
                            self.results_text.insert(ctk.END, f"{key}: {value}\n")
                    else:
                        self.results_text.insert(ctk.END, str(result) + "\n")
                    
                    self.results_text.insert(ctk.END, "\n")
            else:
                self.results_text.insert(ctk.END, str(results))
            
            self.results_text.configure(state="disabled")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des documents: {e}")
            self.show_message(
                "Erreur",
                f"Une erreur est survenue lors de l'analyse: {e}",
                "error"
            )
    
    def show(self):
        """Affiche la vue"""
        self.frame.pack(fill=ctk.BOTH, expand=True)
    
    def hide(self):
        """Cache la vue"""
        self.frame.pack_forget()
    
    def show_message(self, title, message, message_type="info"):
        """
        Affiche un message à l'utilisateur
        
        Args:
            title: Titre du message
            message: Contenu du message
            message_type: Type de message (info, error, warning)
        """
        from views.settings_view import DialogUtils
        DialogUtils.show_message(self.frame, title, message, message_type) 