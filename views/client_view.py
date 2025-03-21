"""
Vue de gestion des clients pour l'application Vynal Docs Automator
Version améliorée avec une interface moderne et de nouvelles fonctionnalités
"""

import logging
import threading
import queue
import time
import customtkinter as ctk
import tkinter.messagebox as messagebox
import csv
import pandas as pd
import os
from PIL import Image, ImageTk
from tkinter import filedialog
from datetime import datetime
import re

logger = logging.getLogger("VynalDocsAutomator.ClientView")

# Constantes de style pour l'interface
# Couleurs primaires
BLEU_PRIMAIRE = "#3498db"
BLEU_FONCE = "#2980b9"

# Couleurs d'action
VERT = "#2ecc71"
VERT_FONCE = "#27ae60"
ROUGE = "#e74c3c"
ROUGE_FONCE = "#c0392b"
ORANGE = "#f39c12"
ORANGE_FONCE = "#e67e22"
GRIS_FONCE_ACTION = "#34495e"
GRIS_TRES_FONCE = "#2c3e50"

# Couleurs neutres
GRIS = "#95a5a6"
GRIS_FONCE = "#7f8c8d"

# Dimensions des boutons
# Boutons standards
BOUTON_STANDARD_HAUTEUR = 35
BOUTON_STANDARD_LARGEUR = 120
BOUTON_STANDARD_RAYON = 8

# Boutons d'action (plus grands)
BOUTON_ACTION_HAUTEUR = 40
BOUTON_ACTION_LARGEUR = 140
BOUTON_ACTION_RAYON = 8

# Petits boutons (pour les lignes du tableau)
BOUTON_PETIT_HAUTEUR = 24
BOUTON_PETIT_LARGEUR = 60
BOUTON_PETIT_RAYON = 5

class ClientTable:
    """
    Composant de tableau pour afficher les clients
    Avec optimisations de performance et UI améliorée
    """
    
    def __init__(self, parent, headers):
        """
        Initialise le tableau
        
        Args:
            parent: Widget parent
            headers: Liste des entêtes de colonnes
        """
        self.parent = parent
        self.headers = headers
        
        # Cadre principal du tableau avec coin arrondis
        self.frame = ctk.CTkFrame(parent, corner_radius=10)
        
        # Cadre pour les en-têtes du tableau avec style moderne
        self.header_frame = ctk.CTkFrame(self.frame, fg_color=("#e0e0e0", "#2c3e50"), corner_radius=8)
        self.header_frame.pack(fill=ctk.X, padx=5, pady=(5, 0))
        
        # Définir des poids pour chaque colonne (pour un alignement uniforme)
        self.column_weights = [2, 2, 3, 2, 1]  # Nom, Entreprise, Email, Téléphone, Actions
        for i, header in enumerate(headers):
            weight = self.column_weights[i] if i < len(self.column_weights) else 1
            self.header_frame.columnconfigure(i, weight=weight)
        
        # Ajouter les en-têtes dans la grille avec style amélioré
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                self.header_frame,
                text=header,
                font=ctk.CTkFont(weight="bold", size=13),
                anchor="w",
                text_color=("black", "white")
            ).grid(row=0, column=i, sticky="nsew", padx=8, pady=8)
        
        # Cadre pour le contenu du tableau (avec défilement) et style amélioré
        self.content_frame = ctk.CTkScrollableFrame(self.frame, corner_radius=5)
        self.content_frame.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        
        # Configurer les colonnes dans le contenu du tableau avec les mêmes poids
        for i in range(len(headers)):
            weight = self.column_weights[i] if i < len(self.column_weights) else 1
            self.content_frame.columnconfigure(i, weight=weight)
        
        # Liste pour stocker les lignes (chaque ligne est un tuple : (row_frame, widgets))
        self.rows = []
        
        # Limite de caractères par colonne avant retour à la ligne (pour le texte)
        self.char_limits = [20, 20, 30, 30, None]  # Pour les colonnes; pour Actions, aucun limite
        
        # Paramètres de performance
        self.max_rows_per_batch = 50  # Nombre maximum de lignes rendues par lot
        self.rendering_queue = queue.Queue()  # File d'attente pour le rendu des lignes
        self.is_rendering = False  # Indicateur de rendu en cours
        
        # Animation de chargement
        self.loading_label = ctk.CTkLabel(
            self.frame, 
            text="Chargement des données...",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=("#3498db", "#3498db")
        )
        
        # Indicateur de sélection
        self.selection_mode = False
        self.selected_rows_ids = set()
        
        # Ajout d'un compteur de lignes sélectionnées
        self.selection_indicator = ctk.CTkLabel(
            self.frame,
            text="0 ligne(s) sélectionnée(s)",
            font=ctk.CTkFont(size=12),
            text_color=("#555", "#aaa")
        )
        
    def show_loading(self, show=True):
        """Affiche ou masque l'animation de chargement"""
        if show:
            self.loading_label.pack(pady=10)
        else:
            self.loading_label.pack_forget()
            
    def toggle_selection_mode(self, enable=None):
        """Active/désactive le mode de sélection multiple"""
        if enable is not None:
            self.selection_mode = enable
        else:
            self.selection_mode = not self.selection_mode
            
        # Afficher/masquer l'indicateur de sélection
        if self.selection_mode:
            self.selection_indicator.pack(side=ctk.BOTTOM, pady=5)
        else:
            self.selection_indicator.pack_forget()
            self.selected_rows_ids.clear()
            self.update_selected_count()
            
        # Mettre à jour les lignes existantes pour ajouter/supprimer les cases à cocher
        self.refresh_selection_checkboxes()
            
    def refresh_selection_checkboxes(self):
        """Met à jour les cases à cocher de sélection pour toutes les lignes"""
        # À implémenter si nécessaire pour mettre à jour l'interface
        pass
            
    def update_selected_count(self):
        """Met à jour le compteur de lignes sélectionnées"""
        count = len(self.selected_rows_ids)
        self.selection_indicator.configure(
            text=f"{count} ligne(s) sélectionnée(s)"
        )
        
    def add_row(self, data, row_id=None):
        """
        Ajoute une ligne au tableau
        
        Args:
            data: Liste des données de la ligne. Si une donnée est une fonction,
                  elle sera appelée en lui passant le parent de la cellule.
            row_id: Identifiant unique de la ligne (pour la sélection)
        
        Returns:
            list: Liste des widgets de la ligne
        """
        row_widgets = []
        row_index = len(self.rows)
        
        # Cadre pour la ligne, avec fond alterné et style amélioré
        bg_color = ("#f8f9fa", "#1e272e") if row_index % 2 == 0 else ("#ffffff", "#2d3436")
        row_frame = ctk.CTkFrame(self.content_frame, fg_color=bg_color, corner_radius=0)
        row_frame.pack(fill=ctk.X, padx=0, pady=1)
        
        # Configurer les colonnes du row_frame avec les mêmes poids
        for i in range(len(self.headers)):
            weight = self.column_weights[i] if i < len(self.column_weights) else 1
            row_frame.columnconfigure(i, weight=weight)
        
        # Ajouter chaque cellule dans la ligne
        for i, cell_data in enumerate(data):
            if callable(cell_data):
                # Créer le widget à partir de la fonction
                widget = cell_data(row_frame)
                widget.grid(row=0, column=i, sticky="nsew", padx=5, pady=6)
                row_widgets.append(widget)
            elif isinstance(cell_data, ctk.CTkBaseClass):
                cell_data.grid(row=0, column=i, sticky="nsew", padx=5, pady=6)
                row_widgets.append(cell_data)
            else:
                # Si c'est du texte, on peut formater pour retour à la ligne
                text = str(cell_data)
                char_limit = self.char_limits[i] if i < len(self.char_limits) else None
                if char_limit and len(text) > char_limit:
                    formatted_text = "\n".join(text[j:j+char_limit] for j in range(0, len(text), char_limit))
                else:
                    formatted_text = text
                cell = ctk.CTkLabel(row_frame, text=formatted_text, anchor="w", justify="left", wraplength=120)
                cell.grid(row=0, column=i, sticky="nsew", padx=8, pady=6)
                row_widgets.append(cell)
        
        # Ajouter un effet de survol pour rendre le tableau plus interactif
        def on_row_enter(event):
            row_frame.configure(fg_color=("#e0f7fa", "#34495e"))
            
        def on_row_leave(event):
            current_bg = ("#f8f9fa", "#1e272e") if row_index % 2 == 0 else ("#ffffff", "#2d3436")
            row_frame.configure(fg_color=current_bg)
            
        row_frame.bind("<Enter>", on_row_enter)
        row_frame.bind("<Leave>", on_row_leave)
        
        # Stocker la ligne avec son ID si fourni
        row_data = {"frame": row_frame, "widgets": row_widgets, "id": row_id}
        self.rows.append(row_data)
        
        return row_widgets
    
    def add_rows_async(self, data_list):
        """
        Ajoute plusieurs lignes au tableau de manière asynchrone
        
        Args:
            data_list: Liste de données pour chaque ligne
        """
        # Afficher l'indicateur de chargement
        self.show_loading(True)
        
        # Vider la file d'attente
        while not self.rendering_queue.empty():
            self.rendering_queue.get()
        
        # Ajouter les données à la file d'attente
        for data in data_list:
            self.rendering_queue.put(data)
        
        # Commencer le rendu si pas déjà en cours
        if not self.is_rendering:
            self._process_rendering_queue()
    
    def _process_rendering_queue(self):
        """
        Traite la file d'attente de rendu par lots
        """
        self.is_rendering = True
        
        # Traiter un lot de lignes
        batch_size = min(self.max_rows_per_batch, self.rendering_queue.qsize())
        if batch_size > 0:
            # Créer et ajouter les lignes du lot
            for _ in range(batch_size):
                if not self.rendering_queue.empty():
                    data = self.rendering_queue.get()
                    row_id = None
                    
                    # Vérifier si on a des données avec ID
                    if isinstance(data, tuple) and len(data) == 2:
                        data, row_id = data
                        
                    self.add_row(data, row_id)
            
            # Si des lignes restent à traiter, programmer le prochain lot
            if not self.rendering_queue.empty():
                self.parent.after(10, self._process_rendering_queue)
            else:
                self.is_rendering = False
                self.show_loading(False)  # Masquer l'indicateur de chargement
        else:
            self.is_rendering = False
            self.show_loading(False)  # Masquer l'indicateur de chargement
    
    def clear(self):
        """
        Efface toutes les lignes du tableau
        """
        for row_data in self.rows:
            row_data["frame"].destroy()
        self.rows = []
        
        # Vider la file d'attente de rendu
        while not self.rendering_queue.empty():
            self.rendering_queue.get()
        
        self.is_rendering = False
        self.selected_rows_ids.clear()
        self.update_selected_count()
        
    def get_selected_ids(self):
        """Retourne les IDs des lignes sélectionnées"""
        return list(self.selected_rows_ids)


