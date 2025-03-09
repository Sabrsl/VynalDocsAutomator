#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue de gestion des documents pour l'application Vynal Docs Automator
Version optimisée pour la performance
"""

import os
import logging
import threading
import queue
import time
import customtkinter as ctk
import tkinter.messagebox as messagebox
from datetime import datetime

logger = logging.getLogger("VynalDocsAutomator.DocumentView")

class DocumentView:
    """
    Vue de gestion des documents
    Permet de visualiser, créer et gérer des documents
    Version optimisée pour les performances
    """
    
    def __init__(self, parent, app_model):
        """
        Initialise la vue de gestion des documents
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        
        # Initialiser le gestionnaire d'utilisation
        from utils.usage_tracker import UsageTracker
        self.usage_tracker = UsageTracker()
        
        # Cadre principal de la vue
        self.frame = ctk.CTkFrame(parent)
        
        # Liste pour stocker les documents sélectionnés
        self.selected_documents = []
        
        # Paramètres de performance
        self.max_documents = 200  # Nombre maximum de documents affichés
        self.debounce_delay = 300  # Délai de debounce en millisecondes
        self.search_timer = None   # Timer pour la recherche
        self.filter_timer = None   # Timer pour les filtres
        self.is_loading = False    # Indicateur de chargement
        self.loading_queue = queue.Queue()  # File d'attente pour le chargement
        
        # Métriques de performance
        self.performance_metrics = {
            'total_load_time': 0,
            'filter_time': 0,
            'render_time': 0,
            'document_count': 0
        }
        
        # Créer les composants de l'interface
        self.create_widgets()
        
        # Initialiser le traitement asynchrone
        self._setup_async_processing()
        
        logger.info("DocumentView optimisée initialisée")
    
    def _setup_async_processing(self):
        """
        Configure le traitement asynchrone des documents
        """
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
                    logger.error(f"Erreur dans le thread de traitement: {e}")
                    # Continuer malgré l'erreur
                    continue
        
        # Démarrer le thread de traitement
        worker_thread = threading.Thread(target=queue_worker, daemon=True)
        worker_thread.start()
        
        # Configurer la journalisation périodique des performances
        def log_performance():
            try:
                logger.info(f"Performance: Chargement={self.performance_metrics['total_load_time']:.3f}s, "
                           f"Filtrage={self.performance_metrics['filter_time']:.3f}s, "
                           f"Rendu={self.performance_metrics['render_time']:.3f}s, "
                           f"Documents={self.performance_metrics['document_count']}")
            except Exception as e:
                logger.error(f"Erreur lors de la journalisation des performances: {e}")
            
            # Programmer la prochaine journalisation
            self.parent.after(300000, log_performance)  # Toutes les 5 minutes
        
        # Démarrer la journalisation
        log_performance()
    
    def create_widgets(self):
        """
        Crée les widgets de la vue
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
        
        # Bouton Supprimer (initialement désactivé)
        self.delete_btn = ctk.CTkButton(
            self.toolbar,
            text="🗑️ Supprimer",
            fg_color="#7f8c8d",
            hover_color="#7f8c8d",
            state="disabled",
            command=self.delete_selected_documents
        )
        self.delete_btn.pack(side=ctk.LEFT, padx=10)
        
        # Bouton Importer
        self.import_btn = ctk.CTkButton(
            self.toolbar,
            text="Importer",
            command=self.import_document
        )
        self.import_btn.pack(side=ctk.LEFT, padx=10)
        
        # Indicateur de chargement
        self.loading_label = ctk.CTkLabel(
            self.toolbar,
            text="Chargement...",
            text_color="#3498db",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        # Ne pas l'afficher au démarrage
        
        # Filtres
        self.filter_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.filter_frame.pack(side=ctk.RIGHT, padx=10)
        
        # Filtre client
        self.client_var = ctk.StringVar(value="Tous les clients")
        self.client_combobox = ctk.CTkComboBox(
            self.filter_frame,
            values=["Tous les clients"],
            variable=self.client_var,
            width=150,
            command=self.debounced_filter_documents
        )
        self.client_combobox.pack(side=ctk.LEFT, padx=5)
        
        # Filtre type
        self.type_var = ctk.StringVar(value="Tous les types")
        self.type_combobox = ctk.CTkComboBox(
            self.filter_frame,
            values=["Tous les types"],
            variable=self.type_var,
            width=150,
            command=self.debounced_filter_documents
        )
        self.type_combobox.pack(side=ctk.LEFT, padx=5)
        
        # Recherche
        self.search_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.search_frame.pack(side=ctk.RIGHT, padx=10)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.debounced_filter_documents())
        
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Rechercher un document...",
            width=200,
            textvariable=self.search_var
        )
        self.search_entry.pack(side=ctk.LEFT)
        
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
        self.no_documents_label.pack(pady=20)
        
        # Grille de documents (contiendra les cartes de documents)
        self.documents_grid = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Configurer la grille pour avoir 3 colonnes
        for i in range(3):
            self.documents_grid.columnconfigure(i, weight=1)
    
    def update_view(self):
        """
        Met à jour la vue avec les données actuelles
        Version optimisée pour réduire le temps de chargement
        """
        # Afficher l'indicateur de chargement
        self.show_loading_indicator()
        
        # Réinitialiser l'UI de sélection
        self.selected_documents = []
        self.update_selection_ui()
        
        # Mettre à jour les filtres clients
        clients = ["Tous les clients"]
        clients_list = [c.get("name", "") for c in self.model.clients]
        clients.extend(clients_list)
        self.client_combobox.configure(values=clients)
        
        # Mettre à jour les filtres types de manière asynchrone
        self.loading_queue.put((self._update_document_types, []))
        
        # S'assurer que les valeurs par défaut sont correctes
        if self.client_var.get() not in clients:
            self.client_var.set("Tous les clients")
        
        # Charger les documents de manière asynchrone
        self.load_documents_async()
    
    def _update_document_types(self):
        """
        Met à jour les types de documents de manière asynchrone
        """
        start_time = time.time()
        
        # Récupérer tous les documents
        documents = self.model.documents
        
        # Extraire les types uniques
        doc_types = ["Tous les types"]
        unique_types = set([d.get("type", "") for d in documents])
        doc_types.extend(sorted(list(unique_types)))
        
        # Mise à jour dans le thread principal
        self.parent.after(0, lambda: self._update_type_combobox(doc_types))
        
        # Mesurer le temps d'exécution
        execution_time = time.time() - start_time
        logger.debug(f"Mise à jour des types terminée en {execution_time:.3f}s")
    
    def _update_type_combobox(self, doc_types):
        """
        Met à jour la ComboBox des types dans le thread principal
        """
        self.type_combobox.configure(values=doc_types)
        
        if self.type_var.get() not in doc_types:
            self.type_var.set("Tous les types")
    
    def load_documents_async(self):
        """
        Charge les documents de manière asynchrone
        """
        # Mettre le flag de chargement à True
        self.is_loading = True
        
        # Lancer le chargement dans un thread séparé
        threading.Thread(target=self._load_and_filter_documents, daemon=True).start()
    
    def _load_and_filter_documents(self):
        """
        Charge et filtre les documents dans un thread séparé
        """
        start_time = time.time()
        
        try:
            # Récupérer tous les documents
            documents = self.model.documents
            
            # Trier les documents par date (du plus récent au plus ancien)
            sorted_docs = sorted(
                documents,
                key=lambda d: d.get("date", ""),
                reverse=True
            )
            
            # Limiter le nombre de documents pour améliorer les performances
            limited_docs = sorted_docs[:self.max_documents]
            
            # Appliquer les filtres
            filtered_docs = self.apply_filters(limited_docs)
            
            # Mesurer le temps de chargement et filtrage
            load_time = time.time() - start_time
            self.performance_metrics['total_load_time'] = load_time
            self.performance_metrics['document_count'] = len(filtered_docs)
            
            # Mettre à jour l'interface dans le thread principal
            self.parent.after(0, lambda: self._update_ui_with_documents(filtered_docs))
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des documents: {e}")
            self.parent.after(0, lambda: self._show_error_message(str(e)))
    
    def _update_ui_with_documents(self, filtered_docs):
        """
        Met à jour l'interface avec les documents filtrés
        """
        start_render_time = time.time()
        
        # Masquer l'indicateur de chargement
        self.hide_loading_indicator()
        
        # Fin du chargement
        self.is_loading = False
        
        # Afficher ou masquer le message "Aucun document"
        if filtered_docs:
            self.no_documents_label.pack_forget()
            self.documents_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
            
            # Nettoyer la grille
            for widget in self.documents_grid.winfo_children():
                widget.destroy()
            
            # Remplir la grille avec les documents filtrés
            row, col = 0, 0
            for doc in filtered_docs:
                self.create_document_card(doc, row, col)
                col += 1
                if col >= 3:  # 3 cartes par ligne
                    col = 0
                    row += 1
        else:
            self.documents_grid.pack_forget()
            self.no_documents_label.pack(pady=20)
        
        # Mesurer le temps de rendu
        render_time = time.time() - start_render_time
        self.performance_metrics['render_time'] = render_time
        
        logger.info(f"Rendu de {len(filtered_docs)} documents en {render_time:.3f}s")
    
    def _show_error_message(self, error_message):
        """
        Affiche un message d'erreur
        """
        messagebox.showerror(
            "Erreur de chargement",
            f"Impossible de charger les documents: {error_message}"
        )
        self.hide_loading_indicator()
        self.is_loading = False
    
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
    
    def create_document_card(self, document, row, col):
        """
        Crée une carte pour afficher un document avec case à cocher
        Version optimisée pour réduire le temps de rendu
        
        Args:
            document: Données du document
            row: Ligne dans la grille
            col: Colonne dans la grille
        """
        # Cadre de la carte
        card = ctk.CTkFrame(self.documents_grid)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Case à cocher de sélection - petite et en haut à droite
        var = ctk.BooleanVar(value=False)
        
        # Créer un cadre pour positionner la checkbox en haut à droite
        checkbox_frame = ctk.CTkFrame(card, fg_color="transparent")
        checkbox_frame.pack(fill=ctk.X, padx=0, pady=0)
        
        # Checkbox petite sans texte
        checkbox = ctk.CTkCheckBox(
            checkbox_frame, 
            text="", 
            variable=var,
            width=16,
            height=16,
            checkbox_width=16,
            checkbox_height=16,
            corner_radius=3,
            border_width=1,
            command=lambda d=document, v=var: self.toggle_document_selection(d, v)
        )
        checkbox.pack(side=ctk.RIGHT, anchor="ne", padx=5, pady=5)
        
        # Icône selon le type
        doc_type = document.get("type", "")
        icon = "📄"  # Par défaut
        
        if doc_type == "contrat":
            icon = "📝"
        elif doc_type == "facture":
            icon = "💰"
        elif doc_type == "proposition":
            icon = "📊"
        elif doc_type == "rapport":
            icon = "📈"
        
        # En-tête avec icône et type
        header = ctk.CTkFrame(card, fg_color=("gray90", "gray20"), corner_radius=6)
        header.pack(fill=ctk.X, padx=5, pady=5)
        
        ctk.CTkLabel(
            header,
            text=f"{icon} {doc_type.capitalize() if doc_type else 'Document'}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side=ctk.LEFT, padx=10, pady=5)
        
        # Date (affichée comme dans ClientView)
        doc_date = document.get("date", "")
        if doc_date:
            # Formater la date pour qu'elle s'affiche de façon lisible
            try:
                # Si c'est un objet datetime
                if isinstance(doc_date, datetime):
                    formatted_date = doc_date.strftime("%d/%m/%Y %H:%M")
                # Si c'est une chaîne ISO
                else:
                    date_obj = datetime.fromisoformat(doc_date.replace('Z', '+00:00')) 
                    formatted_date = date_obj.strftime("%d/%m/%Y %H:%M")
            except Exception:
                # Si le format n'est pas reconnu, afficher tel quel
                formatted_date = doc_date
                
            ctk.CTkLabel(
                header,
                text=formatted_date,
                font=ctk.CTkFont(size=10),
                text_color="gray"
            ).pack(side=ctk.RIGHT, padx=10, pady=5)
        
        # Titre du document
        ctk.CTkLabel(
            card,
            text=document.get("title", "Sans titre"),
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=200
        ).pack(fill=ctk.X, padx=10, pady=5)
        
        # Client (optimisé pour éviter les recherches coûteuses)
        client_id = document.get("client_id", "")
        client_name = "Aucun client"
        
        if client_id:
            # Utilisation d'un dictionnaire pour accélérer la recherche
            clients_dict = {c.get("id"): c.get("name", "Inconnu") for c in self.model.clients}
            client_name = clients_dict.get(client_id, "Inconnu")
        
        ctk.CTkLabel(
            card,
            text=f"Client: {client_name}",
            font=ctk.CTkFont(size=12),
            wraplength=200
        ).pack(fill=ctk.X, padx=10, pady=2)
        
        # Description (avec limitation de longueur pour améliorer les performances)
        description = document.get("description", "")
        if description:
            # Limiter la longueur de la description pour accélérer le rendu
            if len(description) > 200:
                description = description[:197] + "..."
                
            ctk.CTkLabel(
                card,
                text=description,
                font=ctk.CTkFont(size=12),
                wraplength=200,
                text_color="gray",
                justify="left"
            ).pack(fill=ctk.X, padx=10, pady=5)
        
        # Boutons d'action
        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.pack(fill=ctk.X, padx=10, pady=10)
        
        # Bouton Ouvrir
        ctk.CTkButton(
            actions_frame,
            text="Ouvrir",
            width=80,
            height=25,
            command=lambda doc_id=document.get("id"): self.open_document(doc_id)
        ).pack(side=ctk.LEFT, padx=2)
        
        # Bouton Télécharger
        ctk.CTkButton(
            actions_frame,
            text="Télécharger",
            width=80,
            height=25,
            command=lambda doc_id=document.get("id"): self.download_document(doc_id)
        ).pack(side=ctk.RIGHT, padx=2)
    
    def toggle_document_selection(self, document, var):
        """
        Gère la sélection des documents pour suppression avec feedback visuel
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
            # Activer et mettre à jour le bouton de suppression
            self.delete_btn.configure(
                text=f"🗑️ Supprimer ({count})",
                state="normal",
                fg_color="#e74c3c",
                hover_color="#c0392b"
            )
            
            # Afficher un badge flottant avec le nombre de documents sélectionnés
            self.show_selection_badge(count)
        else:
            # Réinitialiser le bouton de suppression
            self.delete_btn.configure(
                text="🗑️ Supprimer",
                state="disabled",
                fg_color="#7f8c8d",
                hover_color="#7f8c8d"
            )
            
            # Masquer le badge
            if hasattr(self, 'selection_badge'):
                self.selection_badge.destroy()
                delattr(self, 'selection_badge')
    
    def show_selection_badge(self, count):
        """
        Affiche un badge avec le nombre d'éléments sélectionnés
        """
        if hasattr(self, 'selection_badge'):
            self.selection_badge.destroy()
        
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
            messagebox.showinfo("Aucune sélection", "Veuillez sélectionner des documents à supprimer.")
            return
        
        # Nombre de documents à supprimer
        count = len(self.selected_documents)
        
        # Demander confirmation avec la boîte de dialogue standard
        confirm = messagebox.askyesno(
            "Confirmer la suppression", 
            f"Voulez-vous vraiment supprimer {count} document{'s' if count > 1 else ''} ?\n\nCette action est irréversible.",
            icon='warning'
        )
        
        if not confirm:
            return
        
        # Afficher l'indicateur de chargement
        self.show_loading_indicator()
        
        # Supprimer les documents de manière asynchrone
        threading.Thread(target=self._delete_documents_async, daemon=True).start()
    
    def _delete_documents_async(self):
        """
        Supprime les documents dans un thread séparé
        """
        try:
            # Récupérer les IDs des documents à supprimer
            doc_ids_to_delete = [doc.get("id") for doc in self.selected_documents]
            
            # Supprimer les documents du modèle
            self.model.documents = [d for d in self.model.documents if d.get("id") not in doc_ids_to_delete]
            
            # Sauvegarder les changements
            self.model.save_documents()
            
            # Mettre à jour l'interface dans le thread principal
            self.parent.after(0, self._finalize_deletion)
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des documents: {e}")
            self.parent.after(0, lambda: messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}"))
            self.parent.after(0, self.hide_loading_indicator)
    
    def _finalize_deletion(self):
        """
        Finalise la suppression dans le thread principal
        """
        # Réinitialiser la liste des documents sélectionnés
        self.selected_documents = []
        
        # Masquer l'indicateur de chargement
        self.hide_loading_indicator()
        
        # Mettre à jour la vue
        self.update_view()
        
        # Afficher une notification de succès
        self.show_success_toast()
    
    def show_success_toast(self):
        """
        Affiche une notification toast de succès
        """
        # Créer un toast en bas de l'écran
        toast = ctk.CTkFrame(self.parent, corner_radius=10)
        
        # Icône de succès
        icon_label = ctk.CTkLabel(
            toast,
            text="✓",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#2ecc71"
        )
        icon_label.pack(side="left", padx=(10, 5), pady=10)
        
        # Message
        message_label = ctk.CTkLabel(
            toast,
            text="Suppression effectuée avec succès",
            font=ctk.CTkFont(size=12)
        )
        message_label.pack(side="left", padx=(0, 10), pady=10)
        
        # Positionner le toast en bas de l'écran
        toast.place(relx=0.5, rely=0.95, anchor="center")
        
        # Faire disparaître le toast après quelques secondes
        def hide_toast():
            toast.destroy()
        
        self.parent.after(3000, hide_toast)
    
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
    
    def debounced_filter_documents(self, *args):
        """
        Applique un debounce sur le filtrage des documents
        """
        # Annuler le timer précédent s'il existe
        if self.filter_timer:
            self.parent.after_cancel(self.filter_timer)
        
        # Définir un nouveau timer
        self.filter_timer = self.parent.after(self.debounce_delay, self.load_documents_async)
    
    def apply_filters(self, documents):
        """
        Applique les filtres aux documents
        Version optimisée pour la performance
        
        Args:
            documents: Liste des documents à filtrer
            
        Returns:
            list: Documents filtrés
        """
        start_time = time.time()
        filtered = documents
        
        # Préparer les filtres une seule fois
        client_filter = self.client_var.get()
        type_filter = self.type_var.get()
        search_text = self.search_var.get().lower()
        
        # Filtre par client (optimisé)
        if client_filter and client_filter != "Tous les clients":
            # Créer un dictionnaire pour une recherche plus rapide
            client_dict = {c.get("name"): c.get("id") for c in self.model.clients}
            client_id = client_dict.get(client_filter)
            
            if client_id:
                filtered = [d for d in filtered if d.get("client_id") == client_id]
        
        # Filtre par type
        if type_filter and type_filter != "Tous les types":
            filtered = [d for d in filtered if d.get("type") == type_filter.lower()]
        
        # Filtre par recherche (optimisé pour éviter les recherches redondantes)
        if search_text:
            # Créer une fonction de test pour éviter les calculs répétés
            def matches_search(doc):
                return (
                    search_text in doc.get("title", "").lower() or 
                    search_text in doc.get("description", "").lower()
                )
            
            filtered = [d for d in filtered if matches_search(d)]
        
        # Mesurer le temps de filtrage
        filter_time = time.time() - start_time
        self.performance_metrics['filter_time'] = filter_time
        
        logger.debug(f"Filtrage de {len(documents)} documents en {filter_time:.3f}s, résultat: {len(filtered)} documents")
        
        return filtered
    
    def new_document(self):
        """
        Crée un nouveau document
        """
        # Cette méthode sera implémentée plus tard
        logger.info("Action: Nouveau document (non implémentée)")
        
    def import_document(self):
        """
        Importe un document depuis un fichier externe
        """
        # Cette méthode sera implémentée plus tard
        logger.info("Action: Importer un document (non implémentée)")
    
    def open_document(self, document_id):
        """
        Ouvre un document pour le visualiser ou le modifier
        
        Args:
            document_id: ID du document à ouvrir
        """
        # Cette méthode sera implémentée plus tard
        logger.info(f"Action: Ouvrir le document {document_id} (non implémentée)")
    
    def download_document(self, document_id):
        """
        Télécharge un document
        
        Args:
            document_id: ID du document à télécharger
        """
        # Cette méthode sera implémentée plus tard
        logger.info(f"Action: Télécharger le document {document_id} (non implémentée)")
    
    def show_error(self, parent, message):
        """
        Affiche un message d'erreur dans le style du Dashboard
        
        Args:
            parent: Widget parent
            message: Message d'erreur
        """
        dialog = ctk.CTkToplevel(parent)
        dialog.title("Erreur")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Frame principal avec padding
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre avec icône
        title_label = ctk.CTkLabel(
            main_frame,
            text="❌ Erreur",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Message
        message_label = ctk.CTkLabel(
            main_frame,
            text=message,
            wraplength=360
        )
        message_label.pack(pady=10)
        
        # Bouton OK
        ok_button = ctk.CTkButton(
            main_frame,
            text="OK",
            width=100,
            command=dialog.destroy
        )
        ok_button.pack(pady=10)
    
    def show_success(self, message):
        """
        Affiche une boîte de dialogue de succès dans le style du Dashboard
        
        Args:
            message: Message de succès
        """
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Succès")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Frame principal avec padding
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre avec icône
        title_label = ctk.CTkLabel(
            main_frame,
            text="✅ Succès",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Message
        message_label = ctk.CTkLabel(
            main_frame,
            text=message,
            wraplength=360
        )
        message_label.pack(pady=10)
        
        # Bouton OK
        ok_button = ctk.CTkButton(
            main_frame,
            text="OK",
            width=100,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=dialog.destroy
        )
        ok_button.pack(pady=10)
    
    def show_success_toast(self, message):
        """
        Affiche une notification toast de succès dans le style du Dashboard
        
        Args:
            message: Message à afficher
        """
        # Créer un toast en bas de l'écran
        toast = ctk.CTkFrame(self.parent, fg_color="#2ecc71")
        
        # Message avec icône
        message_label = ctk.CTkLabel(
            toast,
            text=f"✅ {message}",
            font=ctk.CTkFont(size=14),
            text_color="white"
        )
        message_label.pack(padx=20, pady=10)
        
        # Positionner le toast en bas de l'écran
        toast.place(relx=0.5, rely=0.95, anchor="center")
        
        # Faire disparaître le toast après quelques secondes
        def hide_toast():
            toast.destroy()
        
        self.parent.after(3000, hide_toast)

    def on_create_document(self):
        """Gère la création d'un nouveau document"""
        # Vérifier le compteur d'utilisation
        usage = self.usage_tracker.increment_usage()
        if usage["should_register"]:
            # Trouver la fenêtre principale
            root = self.parent
            while root.master is not None:
                root = root.master
            
            # Afficher le dialogue d'inscription avec un message sur l'utilisation
            if hasattr(root, "_show_auth_dialog"):
                root._show_auth_dialog()
            return
        
        # Si l'utilisateur n'a pas atteint la limite
        self._show_document_creator()
    
    def on_export_pdf(self):
        """Gère l'export en PDF"""
        # L'export PDF est une fonctionnalité gratuite, mais on compte quand même l'utilisation
        usage = self.usage_tracker.increment_usage()
        if usage["should_register"]:
            # Afficher un message suggérant l'inscription
            messagebox.showinfo(
                "Inscription suggérée",
                f"Vous avez utilisé l'application {usage['count']} fois.\n\n{usage['message']}\n\nVous pouvez continuer à utiliser cette fonctionnalité gratuitement."
            )
        
        # Procéder à l'export
        self._export_to_pdf()


class DocumentCacheManager:
    """
    Gestionnaire de cache pour les documents
    Permet d'optimiser l'accès aux documents fréquemment utilisés
    """
    
    def __init__(self, max_size=100):
        """
        Initialise le gestionnaire de cache
        
        Args:
            max_size: Taille maximale du cache
        """
        self.cache = {}
        self.access_count = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, doc_id):
        """
        Récupère un document du cache
        
        Args:
            doc_id: ID du document
            
        Returns:
            dict: Document s'il est en cache, None sinon
        """
        if doc_id in self.cache:
            # Incrémenter le compteur d'accès
            self.access_count[doc_id] = self.access_count.get(doc_id, 0) + 1
            self.hits += 1
            return self.cache[doc_id]
        
        self.misses += 1
        return None
    
    def put(self, doc_id, document):
        """
        Ajoute un document au cache
        
        Args:
            doc_id: ID du document
            document: Document à mettre en cache
        """
        # Vérifier si le cache est plein
        if len(self.cache) >= self.max_size:
            # Supprimer l'élément le moins accédé
            least_accessed = min(self.access_count.items(), key=lambda x: x[1])
            self.cache.pop(least_accessed[0], None)
            self.access_count.pop(least_accessed[0], None)
        
        # Ajouter le nouveau document
        self.cache[doc_id] = document
        self.access_count[doc_id] = 1
    
    def clear(self):
        """
        Vide le cache
        """
        self.cache.clear()
        self.access_count.clear()
    
    def get_stats(self):
        """
        Retourne les statistiques du cache
        
        Returns:
            dict: Statistiques du cache
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests) * 100 if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }


class DocumentIndexer:
    """
    Indexeur de documents pour recherche rapide
    Permet d'accélérer les recherches sur de grandes collections
    """
    
    def __init__(self):
        """
        Initialise l'indexeur
        """
        self.index = {}
        self.document_map = {}
        self.is_dirty = False
    
    def index_documents(self, documents):
        """
        Indexe une collection de documents
        
        Args:
            documents: Documents à indexer
        """
        # Réinitialiser l'index
        self.index = {}
        self.document_map = {}
        
        # Indexer chaque document
        for doc in documents:
            doc_id = doc.get("id")
            if not doc_id:
                continue
            
            # Stocker une référence au document
            self.document_map[doc_id] = doc
            
            # Indexer le titre
            self._index_field(doc_id, "title", doc.get("title", ""))
            
            # Indexer la description
            self._index_field(doc_id, "description", doc.get("description", ""))
            
            # Indexer le type
            self._index_field(doc_id, "type", doc.get("type", ""))
        
        self.is_dirty = False
        
        return len(self.document_map)
    
    def _index_field(self, doc_id, field, value):
        """
        Indexe un champ de document
        
        Args:
            doc_id: ID du document
            field: Nom du champ
            value: Valeur du champ
        """
        if not value:
            return
        
        # Convertir en minuscules
        value = str(value).lower()
        
        # Tokeniser (diviser en mots)
        tokens = value.split()
        
        # Indexer chaque mot
        for token in tokens:
            if len(token) < 2:
                continue
                
            # Créer l'entrée d'index si elle n'existe pas
            if token not in self.index:
                self.index[token] = set()
            
            # Ajouter le document à l'index
            self.index[token].add(doc_id)
    
    def search(self, query, fields=None):
        """
        Recherche des documents
        
        Args:
            query: Requête de recherche
            fields: Champs à considérer (None pour tous)
            
        Returns:
            list: Documents correspondants
        """
        if not query or not self.index:
            return []
        
        # Convertir la requête en minuscules
        query = query.lower()
        
        # Tokeniser la requête
        tokens = query.split()
        
        # Ensemble des documents correspondants
        result_ids = None
        
        # Pour chaque token
        for token in tokens:
            if len(token) < 2:
                continue
                
            # Documents correspondant à ce token
            matching_docs = self.index.get(token, set())
            
            if result_ids is None:
                result_ids = matching_docs
            else:
                # Intersection avec les résultats précédents
                result_ids = result_ids.intersection(matching_docs)
            
            # Si plus aucun document ne correspond, arrêter
            if not result_ids:
                break
        
        # Si aucun résultat
        if not result_ids:
            return []
        
        # Récupérer les documents complets
        results = [self.document_map[doc_id] for doc_id in result_ids]
        
        return results
    
    def add_document(self, document):
        """
        Ajoute un document à l'index
        
        Args:
            document: Document à ajouter
        """
        doc_id = document.get("id")
        if not doc_id:
            return False
        
        # Ajouter à la carte des documents
        self.document_map[doc_id] = document
        
        # Indexer les champs
        self._index_field(doc_id, "title", document.get("title", ""))
        self._index_field(doc_id, "description", document.get("description", ""))
        self._index_field(doc_id, "type", document.get("type", ""))
        
        self.is_dirty = True
        return True
    
    def remove_document(self, doc_id):
        """
        Supprime un document de l'index
        
        Args:
            doc_id: ID du document à supprimer
            
        Returns:
            bool: True si le document a été supprimé
        """
        if doc_id not in self.document_map:
            return False
        
        # Supprimer de la carte des documents
        del self.document_map[doc_id]
        
        # Supprimer des index
        for token, docs in self.index.items():
            if doc_id in docs:
                docs.remove(doc_id)
        
        self.is_dirty = True
        return True
    
    def get_stats(self):
        """
        Retourne les statistiques de l'index
        
        Returns:
            dict: Statistiques de l'index
        """
        return {
            "document_count": len(self.document_map),
            "token_count": len(self.index),
            "is_dirty": self.is_dirty
        }


class PerformanceMonitor:
    """
    Moniteur de performance pour suivre les métriques d'exécution
    """
    
    def __init__(self):
        """
        Initialise le moniteur de performance
        """
        self.metrics = {}
        self.start_times = {}
        self.thresholds = {
            "render_time": 0.5,  # secondes
            "load_time": 1.0,    # secondes
            "filter_time": 0.3   # secondes
        }
    
    def start_timer(self, name):
        """
        Démarre un chronomètre
        
        Args:
            name: Nom du chronomètre
        """
        self.start_times[name] = time.time()
    
    def stop_timer(self, name):
        """
        Arrête un chronomètre et enregistre la durée
        
        Args:
            name: Nom du chronomètre
            
        Returns:
            float: Durée en secondes
        """
        if name not in self.start_times:
            return 0
        
        duration = time.time() - self.start_times[name]
        
        # Enregistrer la métrique
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append(duration)
        
        # Conserver uniquement les 100 dernières valeurs
        if len(self.metrics[name]) > 100:
            self.metrics[name].pop(0)
        
        # Vérifier si la durée dépasse le seuil
        threshold = self.thresholds.get(name)
        if threshold and duration > threshold:
            logger.warning(f"Performance: {name} a pris {duration:.3f}s (seuil: {threshold:.3f}s)")
        
        return duration
    
    def get_average(self, name):
        """
        Calcule la moyenne pour une métrique
        
        Args:
            name: Nom de la métrique
            
        Returns:
            float: Moyenne ou 0 si aucune donnée
        """
        values = self.metrics.get(name, [])
        if not values:
            return 0
        
        return sum(values) / len(values)
    
    def get_all_metrics(self):
        """
        Retourne toutes les métriques
        
        Returns:
            dict: Métriques calculées
        """
        result = {}
        
        for name, values in self.metrics.items():
            if not values:
                continue
                
            result[name] = {
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "last": values[-1],
                "count": len(values)
            }
        
        return result
    
    def reset(self):
        """
        Réinitialise toutes les métriques
        """
        self.metrics.clear()
        self.start_times.clear()


class PerformanceOptimizedDocumentView:
    """
    Classe utilitaire pour les méthodes avancées d'optimisation de performance
    Cette classe étend les fonctionnalités de DocumentView avec des méthodes spécialisées
    """
    
    @staticmethod
    def batch_process_documents(documents, batch_size=50, process_func=None):
        """
        Traite les documents par lots pour éviter les blocages de l'interface
        
        Args:
            documents: Liste de documents à traiter
            batch_size: Taille de chaque lot
            process_func: Fonction de traitement à appliquer
            
        Returns:
            list: Documents traités
        """
        results = []
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        for i in range(total_batches):
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, len(documents))
            batch = documents[start_idx:end_idx]
            
            # Appliquer la fonction de traitement si définie
            if process_func:
                processed_batch = process_func(batch)
                results.extend(processed_batch)
            else:
                results.extend(batch)
                
            # Pause pour permettre à l'interface de respirer
            time.sleep(0.001)
            
        return results
    
    @staticmethod
    def optimize_document_for_display(document):
        """
        Optimise un document pour l'affichage en réduisant sa taille
        
        Args:
            document: Document à optimiser
            
        Returns:
            dict: Document optimisé
        """
        # Créer une copie légère du document
        optimized = {
            "id": document.get("id"),
            "title": document.get("title", "Sans titre"),
            "type": document.get("type", ""),
            "date": document.get("date", ""),
            "client_id": document.get("client_id", "")
        }
        
        # Tronquer la description si elle est trop longue
        description = document.get("description", "")
        if description and len(description) > 150:
            optimized["description"] = description[:147] + "..."
        else:
            optimized["description"] = description
        
        return optimized
    
    @staticmethod
    def create_virtual_scroll_handler(parent, content_frame, document_renderer, items, viewport_size=10):
        """
        Crée un gestionnaire de défilement virtuel pour améliorer les performances
        
        Args:
            parent: Widget parent
            content_frame: Cadre de contenu
            document_renderer: Fonction de rendu pour chaque document
            items: Liste d'éléments à afficher
            viewport_size: Nombre d'éléments visibles à la fois
            
        Returns:
            function: Fonction de mise à jour du défilement
        """
        # Variables pour le suivi de la position de défilement
        current_offset = 0
        last_rendered_range = (0, 0)
        
        def update_scroll_position(offset):
            nonlocal current_offset, last_rendered_range
            
            # Calculer les indices visibles
            start_idx = max(0, offset)
            end_idx = min(len(items), start_idx + viewport_size)
            
            # Vérifier si le rendu est nécessaire
            if (start_idx, end_idx) != last_rendered_range:
                # Nettoyer les widgets précédents
                for widget in content_frame.winfo_children():
                    widget.destroy()
                
                # Rendre uniquement les éléments visibles
                visible_items = items[start_idx:end_idx]
                for i, item in enumerate(visible_items):
                    document_renderer(content_frame, item, i)
                
                # Mettre à jour la plage rendue
                last_rendered_range = (start_idx, end_idx)
                current_offset = offset
        
        # Retourner la fonction de mise à jour
        return update_scroll_position
    
    @staticmethod
    def calculate_memory_usage(documents):
        """
        Estime l'utilisation mémoire d'une collection de documents
        
        Args:
            documents: Liste de documents
            
        Returns:
            int: Utilisation mémoire estimée en octets
        """
        import sys
        
        # Fonction pour estimer la taille d'une valeur
        def get_size(obj):
            if isinstance(obj, str):
                return sys.getsizeof(obj)
            elif isinstance(obj, dict):
                return sys.getsizeof(obj) + sum(get_size(k) + get_size(v) for k, v in obj.items())
            elif isinstance(obj, list):
                return sys.getsizeof(obj) + sum(get_size(item) for item in obj)
            else:
                return sys.getsizeof(obj)
        
        # Calculer la taille totale
        total_size = 0
        sample_size = min(100, len(documents))  # Limiter à 100 documents pour estimer
        
        if sample_size > 0:
            for i in range(sample_size):
                total_size += get_size(documents[i])
            
            # Extrapoler pour tous les documents
            avg_size = total_size / sample_size
            total_estimated_size = avg_size * len(documents)
            
            return int(total_estimated_size)
        
        return 0


def apply_performance_optimizations(document_view):
    """
    Applique des optimisations de performance à une vue de documents
    
    Args:
        document_view: Vue de documents à optimiser
    """
    # Créer un gestionnaire de cache
    cache = DocumentCacheManager(max_size=100)
    document_view.cache = cache
    
    # Créer un indexeur de documents
    indexer = DocumentIndexer()
    document_view.indexer = indexer
    
    # Indexer les documents actuels
    indexer.index_documents(document_view.model.documents)
    
    # Créer un moniteur de performance
    monitor = PerformanceMonitor()
    document_view.performance_monitor = monitor
    
    # Remplacer la méthode de recherche par une version optimisée
    original_filter = document_view.apply_filters
    
    def optimized_filter(documents):
        """
        Version optimisée du filtrage des documents
        """
        # Démarrer le chronomètre
        monitor.start_timer("filter_time")
        
        # Obtenir le texte de recherche
        search_text = document_view.search_var.get().lower()
        
        # Si une recherche est effectuée, utiliser l'indexeur
        if search_text and len(search_text) >= 2:
            # Rechercher les documents
            matching_docs = indexer.search(search_text)
            
            # Appliquer les autres filtres
            result = original_filter([d for d in matching_docs if d in documents])
        else:
            # Utiliser le filtrage standard
            result = original_filter(documents)
        
        # Arrêter le chronomètre
        filter_time = monitor.stop_timer("filter_time")
        logger.debug(f"Filtrage optimisé en {filter_time:.3f}s")
        
        return result
    
    # Remplacer la méthode
    document_view.apply_filters = optimized_filter
    
    # Optimiser le chargement des documents
    original_update = document_view.update_view
    
    def optimized_update():
        """
        Version optimisée de la mise à jour de la vue
        """
        # Démarrer le chronomètre
        monitor.start_timer("update_time")
        
        # Exécuter la mise à jour originale
        original_update()
        
        # Arrêter le chronomètre
        update_time = monitor.stop_timer("update_time")
        logger.debug(f"Mise à jour optimisée en {update_time:.3f}s")
    
    # Remplacer la méthode
    document_view.update_view = optimized_update
    
    logger.info("Optimisations de performance appliquées avec succès")


def log_performance_metrics(description, start_time):
    """
    Fonction utilitaire pour journaliser les métriques de performance
    
    Args:
        description: Description de l'opération
        start_time: Heure de début de l'opération
    """
    global _last_render_time, _render_count, _avg_render_time
    
    duration = time.time() - start_time
    _last_render_time = duration
    _render_count += 1
    
    # Calculer la moyenne mobile
    if _avg_render_time == 0:
        _avg_render_time = duration
    else:
        _avg_render_time = (_avg_render_time * 0.9) + (duration * 0.1)
    
    logger.debug(f"Performance: {description} en {duration:.3f}s (moy: {_avg_render_time:.3f}s)")
    
    if duration > 1.0:  # Plus d'une seconde est considéré comme lent
        logger.warning(f"Performance lente: {description} a pris {duration:.3f}s")


def memory_profile():
    """
    Fournit des informations sur l'utilisation mémoire du processus
    
    Returns:
        dict: Informations sur l'utilisation mémoire
    """
    import os
    import psutil
    
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        return {
            "rss": mem_info.rss / 1024 / 1024,  # Mégaoctets
            "vms": mem_info.vms / 1024 / 1024,  # Mégaoctets
            "percent": process.memory_percent(),
            "cpu_percent": process.cpu_percent(interval=0.1)
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des informations mémoire: {e}")
        return {
            "error": str(e)
        }


# Variables globales pour le traçage des performances
_last_render_time = 0
_render_count = 0
_avg_render_time = 0


class DocumentFormView:
    """
    Vue pour l'ajout et l'édition de documents
    """
    
    def __init__(self, parent, app_model, on_save_callback=None):
        """
        Initialise la vue de formulaire de document
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
            on_save_callback: Fonction à appeler après la sauvegarde
        """
        self.parent = parent
        self.model = app_model
        self.on_save_callback = on_save_callback
        self.document_id = None
        self.document_data = {}
        self.temp_file_path = None
        
        # Si le document est nouveau, générer un ID temporaire
        self.is_new_document = True
        
        # Initialiser la vue du formulaire
        self._create_form_view()
    
    def _create_form_view(self):
        """
        Crée la vue du formulaire
        """
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Nouveau document")
        self.dialog.geometry("600x700")
        self.dialog.resizable(True, True)
        self.dialog.grab_set()  # Modal
        self.dialog.focus_set()
        
        # Centrer la fenêtre
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - self.dialog.winfo_width()) // 2
        y = (self.dialog.winfo_screenheight() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Créer un cadre principal avec défilement
        main_frame = ctk.CTkScrollableFrame(self.dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # 1. Sélection du modèle
        template_frame = ctk.CTkFrame(main_frame)
        template_frame.pack(fill=ctk.X, pady=10)
        
        ctk.CTkLabel(template_frame, text="1. Sélectionner un modèle", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        # Liste des modèles
        template_list_frame = ctk.CTkFrame(template_frame)
        template_list_frame.pack(fill=ctk.X, padx=10, pady=10)
        
        ctk.CTkLabel(template_list_frame, text="Modèle:").pack(side=ctk.LEFT, padx=5)
        self.template_var = ctk.StringVar()
        template_options = [f"{t.get('name')} ({t.get('type', '')})" for t in self.model.templates]
        self.template_combo = ctk.CTkComboBox(template_list_frame, values=template_options, 
                                         variable=self.template_var, width=350)
        self.template_combo.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)
        
        # Description du modèle sélectionné
        self.template_desc = ctk.CTkLabel(template_frame, text="", justify=ctk.LEFT, wraplength=550)
        self.template_desc.pack(fill=ctk.X, padx=10, pady=5)
        
        # 2. Sélection du client
        client_frame = ctk.CTkFrame(main_frame)
        client_frame.pack(fill=ctk.X, pady=10)
        
        ctk.CTkLabel(client_frame, text="2. Sélectionner un client", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        # Liste des clients
        client_list_frame = ctk.CTkFrame(client_frame)
        client_list_frame.pack(fill=ctk.X, padx=10, pady=10)
        
        ctk.CTkLabel(client_list_frame, text="Client:").pack(side=ctk.LEFT, padx=5)
        self.client_var = ctk.StringVar()
        client_options = [f"{c.get('name')} ({c.get('company', '')})" for c in self.model.clients]
        self.client_combo = ctk.CTkComboBox(client_list_frame, values=client_options, 
                                       variable=self.client_var, width=350)
        self.client_combo.pack(side=ctk.LEFT, padx=5, fill=ctk.X, expand=True)
        
        # Informations du client sélectionné
        self.client_info = ctk.CTkLabel(client_frame, text="", justify=ctk.LEFT, wraplength=550)
        self.client_info.pack(fill=ctk.X, padx=10, pady=5)
        
        # 3. Informations du document
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill=ctk.X, pady=10)
        
        ctk.CTkLabel(info_frame, text="3. Informations du document", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        info_list_frame = ctk.CTkFrame(info_frame)
        info_list_frame.pack(fill=ctk.X, padx=10, pady=10)
        
        # Titre
        title_row = ctk.CTkFrame(info_list_frame)
        title_row.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(title_row, text="Titre:").pack(side=ctk.LEFT, padx=5)
        self.title_var = ctk.StringVar()
        self.title_entry = ctk.CTkEntry(title_row, textvariable=self.title_var, width=400)
        self.title_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5)
        
        # Date
        date_row = ctk.CTkFrame(info_list_frame)
        date_row.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(date_row, text="Date:").pack(side=ctk.LEFT, padx=5)
        self.date_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_entry = ctk.CTkEntry(date_row, textvariable=self.date_var, width=200)
        self.date_entry.pack(side=ctk.LEFT, padx=5)
        
        # Description
        desc_row = ctk.CTkFrame(info_list_frame)
        desc_row.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(desc_row, text="Description:").pack(side=ctk.LEFT, padx=5)
        description_frame = ctk.CTkFrame(desc_row)
        description_frame.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5)
        self.desc_text = ctk.CTkTextbox(description_frame, width=400, height=80)
        self.desc_text.pack(fill=ctk.BOTH, expand=True)
        
        # 4. Variables du modèle
        variables_frame = ctk.CTkFrame(main_frame)
        variables_frame.pack(fill=ctk.X, pady=10)
        
        ctk.CTkLabel(variables_frame, text="4. Variables du modèle", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        # Zone de défilement pour les variables
        self.variables_scroll = ctk.CTkScrollableFrame(variables_frame, height=150)
        self.variables_scroll.pack(fill=ctk.X, padx=10, pady=10)
        
        # Les widgets des variables seront ajoutés dynamiquement
        self.variable_widgets = {}
        
        # Connecter les changements de sélection aux fonctions de mise à jour
        self.template_var.trace_add("write", self._update_template_info)
        self.client_var.trace_add("write", self._update_client_info)
        
        # Boutons
        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.pack(fill=ctk.X, pady=10, padx=20)
        
        # Bouton Annuler
        ctk.CTkButton(
            button_frame,
            text="Annuler",
            command=self.dialog.destroy,
            width=100
        ).pack(side=ctk.RIGHT, padx=10)
        
        # Bouton Enregistrer
        ctk.CTkButton(
            button_frame,
            text="Enregistrer",
            command=self._save_document,
            width=100
        ).pack(side=ctk.RIGHT, padx=10)
        
        # Si des données sont fournies, les charger
        if self.document_data:
            self._load_document_data()
    
    def _load_document_data(self):
        """
        Charge les données du document dans le formulaire
        """
        self.title_var.set(self.document_data.get("title", ""))
        self.date_var.set(self.document_data.get("date", datetime.now().strftime("%Y-%m-%d")))
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", self.document_data.get("description", ""))
        self.template_var.set(f"{self.document_data.get('template', {}).get('name')} ({self.document_data.get('template', {}).get('type', '')})")
        self.client_var.set(f"{self.document_data.get('client', {}).get('name')} ({self.document_data.get('client', {}).get('company', '')})")
        self.client_info.configure(text=self.document_data.get("client_info", ""))
        self.variables_scroll.pack_forget()
        self.variable_widgets.clear()
        for var_name, var_value in self.document_data.get("variables", {}).items():
            self._add_variable_widget(var_name, var_value)
    
    def _add_variable_widget(self, var_name, var_value):
        """
        Ajoute un widget pour une variable du modèle
        """
        widget = ctk.CTkEntry(self.variables_scroll, width=300)
        widget.pack(fill=ctk.X, padx=10, pady=5)
        widget.insert(0, var_value)
        self.variable_widgets[var_name] = widget
    
    def _update_template_info(self, *args):
        """
        Met à jour les informations du modèle sélectionné
        """
        template_name = self.template_var.get()
        template = self.model.get_template_by_name(template_name)
        if template:
            self.template_desc.configure(text=template.get("description", ""))
            self.variables_scroll.pack_forget()
            self.variable_widgets.clear()
            for var_name, var_value in template.get("variables", {}).items():
                self._add_variable_widget(var_name, var_value)
            self.variables_scroll.pack(fill=ctk.X, padx=10, pady=10)
        else:
            self.template_desc.configure(text="Modèle non trouvé")
            self.variables_scroll.pack_forget()
            self.variable_widgets.clear()
    
    def _update_client_info(self, *args):
        """
        Met à jour les informations du client sélectionné
        """
        client_name = self.client_var.get()
        client = self.model.get_client_by_name(client_name)
        if client:
            self.client_info.configure(text=f"Informations du client: {client.get('company', '')}")
        else:
            self.client_info.configure(text="Client non trouvé")
    
    def _save_document(self):
        """
        Enregistre le document
        """
        # Récupérer les données du formulaire
        title = self.title_var.get().strip()
        date = self.date_var.get().strip()
        description = self.desc_text.get("1.0", "end-1c").strip()
        
        # Validation
        if not title:
            self.show_error("Le titre est obligatoire")
            return
        
        if not self.template_var.get():
            self.show_error("Veuillez sélectionner un modèle")
            return
        
        if not self.client_var.get():
            self.show_error("Veuillez sélectionner un client")
            return
        
        # Récupérer le modèle et le client
        template = self.get_template_by_name(self.template_var.get())
        client = self.get_client_by_name(self.client_var.get())
        
        if not template:
            self.show_error("Modèle introuvable")
            return
        
        if not client:
            self.show_error("Client introuvable")
            return
        
        # Récupérer les valeurs des variables
        variables = {}
        for var_name, widget in self.variable_widgets.items():
            variables[var_name] = widget.get().strip()
        
        # Préparer les données du document
        document_data = {
            "title": title,
            "type": template.get("type", ""),
            "date": date,
            "description": description,
            "template_id": template.get("id"),
            "client_id": client.get("id"),
            "variables": variables,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Si c'est une mise à jour
        if self.document_id:
            document_data["id"] = self.document_id
            success = self.model.update_document(self.document_id, document_data)
            success_message = "Document mis à jour avec succès"
        else:
            # Nouveau document
            new_id = self.model.add_document(document_data)
            success = new_id is not None
            success_message = "Document créé avec succès"
        
        if success:
            # Afficher le message de succès
            self.show_success_toast(success_message)
            
            # Fermer la boîte de dialogue après un court délai
            self.dialog.after(1000, self.dialog.destroy)
            
            # Appeler le callback si défini
            if self.on_save_callback:
                self.on_save_callback()
        else:
            self.show_error("Erreur lors de l'enregistrement du document")
    
    def _show_error(self, message):
        """
        Affiche un message d'erreur
        
        Args:
            message: Message d'erreur
        """
        messagebox.showerror("Erreur", message, parent=self.dialog)
    
    def load_document(self, document_id):
        """
        Charge un document existant dans le formulaire
        
        Args:
            document_id: ID du document à charger
        """
        document = self.model.get_document_by_id(document_id)
        if not document:
            self._show_error(f"Document introuvable (ID: {document_id})")
            return False
        
        # Mettre à jour les données et l'interface
        self.document_id = document_id
        self.document_data = document
        self.is_new_document = False
        
        # Mettre à jour le titre de la fenêtre
        self.dialog.title(f"Modifier le document - {document.get('title', '')}")
        
        # Mettre à jour les champs du formulaire
        self.title_var.set(document.get("title", ""))
        self.type_var.set(document.get("type", ""))
        
        # Mettre à jour le client
        client_id = document.get("client_id")
        if client_id:
            for client in self.model.clients:
                if client.get("id") == client_id:
                    self.client_var.set(client.get("name", ""))
                    break
        else:
            self.client_var.set("Aucun client")
        
        # Mettre à jour la description
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", document.get("description", ""))
        
        # Mettre à jour le contenu
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", document.get("content", ""))
        
        return True
    
    def get_template_by_name(self, template_name):
        """
        Récupère un modèle par son nom
        
        Args:
            template_name: Nom du modèle (avec le type entre parenthèses)
            
        Returns:
            dict: Le modèle trouvé ou None
        """
        try:
            # Extraire le nom sans le type
            name = template_name.split(" (")[0]
            
            # Chercher le modèle
            return next((t for t in self.model.templates if t.get("name") == name), None)
        except:
            return None
    
    def get_client_by_name(self, client_name):
        """
        Récupère un client par son nom
        
        Args:
            client_name: Nom du client (avec la société entre parenthèses)
            
        Returns:
            dict: Le client trouvé ou None
        """
        try:
            # Extraire le nom sans la société
            name = client_name.split(" (")[0]
            
            # Chercher le client
            return next((c for c in self.model.clients if c.get("name") == name), None)
        except:
            return None
    
    def show_error(self, message):
        """
        Affiche un message d'erreur dans le style du Dashboard
        
        Args:
            message: Message d'erreur
        """
        dialog = ctk.CTkToplevel(self.dialog)
        dialog.title("Erreur")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.dialog)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Frame principal avec padding
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre avec icône
        title_label = ctk.CTkLabel(
            main_frame,
            text="❌ Erreur",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Message
        message_label = ctk.CTkLabel(
            main_frame,
            text=message,
            wraplength=360
        )
        message_label.pack(pady=10)
        
        # Bouton OK
        ok_button = ctk.CTkButton(
            main_frame,
            text="OK",
            width=100,
            command=dialog.destroy
        )
        ok_button.pack(pady=10)
    
    def show_success(self, message):
        """
        Affiche une boîte de dialogue de succès dans le style du Dashboard
        
        Args:
            message: Message de succès
        """
        dialog = ctk.CTkToplevel(self.dialog)
        dialog.title("Succès")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.dialog)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Frame principal avec padding
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre avec icône
        title_label = ctk.CTkLabel(
            main_frame,
            text="✅ Succès",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Message
        message_label = ctk.CTkLabel(
            main_frame,
            text=message,
            wraplength=360
        )
        message_label.pack(pady=10)
        
        # Bouton OK
        ok_button = ctk.CTkButton(
            main_frame,
            text="OK",
            width=100,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=dialog.destroy
        )
        ok_button.pack(pady=10)
    
    def show_success_toast(self, message):
        """
        Affiche une notification toast de succès dans le style du Dashboard
        
        Args:
            message: Message à afficher
        """
        # Créer un toast en bas de l'écran
        toast = ctk.CTkFrame(self.dialog, fg_color="#2ecc71")
        
        # Message avec icône
        message_label = ctk.CTkLabel(
            toast,
            text=f"✅ {message}",
            font=ctk.CTkFont(size=14),
            text_color="white"
        )
        message_label.pack(padx=20, pady=10)
        
        # Positionner le toast en bas de l'écran
        toast.place(relx=0.5, rely=0.95, anchor="center")
        
        # Faire disparaître le toast après quelques secondes
        def hide_toast():
            toast.destroy()
        
        self.dialog.after(3000, hide_toast)


class DocumentImportExport:
    """
    Classe utilitaire pour l'import et l'export de documents
    """
    
    @staticmethod
    def export_document_to_pdf(document, output_path):
        """
        Exporte un document au format PDF
        
        Args:
            document: Document à exporter
            output_path: Chemin du fichier de sortie
            
        Returns:
            bool: True si l'export a réussi
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            
            # Styles pour le document
            styles = getSampleStyleSheet()
            title_style = styles["Heading1"]
            subtitle_style = styles["Heading2"]
            normal_style = styles["Normal"]
            
            # Créer le document
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            
            # Éléments à ajouter au document
            elements = []
            
            # Titre
            elements.append(Paragraph(document.get("title", "Sans titre"), title_style))
            elements.append(Spacer(1, 12))
            
            # Informations du document
            doc_info = [
                ["Type:", document.get("type", "").capitalize()],
                ["Date:", document.get("date", "")],
            ]
            
            # Ajouter le client si présent
            client_id = document.get("client_id")
            if client_id:
                from app_model import AppModel
                client = AppModel.get_client(client_id)
                if client:
                    doc_info.append(["Client:", client.get("name", "")])
            
            # Ajouter la table d'informations
            info_table = Table(doc_info, colWidths=[100, 400])
            info_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.black),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]))
            
            elements.append(info_table)
            elements.append(Spacer(1, 12))
            
            # Description si présente
            description = document.get("description")
            if description:
                elements.append(Paragraph("Description:", subtitle_style))
                elements.append(Spacer(1, 6))
                elements.append(Paragraph(description, normal_style))
                elements.append(Spacer(1, 12))
            
            # Contenu du document
            elements.append(Paragraph("Contenu:", subtitle_style))
            elements.append(Spacer(1, 6))
            
            # Diviser le contenu en paragraphes
            content = document.get("content", "")
            paragraphs = content.split("\n\n")
            
            for para in paragraphs:
                if para.strip():
                    elements.append(Paragraph(para, normal_style))
                    elements.append(Spacer(1, 6))
            
            # Construire le document
            doc.build(elements)
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export PDF: {e}")
            return False
    
    @staticmethod
    def import_document_from_file(file_path, app_model):
        """
        Importe un document depuis un fichier
        
        Args:
            file_path: Chemin du fichier à importer
            app_model: Modèle de l'application
            
        Returns:
            str or None: ID du document importé ou None en cas d'erreur
        """
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.txt', '.md', '.markdown']:
                # Importer fichier texte
                return DocumentImportExport._import_text_file(file_path, app_model)
            elif file_ext in ['.docx']:
                # Importer fichier Word
                return DocumentImportExport._import_docx_file(file_path, app_model)
            elif file_ext in ['.pdf']:
                # Importer fichier PDF
                return DocumentImportExport._import_pdf_file(file_path, app_model)
            else:
                logger.error(f"Format de fichier non supporté: {file_ext}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de l'import du document: {e}")
            return None
    
    @staticmethod
    def _import_text_file(file_path, app_model):
        """
        Importe un fichier texte
        
        Args:
            file_path: Chemin du fichier
            app_model: Modèle de l'application
            
        Returns:
            str or None: ID du document importé ou None en cas d'erreur
        """
        try:
            # Déterminer l'encodage du fichier
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                        break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                logger.error(f"Impossible de déterminer l'encodage du fichier: {file_path}")
                return None
            
            # Extraire le nom du fichier sans extension pour le titre
            file_name = os.path.basename(file_path)
            title = os.path.splitext(file_name)[0]
            
            # Créer les données du document
            document_data = {
                "title": title,
                "type": "document",
                "description": f"Document importé depuis {file_name}",
                "content": content,
                "date": datetime.now().isoformat()
            }
            
            # Ajouter le document au modèle
            return app_model.add_document(document_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import du fichier texte: {e}")
            return None
    
    @staticmethod
    def _import_docx_file(file_path, app_model):
        """
        Importe un fichier Word
        
        Args:
            file_path: Chemin du fichier
            app_model: Modèle de l'application
            
        Returns:
            str or None: ID du document importé ou None en cas d'erreur
        """
        try:
            import docx
            
            # Ouvrir le document Word
            doc = docx.Document(file_path)
            
            # Extraire le texte
            content = "\n\n".join([para.text for para in doc.paragraphs if para.text])
            
            # Extraire le nom du fichier sans extension pour le titre
            file_name = os.path.basename(file_path)
            title = os.path.splitext(file_name)[0]
            
            # Créer les données du document
            document_data = {
                "title": title,
                "type": "document",
                "description": f"Document importé depuis {file_name}",
                "content": content,
                "date": datetime.now().isoformat()
            }
            
            # Ajouter le document au modèle
            return app_model.add_document(document_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import du fichier Word: {e}")
            return None
    
    @staticmethod
    def _import_pdf_file(file_path, app_model):
        """
        Importe un fichier PDF
        
        Args:
            file_path: Chemin du fichier
            app_model: Modèle de l'application
            
        Returns:
            str or None: ID du document importé ou None en cas d'erreur
        """
        try:
            import PyPDF2
            
            # Ouvrir le document PDF
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Extraire le texte de chaque page
                content = ""
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    content += page.extract_text() + "\n\n"
            
            # Extraire le nom du fichier sans extension pour le titre
            file_name = os.path.basename(file_path)
            title = os.path.splitext(file_name)[0]
            
            # Créer les données du document
            document_data = {
                "title": title,
                "type": "document",
                "description": f"Document importé depuis {file_name}",
                "content": content,
                "date": datetime.now().isoformat()
            }
            
            # Ajouter le document au modèle
            return app_model.add_document(document_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import du fichier PDF: {e}")
            return None


class DocumentSearchHelper:
    """
    Classe utilitaire pour améliorer la recherche de documents
    """
    
    @staticmethod
    def search_documents(documents, query, fields=None):
        """
        Recherche des documents selon une requête
        
        Args:
            documents: Liste de documents
            query: Requête de recherche
            fields: Champs à considérer (None pour tous)
            
        Returns:
            list: Documents correspondants triés par pertinence
        """
        if not query:
            return documents
        
        query = query.lower()
        terms = query.split()
        default_fields = ["title", "description", "content", "type"]
        search_fields = fields if fields else default_fields
        
        results = []
        
        # Calculer un score pour chaque document
        for doc in documents:
            score = 0
            matches = 0
            
            for field in search_fields:
                field_value = str(doc.get(field, "")).lower()
                
                # Chercher chaque terme
                for term in terms:
                    if term in field_value:
                        # Le score dépend du champ et de la position
                        if field == "title":
                            score += 10  # Titre a le plus de poids
                            if field_value.startswith(term):
                                score += 5  # Bonus si le titre commence par le terme
                        elif field == "type":
                            score += 5  # Type a un poids moyen
                        elif field == "description":
                            score += 3  # Description a un poids moyen
                        else:
                            score += 1  # Autres champs ont moins de poids
                        
                        matches += 1
            
            # Si au moins un terme correspond
            if matches > 0:
                # Bonus pour les documents qui correspondent à plusieurs termes
                if matches == len(terms):
                    score *= 2
                
                results.append((doc, score))
        
        # Trier par score décroissant
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Retourner seulement les documents
        return [doc for doc, _ in results]
    
    @staticmethod
    def search_by_date_range(documents, start_date, end_date):
        """
        Recherche des documents dans une plage de dates
        
        Args:
            documents: Liste de documents
            start_date: Date de début (datetime ou str ISO)
            end_date: Date de fin (datetime ou str ISO)
            
        Returns:
            list: Documents dans la plage de dates
        """
        # Convertir les dates en objets datetime si nécessaire
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        filtered_docs = []
        
        for doc in documents:
            doc_date_str = doc.get("date", "")
            
            if not doc_date_str:
                continue
                
            try:
                # Convertir la date du document
                doc_date = datetime.fromisoformat(doc_date_str.replace('Z', '+00:00'))
                
                # Vérifier si la date est dans la plage
                if start_date <= doc_date <= end_date:
                    filtered_docs.append(doc)
            except (ValueError, TypeError):
                # Ignorer les documents avec des dates invalides
                continue
        
        return filtered_docs
    
    @staticmethod
    def get_document_statistics(documents):
        """
        Calcule des statistiques sur une collection de documents
        
        Args:
            documents: Liste de documents
            
        Returns:
            dict: Statistiques calculées
        """
        if not documents:
            return {
                "count": 0,
                "types": {},
                "clients": {},
                "dates": {
                    "newest": None,
                    "oldest": None,
                    "average": None
                },
                "word_count": {
                    "total": 0,
                    "average": 0,
                    "max": 0,
                    "min": 0
                }
            }
        
        stats = {
            "count": len(documents),
            "types": {},
            "clients": {},
            "dates": {},
            "word_count": {}
        }
        
        # Calculer les statistiques par type
        for doc in documents:
            doc_type = doc.get("type", "").lower()
            if doc_type:
                stats["types"][doc_type] = stats["types"].get(doc_type, 0) + 1
        
        # Calculer les statistiques par client
        client_ids = {}
        for doc in documents:
            client_id = doc.get("client_id")
            if client_id:
                client_ids[client_id] = client_ids.get(client_id, 0) + 1
        
        # Convertir les IDs de client en noms
        from app_model import AppModel
        for client_id, count in client_ids.items():
            client = AppModel.get_client(client_id)
            client_name = client.get("name", "Inconnu") if client else "Inconnu"
            stats["clients"][client_name] = count
        
        # Calculer les statistiques de dates
        dates = []
        for doc in documents:
            date_str = doc.get("date")
            if date_str:
                try:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    dates.append(date_obj)
                except (ValueError, TypeError):
                    continue
        
        if dates:
            stats["dates"]["newest"] = max(dates).isoformat()
            stats["dates"]["oldest"] = min(dates).isoformat()
            avg_timestamp = sum(dt.timestamp() for dt in dates) / len(dates)
            stats["dates"]["average"] = datetime.fromtimestamp(avg_timestamp).isoformat()
        
        # Calculer les statistiques de nombre de mots
        word_counts = []
        for doc in documents:
            content = doc.get("content", "")
            word_count = len(content.split())
            word_counts.append(word_count)
        
        if word_counts:
            stats["word_count"]["total"] = sum(word_counts)
            stats["word_count"]["average"] = stats["word_count"]["total"] / len(word_counts)
            stats["word_count"]["max"] = max(word_counts)
            stats["word_count"]["min"] = min(word_counts)
        
        return stats


# Point d'entrée pour l'initialisation des optimisations
def initialize_optimizations(app_model):
    """
    Point d'entrée pour initialiser toutes les optimisations de performance
    
    Args:
        app_model: Modèle de l'application
    """
    logger.info("Initialisation des optimisations de performance...")
    
    # Créer les objets de performance
    document_indexer = DocumentIndexer()
    document_indexer.index_documents(app_model.documents)
    
    # Stocker les références pour utilisation ultérieure
    app_model.performance = {
        "document_indexer": document_indexer,
        "cache_manager": DocumentCacheManager(),
        "performance_monitor": PerformanceMonitor()
    }
    
    # Journaliser les résultats
    stats = document_indexer.get_stats()
    logger.info(f"Indexation terminée: {stats['document_count']} documents, {stats['token_count']} tokens")
    
    return True