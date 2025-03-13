"""
Vue de gestion des clients pour l'application Vynal Docs Automator
Version optimisée pour les performances
"""

import logging
import threading
import queue
import time
import customtkinter as ctk
import tkinter.messagebox as messagebox
import csv
import pandas as pd

logger = logging.getLogger("VynalDocsAutomator.ClientView")

class ClientTable:
    """
    Composant de tableau pour afficher les clients
    Avec optimisations de performance
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
        
        # Cadre principal du tableau
        self.frame = ctk.CTkFrame(parent)
        
        # Cadre pour les en-têtes du tableau
        self.header_frame = ctk.CTkFrame(self.frame, fg_color=("gray80", "gray30"))
        self.header_frame.pack(fill=ctk.X, padx=0, pady=0)
        
        # Définir des poids pour chaque colonne (pour un alignement uniforme)
        self.column_weights = [2, 2, 3, 2, 1]  # Nom, Entreprise, Email, Téléphone, Actions
        for i, header in enumerate(headers):
            weight = self.column_weights[i] if i < len(self.column_weights) else 1
            self.header_frame.columnconfigure(i, weight=weight)
        
        # Ajouter les en-têtes dans la grille
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                self.header_frame,
                text=header,
                font=ctk.CTkFont(weight="bold"),
                anchor="w"
            ).grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
        
        # Cadre pour le contenu du tableau (avec défilement)
        self.content_frame = ctk.CTkScrollableFrame(self.frame)
        self.content_frame.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        
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
        
    def add_row(self, data):
        """
        Ajoute une ligne au tableau
        
        Args:
            data: Liste des données de la ligne. Si une donnée est une fonction,
                  elle sera appelée en lui passant le parent de la cellule.
        
        Returns:
            list: Liste des widgets de la ligne
        """
        row_widgets = []
        row_index = len(self.rows)
        
        # Cadre pour la ligne, avec fond alterné
        bg_color = ("gray95", "gray15") if row_index % 2 == 0 else ("white", "gray10")
        row_frame = ctk.CTkFrame(self.content_frame, fg_color=bg_color)
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
                widget.grid(row=0, column=i, sticky="nsew", padx=5, pady=3)
                row_widgets.append(widget)
            elif isinstance(cell_data, ctk.CTkBaseClass):
                cell_data.grid(row=0, column=i, sticky="nsew", padx=5, pady=3)
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
                cell.grid(row=0, column=i, sticky="nsew", padx=5, pady=3)
                row_widgets.append(cell)
        
        self.rows.append((row_frame, row_widgets))
        return row_widgets
    
    def add_rows_async(self, data_list):
        """
        Ajoute plusieurs lignes au tableau de manière asynchrone
        
        Args:
            data_list: Liste de données pour chaque ligne
        """
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
                    self.add_row(data)
            
            # Si des lignes restent à traiter, programmer le prochain lot
            if not self.rendering_queue.empty():
                self.parent.after(10, self._process_rendering_queue)
            else:
                self.is_rendering = False
        else:
            self.is_rendering = False
    
    def clear(self):
        """
        Efface toutes les lignes du tableau
        """
        for row_frame, _ in self.rows:
            row_frame.destroy()
        self.rows = []
        
        # Vider la file d'attente de rendu
        while not self.rendering_queue.empty():
            self.rendering_queue.get()
        
        self.is_rendering = False


class ClientView:
    """
    Vue de gestion des clients
    Permet de visualiser, ajouter, modifier et supprimer des clients
    Version optimisée pour les performances
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
        
        # Cadre principal de la vue
        self.frame = ctk.CTkFrame(parent)
        
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
        
        # Créer les composants de l'interface
        self.create_widgets()
        
        logger.info("ClientView optimisée initialisée")
    
    def create_widgets(self):
        """
        Crée les widgets de la vue
        """
        # Barre d'outils
        self.toolbar = ctk.CTkFrame(self.frame)
        self.toolbar.pack(fill=ctk.X, pady=10)
        
        # Bouton Nouveau client
        self.new_client_btn = ctk.CTkButton(self.toolbar, text="+ Nouveau client", command=self.show_client_form)
        self.new_client_btn.pack(side=ctk.LEFT, padx=10)
        
        # Bouton Importer
        self.import_btn = ctk.CTkButton(self.toolbar, text="Importer", command=self.import_clients)
        self.import_btn.pack(side=ctk.LEFT, padx=10)
        
        # Bouton Exporter
        self.export_btn = ctk.CTkButton(self.toolbar, text="Exporter", command=self.export_clients)
        self.export_btn.pack(side=ctk.LEFT, padx=10)
        
        # Indicateur de chargement
        self.loading_label = ctk.CTkLabel(
            self.toolbar,
            text="Chargement...",
            text_color="#3498db",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        # Ne pas l'afficher au démarrage
        
        # Zone de recherche
        self.search_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.search_frame.pack(side=ctk.RIGHT, padx=10)
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.debounced_filter_clients())
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Rechercher un client...", width=200, textvariable=self.search_var)
        self.search_entry.pack(side=ctk.LEFT)
        
        # Cadre pour la liste des clients
        self.list_frame = ctk.CTkFrame(self.frame)
        self.list_frame.pack(fill=ctk.BOTH, expand=True, pady=10)
        
        # Tableau des clients
        self.clients_table = ClientTable(self.list_frame, ["Nom", "Entreprise", "Email", "Téléphone", "Actions"])
        
        # Message affiché s'il n'y a aucun client
        self.no_clients_label = ctk.CTkLabel(self.list_frame, text="Aucun client disponible. Ajoutez des clients pour commencer.", font=ctk.CTkFont(size=12), fg_color="transparent", text_color="gray")
        self.no_clients_label.pack(pady=20)
    
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
                        search_text in client.get("email", "").lower()):
                        filtered_clients.append(client)
            else:
                filtered_clients = clients
            
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
                    # Bouton Éditer
                    edit_btn = ctk.CTkButton(actions_frame, text="Éditer", width=60, height=22, font=ctk.CTkFont(size=10),
                                             command=lambda cid=client.get("id"): self.edit_client(cid))
                    edit_btn.pack(side=ctk.LEFT, padx=1)
                    # Bouton Supprimer
                    delete_btn = ctk.CTkButton(actions_frame, text="Supprimer", width=60, height=22, font=ctk.CTkFont(size=10),
                                               fg_color="red", hover_color="#C0392B",
                                               command=lambda cid=client.get("id"): self.confirm_delete_client(cid))
                    delete_btn.pack(side=ctk.LEFT, padx=1)
                    return actions_frame
                
                row_data_list.append(data + [create_actions_widget])
            
            # Ajouter les lignes de manière asynchrone
            self.clients_table.add_rows_async(row_data_list)
            
        else:
            self.clients_table.frame.pack_forget()
            self.no_clients_label.pack(pady=20)
        
        # Mesurer le temps de rendu
        render_time = time.time() - start_render_time
        self.performance_metrics['render_time'] = render_time
        
        logger.debug(f"Rendu de {len(clients)} clients en {render_time:.3f}s")
    
    def _show_error_message(self, error_message):
        """
        Affiche un message d'erreur
        
        Args:
            error_message: Message d'erreur
        """
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
                search_text in client.get("email", "").lower()):
                filtered_clients.append(client)
        
        # Mesurer le temps de filtrage
        filter_time = time.time() - start_time
        self.performance_metrics['filter_time'] = filter_time
        
        logger.debug(f"Filtrage de {len(self.clients_cache)} clients en {filter_time:.3f}s")
        
        # Mettre à jour l'interface
        self._update_ui_with_clients(filtered_clients)
    
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
        # Créer une nouvelle fenêtre modale
        dialog = ctk.CTkToplevel(parent or self.parent)
        dialog.title("Modifier le client" if client_data else "Nouveau client")
        dialog.geometry("500x600")
        dialog.resizable(False, False)
        dialog.transient(parent or self.parent)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Frame principal avec padding
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre avec emoji
        title_label = ctk.CTkLabel(
            main_frame,
            text="👤 " + ("Modifier le client" if client_data else "Nouveau client"),
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Frame pour le formulaire
        form_frame = ctk.CTkFrame(main_frame)
        form_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
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
            "notes": ctk.StringVar(value=client_data.get("notes", "") if client_data else "")
        }
        
        # Fonction pour créer un champ de formulaire
        def create_form_field(parent, row, label_text, variable, required=False, placeholder=""):
            # Label
            label = ctk.CTkLabel(
                parent,
                text=f"{label_text}{'*' if required else ''}:",
                anchor="w"
            )
            label.grid(row=row, column=0, sticky="w", padx=10, pady=(10, 0))
            
            # Entry
            entry = ctk.CTkEntry(
                parent,
                textvariable=variable,
                placeholder_text=placeholder,
                width=300
            )
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=(10, 0))
            return entry
        
        # Créer les champs du formulaire
        fields = [
            ("Nom", "name", True),
            ("Prénom", "first_name", False),
            ("Entreprise", "company", False),
            ("Email", "email", True),
            ("Téléphone", "phone", False),
            ("Adresse", "address", False),
            ("Code postal", "postal_code", False),
            ("Ville", "city", False),
            ("Notes", "notes", False)
        ]
        
        # Configurer la grille du formulaire
        form_frame.columnconfigure(1, weight=1)
        
        # Ajouter les champs
        self.form_entries = {}
        for i, (label, field, required) in enumerate(fields):
            entry = create_form_field(
                form_frame,
                i,
                label,
                self.client_data[field],
                required,
                f"Entrez {label.lower()}"
            )
            self.form_entries[field] = entry
        
        # Frame pour les boutons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, pady=(20, 0))
        
        # Fonction de validation et sauvegarde
        def save_client():
            # Valider uniquement le nom
            if not self.client_data["name"].get().strip():
                self.show_error(dialog, "Le nom est requis.")
                self.form_entries["name"].focus()
                return
            
            # Préparer les données
            client = {
                field: var.get().strip()
                for field, var in self.client_data.items()
            }
            
            try:
                # Sauvegarder en arrière-plan
                def save_task():
                    try:
                        if client_data:
                            # Mise à jour
                            if self.model.update_client(client_data["id"], client):
                                dialog.destroy()
                                self.update_view()
                            else:
                                self.show_error(dialog, "Erreur lors de la mise à jour du client.")
                        else:
                            # Création
                            if self.model.add_client(client):
                                dialog.destroy()
                                self.update_view()
                            else:
                                self.show_error(dialog, "Erreur lors de la création du client.")
                    except Exception as e:
                        logger.error(f"Erreur lors de la sauvegarde du client: {e}")
                        self.show_error(dialog, f"Erreur: {str(e)}")
                
                # Lancer la sauvegarde en arrière-plan
                threading.Thread(target=save_task, daemon=True).start()
                
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde du client: {e}")
                self.show_error(dialog, f"Erreur: {str(e)}")
        
        # Boutons
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Annuler",
            width=100,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=dialog.destroy
        )
        cancel_button.pack(side=ctk.LEFT, padx=10)
        
        save_button = ctk.CTkButton(
            button_frame,
            text="Enregistrer",
            width=100,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=save_client
        )
        save_button.pack(side=ctk.RIGHT, padx=10)
        
        # Focus sur le premier champ
        self.form_entries["name"].focus()
    
    def edit_client(self, client_id):
        """
        Édite un client existant
        
        Args:
            client_id: ID du client à modifier
        """
        self._show_client_form(self.model.get_client(client_id))
    
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
        dialog.geometry("400x200")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        msg_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        msg_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(msg_frame, text="⚠️ Confirmer la suppression", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))
        ctk.CTkLabel(msg_frame, text=f"Êtes-vous sûr de vouloir supprimer le client {client.get('name')} ?", wraplength=360).pack(pady=10)
        
        btn_frame = ctk.CTkFrame(msg_frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        # Indicateur de chargement (initialement masqué)
        delete_indicator = ctk.CTkLabel(
            msg_frame,
            text="Suppression en cours...",
            text_color="#3498db",
            font=ctk.CTkFont(size=12)
        )
        
        def delete_confirmed():
            # Afficher l'indicateur de chargement
            delete_indicator.pack(pady=5)
            
            # Désactiver les boutons pendant la suppression
            cancel_btn.configure(state="disabled")
            delete_btn.configure(state="disabled")
            
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
                    dialog.after(0, lambda: delete_btn.configure(state="normal"))
            
            def finalize_delete(success):
                if success:
                    dialog.destroy()
                    self.update_view()
                    
                    # Afficher un toast de succès
                    self.show_success_toast("Client supprimé avec succès")
                else:
                    delete_indicator.pack_forget()
                    cancel_btn.configure(state="normal")
                    delete_btn.configure(state="normal")
                    self.show_error(dialog, "Erreur lors de la suppression du client.")
            
            threading.Thread(target=delete_client_thread, daemon=True).start()
        
        cancel_btn = ctk.CTkButton(btn_frame, text="Annuler", width=100, command=dialog.destroy)
        cancel_btn.pack(side=ctk.LEFT, padx=10)
        
        delete_btn = ctk.CTkButton(btn_frame, text="Supprimer", width=100, fg_color="red", hover_color="#C0392B", command=delete_confirmed)
        delete_btn.pack(side=ctk.LEFT, padx=10)
    
    def import_clients(self):
        """Importe des clients depuis un fichier CSV"""
        from tkinter import filedialog
        
        # Demander le fichier à importer
        file_path = filedialog.askopenfilename(
            title="Importer des clients",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Créer une fenêtre de prévisualisation
            preview_dialog = ctk.CTkToplevel(self.parent)
            preview_dialog.title("Aperçu de l'importation")
            preview_dialog.geometry("800x600")
            preview_dialog.resizable(False, False)
            preview_dialog.transient(self.parent)
            preview_dialog.grab_set()
            
            # Centrer la fenêtre
            preview_dialog.update_idletasks()
            x = (preview_dialog.winfo_screenwidth() - preview_dialog.winfo_width()) // 2
            y = (preview_dialog.winfo_screenheight() - preview_dialog.winfo_height()) // 2
            preview_dialog.geometry(f"+{x}+{y}")
            
            # Frame principal
            main_frame = ctk.CTkFrame(preview_dialog)
            main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            
            # Titre
            title_label = ctk.CTkLabel(
                main_frame,
                text="📥 Aperçu de l'importation",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            title_label.pack(pady=(0, 20))
            
            # Lire le fichier CSV avec pandas
            df = pd.read_csv(file_path)
            
            # Frame pour les options d'importation
            options_frame = ctk.CTkFrame(main_frame)
            options_frame.pack(fill=ctk.X, pady=(0, 20))
            
            # Options d'importation
            skip_duplicates_var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(
                options_frame,
                text="Ignorer les doublons (basé sur l'email)",
                variable=skip_duplicates_var
            ).pack(side=ctk.LEFT, padx=10, pady=10)
            
            update_existing_var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                options_frame,
                text="Mettre à jour les clients existants",
                variable=update_existing_var
            ).pack(side=ctk.LEFT, padx=10, pady=10)
            
            # Frame pour l'aperçu
            preview_frame = ctk.CTkFrame(main_frame)
            preview_frame.pack(fill=ctk.BOTH, expand=True)
            
            # Afficher l'aperçu des données
            preview_text = ctk.CTkTextbox(preview_frame, wrap="none")
            preview_text.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
            
            # Formater l'aperçu
            headers = df.columns.tolist()
            preview_data = df.head(5).values.tolist()
            
            preview_text.insert("end", "Aperçu des 5 premières lignes:\n\n")
            preview_text.insert("end", "| " + " | ".join(headers) + " |\n")
            preview_text.insert("end", "|" + "|".join(["-"*20]*len(headers)) + "|\n")
            
            for row in preview_data:
                preview_text.insert("end", "| " + " | ".join(str(cell) for cell in row) + " |\n")
            
            preview_text.configure(state="disabled")
            
            # Frame pour les statistiques
            stats_frame = ctk.CTkFrame(main_frame)
            stats_frame.pack(fill=ctk.X, pady=(20, 0))
            
            total_rows = len(df)
            stats_label = ctk.CTkLabel(
                stats_frame,
                text=f"Total de lignes à importer : {total_rows}",
                font=ctk.CTkFont(weight="bold")
            )
            stats_label.pack(pady=10)
            
            # Frame pour les boutons
            button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            button_frame.pack(fill=ctk.X, pady=(20, 0))
            
            def import_data():
                try:
                    # Récupérer les clients existants (pour la vérification des doublons)
                    existing_clients = self.model.get_all_clients()
                    existing_emails = {client["email"] for client in existing_clients if "email" in client}
                    
                    imported = 0
                    updated = 0
                    skipped = 0
                    errors = 0
                    
                    # Convertir le DataFrame en liste de dictionnaires
                    clients_to_import = df.to_dict('records')
                    
                    for client in clients_to_import:
                        try:
                            # Nettoyer les données
                            client = {k: str(v).strip() for k, v in client.items() if pd.notna(v)}
                            
                            # Vérifier si le client existe déjà
                            email = client.get("email", "").lower()
                            if email in existing_emails:
                                if update_existing_var.get():
                                    # Mettre à jour le client existant
                                    existing_client = next(c for c in existing_clients if c["email"].lower() == email)
                                    if self.model.update_client(existing_client["id"], client):
                                        updated += 1
                                    else:
                                        errors += 1
                                elif skip_duplicates_var.get():
                                    skipped += 1
                                continue
                            
                            # Ajouter le nouveau client
                            if self.model.add_client(client):
                                imported += 1
                            else:
                                errors += 1
                                
                        except Exception as e:
                            logger.error(f"Erreur lors de l'importation d'un client: {e}")
                            errors += 1
                    
                    # Fermer la fenêtre de prévisualisation
                    preview_dialog.destroy()
                    
                    # Mettre à jour la vue
                    self.update_view()
                    
                    # Afficher le résumé
                    message = f"Importation terminée :\n\n"
                    message += f"✅ {imported} clients importés\n"
                    if updated > 0:
                        message += f"🔄 {updated} clients mis à jour\n"
                    if skipped > 0:
                        message += f"⏭️ {skipped} clients ignorés (doublons)\n"
                    if errors > 0:
                        message += f"❌ {errors} erreurs\n"
                    
                    self.show_success(message)
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'importation: {e}")
                    self.show_error(preview_dialog, f"Erreur lors de l'importation: {str(e)}")
            
            # Boutons
            cancel_button = ctk.CTkButton(
                button_frame,
                text="Annuler",
                width=100,
                fg_color="#e74c3c",
                hover_color="#c0392b",
                command=preview_dialog.destroy
            )
            cancel_button.pack(side=ctk.LEFT, padx=10)
            
            import_button = ctk.CTkButton(
                button_frame,
                text="Importer",
                width=100,
                fg_color="#2ecc71",
                hover_color="#27ae60",
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
        logger.info("Action: Exporter des clients (non implémentée)")
    
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
            dialog.geometry("300x150")
            dialog.transient(parent)
            dialog.grab_set()
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (parent.winfo_rootx() + parent.winfo_width() // 2) - (width // 2)
            y = (parent.winfo_rooty() + parent.winfo_height() // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            msg_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            msg_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            ctk.CTkLabel(msg_frame, text="❌ Erreur", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))
            ctk.CTkLabel(msg_frame, text=message, wraplength=260).pack(pady=10)
            ctk.CTkButton(msg_frame, text="OK", width=100, command=dialog.destroy).pack(pady=10)
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de la boîte de dialogue d'erreur: {e}")
            messagebox.showerror("Erreur", message, parent=parent)
    
    def show_success(self, message):
        """
        Affiche une boîte de dialogue de succès
        
        Args:
            message: Message de succès
        """
        try:
            dialog = ctk.CTkToplevel(self.parent)
            dialog.title("Succès")
            dialog.geometry("400x200")
            dialog.transient(self.parent)
            dialog.grab_set()
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() - width) // 2
            y = (dialog.winfo_screenheight() - height) // 2
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            frame = ctk.CTkFrame(dialog)
            frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            ctk.CTkLabel(frame, text="✅ Succès", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))
            ctk.CTkLabel(frame, text=message, wraplength=360).pack(pady=10)
            ctk.CTkButton(frame, text="OK", width=100, fg_color="#2ecc71", hover_color="#27ae60", command=dialog.destroy).pack(pady=10)
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de la boîte de dialogue de succès: {e}")
            messagebox.showinfo("Succès", message, parent=self.parent)
    
    def show_success_toast(self, message):
        """
        Affiche une notification toast de succès
        
        Args:
            message: Message à afficher
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
            text=message,
            font=ctk.CTkFont(size=12)
        )
        message_label.pack(side="left", padx=(0, 10), pady=10)
        
        # Positionner le toast en bas de l'écran
        toast.place(relx=0.5, rely=0.95, anchor="center")
        
        # Faire disparaître le toast après quelques secondes
        def hide_toast():
            toast.destroy()
        
        self.parent.after(3000, hide_toast)


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

