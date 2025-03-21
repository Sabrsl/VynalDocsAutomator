#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue de gestion des documents pour l'application Vynal Docs Automator
avec organisation en dossiers
"""

import os
import logging
import shutil
import threading
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from utils.dialog_utils import DialogUtils
import traceback
import platform
import subprocess

# Exceptions personnalisées
class DocumentValidationError(Exception):
    """Exception pour les erreurs de validation de document"""
    pass

class FileSecurityError(Exception):
    """Exception pour les erreurs de sécurité de fichier"""
    pass

logger = logging.getLogger("VynalDocsAutomator.DocumentView")

class DocumentView:
    """
    Vue de gestion des documents avec interface moderne et organisation en dossiers
    Permet de visualiser, créer et gérer des documents
    """
    
    # Constantes de configuration
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 Mo
    MAX_CACHE_SIZE = 50
    OPERATION_TIMEOUT = 5.0
    ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt', '.odt', '.rtf']
    ALLOWED_MIME_TYPES = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'application/vnd.oasis.opendocument.text',
        'application/rtf'
    ]
    
    def __init__(self, parent, app_model):
        """
        Initialise la vue de gestion des documents
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        
        # Initialiser les variables de filtre en premier
        self.search_var = ctk.StringVar(value="")
        self.client_var = ctk.StringVar(value="Tous les clients")
        self.type_var = ctk.StringVar(value="Tous les types")
        self.type_filter_var = ctk.StringVar(value="Tous")  
        self.date_filter_var = ctk.StringVar(value="Toutes")
        
        # Initialiser les caches dès le début
        self.client_names_cache = {}
        self._file_type_cache = {}
        self._file_type_cache_size = 100
        
        # Initialiser le gestionnaire d'utilisation
        from utils.usage_tracker import UsageTracker
        self.usage_tracker = UsageTracker()
        
        # Initialiser le gestionnaire de cache
        from utils.cache_manager import CacheManager
        self.cache_manager = CacheManager()
        
        # Initialiser l'optimiseur de fichiers
        from utils.file_optimizer import file_optimizer
        self.file_optimizer = file_optimizer
        
        # Initialiser l'analyseur de documents
        self.doc_analyzer = None
        self._init_doc_analyzer()
        
        # Cadre principal de la vue
        self.frame = ctk.CTkFrame(parent)
        
        # Liste pour stocker les documents sélectionnés
        self.selected_documents = []
        
        # Variable pour stocker le dossier sélectionné
        self.selected_folder = None
        self.current_subfolder = None  # Pour suivre le sous-dossier actuel
        
        # Structure de dossiers
        self.document_folders = {
            "client": "Par client",
            "type": "Par type",
            "date": "Par date"
        }
        
        # Icônes des dossiers
        self.folder_icons = {
            "client": "👥",
            "type": "📑",
            "date": "📅"
        }
        
        # Paramètres de performance et pagination
        self.page_size = 20  # Nombre de documents par page
        self.current_page = 0
        self.total_documents = 0
        self.documents_cache = {}
        self.last_filter = None
        
        # Paramètres de performance
        self.debounce_delay = 300  # Délai de debounce en millisecondes
        self.search_timer = None
        self.is_loading = False
        self.loading_queue = None
        
        # Créer les composants de l'interface
        self.create_widgets()
        
        # Initialiser le traitement asynchrone
        self._setup_async_processing()
        
        # Précalculer et mettre en cache les informations des clients
        try:
            self._cache_client_data()
        except Exception as e:
            # Gestion défensive des erreurs
            logger.error(f"Erreur lors de la mise en cache des données clients: {e}")
            # S'assurer que le cache est au moins vide mais initialisé
            self.client_names_cache = {}
        
        # Créer les attributs pour les modèles personnalisés, s'ils n'existent pas déjà
        if not hasattr(self.model, 'custom_folders'):
            self.model.custom_folders = {}
        
        if not hasattr(self.model, 'get_custom_folders'):
            self.model.get_custom_folders = lambda: self.model.custom_folders
        
        if not hasattr(self.model, 'add_custom_folder'):
            setattr(self.model, 'add_custom_folder', self._add_custom_folder_adapter)
        
        if not hasattr(self.model, 'rename_custom_folder'):
            setattr(self.model, 'rename_custom_folder', self._rename_custom_folder_adapter)
        
        if not hasattr(self.model, 'delete_custom_folder'):
            setattr(self.model, 'delete_custom_folder', self._delete_custom_folder_adapter)
        
        if not hasattr(self.model, 'get_documents_by_custom_folder'):
            setattr(self.model, 'get_documents_by_custom_folder', self._get_documents_by_custom_folder_adapter)
        
        if not hasattr(self.model, 'document_in_custom_folder'):
            setattr(self.model, 'document_in_custom_folder', self._document_in_custom_folder_adapter)
        
        # Configurer la recherche en temps réel
        self._setup_search()
        
        logger.info("DocumentView moderne initialisée")
    
    def _init_doc_analyzer(self):
        """
        Initialise le module doc_analyzer de manière sécurisée
        """
        try:
            # Ajouter le répertoire parent au PYTHONPATH
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            # Importer et initialiser DocumentAnalyzer
            from doc_analyzer.analyzer import DocumentAnalyzer
            self.doc_analyzer = DocumentAnalyzer()
            return True
        except ImportError as e:
            logger = logging.getLogger("VynalDocsAutomator")
            logger.error(f"Impossible d'importer le module doc_analyzer: {e}")
            return False
        except Exception as e:
            logger = logging.getLogger("VynalDocsAutomator")
            logger.error(f"Erreur lors de l'initialisation du doc_analyzer: {e}")
            return False
    
    def _setup_async_processing(self):
        """
        Configure le traitement asynchrone des documents
        """
        import threading
        import queue
        
        # Créer une file d'attente de traitement
        self.loading_queue = queue.Queue()
        
        # Démarrer un thread de surveillance de la file d'attente
        def queue_worker():
            while True:
                try:
                    # Récupérer une tâche de la file d'attente
                    task, args = self.loading_queue.get()
                    # Exécuter la tâche
                    task(*args)
                    # Marquer la tâche comme terminée
                    self.loading_queue.task_done()
                except Exception as e:
                    logger = logging.getLogger("VynalDocsAutomator")
                    logger.error(f"Erreur dans le thread de traitement: {e}")
                    # Continuer malgré l'erreur
                    continue
        
        # Démarrer le thread de traitement
        worker_thread = threading.Thread(target=queue_worker, daemon=True)
        worker_thread.start()
    
    def _cache_client_data(self):
        """Précharge et met en cache les données des clients pour un accès rapide - Version corrigée"""
        try:
            # Vérifier si la propriété model existe
            if not hasattr(self, 'model'):
                logger.error("Modèle non initialisé")
                self.client_names_cache = {}
                return
            
            # Vérifier si clients existe dans le modèle
            if not hasattr(self.model, 'clients') or self.model.clients is None:
                logger.warning("Liste de clients non disponible dans le modèle")
                self.client_names_cache = {}
                return
            
            # Nettoyer le cache existant
            self._cleanup_client_cache()
            
            # Ajouter des logs de débogage pour mieux comprendre la structure
            logger.debug(f"Type de la structure clients: {type(self.model.clients)}")
            
            # Initialiser le cache
            self.client_names_cache = {}
            
            # Traitement différent selon le type de la structure
            if isinstance(self.model.clients, list):
                # Pour une liste de clients
                for client in self.model.clients:
                    client_id = client.get("id")
                    client_name = client.get("name", "Inconnu")
                    
                    if client_id:
                        self.client_names_cache[client_id] = client_name
                        logger.debug(f"Client mis en cache (liste): ID={client_id}, Nom={client_name}")
            
            elif isinstance(self.model.clients, dict):
                # Pour un dictionnaire de clients
                for client_id, client in self.model.clients.items():
                    if isinstance(client, dict):  # Vérifier que c'est bien un dictionnaire
                        client_name = client.get("name", "Inconnu")
                        self.client_names_cache[client_id] = client_name
                        logger.debug(f"Client mis en cache (dict): ID={client_id}, Nom={client_name}")
                    else:
                        logger.warning(f"Structure client invalide pour ID={client_id}: {type(client)}")
            
            else:
                logger.warning(f"Structure clients non reconnue: {type(self.model.clients)}")
            
            # Afficher un résumé du cache
            logger.info(f"Cache clients mis à jour - Nombre de clients: {len(self.client_names_cache)}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise en cache des données clients: {e}")
            # S'assurer que le cache est au moins vide mais initialisé
            self.client_names_cache = {}
    
    def _cleanup_client_cache(self):
        """Nettoie le cache des clients en supprimant les entrées obsolètes"""
        if not hasattr(self, 'client_names_cache') or not self.client_names_cache:
            return
        
        # Liste des IDs à supprimer
        to_remove = []
        
        # Vérifier chaque client dans le cache
        for client_id in self.client_names_cache:
            client_exists = False
            if isinstance(self.model.clients, list):
                client_exists = any(c.get('id') == client_id for c in self.model.clients)
            elif isinstance(self.model.clients, dict):
                client_exists = client_id in self.model.clients
            
            if not client_exists:
                to_remove.append(client_id)
        
        # Supprimer les entrées obsolètes
        for client_id in to_remove:
            logger.debug(f"Suppression du client {client_id} du cache (obsolète)")
            del self.client_names_cache[client_id]
        
        if to_remove:
            logger.info(f"Cache nettoyé : {len(to_remove)} entrées obsolètes supprimées")
    
    def create_widgets(self):
        """
        Crée les widgets de la vue avec un style moderne
        """
        # Barre d'outils
        self.toolbar = ctk.CTkFrame(self.frame)
        self.toolbar.pack(fill=ctk.X, pady=10)
        
        # Bouton Nouveau document
        self.new_doc_btn = ctk.CTkButton(
            self.toolbar,
            text="+ Nouveau document",
            command=self.new_document
        )
        self.new_doc_btn.pack(side=ctk.LEFT, padx=10)
        
        # Bouton Retour (initialement caché)
        self.back_btn = ctk.CTkButton(
            self.toolbar,
            text="Retour",
            command=self.handle_back
        )
        
        # Indicateur de chargement
        self.loading_label = ctk.CTkLabel(
            self.toolbar,
            text="Chargement...",
            text_color="#3498db",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        
        # Recherche
        self.search_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.search_frame.pack(side=ctk.RIGHT, padx=10)
        
        self.search_var.trace("w", lambda name, index, mode: self.debounced_filter_documents())
        
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Rechercher un document...",
            width=200,
            textvariable=self.search_var
        )
        self.search_entry.pack(side=ctk.LEFT)
        
        # Ajouter un bouton de réinitialisation de la recherche
        self.clear_search_btn = ctk.CTkButton(
            self.search_frame,
            text="✕",
            width=25,
            height=25,
            fg_color="transparent",
            hover_color="#E0E0E0",
            command=self._clear_search
        )
        self.clear_search_btn.pack(side=ctk.LEFT, padx=(2, 0))
        
        # Filtres supplémentaires (masqués dans la vue dossiers)
        self._setup_filters()
        
        # Zone principale de contenu
        self.content_frame = ctk.CTkScrollableFrame(self.frame)
        self.content_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Message si aucun document
        self.no_documents_label = ctk.CTkLabel(
            self.content_frame,
            text="Aucun document disponible. Créez un nouveau document pour commencer.",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color="gray"
        )
        
        # Grille de documents
        self.documents_grid = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Grille de dossiers
        self.folders_grid = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Configurer les grilles pour avoir 3 colonnes
        for grid in [self.documents_grid, self.folders_grid]:
            for i in range(3):
                grid.columnconfigure(i, weight=1)
        
        # Ajouter les contrôles de pagination (initialement cachés)
        self.pagination_frame = ctk.CTkFrame(self.frame)
        
        self.prev_page_button = ctk.CTkButton(
            self.pagination_frame,
            text="◀ Précédent",
            command=self._previous_page,
            width=100,
            font=ctk.CTkFont(size=12)
        )
        self.prev_page_button.pack(side=ctk.LEFT, padx=5)
        
        self.pagination_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Page 1/1",
            font=ctk.CTkFont(size=12)
        )
        self.pagination_label.pack(side=ctk.LEFT, padx=10)
        
        self.next_page_button = ctk.CTkButton(
            self.pagination_frame,
            text="Suivant ▶",
            command=self._next_page,
            width=100,
            font=ctk.CTkFont(size=12)
        )
        self.next_page_button.pack(side=ctk.LEFT, padx=5)
        
        # Afficher la vue des dossiers par défaut
        self.show_folders_view()
    
    def _setup_filters(self):
        """Configure les filtres pour les documents"""
        # Cadre pour les filtres
        self.filter_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        
        # Filtre client
        client_label = ctk.CTkLabel(
            self.filter_frame,
            text="Client:",
            font=ctk.CTkFont(size=12)
        )
        client_label.pack(side=ctk.LEFT, padx=(0, 5))
        
        self.client_combobox = ctk.CTkComboBox(
            self.filter_frame,
            values=["Tous les clients"],
            variable=self.client_var,
            width=150,
            command=self.debounced_filter_documents
        )
        self.client_combobox.pack(side=ctk.LEFT, padx=5)
        
        # Filtre type
        type_label = ctk.CTkLabel(
            self.filter_frame,
            text="Type:",
            font=ctk.CTkFont(size=12)
        )
        type_label.pack(side=ctk.LEFT, padx=(10, 5))
        
        self.type_combobox = ctk.CTkComboBox(
            self.filter_frame,
            values=["Tous les types"],
            variable=self.type_var,
            width=150,
            command=self.debounced_filter_documents
        )
        self.type_combobox.pack(side=ctk.LEFT, padx=5)
        
        # Filtre par date
        date_label = ctk.CTkLabel(
            self.filter_frame,
            text="Date:",
            font=ctk.CTkFont(size=12)
        )
        date_label.pack(side=ctk.LEFT, padx=(10, 5))
        
        date_options = [
            "Toutes",
            "Aujourd'hui",
            "Cette semaine",
            "Ce mois",
            "Cette année"
        ]
        
        self.date_menu = ctk.CTkOptionMenu(
            self.filter_frame,
            values=date_options,
            variable=self.date_filter_var,
            width=150,
            command=self.debounced_filter_documents
        )
        self.date_menu.pack(side=ctk.LEFT, padx=5)
        
        # Initialiser les valeurs des filtres
        self._update_filter_values()
        
        # Ajouter un log pour aider au débogage
        logger.info("Filtres configurés avec succès")
    
    def show_folders_view(self):
        """Affiche la vue des dossiers"""
        # Réinitialiser la sélection des documents
        self.selected_documents = []
        self.update_selection_ui()
        
        # Réinitialiser la page courante
        self.current_page = 0
        
        # Cacher le bouton retour et le réinitialiser
        self.back_btn.pack_forget()
        self.back_btn.configure(text="Retour")
        
        # Cacher le titre du dossier s'il existe
        if hasattr(self, 'folder_title_label'):
            self.folder_title_label.pack_forget()
        
        # Cacher les filtres spécifiques
        self.filter_frame.pack_forget()
        
        # Cacher les contrôles de pagination
        self.pagination_frame.pack_forget()
        
        # Réinitialiser le dossier sélectionné
        self.selected_folder = None
        self.current_subfolder = None
        
        # Nettoyer la vue
        self.documents_grid.pack_forget()
        self.no_documents_label.pack_forget()
        
        # Afficher la grille des dossiers
        self.folders_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        
        # Nettoyer la grille
        for widget in self.folders_grid.winfo_children():
            widget.destroy()
        
        # Créer les cards des dossiers
        self._create_folder_cards()
    
    def _create_folder_cards(self):
        """Crée les cards de dossier pour la vue principale"""
        # Déterminer les statistiques de documents par type
        stats = self._get_document_stats()
        
        # Créer les cards des dossiers
        row, col = 0, 0
        for folder_id, folder_name in self.document_folders.items():
            count = stats.get(folder_id, 0)
            self.create_folder_card(folder_id, folder_name, count, row, col)
            col += 1
            if col >= 2:  # 2 cards par ligne
                col = 0
                row += 1
    
    def _get_document_stats(self):
        """Calcule les statistiques des documents pour chaque type de dossier"""
        stats = {
            "date": 0,
            "type": 0,
            "client": 0,
            "custom": 0
        }
        
        # Compter tous les documents
        stats["date"] = len(self.model.documents)
        
        # Compter par type
        doc_types = {}
        for doc in self.model.documents:
            doc_type = doc.get("type", "").lower()
            if doc_type:
                if doc_type not in doc_types:
                    doc_types[doc_type] = 0
                doc_types[doc_type] += 1
        stats["type"] = len(doc_types) if doc_types else 0
        
        # Compter par client
        client_docs = {}
        for doc in self.model.documents:
            client_id = doc.get("client_id", "")
            if client_id:
                if client_id not in client_docs:
                    client_docs[client_id] = 0
                client_docs[client_id] += 1
        stats["client"] = len(client_docs) if client_docs else 0
        
        # Compter les dossiers personnalisés
        custom_folders = self.model.get_custom_folders() if hasattr(self.model, 'get_custom_folders') else {}
        stats["custom"] = len(custom_folders)
        
        return stats
    
    def create_folder_card(self, folder_id, folder_name, count, row, col):
        """Crée une card pour un dossier - version corrigée"""
        # Créer le cadre principal avec une taille fixe
        card = ctk.CTkFrame(
            self.folders_grid,
            width=200,  # Largeur fixe
            height=200,  # Hauteur fixe
            corner_radius=10,
            border_width=0,
            fg_color=("gray95", "gray15")  # Couleur de fond adaptative
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)  # Empêcher le redimensionnement automatique
        
        # Créer un cadre pour le contenu
        content_frame = ctk.CTkFrame(
            card,
            fg_color="transparent",
            width=180,  # Largeur fixe
            height=180  # Hauteur fixe
        )
        content_frame.pack(expand=True, fill="both", padx=10, pady=10)
        content_frame.pack_propagate(False)  # Empêcher le redimensionnement automatique
        
        # Ajouter l'icône
        icon_label = ctk.CTkLabel(
            content_frame,
            text=self.folder_icons.get(folder_id, "📁"),
            font=ctk.CTkFont(size=48)  # Taille d'icône
        )
        icon_label.pack(pady=(20, 10))
        
        # Ajouter le nom du dossier
        name_label = ctk.CTkLabel(
            content_frame,
            text=folder_name,
            font=ctk.CTkFont(size=16, weight="bold"),  # Taille de police
            wraplength=160  # Largeur de texte
        )
        name_label.pack(pady=(0, 10))
        
        # Ajouter le compteur
        count_label = ctk.CTkLabel(
            content_frame,
            text=f"{count} document{'s' if count != 1 else ''}",
            font=ctk.CTkFont(size=12),  # Taille de police
            text_color=("gray50", "gray70")
        )
        count_label.pack(pady=(0, 20))
        
        # Gestionnaires d'événements
        def handle_click(event, folder=folder_id):
            self.show_folder_documents(folder)
        
        def handle_enter(event):
            card.configure(border_width=2, border_color=("gray70", "gray30"))
            event.widget.configure(cursor="hand2")
        
        def handle_leave(event):
            card.configure(border_width=0)
            event.widget.configure(cursor="")
        
        # Lier les événements au cadre et à tous les widgets à l'intérieur
        for widget in [card, content_frame, icon_label, name_label, count_label]:
            widget.bind("<Button-1>", handle_click)
            widget.bind("<Enter>", handle_enter)
            widget.bind("<Leave>", handle_leave)
        
        return card
    
    def show_folder_documents(self, folder_id):
        """Affiche le contenu d'un dossier spécifique"""
        # Réinitialiser la sélection des documents
        self.selected_documents = []
        self.update_selection_ui()
        
        self.selected_folder = folder_id
        self.current_subfolder = None
        
        # Masquer la vue des dossiers
        self.folders_grid.pack_forget()
        
        # Afficher le bouton retour
        self.back_btn.pack(side=ctk.LEFT, padx=10, before=self.new_doc_btn)
        
        folder_name = self.document_folders.get(folder_id, "Documents")
        folder_icon = self.folder_icons.get(folder_id, "📁")
        
        # Ajouter le titre du dossier
        if not hasattr(self, 'folder_title_label'):
            self.folder_title_label = ctk.CTkLabel(
                self.toolbar,
                text=f"{folder_icon} {folder_name}",
                font=ctk.CTkFont(size=16, weight="bold")
            )
        else:
            self.folder_title_label.configure(
                text=f"{folder_icon} {folder_name}"
            )
        self.folder_title_label.pack(side=ctk.LEFT, padx=20, after=self.back_btn)
        
        # Comportement différent selon le type de dossier
        if folder_id == "date":
            self._show_date_folders()
        elif folder_id == "type":
            self._show_type_folders()
        elif folder_id == "client":
            self._show_client_folders()
        elif folder_id == "custom":
            self._show_custom_folders()
        else:
            # Pour les autres dossiers, afficher directement les documents
            documents = self._get_filtered_documents()
            self._display_documents(documents)
            
            # Afficher les contrôles de pagination si nécessaire
            if len(documents) > self.page_size:
                self.pagination_frame.pack(fill=ctk.X, pady=5)
                self._update_pagination_controls(len(documents))
            else:
                self.pagination_frame.pack_forget()
    
    def _show_date_folders(self):
        """Affiche les dossiers organisés par date (avec regroupement par mois)"""
        # Nettoyer la vue
        self.documents_grid.pack_forget()
        self.no_documents_label.pack_forget()
        
        # Afficher la grille des dossiers
        self.folders_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        
        # Nettoyer la grille
        for widget in self.folders_grid.winfo_children():
            widget.destroy()
            
        # Analyser les documents par année-mois
        years = {}  # Dictionnaire pour regrouper par année
        months = {}  # Dictionnaire pour regrouper par mois
        current_year = datetime.now().year
        
        for doc in self.model.documents:
            date_str = doc.get("date", "")
            if date_str and len(date_str) >= 7:  # Format YYYY-MM
                year = date_str[:4]  # Prend "YYYY"
                year_month = date_str[:7]  # Prend "YYYY-MM"
                month = date_str[5:7]
                
                # Regrouper par année
                if year not in years:
                    years[year] = []
                years[year].append(doc)
                
                # Regrouper par mois
                if year_month not in months:
                    months[year_month] = {
                        "docs": [],
                        "year": int(year),
                        "month": month,
                    }
                months[year_month]["docs"].append(doc)
        
        # Noms des mois en français
        months_names = {
            "01": "Janvier", "02": "Février", "03": "Mars",
            "04": "Avril", "05": "Mai", "06": "Juin",
            "07": "Juillet", "08": "Août", "09": "Septembre",
            "10": "Octobre", "11": "Novembre", "12": "Décembre"
        }
        
        # Trier les années et les mois par ordre décroissant (plus récent d'abord)
        sorted_years = sorted(years.keys(), reverse=True)
        sorted_months = sorted(months.keys(), reverse=True)
        
        if not sorted_months:
            # Aucun document avec date
            self.no_documents_label.configure(
                text="Aucun document avec date disponible."
            )
            self.no_documents_label.pack(pady=20)
            return
        
        # Créer les cards des mois, groupées par année
        row, col = 0, 0
        current_year = None
        
        for year_month in sorted_months:
            month_data = months[year_month]
            year = str(month_data["year"])
            month = month_data["month"]
            docs = month_data["docs"]
            
            # Si on change d'année, ajouter un séparateur
            if year != current_year:
                if col != 0:  # Si on n'est pas au début d'une ligne
                    row += 1
                col = 0
                
                # Ajouter le titre de l'année
                year_label = ctk.CTkLabel(
                    self.folders_grid,
                    text=f"Année {year}",
                    font=ctk.CTkFont(size=16, weight="bold")
                )
                year_label.grid(row=row, column=0, columnspan=3, sticky="w", padx=10, pady=(20, 10))
                row += 1
                current_year = year
            
            # Trier les documents du mois du plus récent au plus ancien
            docs.sort(key=lambda x: (x.get('date', ''), x.get('created_at', '')), reverse=True)
            
            # Formater pour l'affichage: "Janvier 2023", "Février 2023", etc.
            month_name = months_names.get(month, month)
            display_name = f"{month_name} {year}"
            
            self._create_month_folder_card(year_month, display_name, len(docs), row, col)
            col += 1
            if col >= 3:  # 3 cards par ligne
                col = 0
                row += 1
    
    def _create_month_folder_card(self, year_month, display_name, count, row, col):
        """Crée une card pour un dossier de mois - version corrigée"""
        # Cadre principal avec taille fixe
        card = ctk.CTkFrame(self.folders_grid)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.configure(width=200, height=200)
        card.grid_propagate(False)
        
        # Conteneur interne pour centrer le contenu
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Icône du mois
        icon_label = ctk.CTkLabel(
            content_frame,
            text="📅",
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=(20, 10))
        
        # Nom du mois
        name_label = ctk.CTkLabel(
            content_frame,
            text=display_name,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        name_label.pack(pady=(0, 10))
        
        # Nombre de documents
        count_label = ctk.CTkLabel(
            content_frame,
            text=f"{count} document{'s' if count > 1 else ''}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        count_label.pack(pady=(0, 20))
        
        # Configurer les gestionnaires d'événements
        def handle_click(event, ym=year_month):
            self.show_documents_by_month(ym, display_name)
        
        def handle_enter(event):
            card.configure(border_width=2)
            event.widget.configure(cursor="hand2")
        
        def handle_leave(event):
            card.configure(border_width=0)
            event.widget.configure(cursor="")
        
        # Lier les événements au cadre et à tous les widgets à l'intérieur
        for widget in [card, content_frame, icon_label, name_label, count_label]:
            widget.bind("<Button-1>", handle_click)
            widget.bind("<Enter>", handle_enter)
            widget.bind("<Leave>", handle_leave)
        
        return card
    
    def show_documents_by_month(self, year_month, display_name):
        """Affiche les documents pour un mois spécifique"""
        # Réinitialiser la sélection des documents
        self.selected_documents = []
        self.update_selection_ui()
        
        # Ajouter un log pour aider au débogage
        logger.info(f"Affichage des documents pour le mois: {display_name} ({year_month})")
        
        # Mettre à jour le chemin dans l'interface
        folder_name = self.document_folders.get(self.selected_folder, "Documents")
        self.folder_title_label.configure(
            text=f"📅 {folder_name} > {display_name}"
        )
        
        # Définir le mois comme sous-dossier courant
        self.current_subfolder = year_month
        
        # Filtrer les documents pour ce mois
        filtered_docs = []
        for doc in self.model.documents:
            doc_date = doc.get("date", "")
            if doc_date and doc_date.startswith(year_month):  # year_month est au format "YYYY-MM"
                filtered_docs.append(doc)
        
        # Ajouter un log de débogage
        logger.info(f"Nombre de documents trouvés pour le mois {display_name}: {len(filtered_docs)}")
        
        # Afficher les documents
        self._display_documents(filtered_docs)
        
        # Afficher les contrôles de pagination si nécessaire
        if len(filtered_docs) > self.page_size:
            self.pagination_frame.pack(fill=ctk.X, pady=5)
            self._update_pagination_controls(len(filtered_docs))
        else:
            self.pagination_frame.pack_forget()
    
    def _show_type_folders(self):
        """Affiche les dossiers organisés par type de document"""
        # Nettoyer la vue
        self.documents_grid.pack_forget()
        self.no_documents_label.pack_forget()
        
        # Afficher la grille des dossiers
        self.folders_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        
        # Nettoyer la grille
        for widget in self.folders_grid.winfo_children():
            widget.destroy()
            
        # Analyser les documents par type
        types = {}
        for doc in self.model.documents:
            # Extraire le type
            doc_type = doc.get("type", "").lower()
            if not doc_type:
                doc_type = "autre"
            
            # Initialiser la liste si nécessaire
            if doc_type not in types:
                types[doc_type] = []
            
            # Ajouter le document à la liste
            types[doc_type].append(doc)
        
        if not types:
            # Aucun document avec type
            self.no_documents_label.configure(
                text="Aucun document classé par type disponible."
            )
            self.no_documents_label.pack(pady=20)
            return
        
        # Créer les cards des types
        row, col = 0, 0
        for doc_type, docs in sorted(types.items()):
            self._create_type_folder_card(doc_type, len(docs), row, col)
            col += 1
            if col >= 3:  # 3 cards par ligne
                col = 0
                row += 1
    
    def _create_type_folder_card(self, doc_type, count, row, col):
        """Crée une card pour un dossier de type - version corrigée"""
        # Cadre principal avec taille fixe
        card = ctk.CTkFrame(self.folders_grid)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.configure(width=200, height=200)
        card.grid_propagate(False)  # CRUCIAL: empêche le redimensionnement
        
        # Conteneur interne pour centrer le contenu
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Icône du type
        type_icons = {
            "contrat": "📝",
            "facture": "💰",
            "proposition": "📊",
            "rapport": "📈",
            "lettre": "✉️",
            "courrier": "✉️",
            "attestation": "🔖",
            "autre": "📄"
        }
        
        icon = type_icons.get(doc_type, "📄")
        
        icon_label = ctk.CTkLabel(
            content_frame,
            text=icon,
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=(20, 10))
        
        # Nom du type
        name_label = ctk.CTkLabel(
            content_frame,
            text=doc_type.capitalize(),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        name_label.pack(pady=(0, 10))
        
        # Nombre de documents
        count_label = ctk.CTkLabel(
            content_frame,
            text=f"{count} document{'s' if count > 1 else ''}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        count_label.pack(pady=(0, 20))
        
        # Configurer les gestionnaires d'événements
        def handle_click(event, type_name=doc_type):
            # Ajouter un log pour aider au débogage
            logger.info(f"Clic sur le dossier de type: '{type_name}'")
            self.show_documents_by_type(type_name)
        
        def handle_enter(event):
            card.configure(border_width=2)
            event.widget.configure(cursor="hand2")
        
        def handle_leave(event):
            card.configure(border_width=0)
            event.widget.configure(cursor="")
        
        # Lier les événements au cadre et à tous les widgets à l'intérieur
        for widget in [card, content_frame, icon_label, name_label, count_label]:
            widget.bind("<Button-1>", handle_click)
            widget.bind("<Enter>", handle_enter)
            widget.bind("<Leave>", handle_leave)
        
        return card
    
    def show_documents_by_type(self, doc_type):
        """Affiche les documents pour un type spécifique"""
        # Réinitialiser la sélection des documents
        self.selected_documents = []
        self.update_selection_ui()
        
        # Ajouter un log pour aider au débogage
        logger.info(f"Affichage des documents de type: '{doc_type}'")
        
        # Mettre à jour le chemin dans l'interface
        folder_name = self.document_folders.get(self.selected_folder, "Documents")
        type_display = doc_type.capitalize() if doc_type else "Sans type"
        self.folder_title_label.configure(
            text=f"📑 {folder_name} > {type_display}"
        )
        
        # Définir le type comme sous-dossier courant
        self.current_subfolder = doc_type
        
        # Filtrer les documents pour ce type
        filtered_docs = []
        for doc in self.model.documents:
            current_type = doc.get("type", "").lower()
            if current_type == doc_type.lower():
                filtered_docs.append(doc)
        
        # Ajouter un log de débogage
        logger.info(f"Nombre de documents trouvés pour le type '{doc_type}': {len(filtered_docs)}")
        
        # Afficher les documents
        self._display_documents(filtered_docs)
        
        # Afficher les contrôles de pagination si nécessaire
        if len(filtered_docs) > self.page_size:
            self.pagination_frame.pack(fill=ctk.X, pady=5)
            self._update_pagination_controls(len(filtered_docs))
        else:
            self.pagination_frame.pack_forget()
    
    def _show_client_folders(self):
        """Affiche les dossiers organisés par client"""
        # Nettoyer la vue
        self.documents_grid.pack_forget()
        self.no_documents_label.pack_forget()
        
        # Afficher la grille des dossiers
        self.folders_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        
        # Nettoyer la grille
        for widget in self.folders_grid.winfo_children():
            widget.destroy()
            
        # Récupérer les IDs des clients valides
        valid_client_ids = []
        if isinstance(self.model.clients, list):
            valid_client_ids = [c.get("id") for c in self.model.clients if c.get("id")]
        elif isinstance(self.model.clients, dict):
            valid_client_ids = list(self.model.clients.keys())
        
        # Initialiser le dictionnaire des clients avec les clients valides uniquement
        clients = {}
        for client_id in valid_client_ids:
            client_name = self._get_client_name_cached(client_id)
            if client_name != "Client inconnu":  # Ne pas inclure les clients inconnus
                clients[client_id] = {
                    "docs": [],
                    "name": client_name
                }
        
        # Ajouter les documents aux clients valides uniquement
        for doc in self.model.documents:
            client_id = doc.get("client_id")
            if client_id in clients:  # N'ajouter que si le client est valide
                clients[client_id]["docs"].append(doc)
        
        # Si aucun client valide
        if not clients:
            self.no_documents_label.configure(
                text="Aucun client disponible."
            )
            self.no_documents_label.pack(pady=20)
            return
        
        # Trier les clients par nom
        sorted_clients = sorted(
            [(cid, info["name"], info["docs"]) for cid, info in clients.items()],
            key=lambda x: x[1].lower()  # Tri insensible à la casse
        )
        
        # Créer les cards des clients
        row, col = 0, 0
        for client_id, client_name, docs in sorted_clients:
            self._create_client_folder_card(client_id, client_name, len(docs), row, col)
            col += 1
            if col >= 3:  # 3 cards par ligne
                col = 0
                row += 1
    
    def _create_client_folder_card(self, client_id, client_name, count, row, col):
        """Crée une card pour un dossier client - version corrigée"""
        # Créer le cadre principal avec une taille fixe
        card = ctk.CTkFrame(
            self.folders_grid,
            width=200,  # Largeur fixe
            height=200,  # Hauteur fixe
            corner_radius=10,
            border_width=0,
            fg_color=("gray95", "gray15")  # Couleur de fond adaptative
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)  # Empêcher le redimensionnement automatique
        
        # Créer un cadre pour le contenu
        content_frame = ctk.CTkFrame(
            card,
            fg_color="transparent",
            width=180,  # Largeur fixe
            height=180  # Hauteur fixe
        )
        content_frame.pack(expand=True, fill="both", padx=10, pady=10)
        content_frame.pack_propagate(False)  # Empêcher le redimensionnement automatique
        
        # Ajouter l'icône
        icon_label = ctk.CTkLabel(
            content_frame,
            text="👥",
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=(20, 10))
        
        # Ajouter le nom du client
        name_label = ctk.CTkLabel(
            content_frame,
            text=client_name,
            font=ctk.CTkFont(size=16, weight="bold"),
            wraplength=160
        )
        name_label.pack(pady=(0, 10))
        
        # Ajouter le compteur
        count_label = ctk.CTkLabel(
            content_frame,
            text=f"{count} document{'s' if count != 1 else ''}",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        count_label.pack(pady=(0, 20))
        
        # Gestionnaires d'événements
        def handle_click(event, cid=client_id, cname=client_name):
            # Ajouter un log pour aider au débogage
            logger.info(f"Clic sur le dossier client: '{cname}' (ID: {cid})")
            self.show_documents_by_client(cid, cname)
        
        def handle_enter(event):
            card.configure(border_width=2, border_color=("gray70", "gray30"))
            event.widget.configure(cursor="hand2")
        
        def handle_leave(event):
            card.configure(border_width=0)
            event.widget.configure(cursor="")
        
        # Lier les événements au cadre et à tous les widgets à l'intérieur
        for widget in [card, content_frame, icon_label, name_label, count_label]:
            widget.bind("<Button-1>", handle_click)
            widget.bind("<Enter>", handle_enter)
            widget.bind("<Leave>", handle_leave)
        
        return card
    
    def show_documents_by_client(self, client_id, client_name):
        """Affiche les documents pour un client spécifique"""
        # Réinitialiser la sélection des documents
        self.selected_documents = []
        self.update_selection_ui()
        
        # Ajouter un log pour aider au débogage
        logger.info(f"Affichage des documents pour le client: '{client_name}' ({client_id})")
        
        # Mettre à jour le chemin dans l'interface
        folder_name = self.document_folders.get(self.selected_folder, "Documents")
        self.folder_title_label.configure(
            text=f"👤 {folder_name} > {client_name}"
        )
        
        # Définir le client comme sous-dossier courant
        self.current_subfolder = client_id
        
        # Filtrer les documents pour ce client
        filtered_docs = []
        for doc in self.model.documents:
            if doc.get("client_id") == client_id:
                filtered_docs.append(doc)
        
        # Ajouter un log de débogage
        logger.info(f"Nombre de documents trouvés pour le client '{client_name}': {len(filtered_docs)}")
        
        # Afficher les documents
        self._display_documents(filtered_docs)
        
        # Afficher les contrôles de pagination si nécessaire
        if len(filtered_docs) > self.page_size:
            self.pagination_frame.pack(fill=ctk.X, pady=5)
            self._update_pagination_controls(len(filtered_docs))
        else:
            self.pagination_frame.pack_forget()
    
    def _show_custom_folders(self):
        """Affiche les dossiers personnalisés"""
        # Nettoyer la vue
        self.documents_grid.pack_forget()
        self.no_documents_label.pack_forget()
        
        # Afficher la grille des dossiers
        self.folders_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        
        # Nettoyer la grille
        for widget in self.folders_grid.winfo_children():
            widget.destroy()
            
        # Récupérer les dossiers personnalisés
        custom_folders = self.model.get_custom_folders()
        
        if not custom_folders:
            # Aucun dossier personnalisé
            self.no_documents_label.configure(
                text="Aucun dossier personnalisé disponible."
            )
            self.no_documents_label.pack(pady=20)
            return
        
        # Créer les cards des dossiers personnalisés
        row, col = 0, 0
        for folder_id, folder_data in sorted(custom_folders.items(), key=lambda x: x[1]["name"].lower()):
            self._create_custom_folder_card(
                folder_id,
                folder_data["name"],
                len(folder_data.get("documents", [])),
                row,
                col
            )
            col += 1
            if col >= 2:  # 2 cards par ligne
                col = 0
                row += 1
    
    def _create_custom_folder_card(self, folder_id, folder_name, count, row, col):
        """Crée une card pour un dossier personnalisé - version corrigée"""
        # Cadre principal avec taille fixe
        card = ctk.CTkFrame(self.folders_grid)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.configure(width=200, height=200)
        card.grid_propagate(False)
        
        # Conteneur interne pour centrer le contenu
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Icône du dossier personnalisé
        icon_label = ctk.CTkLabel(
            content_frame,
            text="📁",
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=(20, 10))
        
        # Nom du dossier
        name_label = ctk.CTkLabel(
            content_frame,
            text=folder_name,
            font=ctk.CTkFont(size=16, weight="bold"),
            wraplength=200
        )
        name_label.pack(pady=(0, 10))
        
        # Nombre de documents
        count_label = ctk.CTkLabel(
            content_frame,
            text=f"{count} document{'s' if count > 1 else ''}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        count_label.pack(pady=(0, 20))
        
        # Configurer les gestionnaires d'événements
        def handle_click(event, fid=folder_id, fname=folder_name):
            # Ajouter un log pour aider au débogage
            logger.info(f"Clic sur le dossier personnalisé: '{fname}' (ID: {fid})")
            self.show_documents_by_custom_folder(fid, fname)
        
        def handle_enter(event):
            card.configure(border_width=2)
            event.widget.configure(cursor="hand2")
        
        def handle_leave(event):
            card.configure(border_width=0)
            event.widget.configure(cursor="")
        
        # Lier les événements au cadre et à tous les widgets à l'intérieur
        for widget in [card, content_frame, icon_label, name_label, count_label]:
            widget.bind("<Button-1>", handle_click)
            widget.bind("<Enter>", handle_enter)
            widget.bind("<Leave>", handle_leave)
        
        return card
    
    def create_custom_folder(self):
        """Crée un nouveau dossier personnalisé"""
        from utils.dialog_utils import DialogUtils
        
        # Afficher une boîte de dialogue pour saisir le nom du dossier
        folder_dialog = ctk.CTkInputDialog(
            title="Nouveau dossier",
            text="Entrez le nom du nouveau dossier :"
        )
        folder_name = folder_dialog.get_input()
        
        if folder_name:
            # Ajouter le dossier dans le modèle
            success = self.model.add_custom_folder(folder_name) if hasattr(self.model, 'add_custom_folder') else False
            
            if success:
                # Afficher un message de confirmation
                DialogUtils.show_toast(self.parent, f"Dossier '{folder_name}' créé avec succès", "success")
                # Rafraîchir la vue
                self._show_custom_folders()
            else:
                DialogUtils.show_message(self.parent, "Erreur", "Impossible de créer le dossier", "error")
    
    def rename_custom_folder(self, folder_id, current_name):
        """Renomme un dossier personnalisé"""
        from utils.dialog_utils import DialogUtils
        
        # Afficher une boîte de dialogue pour saisir le nouveau nom
        folder_dialog = ctk.CTkInputDialog(
            title="Renommer le dossier",
            text="Entrez le nouveau nom du dossier :"
        )
        folder_dialog.set_text(current_name)
        new_name = folder_dialog.get_input()
        
        if new_name and new_name != current_name:
            # Renommer le dossier dans le modèle
            success = self.model.rename_custom_folder(folder_id, new_name) if hasattr(self.model, 'rename_custom_folder') else False
            
            if success:
                # Afficher un message de confirmation
                DialogUtils.show_toast(self.parent, f"Dossier renommé avec succès", "success")
                # Rafraîchir la vue
                self._show_custom_folders()
            else:
                DialogUtils.show_message(self.parent, "Erreur", "Impossible de renommer le dossier", "error")
    
    def delete_custom_folder(self, folder_id):
        """Supprime un dossier personnalisé"""
        from utils.dialog_utils import DialogUtils
        
        # Demander confirmation
        confirm = DialogUtils.show_confirmation(
            self.parent,
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer ce dossier ?\nLes documents qu'il contient ne seront pas supprimés.",
            lambda: self._confirm_delete_folder(folder_id)
        )
    
    def _confirm_delete_folder(self, folder_id):
        """Confirme la suppression d'un dossier personnalisé"""
        from utils.dialog_utils import DialogUtils
        
        # Supprimer le dossier dans le modèle
        success = self.model.delete_custom_folder(folder_id) if hasattr(self.model, 'delete_custom_folder') else False
        
        if success:
            # Afficher un message de confirmation
            DialogUtils.show_toast(self.parent, "Dossier supprimé avec succès", "success")
            # Rafraîchir la vue
            self._show_custom_folders()
        else:
            DialogUtils.show_message(self.parent, "Erreur", "Impossible de supprimer le dossier", "error")
    
    def show_documents_by_custom_folder(self, folder_id, folder_name):
        """Affiche les documents d'un dossier personnalisé"""
        # Réinitialiser la sélection des documents
        self.selected_documents = []
        self.update_selection_ui()
        
        # Mettre à jour le chemin
        folder_cat = self.document_folders.get(self.selected_folder, "Documents")
        self.folder_title_label.configure(
            text=f"📁 {folder_cat} > {folder_name}"
        )
        
        # Définir le dossier personnalisé comme sous-dossier courant
        self.current_subfolder = folder_id
        
        # Récupérer les documents du dossier
        documents = self.model.get_documents_by_custom_folder(folder_id) if hasattr(self.model, 'get_documents_by_custom_folder') else []
        
        # Afficher les documents
        self._display_documents(documents)
        
        # Afficher les contrôles de pagination si nécessaire
        if len(documents) > self.page_size:
            self.pagination_frame.pack(fill=ctk.X, pady=5)
            self._update_pagination_controls(len(documents))
        else:
            self.pagination_frame.pack_forget()
    
    def _display_documents(self, documents):
        """Affiche les documents dans la grille - version corrigée"""
        # Ajouter des logs pour le débogage
        print(f"Tentative d'affichage de {len(documents)} documents")
        
        # Masquer la grille des dossiers
        self.folders_grid.pack_forget()
        
        # Réinitialiser la page
        self.current_page = 0
        
        # Afficher les filtres spécifiques pour cette vue
        self.filter_frame.pack(side=ctk.RIGHT, padx=10, before=self.search_frame)
        
        # Si aucun document
        if not documents:
            print("Aucun document trouvé - affichage du message")
            self.documents_grid.pack_forget()
            self.no_documents_label.configure(
                text="Aucun document disponible dans ce dossier."
            )
            self.no_documents_label.pack(pady=20)
            return
        
        # Masquer le message "Aucun document"
        self.no_documents_label.pack_forget()
        
        # Afficher la grille des documents
        self.documents_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        
        # Nettoyer la grille
        for widget in self.documents_grid.winfo_children():
            widget.destroy()
        
        # Trier les documents par date et heure de création (du plus récent au plus ancien)
        sorted_documents = sorted(
            documents,
            key=lambda x: (x.get('date', ''), x.get('created_at', '')),
            reverse=True  # True pour trier du plus récent au plus ancien
        )
        
        # Calculer la pagination
        total_docs = len(sorted_documents)
        self.total_documents = total_docs
        
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, total_docs)
        
        paginated_docs = sorted_documents[start_idx:end_idx]
        print(f"Affichage des documents {start_idx+1} à {end_idx} sur {total_docs}")
        
        # Mettre en cache les documents pour cette vue
        key = f"folder_{self.selected_folder}_{self.current_subfolder}"
        self.documents_cache[key] = sorted_documents
        
        # Remplir la grille avec les documents paginés (méthode corrigée)
        self._populate_documents_grid(paginated_docs)
        
        # Afficher les contrôles de pagination si nécessaire
        if total_docs > self.page_size:
            self.pagination_frame.pack(fill=ctk.X, pady=5)
            self._update_pagination_controls(total_docs)
        else:
            self.pagination_frame.pack_forget()
    
    def _populate_documents_grid(self, documents):
        """Remplit la grille avec les documents - version corrigée"""
        if not documents:
            print("Aucun document à afficher")
            return
        
        print(f"Remplissage de la grille avec {len(documents)} documents")
        row, col = 0, 0
        for doc in documents:
            try:
                card = self.create_document_card(doc, row, col)
                card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                
                col += 1
                if col >= 2:  # 2 cartes par ligne
                    col = 0
                    row += 1
            except Exception as e:
                print(f"Erreur lors de la création de la carte pour le document {doc.get('id')}: {e}")
    
    def create_document_card(self, document, row, col):
        """
        Crée une carte pour afficher un document avec dimensions fixes
        """
        # Cadre de la carte avec dimensions fixes
        card = ctk.CTkFrame(self.documents_grid)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.configure(width=240, height=320)  # Dimensions fixes
        card.grid_propagate(False)  # CRUCIAL: empêche le redimensionnement
        
        # Attacher le document à la carte pour pouvoir le retrouver plus tard
        card.document = document
        
        # Conteneur interne pour centrer le contenu
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Case à cocher de sélection
        var = ctk.BooleanVar(value=False)
        checkbox = ctk.CTkCheckBox(
            content_frame, 
            text="", 
            variable=var,
            width=16,
            height=16,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=3,
            command=lambda: self.toggle_document_selection(document, var)
        )
        checkbox.pack(anchor="nw")
        
        # Type de document avec icône
        doc_type = document.get("type", "").lower()
        icon = "📄"  # Par défaut
        
        if "contrat" in doc_type:
            icon = "📝"
        elif "facture" in doc_type:
            icon = "💰"
        elif "proposition" in doc_type:
            icon = "📊"
        elif "rapport" in doc_type:
            icon = "📈"
        elif "lettre" in doc_type or "courrier" in doc_type:
            icon = "✉️"
        elif "attestation" in doc_type:
            icon = "🔖"
        
        type_label = ctk.CTkLabel(
            content_frame,
            text=f"{icon} {doc_type.capitalize() if doc_type else 'Document'}",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        type_label.pack(fill=ctk.X, padx=10, pady=(30, 5))
        
        # Titre du document
        title = document.get("title", "Sans titre")
        if len(title) > 50:  # Limiter la longueur pour l'affichage
            title = title[:47] + "..."
        
        title_label = ctk.CTkLabel(
            content_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=220
        )
        title_label.pack(fill=ctk.X, padx=10, pady=5)
        
        # Icône de prévisualisation (œil) en haut à droite
        preview_label = ctk.CTkLabel(
            content_frame,
            text="👁️",
            font=ctk.CTkFont(size=16),
            cursor="hand2"  # Curseur main pour indiquer que c'est cliquable
        )
        preview_label.place(x=content_frame.winfo_width() - 40, y=10)
        
        # Rendre l'icône cliquable
        def on_preview_click(event):
            self.preview_document(document.get("id"))
        
        preview_label.bind("<Button-1>", on_preview_click)
        preview_label.bind("<Enter>", lambda e: preview_label.configure(text_color=("gray50", "gray70")))
        preview_label.bind("<Leave>", lambda e: preview_label.configure(text_color=("black", "white")))
        
        # Date
        date_label = ctk.CTkLabel(
            content_frame,
            text=f"Date: {document.get('date', 'Non spécifiée')}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        date_label.pack(fill=ctk.X, padx=10, pady=2)
        
        # Client
        client_label = ctk.CTkLabel(
            content_frame,
            text=f"Client: {self._get_client_name_cached(document.get('client_id', ''))}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        client_label.pack(fill=ctk.X, padx=10, pady=2)
        
        # Description (si présente)
        description = document.get("description", "")
        if description:
            if len(description) > 80:
                description = description[:77] + "..."
            
            desc_label = ctk.CTkLabel(
                content_frame,
                text=f"Description: {description}",
                font=ctk.CTkFont(size=12),
                text_color="gray",
                wraplength=220,
                justify="left"
            )
            desc_label.pack(fill=ctk.X, padx=10, pady=2)
        
        # Boutons d'action
        actions_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        actions_frame.pack(fill=ctk.X, padx=10, pady=10, side=ctk.BOTTOM)
        
        # Bouton Ouvrir avec prévisualisation
        open_btn = ctk.CTkButton(
            actions_frame,
            text="Ouvrir",
            width=80,
            height=25,
            command=lambda doc_id=document.get("id"): self.preview_document(doc_id)
        )
        open_btn.pack(side=ctk.LEFT, padx=5)
        
        # Bouton Télécharger
        download_btn = ctk.CTkButton(
            actions_frame,
            text="Télécharger",
            width=100,
            height=25,
            command=lambda doc_id=document.get("id"): self.download_document(doc_id)
        )
        download_btn.pack(side=ctk.RIGHT, padx=5)
        
        return card
    
    def _get_client_name_cached(self, client_id):
        """Récupère le nom du client avec gestion d'erreurs améliorée - Version corrigée"""
        if not client_id:
            logger.debug("ID client vide")
            return "Client inconnu"
        
        # Vérifier si le cache existe et le réinitialiser si nécessaire
        if not hasattr(self, 'client_names_cache') or self.client_names_cache is None:
            logger.warning("Cache clients non initialisé, initialisation...")
            self.client_names_cache = {}
        
        # Vérifier si l'ID est dans le cache
        if client_id in self.client_names_cache:
            # Vérifier si le client existe toujours dans le modèle
            client_still_exists = False
            if isinstance(self.model.clients, list):
                client_still_exists = any(c.get('id') == client_id for c in self.model.clients)
            elif isinstance(self.model.clients, dict):
                client_still_exists = client_id in self.model.clients
            
            # Si le client n'existe plus, supprimer du cache
            if not client_still_exists:
                logger.warning(f"Client {client_id} supprimé du cache car n'existe plus dans la base")
                del self.client_names_cache[client_id]
            else:
                return self.client_names_cache[client_id]
        
        # Tentative de récupération directe
        try:
            if hasattr(self.model, 'clients'):
                if isinstance(self.model.clients, list):
                    for client in self.model.clients:
                        if client.get("id") == client_id:
                            name = client.get("name", "Client inconnu")
                            # Mettre à jour le cache
                            self.client_names_cache[client_id] = name
                            logger.debug(f"Client trouvé et ajouté au cache: {client_id} -> {name}")
                            return name
                
                elif isinstance(self.model.clients, dict):
                    if client_id in self.model.clients:
                        client = self.model.clients[client_id]
                        if isinstance(client, dict):
                            name = client.get("name", "Client inconnu")
                            # Mettre à jour le cache
                            self.client_names_cache[client_id] = name
                            logger.debug(f"Client trouvé et ajouté au cache: {client_id} -> {name}")
                            return name
        
        except Exception as e:
            logger.error(f"Erreur lors de la recherche directe du client {client_id}: {e}")
        
        logger.warning(f"Client ID {client_id} introuvable")
        return "Client inconnu"
    
    def toggle_document_selection(self, document, var):
        """
        Gère la sélection des documents pour suppression
        """
        if var.get():
            if document not in self.selected_documents:
                self.selected_documents.append(document)
        else:
            if document in self.selected_documents:
                self.selected_documents.remove(document)
        
        # Mettre à jour l'interface en fonction du nombre de sélections
        self.update_selection_ui()
    
    def update_selection_ui(self):
        """
        Met à jour l'interface utilisateur selon l'état de sélection
        """
        count = len(self.selected_documents)
        
        if count > 0:
            # Afficher un badge flottant
            self.show_selection_badge(count)
        else:
            # Masquer le badge
            if hasattr(self, 'selection_badge') and self.selection_badge:
                self.selection_badge.pack_forget()
                delattr(self, 'selection_badge')
    
    def show_selection_badge(self, count):
        """
        Affiche un badge avec le nombre d'éléments sélectionnés
        """
        if hasattr(self, 'selection_badge'):
            self.selection_badge.pack_forget()
        
        self.selection_badge = ctk.CTkLabel(
            self.toolbar,
            text=f"{count} sélectionné{'s' if count > 1 else ''}",
            fg_color="#3498db",
            corner_radius=10,
            width=30,
            height=20,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="white"
        )
        self.selection_badge.pack(side=ctk.LEFT, padx=(5, 0))
    
    def delete_selected_documents(self):
        """
        Supprime les documents sélectionnés
        """
        if not self.selected_documents:
            return
        
        # Nombre de documents à supprimer
        count = len(self.selected_documents)
        
        # Demander confirmation
        confirm = DialogUtils.show_confirmation(
            self.parent,
            "Confirmer la suppression",
            f"Êtes-vous sûr de vouloir supprimer {count} document{'s' if count > 1 else ''} ?\n\nCette action est irréversible.",
            lambda: self._confirm_delete_documents()
        )
    
    def _confirm_delete_documents(self):
        """Confirme la suppression des documents sélectionnés"""
        try:
            # IDs des documents à supprimer
            ids_to_delete = [doc.get("id") for doc in self.selected_documents]
            
            # 1. Supprimer les fichiers
            for doc in self.selected_documents:
                file_path = doc.get("file_path", "")
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.error(f"Erreur lors de la suppression du fichier {file_path}: {e}")
            
            # 2. Supprimer les documents du modèle
            self.model.documents = [d for d in self.model.documents if d.get("id") not in ids_to_delete]
            
            # 3. Sauvegarder les changements
            self.model.save_documents()
            
            # 4. Réinitialiser la sélection
            self.selected_documents = []
            self.update_selection_ui()
            
            # 5. Mettre à jour la vue (revenir à la vue des dossiers si tous les documents sont supprimés)
            if self.selected_folder:
                # Vérifier combien de documents restent dans ce dossier/sous-dossier
                remaining_docs = self._get_filtered_documents()
                
                if not remaining_docs:
                    # Si plus aucun document, remonter d'un niveau
                    if self.current_subfolder:
                        # Revenir au niveau du dossier
                        self.show_folder_documents(self.selected_folder)
                    else:
                        # Revenir à la vue des dossiers
                        self.show_folders_view()
                else:
                    # Mettre à jour la vue actuelle
                    self._display_documents(remaining_docs)
            else:
                # Dans la vue principale des dossiers, simplement mettre à jour
                self.show_folders_view()
            
            # 6. Afficher une notification de succès
            DialogUtils.show_toast(self.parent, f"{len(ids_to_delete)} document{'s' if len(ids_to_delete) > 1 else ''} supprimé{'s' if len(ids_to_delete) > 1 else ''} avec succès", "success")
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des documents: {e}")
            DialogUtils.show_message(self.parent, "Erreur", f"Une erreur est survenue lors de la suppression: {str(e)}", "error")
    
    def _get_filtered_documents(self):
        """Récupère les documents filtrés en fonction du dossier et sous-dossier actuel"""
        logger.info(f"Filtrage par dossier: {self.selected_folder}, sous-dossier: {self.current_subfolder}")
        
        documents = self.model.documents
        
        # Si aucun dossier n'est sélectionné, retourner tous les documents
        if self.selected_folder is None:
            logger.info("Aucun dossier sélectionné, retour de tous les documents")
            return documents
        
        # Filtrer par dossier
        if self.selected_folder == "date" and self.current_subfolder:
            # Par date (année ou année-mois)
            filtered_docs = []
            for doc in documents:
                doc_date = doc.get("date", "")
                if doc_date:
                    # Si le sous-dossier est une année (ex: "2024")
                    if len(self.current_subfolder) == 4:
                        if doc_date.startswith(self.current_subfolder):
                            filtered_docs.append(doc)
                    # Si le sous-dossier est une année-mois (ex: "2024-03")
                    elif len(self.current_subfolder) == 7:
                        if doc_date.startswith(self.current_subfolder):
                            filtered_docs.append(doc)
            logger.info(f"Filtré par date '{self.current_subfolder}': {len(filtered_docs)} documents")
            return filtered_docs
        
        elif self.selected_folder == "type" and self.current_subfolder:
            # Par type
            filtered_docs = [doc for doc in documents if doc.get("type", "").lower() == self.current_subfolder.lower()]
            logger.info(f"Filtré par type '{self.current_subfolder}': {len(filtered_docs)} documents")
            return filtered_docs
        
        elif self.selected_folder == "client" and self.current_subfolder:
            # Par client
            filtered_docs = [doc for doc in documents if doc.get("client_id") == self.current_subfolder]
            logger.info(f"Filtré par client '{self.current_subfolder}': {len(filtered_docs)} documents")
            return filtered_docs
        
        # Si aucun sous-dossier n'est sélectionné, retourner tous les documents
        logger.info("Aucun sous-dossier sélectionné, retour de tous les documents")
        return documents
    
    def _update_pagination_controls(self, total_docs=None):
        """Met à jour les contrôles de pagination - version corrigée"""
        if total_docs is not None:
            self.total_documents = total_docs
        
        # Calculer le nombre total de pages
        total_pages = max(1, (self.total_documents + self.page_size - 1) // self.page_size)
        current_page = self.current_page + 1  # Convertir en numérotation 1-based pour l'affichage
        
        # Mettre à jour le texte de pagination
        self.pagination_label.configure(text=f"Page {current_page}/{total_pages}")
        
        # Activer/désactiver les boutons selon la position
        self.prev_page_button.configure(
            state="normal" if self.current_page > 0 else "disabled",
            fg_color="#3498db" if self.current_page > 0 else "#7f8c8d",
            hover_color="#2980b9" if self.current_page > 0 else "#7f8c8d"
        )
        
        self.next_page_button.configure(
            state="normal" if self.current_page < total_pages - 1 else "disabled",
            fg_color="#3498db" if self.current_page < total_pages - 1 else "#7f8c8d",
            hover_color="#2980b9" if self.current_page < total_pages - 1 else "#7f8c8d"
        )
    
    def _previous_page(self):
        """Passe à la page précédente - version corrigée"""
        if self.current_page > 0:
            self.current_page -= 1
            # Ajouter un log pour aider au débogage
            logger.info(f"Navigation vers la page précédente: {self.current_page}")
            self._refresh_current_view()
    
    def _next_page(self):
        """Passe à la page suivante - version corrigée"""
        # Calculer le nombre total de pages
        total_documents = len(self.model.documents)
        total_pages = (total_documents + self.page_size - 1) // self.page_size
        
        if self.current_page < total_pages - 1:
            self.current_page += 1
            # Ajouter un log pour aider au débogage
            logger.info(f"Navigation vers la page suivante: {self.current_page}")
            self._refresh_current_view()
    
    def _refresh_current_view(self):
        """Rafraîchit la vue actuelle - version corrigée"""
        # Ajouter un log pour aider au débogage
        logger.info(f"Rafraîchissement de la vue actuelle (page {self.current_page})")
        
        # Déterminer la méthode à appeler en fonction du dossier sélectionné
        if self.selected_folder == "date":
            self._show_date_folders()
        elif self.selected_folder == "type":
            self._show_type_folders()
        elif self.selected_folder == "client":
            self._show_client_folders()
        elif self.selected_folder == "custom":
            self._show_custom_folders()
    
    def load_documents_async(self):
        """Charge les documents de manière asynchrone"""
        if self.is_loading:
            return
        
        self.is_loading = True
        self.show_loading_indicator()
        
        # Utiliser le threading pour le chargement asynchrone
        threading.Thread(target=self._load_documents_thread, daemon=True).start()
    
    def _load_documents_thread(self):
        """Thread de chargement des documents"""
        try:
            # S'assurer que les documents sont chargés dans le modèle
            self.model.load_documents()
            
            # Si nous sommes dans la vue des dossiers, mettre à jour cette vue
            if self.selected_folder is None:
                self.parent.after(0, self.show_folders_view)
            else:
                # Sinon, récupérer les documents filtrés selon le dossier actuel
                documents = self._get_filtered_documents()
                self.parent.after(0, lambda: self._display_documents(documents))
        except Exception as e:
            logger.error(f"Erreur lors du chargement des documents: {e}")
        finally:
            self.is_loading = False
            self.parent.after(0, self.hide_loading_indicator)
    
    def show_loading_indicator(self):
        """Affiche l'indicateur de chargement"""
        self.loading_label.pack(side=ctk.LEFT, padx=10)
    
    def hide_loading_indicator(self):
        """Masque l'indicateur de chargement"""
        self.loading_label.pack_forget()
    
    def debounced_filter_documents(self):
        """Applique les filtres avec un délai pour éviter les appels trop fréquents"""
        logger.info("Démarrage du filtrage différé...")
        
        # Annuler le timer précédent s'il existe
        if hasattr(self, '_filter_timer'):
            self.parent.after_cancel(self._filter_timer)
        
        # Créer un nouveau timer
        self._filter_timer = self.parent.after(self.debounce_delay, self._apply_document_filters)
        logger.info(f"Timer de filtrage programmé pour {self.debounce_delay}ms")
        
        # Afficher un indicateur visuel que la recherche est en cours
        if hasattr(self, 'search_entry'):
            self.search_entry.configure(placeholder_text="Recherche en cours...")
    
    def _apply_document_filters(self):
        """Applique les filtres aux documents - version corrigée"""
        logger.info("Début application des filtres")
        
        # Mémoriser l'état de navigation actuel
        current_folder = self.selected_folder
        current_subfolder = self.current_subfolder
        logger.info(f"État de navigation actuel: dossier={current_folder}, sous-dossier={current_subfolder}")
        
        # Récupérer les critères de filtrage
        search_text = self.search_var.get().lower() if hasattr(self, 'search_var') else ""
        client_filter = self.client_var.get() if hasattr(self, 'client_var') else "Tous les clients"
        type_filter = self.type_var.get() if hasattr(self, 'type_var') else "Tous les types"
        date_filter = self.date_filter_var.get() if hasattr(self, 'date_filter_var') else "Toutes"
        
        logger.info(f"Critères de filtrage: search='{search_text}', client='{client_filter}', type='{type_filter}', date='{date_filter}'")
        
        # Récupérer les documents de base selon le dossier actuel
        base_documents = self._get_filtered_documents()
        logger.info(f"Nombre de documents de base: {len(base_documents)}")
        
        # Filtre par client
        filtered_docs = base_documents
        if client_filter and client_filter != "Tous les clients":
            # Rechercher le client_id correspondant au nom
            client_id = None
            for cid, name in self.client_names_cache.items():
                if name == client_filter:
                    client_id = cid
                    break
            
            if client_id:
                filtered_docs = [d for d in filtered_docs if d.get("client_id") == client_id]
                logger.info(f"Après filtre client: {len(filtered_docs)} documents")
        
        # Filtre par type
        if type_filter and type_filter != "Tous les types":
            filtered_docs = [d for d in filtered_docs if d.get("type", "").lower() == type_filter.lower()]
            logger.info(f"Après filtre type: {len(filtered_docs)} documents")
        
        # Filtre par date
        if date_filter and date_filter != "Toutes":
            today = datetime.now()
            date_filtered_docs = []
            
            for doc in filtered_docs:
                doc_date = doc.get("date", "")
                if not doc_date:
                    continue
                    
                try:
                    doc_date_obj = datetime.strptime(doc_date, "%Y-%m-%d")
                    
                    if date_filter == "Aujourd'hui":
                        if doc_date_obj.date() == today.date():
                            date_filtered_docs.append(doc)
                    elif date_filter == "Cette semaine":
                        week_start = today - timedelta(days=today.weekday())
                        if doc_date_obj.date() >= week_start.date():
                            date_filtered_docs.append(doc)
                    elif date_filter == "Ce mois":
                        month_start = today.replace(day=1)
                        if doc_date_obj.date() >= month_start.date():
                            date_filtered_docs.append(doc)
                    elif date_filter == "Cette année":
                        year_start = today.replace(month=1, day=1)
                        if doc_date_obj.date() >= year_start.date():
                            date_filtered_docs.append(doc)
                except ValueError:
                    continue
            
            filtered_docs = date_filtered_docs
            logger.info(f"Après filtre date: {len(filtered_docs)} documents")
        
        # Filtre par recherche
        if search_text:
            search_results = []
            for doc in filtered_docs:
                # Rechercher dans tous les champs pertinents
                searchable_fields = [
                    doc.get("title", "").lower(),
                    doc.get("type", "").lower(),
                    doc.get("description", "").lower(),
                    self._get_client_name_cached(doc.get("client_id", "")).lower(),
                    doc.get("date", "").lower()
                ]
                
                # Vérifier si le texte de recherche est présent dans au moins un champ
                if any(search_text in field for field in searchable_fields):
                    search_results.append(doc)
            
            filtered_docs = search_results
            logger.info(f"Après recherche '{search_text}': {len(filtered_docs)} documents")
        
        # Réinitialiser la pagination
        self.current_page = 0
        
        # Restaurer l'état de navigation si nous ne sommes pas dans une recherche
        if not search_text:
            self.selected_folder = current_folder
            self.current_subfolder = current_subfolder
            logger.info("État de navigation restauré")
        else:
            logger.info("Recherche active - navigation conservée")
        
        # Afficher les documents filtrés en utilisant la nouvelle méthode
        self._display_documents_with_context(filtered_docs)
        logger.info("Filtres appliqués avec succès")
    
    def update_view(self):
        """Met à jour la vue avec les données actuelles"""
        # Réinitialiser les documents sélectionnés
        self.selected_documents = []
        self.update_selection_ui()
        
        # Mettre à jour les valeurs des ComboBox
        self._update_filter_values()
        
        # Recharger les clients
        self._cache_client_data()
        
        # Afficher l'indicateur de chargement
        self.show_loading_indicator()
        
        # Forcer le rechargement des documents depuis le fichier
        self.model.load_documents()
        
        # Si un dossier est sélectionné, le recharger
        if self.selected_folder is not None:
            # Récupérer les documents filtrés
            documents = self._get_filtered_documents()
            
            # Mettre à jour l'affichage
            self._display_documents(documents)
        else:
            # Sinon, afficher la vue des dossiers
            self.show_folders_view()
        
        self.hide_loading_indicator()
    
    def _update_filter_values(self):
        """Met à jour les valeurs des filtres à partir des documents"""
        logger.info("Mise à jour des valeurs des filtres...")
        
        try:
            # Récupérer tous les documents
            documents = self.model.documents
            
            # Récupérer les IDs clients valides
            valid_client_ids = []
            if isinstance(self.model.clients, list):
                valid_client_ids = [c.get("id") for c in self.model.clients if c.get("id")]
            elif isinstance(self.model.clients, dict):
                valid_client_ids = list(self.model.clients.keys())
            
            # Mettre à jour les types disponibles
            types = sorted(set(doc.get("type", "") for doc in documents if doc.get("type")))
            types.insert(0, "Tous les types")
            self.type_var.set("Tous les types")
            
            # Mettre à jour les clients disponibles - SEULEMENT LES CLIENTS VALIDES
            client_names = ["Tous les clients"]
            for client_id in valid_client_ids:
                client_name = self._get_client_name_cached(client_id)
                if client_name != "Client inconnu":  # Exclure les clients inconnus
                    client_names.append(client_name)
            
            # Mettre à jour les dates disponibles
            dates = sorted(set(doc.get("date", "") for doc in documents if doc.get("date")))
            date_options = ["Toutes"]
            for date in dates:
                if date:
                    date_options.append(date)
            
            # Mettre à jour les widgets
            if hasattr(self, 'type_combobox'):
                self.type_combobox.configure(values=types)
            
            if hasattr(self, 'client_combobox'):
                self.client_combobox.configure(values=sorted(client_names))  # Trier les noms de clients
            
            if hasattr(self, 'date_menu'):
                self.date_menu.configure(values=date_options)
            
            logger.info(f"Filtres mis à jour: {len(types)} types, {len(client_names)} clients, {len(date_options)} dates")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des filtres: {str(e)}")
            logger.error(traceback.format_exc())
    
    def new_document(self):
        """Crée un nouveau document"""
        try:
            # Vérifier s'il y a des modèles disponibles
            if not self.model.templates:
                DialogUtils.show_message(
                    self.parent,
                    "Attention",
                    "Aucun modèle disponible. Veuillez d'abord créer un modèle.",
                    "warning"
                )
                return
            
            # Vérifier s'il y a des clients disponibles
            if not self.model.clients:
                DialogUtils.show_message(
                    self.parent,
                    "Attention",
                    "Aucun client disponible. Veuillez d'abord ajouter un client.",
                    "warning"
                )
                return
            
            # Créer une nouvelle instance du formulaire de document
            from views.document_form_view import DocumentFormView
            
            # Préremplir le dossier si nous sommes dans un dossier personnalisé
            folder_id = None
            if self.selected_folder == "custom" and self.current_subfolder:
                folder_id = self.current_subfolder
            
            # Créer le document avec pré-remplissage du dossier et du type si applicable
            document_data = {}
            
            # Pré-remplir le type si nous sommes dans un dossier de type
            if self.selected_folder == "type" and self.current_subfolder:
                document_data["type"] = self.current_subfolder
            
            # Pré-remplir le client si nous sommes dans un dossier client
            if self.selected_folder == "client" and self.current_subfolder:
                document_data["client_id"] = self.current_subfolder
            
            # Créer le formulaire avec les données pré-remplies
            form = DocumentFormView(
                self.parent,
                self.model,
                document_data=document_data,
                folder_id=folder_id,
                on_save_callback=self.on_document_saved
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du document: {e}")
            DialogUtils.show_message(
                self.parent,
                "Erreur",
                f"Impossible de créer un nouveau document: {str(e)}",
                "error"
            )
    
    def on_document_saved(self, document_id=None, client_id=None, client_name=None, highlight=False, redirect_to_client=False, **kwargs):
        """
        Callback appelé après la sauvegarde d'un document
        
        Args:
            document_id: ID du document sauvegardé
            client_id: ID du client
            client_name: Nom du client
            highlight: Si True, met en évidence le document
            redirect_to_client: Si True, redirige vers le dossier du client
            **kwargs: Arguments supplémentaires ignorés
        """
        logger.info(f"Document sauvegardé: {document_id} pour le client {client_name} (ID: {client_id})")
        
        # Recharger les documents
        self.model.load_documents()
        
        if document_id and redirect_to_client and client_id:
            logger.info(f"Redirection vers le dossier client {client_id}")
            
            # Définir le dossier client comme dossier actif
            self.selected_folder = "client"
            
            def after_navigation():
                # D'abord afficher le dossier "Par client"
                self.show_folder_documents("client")
                
                def show_client_docs():
                    # Ensuite afficher les documents du client spécifique
                    self.show_documents_by_client(
                        client_id,
                        client_name or self._get_client_name_cached(client_id)
                    )
                    
                    def do_highlight():
                        # Si on doit mettre en évidence le document, le faire après un délai
                        if highlight:
                            logger.info(f"Mise en évidence du document {document_id}")
                            self._highlight_document(document_id)
                    
                    # Attendre que les documents soient affichés
                    self.parent.after(1000, do_highlight)
                
                # Attendre que la vue des dossiers soit prête
                self.parent.after(200, show_client_docs)
            
            # Exécuter la navigation après un court délai pour s'assurer que
            # l'interface est prête
            self.parent.after(100, after_navigation)
        else:
            # Comportement par défaut si pas de redirection demandée
            if self.selected_folder:
                document = next((d for d in self.model.documents if d.get("id") == document_id), None)
                if document and self._document_matches_current_folder(document):
                    # Rester dans le dossier actuel et mettre à jour l'affichage
                    documents = self._get_filtered_documents()
                    self._display_documents(documents)
                    
                    # Si on doit mettre en évidence le document
                    if highlight:
                        self.parent.after(1000, lambda: self._highlight_document(document_id))
                else:
                    # Revenir à la vue des dossiers
                    self.show_folders_view()
            else:
                # Par défaut, revenir à la vue des dossiers
                self.show_folders_view()
    
    def _highlight_document(self, document_id):
        """Met en évidence un document avec un effet subtil qui préserve la lisibilité du texte"""
        logger.info(f"Tentative de mise en évidence du document {document_id}")
        
        # Trouver le widget du document dans la grille
        found = False
        latest_card = None
        latest_date = None
        
        # Parcourir toutes les cartes de document dans la grille
        for card in self.documents_grid.winfo_children():
            try:
                if hasattr(card, 'document'):
                    # Obtenir la date de création du document
                    doc_date = card.document.get('created_at') or card.document.get('date')
                    if doc_date:
                        # Si c'est la première carte ou si c'est la plus récente
                        if latest_date is None or doc_date > latest_date:
                            latest_date = doc_date
                            latest_card = card
                            found = True
            except Exception as e:
                logger.warning(f"Erreur lors de la vérification d'une carte: {e}")
                continue
        
        if found and latest_card:
            logger.info(f"Document le plus récent trouvé, créé le {latest_date}")
            
            # Sauvegarder la couleur originale de la carte et du contenu
            original_color = latest_card.cget('fg_color')
            original_border = latest_card.cget('border_width')
            
            # Variable pour suivre si l'effet est en cours
            highlight_active = True
            
            # Gestionnaire d'événement pour arrêter l'effet au clic
            def stop_highlight(event):
                nonlocal highlight_active
                if highlight_active:
                    highlight_active = False
                    latest_card.configure(fg_color=original_color, border_width=original_border)
                    logger.debug("Effet de mise en évidence arrêté par clic utilisateur")
            
            # Lier l'événement clic à toutes les parties de la carte
            for widget in [latest_card] + latest_card.winfo_children():
                widget.bind("<Button-1>", stop_highlight, add="+")
            
            # Créer un effet de bordure qui ne masque pas le texte
            def apply_subtle_border_effect():
                nonlocal highlight_active
                
                # Si l'effet a été arrêté manuellement ou la carte n'existe plus
                if not highlight_active or not latest_card.winfo_exists():
                    return
                
                # Au lieu de changer la couleur de fond, utiliser une bordure subtile
                # qui n'affectera pas la lisibilité
                
                # Définir une bordure légèrement visible
                latest_card.configure(border_width=2)
                
                # Couleurs de bordure selon le thème
                if ctk.get_appearance_mode() == "Dark":
                    border_colors = [
                        "#4a6baf",  # Bleu subtil pour mode sombre
                        "#5272b1",
                        "#5a79b4",
                        "#6280b6",
                        "#6987b9",
                        "#6280b6",
                        "#5a79b4",
                        "#5272b1",
                        "#4a6baf",
                    ]
                else:
                    border_colors = [
                        "#7ba3e0",  # Bleu clair pour mode clair
                        "#6f9ade",
                        "#6391dc",
                        "#5789da",
                        "#4b80d8",
                        "#5789da",
                        "#6391dc",
                        "#6f9ade",
                        "#7ba3e0",
                    ]
                
                # Durée totale de l'effet: environ 3 secondes
                total_steps = len(border_colors)
                interval = 300  # ms entre changements de couleur
                
                def step_effect(step=0):
                    nonlocal highlight_active
                    
                    # Arrêter si l'effet n'est plus actif ou si on a terminé
                    if not highlight_active or step >= total_steps or not latest_card.winfo_exists():
                        # Restaurer l'état d'origine
                        if latest_card.winfo_exists():
                            latest_card.configure(border_width=original_border)
                        highlight_active = False
                        return
                    
                    # Appliquer la couleur de bordure courante
                    latest_card.configure(border_color=border_colors[step])
                    
                    # Programmer l'étape suivante
                    self.parent.after(interval, lambda: step_effect(step + 1))
                
                # Démarrer l'effet
                step_effect()
            
            # Lancer l'effet subtil
            apply_subtle_border_effect()
            
            # Arrêter automatiquement l'effet après 3 secondes
            self.parent.after(3000, lambda: stop_highlight(None) if highlight_active else None)
        else:
            logger.warning("Aucun document trouvé dans la vue pour la mise en évidence")
            # Réessayer après un court délai
            self.parent.after(500, lambda: self._highlight_document(document_id))
    
    def _document_matches_current_folder(self, document):
        """Vérifie si un document correspond au dossier actuel"""
        if self.selected_folder == "date" and self.current_subfolder:
            # Par date
            return document.get("date", "").startswith(self.current_subfolder)
        
        elif self.selected_folder == "type" and self.current_subfolder:
            # Par type
            return document.get("type", "").lower() == self.current_subfolder.lower()
        
        elif self.selected_folder == "client" and self.current_subfolder:
            # Par client
            return document.get("client_id") == self.current_subfolder
        
        elif self.selected_folder == "custom" and self.current_subfolder:
            # Par dossier personnalisé
            # Cette vérification dépend de votre implémentation
            if hasattr(self.model, 'document_in_custom_folder'):
                return self.model.document_in_custom_folder(document.get("id"), self.current_subfolder)
            return False
        
        return True
    
    def _open_document(self, document):
        """Ouvre un document"""
        try:
            # Récupérer le document
            document = next((d for d in self.model.documents if d.get('id') == document.get("id")), None)
            
            if not document:
                DialogUtils.show_message(
                    self.parent,
                    "Erreur",
                    "Document non trouvé",
                    "error"
                )
                return
            
            # Vérifier si le fichier existe
            file_path = document.get('file_path')
            
            if not file_path or not os.path.exists(file_path):
                DialogUtils.show_message(
                    self.parent,
                    "Erreur",
                    "Le fichier du document est introuvable",
                    "error"
                )
                return
            
            # Ouvrir le fichier avec l'application par défaut du système
            try:
                import subprocess
                if os.name == 'nt':  # Windows
                    os.startfile(file_path)
                elif os.name == 'posix':  # macOS ou Linux
                    subprocess.call(('open' if os.uname().sysname == 'Darwin' else 'xdg-open', file_path))
                
                logger.info(f"Document ouvert: {document.get('id')} - {file_path}")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'ouverture du document: {e}")
                DialogUtils.show_message(
                    self.parent,
                    "Erreur",
                    f"Erreur lors de l'ouverture du document: {str(e)}",
                    "error"
                )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du document: {e}")
            DialogUtils.show_message(
                self.parent,
                "Erreur",
                f"Une erreur est survenue: {str(e)}",
                "error"
            )
    
    def download_document(self, document_id):
        """Télécharge un document"""
        try:
            # Récupérer le document
            document = next((d for d in self.model.documents if d.get("id") == document_id), None)
            if not document:
                self.show_message("Erreur", "Document non trouvé", "error")
                return
            
            # Demander où sauvegarder le fichier
            file_path = filedialog.asksaveasfilename(
                defaultextension=os.path.splitext(document.get("file_path", ""))[1],
                initialfile=document.get("title", "document")
            )
            
            if file_path:
                # Copier le fichier
                shutil.copy2(document.get("file_path"), file_path)
                self.show_message("Succès", "Document téléchargé avec succès", "info")
        
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du document: {e}")
            self.show_message("Erreur", f"Impossible de télécharger le document: {str(e)}", "error")
    
    def preview_document(self, document_id):
        """Prévisualise un document"""
        try:
            # Récupérer le document
            document = next((d for d in self.model.documents if d.get("id") == document_id), None)
            if not document:
                self.show_message("Erreur", "Document non trouvé", "error")
                return
            
            # Créer et utiliser le prévisualiseur
            from utils.document_preview import DocumentPreview
            previewer = DocumentPreview(self.frame)
            previewer.preview(document)
            
        except Exception as e:
            logger.error(f"Erreur lors de la prévisualisation du document: {e}")
            self.show_message("Erreur", f"Impossible de prévisualiser le document: {str(e)}", "error")
    
    def import_document(self):
        """Importe un document externe avec validation de taille"""
        try:
            logger.debug("Début de l'importation d'un document")
            
            # Ouvrir une boîte de dialogue pour sélectionner un fichier
            file_path = filedialog.askopenfilename(
                title="Sélectionner un document à importer",
                filetypes=[
                    ("Documents", "*.pdf;*.docx;*.doc;*.txt;*.odt"),
                    ("PDF", "*.pdf"),
                    ("Word", "*.docx;*.doc"),
                    ("Texte", "*.txt"),
                    ("OpenDocument", "*.odt"),
                    ("Tous les fichiers", "*.*")
                ]
            )
            
            if not file_path:
                logger.debug("Importation annulée par l'utilisateur")
                return
            
            logger.info(f"Fichier sélectionné: {file_path}")
            
            # Vérifier si le fichier existe
            if not os.path.exists(file_path):
                logger.error(f"Le fichier n'existe pas: {file_path}")
                DialogUtils.show_message(
                    self.parent,
                    "Erreur",
                    "Le fichier sélectionné n'existe pas.",
                    "error"
                )
                return
            
            # Vérifier la taille du fichier
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_FILE_SIZE:
                logger.warning(f"Fichier trop volumineux: {file_path} ({file_size/1024/1024:.1f} Mo)")
                DialogUtils.show_message(
                    self.parent,
                    "Erreur",
                    f"Le fichier est trop volumineux ({file_size/1024/1024:.1f} Mo). Maximum autorisé: {self.MAX_FILE_SIZE/1024/1024} Mo.",
                    "error"
                )
                return
            
            logger.debug(f"Taille du fichier validée: {file_size/1024/1024:.1f} Mo")
            
            # Vérifier le type de fichier
            if not self._is_valid_file_type(file_path):
                logger.error(f"Type de fichier invalide: {file_path}")
                DialogUtils.show_message(
                    self.parent,
                    "Erreur",
                    "Type de fichier non autorisé ou fichier corrompu.",
                    "error"
                )
                return
            
            logger.info(f"Type de fichier validé: {file_path}")
            
            # Récupérer le nom de fichier comme titre par défaut
            filename = os.path.basename(file_path)
            title = os.path.splitext(filename)[0]
            
            # Déterminer automatiquement le type de document
            doc_type = "autre"
            lower_title = title.lower()
            
            if "contrat" in lower_title or "agreement" in lower_title:
                doc_type = "contrat"
            elif "facture" in lower_title or "invoice" in lower_title:
                doc_type = "facture"
            elif "proposition" in lower_title or "proposal" in lower_title:
                doc_type = "proposition"
            elif "rapport" in lower_title or "report" in lower_title:
                doc_type = "rapport"
            
            logger.debug(f"Type de document détecté: {doc_type}")
            
            # Créer un document avec les informations basiques
            document_data = {
                "title": title,
                "type": doc_type,
                "file_path": file_path,  # Sera copié plus tard
                "imported": True
            }
            
            # Si nous sommes dans un dossier personnalisé, associer le document à ce dossier
            folder_id = None
            if self.selected_folder == "custom" and self.current_subfolder:
                folder_id = self.current_subfolder
                logger.debug(f"Document associé au dossier personnalisé: {folder_id}")
            
            # Ouvrir le formulaire pour compléter les métadonnées
            from views.document_form_view import DocumentFormView
            form = DocumentFormView(
                self.parent,
                self.model,
                document_data=document_data,
                folder_id=folder_id,
                import_mode=True,
                on_save_callback=self.on_document_saved
            )
            
            logger.info("Formulaire d'importation ouvert avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'importation du document: {e}", exc_info=True)
            DialogUtils.show_message(
                self.parent,
                "Erreur",
                f"Erreur lors de l'importation du document: {str(e)}",
                "error"
            )
    
    def show(self):
        """Affiche la vue"""
        self.frame.pack(fill=ctk.BOTH, expand=True)
        self.update_view()
        logger.info("Vue documents affichée")
    
    def hide(self):
        """Masque la vue"""
        self.frame.pack_forget()
    
    def _is_valid_file_type(self, file_path):
        """Vérifie si le type de fichier est valide et sécurisé"""
        if not file_path:
            logger.warning("Tentative de validation d'un chemin de fichier vide")
            return False
        
        # Vérifier le cache d'abord
        if file_path in self._file_type_cache:
            logger.debug(f"Type de fichier trouvé dans le cache: {file_path}")
            return self._file_type_cache[file_path]
        
        # Extensions autorisées
        allowed_extensions = self.ALLOWED_EXTENSIONS
        
        # Vérifier l'extension
        _, ext = os.path.splitext(file_path.lower())
        if ext not in allowed_extensions:
            logger.warning(f"Extension de fichier non autorisée: {ext} pour {file_path}")
            return False
        
        # Pour plus de sécurité, vérifier aussi la signature du fichier (magic numbers)
        try:
            import magic
            file_type = magic.from_file(file_path, mime=True)
            
            # Vérifier le type MIME
            if file_type not in self.ALLOWED_MIME_TYPES:
                logger.warning(f"Type MIME non autorisé: {file_type} pour {file_path}")
                return False
            
            logger.debug(f"Type MIME validé: {file_type} pour {file_path}")
            
        except ImportError:
            logger.warning("Module python-magic non disponible, utilisation de la validation basique")
            # Si python-magic n'est pas disponible, utiliser une approche plus simple
            # Vérifier la taille du fichier
            if os.path.getsize(file_path) == 0:
                logger.warning(f"Fichier vide détecté: {file_path}")
                return False
            
            # Vérifier les premiers octets pour les formats courants
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(8)
                    
                    # Vérification simple des signatures
                    if ext == '.pdf' and not header.startswith(b'%PDF-'):
                        logger.warning(f"Signature PDF invalide pour {file_path}")
                        return False
                    elif ext in ['.docx', '.odt'] and not header.startswith(b'PK\x03\x04'):
                        logger.warning(f"Signature ZIP invalide pour {file_path}")
                        return False
            except Exception as e:
                logger.error(f"Erreur lors de la lecture du fichier {file_path}: {e}")
                return False
        
        # Mettre en cache le résultat
        if len(self._file_type_cache) >= self._file_type_cache_size:
            self._file_type_cache.pop(next(iter(self._file_type_cache)))
        self._file_type_cache[file_path] = True
        
        logger.info(f"Type de fichier validé avec succès: {file_path}")
        return True
    
    def _apply_filters(self, *args):
        """Applique les filtres et met à jour l'affichage - version corrigée"""
        # Ajouter un log pour aider au débogage
        logger.info("Application des filtres...")
        
        # Réinitialiser la page courante
        self.current_page = 1
        
        # Récupérer les documents filtrés
        filtered_docs = self._get_filtered_documents()
        
        # Afficher les documents filtrés
        self._display_documents(filtered_docs)
        
        # Ajouter un log final
        logger.info(f"Filtres appliqués: {len(filtered_docs)} documents affichés")
    
    def _clear_search(self):
        """Efface le texte de recherche et retourne à la vue précédente"""
        logger.info("Réinitialisation de la recherche via le bouton d'effacement")
        
        # Effacer le texte
        self.search_var.set("")
        
        # Forcer l'actualisation de l'entrée
        if hasattr(self, 'search_entry') and self.search_entry.winfo_exists():
            self.search_entry.delete(0, "end")
            self.search_entry.configure(placeholder_text="Rechercher un document...")
            self.search_entry.update()
            
            # Redonner le focus
            self.search_entry.focus_set()
        
        # Restaurer l'état précédent
        self._restore_pre_search_state()
        
        logger.info("Recherche réinitialisée, retour à la vue précédente")
    
    def _add_custom_folder_adapter(self, folder_name):
        """Adaptateur pour ajouter un dossier personnalisé"""
        try:
            import uuid
            folder_id = str(uuid.uuid4())
            
            # Vérifier si custom_folders est initialisé
            if not hasattr(self.model, 'custom_folders'):
                self.model.custom_folders = {}
            
            self.model.custom_folders[folder_id] = {
                "name": folder_name,
                "count": 0,
                "documents": []
            }
            # Sauvegarder les changements
            self._save_custom_folders()
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du dossier personnalisé: {e}")
            return False
    
    def _rename_custom_folder_adapter(self, folder_id, new_name):
        """Adaptateur pour renommer un dossier personnalisé"""
        try:
            # Vérifier si custom_folders est initialisé
            if not hasattr(self.model, 'custom_folders'):
                logger.error("custom_folders n'est pas initialisé")
                return False
            
            if folder_id not in self.model.custom_folders:
                return False
            
            self.model.custom_folders[folder_id]["name"] = new_name
            # Sauvegarder les changements
            self._save_custom_folders()
            return True
        except Exception as e:
            logger.error(f"Erreur lors du renommage du dossier personnalisé: {e}")
            return False
    
    def _delete_custom_folder_adapter(self, folder_id):
        """Adaptateur pour supprimer un dossier personnalisé"""
        try:
            # Vérifier si custom_folders est initialisé
            if not hasattr(self.model, 'custom_folders'):
                logger.error("custom_folders n'est pas initialisé")
                return False
            
            if folder_id not in self.model.custom_folders:
                return False
            
            del self.model.custom_folders[folder_id]
            # Sauvegarder les changements
            self._save_custom_folders()
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du dossier personnalisé: {e}")
            return False
    
    def _get_documents_by_custom_folder_adapter(self, folder_id):
        """Adaptateur pour récupérer les documents d'un dossier personnalisé"""
        try:
            # Vérifier si custom_folders est initialisé
            if not hasattr(self.model, 'custom_folders'):
                logger.error("custom_folders n'est pas initialisé")
                return []
            
            if folder_id not in self.model.custom_folders:
                return []
            
            # Récupérer les IDs des documents dans ce dossier
            document_ids = self.model.custom_folders[folder_id].get("documents", [])
            
            # Récupérer les documents correspondants
            return [doc for doc in self.model.documents if doc.get("id") in document_ids]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des documents du dossier: {e}")
            return []
    
    def _document_in_custom_folder_adapter(self, document_id, folder_id):
        """Adaptateur pour vérifier si un document est dans un dossier personnalisé"""
        try:
            # Vérifier si custom_folders est initialisé
            if not hasattr(self.model, 'custom_folders'):
                logger.error("custom_folders n'est pas initialisé")
                return False
            
            if folder_id not in self.model.custom_folders:
                return False
            
            # Vérifier si le document est dans ce dossier
            document_ids = self.model.custom_folders[folder_id].get("documents", [])
            return document_id in document_ids
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du document dans le dossier: {e}")
            return False
    
    def _save_custom_folders(self):
        """Sauvegarde les dossiers personnalisés"""
        try:
            # Vérifier si custom_folders est initialisé
            if not hasattr(self.model, 'custom_folders'):
                logger.error("custom_folders n'est pas initialisé")
                return False
            
            # Si le modèle a une méthode pour sauvegarder les dossiers personnalisés, l'utiliser
            if hasattr(self.model, 'save_custom_folders'):
                return self.model.save_custom_folders()
            
            # Sinon, utiliser une méthode par défaut
            import json
            import os
            
            # Créer le répertoire de données si nécessaire
            data_dir = getattr(self.model, 'data_dir', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'))
            os.makedirs(data_dir, exist_ok=True)
            
            # Sauvegarder dans un fichier JSON
            filepath = os.path.join(data_dir, 'custom_folders.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.model.custom_folders, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des dossiers personnalisés: {e}")
            return False
    
    def _setup_search(self):
        """Configure la fonctionnalité de recherche en temps réel"""
        # Créer la variable de recherche si elle n'existe pas déjà
        if not hasattr(self, 'search_var'):
            self.search_var = ctk.StringVar(value="")
        
        # Variables pour mémoriser l'état de navigation avant la recherche
        if not hasattr(self, 'pre_search_state'):
            self.pre_search_state = {
                'folder': None,
                'subfolder': None,
                'search_active': False,
                'in_main_view': True
            }
        
        # Ajouter un callback direct en temps réel
        def search_callback(*args):
            # Récupérer la valeur actuelle
            current_search = self.search_var.get()
            
            # Si c'est la première entrée dans la recherche, mémoriser l'état actuel
            if not self.pre_search_state['search_active'] and current_search:
                self.pre_search_state['folder'] = self.selected_folder
                self.pre_search_state['subfolder'] = self.current_subfolder
                self.pre_search_state['in_main_view'] = (self.selected_folder is None)
                self.pre_search_state['search_active'] = True
                logger.info(f"État mémorisé avant recherche: dossier={self.pre_search_state['folder']}, "
                            f"sous-dossier={self.pre_search_state['subfolder']}, "
                            f"vue principale={self.pre_search_state['in_main_view']}")
            
            # Si la recherche devient vide et était active avant, restaurer l'état précédent
            if self.pre_search_state['search_active'] and not current_search:
                logger.info("Recherche vidée, restauration de l'état précédent")
                self._restore_pre_search_state()
                return
            
            # Annuler le timer existant si présent
            if hasattr(self, 'search_timer') and self.search_timer:
                self.parent.after_cancel(self.search_timer)
            
            # Planifier une nouvelle recherche
            self.search_timer = self.parent.after(
                300,  # délai court pour une réactivité en temps réel
                lambda: self._perform_search(current_search)
            )
        
        # Connecter la variable au callback
        self.search_var.trace_add("write", search_callback)
        
        # S'assurer que la barre de recherche utilise cette variable
        if hasattr(self, 'search_entry'):
            self.search_entry.configure(textvariable=self.search_var)
        
        logger.info("Configuration de la recherche en temps réel terminée")

    def _restore_pre_search_state(self):
        """Restaure l'état avant la recherche"""
        # Récupérer l'état mémorisé
        folder = self.pre_search_state['folder']
        subfolder = self.pre_search_state['subfolder']
        in_main_view = self.pre_search_state['in_main_view']
        
        logger.info(f"Restauration de l'état: dossier={folder}, sous-dossier={subfolder}, vue principale={in_main_view}")
        
        # Réinitialiser l'état de la recherche
        self.pre_search_state['search_active'] = False
        
        # Si nous étions dans la vue principale, y retourner
        if in_main_view:
            self.show_folders_view()
            return
        
        # Sinon, restaurer la navigation en fonction de l'état précédent
        if folder is None:
            # Si nous étions dans la vue principale, afficher les dossiers
            self.show_folders_view()
        elif folder is not None and subfolder is None:
            # Si nous étions dans un dossier principal, afficher ses sous-dossiers
            self.show_folder_documents(folder)
        elif folder is not None and subfolder is not None:
            # Si nous étions dans un sous-dossier, afficher ses documents
            self._restore_subfolder_view(folder, subfolder)

    def _restore_subfolder_view(self, folder, subfolder):
        """Restaure la vue d'un sous-dossier spécifique"""
        if folder == "date":
            display_name = self._get_month_display_name(subfolder)
            self.show_documents_by_month(subfolder, display_name)
        elif folder == "type":
            self.show_documents_by_type(subfolder)
        elif folder == "client":
            client_name = self._get_client_name_cached(subfolder)
            self.show_documents_by_client(subfolder, client_name)
        elif folder == "custom":
            folder_name = self.model.custom_folders.get(subfolder, {}).get("name", "Dossier personnalisé")
            self.show_documents_by_custom_folder(subfolder, folder_name)

    def _perform_search(self, search_text):
        """Effectue la recherche en temps réel en préservant la hiérarchie de navigation"""
        logger.info(f"Recherche en cours pour: '{search_text}'")
        
        # Recherche vide, retourner à la vue appropriée
        if not search_text:
            # Si nous sommes dans la vue principale des dossiers
            if self.selected_folder is None:
                self.show_folders_view()
                return
            
            # Si nous sommes dans un dossier principal mais pas dans un sous-dossier
            elif self.selected_folder is not None and self.current_subfolder is None:
                self.show_folder_documents(self.selected_folder)
                return
            
            # Si nous sommes dans un sous-dossier
            elif self.selected_folder is not None and self.current_subfolder is not None:
                # Restaurer la vue du sous-dossier actuel
                self._restore_current_view()
                return
        
        # Si nous sommes dans la vue principale (aucun dossier sélectionné)
        if self.selected_folder is None:
            # Effectuer une recherche dans les dossiers principaux
            search_results = []
            for doc in self.model.documents:
                # Rechercher dans tous les champs pertinents
                searchable_fields = [
                    doc.get("title", "").lower(),
                    doc.get("type", "").lower(),
                    doc.get("description", "").lower(),
                    self._get_client_name_cached(doc.get("client_id", "")).lower(),
                    doc.get("date", "").lower()
                ]
                
                # Vérifier si le texte de recherche est présent dans au moins un champ
                if any(search_text.lower() in field for field in searchable_fields):
                    search_results.append(doc)
            
            # Afficher les résultats dans la vue principale
            self._display_documents(search_results)
            return
        
        # Si nous sommes dans un dossier principal mais pas dans un sous-dossier
        elif self.selected_folder is not None and self.current_subfolder is None:
            # Rechercher selon le type de dossier
            if self.selected_folder == "client":
                # Filtrer les clients selon le texte de recherche
                self._filter_clients_by_search(search_text)
            elif self.selected_folder == "type":
                # Filtrer les types selon le texte de recherche
                self._filter_types_by_search(search_text)
            elif self.selected_folder == "date":
                # Filtrer les dates selon le texte de recherche
                self._filter_dates_by_search(search_text)
            elif self.selected_folder == "custom":
                # Filtrer les dossiers personnalisés selon le texte de recherche
                self._filter_custom_folders_by_search(search_text)
            return
        
        # Si nous sommes dans un sous-dossier (niveau documents)
        elif self.selected_folder is not None and self.current_subfolder is not None:
            # Filtrer les documents du sous-dossier actuel
            documents = self._get_filtered_documents()
            search_results = []
            
            for doc in documents:
                # Rechercher dans tous les champs pertinents
                searchable_fields = [
                    doc.get("title", "").lower(),
                    doc.get("type", "").lower(),
                    doc.get("description", "").lower(),
                    self._get_client_name_cached(doc.get("client_id", "")).lower(),
                    doc.get("date", "").lower()
                ]
                
                # Vérifier si le texte de recherche est présent dans au moins un champ
                if any(search_text.lower() in field for field in searchable_fields):
                    search_results.append(doc)
            
            # Afficher les résultats filtrés sans changer de vue
            self._display_documents(search_results)
            return

    def _filter_clients_by_search(self, search_text):
        """Filtre et affiche les clients correspondant au texte de recherche"""
        search_text = search_text.lower()
        matching_clients = []
        
        # Rechercher dans les clients
        for client in self.model.clients:
            searchable_fields = [
                client.get("name", "").lower(),
                client.get("company", "").lower() if client.get("company") else "",
                client.get("email", "").lower() if client.get("email") else "",
                client.get("phone", "").lower() if client.get("phone") else "",
                client.get("address", "").lower() if client.get("address") else ""
            ]
            
            # Vérifier si le texte de recherche est dans l'un des champs
            if any(search_text in field for field in searchable_fields):
                matching_clients.append(client)
        
        # Nettoyer la vue
        self.folders_grid.pack_forget()
        self.documents_grid.pack_forget()
        self.no_documents_label.pack_forget()
        
        # Afficher la grille des dossiers pour les résultats
        self.folders_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        
        # Nettoyer la grille
        for widget in self.folders_grid.winfo_children():
            widget.destroy()
        
        # Si aucun résultat
        if not matching_clients:
            self.no_documents_label.configure(
                text="Aucun client ne correspond à votre recherche."
            )
            self.no_documents_label.pack(pady=20)
            return
        
        # Afficher les clients trouvés
        row, col = 0, 0
        for client in matching_clients:
            client_id = client.get("id", "")
            client_name = client.get("name", "Client inconnu")
            
            # Compter les documents pour ce client
            doc_count = len([d for d in self.model.documents if d.get("client_id") == client_id])
            
            # Créer une carte pour ce client
            self._create_client_folder_card(client_id, client_name, doc_count, row, col)
            
            col += 1
            if col >= 2:  # 2 cards par ligne
                col = 0
                row += 1

    def _filter_types_by_search(self, search_text):
        """Filtre et affiche les types correspondant au texte de recherche"""
        search_text = search_text.lower()
        matching_types = {}
        
        # Collecter tous les types de documents qui correspondent
        for doc in self.model.documents:
            doc_type = doc.get("type", "").lower()
            if search_text in doc_type:
                if doc_type not in matching_types:
                    matching_types[doc_type] = 0
                matching_types[doc_type] += 1
        
        # Nettoyer la vue
        self.folders_grid.pack_forget()
        self.documents_grid.pack_forget()
        self.no_documents_label.pack_forget()
        
        # Afficher la grille des dossiers pour les résultats
        self.folders_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        
        # Nettoyer la grille
        for widget in self.folders_grid.winfo_children():
            widget.destroy()
        
        # Si aucun résultat
        if not matching_types:
            self.no_documents_label.configure(
                text="Aucun type de document ne correspond à votre recherche."
            )
            self.no_documents_label.pack(pady=20)
            return
        
        # Afficher les types trouvés
        row, col = 0, 0
        for doc_type, count in matching_types.items():
            # Créer une carte pour ce type
            self._create_type_folder_card(doc_type, count, row, col)
            
            col += 1
            if col >= 2:  # 2 cards par ligne
                col = 0
                row += 1

    def _filter_dates_by_search(self, search_text):
        """Filtre et affiche les dates correspondant au texte de recherche"""
        search_text = search_text.lower()
        matching_months = {}
        months_names = {
            "01": "Janvier", "02": "Février", "03": "Mars",
            "04": "Avril", "05": "Mai", "06": "Juin",
            "07": "Juillet", "08": "Août", "09": "Septembre",
            "10": "Octobre", "11": "Novembre", "12": "Décembre"
        }
        
        # Parcourir tous les documents pour trouver les dates
        for doc in self.model.documents:
            date_str = doc.get("date", "")
            if len(date_str) >= 7:  # Format "YYYY-MM"
                year_month = date_str[:7]
                year = date_str[:4]
                month = date_str[5:7]
                month_name = months_names.get(month, month)
                display_name = f"{month_name} {year}"
                
                # Vérifier si la recherche correspond au nom du mois ou à l'année
                if (search_text in display_name.lower() or 
                    search_text in year or 
                    search_text in month):
                    if year_month not in matching_months:
                        matching_months[year_month] = {
                            "display_name": display_name,
                            "count": 0
                        }
                    matching_months[year_month]["count"] += 1
        
        # Nettoyer la vue
        self.folders_grid.pack_forget()
        self.documents_grid.pack_forget()
        self.no_documents_label.pack_forget()
        
        # Afficher la grille des dossiers pour les résultats
        self.folders_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        
        # Nettoyer la grille
        for widget in self.folders_grid.winfo_children():
            widget.destroy()
        
        # Si aucun résultat
        if not matching_months:
            self.no_documents_label.configure(
                text="Aucune date ne correspond à votre recherche."
            )
            self.no_documents_label.pack(pady=20)
            return
        
        # Afficher les mois trouvés
        row, col = 0, 0
        for year_month, data in sorted(matching_months.items(), reverse=True):
            # Créer une carte pour ce mois
            self._create_month_folder_card(year_month, data["display_name"], data["count"], row, col)
            
            col += 1
            if col >= 2:  # 2 cards par ligne
                col = 0
                row += 1

    def _filter_custom_folders_by_search(self, search_text):
        """Filtre et affiche les dossiers personnalisés correspondant au texte de recherche"""
        search_text = search_text.lower()
        matching_folders = []
        
        # Rechercher dans les noms des dossiers personnalisés
        for folder_id, folder_data in self.model.custom_folders.items():
            folder_name = folder_data.get("name", "").lower()
            if search_text in folder_name:
                matching_folders.append((folder_id, folder_data))
        
        # Nettoyer la vue
        self.folders_grid.pack_forget()
        self.documents_grid.pack_forget()
        self.no_documents_label.pack_forget()
        
        # Afficher la grille des dossiers pour les résultats
        self.folders_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        
        # Nettoyer la grille
        for widget in self.folders_grid.winfo_children():
            widget.destroy()
        
        # Si aucun résultat
        if not matching_folders:
            self.no_documents_label.configure(
                text="Aucun dossier personnalisé ne correspond à votre recherche."
            )
            self.no_documents_label.pack(pady=20)
            return
        
        # Afficher les dossiers trouvés
        row, col = 0, 0
        for folder_id, folder_data in matching_folders:
            folder_name = folder_data.get("name", "Dossier personnalisé")
            document_count = len(folder_data.get("documents", []))
            
            # Créer une carte pour ce dossier
            self._create_custom_folder_card(folder_id, folder_name, document_count, row, col)
            
            col += 1
            if col >= 2:  # 2 cards par ligne
                col = 0
                row += 1

    def _get_month_display_name(self, year_month):
        """Convertit un format YYYY-MM en nom de mois affichable"""
        months_names = {
            "01": "Janvier", "02": "Février", "03": "Mars",
            "04": "Avril", "05": "Mai", "06": "Juin",
            "07": "Juillet", "08": "Août", "09": "Septembre",
            "10": "Octobre", "11": "Novembre", "12": "Décembre"
        }
        
        if len(year_month) >= 7:
            year = year_month[:4]
            month = year_month[5:7]
            month_name = months_names.get(month, month)
            return f"{month_name} {year}"
        return year_month

    def handle_back(self):
        """Gère le retour à la vue précédente"""
        if self.current_subfolder:
            # Si on est dans un sous-dossier, retourner au dossier parent
            self.current_subfolder = None
            self.show_folder_documents(self.selected_folder)
        else:
            # Si on est dans un dossier principal, retourner à la vue des dossiers
            self.show_folders_view()