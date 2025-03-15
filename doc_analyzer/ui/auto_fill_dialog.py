#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'interface utilisateur pour le remplissage automatique de documents
Fournit une boîte de dialogue qui affiche les données extraites et permet à l'utilisateur
de les valider, les modifier et de les utiliser pour le remplissage automatique.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Tuple, Optional, Union, Callable

# Importation de customtkinter pour l'interface graphique moderne
try:
    import customtkinter as ctk
except ImportError:
    # Fallback sur tkinter standard si customtkinter n'est pas disponible
    import tkinter as tk
    ctk = tk
    logging.getLogger("Vynal Docs Automator").warning(
        "Module customtkinter non trouvé, utilisation de tkinter standard."
    )

from tkinter import messagebox, filedialog, ttk
from PIL import Image, ImageTk

# Importation des modules internes
from ..config import get_config
from ..analyzer import DocumentAnalyzer
from .client_matcher import ClientMatcher

# Configuration du logger
logger = logging.getLogger("Vynal Docs Automator.doc_analyzer.ui.auto_fill_dialog")

class AutoFillDialog:
    """
    Boîte de dialogue pour le remplissage automatique de documents
    Permet de visualiser, valider et appliquer les données extraites d'un document
    """
    
    def __init__(self, parent, analyzer: DocumentAnalyzer = None, clients_db: List[Dict[str, Any]] = None):
        """
        Initialise la boîte de dialogue de remplissage automatique
        
        Args:
            parent: Widget parent (fenêtre ou cadre)
            analyzer (DocumentAnalyzer, optional): Analyseur de documents à utiliser
            clients_db (list, optional): Base de données des clients
        """
        self.parent = parent
        self.config = get_config()
        self.ui_config = self.config.get_section("ui").get("auto_fill_dialog", {})
        
        # Initialiser l'analyseur
        self.analyzer = analyzer or DocumentAnalyzer(self.config.get_all())
        
        # Base de données des clients
        self.clients_db = clients_db or []
        
        # Gestion des clients
        self.client_matcher = ClientMatcher(self.clients_db)
        
        # Données extraites et état
        self.extraction_results = {}
        self.extracted_data = {}
        self.confidence_scores = {}
        self.form_fields = {}
        self.selected_client = None
        self.current_document_path = None
        self.data_modified = False
        
        # Initialisation des composants UI
        self._init_components()
        
        logger.info("Boîte de dialogue de remplissage automatique initialisée")
    
    def _init_components(self):
        """Initialise les composants de l'interface utilisateur"""
        # Configuration de la fenêtre
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title(self.ui_config.get("window_title", "Remplissage Automatique"))
        self.dialog.geometry(f"{self.ui_config.get('window_width', 800)}x{self.ui_config.get('window_height', 600)}")
        self.dialog.minsize(self.ui_config.get("min_width", 640), self.ui_config.get("min_height", 480))
        
        # Configuration du style
        self._setup_style()
        
        # Création du layout principal
        self._create_layout()
        
        # Initialisation des widgets
        self._init_widgets()
        
        # Centrer la fenêtre
        self.dialog.update_idletasks()
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width - self.dialog.winfo_width()) // 2
        y = (screen_height - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Cacher la fenêtre initialement
        self.dialog.withdraw()
        
        # Gestion des événements de fermeture
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Initialisation des variables
        self.form_fields = {}
    
    def _setup_style(self):
        """Configure le style de l'interface utilisateur"""
        # Configurer le thème selon le paramètre ou le système
        theme = self.ui_config.get("theme", "system")
        if theme == "system":
            ctk.set_appearance_mode("system")
        else:
            ctk.set_appearance_mode(theme)
        
        # Taille de police
        self.font_size = self.ui_config.get("font_size", 11)
        
        # Configuration des couleurs et styles
        self.colors = {
            "high_confidence": "#4CAF50",  # Vert
            "medium_confidence": "#FFC107",  # Jaune
            "low_confidence": "#F44336",  # Rouge
            "background": "#F0F0F0" if theme == "light" else "#333333",
            "text": "#333333" if theme == "light" else "#FFFFFF"
        }
    
    def _create_layout(self):
        """Crée la structure de layout principale"""
        # Conteneur principal avec marge
        self.main_frame = ctk.CTkFrame(self.dialog, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Layout en deux colonnes
        self.left_frame = ctk.CTkFrame(self.main_frame)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=0)
        
        self.right_frame = ctk.CTkFrame(self.main_frame)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=0)
        
        # Barre de boutons en bas
        self.button_frame = ctk.CTkFrame(self.dialog)
        self.button_frame.pack(fill="x", expand=False, padx=10, pady=(0, 10))
    
    def _init_widgets(self):
        """Initialise tous les widgets de l'interface"""
        # === Panneau gauche ===
        # En-tête avec information sur le document analysé
        self.doc_info_frame = ctk.CTkFrame(self.left_frame)
        self.doc_info_frame.pack(fill="x", expand=False, padx=10, pady=10)
        
        self.doc_label = ctk.CTkLabel(self.doc_info_frame, text="Document analysé :", font=("Arial", self.font_size))
        self.doc_label.pack(anchor="w", padx=5, pady=5)
        
        self.doc_path_var = ctk.StringVar(value="Aucun document sélectionné")
        self.doc_path = ctk.CTkLabel(self.doc_info_frame, textvariable=self.doc_path_var, font=("Arial", self.font_size-1))
        self.doc_path.pack(anchor="w", padx=5, pady=0)
        
        self.doc_type_var = ctk.StringVar(value="Type : -")
        self.doc_type = ctk.CTkLabel(self.doc_info_frame, textvariable=self.doc_type_var, font=("Arial", self.font_size-1))
        self.doc_type.pack(anchor="w", padx=5, pady=2)
        
        # Panneau des données extraites
        self.extracted_frame = ctk.CTkFrame(self.left_frame)
        self.extracted_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.extracted_label = ctk.CTkLabel(self.extracted_frame, text="Données extraites", font=("Arial", self.font_size, "bold"))
        self.extracted_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # ScrollableFrame pour les champs
        self.fields_canvas = ctk.CTkCanvas(self.extracted_frame, highlightthickness=0)
        self.fields_canvas.pack(side="left", fill="both", expand=True)
        
        self.fields_scrollbar = ctk.CTkScrollbar(self.extracted_frame, orientation="vertical", command=self.fields_canvas.yview)
        self.fields_scrollbar.pack(side="right", fill="y")
        
        self.fields_canvas.configure(yscrollcommand=self.fields_scrollbar.set)
        self.fields_canvas.bind("<Configure>", lambda e: self.fields_canvas.configure(scrollregion=self.fields_canvas.bbox("all")))
        
        self.fields_frame = ctk.CTkFrame(self.fields_canvas, corner_radius=0)
        self.fields_canvas.create_window((0, 0), window=self.fields_frame, anchor="nw", width=self.fields_canvas.winfo_width())
        
        # === Panneau droit ===
        # Section client
        self.client_frame = ctk.CTkFrame(self.right_frame)
        self.client_frame.pack(fill="x", expand=False, padx=10, pady=10)
        
        self.client_label = ctk.CTkLabel(self.client_frame, text="Client", font=("Arial", self.font_size, "bold"))
        self.client_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.client_search_frame = ctk.CTkFrame(self.client_frame)
        self.client_search_frame.pack(fill="x", expand=False, padx=5, pady=5)
        
        self.client_search_var = ctk.StringVar()
        self.client_search_var.trace_add("write", self._on_search_changed)
        
        self.client_search_label = ctk.CTkLabel(self.client_search_frame, text="Rechercher :", font=("Arial", self.font_size-1))
        self.client_search_label.pack(side="left", padx=5, pady=5)
        
        self.client_search_entry = ctk.CTkEntry(self.client_search_frame, textvariable=self.client_search_var, width=200, font=("Arial", self.font_size))
        self.client_search_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        
        self.client_search_button = ctk.CTkButton(self.client_search_frame, text="Rechercher", command=self._search_clients, width=100, font=("Arial", self.font_size-1))
        self.client_search_button.pack(side="right", padx=5, pady=5)
        
        # Liste des clients correspondants
        self.client_list_frame = ctk.CTkFrame(self.right_frame)
        self.client_list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.client_list_label = ctk.CTkLabel(self.client_list_frame, text="Clients correspondants", font=("Arial", self.font_size-1))
        self.client_list_label.pack(anchor="w", padx=10, pady=5)
        
        # Liste des clients (treeview)
        self.client_list = ttk.Treeview(self.client_list_frame, columns=("name", "email", "phone", "match"), show="headings", height=10)
        self.client_list.heading("name", text="Nom")
        self.client_list.heading("email", text="Email")
        self.client_list.heading("phone", text="Téléphone")
        self.client_list.heading("match", text="Correspondance")
        
        self.client_list.column("name", width=150)
        self.client_list.column("email", width=150)
        self.client_list.column("phone", width=120)
        self.client_list.column("match", width=100)
        
        self.client_list.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.client_list_scrollbar = ctk.CTkScrollbar(self.client_list_frame, orientation="vertical", command=self.client_list.yview)
        self.client_list_scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)
        
        self.client_list.configure(yscrollcommand=self.client_list_scrollbar.set)
        
        # Liaison du double-clic pour sélectionner un client
        self.client_list.bind("<Double-1>", self._on_client_select)
        
        # Actions rapides sur les clients
        self.client_actions_frame = ctk.CTkFrame(self.right_frame)
        self.client_actions_frame.pack(fill="x", expand=False, padx=10, pady=(0, 10))
        
        self.new_client_button = ctk.CTkButton(self.client_actions_frame, text="Nouveau Client", command=self._create_new_client, font=("Arial", self.font_size-1))
        self.new_client_button.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        
        self.edit_client_button = ctk.CTkButton(self.client_actions_frame, text="Modifier Client", command=self._edit_client, state="disabled", font=("Arial", self.font_size-1))
        self.edit_client_button.pack(side="right", padx=5, pady=5, fill="x", expand=True)
        
        # === Barre de boutons ===
        self.cancel_button = ctk.CTkButton(self.button_frame, text="Annuler", command=self._on_close, width=120, font=("Arial", self.font_size))
        self.cancel_button.pack(side="left", padx=10, pady=10)
        
        self.apply_button = ctk.CTkButton(self.button_frame, text="Appliquer", command=self._on_apply, state="disabled", width=120, font=("Arial", self.font_size))
        self.apply_button.pack(side="right", padx=10, pady=10)
        
        self.validate_button = ctk.CTkButton(self.button_frame, text="Valider", command=self._on_validate, state="disabled", width=120, font=("Arial", self.font_size))
        self.validate_button.pack(side="right", padx=10, pady=10)
    
    def _create_field_widgets(self):
        """Crée les widgets pour les champs de données extraites"""
        # Nettoyer les widgets existants
        for widget in self.fields_frame.winfo_children():
            widget.destroy()
        
        self.form_fields = {}
        
        # Aucune donnée extraite
        if not self.extracted_data:
            no_data_label = ctk.CTkLabel(self.fields_frame, text="Aucune donnée extraite", font=("Arial", self.font_size))
            no_data_label.pack(anchor="center", padx=20, pady=20)
            return
        
        # Créer les widgets pour chaque section
        for section, fields in self.extracted_data.items():
            if not fields:
                continue
            
            # Convertir les noms de section en titres lisibles
            section_titles = {
                "personal_info": "Informations Personnelles",
                "professional_info": "Informations Professionnelles",
                "document_info": "Informations Document",
                "banking_info": "Informations Bancaires",
                "amounts": "Montants",
                "dates": "Dates",
                "parties": "Parties",
                "payment": "Paiement",
                "obligations": "Obligations",
                "products": "Produits/Services"
            }
            
            section_title = section_titles.get(section, section.replace('_', ' ').title())
            
            # Créer un cadre pour la section
            section_frame = ctk.CTkFrame(self.fields_frame)
            section_frame.pack(fill="x", expand=False, padx=5, pady=5)
            
            section_label = ctk.CTkLabel(section_frame, text=section_title, font=("Arial", self.font_size, "bold"))
            section_label.pack(anchor="w", padx=10, pady=5)
            
            # Créer les widgets pour chaque champ
            if isinstance(fields, dict):
                for field, value in fields.items():
                    field_frame = self._create_field_widget(section_frame, section, field, value)
                    field_frame.pack(fill="x", expand=False, padx=10, pady=2)
            elif isinstance(fields, list):
                # Pour les listes (ex: produits)
                for i, item in enumerate(fields):
                    if isinstance(item, dict):
                        item_frame = ctk.CTkFrame(section_frame)
                        item_frame.pack(fill="x", expand=False, padx=10, pady=2)
                        
                        item_label = ctk.CTkLabel(item_frame, text=f"Item {i+1}", font=("Arial", self.font_size-1))
                        item_label.pack(anchor="w", padx=5, pady=2)
                        
                        for sub_field, sub_value in item.items():
                            sub_field_frame = self._create_field_widget(item_frame, f"{section}.{i}", sub_field, sub_value)
                            sub_field_frame.pack(fill="x", expand=False, padx=10, pady=2)
        
        # Mettre à jour le scrollregion
        self.fields_canvas.update_idletasks()
        self.fields_canvas.configure(scrollregion=self.fields_canvas.bbox("all"))
    
    def _create_field_widget(self, parent, section, field, value):
        """
        Crée un widget pour un champ spécifique
        
        Args:
            parent: Widget parent
            section (str): Section du champ
            field (str): Nom du champ
            value: Valeur du champ
            
        Returns:
            CTkFrame: Frame contenant les widgets du champ
        """
        # Créer un cadre pour le champ
        field_frame = ctk.CTkFrame(parent, fg_color="transparent")
        
        # Convertir les noms de champs en labels lisibles
        field_labels = {
            "last_name": "Nom",
            "first_name": "Prénom",
            "birth_date": "Date de naissance",
            "birth_place": "Lieu de naissance",
            "gender": "Genre",
            "nationality": "Nationalité",
            "email": "Email",
            "phone": "Téléphone",
            "address": "Adresse",
            "company": "Société",
            "position": "Fonction",
            "iban": "IBAN",
            "bic": "BIC",
            "bank_name": "Banque",
            "price": "Prix",
            "amount": "Montant",
            "total": "Total",
            "tax": "TVA",
            "date": "Date",
            "issue_date": "Date d'émission",
            "expiry_date": "Date d'expiration",
            "description": "Description"
        }
        
        field_label_text = field_labels.get(field, field.replace('_', ' ').title())
        
        # Obtenir le score de confiance
        confidence = self.confidence_scores.get(f"{section}.{field}", 0.5)
        confidence_color = self._get_confidence_color(confidence)
        
        # Afficher le label et l'indicateur de confiance
        label_frame = ctk.CTkFrame(field_frame, fg_color="transparent")
        label_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        # Indicateur de confiance (petit rectangle coloré)
        if self.ui_config.get("show_confidence", True):
            confidence_indicator = ctk.CTkFrame(label_frame, width=8, height=20, fg_color=confidence_color)
            confidence_indicator.pack(side="left", padx=(0, 5), pady=0)
        
        # Label du champ
        field_label = ctk.CTkLabel(label_frame, text=f"{field_label_text}:", font=("Arial", self.font_size-1), width=120, anchor="w")
        field_label.pack(side="left", padx=5, pady=0)
        
        # Widget d'entrée selon le type de valeur
        if value is None:
            value = ""
        
        # Créer la variable pour le champ
        field_var = None
        field_widget = None
        
        # Format de l'ID unique pour le champ
        field_id = f"{section}.{field}"
        
        # Traitement selon le type de champ
        if isinstance(value, bool):
            field_var = ctk.BooleanVar(value=value)
            field_widget = ctk.CTkCheckBox(field_frame, text="", variable=field_var, font=("Arial", self.font_size-1))
            field_widget.pack(side="left", fill="x", expand=True, padx=5, pady=0)
        
        elif field in ["gender", "type", "mode_paiement", "status"]:
            # Champs avec choix limités (combobox)
            field_var = ctk.StringVar(value=str(value))
            
            # Options selon le champ
            options = {
                "gender": ["M", "F", "Autre"],
                "type": ["Contrat", "Facture", "Devis", "Attestation"],
                "mode_paiement": ["Virement", "Chèque", "Carte", "Espèces", "Prélèvement"],
                "status": ["En cours", "Terminé", "Annulé", "En attente"]
            }
            
            field_widget = ctk.CTkComboBox(field_frame, values=options.get(field, []), variable=field_var, font=("Arial", self.font_size-1), width=200)
            field_widget.pack(side="left", fill="x", expand=True, padx=5, pady=0)
        
        elif field.endswith("_date") or field == "birth_date" or field == "date":
            # Champs de type date
            field_var = ctk.StringVar(value=str(value))
            field_widget = ctk.CTkEntry(field_frame, textvariable=field_var, font=("Arial", self.font_size-1), width=200)
            field_widget.pack(side="left", fill="x", expand=True, padx=5, pady=0)
            
            # Ajouter une vérification de format pour les dates
            field_widget.bind("<FocusOut>", lambda e, f=field_var: self._validate_date_format(f))
        
        elif field in ["montant", "prix", "total", "montant_ht", "montant_ttc", "tva", "price", "amount"]:
            # Champs de type montant
            field_var = ctk.StringVar(value=str(value))
            field_widget = ctk.CTkEntry(field_frame, textvariable=field_var, font=("Arial", self.font_size-1), width=200)
            field_widget.pack(side="left", fill="x", expand=True, padx=5, pady=0)
            
            # Ajouter une vérification pour les montants
            field_widget.bind("<FocusOut>", lambda e, f=field_var: self._validate_amount_format(f))
        
        elif field in ["address", "description"] or len(str(value)) > 50:
            # Champs multilignes
            field_var = ctk.StringVar(value=str(value))
            field_widget = ctk.CTkTextbox(field_frame, font=("Arial", self.font_size-1), height=60, width=200)
            field_widget.insert("1.0", str(value))
            field_widget.pack(side="left", fill="x", expand=True, padx=5, pady=0)
            
            # Pour les textbox, on stocke directement le widget
            self.form_fields[field_id] = field_widget
        else:
            # Champs texte standards
            field_var = ctk.StringVar(value=str(value))
            field_widget = ctk.CTkEntry(field_frame, textvariable=field_var, font=("Arial", self.font_size-1), width=200)
            field_widget.pack(side="left", fill="x", expand=True, padx=5, pady=0)
        
        # Stocker la variable et le widget
        if field_var and field_id not in self.form_fields:
            self.form_fields[field_id] = field_var
        
        # Connecter les événements pour détecter les modifications
        if field_widget and not isinstance(field_widget, ctk.CTkTextbox):
            field_widget.bind("<KeyRelease>", self._on_field_changed)
        elif isinstance(field_widget, ctk.CTkTextbox):
            field_widget.bind("<<Modified>>", self._on_field_changed)
        
        return field_frame
    
    def _get_confidence_color(self, confidence: float) -> str:
        """
        Retourne la couleur correspondant au niveau de confiance
        
        Args:
            confidence (float): Score de confiance (0-1)
            
        Returns:
            str: Code couleur hexadécimal
        """
        if confidence >= 0.8:
            return self.colors["high_confidence"]
        elif confidence >= 0.6:
            return self.colors["medium_confidence"]
        else:
            return self.colors["low_confidence"]
    
    def _validate_date_format(self, var):
        """Valide le format d'une date"""
        value = var.get()
        if not value:
            return
        
        # Vérification simple pour l'instant
        import re
        if not re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$|^\d{4}-\d{2}-\d{2}$', value):
            var.set("")
            messagebox.showwarning("Format invalide", "Format de date invalide. Utilisez JJ/MM/AAAA ou AAAA-MM-JJ.")
    
    def _validate_amount_format(self, var):
        """Valide le format d'un montant"""
        value = var.get()
        if not value:
            return
        
        # Vérification simple pour l'instant
        import re
        if not re.match(r'^\d+(?:[,.]\d{1,2})?$', value):
            var.set("")
            messagebox.showwarning("Format invalide", "Format de montant invalide. Utilisez des chiffres avec éventuellement une virgule ou un point pour les décimales.")
    
    def _populate_client_list(self, clients: List[Tuple[Dict[str, Any], float]]):
        """
        Remplit la liste des clients avec les correspondances trouvées
        
        Args:
            clients (list): Liste de tuples (client, score)
        """
        # Vider la liste
        for item in self.client_list.get_children():
            self.client_list.delete(item)
        
        # Ajouter les clients
        for client, score in clients:
            # Formater le pourcentage de correspondance
            match_percent = f"{int(score * 100)}%"
            
            # Obtenir les données du client
            name = f"{client.get('first_name', '')} {client.get('last_name', '')}".strip()
            if not name:
                name = client.get('name', '')
            if not name:
                name = client.get('company', 'Client sans nom')
            
            email = client.get('email', '')
            phone = client.get('phone', '')
            
            # Ajouter à la liste
            self.client_list.insert("", "end", values=(name, email, phone, match_percent), tags=(str(score),))
            
            # Colorer selon le score
            if score >= 0.8:
                self.client_list.tag_configure(str(score), background="#E8F5E9")  # Vert clair
            elif score >= 0.6:
                self.client_list.tag_configure(str(score), background="#FFF8E1")  # Jaune clair
    
    def _get_form_data(self) -> Dict[str, Any]:
        """
        Récupère les données du formulaire
        
        Returns:
            dict: Données du formulaire
        """
        form_data = {}
        
        for field_id, field_var in self.form_fields.items():
            # Traiter les différents types de widgets
            if isinstance(field_var, ctk.CTkTextbox):
                value = field_var.get("1.0", "end-1c")
            else:
                value = field_var.get()
            
            # Déterminer les niveaux de hiérarchie
            parts = field_id.split('.')
            
            # Construire la structure de données
            current = form_data
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    # Vérifier si la partie suivante est un index numérique
                    next_part = parts[i+1] if i+1 < len(parts)-1 else parts[-1]
                    if next_part.isdigit():
                        current[part] = []
                    else:
                        current[part] = {}
                
                # Accéder à la partie courante
                if isinstance(current[part], dict):
                    current = current[part]
                elif isinstance(current[part], list):
                    # Si c'est une liste, créer l'élément s'il n'existe pas
                    index = int(parts[i+1])
                    while len(current[part]) <= index:
                        current[part].append({})
                    
                    current = current[part][index]
                    # Sauter la partie numérique qui a été traitée
                    i += 1
            
            # Ajouter la valeur
            current[parts[-1]] = value
        
        return form_data
    
    def _on_field_changed(self, event=None):
        """Appelé lorsqu'un champ est modifié"""
        self.data_modified = True
        self.validate_button.configure(state="normal")
        
        # Mettre à jour les boutons d'action
        if self.extracted_data:
            self.apply_button.configure(state="normal")
    
    def _on_search_changed(self, *args):
        """Appelé lorsque le texte de recherche change"""
        # Recherche automatique après un délai
        if hasattr(self, '_search_after_id'):
            self.dialog.after_cancel(self._search_after_id)
        
        self._search_after_id = self.dialog.after(500, self._search_clients)
    
    def _search_clients(self):
        """Recherche des clients correspondant au texte de recherche"""
        search_text = self.client_search_var.get()
        
        # Si la recherche est vide et que nous avons des données extraites,
        # afficher les correspondances basées sur les données extraites
        if not search_text and self.extracted_data:
            matches = self.analyzer.get_client_matches({"data": self.extracted_data}, self.clients_db)
            self._populate_client_list(matches)
            return
        
        # Sinon, rechercher par le texte
        matches = self.client_matcher.search_clients(search_text)
        self._populate_client_list([(client, score) for client, score in matches])
    
    def _on_client_select(self, event):
        """Appelé lorsqu'un client est sélectionné dans la liste"""
        selection = self.client_list.selection()
        if not selection:
            return
        
        # Récupérer les valeurs du client sélectionné
        item_id = selection[0]
        values = self.client_list.item(item_id, "values")
        
        # Trouver le client correspondant
        name = values[0]
        email = values[1]
        
        # Chercher le client dans la liste
        for client, _ in self.client_matcher.last_results:
            client_name = f"{client.get('first_name', '')} {client.get('last_name', '')}".strip()
            if not client_name:
                client_name = client.get('name', '')
            if not client_name:
                client_name = client.get('company', '')
            
            if client_name == name and client.get('email', '') == email:
                self.selected_client = client
                self.edit_client_button.configure(state="normal")
                
                # Mettre à jour les champs avec les données du client
                self._fill_fields_from_client(client)
                break
    
    def _fill_fields_from_client(self, client: Dict[str, Any]):
        """
        Remplit les champs du formulaire avec les données du client
        
        Args:
            client (dict): Données du client
        """
        # Mapping entre les champs du client et les champs du formulaire
        field_mappings = {
            "name": "personal_info.last_name",
            "first_name": "personal_info.first_name",
            "last_name": "personal_info.last_name",
            "email": "personal_info.email",
            "phone": "personal_info.phone",
            "address": "personal_info.address",
            "company": "professional_info.company",
            "position": "professional_info.position",
            "siret": "professional_info.siret",
            "vat_number": "professional_info.vat_number",
            "iban": "banking_info.iban",
            "bic": "banking_info.bic"
        }
        
        # Remplir les champs
        for client_field, form_field in field_mappings.items():
            if client_field in client and form_field in self.form_fields:
                value = client[client_field]
                field_var = self.form_fields[form_field]
                
                if isinstance(field_var, ctk.CTkTextbox):
                    field_var.delete("1.0", "end")
                    if value:
                        field_var.insert("1.0", str(value))
                else:
                    field_var.set(value if value is not None else "")
    
    def _create_new_client(self):
        """Crée un nouveau client à partir des données du formulaire"""
        # Récupérer les données du formulaire
        form_data = self._get_form_data()
        
        # Créer un nouveau client à partir des données
        new_client = {}
        
        # Extraire les informations personnelles
        personal_info = form_data.get("personal_info", {})
        if personal_info:
            new_client["first_name"] = personal_info.get("first_name", "")
            new_client["last_name"] = personal_info.get("last_name", "")
            new_client["email"] = personal_info.get("email", "")
            new_client["phone"] = personal_info.get("phone", "")
            new_client["address"] = personal_info.get("address", "")
            
            # Nom complet
            if new_client["first_name"] or new_client["last_name"]:
                new_client["name"] = f"{new_client['first_name']} {new_client['last_name']}".strip()
        
        # Extraire les informations professionnelles
        professional_info = form_data.get("professional_info", {})
        if professional_info:
            new_client["company"] = professional_info.get("company", "")
            new_client["position"] = professional_info.get("position", "")
            new_client["siret"] = professional_info.get("siret", "")
            new_client["vat_number"] = professional_info.get("vat_number", "")
        
        # Extraire les informations bancaires
        banking_info = form_data.get("banking_info", {})
        if banking_info:
            new_client["iban"] = banking_info.get("iban", "")
            new_client["bic"] = banking_info.get("bic", "")
        
        # Vérifier que le client a au moins un identifiant (nom, email ou téléphone)
        if not (new_client.get("name") or new_client.get("email") or new_client.get("phone")):
            messagebox.showwarning("Données insuffisantes", "Veuillez fournir au moins un nom, un email ou un numéro de téléphone.")
            return
        
        # Appeler la méthode de création du client (à implémenter dans l'application principale)
        if hasattr(self.parent, 'create_client'):
            client_id = self.parent.create_client(new_client)
            
            if client_id:
                # Ajouter l'ID au client
                new_client["id"] = client_id
                self.selected_client = new_client
                
                # Mettre à jour la liste des clients
                self.clients_db.append(new_client)
                self._search_clients()
                
                messagebox.showinfo("Client créé", "Le nouveau client a été créé avec succès.")
        else:
            # Méthode de démonstration si l'application principale n'a pas de méthode create_client
            # Générer un ID factice
            import random
            import string
            client_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # Ajouter l'ID au client
            new_client["id"] = client_id
            self.selected_client = new_client
            
            # Mettre à jour la liste des clients
            self.clients_db.append(new_client)
            self._search_clients()
            
            messagebox.showinfo("Client créé", "Le nouveau client a été créé avec succès. (Mode démo)")
    
    def _edit_client(self):
        """Modifie le client sélectionné avec les données du formulaire"""
        if not self.selected_client:
            return
        
        # Récupérer les données du formulaire
        form_data = self._get_form_data()
        
        # Mise à jour du client
        updated_client = self.selected_client.copy()
        
        # Extraire les informations personnelles
        personal_info = form_data.get("personal_info", {})
        if personal_info:
            updated_client["first_name"] = personal_info.get("first_name", updated_client.get("first_name", ""))
            updated_client["last_name"] = personal_info.get("last_name", updated_client.get("last_name", ""))
            updated_client["email"] = personal_info.get("email", updated_client.get("email", ""))
            updated_client["phone"] = personal_info.get("phone", updated_client.get("phone", ""))
            updated_client["address"] = personal_info.get("address", updated_client.get("address", ""))
            
            # Nom complet
            if updated_client["first_name"] or updated_client["last_name"]:
                updated_client["name"] = f"{updated_client['first_name']} {updated_client['last_name']}".strip()
        
        # Extraire les informations professionnelles
        professional_info = form_data.get("professional_info", {})
        if professional_info:
            updated_client["company"] = professional_info.get("company", updated_client.get("company", ""))
            updated_client["position"] = professional_info.get("position", updated_client.get("position", ""))
            updated_client["siret"] = professional_info.get("siret", updated_client.get("siret", ""))
            updated_client["vat_number"] = professional_info.get("vat_number", updated_client.get("vat_number", ""))
        
        # Extraire les informations bancaires
        banking_info = form_data.get("banking_info", {})
        if banking_info:
            updated_client["iban"] = banking_info.get("iban", updated_client.get("iban", ""))
            updated_client["bic"] = banking_info.get("bic", updated_client.get("bic", ""))
        
        # Appeler la méthode de mise à jour du client (à implémenter dans l'application principale)
        if hasattr(self.parent, 'update_client'):
            success = self.parent.update_client(updated_client)
            
            if success:
                # Mettre à jour le client sélectionné
                self.selected_client = updated_client
                
                # Mettre à jour la liste des clients
                for i, client in enumerate(self.clients_db):
                    if client.get("id") == updated_client.get("id"):
                        self.clients_db[i] = updated_client
                        break
                
                self._search_clients()
                
                messagebox.showinfo("Client mis à jour", "Le client a été mis à jour avec succès.")
        else:
            # Méthode de démonstration si l'application principale n'a pas de méthode update_client
            # Mettre à jour le client sélectionné
            self.selected_client = updated_client
            
            # Mettre à jour la liste des clients
            for i, client in enumerate(self.clients_db):
                if client.get("id") == updated_client.get("id"):
                    self.clients_db[i] = updated_client
                    break
            
            self._search_clients()
            
            messagebox.showinfo("Client mis à jour", "Le client a été mis à jour avec succès. (Mode démo)")
    
    def _on_validate(self):
        """Valide les données extraites et les retourne"""
        # Récupérer les données du formulaire
        form_data = self._get_form_data()
        
        # Informations à retourner
        result = {
            "data": form_data,
            "document_path": self.current_document_path,
            "document_type": self.doc_type_var.get().replace("Type : ", ""),
            "client": self.selected_client
        }
        
        # Cacher la boîte de dialogue
        self.dialog.withdraw()
        
        # Appeler le callback de validation
        if hasattr(self, '_validate_callback') and callable(self._validate_callback):
            self._validate_callback(result)
        
        # Fermer la boîte de dialogue
        self._cleanup()
    
    def _on_apply(self):
        """Applique les modifications sans fermer la boîte de dialogue"""
        # Récupérer les données du formulaire
        form_data = self._get_form_data()
        
        # Informations à retourner
        result = {
            "data": form_data,
            "document_path": self.current_document_path,
            "document_type": self.doc_type_var.get().replace("Type : ", ""),
            "client": self.selected_client
        }
        
        # Appeler le callback d'application
        if hasattr(self, '_apply_callback') and callable(self._apply_callback):
            self._apply_callback(result)
        
        # Indiquer que les modifications ont été appliquées
        self.data_modified = False
        messagebox.showinfo("Modifications appliquées", "Les modifications ont été appliquées avec succès.")
    
    def _on_close(self):
        """Ferme la boîte de dialogue"""
        # Si des modifications ont été effectuées, demander confirmation
        if self.data_modified:
            if not messagebox.askyesno("Modifications non sauvegardées", 
                                      "Des modifications n'ont pas été sauvegardées. Êtes-vous sûr de vouloir fermer?"):
                return
        
        # Cacher et nettoyer
        self.dialog.withdraw()
        self._cleanup()
    
    def _cleanup(self):
        """Nettoie les ressources"""
        # Réinitialiser les données
        self.extraction_results = {}
        self.extracted_data = {}
        self.confidence_scores = {}
        self.form_fields = {}
        self.selected_client = None
        self.current_document_path = None
        self.data_modified = False
        
        # Réinitialiser l'interface
        self.doc_path_var.set("Aucun document sélectionné")
        self.doc_type_var.set("Type : -")
        self.client_search_var.set("")
        
        # Vider la liste des clients
        for item in self.client_list.get_children():
            self.client_list.delete(item)
        
        # Désactiver les boutons
        self.edit_client_button.configure(state="disabled")
        self.apply_button.configure(state="disabled")
        self.validate_button.configure(state="disabled")
    
    def show(self, document_path: str, validate_callback: Callable = None, apply_callback: Callable = None):
        """
        Affiche la boîte de dialogue avec les données extraites du document
        
        Args:
            document_path (str): Chemin vers le document à analyser
            validate_callback (callable, optional): Fonction à appeler lorsque les données sont validées
            apply_callback (callable, optional): Fonction à appeler lorsque les données sont appliquées
        """
        # Enregistrer les callbacks
        self._validate_callback = validate_callback
        self._apply_callback = apply_callback
        
        # Réinitialiser l'état
        self._cleanup()
        
        # Enregistrer le chemin du document
        self.current_document_path = document_path
        
        # Mettre à jour l'affichage
        self.doc_path_var.set(os.path.basename(document_path))
        
        # Analyser le document
        try:
            extraction_results = self.analyzer.analyze_document(document_path)
            
            if "error" in extraction_results:
                messagebox.showerror("Erreur d'analyse", f"Erreur lors de l'analyse du document : {extraction_results['error']}")
                return
            
            # Stocker les résultats
            self.extraction_results = extraction_results
            self.extracted_data = extraction_results.get("data", {})
            self.confidence_scores = extraction_results.get("confidence", {})
            
            # Mettre à jour l'affichage du type de document
            doc_type = extraction_results.get("metadata", {}).get("document_type", "unknown")
            self.doc_type_var.set(f"Type : {doc_type}")
            
            # Créer les widgets pour les champs extraits
            self._create_field_widgets()
            
            # Rechercher des clients correspondants
            self._search_clients()
            
            # Activer le bouton de validation
            self.validate_button.configure(state="normal")
            self.apply_button.configure(state="normal")
            
            # Afficher la boîte de dialogue
            self.dialog.deiconify()
            self.dialog.lift()
            
            # Focus sur le premier champ
            if self.fields_frame.winfo_children():
                for widget in self.fields_frame.winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkEntry):
                                child.focus_set()
                                break
                        break
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du document : {e}")
            messagebox.showerror("Erreur d'analyse", f"Erreur lors de l'analyse du document : {str(e)}")


