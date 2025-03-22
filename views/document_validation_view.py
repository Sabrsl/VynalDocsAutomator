#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue de validation des documents
"""

import os
import sys
import logging
import subprocess
from typing import Dict, List, Any, Optional
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
        if not isinstance(result, dict):
            logger.error(f"Erreur: le résultat n'est pas un dictionnaire: {type(result)}")
            self._show_generic_error("Format de résultat invalide")
            return
            
        if result.get('status') == 'error':
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
                self._show_generic_error(result.get('message', 'Erreur inconnue'))
                
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
        dialog.resizable(False, False)  # Empêcher le redimensionnement
        dialog.grab_set()  # Rendre la fenêtre modale
        
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
        
        # Centrer la fenêtre
        self._center_window(dialog)

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
        dialog.grab_set()  # Rendre la fenêtre modale
        
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
        
        # Centrer la fenêtre
        self._center_window(dialog)

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
        info_text += f"Total documents : {stats.get('total', 0)}\n"
        
        # Vérifier que success_rate est un nombre avant de l'afficher
        success_rate = stats.get('success_rate', 0)
        if isinstance(success_rate, (int, float)):
            info_text += f"Taux de réussite : {success_rate:.1f}%\n"
        
        # Vérifier que avg_time est un nombre avant de l'afficher
        avg_time = stats.get('avg_time', 0)
        if isinstance(avg_time, (int, float)):
            info_text += f"Temps moyen : {avg_time:.2f}s\n"
        
        if stats.get('last_creation'):
            info_text += f"Dernière création : {stats['last_creation']}\n"
        
        messagebox.showinfo("Création Réussie", info_text)

    def _propose_open_document(self, path: str) -> None:
        """
        Propose d'ouvrir le document créé
        
        Args:
            path: Chemin vers le document
        """
        if not path or not os.path.exists(path):
            logger.warning(f"Le document n'existe pas: {path}")
            return
            
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
        dialog.grab_set()  # Rendre la fenêtre modale
        
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
            command=lambda: self._save_client_data(input_widgets, dialog)
        )
        save_button.grid(row=0, column=0, padx=5, pady=5)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Annuler",
            command=dialog.destroy
        )
        cancel_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Centrer la fenêtre
        self._center_window(dialog)
    
    def _save_client_data(self, input_widgets: Dict[str, ctk.CTkEntry], dialog: ctk.CTkToplevel) -> None:
        """
        Sauvegarde les données client
        
        Args:
            input_widgets: Dictionnaire des widgets CTkEntry pour la saisie
            dialog: Boîte de dialogue CTkToplevel
        """
        # Récupérer les valeurs depuis les widgets CTkEntry
        new_client_info = {}
        for field, widget in input_widgets.items():
            value = widget.get().strip()
            if value:
                new_client_info[field] = value
        
        # Mettre à jour les données client
        if new_client_info:
            self.client_info.update(new_client_info)
            
            # Relancer la validation
            try:
                self.validate_document()
            except NotImplementedError:
                logger.warning("La méthode validate_document n'est pas implémentée")
                messagebox.showinfo("Information", "Les données ont été mises à jour mais la validation n'a pas pu être relancée.")
        
        dialog.destroy()

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
            # S'assurer que les variables sont correctement stockées dans client_info
            if not hasattr(self, 'client_info') or self.client_info is None:
                self.client_info = {}
                
            self.client_info.update(new_variables)
            
            # Relancer la validation
            try:
                self.validate_document()
            except NotImplementedError:
                logger.warning("La méthode validate_document n'est pas implémentée")
                messagebox.showinfo("Information", "Les variables ont été mises à jour mais la validation n'a pas pu être relancée.")
        
        dialog.destroy()

    def _open_document(self, path: str) -> None:
        """
        Ouvre le document avec l'application par défaut
        
        Args:
            path: Chemin vers le document
        """
        try:
            if not path or not os.path.exists(path):
                logger.warning(f"Le document n'existe pas: {path}")
                messagebox.showerror("Erreur", f"Le document n'existe pas: {path}")
                return
                
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', path], check=True)
            else:
                subprocess.run(['xdg-open', path], check=True)
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
    
    def _center_window(self, window: ctk.CTkToplevel) -> None:
        """
        Centre une fenêtre sur l'écran
        
        Args:
            window: Fenêtre à centrer
        """
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def validate_document(self) -> None:
        """
        Valide le document actuel
        """
        # Cette méthode doit être implémentée par la classe qui hérite de DocumentValidationView
        raise NotImplementedError("La méthode validate_document doit être implémentée")