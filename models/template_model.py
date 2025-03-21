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
from functools import lru_cache
from utils.rich_text_editor import RichTextEditor
from utils.cache_manager import CacheManager
from typing import Dict, List, Optional

logger = logging.getLogger("VynalDocsAutomator.TemplateController")

class TemplateController:
    """
    Contrôleur de gestion des modèles
    Gère la logique métier liée aux modèles de documents
    """
    
    def __init__(self, view: TemplateView, model: AppModel):
        """
        Initialise le contrôleur des modèles
        
        Args:
            view: Vue de gestion des modèles
            model: Modèle de l'application
        """
        self.view = view
        self.model = model
        
        # Initialisation du cache
        self.cache_manager = CacheManager()
        
        # Cache pour les templates fréquemment utilisés
        self._template_cache = {}
        self._template_cache_size = 50
        self._template_access_patterns = {}
        
        # Connecter les événements de la vue aux méthodes du contrôleur
        self.connect_events()
        
        # Chargement initial des templates avec chargement paresseux
        self._templates = None
        self._template_folders = None
        
        logger.info("TemplateController initialisé")
    
    @property
    def templates(self):
        if self._templates is None:
            self._templates = self._load_templates()
        return self._templates
    
    @property
    def template_folders(self):
        if self._template_folders is None:
            self._template_folders = self._load_template_folders()
        return self._template_folders
    
    @lru_cache(maxsize=50)
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Récupère un template avec mise en cache LRU."""
        return self.templates.get(template_id)
    
    @lru_cache(maxsize=10)
    def get_templates_by_folder(self, folder: str) -> List[Dict]:
        """Récupère les templates d'un dossier avec mise en cache LRU."""
        return [t.copy() for t in self.templates.values() if t.get('folder') == folder]
    
    def _load_templates(self) -> Dict:
        """Charge les templates depuis le modèle avec mise en cache."""
        templates = self.model.get_templates()
        self.cache_manager.set("templates", "all", templates)
        return templates
    
    def _load_template_folders(self) -> Dict:
        """Charge les dossiers de templates avec mise en cache."""
        return self.model.template_folders.copy()
    
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
    
    def load_templates(self):
        """Charge les templates avec mise en cache."""
        # Vérifier le cache
        cached_templates = self.cache_manager.get("templates", "all")
        if cached_templates is not None:
            self.view.display_templates(cached_templates)
            return
            
        # Si non trouvé dans le cache, charger depuis le modèle
        templates = self.model.get_templates()
        
        # Mettre en cache
        self.cache_manager.set("templates", "all", templates)
        
        # Afficher dans la vue
        self.view.display_templates(templates)
    
    def create_template(self, template_data: Dict) -> bool:
        """
        Crée un nouveau template avec mise en cache.
        
        Args:
            template_data: Données du template
            
        Returns:
            bool: True si la création est réussie, False sinon
        """
        template_id = self.model.add_template(template_data)
        if template_id:
            # Invalider les caches
            self.cache_manager.invalidate("templates", "all")
            self.get_template.cache_clear()
            self.get_templates_by_folder.cache_clear()
            
            # Recharger les templates
            self._templates = None
            self.load_templates()
            return True
        return False

    def edit_template(self, template_id: str, template_data: Dict) -> bool:
        """
        Modifie un template existant avec mise en cache.
        
        Args:
            template_id: ID du template à modifier
            template_data: Nouvelles données du template
            
        Returns:
            bool: True si la modification est réussie, False sinon
        """
        if self.model.update_template(template_id, template_data):
            # Invalider les caches
            self.cache_manager.invalidate("templates", "all")
            self.cache_manager.invalidate("templates", template_id)
            self.get_template.cache_clear()
            self.get_templates_by_folder.cache_clear()
            
            # Recharger les templates
            self._templates = None
            self.load_templates()
            return True
        return False

    def delete_template(self, template_id: str) -> bool:
        """
        Supprime un template avec invalidation du cache.
        
        Args:
            template_id: ID du template à supprimer
            
        Returns:
            bool: True si la suppression est réussie, False sinon
        """
        if self.model.delete_template(template_id):
            # Invalider les caches
            self.cache_manager.invalidate("templates", "all")
            self.cache_manager.invalidate("templates", template_id)
            self.get_template.cache_clear()
            self.get_templates_by_folder.cache_clear()
            
            # Recharger les templates
            self._templates = None
            self.load_templates()
            return True
        return False

    def filter_templates(self, criteria: Dict) -> List[Dict]:
        """
        Filtre les templates selon des critères avec mise en cache.
        
        Args:
            criteria: Critères de filtrage
            
        Returns:
            List[Dict]: Liste des templates filtrés
        """
        # Créer une clé de cache unique pour les critères
        cache_key = f"filter_{hash(str(criteria))}"
        
        # Vérifier le cache
        cached_filtered = self.cache_manager.get("templates", cache_key)
        if cached_filtered is not None:
            return cached_filtered
            
        # Si non trouvé dans le cache, filtrer les templates
        filtered_templates = [
            t for t in self.templates.values()
            if all(t.get(k) == v for k, v in criteria.items())
        ]
        
        # Mettre en cache
        self.cache_manager.set("templates", cache_key, filtered_templates)
        
        return filtered_templates

    def cleanup(self):
        """Nettoie les ressources du contrôleur."""
        # Nettoyer les caches
        self.cache_manager.cleanup()
        self.get_template.cache_clear()
        self.get_templates_by_folder.cache_clear()

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