class ClientView:
    """
    Vue de gestion des clients avec interface moderne
    Permet de visualiser, ajouter, modifier et supprimer des clients
    """
    
    def __init__(self, parent, app_model):
        """
        Initialise la vue de gestion des clients
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        
        # Cadre principal de la vue avec coins arrondis
        self.frame = ctk.CTkFrame(parent, corner_radius=15, fg_color=("gray95", "gray10"))
        
        # Variables pour le formulaire
        self.current_client_id = None
        self.client_data = {}
        
        # Paramètres d'optimisation
        self.debounce_delay = 300  # Délai de debounce en millisecondes
        self.search_timer = None   # Timer pour la recherche
        self.loading_task = None   # Tâche de chargement en cours
        self.clients_cache = []    # Cache des clients
        self.is_loading = False    # Indicateur de chargement
        
        # Métriques de performance
        self.performance_metrics = {
            'load_time': 0,
            'filter_time': 0,
            'render_time': 0,
            'client_count': 0
        }
        
        # Historique des vues
        self.view_history = []
        self.current_view = "list"  # Vue actuelle ("list" ou "detail")
        
        # Créer les composants de l'interface
        self.create_widgets()
        
        # Charger les icônes (dans un thread pour ne pas bloquer l'interface)
        self.load_icons_thread = threading.Thread(target=self.load_icons, daemon=True)
        self.load_icons_thread.start()
        
        logger.info("ClientView améliorée initialisée")
    
    def load_icons(self):
        """Charge les icônes pour l'interface"""
        # Utiliser des caractères emoji par défaut
        self.icons = {
            "add": "➕",
            "import": "📥",
            "export": "📤",
            "search": "🔍",
            "edit": "✏️",
            "delete": "🗑️",
            "back": "⬅️",
            "refresh": "🔄",
            "mail": "📧",
            "call": "📞",
            "filter": "🔍",
            "sort": "🔢",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        
        # Essayer de charger les icônes depuis un dossier 'assets' si disponible
        try:
            asset_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons")
            if os.path.exists(asset_dir):
                icon_files = {
                    "add": "add.png",
                    "import": "import.png",
                    "export": "export.png",
                    "search": "search.png",
                    "edit": "edit.png",
                    "delete": "delete.png",
                    "back": "back.png",
                    "refresh": "refresh.png",
                    "mail": "mail.png",
                    "call": "call.png",
                    "filter": "filter.png",
                    "sort": "sort.png"
                }
                
                # Charger uniquement les icônes qui existent
                for icon_name, icon_file in icon_files.items():
                    file_path = os.path.join(asset_dir, icon_file)
                    if os.path.exists(file_path):
                        try:
                            img = Image.open(file_path)
                            img = img.resize((16, 16), Image.LANCZOS)
                            photo = ImageTk.PhotoImage(img)
                            self.icons[icon_name] = photo
                        except Exception as e:
                            logger.warning(f"Impossible de charger l'icône {icon_name}: {e}")
        except Exception as e:
            logger.warning(f"Erreur lors du chargement des icônes: {e}")
    
    def create_widgets(self):
        """
        Crée les widgets de la vue avec un design moderne
        """
        # Créer les différentes vues
        self._create_list_view()
        self._create_detail_view()
        
        # Par défaut, afficher la vue liste
        self.detail_frame.pack_forget()
    
    def _create_list_view(self):
        """Crée la vue de liste des clients"""
        # Barre d'outils avec style moderne
        self.toolbar = ctk.CTkFrame(self.frame, corner_radius=10, fg_color=("gray90", "gray15"))
        self.toolbar.pack(fill=ctk.X, padx=15, pady=15)
        
        # Titre de la section
        title_container = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        title_container.pack(side=ctk.LEFT, fill=ctk.Y, padx=(10, 20))
        
        title_label = ctk.CTkLabel(
            title_container,
            text="Liste des clients",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(side=ctk.LEFT, pady=10)
        
        # Compteur de clients
        self.client_counter = ctk.CTkLabel(
            title_container,
            text="0 client(s)",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        self.client_counter.pack(side=ctk.LEFT, padx=(10, 0), pady=10)
        
        # Conteneur pour les boutons de gauche
        left_buttons = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        left_buttons.pack(side=ctk.LEFT, padx=10)
        
        # Bouton Nouveau client avec style moderne
        self.new_client_btn = ctk.CTkButton(
            left_buttons,
            text="Nouveau client",
            command=self.show_client_form,
            fg_color="#3498db",
            hover_color="#2980b9",
            corner_radius=8,
            border_width=0,
            font=ctk.CTkFont(weight="bold")
        )
        self.new_client_btn.pack(side=ctk.LEFT, padx=5)
        
        # Frame pour les boutons d'importation/exportation
        import_export_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        import_export_frame.pack(side=ctk.LEFT, padx=5)
        
        # Boutons Importer/Exporter avec style moderne
        self.import_btn = ctk.CTkButton(
            import_export_frame,
            text="Importer",
            command=self.import_clients,
            fg_color="#3498db",
            hover_color="#2980b9",
            width=100,
            corner_radius=8
        )
        self.import_btn.pack(side=ctk.LEFT, padx=5)
        
        self.export_btn = ctk.CTkButton(
            import_export_frame,
            text="Exporter",
            command=self.export_clients,
            fg_color="#3498db",
            hover_color="#2980b9",
            width=100,
            corner_radius=8
        )
        self.export_btn.pack(side=ctk.LEFT, padx=5)
        
        # Indicateur de chargement avec animation améliorée
        self.loading_label = ctk.CTkLabel(
            self.toolbar,
            text="Chargement...",
            text_color="#3498db",
            font=ctk.CTkFont(size=12, weight="bold", slant="italic")
        )
        # Ne pas l'afficher au démarrage
        
        # Zone de recherche améliorée
        self.search_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.search_frame.pack(side=ctk.RIGHT, padx=10)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.debounced_filter_clients())
        
        search_bg = ctk.CTkFrame(self.search_frame, corner_radius=8, fg_color=("white", "gray25"))
        search_bg.pack(side=ctk.LEFT, padx=(5, 0), pady=5)
        
        # Icône de recherche
        search_icon = ctk.CTkLabel(
            search_bg,
            text="🔍",
            width=15,
            font=ctk.CTkFont(size=14)
        )
        search_icon.pack(side=ctk.LEFT, padx=(8, 0))
        
        # Champ de recherche
        self.search_entry = ctk.CTkEntry(
            search_bg,
            placeholder_text="Rechercher un client...",
            width=220,
            border_width=0,
            fg_color="transparent",
            textvariable=self.search_var
        )
        self.search_entry.pack(side=ctk.LEFT, padx=(0, 5), pady=5, fill=ctk.BOTH)
        
        # Bouton pour effacer la recherche
        self.clear_search_btn = ctk.CTkButton(
            search_bg,
            text="✕",
            width=20,
            height=20,
            corner_radius=10,
            fg_color="transparent",
            hover_color=("gray80", "gray35"),
            command=self._clear_search
        )
        self.clear_search_btn.pack(side=ctk.LEFT, padx=(0, 5))
        
        # Cadre pour la liste des clients avec ombre
        self.list_frame = ctk.CTkFrame(self.frame, corner_radius=10, fg_color=("white", "gray17"), border_width=0)
        self.list_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Barre de filtres
        self.filter_bar = ctk.CTkFrame(self.list_frame, height=40, corner_radius=8, fg_color=("gray95", "gray20"))
        self.filter_bar.pack(fill=ctk.X, padx=10, pady=10)
        
        # Ajouter des boutons de filtre
        filters = ["Tous", "Clients actifs", "Prospects", "Archivés"]
        self.current_filter = ctk.StringVar(value="Tous")
        
        for i, filter_name in enumerate(filters):
            filter_btn = ctk.CTkRadioButton(
                self.filter_bar,
                text=filter_name,
                variable=self.current_filter,
                value=filter_name,
                command=self.apply_filter,
                border_width_checked=6,
                corner_radius=5
            )
            filter_btn.pack(side=ctk.LEFT, padx=15, pady=5)
        
        # Boutons de tri
        sort_frame = ctk.CTkFrame(self.filter_bar, fg_color="transparent")
        sort_frame.pack(side=ctk.RIGHT, padx=10)
        
        sort_label = ctk.CTkLabel(sort_frame, text="Trier par:")
        sort_label.pack(side=ctk.LEFT, padx=(0, 5))
        
        # Menu déroulant pour le tri
        sort_options = ["Nom", "Entreprise", "Date d'ajout", "Dernier contact"]
        self.sort_var = ctk.StringVar(value="Nom")
        
        sort_menu = ctk.CTkOptionMenu(
            sort_frame,
            values=sort_options,
            variable=self.sort_var,
            command=self.apply_sort,
            width=120,
            corner_radius=5
        )
        sort_menu.pack(side=ctk.LEFT, padx=5)
        
        # Tableau des clients amélioré
        self.clients_table = ClientTable(self.list_frame, ["Nom", "Entreprise", "Email", "Téléphone", "Actions"])
        self.clients_table.frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Message affiché s'il n'y a aucun client, avec style amélioré
        self.no_clients_label = ctk.CTkLabel(
            self.list_frame,
            text="Aucun client disponible. Ajoutez des clients pour commencer.",
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color=("gray50", "gray70")
        )
        self.no_clients_label.pack(pady=40)
        
        # Barre d'état en bas
        self.status_bar = ctk.CTkFrame(self.frame, height=25, fg_color=("gray85", "gray20"), corner_radius=0)
        self.status_bar.pack(side=ctk.BOTTOM, fill=ctk.X)
        
        # Informations sur les dernières actions
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Prêt",
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.status_label.pack(side=ctk.LEFT, padx=10, pady=2)
        
        # Métriques de performance
        self.metrics_label = ctk.CTkLabel(
            self.status_bar,
            text="",
            font=ctk.CTkFont(size=11),
            anchor="e"
        )
        self.metrics_label.pack(side=ctk.RIGHT, padx=10, pady=2)
    
    def _create_detail_view(self):
        """Crée la vue détaillée d'un client"""
        # Cadre pour la vue détaillée
        self.detail_frame = ctk.CTkFrame(self.frame, corner_radius=10)
        
        # Barre d'outils de la vue détaillée
        self.detail_toolbar = ctk.CTkFrame(self.detail_frame, corner_radius=10, fg_color=("gray90", "gray15"))
        self.detail_toolbar.pack(fill=ctk.X, padx=15, pady=15)
        
        # Bouton retour
        self.back_btn = ctk.CTkButton(
            self.detail_toolbar,
            text="Retour à la liste",
            command=self.show_list_view,
            corner_radius=8,
            fg_color="#3498db",
            hover_color="#2980b9"
        )
        self.back_btn.pack(side=ctk.LEFT, padx=10)
        
        # Titre du client
        self.detail_title = ctk.CTkLabel(
            self.detail_toolbar,
            text="Détails du client",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.detail_title.pack(side=ctk.LEFT, padx=20, pady=10)
        
        # Conteneur principal pour les détails
        self.detail_content = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        self.detail_content.pack(fill=ctk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Colonnes pour les informations et les actions
        cols_frame = ctk.CTkFrame(self.detail_content, fg_color="transparent")
        cols_frame.pack(fill=ctk.BOTH, expand=True, pady=10)
        
        # Colonne d'informations (2/3 de l'espace)
        info_col = ctk.CTkFrame(cols_frame, fg_color=("white", "gray17"), corner_radius=10)
        info_col.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True, padx=(0, 5))
        
        # En-tête des informations
        info_header = ctk.CTkFrame(info_col, fg_color=("#e0e0e0", "#2c3e50"), corner_radius=8)
        info_header.pack(fill=ctk.X, padx=10, pady=10)
        
        ctk.CTkLabel(
            info_header,
            text="Informations du client",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("black", "white")
        ).pack(pady=10)
        
        # Contenu des informations client
        self.info_content = ctk.CTkScrollableFrame(info_col, fg_color="transparent")
        self.info_content.pack(fill=ctk.BOTH, expand=True, padx=15, pady=15)
        
        # Colonne d'actions (1/3 de l'espace)
        action_col = ctk.CTkFrame(cols_frame, fg_color=("white", "gray17"), corner_radius=10, width=300)
        action_col.pack(side=ctk.RIGHT, fill=ctk.BOTH, padx=(5, 0))
        action_col.pack_propagate(False)
        
        # En-tête des actions
        action_header = ctk.CTkFrame(action_col, fg_color=("#e0e0e0", "#2c3e50"), corner_radius=8)
        action_header.pack(fill=ctk.X, padx=10, pady=10)
        
        ctk.CTkLabel(
            action_header,
            text="Actions",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("black", "white")
        ).pack(pady=10)
        
        # Contenu des actions
        self.action_content = ctk.CTkFrame(action_col, fg_color="transparent")
        self.action_content.pack(fill=ctk.BOTH, expand=True, padx=15, pady=15)
        
        # Boutons d'action
        self.create_action_buttons()
    
    def create_action_buttons(self):
        """Crée les boutons d'action pour la vue détaillée"""
        # Bouton Modifier
        self.edit_btn = ctk.CTkButton(
            self.action_content,
            text="Modifier",
            command=lambda: self.edit_client(self.current_client_id),
            fg_color=BLEU_PRIMAIRE,
            hover_color=BLEU_FONCE,
            width=BOUTON_ACTION_LARGEUR,
            height=BOUTON_ACTION_HAUTEUR,
            corner_radius=BOUTON_ACTION_RAYON
        )
        self.edit_btn.pack(fill=ctk.X, pady=5)
        
        # Bouton Supprimer
        self.delete_btn = ctk.CTkButton(
            self.action_content,
            text="Supprimer",
            command=lambda: self.confirm_delete_client(self.current_client_id),
            fg_color=ROUGE,
            hover_color=ROUGE_FONCE,
            width=BOUTON_ACTION_LARGEUR,
            height=BOUTON_ACTION_HAUTEUR,
            corner_radius=BOUTON_ACTION_RAYON
        )
        self.delete_btn.pack(fill=ctk.X, pady=5)
        
        # Bouton Envoyer un email
        self.email_btn = ctk.CTkButton(
            self.action_content,
            text="Envoyer un email",
            command=self.send_email_to_client,
            fg_color=VERT,
            hover_color=VERT_FONCE,
            width=BOUTON_ACTION_LARGEUR,
            height=BOUTON_ACTION_HAUTEUR,
            corner_radius=BOUTON_ACTION_RAYON
        )
        self.email_btn.pack(fill=ctk.X, pady=5)
        
        # Bouton Appeler
        self.call_btn = ctk.CTkButton(
            self.action_content,
            text="Appeler",
            command=self.call_client,
            fg_color=GRIS_FONCE_ACTION,
            hover_color=GRIS_TRES_FONCE,
            width=BOUTON_ACTION_LARGEUR,
            height=BOUTON_ACTION_HAUTEUR,
            corner_radius=BOUTON_ACTION_RAYON
        )
        self.call_btn.pack(fill=ctk.X, pady=5)
        
        # Bouton créer un document
        self.doc_btn = ctk.CTkButton(
            self.action_content,
            text="Créer un document",
            command=self.create_document,
            fg_color=ORANGE,
            hover_color=ORANGE_FONCE,
            width=BOUTON_ACTION_LARGEUR,
            height=BOUTON_ACTION_HAUTEUR,
            corner_radius=BOUTON_ACTION_RAYON
        )
        self.doc_btn.pack(fill=ctk.X, pady=5)
        
        # Séparateur
        sep = ctk.CTkFrame(self.action_content, height=1, fg_color=("gray80", "gray40"))
        sep.pack(fill=ctk.X, pady=15)
        
        # Dernières activités (liste)
        activities_label = ctk.CTkLabel(
            self.action_content,
            text="Dernières activités",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        activities_label.pack(anchor="w", pady=(5, 10))
        
        # Frame pour la liste des activités
        self.activities_frame = ctk.CTkScrollableFrame(
            self.action_content,
            corner_radius=5,
            fg_color=("gray95", "gray25"),
            height=150
        )
        self.activities_frame.pack(fill=ctk.X, pady=5)
        
        # Activités d'exemple
        activities = [
            {"date": "14/03/2025", "type": "Email", "desc": "Envoi de la proposition commerciale"},
            {"date": "10/03/2025", "type": "Appel", "desc": "Présentation des services"},
            {"date": "05/03/2025", "type": "Document", "desc": "Création du devis #2025-03-15"}
        ]
        
        for activity in activities:
            self.add_activity_item(activity)
    
    def add_activity_item(self, activity):
        """Ajoute un élément d'activité à la liste des activités"""
        item_frame = ctk.CTkFrame(self.activities_frame, fg_color="transparent")
        item_frame.pack(fill=ctk.X, pady=2)
        
        date_label = ctk.CTkLabel(
            item_frame,
            text=activity["date"],
            font=ctk.CTkFont(size=12),
            width=80
        )
        date_label.pack(side=ctk.LEFT)
        
        # Icône selon le type
        icon_map = {"Email": "📧", "Appel": "📞", "Document": "📄"}
        icon = icon_map.get(activity["type"], "🔔")
        
        type_label = ctk.CTkLabel(
            item_frame,
            text=f"{icon} {activity['type']}",
            font=ctk.CTkFont(size=12),
            width=80
        )
        type_label.pack(side=ctk.LEFT)
        
        desc_label = ctk.CTkLabel(
            item_frame,
            text=activity["desc"],
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        desc_label.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
        
    def update_view(self):
        """
        Met à jour la vue avec les données actuelles
        Version optimisée pour la performance
        """
        # Afficher l'indicateur de chargement
        self.show_loading_indicator()
        
        # Annuler la tâche de chargement précédente si elle existe
        if self.loading_task:
            self.parent.after_cancel(self.loading_task)
            self.loading_task = None
        
        # Mettre à jour le statut
        self.update_status("Chargement des données...")
        
        # Charger les clients de manière asynchrone
        self.load_clients_async()
    
    def show_loading_indicator(self):
        """
        Affiche l'indicateur de chargement
        """
        self.loading_label.pack(side=ctk.LEFT, padx=10)
    
    def hide_loading_indicator(self):
        """
        Masque l'indicateur de chargement
        """
        self.loading_label.pack_forget()
    
    def update_status(self, message, message_type="info"):
        """Met à jour la barre d'état avec un message"""
        icon_map = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️"
        }
        icon = icon_map.get(message_type, "ℹ️")
        
        # Mettre à jour le texte de statut
        self.status_label.configure(text=f"{icon} {message}")
        
        # Afficher les métriques de performance
        metrics_text = f"Chargement: {self.performance_metrics['load_time']:.2f}s | Rendu: {self.performance_metrics['render_time']:.2f}s"
        self.metrics_label.configure(text=metrics_text)
    
    def load_clients_async(self):
        """
        Charge les clients de manière asynchrone
        """
        # Indiquer que le chargement est en cours
        self.is_loading = True
        
        # Lancer le chargement dans un thread séparé
        threading.Thread(target=self._load_and_filter_clients, daemon=True).start()
    
    def _load_and_filter_clients(self):
        """
        Charge et filtre les clients dans un thread séparé
        """
        start_time = time.time()
        
        try:
            # Récupérer tous les clients
            clients = self.model.get_all_clients()
            
            # Filtrer les clients si nécessaire
            search_text = self.search_var.get().lower()
            
            if search_text:
                filtered_clients = []
                for client in clients:
                    # Vérifier si le client correspond à la recherche
                    if (search_text in client.get("name", "").lower() or 
                        search_text in client.get("company", "").lower() or 
                        search_text in client.get("email", "").lower() or
                        search_text in client.get("phone", "").lower()):
                        filtered_clients.append(client)
            else:
                filtered_clients = clients
            
            # Appliquer les filtres sélectionnés
            filtered_clients = self._apply_active_filters(filtered_clients)
            
            # Mesurer le temps de chargement et filtrage
            load_time = time.time() - start_time
            self.performance_metrics['load_time'] = load_time
            self.performance_metrics['client_count'] = len(filtered_clients)
            
            # Mettre à jour le cache
            self.clients_cache = filtered_clients
            
            # Mettre à jour l'interface dans le thread principal
            self.parent.after(0, lambda: self._update_ui_with_clients(filtered_clients))
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des clients: {e}")
            self.parent.after(0, lambda: self._show_error_message(str(e)))
    
    def _apply_active_filters(self, clients):
        """Applique les filtres actifs à la liste des clients"""
        filter_value = self.current_filter.get()
        
        if filter_value == "Tous":
            return clients
        elif filter_value == "Clients actifs":
            return [c for c in clients if c.get("status") != "archived" and c.get("status") != "prospect"]
        elif filter_value == "Prospects":
            return [c for c in clients if c.get("status") == "prospect"]
        elif filter_value == "Archivés":
            return [c for c in clients if c.get("status") == "archived"]
        
        return clients
    
    def apply_filter(self):
        """Applique le filtre sélectionné"""
        # Recharger les clients avec le nouveau filtre
        self.update_view()
    
    def apply_sort(self, option=None):
        """Applique le tri sélectionné"""
        if option is None:
            option = self.sort_var.get()
            
        clients = self.clients_cache.copy()
        
        # Trier les clients selon l'option
        if option == "Nom":
            clients.sort(key=lambda c: c.get("name", "").lower())
        elif option == "Entreprise":
            clients.sort(key=lambda c: c.get("company", "").lower())
        elif option == "Date d'ajout":
            clients.sort(key=lambda c: c.get("created_at", "0"), reverse=True)
        elif option == "Dernier contact":
            clients.sort(key=lambda c: c.get("last_contact", "0"), reverse=True)
        
        # Mettre à jour l'interface
        self._update_ui_with_clients(clients)
    
    def _clear_search(self):
        """Efface le champ de recherche"""
        self.search_var.set("")
        self.update_view()
    
    def _update_ui_with_clients(self, clients):
        """
        Met à jour l'interface avec les clients filtrés
        
        Args:
            clients: Liste des clients à afficher
        """
        start_render_time = time.time()
        
        # Masquer l'indicateur de chargement
        self.hide_loading_indicator()
        
        # Fin du chargement
        self.is_loading = False
        
        # Mettre à jour le compteur
        self.client_counter.configure(text=f"{len(clients)} client(s)")
        
        # Afficher ou masquer le message "Aucun client"
        if clients:
            self.no_clients_label.pack_forget()
            self.clients_table.frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
            self.clients_table.clear()
            
            # Préparer les données des lignes
            row_data_list = []
            for client in clients:
                data = [
                    client.get("name", ""),
                    client.get("company", ""),
                    client.get("email", ""),
                    client.get("phone", "")
                ]
                
                def create_actions_widget(parent, client=client):
                    actions_frame = ctk.CTkFrame(parent, fg_color="transparent")
                    
                    # Bouton Détails
                    details_btn = ctk.CTkButton(
                        actions_frame,
                        text="Détails",
                        width=60,
                        height=24,
                        font=ctk.CTkFont(size=12),
                        fg_color=GRIS_FONCE_ACTION,
                        hover_color=GRIS_TRES_FONCE,
                        command=lambda cid=client.get("id"): self.show_client_details(cid)
                    )
                    details_btn.pack(side=ctk.LEFT, padx=1)
                    
                    # Bouton Éditer
                    edit_btn = ctk.CTkButton(
                        actions_frame,
                        text="Éditer",
                        width=60,
                        height=24,
                        font=ctk.CTkFont(size=12),
                        fg_color="#3498db",
                        hover_color="#2980b9",
                        command=lambda cid=client.get("id"): self.edit_client(cid)
                    )
                    edit_btn.pack(side=ctk.LEFT, padx=1)
                    
                    # Bouton Supprimer
                    delete_btn = ctk.CTkButton(
                        actions_frame,
                        text="Supprimer",
                        width=60,
                        height=24,
                        font=ctk.CTkFont(size=12),
                        fg_color="#e74c3c",
                        hover_color="#c0392b",
                        command=lambda cid=client.get("id"): self.confirm_delete_client(cid)
                    )
                    delete_btn.pack(side=ctk.LEFT, padx=1)
                    
                    return actions_frame
                
                row_data_list.append((data + [create_actions_widget], client.get("id")))
            
            # Ajouter les lignes de manière asynchrone
            self.clients_table.add_rows_async(row_data_list)
            
        else:
            self.clients_table.frame.pack_forget()
            self.no_clients_label.pack(pady=40)
        
        # Mesurer le temps de rendu
        render_time = time.time() - start_render_time
        self.performance_metrics['render_time'] = render_time
        
        # Mettre à jour le statut
        self.update_status(f"Chargement de {len(clients)} clients terminé", "success")
        
        logger.debug(f"Rendu de {len(clients)} clients en {render_time:.3f}s")
    
    def _show_error_message(self, error_message):
        """
        Affiche un message d'erreur
        
        Args:
            error_message: Message d'erreur
        """
        self.update_status(f"Erreur: {error_message}", "error")
        messagebox.showerror(
            "Erreur de chargement",
            f"Impossible de charger les clients: {error_message}"
        )
        self.hide_loading_indicator()
        self.is_loading = False
    
    def show(self):
        """
        Affiche la vue
        """
        self.frame.pack(fill=ctk.BOTH, expand=True)
        self.update_view()
    
    def hide(self):
        """
        Masque la vue
        """
        self.frame.pack_forget()
    
    def debounced_filter_clients(self):
        """
        Applique un debounce sur le filtrage des clients
        """
        # Annuler le timer précédent s'il existe
        if self.search_timer:
            self.parent.after_cancel(self.search_timer)
        
        # Définir un nouveau timer
        self.search_timer = self.parent.after(self.debounce_delay, self.filter_clients)
    
    def filter_clients(self):
        """
        Filtre les clients selon le texte de recherche
        """
        # Si un chargement est déjà en cours, attendre
        if self.is_loading:
            self.search_timer = self.parent.after(100, self.filter_clients)
            return
        
        # Mesurer le temps de début
        start_time = time.time()
        
        search_text = self.search_var.get().lower()
        
        # Si le texte de recherche est vide ou très court, utiliser tous les clients
        if not search_text or len(search_text) < 2:
            # Mettre à jour la vue avec tous les clients
            self.load_clients_async()
            return
        
        # Filtrer les clients depuis le cache local
        filtered_clients = []
        for client in self.clients_cache:
            if (search_text in client.get("name", "").lower() or 
                search_text in client.get("company", "").lower() or 
                search_text in client.get("email", "").lower() or
                search_text in client.get("phone", "").lower()):
                filtered_clients.append(client)
        
        # Appliquer les filtres supplémentaires
        filtered_clients = self._apply_active_filters(filtered_clients)
        
        # Mesurer le temps de filtrage
        filter_time = time.time() - start_time
        self.performance_metrics['filter_time'] = filter_time
        
        logger.debug(f"Filtrage de {len(self.clients_cache)} clients en {filter_time:.3f}s")
        
        # Mettre à jour l'interface
        self._update_ui_with_clients(filtered_clients)
    
    def show_client_details(self, client_id):
        """
        Affiche les détails d'un client
        
        Args:
            client_id: ID du client à afficher
        """
        # Sauvegarder l'ID du client courant
        self.current_client_id = client_id
        
        # Récupérer les données du client
        client = self.model.get_client(client_id)
        if not client:
            self.show_error(self.parent, "Client introuvable")
            return
        
        # Mettre à jour le titre
        self.detail_title.configure(text=f"Détails de {client.get('name', 'Client')}")
        
        # Nettoyer l'ancien contenu
        for widget in self.info_content.winfo_children():
            widget.destroy()
        
        # Créer le formulaire de détails en lecture seule
        fields = [
            ("Nom", "name"),
            ("Prénom", "first_name"),
            ("Entreprise", "company"),
            ("Email", "email"),
            ("Téléphone", "phone"),
            ("Adresse", "address"),
            ("Code postal", "postal_code"),
            ("Ville", "city"),
            ("Notes", "notes")
        ]
        
        # Style de la grille
        col_width = 120
        
        # Créer la grille d'informations
        for i, (label, field) in enumerate(fields):
            # Cadre pour la ligne - sans hauteur fixe
            row_frame = ctk.CTkFrame(self.info_content, fg_color=("gray95", "gray20") if i % 2 == 0 else "transparent")
            row_frame.pack(fill=ctk.X, pady=1)
            
            # Libellé
            ctk.CTkLabel(
                row_frame, 
                text=f"{label}:",
                font=ctk.CTkFont(weight="bold"),
                width=col_width,
                anchor="nw"
            ).pack(side=ctk.LEFT, padx=10, pady=8)
            
            # Valeur
            value = client.get(field, "")
            
            if field == "notes":
                # Créer un cadre pour les notes
                notes_container = ctk.CTkFrame(row_frame, fg_color="transparent")
                notes_container.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=10, pady=10)
                
                # Si aucun texte, afficher juste un placeholder
                if not value.strip():
                    notes_label = ctk.CTkLabel(
                        notes_container,
                        text="Aucune note",
                        font=ctk.CTkFont(size=12, slant="italic"),
                        text_color=("gray60", "gray60"),
                        anchor="w"
                    )
                    notes_label.pack(fill=ctk.X, pady=5)
                else:
                    # Diviser le texte en lignes et créer un label par ligne
                    # Cette approche permet d'obtenir une hauteur exacte basée sur le contenu
                    lines = value.split('\n')
                    for line in lines:
                        if line.strip():  # Ignorer les lignes vides
                            line_label = ctk.CTkLabel(
                                notes_container,
                                text=line,
                                anchor="w",
                                justify="left",
                                wraplength=450
                            )
                            line_label.pack(anchor="w", fill=ctk.X, pady=1)
                        else:
                            # Espace pour les lignes vides
                            spacer = ctk.CTkFrame(notes_container, height=10, fg_color="transparent")
                            spacer.pack(fill=ctk.X)
            else:
                # Pour les autres champs, affichage standard avec retour à la ligne
                ctk.CTkLabel(
                    row_frame,
                    text=value,
                    anchor="w",
                    justify="left",
                    wraplength=300  # Force le retour à la ligne
                ).pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=10, pady=8)
        
        # Mettre la vue courante à "detail"
        self.current_view = "detail"
        
        # Masquer la vue liste et afficher la vue détail
        self.list_frame.pack_forget()
        self.toolbar.pack_forget()
        self.detail_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=15)
        
        # Ajouter à l'historique
        self.view_history.append("list")
    
    def show_list_view(self):
        """Retourne à la vue liste"""
        self.current_view = "list"
        self.detail_frame.pack_forget()
        self.toolbar.pack(fill=ctk.X, padx=15, pady=15)
        self.list_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=(0, 15))
    
    def send_email_to_client(self):
        """Fonction pour envoyer un email au client"""
        client = self.model.get_client(self.current_client_id)
        if not client or not client.get("email"):
            self.show_error(self.parent, "Adresse email non disponible")
            return
            
        # Cette fonction ouvrirait idéalement le client email par défaut
        email = client.get("email", "")
        
        try:
            import webbrowser
            webbrowser.open(f"mailto:{email}")
            self.update_status(f"Ouverture du client mail pour {email}", "success")
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du client mail: {e}")
            self.show_error(self.parent, f"Impossible d'ouvrir le client mail: {e}")
    
    def call_client(self):
        """Fonction pour appeler le client"""
        client = self.model.get_client(self.current_client_id)
        if not client or not client.get("phone"):
            self.show_error(self.parent, "Numéro de téléphone non disponible")
            return
            
        # Cette fonction pourrait intégrer avec un système VoIP ou afficher le numéro
        phone = client.get("phone", "")
        self.show_message(
            "Appel",
            f"Appel de {client.get('name', 'Client')} au {phone}",
            "Pour implémenter cette fonctionnalité, intégrez avec votre système téléphonique."
        )
    
    def create_document(self):
        """Fonction pour créer un document pour le client"""
        client = self.model.get_client(self.current_client_id)
        if not client:
            self.show_error(self.parent, "Client introuvable")
            return
            
        # Vérifier si la vue de document existe dans l'application principale
        try:
            # Remonter à la vue principale pour accéder aux autres vues
            main_view = self.parent.master
            while not hasattr(main_view, "show_view") and hasattr(main_view, "master"):
                main_view = main_view.master
                
            if hasattr(main_view, "show_view") and hasattr(main_view, "views") and "documents" in main_view.views:
                # Basculer vers la vue documents
                main_view.show_view("documents")
                
                # Créer un nouveau document avec ce client
                if hasattr(main_view.views["documents"], "new_document"):
                    main_view.views["documents"].new_document(client_id=client.get("id"))
                    return
            
            # Si on n'a pas pu accéder à la vue documents, afficher un message
            self.show_message(
                "Création de document",
                f"Créer un document pour {client.get('name', 'Client')}",
                "La vue de documents n'est pas accessible."
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'accès à la vue documents: {e}")
            self.show_error(self.parent, f"Impossible d'accéder à la vue documents: {e}")
    
    def show_client_form(self, client_data=None, parent=None):
        """
        Méthode publique pour afficher le formulaire client
        Délègue à la méthode privée _show_client_form
        
        Args:
            client_data (dict, optional): Données du client à modifier
            parent (Widget, optional): Widget parent pour le dialogue
        """
        self._show_client_form(client_data, parent)
    
    def _show_client_form(self, client_data=None, parent=None):
        """
        Affiche le formulaire de client
        
        Args:
            client_data (dict, optional): Données du client à modifier
            parent (Widget, optional): Widget parent pour le dialogue (si None, utilise self.parent)
        """
        # Créer une nouvelle fenêtre modale avec style moderne
        dialog = ctk.CTkToplevel(parent or self.parent)
        dialog.title("Modifier le client" if client_data else "Nouveau client")
        dialog.geometry("550x680")
        dialog.resizable(False, False)
        dialog.transient(parent or self.parent)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Frame principal avec padding et coins arrondis
        main_frame = ctk.CTkFrame(dialog, corner_radius=15)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre avec emoji et style moderne
        title_label = ctk.CTkLabel(
            main_frame,
            text="👤 " + ("Modifier le client" if client_data else "Nouveau client"),
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(pady=(20, 30))
        
        # Frame pour le formulaire avec style moderne
        form_frame = ctk.CTkScrollableFrame(main_frame, corner_radius=10, fg_color=("white", "gray17"))
        form_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=15)
        
        # Variables pour les champs
        self.client_data = {
            "name": ctk.StringVar(value=client_data.get("name", "") if client_data else ""),
            "first_name": ctk.StringVar(value=client_data.get("first_name", "") if client_data else ""),
            "company": ctk.StringVar(value=client_data.get("company", "") if client_data else ""),
            "email": ctk.StringVar(value=client_data.get("email", "") if client_data else ""),
            "phone": ctk.StringVar(value=client_data.get("phone", "") if client_data else ""),
            "address": ctk.StringVar(value=client_data.get("address", "") if client_data else ""),
            "postal_code": ctk.StringVar(value=client_data.get("postal_code", "") if client_data else ""),
            "city": ctk.StringVar(value=client_data.get("city", "") if client_data else ""),
            "notes": ctk.StringVar(value=client_data.get("notes", "") if client_data else ""),
            "status": ctk.StringVar(value=client_data.get("status", "active") if client_data else "active")
        }
        
        # Stocker les données originales dans un format normalisé pour comparaison future
        self.original_client_data = {}
        if client_data:
            for field, var in self.client_data.items():
                if field in client_data:
                    # Normaliser les valeurs originales
                    self.original_client_data[field] = str(client_data.get(field, "")).strip()
        
        # Dictionnaire pour stocker les références aux widgets d'entrée
        self.form_entries = {}
        
        # Fonction pour créer un champ de formulaire
        def create_form_field(parent, row, label_text, variable, required=False, placeholder="", field_type="text"):
            # Frame pour le champ
            field_frame = ctk.CTkFrame(parent, fg_color="transparent")
            field_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=(15, 5))
            field_frame.columnconfigure(1, weight=1)
            
            # Label
            label = ctk.CTkLabel(
                field_frame,
                text=f"{label_text}{'*' if required else ''}:",
                font=ctk.CTkFont(weight="bold" if required else "normal"),
                anchor="w"
            )
            label.grid(row=0, column=0, sticky="w")
            
            # Widget selon le type
            if field_type == "text":
                # Entry standard
                entry = ctk.CTkEntry(
                    field_frame,
                    textvariable=variable,
                    placeholder_text=placeholder,
                    width=350,
                    height=35,
                    corner_radius=8,
                    border_color=("#3498db", "#2980b9") if required else None
                )
                entry.grid(row=1, column=0, sticky="ew", columnspan=2, pady=(5, 0))
                return entry
            elif field_type == "textarea":
                # Frame conteneur pour le textarea avec taille fixe
                container_frame = ctk.CTkFrame(field_frame)
                container_frame.grid(row=1, column=0, sticky="ew", columnspan=2, pady=(5, 0))
                container_frame.grid_propagate(False)  # Empêche le redimensionnement du conteneur
                container_frame.configure(width=350, height=200)  # Augmenté à 200
                
                entry = ctk.CTkTextbox(
                    container_frame,
                    width=350,
                    height=200,  # Augmenté à 200
                    corner_radius=8,
                    wrap="word"  # Active le retour à la ligne automatique
                )
                entry.pack(fill="both", expand=True)  # Remplit le conteneur
                
                # Insérer le texte initial
                if variable.get():
                    entry.insert("1.0", variable.get())
                    
                # Fonction pour mettre à jour la variable quand le texte change
                def update_var(*args):
                    content = entry.get("1.0", "end-1c")
                    # Limiter à 500 caractères
                    if len(content) > 500:
                        content = content[:500]
                        entry.delete("1.0", "end")
                        entry.insert("1.0", content)
                        entry.mark_set("insert", "end")
                    variable.set(content)
                
                # Lier à un timer pour ne pas surcharger
                update_timer = None
                def delayed_update(*args):
                    nonlocal update_timer
                    if update_timer:
                        entry.after_cancel(update_timer)
                    update_timer = entry.after(300, update_var)
                
                # Lier les événements de modification du texte
                entry.bind("<KeyRelease>", delayed_update)
                
                # Ajouter un label pour le compteur de caractères
                char_count_label = ctk.CTkLabel(
                    field_frame,
                    text="0/500 caractères",
                    font=ctk.CTkFont(size=12),
                    text_color="gray"
                )
                char_count_label.grid(row=2, column=0, sticky="e", columnspan=2, pady=(2, 0))
                
                # Mettre à jour le compteur de caractères
                def update_char_count(*args):
                    content = entry.get("1.0", "end-1c")
                    char_count_label.configure(text=f"{len(content)}/500 caractères")
                
                entry.bind("<KeyRelease>", lambda e: (delayed_update(), update_char_count()))
                
                # Mettre à jour le compteur initial si des données existent
                if variable.get():
                    update_char_count()
                
                return entry
            elif field_type == "combobox":
                # Menu déroulant
                options = ["active", "prospect", "archived"]
                option_labels = ["Client actif", "Prospect", "Archivé"]
                
                combo = ctk.CTkOptionMenu(
                    field_frame,
                    values=option_labels,
                    variable=variable,
                    width=350,
                    height=35,
                    corner_radius=8,
                    dynamic_resizing=False
                )
                combo.grid(row=1, column=0, sticky="ew", columnspan=2, pady=(5, 0))
                
                # Définir la valeur initiale
                idx = options.index(variable.get()) if variable.get() in options else 0
                combo.set(option_labels[idx])
                
                # Fonction pour convertir entre valeurs internes et affichées
                def on_selection(choice):
                    idx = option_labels.index(choice)
                    variable.set(options[idx])
                
                combo.configure(command=on_selection)
                return combo
        
        # Créer les champs du formulaire
        fields = [
            ("Nom", "name", True, "text"),
            ("Prénom", "first_name", False, "text"),
            ("Entreprise", "company", False, "text"),
            ("Email", "email", True, "text"),
            ("Téléphone", "phone", False, "text"),
            ("Adresse", "address", False, "text"),
            ("Code postal", "postal_code", False, "text"),
            ("Ville", "city", False, "text"),
            ("Statut", "status", False, "combobox"),
            ("Notes", "notes", False, "textarea")
        ]
        
        # Configurer la grille du formulaire
        form_frame.columnconfigure(0, weight=1)
        
        # Ajouter les champs
        self.form_entries = {}
        for i, (label, field, required, field_type) in enumerate(fields):
            entry = create_form_field(
                form_frame,
                i,
                label,
                self.client_data[field],
                required,
                f"Entrez {label.lower()}",
                field_type
            )
            self.form_entries[field] = entry
        
        # Frame pour les boutons avec style moderne
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, pady=(20, 0))
        
        # Fonction de validation et sauvegarde avec confirmation
        def save_client():
            # Récupérer les valeurs des zones de texte multilignes
            if "notes" in self.form_entries and hasattr(self.form_entries["notes"], "get"):
                if hasattr(self.form_entries["notes"].get, "__call__"):  # Si c'est un CTkTextbox
                    self.client_data["notes"].set(self.form_entries["notes"].get("1.0", "end-1c"))
            
            # Valider uniquement le nom
            if not self.client_data["name"].get().strip():
                self.show_error(dialog, "❌ Le nom est requis.")
                self.form_entries["name"].focus()
                return
                
            # Valider l'email
            email = self.client_data["email"].get().strip()
            if not email:
                self.show_error(dialog, "❌ L'email est requis.")
                self.form_entries["email"].focus()
                return
            
            # Validation plus stricte du format email
            # Cette regex vérifie:
            # - Format général de l'email (caractères autorisés avant @)
            # - Domaine correctement formaté
            # - Extension de domaine valide (minimum 2 caractères, maximum 6)
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, email):
                self.show_error(dialog, "❌ Format d'email invalide.\nExemple valide: nom@domaine.com")
                self.form_entries["email"].focus()
                return
            
            # Vérifications supplémentaires pour l'email
            if '..' in email or email.startswith('.') or email.endswith('.'):
                self.show_error(dialog, "❌ L'email contient des points consécutifs ou commence/termine par un point.")
                self.form_entries["email"].focus()
                return
            
            # Valider le format du numéro de téléphone (pas de lettres)
            phone = self.client_data["phone"].get().strip()
            if phone:  # Validation uniquement si le champ n'est pas vide
                # Supprimer les espaces, tirets, parenthèses et le signe "+" pour vérifier s'il reste des lettres
                cleaned_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
                if not cleaned_phone.isdigit():
                    self.show_error(dialog, "❌ Le numéro de téléphone ne doit contenir que des chiffres et éventuellement '+', '-', '(', ')', ' '.")
                    self.form_entries["phone"].focus()
                    return
                    
                # Vérifier que le numéro a une longueur raisonnable (entre 8 et 15 chiffres)
                if len(cleaned_phone) < 8 or len(cleaned_phone) > 15:
                    self.show_error(dialog, "❌ Le numéro de téléphone doit contenir entre 8 et 15 chiffres.")
                    self.form_entries["phone"].focus()
                    return
            
            # Préparer les données
            client = {
                field: var.get().strip()
                for field, var in self.client_data.items()
            }
            
            # Vérifier si des modifications ont été effectuées (uniquement pour l'édition)
            if client_data and hasattr(self, 'original_client_data'):
                # Utiliser la nouvelle méthode robuste pour détecter les modifications
                modifications, modified_fields = self.check_client_modifications(
                    self.original_client_data, client
                )
                
                # Si aucune modification, afficher le message et fermer le formulaire
                if not modifications:
                    # Afficher le message "Aucune modification effectuée"
                    message_dialog = ctk.CTkToplevel(dialog)
                    message_dialog.title("Information")
                    message_dialog.geometry("300x150")
                    message_dialog.resizable(False, False)
                    message_dialog.transient(dialog)
                    message_dialog.grab_set()
                    
                    # Centrer le dialogue
                    message_dialog.update_idletasks()
                    width = message_dialog.winfo_width()
                    height = message_dialog.winfo_height()
                    x = (dialog.winfo_rootx() + dialog.winfo_width() // 2) - (width // 2)
                    y = (dialog.winfo_rooty() + dialog.winfo_height() // 2) - (height // 2)
                    message_dialog.geometry(f"{width}x{height}+{x}+{y}")
                    
                    # Créer le contenu du message
                    frame = ctk.CTkFrame(message_dialog, corner_radius=10)
                    frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=15)
                    
                    # Icône d'information
                    ctk.CTkLabel(
                        frame,
                        text="ℹ️",
                        font=ctk.CTkFont(size=32)
                    ).pack(pady=(10, 5))
                    
                    # Message
                    ctk.CTkLabel(
                        frame,
                        text="Aucune modification effectuée",
                        font=ctk.CTkFont(size=14, weight="bold")
                    ).pack(pady=10)
                    
                    # Bouton OK
                    ctk.CTkButton(
                        frame,
                        text="OK",
                        width=80,
                        height=30,
                        corner_radius=8,
                        fg_color=BLEU_PRIMAIRE,
                        hover_color=BLEU_FONCE,
                        command=lambda: [message_dialog.destroy(), dialog.destroy()]
                    ).pack(pady=10)
                    
                    return
            
            # Ajouter la date de création pour les nouveaux clients
            if not client_data:
                client["created_at"] = datetime.now().isoformat()
                client["last_contact"] = datetime.now().isoformat()
            
            # Créer le dialogue de confirmation
            confirm_dialog = ctk.CTkToplevel(dialog)
            confirm_dialog.title("Confirmation")
            confirm_dialog.geometry("400x200")
            confirm_dialog.resizable(False, False)
            confirm_dialog.transient(dialog)
            confirm_dialog.grab_set()
            
            # Centrer le dialogue
            confirm_dialog.update_idletasks()
            width = confirm_dialog.winfo_width()
            height = confirm_dialog.winfo_height()
            x = (dialog.winfo_rootx() + dialog.winfo_width() // 2) - (width // 2)
            y = (dialog.winfo_rooty() + dialog.winfo_height() // 2) - (height // 2)
            confirm_dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            # Contenu du dialogue
            content_frame = ctk.CTkFrame(confirm_dialog, corner_radius=10)
            content_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=15)
            
            # Icône d'avertissement
            warning_icon = ctk.CTkLabel(
                content_frame,
                text="⚠️",
                font=ctk.CTkFont(size=36)
            )
            warning_icon.pack(pady=(10, 5))
            
            # Titre
            title_label = ctk.CTkLabel(
                content_frame,
                text="Confirmation",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title_label.pack(pady=(0, 10))
            
            # Message de confirmation
            action = "modifier" if client_data else "créer"
            message = ctk.CTkLabel(
                content_frame,
                text=f"Êtes-vous sûr de vouloir {action} ce client ?",
                font=ctk.CTkFont(size=13),
                wraplength=350
            )
            message.pack(pady=10)
            
            # Boutons de confirmation
            btn_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            btn_frame.pack(pady=15, fill=ctk.X)
            
            # Fonction pour sauvegarder après confirmation
            def confirmed_save():
                confirm_dialog.destroy()
                
                try:
                    # Sauvegarder en arrière-plan
                    def save_task():
                        try:
                            if client_data:
                                # Mise à jour
                                if self.model.update_client(client_data["id"], client):
                                    dialog.destroy()
                                    
                                    # Si nous sommes dans la vue détaillée, mettre à jour les détails du client
                                    if hasattr(self, 'current_view') and hasattr(self, 'current_client_id'):
                                        if self.current_view == "detail" and self.current_client_id == client_data["id"]:
                                            # Mettre à jour la vue détaillée
                                            self.parent.after(0, lambda: self.show_client_details(client_data["id"]))
                                        else:
                                            # Simplement mettre à jour la liste
                                            self.update_view()
                                    else:
                                        # Fallback si les attributs n'existent pas
                                        self.update_view()
                                    
                                    self.update_status(f"✅ Client {client['name']} mis à jour avec succès", "success")
                                else:
                                    self.show_error(dialog, "❌ Erreur lors de la mise à jour du client.")
                            else:
                                # Création
                                if self.model.add_client(client):
                                    dialog.destroy()
                                    self.update_view()
                                    self.update_status(f"✅ Client {client['name']} créé avec succès", "success")
                                else:
                                    self.show_error(dialog, "❌ Erreur lors de la création du client.")
                        except Exception as e:
                            logger.error(f"Erreur lors de la sauvegarde du client: {e}")
                            self.show_error(dialog, f"❌ Erreur: {str(e)}")
                    
                    # Afficher une animation de chargement
                    save_btn.configure(text="Enregistrement...", state="disabled")
                    cancel_button.configure(state="disabled")
                    
                    # Lancer la sauvegarde en arrière-plan
                    threading.Thread(target=save_task, daemon=True).start()
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde du client: {e}")
                    self.show_error(dialog, f"❌ Erreur: {str(e)}")
            
            # Bouton Non
            no_btn = ctk.CTkButton(
                btn_frame,
                text="Non",
                fg_color=ROUGE,
                hover_color=ROUGE_FONCE,
                width=100,
                height=35,
                corner_radius=8,
                command=confirm_dialog.destroy
            )
            no_btn.pack(side=ctk.LEFT, padx=10, expand=True)
            
            # Bouton Oui
            yes_btn = ctk.CTkButton(
                btn_frame,
                text="Oui",
                fg_color=VERT,
                hover_color=VERT_FONCE,
                width=100,
                height=35,
                corner_radius=8,
                command=confirmed_save
            )
            yes_btn.pack(side=ctk.RIGHT, padx=10, expand=True)

        # Boutons avec style moderne
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Annuler",
            width=120,
            height=40,
            corner_radius=8,
            fg_color="#95a5a6",
            hover_color="#7f8c8d",
            font=ctk.CTkFont(weight="bold"),
            command=dialog.destroy
        )
        cancel_button.pack(side=ctk.LEFT, padx=10)

        # Bouton Enregistrer
        save_btn = ctk.CTkButton(
            button_frame,
            text="Enregistrer",
            width=120,
            height=40,
            corner_radius=8,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            font=ctk.CTkFont(weight="bold"),
            command=save_client
        )
        save_btn.pack(side=ctk.RIGHT, padx=10)
        
        # Focus sur le premier champ
        self.form_entries["name"].focus()
    
    def edit_client(self, client_id):
        """
        Édite un client existant
        
        Args:
            client_id: ID du client à modifier
        """
        self._show_client_form(self.model.get_client(client_id))
        self.update_status("Modification du client en cours...")
    
    def confirm_delete_client(self, client_id):
        """
        Demande confirmation avant de supprimer un client
        
        Args:
            client_id: ID du client à supprimer
        """
        client = self.model.get_client(client_id)
        if not client:
            return
        
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Confirmer la suppression")
        dialog.geometry("450x350")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        dialog.attributes('-topmost', True)
        dialog.resizable(False, False)
        
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Contenu du dialogue avec style moderne
        content_frame = ctk.CTkFrame(dialog, corner_radius=15)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Icône d'alerte
        warning_label = ctk.CTkLabel(
            content_frame,
            text="⚠️",
            font=ctk.CTkFont(size=64)
        )
        warning_label.pack(pady=(30, 20))
        
        # Titre de l'alerte
        title_label = ctk.CTkLabel(
            content_frame,
            text="Confirmer la suppression",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Message de confirmation
        message_label = ctk.CTkLabel(
            content_frame,
            text=f"Êtes-vous sûr de vouloir supprimer le client \n{client.get('name')} ?",
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        message_label.pack(pady=(0, 10))
        
        # Avertissement
        warning_text = "Cette action est irréversible et le client supprimé ne pourra pas être récupéré."
        warning_message = ctk.CTkLabel(
            content_frame,
            text=warning_text,
            font=ctk.CTkFont(size=13),
            text_color=("#e74c3c", "#ff6b6b"),
            wraplength=350
        )
        warning_message.pack(pady=(0, 30))
        
        # Indicateur de chargement (initialement masqué)
        delete_indicator = ctk.CTkLabel(
            content_frame,
            text="Suppression en cours...",
            text_color="#3498db",
            font=ctk.CTkFont(size=13, slant="italic")
        )
        
        # Boutons
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(pady=(0, 20), fill="x", padx=20)
        
        def delete_confirmed():
            # Afficher l'indicateur de chargement
            delete_indicator.pack(pady=10)
            
            # Désactiver les boutons pendant la suppression
            cancel_btn.configure(state="disabled")
            delete_btn.configure(state="disabled", text="Suppression...")
            
            dialog.update_idletasks()
            
            # Supprimer le client dans un thread séparé
            def delete_client_thread():
                try:
                    success = self.model.delete_client(client_id)
                    
                    # Mettre à jour l'interface dans le thread principal
                    dialog.after(0, lambda: finalize_delete(success))
                except Exception as e:
                    dialog.after(0, lambda: self.show_error(dialog, f"Erreur lors de la suppression: {str(e)}"))
                    dialog.after(0, lambda: delete_indicator.pack_forget())
                    dialog.after(0, lambda: cancel_btn.configure(state="normal"))
                    dialog.after(0, lambda: delete_btn.configure(state="normal", text="Supprimer"))
            
            def finalize_delete(success):
                if success:
                    dialog.destroy()
                    self.update_view()
                    
                    # Afficher un toast de succès
                    self.update_status(f"Client {client.get('name')} supprimé", "success")
                else:
                    delete_indicator.pack_forget()
                    cancel_btn.configure(state="normal")
                    delete_btn.configure(state="normal", text="Supprimer")
                    self.show_error(dialog, "Erreur lors de la suppression du client.")
            
            threading.Thread(target=delete_client_thread, daemon=True).start()
        
        # Bouton Annuler
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            width=BOUTON_STANDARD_LARGEUR,
            height=BOUTON_STANDARD_HAUTEUR,
            corner_radius=BOUTON_STANDARD_RAYON,
            fg_color=GRIS,
            hover_color=GRIS_FONCE,
            font=ctk.CTkFont(weight="bold"),
            command=dialog.destroy
        )
        cancel_btn.pack(side=ctk.LEFT, padx=(0, 10), fill="x", expand=True)
        
        # Bouton Supprimer
        delete_btn = ctk.CTkButton(
            buttons_frame,
            text="Supprimer",
            width=BOUTON_STANDARD_LARGEUR,
            height=BOUTON_STANDARD_HAUTEUR,
            corner_radius=BOUTON_STANDARD_RAYON,
            fg_color=ROUGE,
            hover_color=ROUGE_FONCE,
            font=ctk.CTkFont(weight="bold"),
            command=delete_confirmed
        )
        delete_btn.pack(side=ctk.RIGHT, fill="x", expand=True)
    
    def import_clients(self):
        """Importe des clients depuis un fichier CSV"""
        # Demander le fichier à importer
        file_path = filedialog.askopenfilename(
            title="Importer des clients",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Créer une fenêtre de prévisualisation moderne
            preview_dialog = ctk.CTkToplevel(self.parent)
            preview_dialog.title("Aperçu de l'importation")
            preview_dialog.geometry("900x700")
            preview_dialog.resizable(True, True)
            preview_dialog.transient(self.parent)
            preview_dialog.grab_set()
            
            # Centrer la fenêtre
            preview_dialog.update_idletasks()
            x = (preview_dialog.winfo_screenwidth() - preview_dialog.winfo_width()) // 2
            y = (preview_dialog.winfo_screenheight() - preview_dialog.winfo_height()) // 2
            preview_dialog.geometry(f"+{x}+{y}")
            
            # Frame principal avec style moderne
            main_frame = ctk.CTkFrame(preview_dialog, corner_radius=15)
            main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            
            # Titre avec style moderne
            title_label = ctk.CTkLabel(
                main_frame,
                text="📥 Aperçu de l'importation",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title_label.pack(pady=(20, 30))
            
            # Lire le fichier CSV avec pandas
            df = pd.read_csv(file_path)
            
            # Frame pour les options d'importation avec style moderne
            options_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=("gray95", "gray20"))
            options_frame.pack(fill=ctk.X, padx=15, pady=(0, 20))
            
            # Titre de la section options
            options_title = ctk.CTkLabel(
                options_frame,
                text="Options d'importation",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            options_title.pack(pady=(15, 10))
            
            # Options d'importation
            checkboxes_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
            checkboxes_frame.pack(fill=ctk.X, padx=20, pady=(0, 15))
            
            skip_duplicates_var = ctk.BooleanVar(value=True)
            skip_checkbox = ctk.CTkCheckBox(
                checkboxes_frame,
                text="Ignorer les doublons (basé sur l'email)",
                variable=skip_duplicates_var,
                corner_radius=6,
                border_width=2
            )
            skip_checkbox.pack(side=ctk.LEFT, padx=20, pady=10)
            
            update_existing_var = ctk.BooleanVar(value=False)
            update_checkbox = ctk.CTkCheckBox(
                checkboxes_frame,
                text="Mettre à jour les clients existants",
                variable=update_existing_var,
                corner_radius=6,
                border_width=2
            )
            update_checkbox.pack(side=ctk.LEFT, padx=20, pady=10)
            
            # Frame pour le mappage des colonnes
            mapping_frame = ctk.CTkFrame(main_frame, fg_color=("white", "gray17"), corner_radius=10)
            mapping_frame.pack(fill=ctk.X, padx=15, pady=(0, 20))
            
            # Titre du mappage
            mapping_title = ctk.CTkLabel(
                mapping_frame,
                text="Mappage des colonnes",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            mapping_title.pack(pady=(15, 10))
            
            # Créer une grille pour le mappage
            mapping_grid = ctk.CTkFrame(mapping_frame, fg_color="transparent")
            mapping_grid.pack(fill=ctk.X, padx=20, pady=(0, 15))
            
            # Champs de destination disponibles
            target_fields = [
                "name", "first_name", "company", "email", "phone", 
                "address", "postal_code", "city", "notes", "status"
            ]
            readable_fields = [
                "Nom", "Prénom", "Entreprise", "Email", "Téléphone",
                "Adresse", "Code postal", "Ville", "Notes", "Statut"
            ]
            
            # Dictionnaire pour stocker les variables de mappage
            mapping_vars = {}
            
            # En-têtes CSV détectés
            csv_headers = df.columns.tolist()
            
            # Ajouter l'option "Ne pas importer"
            csv_headers_with_none = ["-- Ne pas importer --"] + csv_headers
            
            # Créer le mappage
            for i, (field, readable) in enumerate(zip(target_fields, readable_fields)):
                # Frame pour chaque ligne
                field_frame = ctk.CTkFrame(mapping_grid, fg_color="transparent")
                field_frame.pack(fill=ctk.X, pady=5)
                
                # Étiquette du champ
                ctk.CTkLabel(
                    field_frame,
                    text=f"{readable} :",
                    width=120,
                    anchor="e"
                ).pack(side=ctk.LEFT, padx=(0, 10))
                
                # Menu déroulant
                mapping_vars[field] = ctk.StringVar()
                
                # Essayer de trouver une correspondance automatique
                default_value = "-- Ne pas importer --"
                for header in csv_headers:
                    if field.lower() in header.lower() or readable.lower() in header.lower():
                        default_value = header
                        break
                
                mapping_vars[field].set(default_value)
                
                dropdown = ctk.CTkOptionMenu(
                    field_frame,
                    values=csv_headers_with_none,
                    variable=mapping_vars[field],
                    width=280,
                    dynamic_resizing=False
                )
                dropdown.pack(side=ctk.LEFT)
                
                # Indicateur si c'est un champ requis
                if field in ["name", "email"]:
                    required_label = ctk.CTkLabel(
                        field_frame,
                        text="(requis)",
                        text_color=("#e74c3c", "#ff6b6b"),
                        font=ctk.CTkFont(size=12)
                    )
                    required_label.pack(side=ctk.LEFT, padx=10)
            
            # Frame pour l'aperçu avec style moderne
            preview_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=("white", "gray17"))
            preview_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=(0, 20))
            
            # Titre de l'aperçu
            preview_title = ctk.CTkLabel(
                preview_frame,
                text="Aperçu des données",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            preview_title.pack(pady=(15, 10))
            
            # Afficher l'aperçu des données dans un tableau
            preview_table = ctk.CTkScrollableFrame(preview_frame, corner_radius=6)
            preview_table.pack(fill=ctk.BOTH, expand=True, padx=15, pady=(0, 15))
            
            # Créer une grille pour l'aperçu
            table_grid = ctk.CTkFrame(preview_table, fg_color="transparent")
            table_grid.pack(fill=ctk.BOTH, expand=True)
            
            # Ajouter les en-têtes
            for i, header in enumerate(csv_headers):
                header_label = ctk.CTkLabel(
                    table_grid,
                    text=header,
                    font=ctk.CTkFont(weight="bold"),
                    fg_color=("#e0e0e0", "#2c3e50"),
                    corner_radius=4
                )
                header_label.grid(row=0, column=i, sticky="nsew", padx=1, pady=1)
            
            # Ajouter quelques lignes d'exemple
            sample_rows = min(5, len(df))
            for row_idx in range(sample_rows):
                for col_idx, col_name in enumerate(csv_headers):
                    value = str(df.iloc[row_idx, col_idx])
                    bg_color = ("white", "gray25") if row_idx % 2 == 0 else (("gray95", "gray20"))
                    cell = ctk.CTkLabel(
                        table_grid,
                        text=value,
                        wraplength=150,
                        fg_color=bg_color,
                        corner_radius=4
                    )
                    cell.grid(row=row_idx+1, column=col_idx, sticky="nsew", padx=1, pady=1)
            
            # Frame pour les statistiques avec style moderne
            stats_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color=("gray95", "gray20"))
            stats_frame.pack(fill=ctk.X, padx=15, pady=(0, 20))
            
            total_rows = len(df)
            stats_label = ctk.CTkLabel(
                stats_frame,
                text=f"Total de lignes à importer : {total_rows}",
                font=ctk.CTkFont(weight="bold", size=14)
            )
            stats_label.pack(pady=15)
            
            # Frame pour les boutons
            button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            button_frame.pack(fill=ctk.X, pady=(0, 0))
            
            # Fonction de validation et d'importation
            def import_data():
                # Vérifier les champs requis
                if mapping_vars["name"].get() == "-- Ne pas importer --":
                    self.show_error(preview_dialog, "Le champ 'Nom' est requis pour l'importation.")
                    return
                    
                if mapping_vars["email"].get() == "-- Ne pas importer --":
                    self.show_error(preview_dialog, "Le champ 'Email' est requis pour l'importation.")
                    return
                
                try:
                    # Désactiver les boutons et afficher un indicateur
                    cancel_button.configure(state="disabled")
                    import_button.configure(state="disabled", text="Importation en cours...")
                    
                    # Créer une barre de progression
                    progress_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
                    progress_frame.pack(fill=ctk.X, padx=15, pady=15)
                    
                    progress_label = ctk.CTkLabel(
                        progress_frame,
                        text="Importation en cours...",
                        font=ctk.CTkFont(size=12)
                    )
                    progress_label.pack(pady=(0, 5))
                    
                    progress_bar = ctk.CTkProgressBar(progress_frame, width=400)
                    progress_bar.pack()
                    progress_bar.set(0)
                    
                    # Fonction d'importation dans un thread
                    def import_thread():
                        try:
                            # Récupérer les clients existants (pour la vérification des doublons)
                            existing_clients = self.model.get_all_clients()
                            existing_emails = {client["email"].lower() for client in existing_clients if "email" in client}
                            
                            imported = 0
                            updated = 0
                            skipped = 0
                            errors = 0
                            
                            # Construire le mappage réel
                            column_mapping = {}
                            for target_field, var in mapping_vars.items():
                                source_column = var.get()
                                if source_column != "-- Ne pas importer --":
                                    column_mapping[target_field] = source_column
                            
                            # Nombre total de lignes à traiter
                            total = len(df)
                            
                            # Traiter chaque ligne
                            for idx, row in df.iterrows():
                                try:
                                    # Mettre à jour la progression
                                    progress = (idx + 1) / total
                                    preview_dialog.after(0, lambda p=progress: progress_bar.set(p))
                                    preview_dialog.after(0, lambda p=progress: progress_label.configure(
                                        text=f"Importation en cours... {int(p*100)}% ({idx+1}/{total})"
                                    ))
                                    
                                    # Construire le client à partir du mappage
                                    client = {}
                                    for target_field, source_column in column_mapping.items():
                                        value = row[source_column]
                                        # Convertir NaN en chaîne vide
                                        if pd.isna(value):
                                            value = ""
                                        client[target_field] = str(value).strip()
                                    
                                    # Ajouter la date de création
                                    client["created_at"] = datetime.now().isoformat()
                                    
                                    # Vérifier si le client existe déjà
                                    email = client.get("email", "").lower()
                                    if email and email in existing_emails:
                                        if update_existing_var.get():
                                            # Mettre à jour le client existant
                                            existing_client = next(c for c in existing_clients if c["email"].lower() == email)
                                            if self.model.update_client(existing_client["id"], client):
                                                updated += 1
                                            else:
                                                errors += 1
                                        elif skip_duplicates_var.get():
                                            skipped += 1
                                        else:
                                            # Ajouter quand même (crée un doublon)
                                            if self.model.add_client(client):
                                                imported += 1
                                            else:
                                                errors += 1
                                    else:
                                        # Ajouter le nouveau client
                                        if self.model.add_client(client):
                                            imported += 1
                                            # Ajouter l'email à la liste des existants
                                            if email:
                                                existing_emails.add(email)
                                        else:
                                            errors += 1
                                        
                                except Exception as e:
                                    logger.error(f"Erreur lors de l'importation d'un client: {e}")
                                    errors += 1
                            
                            # Montrer que c'est terminé
                            preview_dialog.after(0, lambda: progress_bar.set(1.0))
                            preview_dialog.after(0, lambda: progress_label.configure(
                                text=f"Importation terminée ! {imported} importés, {updated} mis à jour, {skipped} ignorés, {errors} erreurs"
                            ))
                            
                            # Fermer la fenêtre de prévisualisation après un délai
                            preview_dialog.after(2000, preview_dialog.destroy)
                            
                            # Mettre à jour la vue
                            preview_dialog.after(2100, self.update_view)
                            
                            # Afficher le résumé
                            message = f"Importation terminée :\n\n"
                            message += f"✅ {imported} clients importés\n"
                            if updated > 0:
                                message += f"🔄 {updated} clients mis à jour\n"
                            if skipped > 0:
                                message += f"⏭️ {skipped} clients ignorés (doublons)\n"
                            if errors > 0:
                                message += f"❌ {errors} erreurs\n"
                            
                            preview_dialog.after(2200, lambda msg=message: self.show_success(msg))
                            
                        except Exception as e:
                            logger.error(f"Erreur lors de l'importation: {e}")
                            preview_dialog.after(0, lambda err=e: self.show_error(preview_dialog, f"Erreur lors de l'importation: {str(err)}"))
                            preview_dialog.after(0, lambda: cancel_button.configure(state="normal"))
                            preview_dialog.after(0, lambda: import_button.configure(state="normal", text="Importer"))
                    
                    # Lancer le thread d'importation
                    threading.Thread(target=import_thread, daemon=True).start()
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'importation: {e}")
                    self.show_error(preview_dialog, f"Erreur lors de l'importation: {str(e)}")
                    cancel_button.configure(state="normal")
                    import_button.configure(state="normal", text="Importer")
            
            # Boutons avec style moderne
            cancel_button = ctk.CTkButton(
                button_frame,
                text="Annuler",
                width=120,
                height=40,
                corner_radius=8,
                fg_color="#95a5a6",
                hover_color="#7f8c8d",
                font=ctk.CTkFont(weight="bold"),
                command=preview_dialog.destroy
            )
            cancel_button.pack(side=ctk.LEFT, padx=10)
            
            import_button = ctk.CTkButton(
                button_frame,
                text="Importer",
                width=120,
                height=40,
                corner_radius=8,
                fg_color="#2ecc71",
                hover_color="#27ae60",
                font=ctk.CTkFont(weight="bold"),
                command=import_data
            )
            import_button.pack(side=ctk.RIGHT, padx=10)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du fichier: {e}")
            self.show_error(self.parent, f"Erreur lors de l'ouverture du fichier: {str(e)}")
    
    def export_clients(self):
        """
        Exporte les clients vers un fichier CSV ou Excel
        """
        # Demander le type d'exportation et le fichier de destination
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Exporter les clients")
        dialog.geometry("450x350")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        dialog.resizable(False, False)
        
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Contenu du dialogue avec style moderne
        content_frame = ctk.CTkFrame(dialog, corner_radius=15)
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre
        title_label = ctk.CTkLabel(
            content_frame,
            text="📤 Exporter les clients",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(pady=(20, 30))
        
        # Options d'exportation
        options_frame = ctk.CTkFrame(content_frame, corner_radius=10, fg_color=("gray95", "gray20"))
        options_frame.pack(fill=ctk.X, padx=15, pady=(0, 20))
        
        # Sous-titre
        options_title = ctk.CTkLabel(
            options_frame,
            text="Options d'exportation",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        options_title.pack(pady=(15, 10))
        
        # Type de fichier
        file_type_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        file_type_frame.pack(fill=ctk.X, padx=20, pady=10)
        
        file_type_label = ctk.CTkLabel(file_type_frame, text="Format de fichier:", width=120, anchor="w")
        file_type_label.pack(side=ctk.LEFT)
        
        file_type_var = ctk.StringVar(value="CSV")
        file_type_menu = ctk.CTkOptionMenu(
            file_type_frame,
            values=["CSV", "Excel"],
            variable=file_type_var,
            width=200,
            corner_radius=6
        )
        file_type_menu.pack(side=ctk.LEFT, padx=(10, 0))
        
        # Filtre d'exportation
        filter_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        filter_frame.pack(fill=ctk.X, padx=20, pady=10)
        
        filter_label = ctk.CTkLabel(filter_frame, text="Exporter:", width=120, anchor="w")
        filter_label.pack(side=ctk.LEFT)
        
        filter_var = ctk.StringVar(value="Tous les clients")
        filter_menu = ctk.CTkOptionMenu(
            filter_frame,
            values=["Tous les clients", "Clients actifs", "Prospects", "Clients archivés", "Résultats de recherche"],
            variable=filter_var,
            width=200,
            corner_radius=6
        )
        filter_menu.pack(side=ctk.LEFT, padx=(10, 0))
        
        # Champs à exporter
        fields_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        fields_frame.pack(fill=ctk.X, padx=20, pady=10)
        
        fields_label = ctk.CTkLabel(fields_frame, text="Champs:", anchor="w")
        fields_label.pack(anchor="w", pady=(0, 5))
        
        # Variables pour les cases à cocher
        field_vars = {
            "name": ctk.BooleanVar(value=True),
            "first_name": ctk.BooleanVar(value=True),
            "company": ctk.BooleanVar(value=True),
            "email": ctk.BooleanVar(value=True),
            "phone": ctk.BooleanVar(value=True),
            "address": ctk.BooleanVar(value=True),
            "postal_code": ctk.BooleanVar(value=True),
            "city": ctk.BooleanVar(value=True),
            "notes": ctk.BooleanVar(value=True),
            "status": ctk.BooleanVar(value=True),
            "created_at": ctk.BooleanVar(value=True)
        }
        
        # Grille pour les cases à cocher
        checkboxes_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
        checkboxes_frame.pack(fill=ctk.X)
        
        # Créer les cases à cocher en deux colonnes
        field_labels = {
            "name": "Nom",
            "first_name": "Prénom",
            "company": "Entreprise",
            "email": "Email",
            "phone": "Téléphone",
            "address": "Adresse",
            "postal_code": "Code postal",
            "city": "Ville",
            "notes": "Notes",
            "status": "Statut",
            "created_at": "Date de création"
        }
        
        col1 = ctk.CTkFrame(checkboxes_frame, fg_color="transparent")
        col1.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)
        
        col2 = ctk.CTkFrame(checkboxes_frame, fg_color="transparent")
        col2.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)
        
        # Répartir les champs sur les deux colonnes
        fields = list(field_vars.keys())
        mid = len(fields) // 2 + len(fields) % 2
        
        for i, field in enumerate(fields[:mid]):
            ctk.CTkCheckBox(
                col1,
                text=field_labels[field],
                variable=field_vars[field],
                corner_radius=6
            ).pack(anchor="w", pady=2)
            
        for i, field in enumerate(fields[mid:]):
            ctk.CTkCheckBox(
                col2,
                text=field_labels[field],
                variable=field_vars[field],
                corner_radius=6
            ).pack(anchor="w", pady=2)
        
        # Fonction d'exportation
        def do_export():
            try:
                # Déterminer le filtre à appliquer
                filter_type = filter_var.get()
                
                # Obtenir les clients selon le filtre
                if filter_type == "Résultats de recherche":
                    clients_to_export = self.clients_cache
                else:
                    # Obtenir tous les clients puis filtrer
                    all_clients = self.model.get_all_clients()
                    
                    if filter_type == "Tous les clients":
                        clients_to_export = all_clients
                    elif filter_type == "Clients actifs":
                        clients_to_export = [c for c in all_clients if c.get("status") != "archived" and c.get("status") != "prospect"]
                    elif filter_type == "Prospects":
                        clients_to_export = [c for c in all_clients if c.get("status") == "prospect"]
                    elif filter_type == "Clients archivés":
                        clients_to_export = [c for c in all_clients if c.get("status") == "archived"]
                    else:
                        clients_to_export = all_clients
                
                # Sélectionner les champs à exporter
                fields_to_export = [field for field, var in field_vars.items() if var.get()]
                
                # Si aucun champ sélectionné, afficher une erreur
                if not fields_to_export:
                    self.show_error(dialog, "Veuillez sélectionner au moins un champ à exporter.")
                    return
                
                # Préparer les données d'exportation
                export_data = []
                for client in clients_to_export:
                    client_data = {}
                    for field in fields_to_export:
                        client_data[field_labels.get(field, field)] = client.get(field, "")
                    export_data.append(client_data)
                
                # Détermer le type de fichier
                file_type = file_type_var.get()
                if file_type == "CSV":
                    file_extension = ".csv"
                    file_types = [("Fichier CSV", "*.csv")]
                else:  # Excel
                    file_extension = ".xlsx"
                    file_types = [("Fichier Excel", "*.xlsx")]
                
                # Demander le fichier de destination
                current_date = datetime.now().strftime("%Y-%m-%d")
                default_filename = f"clients_export_{current_date}{file_extension}"
                
                output_path = filedialog.asksaveasfilename(
                    defaultextension=file_extension,
                    filetypes=file_types,
                    initialfile=default_filename
                )
                
                if not output_path:
                    return
                
                # Désactiver les boutons
                cancel_btn.configure(state="disabled")
                export_btn.configure(state="disabled", text="Exportation en cours...")
                
                # Créer un DataFrame
                df = pd.DataFrame(export_data)
                
                # Exporter selon le type de fichier
                def export_thread():
                    try:
                        if file_type == "CSV":
                            df.to_csv(output_path, index=False, encoding='utf-8-sig')
                        else:  # Excel
                            df.to_excel(output_path, index=False)
                        
                        # Fermer le dialogue
                        dialog.after(0, dialog.destroy)
                        
                        # Afficher un message de succès
                        dialog.after(100, lambda: self.show_success(f"Export réussi!\n\n{len(export_data)} clients ont été exportés vers {os.path.basename(output_path)}"))
                        
                    except Exception as e:
                        logger.error(f"Erreur lors de l'exportation: {e}")
                        dialog.after(0, lambda err=e: self.show_error(dialog, f"Erreur lors de l'exportation: {str(err)}"))
                        dialog.after(0, lambda: cancel_btn.configure(state="normal"))
                        dialog.after(0, lambda: export_btn.configure(state="normal", text="Exporter"))
                
                # Lancer l'exportation dans un thread séparé
                threading.Thread(target=export_thread, daemon=True).start()
                
            except Exception as e:
                logger.error(f"Erreur lors de l'exportation: {e}")
                self.show_error(dialog, f"Erreur lors de l'exportation: {str(e)}")
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, pady=(20, 0))
        
        # Boutons avec style moderne
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            width=120,
            height=40,
            corner_radius=8,
            fg_color="#95a5a6",
            hover_color="#7f8c8d",
            font=ctk.CTkFont(weight="bold"),
            command=dialog.destroy
        )
        cancel_btn.pack(side=ctk.LEFT, padx=10)
        
        export_btn = ctk.CTkButton(
            buttons_frame,
            text="Exporter",
            width=120,
            height=40,
            corner_radius=8,
            fg_color="#3498db",
            hover_color="#2980b9",
            font=ctk.CTkFont(weight="bold"),
            command=do_export
        )
        export_btn.pack(side=ctk.RIGHT, padx=10)
    
    def show_error(self, parent, message):
        """
        Affiche un message d'erreur
        
        Args:
            parent: Widget parent
            message: Message d'erreur
        """
        try:
            dialog = ctk.CTkToplevel(parent)
            dialog.title("Erreur")
            dialog.geometry("400x200")
            dialog.transient(parent)
            dialog.grab_set()
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (parent.winfo_rootx() + parent.winfo_width() // 2) - (width // 2)
            y = (parent.winfo_rooty() + parent.winfo_height() // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            # Contenu du dialogue avec style moderne
            msg_frame = ctk.CTkFrame(dialog, corner_radius=10, fg_color="transparent")
            msg_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            
            # Icône d'erreur
            error_icon = ctk.CTkLabel(msg_frame, text="❌", font=ctk.CTkFont(size=36), text_color=("#e74c3c", "#ff6b6b"))
            error_icon.pack(pady=(10, 0))
            
            # Titre
            ctk.CTkLabel(
                msg_frame,
                text="Erreur",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=(0, 10))
            
            # Message
            ctk.CTkLabel(
                msg_frame,
                text=message,
                wraplength=320
            ).pack(pady=5)
            
            # Bouton OK
            ctk.CTkButton(
                msg_frame,
                text="OK",
                width=BOUTON_STANDARD_LARGEUR,
                height=BOUTON_STANDARD_HAUTEUR,
                corner_radius=BOUTON_STANDARD_RAYON,
                fg_color=VERT,
                hover_color=VERT_FONCE,
                font=ctk.CTkFont(weight="bold"),
                command=dialog.destroy
            ).pack(pady=15)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de la boîte de dialogue d'erreur: {e}")
            messagebox.showerror("Erreur", message, parent=parent)
    
    def show_message(self, title, message, information=None, message_type="info"):
        """
        Affiche une boîte de dialogue avec un message et une icône cohérente
        
        Args:
            title: Titre du message
            message: Message principal
            information: Informations supplémentaires (optionnel)
            message_type: Type de message ("info", "success", "error", "warning")
        """
        try:
            dialog = ctk.CTkToplevel(self.parent)
            dialog.title(title)
            dialog.geometry("400x250")
            dialog.transient(self.parent)
            dialog.grab_set()
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            # Icônes cohérentes pour chaque type de message
            icon_map = {
                "info": "ℹ️",
                "success": "✅",
                "error": "❌",
                "warning": "⚠️"
            }
            icon = icon_map.get(message_type, "ℹ️")
            
            # Couleurs cohérentes pour chaque type de message
            color_map = {
                "info": BLEU_PRIMAIRE,
                "success": VERT,
                "error": ROUGE,
                "warning": ORANGE
            }
            color = color_map.get(message_type, BLEU_PRIMAIRE)
            hover_color_map = {
                "info": BLEU_FONCE,
                "success": VERT_FONCE,
                "error": ROUGE_FONCE,
                "warning": ORANGE_FONCE
            }
            hover_color = hover_color_map.get(message_type, BLEU_FONCE)
            
            # Contenu du dialogue avec style moderne
            msg_frame = ctk.CTkFrame(dialog, corner_radius=10, fg_color="transparent")
            msg_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            
            # Icône adaptée au type de message
            info_icon = ctk.CTkLabel(msg_frame, text=icon, font=ctk.CTkFont(size=36))
            info_icon.pack(pady=(10, 0))
            
            # Titre
            ctk.CTkLabel(
                msg_frame,
                text=title,
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=(0, 10))
            
            # Message principal
            ctk.CTkLabel(
                msg_frame,
                text=message,
                wraplength=320
            ).pack(pady=5)
            
            # Informations supplémentaires si fournies
            if information:
                info_frame = ctk.CTkFrame(msg_frame, fg_color=("gray95", "gray20"), corner_radius=8)
                info_frame.pack(fill=ctk.X, padx=10, pady=10)
                
                ctk.CTkLabel(
                    info_frame,
                    text=information,
                    wraplength=300,
                    font=ctk.CTkFont(size=12),
                    justify="left"
                ).pack(padx=10, pady=10)
            
            # Bouton OK
            ctk.CTkButton(
                msg_frame,
                text="OK",
                width=BOUTON_STANDARD_LARGEUR,
                height=BOUTON_STANDARD_HAUTEUR,
                corner_radius=BOUTON_STANDARD_RAYON,
                fg_color=color,
                hover_color=hover_color,
                font=ctk.CTkFont(weight="bold"),
                command=dialog.destroy
            ).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de la boîte de dialogue: {e}")
            messagebox.showinfo(title, message, parent=self.parent)
    
    def show_success(self, message):
        """
        Affiche une boîte de dialogue de succès
        
        Args:
            message: Message de succès
        """
        try:
            dialog = ctk.CTkToplevel(self.parent)
            dialog.title("Succès")
            dialog.geometry("400x250")
            dialog.transient(self.parent)
            dialog.grab_set()
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() - width) // 2
            y = (dialog.winfo_screenheight() - height) // 2
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            # Contenu du dialogue avec style moderne
            frame = ctk.CTkFrame(dialog, corner_radius=10)
            frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            
            # Icône de succès
            success_icon = ctk.CTkLabel(frame, text="✅", font=ctk.CTkFont(size=36), text_color=("#2ecc71", "#2ecc71"))
            success_icon.pack(pady=(10, 0))
            
            # Titre
            ctk.CTkLabel(
                frame,
                text="Succès",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=(0, 10))
            
            # Message
            ctk.CTkLabel(
                frame,
                text=message,
                wraplength=320
            ).pack(pady=10)
            
            # Bouton OK
            ctk.CTkButton(
                frame,
                text="OK",
                width=BOUTON_STANDARD_LARGEUR,
                height=BOUTON_STANDARD_HAUTEUR,
                corner_radius=BOUTON_STANDARD_RAYON,
                fg_color=VERT,
                hover_color=VERT_FONCE,
                font=ctk.CTkFont(weight="bold"),
                command=dialog.destroy
            ).pack(pady=15)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de la boîte de dialogue de succès: {e}")
            messagebox.showinfo("Succès", message, parent=self.parent)
    
    def show_success_toast(self, message):
        """Affiche une notification toast de succès avec icône cohérente"""
        # Créer un toast avec style moderne
        toast = ctk.CTkFrame(self.parent, corner_radius=10, fg_color=("gray95", "#2c3e50"), border_width=1, border_color=("#2ecc71", "#2ecc71"))
        
        # Icône de succès cohérente
        icon_label = ctk.CTkLabel(
            toast,
            text="✅",  # Utiliser la même icône que dans update_status
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#2ecc71", "#2ecc71"),
            width=20
        )
        icon_label.pack(side="left", padx=(10, 5), pady=10)
        
        # Message
        message_label = ctk.CTkLabel(
            toast,
            text=message,
            font=ctk.CTkFont(size=14)
        )
        message_label.pack(side="left", padx=(0, 20), pady=10)
        
        # Positionner le toast en bas de l'écran
        toast.place(relx=0.5, rely=0.95, anchor="center")
        
        # Animation d'entrée et de sortie (inchangée)
        alpha = 0.0
        def fade_in():
            nonlocal alpha
            alpha += 0.1
            if alpha <= 1.0:
                toast.attributes('-alpha', alpha)
                self.parent.after(20, fade_in)
        
        def fade_out():
            nonlocal alpha
            alpha -= 0.1
            if alpha >= 0.0:
                toast.attributes('-alpha', alpha)
                self.parent.after(20, fade_out)
            else:
                toast.destroy()
        
        fade_in()
        self.parent.after(3000, fade_out)

    def _normalize_value(self, value):
        """
        Normalise une valeur pour comparaison cohérente
        
        Args:
            value: Valeur à normaliser
            
        Returns:
            str: Valeur normalisée en chaîne de caractères
        """
        if value is None:
            return ""
        
        # Convertir en chaîne de caractères et supprimer les espaces en début/fin
        return str(value).strip()

    def check_client_modifications(self, original_data, new_data):
        """
        Vérifie si des modifications ont été apportées aux données du client
        
        Args:
            original_data: Données originales du client
            new_data: Nouvelles données du client
            
        Returns:
            tuple: (modifications_détectées, détails_des_modifications)
        """
        modifications = False
        modified_fields = []
        
        # Liste des champs à ignorer dans la comparaison
        ignore_fields = ["id", "created_at", "last_contact"]
        
        # Comparer chaque champ
        for field, new_value in new_data.items():
            # Ignorer les champs techniques
            if field in ignore_fields:
                continue
            
            # Normaliser les valeurs
            norm_new = self._normalize_value(new_value)
            
            # Obtenir et normaliser la valeur originale
            if field in original_data:
                norm_original = self._normalize_value(original_data.get(field, ""))
            else:
                norm_original = ""
            
            # Comparer et logger si différent
            if norm_original != norm_new:
                modifications = True
                modified_fields.append({
                    "field": field,
                    "original": norm_original,
                    "new": norm_new
                })
                logger.debug(f"Modification détectée: {field} - original: '{norm_original}' -> nouveau: '{norm_new}'")
        
        # Si aucune modification n'est détectée, le logger
        if not modifications:
            logger.debug("Aucune modification détectée entre les données originales et nouvelles")
            
        return modifications, modified_fields


# Classes d'optimisation - Importées directement du fichier original
class ClientCache:
    """
    Cache pour les données clients
    Permet d'optimiser les accès aux données fréquemment utilisées
    """
    
    def __init__(self, max_size=100):
        """
        Initialise le cache
        
        Args:
            max_size: Taille maximale du cache
        """
        self.cache = {}  # client_id -> client_data
        self.access_count = {}  # client_id -> count
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self.last_update = time.time()
    
    def get(self, client_id):
        """
        Récupère un client du cache
        
        Args:
            client_id: ID du client
            
        Returns:
            dict: Données du client ou None si non trouvé
        """
        if client_id in self.cache:
            # Incrémenter le compteur d'accès
            self.access_count[client_id] = self.access_count.get(client_id, 0) + 1
            self.hits += 1
            return self.cache[client_id]
        
        self.misses += 1
        return None
    
    def put(self, client_id, client_data):
        """
        Ajoute un client au cache
        
        Args:
            client_id: ID du client
            client_data: Données du client
        """
        # Si le cache est plein, supprimer l'élément le moins utilisé
        if len(self.cache) >= self.max_size:
            least_used = min(self.access_count.items(), key=lambda x: x[1])[0]
            self.cache.pop(least_used, None)
            self.access_count.pop(least_used, None)
        
        # Ajouter au cache
        self.cache[client_id] = client_data.copy()  # Copie pour éviter les références partagées
        self.access_count[client_id] = 1
        self.last_update = time.time()
    
    def update(self, client_id, client_data):
        """
        Met à jour un client dans le cache
        
        Args:
            client_id: ID du client
            client_data: Nouvelles données du client
        """
        if client_id in self.cache:
            self.cache[client_id] = client_data.copy()
            self.last_update = time.time()
    
    def invalidate(self, client_id=None):
        """
        Invalide une entrée du cache ou tout le cache
        
        Args:
            client_id: ID du client à invalider, ou None pour tout invalider
        """
        if client_id is not None:
            self.cache.pop(client_id, None)
            self.access_count.pop(client_id, None)
        else:
            self.cache.clear()
            self.access_count.clear()
        
        self.last_update = time.time()
    
    def get_all(self):
        """
        Récupère tous les clients du cache
        
        Returns:
            list: Liste de tous les clients en cache
        """
        return list(self.cache.values())
    
    def get_stats(self):
        """
        Récupère les statistiques du cache
        
        Returns:
            dict: Statistiques du cache
        """
        hit_rate = 0
        if self.hits + self.misses > 0:
            hit_rate = (self.hits / (self.hits + self.misses)) * 100
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "last_update": self.last_update
        }


class ClientSearchOptimizer:
    """
    Optimiseur de recherche pour les clients
    Utilise l'indexation pour accélérer les recherches
    """
    
    def __init__(self):
        """
        Initialise l'optimiseur de recherche
        """
        self.index = {}  # token -> set(client_ids)
        self.clients_map = {}  # client_id -> client
        self.indexed_fields = ["name", "company", "email", "phone"]
    
    def build_index(self, clients):
        """
        Construit l'index de recherche
        
        Args:
            clients: Liste des clients à indexer
        """
        # Réinitialiser l'index
        self.index = {}
        self.clients_map = {}
        
        # Indexer chaque client
        for client in clients:
            client_id = client.get("id")
            if not client_id:
                continue
            
            # Stocker le client dans la map
            self.clients_map[client_id] = client
            
            # Indexer les champs spécifiés
            for field in self.indexed_fields:
                self._index_field(client_id, client.get(field, ""))
    
    def _index_field(self, client_id, field_value):
        """
        Indexe un champ d'un client
        
        Args:
            client_id: ID du client
            field_value: Valeur du champ à indexer
        """
        if not field_value:
            return
        
        # Convertir en chaîne et en minuscules
        text = str(field_value).lower()
        
        # Tokeniser (diviser en mots)
        words = text.split()
        
        # Ajouter des sous-chaînes pour la recherche partielle
        tokens = set()
        for word in words:
            # Ajouter le mot complet
            tokens.add(word)
            
            # Ajouter des sous-chaînes (min 2 caractères)
            if len(word) > 2:
                for i in range(2, len(word) + 1):
                    tokens.add(word[:i])
        
        # Ajouter à l'index
        for token in tokens:
            if token not in self.index:
                self.index[token] = set()
            
            self.index[token].add(client_id)
    
    def search(self, query):
        """
        Recherche des clients selon une requête
        
        Args:
            query: Requête de recherche
            
        Returns:
            list: Liste des clients correspondants
        """
        if not query or not self.index:
            return list(self.clients_map.values())
        
        # Convertir en minuscules
        query = query.lower()
        
        # Diviser en tokens
        tokens = query.split()
        
        # Ensembles des IDs correspondants
        matching_ids = set()
        
        # Pour chaque token de la requête
        for token in tokens:
            # Si le token est trop court, ignorer
            if len(token) < 2:
                continue
            
            # Chercher des correspondances
            token_matches = set()
            
            # Rechercher les correspondances exactes et partielles
            for indexed_token, client_ids in self.index.items():
                if indexed_token.startswith(token):
                    token_matches.update(client_ids)
            
            # Si c'est le premier token, initialiser matching_ids
            if not matching_ids:
                matching_ids = token_matches
            else:
                # Intersection avec les résultats précédents
                matching_ids &= token_matches
            
            # Si plus aucun client ne correspond, arrêter
            if not matching_ids:
                break
        
        # Récupérer les clients correspondants
        results = [self.clients_map[client_id] for client_id in matching_ids]
        
        return results
    
    def get_stats(self):
        """
        Récupère les statistiques de l'indexeur
        
        Returns:
            dict: Statistiques de l'indexeur
        """
        return {
            "tokens": len(self.index),
            "clients": len(self.clients_map),
            "avg_clients_per_token": sum(len(ids) for ids in self.index.values()) / len(self.index) if self.index else 0
        }


# Fonction pour appliquer les optimisations à ClientView
def apply_client_view_optimizations(view):
    """
    Applique des optimisations de performance à ClientView
    
    Args:
        view: Instance de ClientView à optimiser
    """
    # Créer un cache clients
    view.clients_cache = ClientCache(max_size=200)
    
    # Créer un optimiseur de recherche
    view.search_optimizer = ClientSearchOptimizer()
    
    # Stocker les métriques de performance
    view.performance_metrics = {
        'load_time': 0,
        'filter_time': 0,
        'render_time': 0,
        'client_count': 0
    }
    
    # Capturer l'ancienne méthode update_view
    original_update_view = view.update_view
    
    # Remplacer par une version optimisée
    def optimized_update_view():
        # Afficher l'indicateur de chargement
        view.show_loading_indicator()
        
        # Annuler la tâche de chargement précédente si elle existe
        if hasattr(view, 'loading_task') and view.loading_task:
            view.parent.after_cancel(view.loading_task)
            view.loading_task = None
        
        # Vérifier si le cache peut être utilisé
        cache_stats = view.clients_cache.get_stats()
        if cache_stats["size"] > 0 and time.time() - cache_stats["last_update"] < 60:  # Cache valide pendant 60 secondes
            # Utiliser le cache
            clients = view.clients_cache.get_all()
            
            # Filtrer si nécessaire
            search_text = view.search_var.get().lower()
            if search_text:
                # Utiliser l'optimiseur de recherche si possible
                if hasattr(view, 'search_optimizer'):
                    filtered_clients = view.search_optimizer.search(search_text)
                else:
                    # Filtrage manuel
                    filtered_clients = []
                    for client in clients:
                        if (search_text in client.get("name", "").lower() or 
                            search_text in client.get("company", "").lower() or 
                            search_text in client.get("email", "").lower()):
                            filtered_clients.append(client)
            else:
                filtered_clients = clients
            
            # Mettre à jour l'interface
            view._update_ui_with_clients(filtered_clients)
            logger.debug("Utilisation du cache clients")
        else:
            # Charger les clients de manière asynchrone
            threading.Thread(target=view._load_and_filter_clients, daemon=True).start()
    
    # Remplacer la méthode
    view.update_view = optimized_update_view
    
    # Capturer l'ancienne méthode de chargement
    original_load = view._load_and_filter_clients
    
    # Remplacer par une version qui utilise l'indexeur
    def optimized_load_and_filter():
        start_time = time.time()
        
        try:
            # Récupérer tous les clients
            clients = view.model.get_all_clients()
            
            # Mettre à jour le cache
            for client in clients:
                client_id = client.get("id")
                if client_id:
                    view.clients_cache.put(client_id, client)
            
            # Mettre à jour l'indexeur de recherche
            view.search_optimizer.build_index(clients)
            
            # Filtrer les clients si nécessaire
            search_text = view.search_var.get().lower()
            
            if search_text:
                filtered_clients = view.search_optimizer.search(search_text)
            else:
                filtered_clients = clients
            
            # Appliquer les filtres sélectionnés si la méthode existe
            if hasattr(view, '_apply_active_filters'):
                filtered_clients = view._apply_active_filters(filtered_clients)
            
            # Mesurer le temps de chargement et filtrage
            load_time = time.time() - start_time
            view.performance_metrics['load_time'] = load_time
            view.performance_metrics['client_count'] = len(filtered_clients)
            
            # Mettre à jour l'interface dans le thread principal
            view.parent.after(0, lambda: view._update_ui_with_clients(filtered_clients))
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des clients: {e}")
            view.parent.after(0, lambda: view._show_error_message(str(e)))
    
    # Remplacer la méthode
    view._load_and_filter_clients = optimized_load_and_filter
    
    logger.info("Optimisations appliquées à ClientView")
    
    return view


# Mesure du temps d'exécution de certaines opérations
def measure_execution_time(func_name=None):
    """
    Décorateur pour mesurer le temps d'exécution d'une fonction
    
    Args:
        func_name: Nom de la fonction (par défaut, utilise le nom réel)
    
    Returns:
        function: Fonction décorée
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            name = func_name or func.__name__
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{name} exécuté en {execution_time:.3f}s")
            return result
        return wrapper
    return decorator


# Exemple d'utilisation des optimisations
@measure_execution_time("Initialisation de ClientView")
def create_optimized_client_view(parent, app_model):
    """
    Crée une instance optimisée de ClientView
    
    Args:
        parent: Widget parent
        app_model: Modèle de l'application
        
    Returns:
        ClientView: Instance optimisée de ClientView
    """
    view = ClientView(parent, app_model)
    return apply_client_view_optimizations(view)
