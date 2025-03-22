#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue formulaire pour les documents
Adapté pour correspondre au style du formulaire de modèle (TemplateFormView)
"""

import os
import logging
import customtkinter as ctk
from datetime import datetime
from utils.dialog_utils import DialogUtils

logger = logging.getLogger("VynalDocsAutomator.DocumentFormView")

class DocumentFormView:
    """Vue formulaire pour les documents"""
    
    def __init__(self, parent, model, document_data=None, folder_id=None, import_mode=False, on_save_callback=None, on_cancel_callback=None):
        """Initialise le formulaire de document"""
        self.parent = parent
        self.model = model
        self.document_data = document_data or {}
        # Le dossier Import est utilisé uniquement si on crée un modèle depuis un document importé
        self.folder_id = folder_id if folder_id else ("import" if import_mode and document_data.get("from_analysis") else None)
        self.import_mode = import_mode
        self.on_save_callback = on_save_callback
        self.on_cancel_callback = on_cancel_callback
        
        # Créer la boîte de dialogue mais la cacher jusqu'à ce qu'elle soit prête
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.withdraw()  # Cache la fenêtre pendant le chargement
        self.dialog.title("Nouveau document" if not import_mode else "Importer un document")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        
        # Configurer le gestionnaire d'événement pour la fermeture de la fenêtre
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Initialiser les variables de formulaire
        self.title_var = ctk.StringVar(value=document_data.get("title", ""))
        self.type_var = ctk.StringVar(value=document_data.get("type", ""))
        self.template_var = ctk.StringVar()
        self.client_var = ctk.StringVar()
        
        # Variables supplémentaires
        self.variable_entries = {}
        self.template_data = None
        
        # Créer le contenu du formulaire
        self._create_form()
        
        # Si un template_id est fourni dans les données initiales, sélectionner le modèle
        if document_data.get("template_id"):
            template_id = document_data.get("template_id")
            template = next((t for t in self.model.templates if t.get("id") == template_id), None)
            if template:
                self.template_data = template
                template_name = f"{template.get('name')} ({template.get('type', '')})"
                self.template_var.set(template_name)
                self._update_template_info()
        
        # Après avoir créé tout le contenu, centrer et afficher la fenêtre
        self.dialog.update_idletasks()  # Force le calcul des dimensions
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width - self.dialog.winfo_width()) // 2
        y = (screen_height - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Maintenant que tout est prêt, afficher la fenêtre et capturer le focus
        self.dialog.deiconify()  # Rend la fenêtre visible
        self.dialog.grab_set()  # Capture le focus
        self.dialog.focus_force()  # Force le focus sur cette fenêtre
        
        logger.info("Formulaire de document initialisé")
    
    def _create_form(self):
        """Crée le contenu du formulaire dans un style identique à TemplateFormView"""
        # Structure globale: un main_frame pour tout le contenu
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Zone de défilement pour le formulaire
        form_frame = ctk.CTkScrollableFrame(main_frame)
        form_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Titre du formulaire avec icône
        title_label = ctk.CTkLabel(
            form_frame,
            text="📄 " + ("Importer un document" if self.import_mode else "Nouveau document"),
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Type de document
        type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        type_frame.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(type_frame, text="Type*:", width=100).pack(side=ctk.LEFT)
        
        # Obtenir les types de documents disponibles
        types = set()  # Utiliser un set pour éviter les doublons
        normalized_types = {}  # Dictionnaire pour stocker la forme normalisée -> forme originale
        
        def add_type(type_str):
            """Ajoute un type en évitant les doublons quelle que soit la casse"""
            if not type_str:
                return
            type_str = type_str.strip()
            if not type_str:
                return
            normalized = type_str.lower()
            # On garde la première version rencontrée (priorité aux dossiers de modèles)
            if normalized not in normalized_types:
                normalized_types[normalized] = type_str
        
        try:
            # Ajouter d'abord les types depuis les dossiers de modèles (priorité)
            if hasattr(self.model, 'template_folders'):
                folder_types = self.model.template_folders.values()
                for folder_type in folder_types:
                    add_type(folder_type)
                logger.debug(f"Types ajoutés depuis les dossiers de modèles: {folder_types}")
            
            # Récupérer les types depuis les modèles pour la rétrocompatibilité
            if hasattr(self.model, 'templates'):
                if isinstance(self.model.templates, list):
                    for template in self.model.templates:
                        add_type(template.get('type', ''))
                elif isinstance(self.model.templates, dict):
                    for template_id, template in self.model.templates.items():
                        add_type(template.get('type', ''))
            
            # Récupérer les types des documents existants pour la rétrocompatibilité
            if hasattr(self.model, 'documents'):
                if isinstance(self.model.documents, list):
                    for doc in self.model.documents:
                        add_type(doc.get('type', ''))
                elif isinstance(self.model.documents, dict):
                    for doc_id, doc in self.model.documents.items():
                        add_type(doc.get('type', ''))
            
            # Ajouter les types par défaut en dernier (si pas déjà présents)
            default_types = ["contrat", "facture", "proposition", "rapport", "autre"]
            for default_type in default_types:
                add_type(default_type)
            
            # Obtenir la liste finale des types uniques dans leur forme originale
            types = sorted(normalized_types.values())
            
            logger.debug(f"Types de documents disponibles (uniques) : {types}")
            
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des types: {e}")
            types = ["contrat", "facture", "proposition", "rapport", "autre"]
        
        type_menu = ctk.CTkOptionMenu(type_frame, values=types, variable=self.type_var, width=400,
                                     command=self._update_template_options)
        type_menu.pack(side=ctk.LEFT, padx=10)
        
        # Sélection du modèle
        template_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        template_frame.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(template_frame, text="Modèle*:", width=100).pack(side=ctk.LEFT)
        
        # Préparer les options du modèle
        template_options = ["Sélectionner un modèle"]
        try:
            # Vérifier si le type existe dans les dossiers de modèles
            type_exists = False
            if hasattr(self.model, 'template_folders'):
                for folder_id, folder_name in self.model.template_folders.items():
                    if folder_name.lower() == self.type_var.get().lower():
                        type_exists = True
                        break
            
            # Si le type existe, récupérer les modèles correspondants
            if type_exists:
                if hasattr(self.model, 'templates'):
                    if isinstance(self.model.templates, list):
                        for template in self.model.templates:
                            name = template.get('name', '')
                            if name:
                                # Vérifier si le modèle appartient au dossier du type sélectionné
                                folder_id = str(template.get('folder', ''))
                                if folder_id in self.model.template_folders:
                                    folder_name = self.model.template_folders[folder_id]
                                    if folder_name.lower() == self.type_var.get().lower():
                                        template_options.append(f"{name} ({template.get('type', '')})")
                    elif isinstance(self.model.templates, dict):
                        for template_id, template in self.model.templates.items():
                            name = template.get('name', '')
                            if name:
                                # Vérifier si le modèle appartient au dossier du type sélectionné
                                folder_id = str(template.get('folder', ''))
                                if folder_id in self.model.template_folders:
                                    folder_name = self.model.template_folders[folder_id]
                                    if folder_name.lower() == self.type_var.get().lower():
                                        template_options.append(f"{name} ({template.get('type', '')})")
            
            logger.debug(f"Options de modèles pour le type '{self.type_var.get()}': {template_options}")
            
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des modèles: {e}")
        
        # Créer le combobox pour les modèles
        template_combo = ctk.CTkOptionMenu(
            template_frame, 
            width=400,
            values=template_options,
            command=self._update_template_info
        )
        template_combo.pack(side=ctk.LEFT, padx=10)
        
        # Titre du document
        name_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        name_frame.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(name_frame, text="Titre*:", width=100).pack(side=ctk.LEFT)
        title_entry = ctk.CTkEntry(name_frame, textvariable=self.title_var, width=400)
        title_entry.pack(side=ctk.LEFT, padx=10)
        
        # Ajouter le message d'aide en italique
        help_label = ctk.CTkLabel(
            form_frame,
            text="⚠️ Veuillez sélectionner à nouveau un client si vous changez de modèle",
            text_color="gray60",  # Couleur plus claire pour indiquer que c'est un message d'aide
            font=ctk.CTkFont(size=12, slant="italic")  # Police en italique et plus petite
        )
        help_label.pack(pady=(0, 10))  # Petit espacement en bas
        
        # Cadre pour les informations du modèle
        self.template_info_frame = ctk.CTkFrame(form_frame)
        self.template_info_frame.pack(fill=ctk.X, pady=10, padx=10)
        
        
        # Étiquette pour les informations du modèle
        self.template_info_label = ctk.CTkLabel(
            self.template_info_frame,
            text="Sélectionnez un modèle pour voir les détails",
            wraplength=550
        )
        self.template_info_label.pack(pady=10)
        
        # Sélection du client
        client_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        client_frame.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(client_frame, text="Client*:", width=100).pack(side=ctk.LEFT)

        # Créer un sous-frame pour la recherche et le combo
        client_input_frame = ctk.CTkFrame(client_frame, fg_color="transparent")
        client_input_frame.pack(side=ctk.LEFT, fill=ctk.X, expand=True)

        # Champ de recherche
        self.client_search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            client_input_frame,
            placeholder_text="Rechercher un client...",
            textvariable=self.client_search_var,
            width=370  # Légèrement réduit pour faire place au bouton X
        )
        search_entry.pack(side=ctk.LEFT, padx=(10, 2), pady=(0, 5))

        # Bouton X pour effacer la recherche
        clear_button = ctk.CTkButton(
            client_input_frame,
            text="✕",
            width=25,
            height=25,
            fg_color="transparent",
            hover_color="#E0E0E0",
            command=lambda: [self.client_search_var.set(""), search_entry.focus_set()]
        )
        clear_button.pack(side=ctk.LEFT, padx=(0, 10), pady=(0, 5))

        # Préparer les options des clients
        self.all_clients = []  # Pour stocker tous les clients
        client_options = ["Sélectionner un client"]
        recent_clients = []  # Pour stocker les 5 clients les plus récents
        
        try:
            # Gérer les cas où clients est une liste ou un dictionnaire
            if hasattr(self.model, 'clients'):
                clients_list = []
                
                if isinstance(self.model.clients, list):
                    clients_list = self.model.clients
                elif isinstance(self.model.clients, dict):
                    clients_list = [
                        {**client, 'id': cid} 
                        for cid, client in self.model.clients.items()
                    ]
                
                # Trier par date de création si disponible
                sorted_clients = sorted(
                    clients_list,
                    key=lambda c: c.get('created_at', ''),
                    reverse=True
                )
                
                # Collecter tous les clients et les 5 plus récents
                for client in sorted_clients:
                    name = client.get('name', '')
                    if name:
                        display_name = name
                        if client.get('company'):
                            display_name += f" ({client.get('company')})"
                        
                        # Stocker pour la recherche
                        self.all_clients.append({
                            'id': client.get('id'),
                            'display': display_name,
                            'name': name.lower(),
                            'company': client.get('company', '').lower(),
                            'email': client.get('email', '').lower(),
                            'phone': client.get('phone', '').lower()
                        })
                        
                        # Ajouter aux clients récents si dans les 5 premiers
                        if len(recent_clients) < 5:
                            recent_clients.append(display_name)
                
                # Ajouter les clients récents en premier
                client_options.extend(recent_clients)
                
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des clients: {e}")

        # Créer le combobox pour les clients
        client_combo = ctk.CTkOptionMenu(
            client_input_frame, 
            width=400,
            values=client_options,
            command=self._update_client_info
        )
        client_combo.pack(fill=ctk.X, padx=10)

        # Configurer la recherche
        def filter_clients(*args):
            search_text = self.client_search_var.get().lower()
            if not search_text:
                # Afficher les clients récents
                options = ["Sélectionner un client"]
                options.extend(recent_clients)
            else:
                # Filtrer les clients selon le texte de recherche
                filtered = [
                    c['display'] for c in self.all_clients
                    if search_text in c['name'] or
                       search_text in c['company'] or
                       search_text in c['email'] or
                       search_text in c['phone']
                ]
                options = ["Sélectionner un client"]
                options.extend(filtered)
            
            current_value = client_combo.get()
            client_combo.configure(values=options)
            # Restaurer la valeur si elle existe toujours dans les options
            if current_value in options:
                client_combo.set(current_value)

        # Lier la recherche au champ de texte
        self.client_search_var.trace("w", filter_clients)
        
        # Ouvrir le menu déroulant quand on clique dans le champ de recherche
        search_entry.bind("<FocusIn>", lambda e: filter_clients())
        
        # Ajouter la détection de fermeture du menu déroulant
        client_combo.bind("<FocusOut>", lambda e: setattr(self, '_dropdown_showing', False) if hasattr(self, '_dropdown_showing') else None)
        
        # Cadre pour les informations du client
        self.client_info_frame = ctk.CTkFrame(form_frame)
        self.client_info_frame.pack(fill=ctk.X, pady=10, padx=10)

        # Étiquette pour les informations du client
        self.client_info_label = ctk.CTkLabel(
            self.client_info_frame,
            text="Sélectionnez un client pour voir les détails",
            wraplength=550
        )
        self.client_info_label.pack(pady=10)
        
        # Zone pour les variables spécifiques du modèle
        self.variables_frame = ctk.CTkFrame(form_frame)
        self.variables_frame.pack(fill=ctk.X, pady=10)
        
        # Frame pour les boutons
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, pady=(20, 0))
        
        # Bouton Annuler
        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text="Annuler",
            width=100,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self._on_cancel
        )
        self.cancel_btn.pack(side=ctk.RIGHT, padx=10)
        
        # Bouton Enregistrer
        self.save_btn = ctk.CTkButton(
            button_frame,
            text="Enregistrer",
            width=100,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=self._save_document
        )
        self.save_btn.pack(side=ctk.RIGHT, padx=10)
        
        # Focus sur le champ titre
        title_entry.focus()
        
        # Stocker les références aux widgets importants
        self.template_combo = template_combo
        self.client_combo = client_combo
        
        logger.debug("Formulaire créé avec succès")
    
    def _update_template_info(self, value=None):
        """Met à jour les informations du modèle sélectionné"""
        selected_name = value if value else self.template_combo.get()
        selected_type = self.type_var.get().strip()
        
        if selected_name == "Sélectionner un modèle":
            self.template_info_label.configure(text="Sélectionnez un modèle pour voir les détails")
            for widget in self.variables_frame.winfo_children():
                widget.destroy()
            self.variables_frame.pack_forget()  # Cacher le cadre des variables
            return
            
        # Trouver le modèle correspondant
        template = None
        if hasattr(self.model, 'templates'):
            templates_to_check = []
            
            if isinstance(self.model.templates, list):
                templates_to_check = self.model.templates
            elif isinstance(self.model.templates, dict):
                templates_to_check = list(self.model.templates.values())
            
            for t in templates_to_check:
                if t.get('name') and selected_name.startswith(t.get('name')):
                    # Vérifier d'abord le dossier si disponible
                    if hasattr(self.model, 'template_folders'):
                        folder_id = str(t.get('folder', ''))
                        for fid, fname in self.model.template_folders.items():
                            if str(fid) == folder_id and fname.lower() == selected_type.lower():
                                template = t
                                break
                    
                    # Si pas de correspondance par dossier, vérifier le type (rétrocompatibilité)
                    if not template and t.get('type', '').lower() == selected_type.lower():
                        template = t
                        break
        
        if not template:
            self.template_info_label.configure(text="Modèle non trouvé")
            self.variables_frame.pack_forget()  # Cacher le cadre des variables
            return
            
        # Stocker les données du modèle
        self.template_data = template
        
        # Afficher uniquement le type et la description du modèle
        template_type = template.get('type', 'Non spécifié')
        template_desc = template.get('description', 'Aucune description')
        info_text = f"Type: {template_type}\nDescription: {template_desc}"
        self.template_info_label.configure(text=info_text)
        
        # Mettre à jour le type si nécessaire
        if not self.type_var.get() and template_type:
            self.type_var.set(template_type)
        
        # Auto-remplir le titre si le champ est vide
        current_title = self.title_var.get().strip()
        if not current_title:
            # Générer un titre automatique basé sur le type et le nom du modèle
            selected_type = self.type_var.get()
            template_name = template.get('name', '')
            
            # Récupérer la date actuelle au format JJ/MM/AAAA
            from datetime import datetime
            current_date = datetime.now().strftime("%d/%m/%Y")
            
            # Générer un titre avec format: [Type] - [Nom du modèle] - [Date]
            auto_title = f"{selected_type.capitalize()} - {template_name} - {current_date}"
            
            # Mettre à jour le champ titre
            self.title_var.set(auto_title)
            logger.info(f"Titre auto-généré: {auto_title}")
        
        # Afficher les variables du modèle
        self._show_template_variables()
        
        # S'assurer que le modèle est sélectionné dans le combobox
        if hasattr(self, 'template_combo'):
            template_name = f"{template.get('name')} ({template.get('type', '')})"
            self.template_combo.set(template_name)
    
    def _update_template_options(self, value=None):
        """Met à jour la liste des modèles en fonction du type sélectionné"""
        selected_type = self.type_var.get().strip()
        
        # Préparer les options du modèle
        template_options = ["Sélectionner un modèle"]
        try:
            # Vérifier si le type existe dans les dossiers de modèles
            type_exists = False
            if hasattr(self.model, 'template_folders'):
                for folder_id, folder_name in self.model.template_folders.items():
                    if folder_name.lower() == selected_type.lower():
                        type_exists = True
                        break
            
            # Si le type existe, récupérer les modèles correspondants
            if type_exists:
                if hasattr(self.model, 'templates'):
                    if isinstance(self.model.templates, list):
                        for template in self.model.templates:
                            name = template.get('name', '')
                            if name:
                                # Vérifier si le modèle appartient au dossier du type sélectionné
                                folder_id = str(template.get('folder', ''))
                                if folder_id in self.model.template_folders:
                                    folder_name = self.model.template_folders[folder_id]
                                    if folder_name.lower() == selected_type.lower():
                                        template_options.append(f"{name} ({template.get('type', '')})")
                    elif isinstance(self.model.templates, dict):
                        for template_id, template in self.model.templates.items():
                            name = template.get('name', '')
                            if name:
                                # Vérifier si le modèle appartient au dossier du type sélectionné
                                folder_id = str(template.get('folder', ''))
                                if folder_id in self.model.template_folders:
                                    folder_name = self.model.template_folders[folder_id]
                                    if folder_name.lower() == selected_type.lower():
                                        template_options.append(f"{name} ({template.get('type', '')})")
            
            logger.debug(f"Options de modèles pour le type '{selected_type}': {template_options}")
            
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des modèles: {e}")
        
        # Mettre à jour le combobox avec les nouvelles options
        if hasattr(self, 'template_combo'):
            self.template_combo.configure(values=template_options)
            self.template_combo.set("Sélectionner un modèle")
            self.template_info_label.configure(text="Sélectionnez un modèle pour voir les détails")
            self.variables_frame.pack_forget()  # Cacher le cadre des variables
    
    def _update_client_info(self, selection=None):
        """Met à jour les informations du client sélectionné"""
        selected_name = selection if selection else self.client_combo.get()
        
        if selected_name == "Sélectionner un client":
            self.client_info_label.configure(text="Sélectionnez un client pour voir les détails")
            return
        
        # Trouver le client correspondant
        client = None
        if hasattr(self.model, 'clients'):
            if isinstance(self.model.clients, list):
                for c in self.model.clients:
                    if c.get('name') and selected_name.startswith(c.get('name')):
                        client = c
                        break
            elif isinstance(self.model.clients, dict):
                for c_id, c in self.model.clients.items():
                    if c.get('name') and selected_name.startswith(c.get('name')):
                        client = c
                        break
        
        if not client:
            self.client_info_label.configure(text="Client non trouvé")
            return
        
        # Afficher les informations du client
        client_name = client.get('name', 'Non spécifié')
        client_company = client.get('company', 'Non spécifié')
        client_email = client.get('email', 'Non spécifié')
        client_phone = client.get('phone', 'Non spécifié')
        client_address = client.get('address', 'Non spécifié')
        
        info_text = f"Nom: {client_name}\nEntreprise: {client_company}\nEmail: {client_email}\nTéléphone: {client_phone}"
        if client_address != 'Non spécifié':
            info_text += f"\nAdresse: {client_address}"
        self.client_info_label.configure(text=info_text)
        
        # Pré-remplir les variables du client si elles existent dans notre formulaire
        if hasattr(self, 'variable_entries') and self.variable_entries:
            # Mapping des variables client vers les champs du formulaire
            client_vars = {
                'client_name': client_name,
                'client_company': client_company,
                'client_email': client_email,
                'client_phone': client_phone,
                'client_address': client_address,
                'nom_client': client_name,
                'entreprise_client': client_company,
                'email_client': client_email,
                'telephone_client': client_phone,
                'adresse_client': client_address
            }
            
            # Remplir les variables correspondantes
            for var_name, var_var in self.variable_entries.items():
                if var_name in client_vars and client_vars[var_name] != 'Non spécifié':
                    var_var.set(client_vars[var_name])
    
    def _show_template_variables(self):
        """Affiche les champs pour les variables présentes dans le contenu du document"""
        # Nettoyer les widgets existants
        for widget in self.variables_frame.winfo_children():
            widget.destroy()
        
        # Vérifier si nous avons des données de modèle avec un contenu
        if not self.template_data or 'content' not in self.template_data:
            self.variables_frame.pack_forget()
            return
        
        # Extraire les variables directement du contenu du document
        import re
        content = self.template_data.get('content', '')
        
        # Chercher toutes les variables au format {{variable}} et {variable}
        double_brace_vars = re.findall(r'{{([^{}]+?)}}', content)
        single_brace_vars = re.findall(r'{([^{}]+?)}', content)
        
        # Fusionner les deux listes
        all_vars = double_brace_vars + single_brace_vars
        
        # Filtrer les variables standard qui seront remplies automatiquement
        standard_vars = [
            'client_name', 'client_company', 'client_email', 'client_phone', 'client_address',
            'company_name', 'company_address', 'company_email', 'company_phone', 'company_website',
            'date', 'time', 'document_title'
        ]
        
        # Filtrer pour ne garder que les variables personnalisées
        custom_variables = [var for var in all_vars if var not in standard_vars]
        
        # Retirer les doublons tout en préservant l'ordre de première apparition
        seen = set()
        unique_custom_vars = []
        for var in custom_variables:
            if var not in seen:
                seen.add(var)
                unique_custom_vars.append(var)
        
        if not unique_custom_vars:
            self.variables_frame.pack_forget()
            return
        
        # Afficher le cadre des variables
        self.variables_frame.pack(fill=ctk.X, pady=10, padx=10)
        
        # Titre de la section
        ctk.CTkLabel(
            self.variables_frame,
            text="Variables à remplir",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        # Créer un champ pour chaque variable unique
        for var_name in unique_custom_vars:
            var_frame = ctk.CTkFrame(self.variables_frame, fg_color="transparent")
            var_frame.pack(fill=ctk.X, pady=5)
            
            # Format exact comme dans l'image
            ctk.CTkLabel(var_frame, text=f'"{var_name}":', width=150).pack(side=ctk.LEFT)
            
            # Champ de saisie
            var_var = ctk.StringVar()
            var_entry = ctk.CTkEntry(var_frame, textvariable=var_var, width=400)
            var_entry.pack(side=ctk.LEFT, padx=10)
            
            # Stocker la référence
            self.variable_entries[var_name] = var_var
    
    def get_selected_client(self):
        """Récupère le client sélectionné - Version améliorée avec support de la recherche"""
        selected_name = self.client_combo.get()
        
        # Journalisation pour le débogage
        logger.debug(f"Tentative de récupération du client: '{selected_name}'")
        
        if selected_name == "Sélectionner un client":
            logger.warning("Aucun client sélectionné")
            return None
        
        # D'abord, essayer de trouver le client dans la nouvelle structure
        if hasattr(self, 'all_clients') and self.all_clients:
            for client in self.all_clients:
                if client['display'] == selected_name:
                    logger.info(f"Client trouvé dans la nouvelle structure: {client['name']}, ID: {client['id']}")
                    return client['id']
        
        # Si non trouvé ou si ancienne structure, utiliser la méthode originale
        if hasattr(self.model, 'clients'):
            if isinstance(self.model.clients, list):
                for client in self.model.clients:
                    client_name = client.get('name', '')
                    if client.get('company'):
                        full_name = f"{client_name} ({client.get('company')})"
                    else:
                        full_name = client_name
                    
                    if client_name and selected_name.startswith(client_name):
                        logger.info(f"Client trouvé par nom: {client_name}, ID: {client.get('id')}")
                        return client.get('id')
                    
                    if full_name and selected_name.startswith(full_name):
                        logger.info(f"Client trouvé par nom complet: {full_name}, ID: {client.get('id')}")
                        return client.get('id')
                    
            elif isinstance(self.model.clients, dict):
                for client_id, client in self.model.clients.items():
                    client_name = client.get('name', '')
                    if client.get('company'):
                        full_name = f"{client_name} ({client.get('company')})"
                    else:
                        full_name = client_name
                    
                    if client_name and selected_name.startswith(client_name):
                        logger.info(f"Client trouvé par nom: {client_name}, ID: {client_id}")
                        return client_id
                    
                    if full_name and selected_name.startswith(full_name):
                        logger.info(f"Client trouvé par nom complet: {full_name}, ID: {client_id}")
                        return client_id
        
        # Méthode alternative: extraction de l'ID du client à partir du texte
        try:
            import re
            match = re.search(r'\(ID: ([^)]+)\)', selected_name)
            if match:
                client_id = match.group(1)
                logger.info(f"ID client extrait du texte: {client_id}")
                return client_id
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction alternative de l'ID: {e}")
        
        logger.warning(f"Client non trouvé pour: {selected_name}")
        return None
    
    def get_selected_template(self):
        """Récupère le modèle sélectionné"""
        selected_name = self.template_combo.get()
        if selected_name == "Sélectionner un modèle":
            return None
        
        # Trouver le modèle
        if hasattr(self.model, 'templates'):
            if isinstance(self.model.templates, list):
                for template in self.model.templates:
                    if template.get('name') and selected_name.startswith(template.get('name')):
                        return template.get('id')
            elif isinstance(self.model.templates, dict):
                for template_id, template in self.model.templates.items():
                    if template.get('name') and selected_name.startswith(template.get('name')):
                        return template_id
        
        return None
    
    def _save_document(self):
        """Sauvegarde les données du document"""
        try:
            # Vérifications de base
            title = self.title_var.get().strip()
            if not title:
                DialogUtils.show_message(self.dialog, "Erreur", "Le titre est obligatoire", "error")
                return
            
            # Vérifier que le client est sélectionné
            client_id = self.get_selected_client()
            if not client_id:
                DialogUtils.show_message(self.dialog, "Erreur", "Veuillez sélectionner un client", "error")
                return
            
            # Récupérer les valeurs du formulaire
            document_type = self.type_var.get()
            template_id = self.get_selected_template()
            
            # Vérifier le modèle
            if not template_id and not self.import_mode:
                DialogUtils.show_message(self.dialog, "Erreur", "Veuillez sélectionner un modèle", "error")
                return
            
            # Récupérer les valeurs des variables
            variables = {}
            for var_name, entry in self.variable_entries.items():
                value = entry.get()
                variables[var_name] = value
            
            # Construire l'objet document
            document = {
                "title": title,
                "type": document_type,
                "client_id": client_id,
                "variables": variables,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "modified_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            # Ajouter le template_id si disponible
            if template_id:
                document["template_id"] = template_id
            
            # En mode import, mettre à jour avec les données existantes
            if self.import_mode and self.document_data:
                # Conserver le chemin du fichier importé
                if "file_path" in self.document_data:
                    document["file_path"] = self.document_data["file_path"]
                    
                # Conserver les autres données spécifiques à l'import
                for key in ["from_analysis", "analysis_results"]:
                    if key in self.document_data:
                        document[key] = self.document_data[key]
            
            # Ajouter le dossier si disponible
            if self.folder_id:
                document["folder"] = self.folder_id
            
            # Ajouter l'ID si c'est une modification
            if "id" in self.document_data:
                document["id"] = self.document_data["id"]
            
            # Appeler la méthode pour sauvegarder le document
            if hasattr(self.model, "save_document"):
                result = self.model.save_document(document)
                
                if result and isinstance(result, dict):
                    # Récupérer l'ID du document créé/modifié
                    document_id = result.get("id") or document.get("id")
                    
                    # Fermer le formulaire
                    self.dialog.destroy()
                    
                    # Afficher un message de succès
                    DialogUtils.show_message(self.parent, "Succès", "Document sauvegardé avec succès", "info")
                    
                    # Créer une fenêtre de finalisation pour offrir différentes options
                    self._show_finalization_options(document_id, client_id)
                    
                    # Si un callback est défini, l'appeler avec les informations du document
                    if callable(self.on_save_callback):
                        client_name = self._get_client_name(client_id)
                        self.on_save_callback(document_id=document_id, client_id=client_id, client_name=client_name)
                else:
                    DialogUtils.show_message(self.dialog, "Erreur", "Erreur lors de la sauvegarde du document", "error")
            else:
                logger.error("La méthode save_document n'existe pas dans le modèle")
                DialogUtils.show_message(self.dialog, "Erreur", "Méthode de sauvegarde non disponible", "error")
        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du document: {e}")
            DialogUtils.show_message(self.dialog, "Erreur", f"Erreur lors de la sauvegarde: {str(e)}", "error")

    def _show_finalization_options(self, document_id, client_id):
        """
        Affiche une fenêtre avec des options pour finaliser le document
        
        Args:
            document_id: ID du document sauvegardé
            client_id: ID du client associé
        """
        try:
            # Récupérer les informations du document
            document = next((d for d in self.model.documents if d.get("id") == document_id), None)
            if not document:
                logger.error(f"Document {document_id} non trouvé pour la finalisation")
                return
            
            # Créer une fenêtre modale
            finalization_window = ctk.CTkToplevel(self.parent)
            finalization_window.title("Document créé avec succès")
            finalization_window.geometry("600x400")
            finalization_window.resizable(True, True)
            finalization_window.grab_set()  # Rendre la fenêtre modale
            
            # Centrer la fenêtre
            finalization_window.update_idletasks()
            screen_width = finalization_window.winfo_screenwidth()
            screen_height = finalization_window.winfo_screenheight()
            x = (screen_width - finalization_window.winfo_width()) // 2
            y = (screen_height - finalization_window.winfo_height()) // 2
            finalization_window.geometry(f"+{x}+{y}")
            
            # Cadre principal
            main_frame = ctk.CTkFrame(finalization_window)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Message de confirmation en vert
            success_frame = ctk.CTkFrame(main_frame, fg_color=("green", "#005000"))
            success_frame.pack(fill="x", padx=20, pady=10)
            
            success_label = ctk.CTkLabel(
                success_frame,
                text="Document créé avec succès !",
                font=("", 16, "bold"),
                text_color="white"
            )
            success_label.pack(pady=10)
            
            # Informations sur le document créé
            info_frame = ctk.CTkFrame(main_frame, fg_color=("gray95", "gray15"))
            info_frame.pack(fill="x", padx=20, pady=10)
            
            # Titre du document
            info_label = ctk.CTkLabel(
                info_frame,
                text=f"Document: {document.get('title', 'Sans titre')}",
                font=("", 14)
            )
            info_label.pack(pady=10, padx=20, anchor="w")
            
            # Client associé
            client_name = self._get_client_name(client_id)
            client_label = ctk.CTkLabel(
                info_frame,
                text=f"Client: {client_name}",
                font=("", 14)
            )
            client_label.pack(pady=5, padx=20, anchor="w")
            
            # Options de finalisation
            options_frame = ctk.CTkFrame(main_frame)
            options_frame.pack(fill="x", padx=20, pady=20)
            
            options_label = ctk.CTkLabel(
                options_frame,
                text="Que souhaitez-vous faire ?",
                font=("", 16, "bold")
            )
            options_label.pack(pady=10)
            
            # Boutons d'action
            buttons_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
            buttons_frame.pack(pady=10)
            
            # Bouton pour prévisualiser le document
            preview_button = ctk.CTkButton(
                buttons_frame,
                text="Prévisualiser le document",
                command=lambda: self._preview_document(document_id, finalization_window),
                width=200
            )
            preview_button.pack(pady=5)
            
            # Bouton pour télécharger le document
            download_button = ctk.CTkButton(
                buttons_frame,
                text="Télécharger le document",
                command=lambda: self._download_document(document_id, finalization_window),
                width=200
            )
            download_button.pack(pady=5)
            
            # Bouton pour envoyer le document par email
            email_button = ctk.CTkButton(
                buttons_frame,
                text="Envoyer par email",
                command=lambda: self._send_email(document_id, finalization_window),
                width=200
            )
            email_button.pack(pady=5)
            
            # Fonction pour rediriger vers le tableau de bord
            def retour_au_dashboard():
                finalization_window.destroy()
                if hasattr(self.parent, 'show_view'):
                    logger.info("Retour au tableau de bord après finalisation")
                    self.parent.show_view('dashboard')
                else:
                    logger.error("Impossible de revenir au tableau de bord: méthode show_view non trouvée")
            
            # Bouton pour fermer et retourner au dashboard
            close_button = ctk.CTkButton(
                buttons_frame,
                text="Terminer",
                command=retour_au_dashboard,
                width=200,
                fg_color=("gray80", "gray30"),
                text_color=("gray10", "gray90")
            )
            close_button.pack(pady=5)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des options de finalisation: {e}")
            # En cas d'erreur, essayer quand même de revenir au tableau de bord
            if hasattr(self.parent, 'show_view'):
                self.parent.show_view('dashboard')

    def _preview_document(self, document_id, parent_window=None):
        """
        Prévisualise un document
        
        Args:
            document_id: ID du document à prévisualiser
            parent_window: Fenêtre parente à fermer (optionnel)
        """
        try:
            # Récupérer le document
            document = next((d for d in self.model.documents if d.get("id") == document_id), None)
            if not document:
                DialogUtils.show_message(self.parent, "Erreur", "Document non trouvé", "error")
                return
            
            # Créer et utiliser le prévisualiseur
            from utils.document_preview import DocumentPreview
            previewer = DocumentPreview(self.parent)
            previewer.preview(document)
            
            # Fermer la fenêtre parent si spécifiée
            if parent_window and parent_window.winfo_exists():
                parent_window.destroy()
            
        except Exception as e:
            logger.error(f"Erreur lors de la prévisualisation du document: {e}")
            DialogUtils.show_message(self.parent, "Erreur", f"Impossible de prévisualiser le document: {str(e)}", "error")

    def _download_document(self, document_id, parent_window=None):
        """
        Télécharge un document
        
        Args:
            document_id: ID du document à télécharger
            parent_window: Fenêtre parente à fermer (optionnel)
        """
        try:
            import tkinter.filedialog as filedialog
            import shutil
            import os
            
            # Récupérer le document
            document = next((d for d in self.model.documents if d.get("id") == document_id), None)
            if not document:
                DialogUtils.show_message(self.parent, "Erreur", "Document non trouvé", "error")
                return
            
            # Vérifier que le document a un chemin de fichier
            file_path = document.get("file_path")
            if not file_path or not os.path.exists(file_path):
                DialogUtils.show_message(self.parent, "Erreur", "Le fichier du document est introuvable", "error")
                return
            
            # Déterminer l'extension du fichier
            _, ext = os.path.splitext(file_path)
            
            # Ouvrir une boîte de dialogue pour choisir l'emplacement de sauvegarde
            dest_path = filedialog.asksaveasfilename(
                title="Enregistrer le document",
                defaultextension=ext,
                initialfile=os.path.basename(file_path),
                filetypes=[(f"Fichiers {ext.upper()}", f"*{ext}"), ("Tous les fichiers", "*.*")]
            )
            
            if not dest_path:
                return
            
            # Copier le fichier
            shutil.copy2(file_path, dest_path)
            
            logger.info(f"Document téléchargé: {dest_path}")
            DialogUtils.show_message(self.parent, "Succès", "Document téléchargé avec succès", "info")
            
            # Fermer la fenêtre parent si spécifiée
            if parent_window and parent_window.winfo_exists():
                parent_window.destroy()
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du document: {e}")
            DialogUtils.show_message(self.parent, "Erreur", f"Erreur lors du téléchargement: {str(e)}", "error")

    def _send_email(self, document_id, parent_window=None):
        """
        Envoie un document par email
        
        Args:
            document_id: ID du document à envoyer
            parent_window: Fenêtre parente à fermer (optionnel)
        """
        try:
            # Récupérer le document
            document = next((d for d in self.model.documents if d.get("id") == document_id), None)
            if not document:
                DialogUtils.show_message(self.parent, "Erreur", "Document non trouvé", "error")
                return
            
            # Implémenter la logique d'envoi par email
            # Pour l'instant, afficher un message d'information
            logger.info(f"Demande d'envoi du document {document_id} par email")
            DialogUtils.show_message(self.parent, "Information", "La fonctionnalité d'envoi par email sera disponible prochainement", "info")
            
            # Fermer la fenêtre parent si spécifiée
            if parent_window and parent_window.winfo_exists():
                parent_window.destroy()
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du document par email: {e}")
            DialogUtils.show_message(self.parent, "Erreur", f"Erreur lors de l'envoi par email: {str(e)}", "error")

    def _get_client_name(self, client_id):
        """
        Récupère le nom d'un client à partir de son ID
        
        Args:
            client_id: ID du client
            
        Returns:
            Nom du client ou "Client inconnu" si non trouvé
        """
        try:
            if hasattr(self.model, 'clients'):
                client = next((c for c in self.model.clients if c.get("id") == client_id), None)
                if client:
                    return client.get('nom', '') or client.get('name', '') or client.get('société', '') or "Client sans nom"
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du nom du client: {e}")
        
        return "Client inconnu"
    
    def _on_cancel(self):
        """Appelé lorsque l'utilisateur annule"""
        logger.info("Annulation du formulaire de document")
        if callable(self.on_cancel_callback):
            self.on_cancel_callback()
        self.dialog.destroy() 