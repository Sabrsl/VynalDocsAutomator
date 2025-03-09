#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contrôleur de gestion des modèles pour l'application Vynal Docs Automator
"""

import os
import json
import logging
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import customtkinter as ctk
from datetime import datetime
from utils.rich_text_editor import RichTextEditor

logger = logging.getLogger("VynalDocsAutomator.TemplateController")

class TemplateController:
    """
    Contrôleur de gestion des modèles
    Gère la logique métier liée aux modèles de documents
    """
    
    def __init__(self, app_model, template_view):
        """
        Initialise le contrôleur des modèles
        
        Args:
            app_model: Modèle de l'application
            template_view: Vue de gestion des modèles
        """
        self.model = app_model
        self.view = template_view
        
        # Connecter les événements de la vue aux méthodes du contrôleur
        self.connect_events()
        
        logger.info("TemplateController initialisé")
    
    def connect_events(self):
        """
        Connecte les événements de la vue aux méthodes du contrôleur
        """
        # Remplacer les méthodes de la vue par les méthodes du contrôleur
        self.view.new_template = self.new_template
        self.view.edit_template = self.edit_template
        self.view.use_template = self.use_template
        self.view.import_template = self.import_template
        self.view.filter_templates = self.filter_templates
        
        logger.info("Événements de TemplateView connectés")
    
    def filter_templates(self, *args):
        """
        Filtre les modèles selon les critères de recherche
        """
        # Cette méthode est déjà implémentée dans la vue
        # On s'assure juste qu'elle est appelée au bon moment
        self.view.update_view()
        logger.debug("Modèles filtrés")
    
    def new_template(self):
        """
        Crée un nouveau modèle de document
        """
        # Créer une fenêtre de dialogue
        dialog = ctk.CTkToplevel(self.view.parent)
        dialog.title("Nouveau modèle")
        dialog.geometry("700x800")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'+{x}+{y}')
        
        # Créer un cadre pour le formulaire
        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Champs du formulaire
        # Nom
        ctk.CTkLabel(form_frame, text="Nom*:").grid(row=0, column=0, sticky="w", pady=5)
        name_var = ctk.StringVar()
        name_entry = ctk.CTkEntry(form_frame, textvariable=name_var, width=400)
        name_entry.grid(row=0, column=1, sticky="w", pady=5)
        
        # Type de document
        ctk.CTkLabel(form_frame, text="Type*:").grid(row=1, column=0, sticky="w", pady=5)
        types = ["contrat", "facture", "proposition", "rapport", "autre"]
        type_var = ctk.StringVar(value=types[0])
        type_menu = ctk.CTkOptionMenu(form_frame, values=types, variable=type_var)
        type_menu.grid(row=1, column=1, sticky="w", pady=5)
        
        # Description
        ctk.CTkLabel(form_frame, text="Description:").grid(row=2, column=0, sticky="w", pady=5)
        description_text = ctk.CTkTextbox(form_frame, width=400, height=60)
        description_text.grid(row=2, column=1, sticky="w", pady=5)
        
        # Variables
        ctk.CTkLabel(form_frame, text="Variables:").grid(row=3, column=0, sticky="w", pady=5)
        variables_text = ctk.CTkTextbox(form_frame, width=400, height=80)
        variables_text.grid(row=3, column=1, sticky="w", pady=5)
        ctk.CTkLabel(form_frame, text="(Une variable par ligne)").grid(row=4, column=1, sticky="w")
        
        # Exemple de variables standards
        ctk.CTkLabel(form_frame, text="Variables standards disponibles:").grid(row=5, column=0, columnspan=2, sticky="w", pady=5)
        standard_vars = "client_name, client_company, client_email, client_phone, client_address, company_name, date"
        ctk.CTkLabel(form_frame, text=standard_vars, text_color="gray").grid(row=6, column=0, columnspan=2, sticky="w")
        
        # Contenu du modèle avec l'éditeur de texte enrichi
        ctk.CTkLabel(form_frame, text="Contenu*:").grid(row=7, column=0, sticky="w", pady=5)
        
        # Préparer les variables standard pour l'éditeur
        standard_variables = ["client_name", "client_company", "client_email", "client_phone", 
                             "client_address", "company_name", "date"]
        
        # Créer l'éditeur de texte enrichi
        editor_frame = ctk.CTkFrame(form_frame)
        editor_frame.grid(row=7, column=1, sticky="nsew", pady=5)
        content_editor = RichTextEditor(editor_frame, variable_options=standard_variables)
        content_editor.pack(fill=ctk.BOTH, expand=True)
        
        # Permettre à l'éditeur d'occuper plus d'espace
        form_frame.grid_rowconfigure(7, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Note explicative pour les variables
        ctk.CTkLabel(form_frame, text="Utilisez {variable} pour insérer des variables dans le contenu").grid(row=8, column=0, columnspan=2, sticky="w", pady=5)
        
        # Note obligatoire
        ctk.CTkLabel(form_frame, text="* Champs obligatoires", text_color="gray").grid(row=9, column=0, columnspan=2, sticky="w", pady=10)
        
        # Boutons
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, pady=10)
        
        # Fonction pour sauvegarder
        def save_template():
            # Récupérer les valeurs
            name = name_var.get().strip()
            template_type = type_var.get().strip()
            description = description_text.get("1.0", "end-1c").strip()
            
            # Récupérer les variables (une par ligne)
            variables_raw = variables_text.get("1.0", "end-1c").strip()
            variables = [v.strip() for v in variables_raw.split('\n') if v.strip()]
            
            # Récupérer le contenu de l'éditeur de texte enrichi
            content = content_editor.get_content().strip()
            
            # Validation
            if not name:
                messagebox.showerror("Erreur", "Le nom est obligatoire", parent=dialog)
                return
            
            if not content:
                messagebox.showerror("Erreur", "Le contenu est obligatoire", parent=dialog)
                return
            
            # Afficher un indicateur de chargement pendant la sauvegarde
            save_indicator = ctk.CTkLabel(
                buttons_frame,
                text="Enregistrement...",
                text_color="#3498db",
                font=ctk.CTkFont(size=12)
            )
            save_indicator.pack(side=ctk.LEFT, padx=10)
            dialog.update_idletasks()
            
            try:
                # Créer un dictionnaire avec les données
                template_data = {
                    'name': name,
                    'type': template_type,
                    'description': description,
                    'variables': variables,
                    'content': content,
                    'id': f"template_{len(self.model.templates) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                # Ajouter à la liste
                self.model.templates.append(template_data)
                
                # Sauvegarder les changements
                self.model.save_templates()
                
                # Mettre à jour la vue
                self.view.update_view()
                
                # Ajouter l'activité
                self.model.add_activity('template', f"Nouveau modèle: {name}")
                
                # Fermer la fenêtre
                dialog.destroy()
                
                logger.info(f"Nouveau modèle créé: {template_data['id']} - {name}")
                
                # Afficher un message de succès
                messagebox.showinfo("Succès", "Modèle ajouté avec succès")
            
            except Exception as e:
                save_indicator.destroy()
                messagebox.showerror("Erreur", f"Erreur lors de l'enregistrement: {str(e)}", parent=dialog)
        
        # Fonction pour annuler
        def cancel():
            dialog.destroy()
        
        # Bouton Annuler
        ctk.CTkButton(buttons_frame, text="Annuler", command=cancel, width=100).pack(side=ctk.RIGHT, padx=10)
        
        # Bouton Enregistrer
        ctk.CTkButton(buttons_frame, text="Enregistrer", command=save_template, width=100).pack(side=ctk.RIGHT, padx=10)
        
        # Focus sur le premier champ
        name_entry.focus_set()
        
        logger.info("Formulaire de création de modèle affiché")
    
    def edit_template(self, template_id):
        """
        Édite un modèle existant
        
        Args:
            template_id: ID du modèle à modifier
        """
        # Vérifier si le modèle existe
        template = next((t for t in self.model.templates if t.get('id') == template_id), None)
        if not template:
            messagebox.showerror("Erreur", "Modèle non trouvé")
            return
        
        # Créer une fenêtre de dialogue
        dialog = ctk.CTkToplevel(self.view.parent)
        dialog.title(f"Modifier le modèle - {template.get('name')}")
        dialog.geometry("700x800")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Créer un cadre pour le formulaire
        form_frame = ctk.CTkFrame(dialog)
        form_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Champs du formulaire
        # Nom
        ctk.CTkLabel(form_frame, text="Nom*:").grid(row=0, column=0, sticky="w", pady=5)
        name_var = ctk.StringVar(value=template.get('name', ''))
        name_entry = ctk.CTkEntry(form_frame, textvariable=name_var, width=400)
        name_entry.grid(row=0, column=1, sticky="w", pady=5)
        
        # Type de document
        ctk.CTkLabel(form_frame, text="Type*:").grid(row=1, column=0, sticky="w", pady=5)
        types = ["contrat", "facture", "proposition", "rapport", "autre"]
        current_type = template.get('type', 'contrat')
        if current_type not in types:
            types.append(current_type)
        type_var = ctk.StringVar(value=current_type)
        type_menu = ctk.CTkOptionMenu(form_frame, values=types, variable=type_var)
        type_menu.grid(row=1, column=1, sticky="w", pady=5)
        
        # Description
        ctk.CTkLabel(form_frame, text="Description:").grid(row=2, column=0, sticky="w", pady=5)
        description_text = ctk.CTkTextbox(form_frame, width=400, height=60)
        description_text.grid(row=2, column=1, sticky="w", pady=5)
        description_text.insert("1.0", template.get('description', ''))
        
        # Variables
        ctk.CTkLabel(form_frame, text="Variables:").grid(row=3, column=0, sticky="w", pady=5)
        variables_text = ctk.CTkTextbox(form_frame, width=400, height=80)
        variables_text.grid(row=3, column=1, sticky="w", pady=5)
        variables = template.get('variables', [])
        variables_text.insert("1.0", "\n".join(variables))
        ctk.CTkLabel(form_frame, text="(Une variable par ligne)").grid(row=4, column=1, sticky="w")
        
        # Exemple de variables standards
        ctk.CTkLabel(form_frame, text="Variables standards disponibles:").grid(row=5, column=0, columnspan=2, sticky="w", pady=5)
        standard_vars = "client_name, client_company, client_email, client_phone, client_address, company_name, date"
        ctk.CTkLabel(form_frame, text=standard_vars, text_color="gray").grid(row=6, column=0, columnspan=2, sticky="w")
        
        # Contenu du modèle avec l'éditeur de texte enrichi
        ctk.CTkLabel(form_frame, text="Contenu*:").grid(row=7, column=0, sticky="w", pady=5)
        
        # Préparer les variables pour l'éditeur
        standard_variables = ["client_name", "client_company", "client_email", "client_phone", 
                             "client_address", "company_name", "date"]
        # Ajouter les variables personnalisées
        all_variables = standard_variables + variables
        
        # Créer l'éditeur de texte enrichi
        editor_frame = ctk.CTkFrame(form_frame)
        editor_frame.grid(row=7, column=1, sticky="nsew", pady=5)
        content_editor = RichTextEditor(editor_frame, initial_content=template.get('content', ''), 
                                      variable_options=all_variables)
        content_editor.pack(fill=ctk.BOTH, expand=True)
        
        # Permettre à l'éditeur d'occuper plus d'espace
        form_frame.grid_rowconfigure(7, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Note explicative pour les variables
        ctk.CTkLabel(form_frame, text="Utilisez {variable} pour insérer des variables dans le contenu").grid(row=8, column=0, columnspan=2, sticky="w", pady=5)
        
        # Note obligatoire
        ctk.CTkLabel(form_frame, text="* Champs obligatoires", text_color="gray").grid(row=9, column=0, columnspan=2, sticky="w", pady=10)
        
        # Boutons
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, pady=10)
        
        # Fonction pour sauvegarder
        def save_template():
            # Récupérer les valeurs
            name = name_var.get().strip()
            template_type = type_var.get().strip()
            description = description_text.get("1.0", "end-1c").strip()
            
            # Récupérer les variables (une par ligne)
            variables_raw = variables_text.get("1.0", "end-1c").strip()
            variables = [v.strip() for v in variables_raw.split('\n') if v.strip()]
            
            # Récupérer le contenu de l'éditeur de texte enrichi
            content = content_editor.get_content().strip()
            
            # Validation
            if not name:
                messagebox.showerror("Erreur", "Le nom est obligatoire", parent=dialog)
                return
            
            if not content:
                messagebox.showerror("Erreur", "Le contenu est obligatoire", parent=dialog)
                return
            
            # Afficher un indicateur de chargement pendant la sauvegarde
            save_indicator = ctk.CTkLabel(
                buttons_frame,
                text="Enregistrement...",
                text_color="#3498db",
                font=ctk.CTkFont(size=12)
            )
            save_indicator.pack(side=ctk.LEFT, padx=10)
            dialog.update_idletasks()
            
            try:
                # Créer un dictionnaire avec les données
                template_data = {
                    'id': template_id,
                    'name': name,
                    'type': template_type,
                    'description': description,
                    'variables': variables,
                    'content': content,
                    'created_at': template.get('created_at', datetime.now().isoformat()),
                    'updated_at': datetime.now().isoformat()
                }
                
                # Trouver l'index du modèle dans la liste
                template_index = next((i for i, t in enumerate(self.model.templates) if t.get('id') == template_id), None)
                if template_index is not None:
                    # Remplacer le modèle dans la liste
                    self.model.templates[template_index] = template_data
                    
                    # Sauvegarder les changements
                    self.model.save_templates()
                    
                    # Mettre à jour la vue
                    self.view.update_view()
                    
                    # Ajouter l'activité
                    self.model.add_activity('template', f"Modèle modifié: {name}")
                    
                    # Fermer la fenêtre
                    dialog.destroy()
                    
                    logger.info(f"Modèle modifié: {template_id} - {name}")
                    
                    # Afficher un message de succès
                    messagebox.showinfo("Succès", "Modèle modifié avec succès")
                else:
                    messagebox.showerror("Erreur", "Modèle non trouvé", parent=dialog)
            
            except Exception as e:
                save_indicator.destroy()
                messagebox.showerror("Erreur", f"Erreur lors de l'enregistrement: {str(e)}", parent=dialog)
        
        # Fonction pour annuler
        def cancel():
            dialog.destroy()
        
        # Bouton Annuler
        ctk.CTkButton(buttons_frame, text="Annuler", command=cancel, width=100).pack(side=ctk.RIGHT, padx=10)
        
        # Bouton Enregistrer
        ctk.CTkButton(buttons_frame, text="Enregistrer", command=save_template, width=100).pack(side=ctk.RIGHT, padx=10)
        
        logger.info(f"Formulaire d'édition de modèle affiché pour {template_id}")
    
    def use_template(self, template_id):
        """
        Utilise un modèle pour créer un document
        
        Args:
            template_id: ID du modèle à utiliser
        """
        # Vérifier si le modèle existe
        template = next((t for t in self.model.templates if t.get('id') == template_id), None)
        if not template:
            messagebox.showerror("Erreur", "Modèle non trouvé")
            return
        
        # Changer de vue pour créer un document avec ce modèle
        # Généralement, on passe à la vue documents et on préremplit le formulaire
        
        # Ici, nous allons simplement ouvrir la vue Documents et laisser le contrôleur de documents faire le reste
        from controllers.document_controller import DocumentController
        
        # Passer à la vue documents
        self.view.parent.master.show_view("documents")
        
        # Obtenir le contrôleur de documents
        document_controller = None
        for controller_name in dir(self.view.parent.master):
            controller = getattr(self.view.parent.master, controller_name)
            if isinstance(controller, DocumentController):
                document_controller = controller
                break
        
        # Appeler la méthode new_document du contrôleur de documents avec le modèle préselectionné
        if document_controller:
            if hasattr(document_controller, 'new_document'):
                # Passer l'ID du modèle à la méthode new_document
                document_controller.new_document(template_id)
            else:
                messagebox.showerror("Erreur", "Contrôleur de documents non configuré correctement")
        else:
            messagebox.showerror("Erreur", "Contrôleur de documents non trouvé")
        
        logger.info(f"Utilisation du modèle {template_id} pour créer un document")
    
    def import_template(self):
        """
        Importe un modèle depuis un fichier
        """
        # Ouvrir une boîte de dialogue pour sélectionner le fichier
        file_path = filedialog.askopenfilename(
            title="Importer un modèle",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
            parent=self.view.parent
        )
        
        if not file_path:
            return
        
        # Créer une fenêtre de dialogue pour afficher l'avancement et le résultat
        dialog = ctk.CTkToplevel(self.view.parent)
        dialog.title("Importation de modèle")
        dialog.geometry("400x200")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Créer un cadre pour le contenu
        content_frame = ctk.CTkFrame(dialog)
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Message initial
        status_label = ctk.CTkLabel(
            content_frame,
            text="Importation du modèle en cours...",
            font=ctk.CTkFont(size=14)
        )
        status_label.pack(pady=20)
        
        # Indicateur de progression
        progress_bar = ctk.CTkProgressBar(content_frame)
        progress_bar.pack(pady=10, fill=ctk.X)
        progress_bar.set(0.5)  # Valeur indéterminée
        
        # Mettre à jour l'interface
        dialog.update_idletasks()
        
        try:
            # Lire le fichier JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_template = json.load(f)
            
            # Vérifier que c'est un modèle valide
            required_fields = ['name', 'type', 'content']
            if not all(field in imported_template for field in required_fields):
                status_label.configure(text="❌ Erreur: Le fichier ne contient pas un modèle valide", text_color="red")
                progress_bar.set(0)  # Indiquer l'échec
                
                # Bouton Fermer
                ctk.CTkButton(content_frame, text="Fermer", command=dialog.destroy, width=100).pack(pady=10)
                return
            
            # Générer un nouvel ID
            imported_template['id'] = f"template_{len(self.model.templates) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            imported_template['created_at'] = datetime.now().isoformat()
            imported_template['updated_at'] = datetime.now().isoformat()
            
            # Ajouter à la liste
            self.model.templates.append(imported_template)
            
            # Sauvegarder les changements
            self.model.save_templates()
            
            # Mettre à jour la vue
            self.view.update_view()
            
            # Ajouter l'activité
            self.model.add_activity('template', f"Modèle importé: {imported_template['name']}")
            
            logger.info(f"Modèle importé: {imported_template['id']} - {imported_template['name']}")
            
            # Afficher le succès
            status_label.configure(text=f"✅ Succès: Modèle '{imported_template['name']}' importé", text_color="green")
            progress_bar.set(1)  # Indiquer le succès
            
            # Bouton Fermer
            ctk.CTkButton(content_frame, text="Fermer", command=dialog.destroy, width=100).pack(pady=10)
            
        except json.JSONDecodeError:
            status_label.configure(text="❌ Erreur: Format JSON invalide", text_color="red")
            progress_bar.set(0)  # Indiquer l'échec
            
            # Bouton Fermer
            ctk.CTkButton(content_frame, text="Fermer", command=dialog.destroy, width=100).pack(pady=10)
        
        except Exception as e:
            logger.error(f"Erreur lors de l'importation du modèle: {e}")
            status_label.configure(text=f"❌ Erreur: {str(e)}", text_color="red")
            progress_bar.set(0)  # Indiquer l'échec
            
            # Bouton Fermer
            ctk.CTkButton(content_frame, text="Fermer", command=dialog.destroy, width=100).pack(pady=10)