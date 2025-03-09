#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contrôleur de gestion des modèles pour l'application Vynal Docs Automator
"""

import os
import json
import logging
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from datetime import datetime

# Essayer d'importer RichTextEditor, avec un fallback si non disponible
try:
    from utils.rich_text_editor import RichTextEditor
    RICH_TEXT_AVAILABLE = True
except ImportError:
    RICH_TEXT_AVAILABLE = False
    print("Avertissement: RichTextEditor non disponible, utilisation de l'éditeur de texte standard")

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
        
        # Vérification explicite que les méthodes sont bien remplacées
        print("Connexion des événements de la vue des modèles:")
        print(f"new_template: {self.view.new_template == self.new_template}")
        print(f"edit_template: {self.view.edit_template == self.edit_template}")
        print(f"use_template: {self.view.use_template == self.use_template}")
        print(f"import_template: {self.view.import_template == self.import_template}")
        
        logger.info("Événements de TemplateView connectés")
    
    def filter_templates(self, *args):
        """
        Filtre les modèles selon les critères de recherche
        """
        self.view.update_view()
        logger.debug("Modèles filtrés")
    
    def new_template(self):
        """
        Crée un nouveau modèle de document
        """
        print("Méthode new_template appelée dans le contrôleur")
        try:
            # Créer une fenêtre de dialogue
            dialog = ctk.CTkToplevel(self.view.parent)
            dialog.title("Nouveau modèle")
            dialog.geometry("700x800")
            dialog.lift()
            dialog.focus_force()
            dialog.grab_set()
            
            # Centrer la fenêtre
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
            y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            
            # Structure globale: un main_frame pour tout le contenu
            main_frame = ctk.CTkFrame(dialog)
            main_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
            
            # Zone de défilement pour le formulaire
            form_frame = ctk.CTkScrollableFrame(main_frame)
            form_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
            
            # Champs du formulaire
            # Nom
            name_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            name_frame.pack(fill=ctk.X, pady=5)
            ctk.CTkLabel(name_frame, text="Nom*:", width=100).pack(side=ctk.LEFT)
            name_var = ctk.StringVar()
            name_entry = ctk.CTkEntry(name_frame, textvariable=name_var, width=400)
            name_entry.pack(side=ctk.LEFT, padx=10)
            
            # Type de document
            type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            type_frame.pack(fill=ctk.X, pady=5)
            ctk.CTkLabel(type_frame, text="Type*:", width=100).pack(side=ctk.LEFT)
            types = ["contrat", "facture", "proposition", "rapport", "autre"]
            type_var = ctk.StringVar(value=types[0])
            type_menu = ctk.CTkOptionMenu(type_frame, values=types, variable=type_var, width=400)
            type_menu.pack(side=ctk.LEFT, padx=10)
            
            # Description
            desc_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            desc_frame.pack(fill=ctk.X, pady=5)
            ctk.CTkLabel(desc_frame, text="Description:", width=100).pack(side=ctk.LEFT)
            description_text = ctk.CTkTextbox(desc_frame, width=400, height=60)
            description_text.pack(side=ctk.LEFT, padx=10)
            
            # Variables
            var_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            var_frame.pack(fill=ctk.X, pady=5)
            ctk.CTkLabel(var_frame, text="Variables:", width=100).pack(side=ctk.LEFT)
            variables_text = ctk.CTkTextbox(var_frame, width=400, height=80)
            variables_text.pack(side=ctk.LEFT, padx=10)
            
            var_note_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            var_note_frame.pack(fill=ctk.X)
            ctk.CTkLabel(var_note_frame, text="(Une variable par ligne)", text_color="gray").pack(pady=2)
            
            # Exemple de variables standards
            std_var_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            std_var_frame.pack(fill=ctk.X, pady=10)
            ctk.CTkLabel(std_var_frame, text="Variables standards disponibles:").pack(anchor="w")
            standard_vars = "client_name, client_company, client_email, client_phone, client_address, company_name, date"
            ctk.CTkLabel(std_var_frame, text=standard_vars, text_color="gray").pack(anchor="w")
            
            # Contenu du modèle
            content_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            content_frame.pack(fill=ctk.X, pady=10)
            ctk.CTkLabel(content_frame, text="Contenu*:", width=100).pack(anchor="nw")
            
            # Éditeur de contenu - avec fallback si RichTextEditor n'est pas disponible
            if RICH_TEXT_AVAILABLE:
                standard_variables = ["client_name", "client_company", "client_email", "client_phone", 
                                      "client_address", "company_name", "date"]
                editor_container = ctk.CTkFrame(form_frame)
                editor_container.pack(fill=ctk.BOTH, expand=True, pady=5)
                content_editor = RichTextEditor(editor_container, variable_options=standard_variables)
                content_editor.pack(fill=ctk.BOTH, expand=True)
            else:
                content_editor = ctk.CTkTextbox(form_frame, height=300)
                content_editor.pack(fill=ctk.BOTH, expand=True, pady=5)
            
            # Note explicative pour les variables
            note_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            note_frame.pack(fill=ctk.X, pady=5)
            ctk.CTkLabel(note_frame, text="Utilisez {variable} pour insérer des variables dans le contenu").pack(anchor="w")
            
            # Note obligatoire
            req_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            req_frame.pack(fill=ctk.X, pady=5)
            ctk.CTkLabel(req_frame, text="* Champs obligatoires", text_color="gray").pack(anchor="w")
            
            # Cadre pour les boutons en bas de la fenêtre
            buttons_frame = ctk.CTkFrame(main_frame)
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
                
                # Récupérer le contenu de l'éditeur
                if RICH_TEXT_AVAILABLE:
                    content = content_editor.get_content().strip()
                else:
                    content = content_editor.get("1.0", "end-1c").strip()
                
                # Validation
                if not name:
                    messagebox.showerror("Erreur", "Le nom est obligatoire", parent=dialog)
                    return
                
                if not content:
                    messagebox.showerror("Erreur", "Le contenu est obligatoire", parent=dialog)
                    return
                
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
            
            # Fonction pour annuler
            def cancel():
                dialog.destroy()
            
            # Bouton Annuler
            cancel_btn = ctk.CTkButton(
                buttons_frame, 
                text="Annuler", 
                command=cancel, 
                width=100
            )
            cancel_btn.pack(side=ctk.RIGHT, padx=10)
            
            # Bouton Enregistrer
            save_btn = ctk.CTkButton(
                buttons_frame, 
                text="Enregistrer", 
                command=save_template, 
                width=100
            )
            save_btn.pack(side=ctk.RIGHT, padx=10)
            
            # Focus sur le premier champ
            name_entry.focus_set()
            
            logger.info("Formulaire de création de modèle affiché")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du formulaire: {e}")
            messagebox.showerror("Erreur", f"Impossible d'afficher le formulaire: {str(e)}")
    
    def edit_template(self, template_id):
        """
        Édite un modèle existant
        
        Args:
            template_id: ID du modèle à modifier
        """
        print(f"Méthode edit_template appelée dans le contrôleur avec ID: {template_id}")
        # Vérifier si le modèle existe
        template = next((t for t in self.model.templates if t.get('id') == template_id), None)
        if not template:
            messagebox.showerror("Erreur", "Modèle non trouvé")
            return
        
        # Appeler la méthode new_template et la modifier pour l'édition
        # Cette partie serait similaire à new_template mais avec les données pré-remplies
        # Pour simplifier, vous pouvez implémenter cette partie plus tard
        messagebox.showinfo("Information", f"Édition du modèle {template.get('name')} à implémenter")
    
    def use_template(self, template_id):
        """
        Utilise un modèle pour créer un document
        
        Args:
            template_id: ID du modèle à utiliser
        """
        print(f"Méthode use_template appelée dans le contrôleur avec ID: {template_id}")
        # Vérifier si le modèle existe
        template = next((t for t in self.model.templates if t.get('id') == template_id), None)
        if not template:
            messagebox.showerror("Erreur", "Modèle non trouvé")
            return
        
        try:
            # Passer à la vue documents
            self.view.parent.master.show_view("documents")
            
            # Récupérer le document_controller de l'app_controller
            main_view = self.view.parent.master
            
            # Parcourir les attributs pour trouver app_controller
            app_controller = None
            for attr_name in dir(main_view):
                if attr_name == "controller":
                    app_controller = getattr(main_view, attr_name)
                    break
            
            if not app_controller:
                # Parcourir les autres attributs à la recherche du contrôleur
                for attr_name in dir(main_view):
                    attr = getattr(main_view, attr_name)
                    if hasattr(attr, "document_controller"):
                        app_controller = attr
                        break
            
            if app_controller and hasattr(app_controller, "document_controller"):
                # Appeler la méthode new_document du document_controller
                app_controller.document_controller.new_document(template_id)
                logger.info(f"Modèle {template_id} utilisé pour créer un document")
            else:
                # Essayer d'appeler directement la méthode new_document de la vue documents
                documents_view = main_view.views.get("documents")
                if documents_view and hasattr(documents_view, "new_document"):
                    documents_view.new_document(template_id)
                    logger.info(f"Modèle {template_id} utilisé pour créer un document via la vue")
                else:
                    raise Exception("Impossible de trouver le contrôleur de documents")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'utilisation du modèle: {e}")
            messagebox.showerror("Erreur", f"Impossible d'utiliser ce modèle: {str(e)}")
    
    def import_template(self):
        """
        Importe un modèle depuis un fichier
        """
        print("Méthode import_template appelée dans le contrôleur")
        # Ouvrir une boîte de dialogue pour sélectionner le fichier
        file_path = filedialog.askopenfilename(
            title="Importer un modèle",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
            parent=self.view.parent
        )
        
        if not file_path:
            return
        
        try:
            # Lire le fichier JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_template = json.load(f)
            
            # Vérifier que c'est un modèle valide
            required_fields = ['name', 'type', 'content']
            if not all(field in imported_template for field in required_fields):
                messagebox.showerror("Erreur", "Le fichier ne contient pas un modèle valide")
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
            
            # Afficher un message de succès
            messagebox.showinfo("Succès", "Modèle importé avec succès")
        
        except json.JSONDecodeError:
            messagebox.showerror("Erreur", "Le fichier JSON est invalide")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'importation du modèle: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'importation du modèle: {str(e)}")