#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue de gestion des modèles pour l'application Vynal Docs Automator
"""

import os
import logging
import customtkinter as ctk
from datetime import datetime
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
from utils.usage_tracker import UsageTracker

logger = logging.getLogger("VynalDocsAutomator.TemplateView")

class TemplateView:
    """
    Vue de gestion des modèles
    Permet de visualiser, créer et gérer des modèles de documents
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
        
        # Initialiser le gestionnaire d'utilisation
        self.usage_tracker = UsageTracker()
        
        # Cadre principal de la vue
        self.frame = ctk.CTkFrame(parent)
        
        # Liste pour stocker les templates sélectionnés
        self.selected_templates = []
        
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
        
        # Bouton Importer
        self.import_btn = ctk.CTkButton(
            self.toolbar,
            text="Importer",
            command=self.import_template
        )
        self.import_btn.pack(side=ctk.LEFT, padx=10)
        
        # Bouton Supprimer (initialement désactivé)
        self.delete_btn = ctk.CTkButton(
            self.toolbar,
            text="🗑️ Supprimer",
            fg_color="#7f8c8d",
            hover_color="#7f8c8d",
            state="disabled",
            command=self.delete_selected_templates
        )
        self.delete_btn.pack(side=ctk.LEFT, padx=10)
        
        # Recherche
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
        
        # Zone principale de contenu
        self.content_frame = ctk.CTkScrollableFrame(self.frame)
        self.content_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Message si aucun modèle
        self.no_templates_label = ctk.CTkLabel(
            self.content_frame,
            text="Aucun modèle disponible. Créez ou importez un modèle pour commencer.",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color="gray"
        )
        self.no_templates_label.pack(pady=20)
        
        # Grille de modèles
        self.templates_grid = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Configurer la grille pour avoir 3 colonnes
        for i in range(3):
            self.templates_grid.columnconfigure(i, weight=1)
    
    def update_view(self):
        """
        Met à jour la vue avec les données actuelles, triées du plus récent au plus ancien
        """
        # Trier les templates du plus récent au plus ancien
        try:
            self.model.templates.sort(
                key=lambda t: datetime.fromisoformat(t.get('created_at', datetime.min.isoformat())), 
                reverse=True
            )
        except Exception as e:
            logger.error(f"Erreur lors du tri des modèles : {e}")
        
        # Récupérer tous les modèles
        templates = self.model.templates
        
        # Réinitialiser la liste des templates sélectionnés
        self.selected_templates = []
        
        # Réinitialiser l'UI de sélection
        self.update_selection_ui()
        
        # Afficher ou masquer le message "Aucun modèle"
        if templates:
            self.no_templates_label.pack_forget()
            self.templates_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
            
            # Appliquer les filtres
            filtered_templates = self.apply_filters(templates)
            
            # Nettoyer la grille
            for widget in self.templates_grid.winfo_children():
                widget.destroy()
            
            # Remplir la grille avec les modèles filtrés
            if filtered_templates:
                row, col = 0, 0
                for template in filtered_templates:
                    self.create_template_card(template, row, col)
                    col += 1
                    if col >= 3:  # 3 cartes par ligne
                        col = 0
                        row += 1
            else:
                # Aucun modèle après filtrage
                ctk.CTkLabel(
                    self.templates_grid,
                    text="Aucun modèle ne correspond aux critères de recherche.",
                    font=ctk.CTkFont(size=12),
                    fg_color="transparent",
                    text_color="gray"
                ).grid(row=0, column=0, columnspan=3, pady=20)
        else:
            self.templates_grid.pack_forget()
            self.no_templates_label.pack(pady=20)
        
        logger.info("TemplateView mise à jour")
    
    def create_template_card(self, template, row, col):
        """
        Crée une carte pour afficher un modèle avec case à cocher
        
        Args:
            template: Données du modèle
            row: Ligne dans la grille
            col: Colonne dans la grille
        """
        # Cadre de la carte
        card = ctk.CTkFrame(self.templates_grid)
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
            command=lambda t=template, v=var: self.toggle_template_selection(t, v)
        )
        checkbox.pack(side=ctk.RIGHT, anchor="ne", padx=5, pady=5)
        
        # Icône selon le type
        template_type = template.get("type", "")
        icon = "📋"  # Par défaut
        
        if template_type == "contrat":
            icon = "📝"
        elif template_type == "facture":
            icon = "💰"
        elif template_type == "proposition":
            icon = "📊"
        elif template_type == "rapport":
            icon = "📈"
        
        # En-tête avec icône et type
        header = ctk.CTkFrame(card, fg_color=("gray90", "gray20"), corner_radius=6)
        header.pack(fill=ctk.X, padx=5, pady=5)
        
        ctk.CTkLabel(
            header,
            text=f"{icon} {template_type.capitalize() if template_type else 'Modèle'}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side=ctk.LEFT, padx=10, pady=5)
        
        # Date de création
        creation_date = template.get('created_at', '')
        if creation_date:
            try:
                date_obj = datetime.fromisoformat(creation_date)
                formatted_date = date_obj.strftime("%d/%m/%Y %H:%M")
                ctk.CTkLabel(
                    header,
                    text=formatted_date,
                    font=ctk.CTkFont(size=10),
                    text_color="gray"
                ).pack(side=ctk.RIGHT, padx=10, pady=5)
            except Exception:
                pass
        
        # Titre du modèle
        ctk.CTkLabel(
            card,
            text=template.get("name", "Sans nom"),
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=200
        ).pack(fill=ctk.X, padx=10, pady=5)
        
        # Description
        description = template.get("description", "")
        if description:
            ctk.CTkLabel(
                card,
                text=description,
                font=ctk.CTkFont(size=12),
                wraplength=200,
                text_color="gray",
                justify="left"
            ).pack(fill=ctk.X, padx=10, pady=5)
        
        # Variables disponibles
        variables = template.get("variables", [])
        if variables:
            variables_text = ", ".join(variables[:3])
            if len(variables) > 3:
                variables_text += f" et {len(variables) - 3} autres..."
            
            ctk.CTkLabel(
                card,
                text=f"Variables: {variables_text}",
                font=ctk.CTkFont(size=10),
                wraplength=200,
                text_color="gray"
            ).pack(fill=ctk.X, padx=10, pady=2)
        
        # Boutons d'action
        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.pack(fill=ctk.X, padx=10, pady=10)
        
        # Bouton Éditer
        ctk.CTkButton(
            actions_frame,
            text="Éditer",
            width=80,
            height=25,
            command=lambda tid=template.get("id"): self.on_edit_template(tid)
        ).pack(side=ctk.LEFT, padx=2)
        
        # Bouton Utiliser
        ctk.CTkButton(
            actions_frame,
            text="Utiliser",
            width=80,
            height=25,
            command=lambda tid=template.get("id"): self.use_template(tid)
        ).pack(side=ctk.RIGHT, padx=2)
    
    def toggle_template_selection(self, template, var):
        """
        Gère la sélection des modèles pour suppression avec feedback visuel
        """
        if var.get():
            if template not in self.selected_templates:
                self.selected_templates.append(template)
        else:
            if template in self.selected_templates:
                self.selected_templates.remove(template)
        
        # Mettre à jour l'interface en fonction du nombre de sélections
        self.update_selection_ui()
    
    def update_selection_ui(self):
        """
        Met à jour l'interface utilisateur selon l'état de sélection
        """
        count = len(self.selected_templates)
        
        if count > 0:
            # Activer et mettre à jour le bouton de suppression
            self.delete_btn.configure(
                text=f"🗑️ Supprimer ({count})",
                state="normal",
                fg_color="#e74c3c",
                hover_color="#c0392b"
            )
            
            # Afficher un badge flottant avec le nombre de modèles sélectionnés
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
    
    def delete_selected_templates(self):
        """
        Supprime les modèles sélectionnés avec confirmation visuelle moderne
        """
        if not self.selected_templates:
            return
        
        # Nombre de modèles à supprimer
        count = len(self.selected_templates)
        
        # Créer une fenêtre de confirmation moderne
        confirm_dialog = self.create_modern_confirm_dialog(count)
        
        # Centrer la fenêtre de confirmation
        confirm_dialog.update_idletasks()
        width = confirm_dialog.winfo_width()
        height = confirm_dialog.winfo_height()
        x = (confirm_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (confirm_dialog.winfo_screenheight() // 2) - (height // 2)
        confirm_dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Attendre la réponse de l'utilisateur (empêcher l'interaction avec la fenêtre principale)
        self.parent.wait_window(confirm_dialog)
        
        # Si l'utilisateur a confirmé la suppression
        if getattr(confirm_dialog, 'result', False):
            # Supprimer avec animation
            self.perform_deletion_with_animation()
    
    def create_modern_confirm_dialog(self, count):
        """
        Crée une fenêtre de confirmation de suppression moderne
        """
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Confirmer la suppression")
        dialog.attributes('-topmost', True)
        dialog.resizable(False, False)
        dialog.result = False
        
        # Contenu du dialogue
        content_frame = ctk.CTkFrame(dialog, corner_radius=0)
        content_frame.pack(fill="both", expand=True)
        
        # Icône d'alerte
        warning_label = ctk.CTkLabel(
            content_frame,
            text="⚠️",
            font=ctk.CTkFont(size=48)
        )
        warning_label.pack(pady=(20, 10))
        
        # Titre de l'alerte
        title_label = ctk.CTkLabel(
            content_frame,
            text="Confirmer la suppression",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Message de confirmation
        message = f"Vous êtes sur le point de supprimer {count} modèle{'s' if count > 1 else ''}."
        message_label = ctk.CTkLabel(
            content_frame,
            text=message,
            font=ctk.CTkFont(size=12),
            wraplength=300
        )
        message_label.pack(pady=(0, 5))
        
        # Avertissement
        warning_text = "Cette action est irréversible et les modèles supprimés ne pourront pas être récupérés."
        warning_message = ctk.CTkLabel(
            content_frame,
            text=warning_text,
            font=ctk.CTkFont(size=12),
            text_color="#e74c3c",
            wraplength=300
        )
        warning_message.pack(pady=(0, 20))
        
        # Boutons
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(pady=(0, 20), fill="x", padx=20)
        
        # Bouton Annuler
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            command=lambda: self.close_confirm_dialog(dialog, False)
        )
        cancel_btn.pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        # Bouton Supprimer
        delete_btn = ctk.CTkButton(
            buttons_frame,
            text=f"Supprimer {count} modèle{'s' if count > 1 else ''}",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=lambda: self.close_confirm_dialog(dialog, True)
        )
        delete_btn.pack(side="right", fill="x", expand=True)
        
        return dialog
    
    def close_confirm_dialog(self, dialog, result):
        """
        Ferme la fenêtre de dialogue avec le résultat
        """
        dialog.result = result
        dialog.destroy()
    
    def perform_deletion_with_animation(self):
        """
        Effectue la suppression avec animation
        """
        # Stocker les widgets des cartes à supprimer
        cards_to_delete = []
        
        for widget in self.templates_grid.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                # Vérifier si ce widget correspond à un modèle sélectionné
                for template in self.selected_templates:
                    # Recherche de la checkbox dans cette carte
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkCheckBox):
                            # Si la checkbox est cochée, c'est une carte à supprimer
                            if child.get():
                                cards_to_delete.append(widget)
                                break
        
        # Animation de suppression
        def animate_deletion(cards, index=0):
            if index < len(cards):
                card = cards[index]
                
                # Animation de disparition
                def fade_out(alpha=1.0):
                    if alpha > 0:
                        card.configure(fg_color=self.blend_colors("#ffffff", "#e74c3c", alpha))
                        self.parent.after(20, lambda: fade_out(alpha - 0.1))
                    else:
                        card.destroy()
                        animate_deletion(cards, index + 1)
                
                fade_out()
            else:
                # Une fois l'animation terminée, effectuer la suppression réelle
                self.delete_templates_from_model()
        
        # Commencer l'animation
        animate_deletion(cards_to_delete)
    
    def blend_colors(self, color1, color2, factor):
        """
        Mélange deux couleurs selon un facteur (0.0 à 1.0)
        """
        # Convertir les couleurs en RGB
        r1, g1, b1 = self.hex_to_rgb(color1)
        r2, g2, b2 = self.hex_to_rgb(color2)
        
        # Mélanger les couleurs
        r = int(r1 * factor + r2 * (1 - factor))
        g = int(g1 * factor + g2 * (1 - factor))
        b = int(b1 * factor + b2 * (1 - factor))
        
        # Convertir en hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def hex_to_rgb(self, hex_color):
        """
        Convertit une couleur hexadécimale en RGB
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def delete_templates_from_model(self):
        """
        Supprime les modèles du modèle de données
        """
        # Supprimer les modèles sélectionnés
        for template in self.selected_templates:
            self.model.templates = [t for t in self.model.templates if t.get("id") != template.get("id")]
        
        # Réinitialiser la liste des modèles sélectionnés
        self.selected_templates = []
        
        # Sauvegarder les changements
        self.model.save_templates()
        
        # Mettre à jour la vue avec un léger délai pour une meilleure UX
        self.parent.after(300, self.update_view)
        
        # Afficher une notification de succès
        self.show_success_toast("Suppression effectuée avec succès")
    
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
    
    def apply_filters(self, templates):
        """
        Applique les filtres aux modèles
        
        Args:
            templates: Liste des modèles à filtrer
            
        Returns:
            list: Modèles filtrés
        """
        filtered = templates
        
        # Filtre par recherche
        search_text = self.search_var.get().lower()
        if search_text:
            filtered = [t for t in filtered if 
                        search_text in t.get("name", "").lower() or 
                        search_text in t.get("description", "").lower() or
                        search_text in t.get("type", "").lower()]
        
        return filtered
    
    def filter_templates(self, *args):
        """
        Filtre les modèles selon les critères de recherche
        """
        self.update_view()
    
    def new_template(self):
        """
        Crée un nouveau modèle
        """
        # Trouver la fenêtre principale (root)
        root = self.parent.winfo_toplevel()
        
        # Si la fenêtre principale a une méthode create_template, l'utiliser
        if hasattr(root, "create_template"):
            root.create_template()
        else:
            # Sinon, utiliser notre propre formulaire
            form = TemplateFormView(self.parent, self.model, on_save_callback=self.update_view)
    
    def on_edit_template(self, template_id):
        """Gère l'édition d'un modèle"""
        # Vérifier si l'édition nécessite une inscription
        check = self.usage_tracker.needs_registration("template_editing")
        if check["needs_registration"]:
            # Trouver la fenêtre principale
            root = self.parent
            while root.master is not None:
                root = root.master
            
            # Afficher le dialogue d'inscription
            if hasattr(root, "_show_auth_dialog"):
                root._show_auth_dialog()
            return
        
        # Si l'utilisateur est inscrit ou n'a pas atteint la limite
        self._show_template_editor(template_id)
    
    def _show_template_editor(self, template_id):
        """
        Édite un modèle existant
        
        Args:
            template_id: ID du modèle à éditer
        """
        try:
            # Trouver la fenêtre principale (root)
            root = self.parent
            while root.master is not None:
                root = root.master
            
            # Si la fenêtre principale a une méthode edit_template, l'utiliser
            if hasattr(root, "edit_template"):
                root.edit_template(template_id=template_id)
            else:
                # Sinon, utiliser notre propre formulaire
                form = TemplateFormView(self.parent, self.model, on_save_callback=self.update_view)
                form.load_template(template_id)
        except Exception as e:
            logger.error(f"Erreur lors de l'édition du modèle: {e}")
            self.show_error(self.parent, "Erreur lors de l'édition du modèle")
    
    def use_template(self, template_id):
        """
        Utilise un modèle pour créer un nouveau document
        
        Args:
            template_id: ID du modèle à utiliser
        """
        try:
            # Trouver la fenêtre principale (root)
            root = self.parent
            while root.master is not None:
                root = root.master
            
            # Si la fenêtre principale a une méthode new_document, l'utiliser
            if hasattr(root, "new_document"):
                root.new_document(template_id=template_id)
            else:
                self.show_error(self.parent, "Impossible de créer un nouveau document")
        except Exception as e:
            logger.error(f"Erreur lors de l'utilisation du modèle: {e}")
            self.show_error(self.parent, "Erreur lors de la création du document")
    
    def import_template(self):
        """
        Importe un modèle depuis un fichier externe
        """
        # Trouver la fenêtre principale (root)
        root = self.parent.winfo_toplevel()
        
        # Si la fenêtre principale a une méthode import_template, l'utiliser
        if hasattr(root, "import_template"):
            root.import_template()
        else:
            # Sinon, utiliser notre propre boîte de dialogue
            self.show_import_dialog()

    def show_import_dialog(self):
        """
        Affiche la boîte de dialogue d'importation de modèle
        """
        # Créer une fenêtre de dialogue
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Importer un modèle")
        dialog.geometry("500x300")
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
            text="📄 Importer un modèle",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Message d'instructions
        message_label = ctk.CTkLabel(
            main_frame,
            text="Sélectionnez un fichier de modèle à importer.\nFormats supportés : .docx, .txt",
            wraplength=360
        )
        message_label.pack(pady=10)
        
        # Variable pour stocker le chemin du fichier
        file_path_var = ctk.StringVar()
        
        # Frame pour le chemin du fichier
        file_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        file_frame.pack(fill=ctk.X, pady=10)
        
        # Entry pour afficher le chemin du fichier
        file_entry = ctk.CTkEntry(file_frame, textvariable=file_path_var, width=300)
        file_entry.pack(side=ctk.LEFT, padx=(0, 10))
        
        def browse_file():
            file_types = [
                ('Fichiers Word', '*.docx'),
                ('Fichiers texte', '*.txt'),
                ('Tous les fichiers', '*.*')
            ]
            file_path = filedialog.askopenfilename(
                parent=dialog,
                title="Sélectionner un fichier",
                filetypes=file_types
            )
            if file_path:
                file_path_var.set(file_path)
        
        # Bouton Parcourir
        browse_button = ctk.CTkButton(
            file_frame,
            text="Parcourir",
            width=100,
            command=browse_file
        )
        browse_button.pack(side=ctk.LEFT)
        
        def import_file():
            file_path = file_path_var.get()
            if not file_path:
                self.show_error("Veuillez sélectionner un fichier")
                return
            
            if not os.path.exists(file_path):
                self.show_error("Le fichier sélectionné n'existe pas")
                return
            
            try:
                # Importer le fichier selon son extension
                ext = os.path.splitext(file_path)[1].lower()
                
                if ext == '.docx':
                    success = self._import_docx(file_path)
                elif ext == '.txt':
                    success = self._import_text(file_path)
                else:
                    self.show_error("Format de fichier non supporté")
                    return
                
                if success:
                    self.show_success_toast("Modèle importé avec succès")
                    dialog.destroy()
                    self.update_view()
                else:
                    self.show_error("Erreur lors de l'importation du modèle")
            
            except Exception as e:
                self.show_error(f"Erreur lors de l'importation : {str(e)}")
        
        # Frame pour les boutons
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, pady=20)
        
        # Bouton Annuler
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            width=100,
            command=dialog.destroy
        )
        cancel_button.pack(side=ctk.RIGHT, padx=10)
        
        # Bouton Importer
        import_button = ctk.CTkButton(
            buttons_frame,
            text="Importer",
            width=100,
            command=import_file
        )
        import_button.pack(side=ctk.RIGHT, padx=10)

    def _import_docx(self, file_path):
        """
        Importe un fichier Word comme modèle
        
        Args:
            file_path: Chemin du fichier à importer
            
        Returns:
            bool: True si l'importation a réussi, False sinon
        """
        try:
            import docx
            
            # Ouvrir le document Word
            doc = docx.Document(file_path)
            
            # Extraire le texte
            content = "\n\n".join([para.text for para in doc.paragraphs if para.text])
            
            # Extraire le nom du fichier sans extension pour le titre
            file_name = os.path.basename(file_path)
            name = os.path.splitext(file_name)[0]
            
            # Créer les données du modèle
            template_data = {
                "name": name,
                "type": "autre",
                "description": f"Modèle importé depuis {file_name}",
                "content": content,
                "variables": [],
                "created_at": datetime.now().isoformat()
            }
            
            # Ouvrir le formulaire avec les données pré-remplies
            form = TemplateFormView(self.parent, self.model, on_save_callback=self.update_view)
            form.template_data = template_data
            form._create_form_view()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import du fichier Word: {e}")
            return False
    
    def _import_text(self, file_path):
        """
        Importe un fichier texte comme modèle
        
        Args:
            file_path: Chemin du fichier à importer
            
        Returns:
            bool: True si l'importation a réussi, False sinon
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
                return False
            
            # Extraire le nom du fichier sans extension pour le titre
            file_name = os.path.basename(file_path)
            name = os.path.splitext(file_name)[0]
            
            # Créer les données du modèle
            template_data = {
                "name": name,
                "type": "autre",
                "description": f"Modèle importé depuis {file_name}",
                "content": content,
                "variables": [],
                "created_at": datetime.now().isoformat()
            }
            
            # Ouvrir le formulaire avec les données pré-remplies
            form = TemplateFormView(self.parent, self.model, on_save_callback=self.update_view)
            form.template_data = template_data
            form._create_form_view()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import du fichier texte: {e}")
            return False

class TemplateFormView:
    """
    Vue pour l'ajout et l'édition de modèles
    """
    
    def __init__(self, parent, app_model, on_save_callback=None):
        """
        Initialise la vue de formulaire de modèle
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
            on_save_callback: Fonction à appeler après la sauvegarde
        """
        self.parent = parent
        self.model = app_model
        self.on_save_callback = on_save_callback
        self.template_id = None
        self.template_data = {}
        
        # Initialiser la vue du formulaire
        self._create_form_view()
    
    def _create_form_view(self):
        """
        Crée la vue du formulaire
        """
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Nouveau modèle")
        self.dialog.geometry("700x600")
        self.dialog.lift()
        self.dialog.focus_force()
        self.dialog.grab_set()
        
        # Centrer la fenêtre
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Cadre principal
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Informations générales
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill=ctk.X, padx=10, pady=10)
        
        # Nom du modèle
        name_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_frame.pack(fill=ctk.X, padx=5, pady=5)
        
        ctk.CTkLabel(name_frame, text="Nom *", anchor="w", width=100).pack(side=ctk.LEFT, padx=5)
        self.name_var = ctk.StringVar(value=self.template_data.get("name", ""))
        self.name_entry = ctk.CTkEntry(name_frame, textvariable=self.name_var, width=400)
        self.name_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5)
        
        # Type de modèle
        type_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        type_frame.pack(fill=ctk.X, padx=5, pady=5)
        
        ctk.CTkLabel(type_frame, text="Type *", anchor="w", width=100).pack(side=ctk.LEFT, padx=5)
        self.type_var = ctk.StringVar(value=self.template_data.get("type", ""))
        self.type_combo = ctk.CTkComboBox(
            type_frame,
            values=["contrat", "facture", "proposition", "rapport", "autre"],
            variable=self.type_var,
            width=200
        )
        self.type_combo.pack(side=ctk.LEFT, padx=5)
        
        # Description
        desc_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        desc_frame.pack(fill=ctk.X, padx=5, pady=5)
        
        ctk.CTkLabel(desc_frame, text="Description", anchor="w", width=100).pack(side=ctk.LEFT, padx=5, anchor="n")
        self.desc_text = ctk.CTkTextbox(desc_frame, height=100, width=400)
        self.desc_text.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True, padx=5, pady=5)
        
        # Variables du modèle
        variables_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        variables_frame.pack(fill=ctk.X, padx=5, pady=5)
        
        ctk.CTkLabel(variables_frame, text="Variables", anchor="w", width=100).pack(side=ctk.LEFT, padx=5)
        self.variables_entry = ctk.CTkEntry(variables_frame, width=400, placeholder_text="Ex: nom, date, montant (séparés par des virgules)")
        self.variables_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5)
        
        # Contenu du modèle
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(content_frame, text="Contenu du modèle", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=10, pady=5, anchor="w")
        
        # Zone d'édition du contenu
        self.content_text = ctk.CTkTextbox(content_frame, wrap="word")
        self.content_text.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, padx=20, pady=10)
        
        # Bouton Annuler
        ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            command=self.dialog.destroy,
            width=100
        ).pack(side=ctk.RIGHT, padx=10)
        
        # Bouton Enregistrer
        ctk.CTkButton(
            buttons_frame,
            text="Enregistrer",
            command=self._save_template,
            width=100
        ).pack(side=ctk.RIGHT, padx=10)
    
    def _save_template(self):
        """
        Enregistre le modèle
        """
        # Récupérer les données du formulaire
        name = self.name_var.get().strip()
        template_type = self.type_var.get().strip().lower()
        description = self.desc_text.get("1.0", "end-1c").strip()
        content = self.content_text.get("1.0", "end-1c")
        variables = [v.strip() for v in self.variables_entry.get().split(",") if v.strip()]
        
        # Validation
        if not name:
            self._show_error("Le nom est obligatoire")
            return
        
        if not template_type:
            self._show_error("Le type de modèle est obligatoire")
            return
        
        if not content:
            self._show_error("Le contenu du modèle est obligatoire")
            return
        
        # Préparer les données du modèle
        template_data = {
            "name": name,
            "type": template_type,
            "description": description,
            "content": content,
            "variables": variables,
            "created_at": datetime.now().isoformat()
        }
        
        # Si c'est une mise à jour
        if self.template_id:
            template_data["id"] = self.template_id
            success = self.model.update_template(self.template_id, template_data)
            success_message = "Modèle mis à jour avec succès"
        else:
            # Nouveau modèle
            success = self.model.add_template(template_data)
            success_message = "Nouveau modèle créé avec succès"
        
        if success:
            # Afficher le toast de succès
            self.show_success_toast(success_message)
            
            # Fermer la boîte de dialogue après un court délai
            self.dialog.after(1000, self.dialog.destroy)
            
            # Appeler le callback si défini
            if self.on_save_callback:
                self.on_save_callback()
        else:
            self._show_error("Erreur lors de l'enregistrement du modèle")
    
    def _show_error(self, message):
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
    
    def load_template(self, template_id):
        """
        Charge un modèle existant dans le formulaire
        
        Args:
            template_id: ID du modèle à charger
        """
        template = next((t for t in self.model.templates if t.get("id") == template_id), None)
        if not template:
            self._show_error(f"Modèle introuvable (ID: {template_id})")
            return False
        
        # Mettre à jour les données et l'interface
        self.template_id = template_id
        self.template_data = template
        
        # Mettre à jour le titre de la fenêtre
        self.dialog.title(f"Modifier le modèle - {template.get('name', '')}")
        
        # Mettre à jour les champs du formulaire
        self.name_var.set(template.get("name", ""))
        self.type_var.set(template.get("type", ""))
        
        # Mettre à jour la description
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", template.get("description", ""))
        
        # Mettre à jour les variables
        variables = template.get("variables", [])
        self.variables_entry.delete(0, "end")
        self.variables_entry.insert(0, ", ".join(variables))
        
        # Mettre à jour le contenu
        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", template.get("content", ""))
        
        return True
    
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