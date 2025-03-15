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
    
    def __init__(self, parent, model, document_data=None, folder_id=None, import_mode=False, on_save_callback=None):
        """Initialise le formulaire de document"""
        self.parent = parent
        self.model = model
        self.document_data = document_data or {}
        self.folder_id = folder_id
        self.import_mode = import_mode
        self.on_save_callback = on_save_callback
        
        # Créer la boîte de dialogue
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Nouveau document" if not import_mode else "Importer un document")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        self.dialog.grab_set()
        
        # Centrer la fenêtre
        self.dialog.update_idletasks()
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width - self.dialog.winfo_width()) // 2
        y = (screen_height - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
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
        
        # Titre du document
        name_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        name_frame.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(name_frame, text="Titre*:", width=100).pack(side=ctk.LEFT)
        title_entry = ctk.CTkEntry(name_frame, textvariable=self.title_var, width=400)
        title_entry.pack(side=ctk.LEFT, padx=10)
        
        # Type de document
        type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        type_frame.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(type_frame, text="Type*:", width=100).pack(side=ctk.LEFT)
        
        # Obtenir les types de documents disponibles
        types = set()  # Utiliser un set pour éviter les doublons
        try:
            # Types par défaut toujours disponibles
            default_types = ["contrat", "facture", "proposition", "rapport", "autre"]
            types.update(default_types)
            
            # Récupérer les types depuis les modèles
            if hasattr(self.model, 'templates'):
                if isinstance(self.model.templates, list):
                    for template in self.model.templates:
                        template_type = template.get('type', '').strip()
                        if template_type:
                            types.add(template_type)
                elif isinstance(self.model.templates, dict):
                    for template_id, template in self.model.templates.items():
                        template_type = template.get('type', '').strip()
                        if template_type:
                            types.add(template_type)
            
            # Récupérer les types des documents existants
            if hasattr(self.model, 'documents'):
                if isinstance(self.model.documents, list):
                    for doc in self.model.documents:
                        doc_type = doc.get("type", "").strip()
                        if doc_type:
                            types.add(doc_type)
                elif isinstance(self.model.documents, dict):
                    for doc_id, doc in self.model.documents.items():
                        doc_type = doc.get("type", "").strip()
                        if doc_type:
                            types.add(doc_type)
            
            # Convertir en liste triée
            types = sorted(list(types))
            
            logger.debug(f"Types de documents disponibles : {types}")
            
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des types: {e}")
            types = ["contrat", "facture", "proposition", "rapport", "autre"]
        
        type_menu = ctk.CTkOptionMenu(type_frame, values=types, variable=self.type_var, width=400)
        type_menu.pack(side=ctk.LEFT, padx=10)
        
        # Sélection du modèle
        template_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        template_frame.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(template_frame, text="Modèle*:", width=100).pack(side=ctk.LEFT)
        
        # Préparer les options du modèle
        template_options = ["Sélectionner un modèle"]
        try:
            # Gérer les cas où templates est une liste ou un dictionnaire
            if hasattr(self.model, 'templates'):
                if isinstance(self.model.templates, list):
                    for template in self.model.templates:
                        name = template.get('name', '')
                        if name:
                            template_options.append(f"{name} ({template.get('type', '')})")
                elif isinstance(self.model.templates, dict):
                    for template_id, template in self.model.templates.items():
                        name = template.get('name', '')
                        if name:
                            template_options.append(f"{name} ({template.get('type', '')})")
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des modèles: {e}")
        
        # Créer le combobox pour les modèles
        template_combo = ctk.CTkComboBox(
            template_frame, 
            width=400,
            values=template_options,
            command=self._update_template_info
        )
        template_combo.pack(side=ctk.LEFT, padx=10)
        
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
        
        # Préparer les options des clients
        client_options = ["Sélectionner un client"]
        try:
            # Gérer les cas où clients est une liste ou un dictionnaire
            if hasattr(self.model, 'clients'):
                if isinstance(self.model.clients, list):
                    for client in self.model.clients:
                        name = client.get('name', '')
                        if name:
                            if client.get('company'):
                                name += f" ({client.get('company')})"
                            client_options.append(name)
                elif isinstance(self.model.clients, dict):
                    for client_id, client in self.model.clients.items():
                        name = client.get('name', '')
                        if name:
                            if client.get('company'):
                                name += f" ({client.get('company')})"
                            client_options.append(name)
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des clients: {e}")
        
        # Créer le combobox pour les clients
        client_combo = ctk.CTkComboBox(
            client_frame, 
            width=400,
            values=client_options,
            command=self._update_client_info
        )
        client_combo.pack(side=ctk.LEFT, padx=10)
        
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
            command=self.dialog.destroy
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
        selected_name = self.template_combo.get()
        
        if selected_name == "Sélectionner un modèle":
            self.template_info_label.configure(text="Sélectionnez un modèle pour voir les détails")
            for widget in self.variables_frame.winfo_children():
                widget.destroy()
            return
            
        # Trouver le modèle correspondant
        template = None
        if hasattr(self.model, 'templates'):
            if isinstance(self.model.templates, list):
                for t in self.model.templates:
                    if t.get('name') and selected_name.startswith(t.get('name')):
                        template = t
                        break
            elif isinstance(self.model.templates, dict):
                for t_id, t in self.model.templates.items():
                    if t.get('name') and selected_name.startswith(t.get('name')):
                        template = t
                        break
        
        if not template:
            self.template_info_label.configure(text="Modèle non trouvé")
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
        
        # Afficher les variables du modèle
        self._show_template_variables()
    
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
        """Récupère le client sélectionné - Version corrigée avec journalisation détaillée"""
        selected_name = self.client_combo.get()
        
        # Journalisation pour le débogage
        logger.debug(f"Tentative de récupération du client: '{selected_name}'")
        
        if selected_name == "Sélectionner un client":
            logger.warning("Aucun client sélectionné")
            return None
        
        # Trouver le client en fonction du type de structure
        if hasattr(self.model, 'clients'):
            # Log la structure des clients pour le débogage
            logger.debug(f"Type de la structure clients: {type(self.model.clients)}")
            
            if isinstance(self.model.clients, list):
                logger.debug(f"Recherche dans une liste de {len(self.model.clients)} clients")
                
                for client in self.model.clients:
                    client_name = client.get('name', '')
                    if client.get('company'):
                        full_name = f"{client_name} ({client.get('company')})"
                    else:
                        full_name = client_name
                    
                    # Plus flexible: vérifie si le texte sélectionné correspond au début du nom du client
                    if client_name and selected_name.startswith(client_name):
                        logger.info(f"Client trouvé par nom: {client_name}, ID: {client.get('id')}")
                        return client.get('id')
                    
                    # Vérification additionnelle avec le nom complet
                    if full_name and selected_name.startswith(full_name):
                        logger.info(f"Client trouvé par nom complet: {full_name}, ID: {client.get('id')}")
                        return client.get('id')
                    
            elif isinstance(self.model.clients, dict):
                logger.debug(f"Recherche dans un dictionnaire de {len(self.model.clients)} clients")
                
                for client_id, client in self.model.clients.items():
                    client_name = client.get('name', '')
                    if client.get('company'):
                        full_name = f"{client_name} ({client.get('company')})"
                    else:
                        full_name = client_name
                    
                    # Plus flexible: vérifie si le texte sélectionné correspond au début du nom du client
                    if client_name and selected_name.startswith(client_name):
                        logger.info(f"Client trouvé par nom: {client_name}, ID: {client_id}")
                        return client_id
                    
                    # Vérification additionnelle avec le nom complet
                    if full_name and selected_name.startswith(full_name):
                        logger.info(f"Client trouvé par nom complet: {full_name}, ID: {client_id}")
                        return client_id
        else:
            logger.error("Le modèle n'a pas d'attribut 'clients'")
        
        # Méthode alternative: extraction de l'ID du client à partir du texte
        try:
            # Cas où le nom affiché contient un ID entre parenthèses
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
        """Enregistre le document"""
        try:
            # Récupérer et valider les valeurs du formulaire
            title = self.title_var.get().strip()
            if not title:
                DialogUtils.show_message(self.dialog, "Erreur", "Le titre est obligatoire", "error")
                return
            
            doc_type = self.type_var.get().strip()
            if not doc_type:
                DialogUtils.show_message(self.dialog, "Erreur", "Le type est obligatoire", "error")
                return
            
            client_id = self.get_selected_client()
            if not client_id:
                DialogUtils.show_message(self.dialog, "Erreur", "Veuillez sélectionner un client", "error")
                return
            
            # Validation robuste du client_id
            client_exists = False
            client_name = None
            
            # Vérifier dans la structure clients (liste ou dictionnaire)
            if isinstance(self.model.clients, list):
                for client in self.model.clients:
                    if client.get('id') == client_id:
                        client_exists = True
                        client_name = client.get('name')
                        break
            elif isinstance(self.model.clients, dict):
                if client_id in self.model.clients:
                    client = self.model.clients[client_id]
                    if isinstance(client, dict):
                        client_exists = True
                        client_name = client.get('name')
            
            if not client_exists:
                logger.error(f"Client introuvable lors de la validation finale (ID: {client_id})")
                DialogUtils.show_message(self.dialog, "Erreur", "Le client sélectionné n'existe plus dans la base de données", "error")
                return
            
            template_id = self.get_selected_template()
            if not template_id:
                DialogUtils.show_message(self.dialog, "Erreur", "Veuillez sélectionner un modèle", "error")
                return
            
            # Récupérer les valeurs des variables personnalisées
            variables = {}
            for var_name, var_var in self.variable_entries.items():
                variables[var_name] = var_var.get()
            
            # Créer le document avec un ID unique
            import uuid
            document_id = str(uuid.uuid4())
            document = {
                "id": document_id,
                "title": title,
                "type": doc_type,
                "client_id": client_id,
                "template_id": template_id,
                "folder_id": self.folder_id,
                "variables": variables,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "created_at": datetime.now().isoformat(),
                "classification": {
                    "client": {
                        "id": client_id,
                        "name": client_name
                    },
                    "type": doc_type,
                    "date": {
                        "year": datetime.now().strftime("%Y"),
                        "month": datetime.now().strftime("%m"),
                        "full": datetime.now().strftime("%Y-%m-%d")
                    }
                }
            }
            
            logger.info(f"Tentative de sauvegarde du document: {title} pour client {client_name} (ID: {client_id})")
            
            # Générer le document physique
            try:
                # Récupérer le modèle et le client complets
                template = None
                client = None
                
                # Trouver le modèle correspondant
                if isinstance(self.model.templates, list):
                    for t in self.model.templates:
                        if t.get('id') == template_id:
                            template = t
                            break
                elif isinstance(self.model.templates, dict):
                    template = self.model.templates.get(template_id)
                
                # Trouver le client correspondant
                if isinstance(self.model.clients, list):
                    for c in self.model.clients:
                        if c.get('id') == client_id:
                            client = c
                            break
                elif isinstance(self.model.clients, dict):
                    client = self.model.clients.get(client_id)
                
                if not template:
                    logger.error(f"Modèle introuvable (ID: {template_id})")
                    raise ValueError(f"Modèle introuvable (ID: {template_id})")
                    
                if not client:
                    logger.error(f"Client introuvable (ID: {client_id})")
                    raise ValueError(f"Client introuvable (ID: {client_id})")
                
                # Préparer les informations de l'entreprise
                company_info = {}
                if hasattr(self.model, 'config'):
                    company_info = {
                        "name": self.model.config.get("app.company_name", ""),
                        "address": self.model.config.get("app.company_address", ""),
                        "email": self.model.config.get("app.company_email", ""),
                        "phone": self.model.config.get("app.company_phone", ""),
                        "website": self.model.config.get("app.company_website", "")
                    }
                
                # Créer le générateur de documents
                from utils.document_generator import DocumentGenerator
                generator = DocumentGenerator(getattr(self.model, 'config', None))
                
                # Générer le nom du fichier
                clean_title = generator.clean_filename(title)
                clean_client_name = generator.clean_filename(client.get('name', 'client'))
                clean_doc_type = generator.clean_filename(doc_type)
                current_date = datetime.now()
                date_str = current_date.strftime("%Y-%m-%d")
                year_str = current_date.strftime("%Y")
                month_str = current_date.strftime("%m")
                day_str = current_date.strftime("%d")
                
                # Structure hiérarchique des dossiers
                doc_base_dir = getattr(self.model, 'paths', {}).get('documents', 'data/documents')
                
                # Structure par client / type / date
                client_dir = os.path.join(doc_base_dir, 'clients', clean_client_name)
                type_dir = os.path.join(doc_base_dir, 'types', clean_doc_type)
                date_dir = os.path.join(doc_base_dir, 'dates', year_str, month_str, day_str)
                
                # Créer les dossiers s'ils n'existent pas
                os.makedirs(client_dir, exist_ok=True)
                os.makedirs(type_dir, exist_ok=True)
                os.makedirs(date_dir, exist_ok=True)
                
                format_type = "pdf"  # format par défaut
                if hasattr(self.model, 'config'):
                    format_type = self.model.config.get("document.default_format", "pdf")
                
                # Générer le nom de fichier
                file_name = f"{clean_title}_{clean_client_name}_{date_str}.{format_type}"
                
                # Chemins complets pour chaque classification
                client_file_path = os.path.join(client_dir, file_name)
                type_file_path = os.path.join(type_dir, file_name)
                date_file_path = os.path.join(date_dir, file_name)
                
                # Générer le document principal (dans le dossier client)
                success = generator.generate_document(
                    client_file_path,
                    template,
                    client,
                    company_info,
                    variables,
                    format_type
                )
                
                if not success:
                    logger.error(f"Échec de la génération du document: {client_file_path}")
                    raise ValueError("Échec de la génération du document")
                
                # Créer des copies pour les autres structures de classement
                import shutil
                try:
                    # Copier vers le dossier type
                    shutil.copy2(client_file_path, type_file_path)
                    # Copier vers le dossier date
                    shutil.copy2(client_file_path, date_file_path)
                    logger.info(f"Copies du document créées pour les classifications par type et date")
                except Exception as copy_error:
                    logger.warning(f"Erreur lors de la création des copies: {copy_error}")
                
                # Ajouter tous les chemins d'accès au document
                document["file_paths"] = {
                    "main": client_file_path,  # Chemin principal (dans le dossier client)
                    "by_client": client_file_path,
                    "by_type": type_file_path,
                    "by_date": date_file_path
                }
                
                # Vérifier et valider tous les chemins
                valid_paths = {}
                for path_type, path in document["file_paths"].items():
                    if path and os.path.exists(path):
                        valid_paths[path_type] = path
                    else:
                        logger.warning(f"Chemin {path_type} invalide ou manquant: {path}")
                
                # S'assurer qu'il y a au moins un chemin valide
                if not valid_paths:
                    raise ValueError("Aucun chemin de fichier valide pour le document")
                
                document["file_paths"] = valid_paths
                document["file_path"] = valid_paths.get("main", next(iter(valid_paths.values())))
                
                # Assurer la compatibilité avec le code existant
                logger.info(f"Document généré avec succès: {document['file_path']}")
                
                # Vérifier que le document est complet avant la sauvegarde
                required_fields = ["id", "title", "type", "client_id", "template_id", "file_path", "file_paths"]
                missing_fields = [field for field in required_fields if field not in document]
                if missing_fields:
                    logger.warning(f"Champs manquants dans le document: {missing_fields}")
                    # Ajouter des valeurs par défaut pour les champs manquants
                    for field in missing_fields:
                        if field == "id":
                            document[field] = str(uuid.uuid4())
                        elif field in ["title", "type"]:
                            document[field] = "Sans titre" if field == "title" else "autre"
                        elif field == "file_paths" and "file_path" in document:
                            document[field] = {"main": document["file_path"]}
                        elif field == "file_path" and "file_paths" in document:
                            document[field] = document["file_paths"].get("main", "")
                
            except Exception as gen_error:
                logger.error(f"Erreur lors de la génération du document: {gen_error}")
                DialogUtils.show_message(
                    self.dialog,
                    "Erreur",
                    f"Erreur lors de la génération du document: {str(gen_error)}",
                    "error"
                )
                return  # Arrêter le processus en cas d'erreur de génération
            
            # Vérifier et initialiser la structure documents si nécessaire
            if not hasattr(self.model, 'documents'):
                self.model.documents = []
                logger.info("Initialisation de la structure documents")
            elif self.model.documents is None:
                self.model.documents = []
                logger.info("Réinitialisation de la structure documents")
            
            # Ajouter le document selon la structure du modèle
            if isinstance(self.model.documents, list):
                self.model.documents.append(document)
                logger.debug(f"Document ajouté à la liste (total: {len(self.model.documents)})")
            elif isinstance(self.model.documents, dict):
                self.model.documents[document_id] = document
                logger.debug(f"Document ajouté au dictionnaire (total: {len(self.model.documents)})")
            else:
                logger.warning(f"Type de structure non supporté: {type(self.model.documents)}")
                self.model.documents = [document]
                logger.info("Structure documents convertie en liste")
            
            # Sauvegarder les changements
            save_success = False
            try:
                if hasattr(self.model, 'save_documents'):
                    # Sauvegarder d'abord le nouveau document dans une variable temporaire
                    current_doc = dict(document)
                    
                    # Tenter la sauvegarde
                    self.model.save_documents()
                    save_success = True
                    logger.info("Documents sauvegardés avec succès")
                    
                    # Vérifier que le document est bien présent après la sauvegarde
                    doc_exists = False
                    if isinstance(self.model.documents, list):
                        doc_exists = any(d.get('id') == document_id for d in self.model.documents)
                    elif isinstance(self.model.documents, dict):
                        doc_exists = document_id in self.model.documents
                    
                    if not doc_exists:
                        # Le document a été perdu pendant la sauvegarde, le réajouter
                        if isinstance(self.model.documents, list):
                            self.model.documents.append(current_doc)
                        elif isinstance(self.model.documents, dict):
                            self.model.documents[document_id] = current_doc
                        # Retenter la sauvegarde
                        try:
                            self.model.save_documents()
                            save_success = True
                            logger.info("Document restauré et sauvegardé avec succès")
                        except Exception as retry_error:
                            logger.error(f"Erreur lors de la nouvelle tentative de sauvegarde: {retry_error}")
                            save_success = False
            except Exception as save_error:
                logger.error(f"Erreur lors de la sauvegarde: {save_error}")
                save_success = False
            
            if not save_success:
                logger.warning("Sauvegarde non confirmée")
                DialogUtils.show_message(
                    self.dialog,
                    "Avertissement",
                    "Le document a été créé mais la sauvegarde n'est pas confirmée. Vérifiez qu'il apparaît bien dans la liste.",
                    "warning"
                )
            else:
                # Afficher un message de succès
                DialogUtils.show_message(
                    self.dialog,
                    "Succès",
                    f"Le document '{title}' a été créé avec succès",
                    "success"
                )
            
            # Fermer la fenêtre après un court délai
            self.dialog.after(1500, self.dialog.destroy)
            
            # Appeler le callback si fourni
            if self.on_save_callback:
                try:
                    self.on_save_callback()
                    logger.info("Callback exécuté avec succès")
                except Exception as callback_error:
                    logger.error(f"Erreur lors de l'exécution du callback: {callback_error}")
            
            logger.info(f"Document '{title}' créé avec succès (ID: {document_id})")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du document: {e}")
            DialogUtils.show_message(
                self.dialog,
                "Erreur",
                f"Impossible de sauvegarder le document: {str(e)}",
                "error"
            ) 