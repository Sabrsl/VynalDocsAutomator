"""
Vue de gestion des modèles pour l'application Vynal Docs Automator
"""

import logging
import customtkinter as ctk
from tkinter import messagebox
from utils.rich_text_editor import RichTextEditor

logger = logging.getLogger("VynalDocsAutomator.TemplateView")

class TemplateView:
    """
    Vue de gestion des modèles
    Permet de visualiser, ajouter, modifier et supprimer des modèles
    """
    
    def __init__(self, parent, app_model):
        """
        Initialise la vue de gestion des modèles
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        
        # Cadre principal de la vue
        self.frame = ctk.CTkFrame(parent)
        
        # Variables pour le formulaire
        self.current_template_id = None
        self.template_data = {}
        
        # Créer les composants de l'interface
        self.create_widgets()
        
        logger.info("TemplateView initialisée")
    
    def create_widgets(self):
        """
        Crée les widgets de la vue
        """
        # Barre d'outils
        self.toolbar = ctk.CTkFrame(self.frame)
        self.toolbar.pack(fill=ctk.X, pady=10)
        
        # Bouton Nouveau modèle
        self.new_template_btn = ctk.CTkButton(
            self.toolbar,
            text="+ Nouveau modèle",
            command=self.new_template
        )
        self.new_template_btn.pack(side=ctk.LEFT, padx=10)
        
        # Zone de recherche
        self.search_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.search_frame.pack(side=ctk.RIGHT, padx=10)
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.filter_templates())
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Rechercher un modèle...",
            width=200,
            textvariable=self.search_var
        )
        self.search_entry.pack(side=ctk.LEFT)
        
        # Cadre pour la liste des modèles
        self.list_frame = ctk.CTkFrame(self.frame)
        self.list_frame.pack(fill=ctk.BOTH, expand=True, pady=10)
        
        # Message affiché s'il n'y a aucun modèle
        self.no_templates_label = ctk.CTkLabel(
            self.list_frame,
            text="Aucun modèle disponible. Ajoutez des modèles pour commencer.",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color="gray"
        )
        self.no_templates_label.pack(pady=20)
    
    def new_template(self):
        """
        Affiche le formulaire pour créer un nouveau modèle
        """
        try:
            form = TemplateFormView(self.frame, self.model, update_view_callback=self.update_view)
            logger.info("Formulaire de création de modèle affiché")
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du formulaire: {e}")
            messagebox.showerror("Erreur", f"Impossible d'afficher le formulaire: {str(e)}")
    
    def update_view(self):
        """
        Met à jour la vue avec les données actuelles
        """
        try:
            # Récupérer tous les modèles
            templates = self.model.get_all_templates()
            
            # Filtrer les modèles si nécessaire
            search_text = self.search_var.get().lower()
            if search_text:
                templates = [
                    template for template in templates
                    if search_text in template.get("name", "").lower()
                ]
            
            # Mettre à jour l'affichage
            self._update_templates_list(templates)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la vue: {e}")
            messagebox.showerror("Erreur", f"Impossible de mettre à jour la vue: {str(e)}")
    
    def _update_templates_list(self, templates):
        """
        Met à jour la liste des modèles
        
        Args:
            templates: Liste des modèles à afficher
        """
        # Nettoyer la liste existante
        for widget in self.list_frame.winfo_children():
            if widget != self.no_templates_label:
                widget.destroy()
        
        if templates:
            self.no_templates_label.pack_forget()
            
            # Créer un cadre pour chaque modèle
            for template in templates:
                template_frame = ctk.CTkFrame(self.list_frame)
                template_frame.pack(fill=ctk.X, padx=10, pady=5)
                
                # Nom du modèle
                name_label = ctk.CTkLabel(
                    template_frame,
                    text=template.get("name", ""),
                    font=ctk.CTkFont(weight="bold")
                )
                name_label.pack(side=ctk.LEFT, padx=10, pady=5)
                
                # Boutons d'action
                action_frame = ctk.CTkFrame(template_frame, fg_color="transparent")
                action_frame.pack(side=ctk.RIGHT, padx=10)
                
                # Bouton Utiliser
                use_btn = ctk.CTkButton(
                    action_frame,
                    text="Utiliser",
                    width=80,
                    command=lambda t=template: self.use_template(t)
                )
                use_btn.pack(side=ctk.LEFT, padx=5)
                
                # Bouton Éditer
                edit_btn = ctk.CTkButton(
                    action_frame,
                    text="Éditer",
                    width=80,
                    command=lambda t=template: self.edit_template(t)
                )
                edit_btn.pack(side=ctk.LEFT, padx=5)
                
                # Bouton Supprimer
                delete_btn = ctk.CTkButton(
                    action_frame,
                    text="Supprimer",
                    width=80,
                    fg_color="red",
                    hover_color="#C0392B",
                    command=lambda t=template: self.delete_template(t)
                )
                delete_btn.pack(side=ctk.LEFT, padx=5)
        else:
            self.no_templates_label.pack(pady=20)
    
    def filter_templates(self):
        """
        Filtre les modèles selon le texte de recherche
        """
        self.update_view()
    
    def use_template(self, template):
        """
        Utilise un modèle pour créer un nouveau document
        
        Args:
            template: Modèle à utiliser
        """
        try:
            self.model.create_document_from_template(template)
            messagebox.showinfo("Succès", "Document créé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la création du document: {e}")
            messagebox.showerror("Erreur", f"Impossible de créer le document: {str(e)}")
    
    def edit_template(self, template):
        """
        Édite un modèle existant
        
        Args:
            template: Modèle à éditer
        """
        try:
            form = TemplateFormView(self.frame, self.model, template, self.update_view)
            logger.info(f"Formulaire d'édition affiché pour le modèle {template.get('name')}")
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du formulaire: {e}")
            messagebox.showerror("Erreur", f"Impossible d'afficher le formulaire: {str(e)}")
    
    def delete_template(self, template):
        """
        Supprime un modèle
        
        Args:
            template: Modèle à supprimer
        """
        if messagebox.askyesno("Confirmer", f"Voulez-vous vraiment supprimer le modèle {template.get('name')} ?"):
            try:
                self.model.delete_template(template["id"])
                self.update_view()
                messagebox.showinfo("Succès", "Modèle supprimé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du modèle: {e}")
                messagebox.showerror("Erreur", f"Impossible de supprimer le modèle: {str(e)}")
    
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


class TemplateFormView:
    """
    Vue du formulaire de modèle
    Permet de créer ou modifier un modèle
    """
    
    def __init__(self, parent, app_model, template_data=None, update_view_callback=None):
        """
        Initialise le formulaire de modèle
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
            template_data: Données du modèle à modifier (None pour un nouveau modèle)
            update_view_callback: Fonction de rappel pour mettre à jour la vue principale
        """
        self.parent = parent
        self.model = app_model
        self.template_data = template_data
        self.update_view_callback = update_view_callback
        
        self._create_form_view()
    
    def _create_form_view(self):
        """
        Crée la vue du formulaire
        """
        # Créer une nouvelle fenêtre modale
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Modifier le modèle" if self.template_data else "Nouveau modèle")
        self.dialog.geometry("700x800")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Centrer la fenêtre
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - self.dialog.winfo_width()) // 2
        y = (self.dialog.winfo_screenheight() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Frame principal avec padding
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre
        title_label = ctk.CTkLabel(
            main_frame,
            text="📝 " + ("Modifier le modèle" if self.template_data else "Nouveau modèle"),
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Champ Nom
        name_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        name_frame.pack(fill=ctk.X, pady=(0, 10))
        
        name_label = ctk.CTkLabel(name_frame, text="Nom*:", anchor="w")
        name_label.pack(side=ctk.LEFT, padx=5)
        
        self.name_var = ctk.StringVar(value=self.template_data.get("name", "") if self.template_data else "")
        self.name_entry = ctk.CTkEntry(name_frame, textvariable=self.name_var, width=400)
        self.name_entry.pack(side=ctk.LEFT, padx=5)
        
        # Séparateur
        separator = ctk.CTkFrame(main_frame, height=2, fg_color="gray70")
        separator.pack(fill=ctk.X, pady=10)
        
        # Zone de contenu avec l'éditeur de texte enrichi
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill=ctk.BOTH, expand=True, pady=10)
        
        content_label = ctk.CTkLabel(content_frame, text="Contenu*:", anchor="w")
        content_label.pack(anchor="w", padx=5, pady=(0, 5))
        
        # Utiliser RichTextEditor s'il est disponible
        try:
            self.content_editor = RichTextEditor(content_frame)
            self.content_editor.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
            
            # Variables standard disponibles
            standard_vars = [
                "{{client.name}}", "{{client.company}}", "{{client.email}}",
                "{{client.phone}}", "{{client.address}}", "{{client.city}}",
                "{{date}}", "{{time}}", "{{document.title}}"
            ]
            
            # Ajouter les variables au menu de l'éditeur
            self.content_editor.add_variables(standard_vars)
            
            # Charger le contenu si on modifie un modèle existant
            if self.template_data:
                self.content_editor.set_content(self.template_data.get("content", ""))
            
        except Exception as e:
            logger.warning(f"Impossible d'utiliser RichTextEditor: {e}")
            # Fallback sur un CTkTextbox standard
            self.content_editor = ctk.CTkTextbox(content_frame)
            self.content_editor.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
            
            if self.template_data:
                self.content_editor.insert("1.0", self.template_data.get("content", ""))
        
        # Séparateur avant les boutons
        separator = ctk.CTkFrame(main_frame, height=2, fg_color="gray70")
        separator.pack(fill=ctk.X, pady=10)
        
        # Frame pour les boutons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, pady=(10, 0))
        
        # Bouton Annuler
        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text="Annuler",
            width=120,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.dialog.destroy
        )
        self.cancel_btn.pack(side=ctk.LEFT, padx=10)
        
        # Bouton Enregistrer
        self.save_btn = ctk.CTkButton(
            button_frame,
            text="Enregistrer",
            width=120,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=self._save_template
        )
        self.save_btn.pack(side=ctk.RIGHT, padx=10)
        
        # Focus sur le champ nom
        self.name_entry.focus()
    
    def _save_template(self):
        """
        Sauvegarde le modèle
        """
        # Valider les champs requis
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Erreur", "Le nom est requis")
            self.name_entry.focus()
            return
        
        # Récupérer le contenu selon le type d'éditeur
        if isinstance(self.content_editor, RichTextEditor):
            content = self.content_editor.get_content()
        else:
            content = self.content_editor.get("1.0", "end-1c")
        
        if not content:
            messagebox.showerror("Erreur", "Le contenu est requis")
            self.content_editor.focus()
            return
        
        try:
            template_data = {
                "name": name,
                "content": content
            }
            
            if self.template_data:
                # Mise à jour
                success = self.model.update_template(self.template_data["id"], template_data)
                if success:
                    messagebox.showinfo("Succès", "Modèle mis à jour avec succès")
                    self.dialog.destroy()
                    if self.update_view_callback:
                        self.update_view_callback()
                else:
                    messagebox.showerror("Erreur", "Impossible de mettre à jour le modèle")
            else:
                # Création
                success = self.model.add_template(template_data)
                if success:
                    messagebox.showinfo("Succès", "Modèle créé avec succès")
                    self.dialog.destroy()
                    if self.update_view_callback:
                        self.update_view_callback()
                else:
                    messagebox.showerror("Erreur", "Impossible de créer le modèle")
                    
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du modèle: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}") 