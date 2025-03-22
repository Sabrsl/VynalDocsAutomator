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
from utils.rich_text_editor import RichTextEditor
from utils.date_helpers import parse_iso_datetime

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
        
        # Variable pour stocker le dossier sélectionné
        self.selected_folder = None
        
        # Initialiser le contrôleur
        from controllers.template_controller import TemplateController
        self.controller = TemplateController(app_model, self)
        
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
        
        # Bouton Retour (initialement caché)
        self.back_btn = ctk.CTkButton(
            self.toolbar,
            text="Retour",
            command=self.show_folders_view
        )
        
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
        
        # Grille de modèles
        self.templates_grid = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Grille de dossiers
        self.folders_grid = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Configurer les grilles pour avoir 3 colonnes
        for grid in [self.templates_grid, self.folders_grid]:
            for i in range(3):
                grid.columnconfigure(i, weight=1)
        
        # Afficher la vue des dossiers par défaut
        self.show_folders_view()
    
    def show_folders_view(self):
        """Affiche la vue des dossiers"""
        # Cacher le bouton retour
        self.back_btn.pack_forget()
        
        # Cacher le titre du dossier s'il existe
        if hasattr(self, 'folder_title_label'):
            self.folder_title_label.pack_forget()
        
        # Réinitialiser le dossier sélectionné et les templates
        self.selected_folder = None
        self.selected_templates = []
        self.update_selection_ui()
        
        # Nettoyer la vue
        self.templates_grid.pack_forget()
        self.no_templates_label.pack_forget()
        
        # Afficher la grille des dossiers
        self.folders_grid.pack(fill=ctk.BOTH, expand=True, padx=0, pady=0)
        
        # Nettoyer la grille
        for widget in self.folders_grid.winfo_children():
            widget.destroy()
        
        # Créer les cards des dossiers
        row, col = 0, 0
        for folder_id, folder_name in self.model.template_folders.items():
            self.create_folder_card(folder_id, folder_name, row, col)
            col += 1
            if col >= 3:  # 3 cards par ligne
                col = 0
                row += 1
    
    def create_folder_card(self, folder_id, folder_name, row, col):
        """Crée une card pour un dossier"""
        # Créer le cadre principal avec une taille fixe
        card = ctk.CTkFrame(
            self.folders_grid,
            width=200,  # Largeur fixe
            height=200,  # Hauteur fixe
            corner_radius=10,
            border_width=0,
            fg_color=("gray95", "gray15")  # Couleur de fond adaptative
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)  # Empêcher le redimensionnement automatique
        
        # Créer un cadre pour le contenu
        content_frame = ctk.CTkFrame(
            card,
            fg_color="transparent",
            width=180,  # Largeur fixe
            height=180  # Hauteur fixe
        )
        content_frame.pack(expand=True, fill="both", padx=10, pady=10)
        content_frame.pack_propagate(False)  # Empêcher le redimensionnement automatique
        
        # Icône du dossier selon le type
        folder_icons = {
            "juridique": "⚖️",      # Balance de la justice
            "contrats": "📝",       # Document avec stylo
            "commercial": "📈",      # Graphique montant
            "administratif": "📎",   # Trombone (administratif)
            "ressources_humaines": "👥", # Silhouettes de personnes
            "fiscal": "💰",         # Sac d'argent
            "correspondance": "✉️",  # Enveloppe
            "bancaire": "🏦",       # Bâtiment de banque
            "corporate": "🏢",      # Bâtiment d'entreprise
            "immobilier": "🏠",     # Maison
            "autre": "📁"           # Dossier standard
        }
        
        # Obtenir l'icône correspondante au dossier
        folder_icon = folder_icons.get(folder_id, "📁")  # Utilise l'icône de dossier par défaut si non trouvé
        
        # Icône du dossier
        icon_label = ctk.CTkLabel(
            content_frame,
            text=folder_icon,
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=(20, 10))
        
        # Nom du dossier
        name_label = ctk.CTkLabel(
            content_frame,
            text=folder_name,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        name_label.pack(pady=(0, 10))
        
        # Nombre de modèles
        count = len(self.model.get_templates_by_folder(folder_id))
        count_label = ctk.CTkLabel(
            content_frame,
            text=f"{count} modèle{'s' if count > 1 else ''}",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        count_label.pack(pady=(0, 20))
        
        # Gestionnaires d'événements
        def handle_click(event, fid=folder_id):
            self.show_templates_in_folder(fid)
        
        def handle_enter(event):
            card.configure(border_width=2, border_color=("gray70", "gray30"))
            event.widget.configure(cursor="hand2")
        
        def handle_leave(event):
            card.configure(border_width=0)
            event.widget.configure(cursor="")
        
        # Lier les événements au cadre et à tous les widgets à l'intérieur
        for widget in [card, content_frame, icon_label, name_label, count_label]:
            widget.bind("<Button-1>", handle_click)
            widget.bind("<Enter>", handle_enter)
            widget.bind("<Leave>", handle_leave)
    
    def show_templates_in_folder(self, folder_name):
        """Affiche les modèles d'un dossier spécifique"""
        self.selected_folder = folder_name
        
        # Afficher le bouton retour
        self.back_btn.pack(side=ctk.LEFT, padx=10, before=self.new_template_btn)
        
        # Cacher la grille des dossiers
        self.folders_grid.pack_forget()
        
        # Ajouter le titre du dossier
        folder_name = self.model.template_folders.get(folder_name, "Autres")
        if not hasattr(self, 'folder_title_label'):
            self.folder_title_label = ctk.CTkLabel(
                self.toolbar,
                text=f"📁 {folder_name}",  # Ajout d'une icône pour plus de clarté
                font=ctk.CTkFont(size=16, weight="bold")
            )
        else:
            self.folder_title_label.configure(text=f"📁 {folder_name}")
        self.folder_title_label.pack(side=ctk.LEFT, padx=20, after=self.back_btn)
        
        # Mettre à jour la vue avec les modèles du dossier
        self.update_view()
    
    def update_view(self):
        """Met à jour la vue avec les données actuelles"""
        # Si un dossier est sélectionné, afficher ses modèles
        if self.selected_folder:
            templates = self.model.get_templates_by_folder(self.selected_folder)
            
            # Trier les templates du plus récent au plus ancien
            try:
                templates.sort(
                    key=lambda t: datetime.fromisoformat(t.get('created_at', datetime.min.isoformat())), 
                    reverse=True
                )
            except Exception as e:
                logger.error(f"Erreur lors du tri des modèles : {e}")
            
            # Réinitialiser la liste des templates sélectionnés
            self.selected_templates = []
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
                folder_name = self.model.template_folders.get(self.selected_folder, "ce dossier")
                self.no_templates_label.configure(text=f"Aucun modèle disponible dans {folder_name}.")
                self.no_templates_label.pack(pady=20)
        else:
            # Si aucun dossier n'est sélectionné, montrer la vue des dossiers
            self.show_folders_view()
        
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
        
        if template_type == "Contrat":
            icon = "📝"
        elif template_type == "Facture":
            icon = "💰"
        elif template_type == "Proposition":
            icon = "📊"
        elif template_type == "Rapport":
            icon = "📈"
        
        # En-tête avec icône et type
        header = ctk.CTkFrame(card, fg_color=("gray90", "gray20"), corner_radius=6)
        header.pack(fill=ctk.X, padx=5, pady=5)
        
        ctk.CTkLabel(
            header,
            text=f"{icon} {template_type.capitalize() if template_type else 'Modèle'}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side=ctk.LEFT, padx=10, pady=5)
        
        # Date et heure de création
        creation_date = template.get('created_at', '')
        if creation_date:
            try:
                date_obj = datetime.fromisoformat(creation_date)
                formatted_date = date_obj.strftime("%d/%m/%Y à %H:%M")
                ctk.CTkLabel(
                    header,
                    text=formatted_date,
                    font=ctk.CTkFont(size=10),
                    text_color="gray"
                ).pack(side=ctk.RIGHT, padx=10, pady=5)
            except Exception as e:
                logger.error(f"Erreur lors du formatage de la date : {e}")
        
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
            command=lambda tid=template.get("id"): self.edit_template(tid)
        ).pack(side=ctk.LEFT, padx=2)
        
        # Bouton Utiliser
        ctk.CTkButton(
            actions_frame,
            text="Utiliser",
            width=80,
            height=25,
            command=lambda tid=template.get("id"): self.on_use_template(tid)
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
        dialog.geometry("400x200")  # Même taille que la boîte de dialogue des clients
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
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
            width=100,
            command=lambda: self.close_confirm_dialog(dialog, False)
        )
        cancel_btn.pack(side=ctk.LEFT, padx=(0, 10), fill="x", expand=True)
        
        # Bouton Supprimer
        delete_btn = ctk.CTkButton(
            buttons_frame,
            text="Supprimer",  # Texte simplifié comme pour les clients
            fg_color="#e74c3c",
            hover_color="#c0392b",
            width=100,
            command=lambda: self.close_confirm_dialog(dialog, True)
        )
        delete_btn.pack(side=ctk.RIGHT, fill="x", expand=True)
        
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
        self.show_success("Suppression effectuée avec succès")
    
    def show_error(self, message):
        """
        Affiche un message d'erreur dans le style du Dashboard
        
        Args:
            message: Message d'erreur
        """
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Erreur")
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
        try:
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
                try:
                    toast.destroy()
                except:
                    pass
            
            self.dialog.after(3000, hide_toast)
            
            logger.info(f"Toast de succès affiché: {message}")
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du toast: {e}")
            # En cas d'erreur, afficher un message dans la console
            print(f"Succès: {message}")
    
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
    
    def filter_templates(self):
        """
        Filtre les modèles selon les critères de recherche
        """
        self.update_view()
    
    def new_template(self):
        """
        Crée un nouveau modèle
        """
        try:
            # Créer les données initiales du modèle avec le dossier actuel
            template_data = {
                "name": "",
                "type": "autre",
                "description": "",
                "content": "",
                "variables": [],
                "folder": self.selected_folder if self.selected_folder else "autre"
            }
            
            # Créer une nouvelle instance du formulaire
            TemplateFormView(
                self.parent,
                self.model,
                template_data=template_data,
                update_view_callback=self.update_view
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du modèle: {e}")
            self.show_error("Erreur lors de la création du modèle")
    
    def on_edit_template(self, template_id):
        """Gère l'édition d'un modèle"""
        print(f"Tentative d'édition du modèle {template_id}")
        
        # Vérifier si l'édition nécessite une inscription
        check = self.usage_tracker.needs_registration("template_editing")
        if check["needs_registration"]:
            print("Inscription requise pour l'édition")
            # Trouver la fenêtre principale
            root = self.parent
            while root.master is not None:
                root = root.master
            
            # Afficher le dialogue d'inscription
            if hasattr(root, "_show_auth_dialog"):
                root._show_auth_dialog()
            return
        
        # Si l'utilisateur est inscrit ou n'a pas atteint la limite
        try:
            print("Appel de la méthode edit_template")
            self.edit_template(template_id)
        except Exception as e:
            print(f"Erreur lors de l'édition du modèle: {e}")
            logger.error(f"Erreur lors de l'édition du modèle: {e}")
            self.show_error("Erreur lors de l'édition du modèle")
    
    def edit_template(self, template_id):
        """
        Édite un modèle existant
        
        Args:
            template_id: ID du modèle à éditer
        """
        try:
            # Trouver le modèle à éditer
            template = next((t for t in self.model.templates if t.get("id") == template_id), None)
            if not template:
                raise ValueError(f"Modèle {template_id} non trouvé")
            
            # S'assurer que le dossier est correctement défini
            if not "folder" in template:
                template["folder"] = self.selected_folder if self.selected_folder else "autre"
            
            # Créer une nouvelle instance du formulaire
            TemplateFormView(
                self.parent,
                self.model,
                template_data=template,
                update_view_callback=self.update_view
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'édition du modèle: {e}")
            self.show_error("Erreur lors de l'édition du modèle")
    
    def on_use_template(self, template_id):
        """
        Utilise un modèle pour créer un document
        
        Args:
            template_id: ID du modèle à utiliser
        """
        try:
            logger.info(f"Délégation de l'utilisation du modèle {template_id} au contrôleur")
            # Déléguer l'action au contrôleur
            if hasattr(self, "controller"):
                self.controller.use_template(template_id)
            else:
                logger.error("Contrôleur non trouvé")
                self.show_error("Impossible d'utiliser le modèle : contrôleur non trouvé")
        except Exception as e:
            logger.error(f"Erreur lors de l'utilisation du modèle: {e}")
            self.show_error(f"Impossible d'utiliser le modèle : {str(e)}")
    
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
        Affiche la boîte de dialogue d'importation de modèle avec analyse de document
        """
        # Créer une fenêtre de dialogue
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Importer et analyser un modèle")
        dialog.geometry("800x600")
        dialog.resizable(True, True)
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
            text="📄 Importer et analyser un modèle",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Message d'instructions
        message_label = ctk.CTkLabel(
            main_frame,
            text="Sélectionnez un fichier à analyser et importer comme modèle.\nL'analyse permettra d'identifier les variables dans le document.",
            wraplength=760
        )
        message_label.pack(pady=10)
        
        # Variable pour stocker le chemin du fichier
        file_path_var = ctk.StringVar()
        
        # Frame pour le chemin du fichier
        file_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        file_frame.pack(fill=ctk.X, pady=10)
        
        # Entry pour afficher le chemin du fichier
        file_entry = ctk.CTkEntry(file_frame, textvariable=file_path_var, width=500)
        file_entry.pack(side=ctk.LEFT, padx=(0, 10))
        
        # Zone de contenu pour les résultats d'analyse
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Message initial
        info_label = ctk.CTkLabel(
            content_frame,
            text="Sélectionnez un fichier pour commencer l'analyse",
            font=ctk.CTkFont(size=14)
        )
        info_label.pack(pady=40)
        
        # Zone de statut et de progression
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(fill=ctk.X, padx=10, pady=(10, 0))
        
        # Indicateur de chargement
        spinner = None
        try:
            from utils.ui_components import LoadingSpinner
            spinner = LoadingSpinner(status_frame, size=20)
            spinner.pack(side=ctk.LEFT, padx=(10, 5), pady=5)
            # Ne pas démarrer immédiatement
            spinner.pack_forget()
        except Exception as e:
            logger.warning(f"Impossible de créer l'indicateur de chargement: {e}")
        
        # Étiquette de statut
        status_label = ctk.CTkLabel(
            status_frame,
            text="En attente de sélection d'un fichier",
            font=ctk.CTkFont(size=12)
        )
        status_label.pack(side=ctk.LEFT, padx=5, pady=5)
        
        # Boutons (initialement désactivés)
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill=ctk.X, padx=10, pady=10)
        
        # Bouton Annuler (toujours disponible)
        ctk.CTkButton(
            button_frame,
            text="Annuler",
            command=dialog.destroy
        ).pack(side=ctk.RIGHT, padx=5)
        
        # Fonction pour importer le fichier après l'analyse
        def import_file_with_analysis(analysis_results=None):
            file_path = file_path_var.get()
            if not file_path:
                self.show_error("Veuillez sélectionner un fichier")
                return
            
            try:
                # Extraire l'extension pour déterminer le type de fichier
                ext = os.path.splitext(file_path)[1].lower()
                
                # Créer les données de base du modèle
                template_data = {
                    "name": os.path.basename(os.path.splitext(file_path)[0]),
                    "category": "Importé",
                    "description": "Modèle importé et analysé"
                }
                
                # Si des variables ont été détectées, les ajouter
                if analysis_results and "variables" in analysis_results:
                    variables = analysis_results["variables"]
                    template_data["variables"] = list(variables.keys())
                
                # Importer en fonction du type de fichier
                if ext == '.docx':
                    result = self._import_docx(file_path, template_data)
                elif ext == '.txt' or ext == '.odt' or ext == '.rtf':
                    result = self._import_text(file_path, template_data)
                elif ext == '.pdf':
                    self.show_error("L'importation directe de fichiers PDF n'est pas prise en charge")
                    return
                else:
                    self.show_error("Format de fichier non pris en charge")
                    return
                
                if result:
                    # Mettre à jour la vue
                    self.update_view()
                    dialog.destroy()
                    self.show_success(f"Le modèle '{template_data['name']}' a été importé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de l'importation: {e}")
                self.show_error(f"Erreur lors de l'importation: {e}")
        
        # Fonction pour analyser le fichier
        def analyze_file(file_path):
            if not file_path:
                return
            
            # Vérifier que le fichier existe
            if not os.path.exists(file_path):
                self.show_error("Le fichier sélectionné n'existe pas")
                return
            
            # Afficher l'indicateur de chargement
            if spinner:
                spinner.pack(side=ctk.LEFT, padx=(10, 5), pady=5)
                spinner.start()
            
            # Mettre à jour le message et le statut
            info_label.configure(text=f"Analyse de {os.path.basename(file_path)} en cours...\nCette opération peut prendre quelques instants.")
            status_label.configure(text=f"Analyse de {os.path.basename(file_path)} en cours...")
            
            # Initialiser l'analyseur de documents si nécessaire
            if not hasattr(self, "doc_analyzer"):
                try:
                    from doc_analyzer import DocumentAnalyzer
                    self.doc_analyzer = DocumentAnalyzer()
                except Exception as e:
                    logger.error(f"Erreur lors de l'initialisation de l'analyseur: {e}")
                    self.doc_analyzer = None
            
            # Fonction pour afficher les résultats
            def display_results(results):
                # Supprimer le message de chargement
                info_label.destroy()
                
                if spinner:
                    spinner.stop()
                    spinner.pack_forget()
                
                status_label.configure(text="Analyse terminée")
                
                # Créer une zone défilante pour les résultats
                results_frame = ctk.CTkScrollableFrame(content_frame)
                results_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
                
                # Afficher des informations générales sur le document
                if "document_type" in results:
                    ctk.CTkLabel(
                        results_frame,
                        text=f"Type de document: {results['document_type']}",
                        font=ctk.CTkFont(size=14, weight="bold")
                    ).pack(anchor="w", pady=(5, 2))
                
                # Afficher les variables trouvées
                if "variables" in results and results["variables"]:
                    variables = results["variables"]
                    ctk.CTkLabel(
                        results_frame,
                        text="Variables détectées:",
                        font=ctk.CTkFont(size=14, weight="bold")
                    ).pack(anchor="w", pady=(10, 5))
                    
                    for var_name, var_value in variables.items():
                        var_frame = ctk.CTkFrame(results_frame)
                        var_frame.pack(fill=ctk.X, padx=5, pady=2)
                        
                        ctk.CTkLabel(
                            var_frame,
                            text=f"{var_name}:",
                            font=ctk.CTkFont(size=12, weight="bold"),
                            width=150
                        ).pack(side=ctk.LEFT, padx=5, pady=2)
                        
                        ctk.CTkLabel(
                            var_frame,
                            text=str(var_value),
                            font=ctk.CTkFont(size=12),
                            anchor="w"
                        ).pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5, pady=2)
                
                # Activer le bouton
                ctk.CTkButton(
                    button_frame,
                    text="Importer comme modèle",
                    command=lambda: import_file_with_analysis(results)
                ).pack(side=ctk.RIGHT, padx=5)
            
            # Fonction pour gérer l'échec de l'analyse
            def handle_analysis_failure(error_msg):
                if spinner:
                    spinner.stop()
                    spinner.pack_forget()
                
                info_label.destroy()
                
                # Afficher un message d'erreur
                error_label = ctk.CTkLabel(
                    content_frame,
                    text=f"Impossible d'analyser le document:\n{error_msg}",
                    font=ctk.CTkFont(size=14),
                    text_color=("red", "#FF5555")
                )
                error_label.pack(pady=40)
                
                status_label.configure(text="Analyse échouée")
                
                # Activer le bouton
                ctk.CTkButton(
                    button_frame,
                    text="Continuer sans analyse",
                    command=lambda: import_file_with_analysis()
                ).pack(side=ctk.RIGHT, padx=5)
            
            # Lancer l'analyse dans un thread séparé
            import threading
            
            def analyze_thread():
                try:
                    if self.doc_analyzer:
                        # Analyser le document
                        results = self.doc_analyzer.analyze_document(file_path)
                        
                        if results:
                            # Mettre à jour l'interface dans le thread principal
                            dialog.after(0, lambda: display_results(results))
                        else:
                            dialog.after(0, lambda: handle_analysis_failure("Aucun résultat d'analyse obtenu"))
                    else:
                        dialog.after(0, lambda: handle_analysis_failure("Analyseur non disponible"))
                except Exception as error:
                    logger.error(f"Erreur lors de l'analyse du document {file_path}: {error}")
                    dialog.after(0, lambda err=error: handle_analysis_failure(str(err)))
            
            # Lancer l'analyse
            thread = threading.Thread(target=analyze_thread)
            thread.daemon = True
            thread.start()
        
        def browse_file():
            file_types = [
                ('Documents', '*.pdf;*.docx;*.doc;*.txt;*.odt'),
                ('PDF', '*.pdf'),
                ('Word', '*.docx;*.doc'),
                ('Texte', '*.txt'),
                ('OpenDocument', '*.odt'),
                ('Tous les fichiers', '*.*')
            ]
            file_path = filedialog.askopenfilename(
                parent=dialog,
                title="Sélectionner un fichier",
                filetypes=file_types
            )
            if file_path:
                file_path_var.set(file_path)
                
                # Lancer automatiquement l'analyse quand un fichier est choisi
                analyze_file(file_path)
        
        # Bouton Parcourir
        browse_button = ctk.CTkButton(
            file_frame,
            text="Parcourir",
            width=100,
            command=browse_file
        )
        browse_button.pack(side=ctk.LEFT)
        
    def _import_docx(self, file_path, template_data=None):
        # Code d'importation de docx existant...
        # à adapter pour utiliser template_data si fourni
        try:
            import docx
            from docx.opc.exceptions import PackageNotFoundError
            
            # Convertir le fichier DOCX en données de modèle
            try:
                # Charger le document
                doc = docx.Document(file_path)
                
                # Extraire le texte complet
                full_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                
                # Si aucune donnée de modèle n'est fournie, créer un dictionnaire de base
                if template_data is None:
                    template_data = {
                        "name": os.path.basename(os.path.splitext(file_path)[0]),
                        "category": "Importé",
                        "description": "Modèle importé directement"
                    }
                
                # Détecter les variables si elles ne sont pas déjà définies
                if "variables" not in template_data:
                    # Détecter les variables du type {nom_variable}
                    import re
                    variable_pattern = r"\{([a-zA-Z0-9_]+)\}"
                    variables = re.findall(variable_pattern, full_text)
                    
                    # Détecter les variables du type {{nom_variable}}
                    variable_pattern2 = r"\{\{([a-zA-Z0-9_]+)\}\}"
                    variables2 = re.findall(variable_pattern2, full_text)
                    
                    # Fusionner les listes de variables
                    all_variables = list(set(variables + variables2))
                    
                    if all_variables:
                        template_data["variables"] = all_variables
                
                # Ajouter les données du document
                template_data["content"] = full_text
                
                # Enregistrer le modèle dans la base de données
                self.model.templates.add_template(template_data)
                
                return True
            except PackageNotFoundError:
                self.show_error("Le fichier n'est pas un document Word valide")
                return False
        except ImportError:
            self.show_error("Module python-docx non disponible")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'importation du fichier DOCX: {e}")
            self.show_error(f"Erreur lors de l'importation: {e}")
            return False

    def _import_text(self, file_path, template_data=None):
        # Code d'importation de texte existant...
        # à adapter pour utiliser template_data si fourni
        try:
            # Lire le fichier texte
            import chardet
            
            # Détecter l'encodage du fichier
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                detection = chardet.detect(raw_data)
                encoding = detection['encoding']
            
            # Lire le fichier avec l'encodage détecté
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Si aucune donnée de modèle n'est fournie, créer un dictionnaire de base
            if template_data is None:
                template_data = {
                    "name": os.path.basename(os.path.splitext(file_path)[0]),
                    "category": "Importé",
                    "description": "Modèle importé directement"
                }
            
            # Détecter les variables si elles ne sont pas déjà définies
            if "variables" not in template_data:
                # Détecter les variables du type {nom_variable}
                import re
                variable_pattern = r"\{([a-zA-Z0-9_]+)\}"
                variables = re.findall(variable_pattern, content)
                
                # Détecter les variables du type {{nom_variable}}
                variable_pattern2 = r"\{\{([a-zA-Z0-9_]+)\}\}"
                variables2 = re.findall(variable_pattern2, content)
                
                # Fusionner les listes de variables
                all_variables = list(set(variables + variables2))
                
                if all_variables:
                    template_data["variables"] = all_variables
            
            # Ajouter les données du document
            template_data["content"] = content
            
            # Enregistrer le modèle dans la base de données
            self.model.templates.add_template(template_data)
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'importation du fichier texte: {e}")
            self.show_error(f"Erreur lors de l'importation: {e}")
            return False

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
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Centrer la fenêtre
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Structure globale: un main_frame pour tout le contenu
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Zone de défilement pour le formulaire
        form_frame = ctk.CTkScrollableFrame(main_frame)
        form_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Titre
        title_label = ctk.CTkLabel(
            form_frame,
            text="📝 " + ("Modifier le modèle" if self.template_data else "Nouveau modèle"),
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Nom
        name_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        name_frame.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(name_frame, text="Nom*:", width=100).pack(side=ctk.LEFT)
        self.name_var = ctk.StringVar(value=self.template_data.get("name", "") if self.template_data else "")
        self.name_entry = ctk.CTkEntry(name_frame, textvariable=self.name_var, width=400)
        self.name_entry.pack(side=ctk.LEFT, padx=10)
        
        # Type de document
        type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        type_frame.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(type_frame, text="Type*:", width=100).pack(side=ctk.LEFT)
        types = ["contrat", "facture", "proposition", "rapport", "autre"]
        self.type_var = ctk.StringVar(value=self.template_data.get("type", types[0]) if self.template_data else types[0])
        type_menu = ctk.CTkOptionMenu(type_frame, values=types, variable=self.type_var, width=400)
        type_menu.pack(side=ctk.LEFT, padx=10)
        
        # Description
        desc_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        desc_frame.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(desc_frame, text="Description:", width=100).pack(side=ctk.LEFT)
        self.description_text = ctk.CTkTextbox(desc_frame, width=400, height=60)
        self.description_text.pack(side=ctk.LEFT, padx=10)
        if self.template_data and "description" in self.template_data:
            self.description_text.insert("1.0", self.template_data["description"])
        
        # Dossier (obligatoire)
        folder_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        folder_frame.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(folder_frame, text="Dossier*:", width=100).pack(side=ctk.LEFT)
        folders = list(self.model.template_folders.values())
        # Obtenir le nom du dossier à partir de l'ID si on est en mode édition
        initial_folder = folders[0]
        if self.template_data and "folder" in self.template_data:
            folder_id = str(self.template_data["folder"])  # Convertir en string pour la comparaison
            for fid, fname in self.model.template_folders.items():
                if str(fid) == folder_id:
                    initial_folder = fname
                    break
        self.folder_var = ctk.StringVar(value=initial_folder)
        folder_menu = ctk.CTkOptionMenu(folder_frame, values=folders, variable=self.folder_var, width=400)
        folder_menu.pack(side=ctk.LEFT, padx=10)
        
        # Variables
        var_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        var_frame.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(var_frame, text="Variables:", width=100).pack(side=ctk.LEFT)
        self.variables_text = ctk.CTkTextbox(var_frame, width=400, height=80)
        self.variables_text.pack(side=ctk.LEFT, padx=10)
        if self.template_data and "variables" in self.template_data:
            self.variables_text.insert("1.0", "\n".join(self.template_data["variables"]))
        
        # Note sur les variables
        var_note_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        var_note_frame.pack(fill=ctk.X)
        ctk.CTkLabel(var_note_frame, text="(Une variable par ligne)", text_color="gray").pack(pady=2)
        
        # Variables standards disponibles
        std_var_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        std_var_frame.pack(fill=ctk.X, pady=10)
        ctk.CTkLabel(std_var_frame, text="Variables standards disponibles:").pack(anchor="w")
        standard_vars = "client_name, client_company, client_email, client_phone, client_address, company_name, date"
        ctk.CTkLabel(std_var_frame, text=standard_vars, text_color="gray").pack(anchor="w")
        
        # Contenu
        content_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        content_frame.pack(fill=ctk.X, pady=5)
        ctk.CTkLabel(content_frame, text="Contenu*:", width=100).pack(anchor="w")
        
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
            if self.template_data and "content" in self.template_data:
                self.content_editor.set_content(self.template_data["content"])
            
        except Exception as e:
            logger.warning(f"Impossible d'utiliser RichTextEditor: {e}")
            # Fallback sur un CTkTextbox standard
            self.content_editor = ctk.CTkTextbox(content_frame)
            self.content_editor.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
            
            if self.template_data and "content" in self.template_data:
                self.content_editor.insert("1.0", self.template_data["content"])
        
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
            self.show_error("Le nom est requis")
            self.name_entry.focus()
            return
        
        # Récupérer le type
        template_type = self.type_var.get().strip()
        
        # Récupérer la description
        description = self.description_text.get("1.0", "end-1c").strip()
        
        # Récupérer le dossier et convertir le nom en ID
        folder_name = self.folder_var.get().strip()
        if not folder_name:
            self.show_error("Le dossier est requis")
            return
        
        # Trouver l'ID du dossier à partir du nom
        folder_id = None
        for fid, fname in self.model.template_folders.items():
            if fname == folder_name:
                folder_id = fid
                break
        
        if not folder_id:
            folder_id = "autre"  # Utiliser le dossier par défaut si non trouvé
        
        # Récupérer les variables (une par ligne)
        variables_raw = self.variables_text.get("1.0", "end-1c").strip()
        variables = [v.strip() for v in variables_raw.split('\n') if v.strip()]
        
        # Récupérer le contenu selon le type d'éditeur
        if isinstance(self.content_editor, RichTextEditor):
            content = self.content_editor.get_content()
        else:
            content = self.content_editor.get("1.0", "end-1c")
        
        if not content:
            self.show_error("Le contenu est requis")
            self.content_editor.focus()
            return
        
        try:
            template_data = {
                "name": name,
                "type": template_type,
                "description": description,
                "folder": folder_id,
                "variables": variables,
                "content": content
            }
            
            if self.template_data and "id" in self.template_data:
                # Mise à jour
                success = self.model.update_template(self.template_data["id"], template_data)
                if success:
                    self.show_success("Modèle mis à jour avec succès")
                    self.dialog.destroy()
                    if self.update_view_callback:
                        self.update_view_callback()
                else:
                    self.show_error("Impossible de mettre à jour le modèle")
            else:
                # Création
                template_id = self.model.add_template(template_data)
                if template_id:
                    self.show_success("Modèle créé avec succès")
                    self.dialog.destroy()
                    if self.update_view_callback:
                        self.update_view_callback()
                else:
                    self.show_error("Impossible de créer le modèle")
                    
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du modèle: {e}")
            self.show_error(f"Erreur lors de la sauvegarde: {str(e)}")

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

