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
        dialog = tk.Toplevel(self.view.parent)
        dialog.title("Nouveau modèle")
        dialog.geometry("800x750")
        dialog.resizable(True, True)
        dialog.grab_set()  # Modal
        dialog.focus_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Créer un cadre pour le formulaire
        form_frame = tk.Frame(dialog, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Champs du formulaire
        # Nom
        tk.Label(form_frame, text="Nom*:").grid(row=0, column=0, sticky="w", pady=5)
        name_var = tk.StringVar()
        name_entry = tk.Entry(form_frame, textvariable=name_var, width=40)
        name_entry.grid(row=0, column=1, sticky="w", pady=5)
        
        # Type de document
        tk.Label(form_frame, text="Type*:").grid(row=1, column=0, sticky="w", pady=5)
        types = ["Contrat", "Facture", "Proposition", "Rapport", "Autre"]
        type_var = tk.StringVar(value=types[0])
        type_menu = tk.OptionMenu(form_frame, type_var, *types)
        type_menu.grid(row=1, column=1, sticky="w", pady=5)
        
        # Description
        tk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky="w", pady=5)
        description_text = tk.Text(form_frame, width=40, height=3)
        description_text.grid(row=2, column=1, sticky="w", pady=5)
        
        # Variables
        tk.Label(form_frame, text="Variables:").grid(row=3, column=0, sticky="w", pady=5)
        variables_text = tk.Text(form_frame, width=40, height=5)
        variables_text.grid(row=3, column=1, sticky="w", pady=5)
        tk.Label(form_frame, text="(Une variable par ligne)").grid(row=4, column=1, sticky="w")
        
        # Exemple de variables standards
        tk.Label(form_frame, text="Variables standards disponibles:").grid(row=5, column=0, columnspan=2, sticky="w", pady=5)
        standard_vars = "client_name, client_company, client_email, client_phone, client_address, company_name, date"
        tk.Label(form_frame, text=standard_vars, fg="gray").grid(row=6, column=0, columnspan=2, sticky="w")
        
        # Contenu du modèle avec éditeur enrichi
        tk.Label(form_frame, text="Contenu*:").grid(row=7, column=0, sticky="w", pady=5)
        content_text = RichTextEditor(form_frame, variable_options=standard_vars.split(", "), height=350, width=600)
        content_text.grid(row=7, column=1, sticky="w", pady=5)
        
        # Note explicative pour les variables
        tk.Label(form_frame, text="Utilisez {variable} pour insérer des variables dans le contenu").grid(row=8, column=0, columnspan=2, sticky="w", pady=5)
        
        # Note obligatoire
        tk.Label(form_frame, text="* Champs obligatoires", fg="gray").grid(row=9, column=0, columnspan=2, sticky="w", pady=10)
        
        # Boutons
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Fonction pour sauvegarder
        def save_template():
            # Récupérer les valeurs
            name = name_var.get().strip()
            template_type = type_var.get().strip()
            description = description_text.get("1.0", "end-1c").strip()
            
            # Récupérer les variables (une par ligne)
            variables_raw = variables_text.get("1.0", "end-1c").strip()
            variables = [v.strip() for v in variables_raw.split('\n') if v.strip()]
            
            # Récupérer le contenu
            content = content_text.get_content().strip()
            
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
        cancel_btn = tk.Button(button_frame, text="Annuler", command=cancel, width=10)
        cancel_btn.pack(side=tk.RIGHT, padx=10)
        
        # Bouton Enregistrer
        save_btn = tk.Button(button_frame, text="Enregistrer", command=save_template, width=10)
        save_btn.pack(side=tk.RIGHT, padx=10)
        
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
        dialog = tk.Toplevel(self.view.parent)
        dialog.title(f"Modifier le modèle - {template.get('name')}")
        dialog.geometry("800x750")
        dialog.resizable(True, True)
        dialog.grab_set()  # Modal
        dialog.focus_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Créer un cadre pour le formulaire
        form_frame = tk.Frame(dialog, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Champs du formulaire
        # Nom
        tk.Label(form_frame, text="Nom*:").grid(row=0, column=0, sticky="w", pady=5)
        name_var = tk.StringVar(value=template.get('name', ''))
        name_entry = tk.Entry(form_frame, textvariable=name_var, width=40)
        name_entry.grid(row=0, column=1, sticky="w", pady=5)
        
        # Type de document
        tk.Label(form_frame, text="Type*:").grid(row=1, column=0, sticky="w", pady=5)
        types = ["Contrat", "Facture", "Proposition", "Rapport", "Autre"]
        current_type = template.get('type', 'contrat')
        if current_type not in types:
            types.append(current_type)
        type_var = tk.StringVar(value=current_type)
        type_menu = tk.OptionMenu(form_frame, type_var, *types)
        type_menu.grid(row=1, column=1, sticky="w", pady=5)
        
        # Description
        tk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky="w", pady=5)
        description_text = tk.Text(form_frame, width=40, height=3)
        description_text.grid(row=2, column=1, sticky="w", pady=5)
        description_text.insert("1.0", template.get('description', ''))
        
        # Variables
        tk.Label(form_frame, text="Variables:").grid(row=3, column=0, sticky="w", pady=5)
        variables_text = tk.Text(form_frame, width=40, height=5)
        variables_text.grid(row=3, column=1, sticky="w", pady=5)
        variables = template.get('variables', [])
        variables_text.insert("1.0", "\n".join(variables))
        tk.Label(form_frame, text="(Une variable par ligne)").grid(row=4, column=1, sticky="w")
        
        # Exemple de variables standards
        tk.Label(form_frame, text="Variables standards disponibles:").grid(row=5, column=0, columnspan=2, sticky="w", pady=5)
        standard_vars = "client_name, client_company, client_email, client_phone, client_address, company_name, date"
        tk.Label(form_frame, text=standard_vars, fg="gray").grid(row=6, column=0, columnspan=2, sticky="w")
        
        # Contenu du modèle avec éditeur enrichi
        tk.Label(form_frame, text="Contenu*:").grid(row=7, column=0, sticky="w", pady=5)
        content_text = RichTextEditor(form_frame, initial_content=template.get('content', ''), 
                                     variable_options=standard_vars.split(", "), 
                                     height=350, width=600)
        content_text.grid(row=7, column=1, sticky="w", pady=5)
        
        # Note explicative pour les variables
        tk.Label(form_frame, text="Utilisez {variable} pour insérer des variables dans le contenu").grid(row=8, column=0, columnspan=2, sticky="w", pady=5)
        
        # Note obligatoire
        tk.Label(form_frame, text="* Champs obligatoires", fg="gray").grid(row=9, column=0, columnspan=2, sticky="w", pady=10)
        
        # Boutons
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Fonction pour sauvegarder
        def save_template():
            # Récupérer les valeurs
            name = name_var.get().strip()
            template_type = type_var.get().strip()
            description = description_text.get("1.0", "end-1c").strip()
            
            # Récupérer les variables (une par ligne)
            variables_raw = variables_text.get("1.0", "end-1c").strip()
            variables = [v.strip() for v in variables_raw.split('\n') if v.strip()]
            
            # Récupérer le contenu
            content = content_text.get_content().strip()
            
            # Validation
            if not name:
                messagebox.showerror("Erreur", "Le nom est obligatoire", parent=dialog)
                return
            
            if not content:
                messagebox.showerror("Erreur", "Le contenu est obligatoire", parent=dialog)
                return
            
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
        
        # Fonction pour annuler
        def cancel():
            dialog.destroy()
        
        # Bouton Annuler
        cancel_btn = tk.Button(button_frame, text="Annuler", command=cancel, width=10)
        cancel_btn.pack(side=tk.RIGHT, padx=10)
        
        # Bouton Enregistrer
        save_btn = tk.Button(button_frame, text="Enregistrer", command=save_template, width=10)
        save_btn.pack(side=tk.RIGHT, padx=10)
        
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
        
        # Afficher la vue des documents
        self.view.parent.master.show_view("documents")
        
        # Accéder au contrôleur de documents via le contrôleur principal
        # et appeler la méthode new_document avec le template préselectionné
        try:
            # Cette approche peut être adaptée selon la structure de votre application
            document_view = self.view.parent.master.views["documents"]
            document_view.new_document(template_id)
            
            logger.info(f"Modèle {template_id} utilisé pour créer un nouveau document")
        except Exception as e:
            logger.error(f"Erreur lors de l'utilisation du modèle: {e}")
            messagebox.showerror("Erreur", f"Impossible d'utiliser ce modèle: {str(e)}")
    
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
            
        except Exception as e:
            logger.error(f"Erreur lors de l'importation du modèle: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'importation du modèle: {str(e)}")