#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue de validation des documents
"""

import os
import sys
import logging
import subprocess
from typing import Dict, List
import customtkinter as ctk
from tkinter import messagebox

logger = logging.getLogger("VynalDocsAutomator.DocumentValidationView")

class DocumentValidationView:
    """Vue de validation des documents"""
    
    def __init__(self, parent):
        """
        Initialise la vue de validation
        
        Args:
            parent: Widget parent
        """
        self.parent = parent
        self.client_info = {}
        
        # Créer le label de statut
        self.status_label = ctk.CTkLabel(
            parent,
            text="",
            text_color="gray"
        )
        self.status_label.pack(pady=10)

    def handle_validation_result(self, result: Dict) -> None:
        """
        Gère le résultat de la validation
        
        Args:
            result: Résultat de la validation
        """
        if result['status'] == 'error':
            # Déterminer le type d'erreur
            validation_type = result.get('validation_type', 'unknown')
            errors = result.get('errors', [])
            
            if validation_type == 'template':
                self._show_template_errors(errors)
            elif validation_type == 'client':
                self._show_client_errors(errors)
            elif validation_type == 'variables':
                self._show_variable_errors(errors)
            else:
                self._show_generic_error(result['message'])
                
            # Mettre à jour l'interface
            self.status_label.configure(text="Validation échouée", text_color="red")
            
        else:
            # Afficher les statistiques
            self._show_success_info(result)
            
            # Mettre à jour l'interface
            self.status_label.configure(text="Document créé avec succès", text_color="green")
            
            # Proposer d'ouvrir le document
            if 'path' in result:
                self._propose_open_document(result['path'])

    def _show_template_errors(self, errors: List[str]) -> None:
        """
        Affiche les erreurs de template
        
        Args:
            errors: Liste des erreurs
        """
        error_text = "Erreurs de template :\n\n"
        for error in errors:
            error_text += f"• {error}\n"
        
        messagebox.showerror("Erreur de Template", error_text)

    def _show_client_errors(self, errors: List[str]) -> None:
        """
        Affiche les erreurs de données client
        
        Args:
            errors: Liste des erreurs
        """
        error_text = "Erreurs dans les données client :\n\n"
        for error in errors:
            error_text += f"• {error}\n"
        
        # Créer une boîte de dialogue personnalisée
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Erreurs de Validation")
        dialog.geometry("400x300")
        
        # Layout
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(0, weight=1)
        
        # Frame principal
        main_frame = ctk.CTkFrame(dialog)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Label d'erreur
        error_label = ctk.CTkLabel(
            main_frame, 
            text=error_text,
            text_color="red",
            justify="left"
        )
        error_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Frame pour les boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Boutons
        edit_button = ctk.CTkButton(
            button_frame,
            text="Modifier les données",
            command=lambda: self._edit_client_data(errors)
        )
        edit_button.grid(row=0, column=0, padx=5, pady=5)
        
        ok_button = ctk.CTkButton(
            button_frame,
            text="OK",
            command=dialog.destroy
        )
        ok_button.grid(row=0, column=1, padx=5, pady=5)

    def _show_variable_errors(self, errors: List[str]) -> None:
        """
        Affiche les erreurs de variables
        
        Args:
            errors: Liste des erreurs
        """
        error_text = "Variables manquantes ou invalides :\n\n"
        for error in errors:
            error_text += f"• {error}\n"
        
        # Créer une boîte de dialogue personnalisée
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Variables Manquantes")
        dialog.geometry("400x400")
        
        # Layout
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(0, weight=1)
        
        # Frame principal
        main_frame = ctk.CTkFrame(dialog)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Label d'erreur
        error_label = ctk.CTkLabel(
            main_frame,
            text=error_text,
            text_color="red",
            justify="left"
        )
        error_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Frame pour les variables
        variables_frame = ctk.CTkFrame(main_frame)
        variables_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        variables_frame.grid_columnconfigure(0, weight=1)
        
        # Zone de saisie pour chaque variable manquante
        input_widgets = {}
        row = 0
        for error in errors:
            if "manquante" in error or "invalide" in error:
                var_name = error.split(":")[0].strip()
                if "Variable requise manquante" in error:
                    var_name = error.split("Variable requise manquante:")[1].strip()
                
                # Créer un groupe pour la variable
                group = ctk.CTkFrame(variables_frame)
                group.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
                group.grid_columnconfigure(1, weight=1)
                
                # Label
                label = ctk.CTkLabel(group, text=var_name)
                label.grid(row=0, column=0, padx=5, pady=5)
                
                # Champ de saisie
                entry = ctk.CTkEntry(group)
                entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
                input_widgets[var_name] = entry
                
                row += 1
        
        # Frame pour les boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Boutons
        save_button = ctk.CTkButton(
            button_frame,
            text="Enregistrer",
            command=lambda: self._save_missing_variables(input_widgets, dialog)
        )
        save_button.grid(row=0, column=0, padx=5, pady=5)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Annuler",
            command=dialog.destroy
        )
        cancel_button.grid(row=0, column=1, padx=5, pady=5)

    def _show_success_info(self, result: Dict) -> None:
        """
        Affiche les informations de succès
        
        Args:
            result: Résultat de la création
        """
        stats = result.get('stats', {})
        if not stats:
            return
        
        info_text = "Document créé avec succès !\n\n"
        info_text += f"Total documents : {stats['total']}\n"
        info_text += f"Taux de réussite : {stats['success_rate']:.1f}%\n"
        info_text += f"Temps moyen : {stats['avg_time']:.2f}s\n"
        
        if stats.get('last_creation'):
            info_text += f"Dernière création : {stats['last_creation']}\n"
        
        messagebox.showinfo("Création Réussie", info_text)

    def _propose_open_document(self, path: str) -> None:
        """
        Propose d'ouvrir le document créé
        
        Args:
            path: Chemin vers le document
        """
        if messagebox.askyesno("Ouvrir le Document", "Voulez-vous ouvrir le document créé ?"):
            self._open_document(path)

    def _edit_client_data(self, errors: List[str]) -> None:
        """
        Ouvre l'éditeur de données client avec CTkEntry
        
        Args:
            errors: Liste des erreurs
        """
        # Créer une boîte de dialogue personnalisée
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Édition des Données Client")
        dialog.geometry("400x300")
        
        # Layout
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(0, weight=1)
        
        # Frame principal
        main_frame = ctk.CTkFrame(dialog)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Champs de saisie pour les données client
        input_widgets = {}
        row = 0
        for field in ['name', 'email', 'phone', 'company', 'address']:
            # Créer un groupe pour le champ
            group = ctk.CTkFrame(main_frame)
            group.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
            group.grid_columnconfigure(1, weight=1)
            
            # Label
            label = ctk.CTkLabel(group, text=f"{field.capitalize()}:")
            label.grid(row=0, column=0, padx=5, pady=5)
            
            # Champ de saisie
            entry = ctk.CTkEntry(group)
            entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
            
            # Pré-remplir avec les données existantes
            if field in self.client_info:
                entry.insert(0, self.client_info[field])
                
            input_widgets[field] = entry
            row += 1
        
        # Frame pour les boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=10)
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Boutons
        save_button = ctk.CTkButton(
            button_frame,
            text="Enregistrer",
            command=lambda: self._save_missing_variables(input_widgets, dialog)
        )
        save_button.grid(row=0, column=0, padx=5, pady=5)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Annuler",
            command=dialog.destroy
        )
        cancel_button.grid(row=0, column=1, padx=5, pady=5)

    def _save_missing_variables(self, input_widgets: Dict[str, ctk.CTkEntry], dialog: ctk.CTkToplevel) -> None:
        """
        Sauvegarde les variables manquantes
        
        Args:
            input_widgets: Dictionnaire des widgets CTkEntry pour la saisie
            dialog: Boîte de dialogue CTkToplevel
        """
        # Récupérer les valeurs depuis les widgets CTkEntry
        new_variables = {}
        for var_name, widget in input_widgets.items():
            value = widget.get().strip()
            if value:
                new_variables[var_name] = value
        
        # Mettre à jour les variables
        if new_variables:
            self.client_info.update(new_variables)
            
            # Relancer la validation
            self.validate_document()
        
        dialog.destroy()

    def _open_document(self, path: str) -> None:
        """
        Ouvre le document avec l'application par défaut
        
        Args:
            path: Chemin vers le document
        """
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', path])
            else:
                subprocess.run(['xdg-open', path])
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du document: {e}")
            messagebox.showerror(
                "Erreur",
                f"Impossible d'ouvrir le document: {str(e)}"
            )

    def _show_generic_error(self, message: str) -> None:
        """
        Affiche une erreur générique
        
        Args:
            message: Message d'erreur
        """
        messagebox.showerror("Erreur", message)

    def validate_document(self) -> None:
        """
        Valide le document actuel
        """
        # Cette méthode doit être implémentée par la classe qui hérite de DocumentValidationView
        raise NotImplementedError("La méthode validate_document doit être implémentée") 