class SimpleAutoFillDialog:
    """
    Version simplifiée de la boîte de dialogue de remplissage automatique
    Pour les cas d'utilisation simples ou les tests rapides
    """
    
    def __init__(self, parent, analyzer: DocumentAnalyzer = None):
        """
        Initialise la boîte de dialogue simplifiée
        
        Args:
            parent: Widget parent (fenêtre ou cadre)
            analyzer (DocumentAnalyzer, optional): Analyseur de documents à utiliser
        """
        self.parent = parent
        self.config = get_config()
        
        # Initialiser l'analyseur
        self.analyzer = analyzer or DocumentAnalyzer(self.config.get_all())
    
    def show(self, document_path: str, callback: Callable = None):
        """
        Analyse un document et retourne directement les résultats
        
        Args:
            document_path (str): Chemin vers le document à analyser
            callback (callable, optional): Fonction à appeler avec les résultats
        """
        try:
            # Analyser le document
            extraction_results = self.analyzer.analyze_document(document_path)
            
            if "error" in extraction_results:
                messagebox.showerror("Erreur d'analyse", f"Erreur lors de l'analyse du document : {extraction_results['error']}")
                return
            
            # Informations à retourner
            result = {
                "data": extraction_results.get("data", {}),
                "document_path": document_path,
                "document_type": extraction_results.get("metadata", {}).get("document_type", "unknown"),
                "client": None
            }
            
            # Appeler le callback
            if callback and callable(callback):
                callback(result)
            
            return result
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du document : {e}")
            messagebox.showerror("Erreur d'analyse", f"Erreur lors de l'analyse du document : {str(e)}")
            return None


# Fonction pour utilisation directe
def show_auto_fill_dialog(parent, document_path: str, 
                        clients_db: List[Dict[str, Any]] = None,
                        validate_callback: Callable = None, 
                        apply_callback: Callable = None):
    """
    Affiche la boîte de dialogue de remplissage automatique pour un document
    
    Args:
        parent: Widget parent (fenêtre ou cadre)
        document_path (str): Chemin vers le document à analyser
        clients_db (list, optional): Base de données des clients
        validate_callback (callable, optional): Fonction à appeler lorsque les données sont validées
        apply_callback (callable, optional): Fonction à appeler lorsque les données sont appliquées
        
    Returns:
        AutoFillDialog: Instance de la boîte de dialogue
    """
    dialog = AutoFillDialog(parent, clients_db=clients_db)
    dialog.show(document_path, validate_callback, apply_callback)
    return dialog