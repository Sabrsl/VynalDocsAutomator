#!/usr/bin/env python3 
# -*- coding: utf-8 -*-

"""
Module d'éditeur de texte enrichi pour l'application Vynal Docs Automator
Permet la mise en forme du texte avec gras, italique, souligné, etc.
"""

import os
import logging
import tkinter as tk
from tkinter import font as tkfont
from tkinter import colorchooser
import customtkinter as ctk
from tkinter import ttk
import re
from functools import lru_cache
from tkinter import filedialog
from PIL import Image, ImageTk
import base64
from bs4 import BeautifulSoup
import io

logger = logging.getLogger("VynalDocsAutomator.RichTextEditor")

class RichTextEditor(ctk.CTkFrame):
    """
    Composant d'éditeur de texte enrichi pour l'application
    """
    
    def __init__(self, parent, initial_content="", variable_options=None, **kwargs):
        """
        Initialise l'éditeur de texte enrichi
        
        Args:
            parent: Widget parent
            initial_content: Contenu initial de l'éditeur
            variable_options: Liste des variables disponibles pour l'insertion
            **kwargs: Arguments supplémentaires pour le cadre
        """
        super().__init__(parent, **kwargs)
        
        # Variables d'état
        self.current_tags = set()  # Tags actifs (bold, italic, etc.)
        self.variable_options = variable_options or []  # Liste des variables disponibles
        
        # Polices disponibles
        self.available_fonts = ["Arial", "Times New Roman", "Courier New", "Verdana", "Helvetica"]
        self.font_sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32", "36", "48", "72"]
        
        # Menu contextuel
        self.more_options_menu = None
        
        # Cache pour les performances
        self._tag_cache = {}
        
        # Dictionnaires pour suivre les styles actifs
        self.active_styles = {}
        
        # Création de l'interface
        self.create_toolbar()
        self.create_text_area()
        
        # Configuration des événements
        self.bind_events()
        
        # Initialisation du contenu
        if initial_content:
            self.set_content(initial_content)
        
        logger.info("RichTextEditor initialisé")
    
    def create_toolbar(self):
        """
        Crée la barre d'outils de l'éditeur
        """
        # Cadre principal de la barre d'outils
        self.toolbar = ctk.CTkFrame(self)
        self.toolbar.pack(fill=ctk.X, padx=5, pady=5)
        
        # Section 1: Style et police
        style_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        style_frame.pack(side=ctk.LEFT, padx=5, fill=ctk.Y)
        
        # Police
        self.font_var = ctk.StringVar(value="Arial")
        self.font_dropdown = ctk.CTkOptionMenu(
            style_frame,
            values=self.available_fonts,
            variable=self.font_var,
            width=120,
            command=self.apply_font
        )
        self.font_dropdown.pack(side=ctk.LEFT, padx=2)
        
        # Taille de police
        self.font_size_var = ctk.StringVar(value="12")
        self.font_size_dropdown = ctk.CTkOptionMenu(
            style_frame,
            values=self.font_sizes,
            variable=self.font_size_var,
            width=60,
            command=self.apply_font_size
        )
        self.font_size_dropdown.pack(side=ctk.LEFT, padx=2)
        
        # Séparateur
        self.create_separator(self.toolbar)
        
        # Section 2: Format basique
        format_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        format_frame.pack(side=ctk.LEFT, padx=5, fill=ctk.Y)
        
        # Bouton gras
        self.bold_btn = self.create_toolbar_button(
            format_frame, "B", "Gras (Ctrl+B)", 
            self.toggle_bold
        )
        self.bold_btn._text_label.configure(font=("Arial", 14, "bold"))
        
        # Bouton italique
        self.italic_btn = self.create_toolbar_button(
            format_frame, "I", "Italique (Ctrl+I)", 
            self.toggle_italic
        )
        self.italic_btn._text_label.configure(font=("Arial", 14, "italic"))
        
        # Bouton souligné
        self.underline_btn = self.create_toolbar_button(
            format_frame, "U", "Souligné (Ctrl+U)", 
            self.toggle_underline
        )
        self.underline_btn._text_label.configure(font=("Arial", 14))
        
        # Bouton couleur de texte
        self.color_btn = self.create_toolbar_button(
            format_frame, "A", "Couleur du texte", 
            self.choose_text_color
        )
        self.color_btn._text_label.configure(font=("Arial", 14))
        
        # Séparateur
        self.create_separator(self.toolbar)
        
        # Section 3: Alignement
        align_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        align_frame.pack(side=ctk.LEFT, padx=5, fill=ctk.Y)
        
        # Boutons d'alignement
        self.align_left_btn = self.create_toolbar_button(
            align_frame, "◀", "Aligner à gauche", 
            lambda: self.set_alignment("left")
        )
        
        self.align_center_btn = self.create_toolbar_button(
            align_frame, "◆", "Centrer", 
            lambda: self.set_alignment("center")
        )
        
        self.align_right_btn = self.create_toolbar_button(
            align_frame, "▶", "Aligner à droite", 
            lambda: self.set_alignment("right")
        )
        
        # Séparateur
        self.create_separator(self.toolbar)
        
        # Section 4: Listes
        list_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        list_frame.pack(side=ctk.LEFT, padx=5, fill=ctk.Y)
        
        # Bouton liste à puces
        self.bullet_list_btn = self.create_toolbar_button(
            list_frame, "•", "Liste à puces", 
            self.toggle_bullet_list
        )
        
        # Bouton liste numérotée
        self.numbered_list_btn = self.create_toolbar_button(
            list_frame, "1.", "Liste numérotée", 
            self.toggle_numbered_list
        )
        
        # Séparateur
        self.create_separator(self.toolbar)
        
        # Section 5: Insertion d'image
        image_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        image_frame.pack(side=ctk.LEFT, padx=5, fill=ctk.Y)
        
        # Bouton insertion d'image
        self.image_btn = self.create_toolbar_button(
            image_frame, "🖼️", "Insérer une image", 
            self.insert_image
        )
        
        # Séparateur
        self.create_separator(self.toolbar)
        
        # Section 6: Plus d'options
        more_options_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        more_options_frame.pack(side=ctk.LEFT, padx=5, fill=ctk.Y)
        
        # Bouton plus d'options
        self.more_options_btn = self.create_toolbar_button(
            more_options_frame, "...", "Plus d'options", 
            self.show_more_options
        )
        
        # Section 7: Variables
        self.create_separator(self.toolbar)
        var_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        var_frame.pack(side=ctk.LEFT, padx=5, fill=ctk.Y)
        
        # Menu déroulant pour les variables
        self.variable_var = ctk.StringVar()
        self.variable_dropdown = ctk.CTkComboBox(
            var_frame,
            values=self.variable_options,
            variable=self.variable_var,
            width=150
        )
        self.variable_dropdown.pack(side=ctk.LEFT, padx=2)
        
        # Bouton d'insertion de variable
        self.insert_var_btn = self.create_toolbar_button(
            var_frame, "Insérer", "Insérer la variable sélectionnée", 
            self.insert_variable
        )
    
    def create_text_area(self):
        """
        Crée la zone de texte de l'éditeur
        """
        # Cadre de la zone de texte avec bordure
        self.text_frame = ctk.CTkFrame(self)
        self.text_frame.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        
        # Barres de défilement
        self.scrollbar_y = ctk.CTkScrollbar(self.text_frame)
        self.scrollbar_y.pack(side=ctk.RIGHT, fill=ctk.Y)
        
        self.scrollbar_x = ctk.CTkScrollbar(self.text_frame, orientation="horizontal")
        self.scrollbar_x.pack(side=ctk.BOTTOM, fill=ctk.X)
        
        # Zone de texte
        self.text_area = tk.Text(
            self.text_frame,
            wrap="word",
            undo=True,
            font=("Arial", 12),
            bg="white",
            fg="black",
            insertbackground="black",
            borderwidth=0,
            highlightthickness=0
        )
        self.text_area.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)
        
        # Connecter les barres de défilement
        self.scrollbar_y.configure(command=self.text_area.yview)
        self.scrollbar_x.configure(command=self.text_area.xview)
        self.text_area.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)
        
        # Configuration des tags pour la mise en forme
        self.initialize_basic_tags()
        self.initialize_composite_tags()
    
    def initialize_basic_tags(self):
        """
        Initialise les tags de base pour le formatage
        """
        # Tags pour les styles de base
        self.text_area.tag_configure("bold", font=("Arial", 12, "bold"))
        self.text_area.tag_configure("italic", font=("Arial", 12, "italic"))
        self.text_area.tag_configure("underline", underline=1)
        self.text_area.tag_configure("left", justify="left")
        self.text_area.tag_configure("center", justify="center")
        self.text_area.tag_configure("right", justify="right")
        self.text_area.tag_configure("variable", foreground="blue")
        self.text_area.tag_configure("strikethrough", overstrike=1)
    
    def initialize_composite_tags(self):
        """
        Initialise les tags composés pour les combinaisons de styles
        """
        # Créer des tags pour toutes les combinaisons possibles
        for font_name in self.available_fonts:
            for size in self.font_sizes:
                size_int = int(size)
                
                # Tag pour police et taille
                base_tag = f"font_{font_name}_size_{size}"
                self.text_area.tag_configure(base_tag, font=(font_name, size_int))
                
                # Tag pour police, taille et gras
                bold_tag = f"{base_tag}_bold"
                self.text_area.tag_configure(bold_tag, font=(font_name, size_int, "bold"))
                
                # Tag pour police, taille et italique
                italic_tag = f"{base_tag}_italic"
                self.text_area.tag_configure(italic_tag, font=(font_name, size_int, "italic"))
                
                # Tag pour police, taille, gras et italique
                bold_italic_tag = f"{base_tag}_bold_italic"
                self.text_area.tag_configure(bold_italic_tag, font=(font_name, size_int, "bold italic"))
                
                # Tag pour police, taille et souligné
                underline_tag = f"{base_tag}_underline"
                self.text_area.tag_configure(underline_tag, font=(font_name, size_int), underline=1)
                
                # Tag pour police, taille, gras et souligné
                bold_underline_tag = f"{base_tag}_bold_underline"
                self.text_area.tag_configure(bold_underline_tag, font=(font_name, size_int, "bold"), underline=1)
                
                # Tag pour police, taille, italique et souligné
                italic_underline_tag = f"{base_tag}_italic_underline"
                self.text_area.tag_configure(italic_underline_tag, font=(font_name, size_int, "italic"), underline=1)
                
                # Tag pour police, taille, gras, italique et souligné
                bold_italic_underline_tag = f"{base_tag}_bold_italic_underline"
                self.text_area.tag_configure(bold_italic_underline_tag, font=(font_name, size_int, "bold italic"), underline=1)
    
    def create_toolbar_button(self, parent, text, tooltip, command):
        """
        Crée un bouton pour la barre d'outils
        
        Args:
            parent: Widget parent
            text: Texte du bouton
            tooltip: Info-bulle du bouton
            command: Fonction à exécuter lorsque le bouton est cliqué
            
        Returns:
            ctk.CTkButton: Bouton créé
        """
        button = ctk.CTkButton(
            parent,
            text=text,
            width=40,
            height=25,
            command=command
        )
        button.pack(side=ctk.LEFT, padx=2)
        
        # Ajouter une info-bulle (tooltip)
        self.create_tooltip(button, tooltip)
        
        return button
    
    def create_separator(self, parent):
        """
        Crée un séparateur vertical dans la barre d'outils
        
        Args:
            parent: Widget parent
        """
        separator = ctk.CTkFrame(
            parent,
            width=1,
            height=25,
            fg_color="gray"
        )
        separator.pack(side=ctk.LEFT, padx=5, pady=2)
    
    def create_tooltip(self, widget, text):
        """
        Crée une info-bulle pour un widget
        
        Args:
            widget: Widget auquel attacher l'info-bulle
            text: Texte de l'info-bulle
        """
        def enter(event):
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(
                self.tooltip,
                text=text,
                background="#ffffe0",
                relief="solid",
                borderwidth=1,
                font=("Arial", 8)
            )
            label.pack()
        
        def leave(event):
            if hasattr(self, "tooltip"):
                self.tooltip.destroy()
                del self.tooltip
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    
    def bind_events(self):
        """
        Configure les événements pour l'éditeur
        """
        # Raccourcis clavier
        self.text_area.bind("<Control-b>", lambda event: self.toggle_bold())
        self.text_area.bind("<Control-i>", lambda event: self.toggle_italic())
        self.text_area.bind("<Control-u>", lambda event: self.toggle_underline())
        
        # Suivi de la position du curseur
        self.text_area.bind("<<Selection>>", self.update_toolbar_state)
        self.text_area.bind("<Button-1>", self.update_toolbar_state)
        self.text_area.bind("<KeyRelease>", self.update_toolbar_state)
        
        # Optimisation: throttle pour les événements fréquents
        self._last_update = 0
    
    def get_active_styles(self, position=None):
        """
        Récupère les styles actifs à une position donnée ou pour la sélection actuelle
        
        Args:
            position: Position à vérifier (None = position du curseur ou sélection)
            
        Returns:
            dict: Dictionnaire des styles actifs
        """
        styles = {
            "font": "Arial",
            "size": "12",
            "bold": False,
            "italic": False,
            "underline": False,
            "color": None,
            "alignment": "left"
        }
        
        if position is None:
            # Vérifier s'il y a une sélection
            try:
                selection_ranges = self.text_area.tag_ranges(tk.SEL)
                if selection_ranges:
                    position = selection_ranges[0]
                else:
                    position = f"{self.text_area.index(tk.INSERT)}"
            except:
                position = f"{self.text_area.index(tk.INSERT)}"
        
        # Récupérer tous les tags à cette position
        tags = self.text_area.tag_names(position)
        
        # Analyser les tags pour déterminer les styles
        for tag in tags:
            if tag == "bold":
                styles["bold"] = True
            elif tag == "italic":
                styles["italic"] = True
            elif tag == "underline":
                styles["underline"] = True
            elif tag in ["left", "center", "right"]:
                styles["alignment"] = tag
            elif tag.startswith("font_"):
                # Extraire les informations du tag composite
                parts = tag.split("_")
                for i, part in enumerate(parts):
                    if part == "font" and i+1 < len(parts):
                        styles["font"] = parts[i+1]
                    elif part == "size" and i+1 < len(parts):
                        styles["size"] = parts[i+1]
                    elif part == "bold":
                        styles["bold"] = True
                    elif part == "italic":
                        styles["italic"] = True
                    elif part == "underline":
                        styles["underline"] = True
            elif tag.startswith("color-"):
                color_hex = "#" + tag[6:]
                styles["color"] = color_hex
        
        return styles
    
    def get_composite_tag(self, font, size, bold=False, italic=False, underline=False):
        """
        Génère un nom de tag composite pour une combinaison de styles
        
        Args:
            font: Nom de la police
            size: Taille de police
            bold: Texte en gras
            italic: Texte en italique
            underline: Texte souligné
            
        Returns:
            str: Nom du tag composite
        """
        tag = f"font_{font}_size_{size}"
        
        if bold:
            tag += "_bold"
        
        if italic:
            tag += "_italic"
        
        if underline:
            tag += "_underline"
        
        return tag
    
    def apply_composite_tag(self, start=None, end=None):
        """
        Applique un tag composite basé sur les styles actifs
        
        Args:
            start: Position de début (None = position du curseur ou début de sélection)
            end: Position de fin (None = égal à start ou fin de sélection)
        """
        # Déterminer la plage de texte à modifier
        if start is None or end is None:
            try:
                selection_ranges = self.text_area.tag_ranges(tk.SEL)
                if selection_ranges:
                    start, end = selection_ranges
                else:
                    start = self.text_area.index(tk.INSERT)
                    end = start
            except:
                start = self.text_area.index(tk.INSERT)
                end = start
        
        # Récupérer les styles actifs
        styles = self.get_active_styles(start)
        
        # Créer le tag composite
        composite_tag = self.get_composite_tag(
            styles["font"],
            styles["size"],
            styles["bold"],
            styles["italic"],
            styles["underline"]
        )
        
        # Supprimer les tags de police et de style existants
        for tag in list(self.text_area.tag_names(start)):
            if tag.startswith("font_") or tag in ["bold", "italic", "underline"]:
                self.text_area.tag_remove(tag, start, end)
        
        # Appliquer le nouveau tag composite
        self.text_area.tag_add(composite_tag, start, end)
        
        # Appliquer les autres styles (couleur, alignement)
        if styles["color"]:
            color_tag = f"color-{styles['color'].replace('#', '')}"
            self.text_area.tag_add(color_tag, start, end)
        
        if styles["alignment"]:
            self.text_area.tag_add(styles["alignment"], start, end)
    
    def toggle_bold(self):
        """Active/désactive le gras sur le texte sélectionné"""
        try:
            selection_ranges = self.text_area.tag_ranges(tk.SEL)
            if selection_ranges:
                start, end = selection_ranges
                
                # Récupérer les styles actuels
                styles = self.get_active_styles(start)
                
                # Inverser l'état du gras
                styles["bold"] = not styles["bold"]
                
                # Créer le tag composite
                composite_tag = self.get_composite_tag(
                    styles["font"],
                    styles["size"],
                    styles["bold"],
                    styles["italic"],
                    styles["underline"]
                )
                
                # Supprimer les tags de police et de style existants
                for tag in list(self.text_area.tag_names(start)):
                    if tag.startswith("font_") or tag in ["bold", "italic", "underline"]:
                        self.text_area.tag_remove(tag, start, end)
                
                # Appliquer le nouveau tag composite
                self.text_area.tag_add(composite_tag, start, end)
                
                # Mettre à jour l'état du bouton
                self.update_button_state(self.bold_btn, styles["bold"])
            else:
                # Sans sélection, on change l'état pour les prochaines saisies
                if "bold" in self.current_tags:
                    self.current_tags.remove("bold")
                    self.update_button_state(self.bold_btn, False)
                else:
                    self.current_tags.add("bold")
                    self.update_button_state(self.bold_btn, True)
        except Exception as e:
            logger.error(f"Erreur lors de l'application du gras: {e}")
    
    def toggle_italic(self):
        """Active/désactive l'italique sur le texte sélectionné"""
        try:
            selection_ranges = self.text_area.tag_ranges(tk.SEL)
            if selection_ranges:
                start, end = selection_ranges
                
                # Récupérer les styles actuels
                styles = self.get_active_styles(start)
                
                # Inverser l'état de l'italique
                styles["italic"] = not styles["italic"]
                
                # Créer le tag composite
                composite_tag = self.get_composite_tag(
                    styles["font"],
                    styles["size"],
                    styles["bold"],
                    styles["italic"],
                    styles["underline"]
                )
                
                # Supprimer les tags de police et de style existants
                for tag in list(self.text_area.tag_names(start)):
                    if tag.startswith("font_") or tag in ["bold", "italic", "underline"]:
                        self.text_area.tag_remove(tag, start, end)
                
                # Appliquer le nouveau tag composite
                self.text_area.tag_add(composite_tag, start, end)
                
                # Mettre à jour l'état du bouton
                self.update_button_state(self.italic_btn, styles["italic"])
            else:
                # Sans sélection, on change l'état pour les prochaines saisies
                if "italic" in self.current_tags:
                    self.current_tags.remove("italic")
                    self.update_button_state(self.italic_btn, False)
                else:
                    self.current_tags.add("italic")
                    self.update_button_state(self.italic_btn, True)
        except Exception as e:
            logger.error(f"Erreur lors de l'application de l'italique: {e}")
    
    def toggle_underline(self):
        """Active/désactive le soulignement sur le texte sélectionné"""
        try:
            selection_ranges = self.text_area.tag_ranges(tk.SEL)
            if selection_ranges:
                start, end = selection_ranges
                
                # Récupérer les styles actuels
                styles = self.get_active_styles(start)
                
                # Inverser l'état du soulignement
                styles["underline"] = not styles["underline"]
                
                # Créer le tag composite
                composite_tag = self.get_composite_tag(
                    styles["font"],
                    styles["size"],
                    styles["bold"],
                    styles["italic"],
                    styles["underline"]
                )
                
                # Supprimer les tags de police et de style existants
                for tag in list(self.text_area.tag_names(start)):
                    if tag.startswith("font_") or tag in ["bold", "italic", "underline"]:
                        self.text_area.tag_remove(tag, start, end)
                
                # Appliquer le nouveau tag composite
                self.text_area.tag_add(composite_tag, start, end)
                
                # Mettre à jour l'état du bouton
                self.update_button_state(self.underline_btn, styles["underline"])
            else:
                # Sans sélection, on change l'état pour les prochaines saisies
                if "underline" in self.current_tags:
                    self.current_tags.remove("underline")
                    self.update_button_state(self.underline_btn, False)
                else:
                    self.current_tags.add("underline")
                    self.update_button_state(self.underline_btn, True)
        except Exception as e:
            logger.error(f"Erreur lors de l'application du soulignement: {e}")
    
    def set_alignment(self, alignment):
        """
        Définit l'alignement du paragraphe actuel
        
        Args:
            alignment: Type d'alignement ('left', 'center', 'right')
        """
        try:
            insert_pos = self.text_area.index(tk.INSERT)
            start = self.text_area.index(f"{insert_pos} linestart")
            end = self.text_area.index(f"{insert_pos} lineend+1c")
            
            # Supprimer les tags d'alignement existants
            for align in ['left', 'center', 'right']:
                self.text_area.tag_remove(align, start, end)
            
            # Appliquer le nouvel alignement
            self.text_area.tag_add(alignment, start, end)
            
            # Mettre à jour l'état des boutons d'alignement
            self.update_button_state(self.align_left_btn, alignment == "left")
            self.update_button_state(self.align_center_btn, alignment == "center")
            self.update_button_state(self.align_right_btn, alignment == "right")
        except Exception as e:
            logger.error(f"Erreur lors de l'application de l'alignement {alignment}: {e}")
    
    def toggle_bullet_list(self):
        """Ajoute/supprime une liste à puces au paragraphe actuel"""
        try:
            insert_pos = self.text_area.index(tk.INSERT)
            line_start = self.text_area.index(f"{insert_pos} linestart")
            line_content = self.text_area.get(line_start, f"{line_start} lineend")
            
            if line_content.startswith("• "):
                self.text_area.delete(line_start, f"{line_start}+2c")
            else:
                self.text_area.insert(line_start, "• ")
        except Exception as e:
            logger.error(f"Erreur lors de la gestion de la liste à puces: {e}")
    
    def toggle_numbered_list(self):
        """Ajoute/supprime une liste numérotée au paragraphe actuel"""
        try:
            insert_pos = self.text_area.index(tk.INSERT)
            line_start = self.text_area.index(f"{insert_pos} linestart")
            line_content = self.text_area.get(line_start, f"{line_start} lineend")
            
            if re.match(r'^\d+\.\s', line_content):
                match = re.match(r'^\d+\.\s', line_content)
                self.text_area.delete(line_start, f"{line_start}+{len(match.group())}c")
            else:
                previous_line = self.text_area.index(f"{line_start}-1l")
                prev_content = self.text_area.get(f"{previous_line} linestart", f"{previous_line} lineend")
                match = re.match(r'^(\d+)\.\s', prev_content)
                num = int(match.group(1)) + 1 if match else 1
                self.text_area.insert(line_start, f"{num}. ")
        except Exception as e:
            logger.error(f"Erreur lors de la gestion de la liste numérotée: {e}")
    
    def choose_text_color(self):
        """Ouvre un sélecteur de couleur et applique la couleur choisie au texte"""
        color = colorchooser.askcolor(title="Choisir une couleur de texte")
        if color[1]:
            try:
                # Créer un tag pour cette couleur
                color_tag = f"color-{color[1].replace('#', '')}"
                self.text_area.tag_configure(color_tag, foreground=color[1])
                
                # Appliquer la couleur au texte sélectionné
                selection_ranges = self.text_area.tag_ranges(tk.SEL)
                if selection_ranges:
                    start, end = selection_ranges
                    
                    # Supprimer les autres tags de couleur
                    for tag in self.text_area.tag_names(start):
                        if tag.startswith("color-"):
                            self.text_area.tag_remove(tag, start, end)
                    
                    # Appliquer la nouvelle couleur
                    self.text_area.tag_add(color_tag, start, end)
                else:
                    # Sans sélection, on change l'état pour les prochaines saisies
                    self.current_tags = {tag for tag in self.current_tags if not tag.startswith("color-")}
                    self.current_tags.add(color_tag)
                
                # Mettre à jour l'indicateur du bouton de couleur
                self.color_btn.configure(fg_color=color[1])
            except Exception as e:
                logger.error(f"Erreur lors de l'application de la couleur de texte: {e}")
    
    def apply_font(self, font_name):
        """
        Applique une police de caractères
        
        Args:
            font_name: Nom de la police à appliquer
        """
        try:
            # Récupérer la taille actuelle
            current_size = int(self.font_size_var.get())
            
            selection_ranges = self.text_area.tag_ranges(tk.SEL)
            if selection_ranges:
                start, end = selection_ranges
                
                # Récupérer les styles actuels
                styles = self.get_active_styles(start)
                styles["font"] = font_name
                
                # Créer le tag composite
                composite_tag = self.get_composite_tag(
                    font_name,
                    styles["size"],
                    styles["bold"],
                    styles["italic"],
                    styles["underline"]
                )
                
                # Supprimer les tags de police existants
                for tag in list(self.text_area.tag_names(start)):
                    if tag.startswith("font_"):
                        self.text_area.tag_remove(tag, start, end)
                
                # Appliquer le nouveau tag composite
                self.text_area.tag_add(composite_tag, start, end)
            else:
                # Sans sélection, mettre à jour les styles actifs pour les prochaines saisies
                self.font_var.set(font_name)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la police {font_name}: {e}")
    
    def apply_font_size(self, size):
        """
        Applique une taille de police
        
        Args:
            size: Taille de police à appliquer
        """
        try:
            # Récupérer la police actuelle
            current_font = self.font_var.get()
            
            selection_ranges = self.text_area.tag_ranges(tk.SEL)
            if selection_ranges:
                start, end = selection_ranges
                
                # Récupérer les styles actuels
                styles = self.get_active_styles(start)
                styles["size"] = size
                
                # Créer le tag composite
                composite_tag = self.get_composite_tag(
                    styles["font"],
                    size,
                    styles["bold"],
                    styles["italic"],
                    styles["underline"]
                )
                
                # Supprimer les tags de police existants
                for tag in list(self.text_area.tag_names(start)):
                    if tag.startswith("font_"):
                        self.text_area.tag_remove(tag, start, end)
                
                # Appliquer le nouveau tag composite
                self.text_area.tag_add(composite_tag, start, end)
            else:
                # Sans sélection, mettre à jour les styles actifs pour les prochaines saisies
                self.font_size_var.set(size)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la taille {size}: {e}")
    
    def insert_variable(self):
        """Insère une variable à la position du curseur"""
        variable = self.variable_var.get()
        if variable:
            var_text = f"{{{variable}}}"
            self.text_area.insert(tk.INSERT, var_text)
            insert_pos = self.text_area.index(tk.INSERT)
            start_pos = f"insert-{len(var_text)}c"
            self.text_area.tag_add("variable", start_pos, insert_pos)
    
    def show_more_options(self):
        """Affiche un menu avec plus d'options de mise en forme"""
        try:
            if self.more_options_menu:
                self.more_options_menu.destroy()
            self.more_options_menu = tk.Menu(self, tearoff=0)
            self.more_options_menu.add_command(label="Surligner", command=self.highlight_text)
            self.more_options_menu.add_command(label="Barré", command=self.strikethrough_text)
            self.more_options_menu.add_separator()
            self.more_options_menu.add_command(label="Indentation ▶", command=lambda: self.change_indentation(1))
            self.more_options_menu.add_command(label="Désindentation ◀", command=lambda: self.change_indentation(-1))
            self.more_options_menu.add_separator()
            self.more_options_menu.add_command(label="Insérer une image", command=self.insert_image)
            self.more_options_menu.add_separator()
            self.more_options_menu.add_command(label="Insérer une ligne horizontale", command=self.insert_horizontal_line)
            self.more_options_menu.add_command(label="Insérer un saut de page", command=self.insert_page_break)
            button = self.more_options_btn
            x = button.winfo_rootx()
            y = button.winfo_rooty() + button.winfo_height()
            self.more_options_menu.post(x, y)
            self.bind_all("<Button-1>", self.close_more_options_menu, add="+")
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du menu d'options: {e}")
    
    def close_more_options_menu(self, event=None):
        """Ferme le menu 'Plus d'options'"""
        if self.more_options_menu:
            self.more_options_menu.unpost()
            self.unbind_all("<Button-1>")
    
    def highlight_text(self):
        """Surligne le texte sélectionné"""
        color = colorchooser.askcolor(title="Choisir une couleur de surbrillance")
        if color[1]:
            try:
                # Créer un tag pour cette couleur de fond
                bg_color_tag = f"bg-color-{color[1].replace('#', '')}"
                self.text_area.tag_configure(bg_color_tag, background=color[1])
                
                # Appliquer la surbrillance au texte sélectionné
                selection_ranges = self.text_area.tag_ranges(tk.SEL)
                if selection_ranges:
                    start, end = selection_ranges
                    
                    # Supprimer les autres tags de couleur de fond
                    for tag in self.text_area.tag_names(start):
                        if tag.startswith("bg-color-"):
                            self.text_area.tag_remove(tag, start, end)
                    
                    # Appliquer la nouvelle couleur de fond
                    self.text_area.tag_add(bg_color_tag, start, end)
                else:
                    logger.info("Aucun texte sélectionné pour la surbrillance")
            except Exception as e:
                logger.error(f"Erreur lors de l'application de la surbrillance: {e}")
    
    def strikethrough_text(self):
        """Barre le texte sélectionné"""
        try:
            selection_ranges = self.text_area.tag_ranges(tk.SEL)
            if selection_ranges:
                start, end = selection_ranges
                
                # Vérifier si le texte est déjà barré
                if "strikethrough" in self.text_area.tag_names(start):
                    self.text_area.tag_remove("strikethrough", start, end)
                else:
                    self.text_area.tag_add("strikethrough", start, end)
            else:
                logger.info("Aucun texte sélectionné pour barrer")
        except Exception as e:
            logger.error(f"Erreur lors de l'application du barré: {e}")
    
    def change_indentation(self, delta):
        """Modifie l'indentation du paragraphe actuel
        
        Args:
            delta: Valeur positive pour augmenter et négative pour diminuer l'indentation
        """
        try:
            insert_pos = self.text_area.index(tk.INSERT)
            line_start = self.text_area.index(f"{insert_pos} linestart")
            line_end = self.text_area.index(f"{insert_pos} lineend")
            line_content = self.text_area.get(line_start, line_end)
            
            if delta > 0:
                new_line = "    " + line_content
            elif delta < 0:
                new_line = re.sub(r'^(    )', '', line_content)
            
            self.text_area.delete(line_start, line_end)
            self.text_area.insert(line_start, new_line)
        except Exception as e:
            logger.error(f"Erreur lors du changement d'indentation: {e}")
    
    def insert_horizontal_line(self):
        """Insère une ligne horizontale"""
        try:
            self.text_area.insert(tk.INSERT, "\n" + "-" * 40 + "\n")
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion d'une ligne horizontale: {e}")
    
    def insert_page_break(self):
        """Insère un saut de page"""
        try:
            self.text_area.insert(tk.INSERT, "\n" + "=" * 40 + "\n")
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion d'un saut de page: {e}")
    
    def update_toolbar_state(self, event=None):
        """Met à jour l'état des boutons de la barre d'outils en fonction de la sélection"""
        try:
            # Récupérer les styles actifs à la position actuelle
            styles = self.get_active_styles()
            
            # Mettre à jour l'état des boutons
            self.update_button_state(self.bold_btn, styles["bold"])
            self.update_button_state(self.italic_btn, styles["italic"])
            self.update_button_state(self.underline_btn, styles["underline"])
            
            # Mettre à jour les menus déroulants
            if styles["font"] in self.available_fonts:
                self.font_var.set(styles["font"])
            
            if styles["size"] in self.font_sizes:
                self.font_size_var.set(styles["size"])
            
            # Mettre à jour les boutons d'alignement
            self.update_button_state(self.align_left_btn, styles["alignment"] == "left")
            self.update_button_state(self.align_center_btn, styles["alignment"] == "center")
            self.update_button_state(self.align_right_btn, styles["alignment"] == "right")
            
            # Mettre à jour le bouton de couleur
            if styles["color"]:
                self.color_btn.configure(fg_color=styles["color"])
            else:
                self.color_btn.configure(fg_color=None)  # Réinitialiser à la couleur par défaut
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'état de la barre d'outils: {e}")
    
    def update_button_state(self, button, active):
        """Met à jour l'apparence d'un bouton en fonction de son état actif/inactif"""
        try:
            if active:
                button.configure(fg_color="blue")
            else:
                button.configure(fg_color=None)  # Réinitialiser à la couleur par défaut
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'état du bouton: {e}")
    
    def set_content(self, content):
        """
        Définit le contenu de l'éditeur
        
        Args:
            content: Contenu à définir (peut être du HTML)
        """
        try:
            # Vider le contenu actuel
            self.text_area.delete("1.0", tk.END)
            
            # Vérifier s'il s'agit de HTML
            if content and (content.strip().startswith("<html") or content.strip().startswith("<!DOCTYPE")):
                # Traiter le contenu HTML
                soup = BeautifulSoup(content, 'html.parser')
                current_pos = "1.0"
                
                # Extraire les balises d'image
                images = soup.find_all('img')
                for img in images:
                    # Récupérer les attributs de l'image
                    src = img.get('src', '')
                    alt = img.get('alt', 'Image')
                    width = img.get('width', '200')
                    height = img.get('height', '150')
                    
                    # Traiter les images en base64
                    if src.startswith('data:image/'):
                        try:
                            # Extraire le type et les données
                            header, data = src.split(',', 1)
                            mime_type = header.split(';')[0].split(':')[1]
                            img_ext = mime_type.split('/')[1]
                            
                            # Créer une image temporaire
                            img_data = base64.b64decode(data)
                            img_file = io.BytesIO(img_data)
                            pil_img = Image.open(img_file)
                            
                            # Redimensionner si nécessaire
                            try:
                                w = int(width)
                                h = int(height)
                                if w > 0 and h > 0:
                                    pil_img = pil_img.resize((w, h), Image.LANCZOS)
                            except:
                                pass
                            
                            # Convertir en PhotoImage pour l'affichage
                            photo = ImageTk.PhotoImage(pil_img)
                            
                            # Créer un identifiant unique pour l'image
                            img_id = f"img_base64_{len(self._tag_cache)}"
                            
                            # Stocker l'image pour éviter qu'elle ne soit supprimée par le garbage collector
                            self._tag_cache[img_id] = photo
                            
                            # Insérer l'image dans le texte
                            self.text_area.image_create(current_pos, image=photo)
                            
                            # Créer un tag pour l'image avec les informations nécessaires
                            img_tag = f"img_{current_pos.replace('.', '_')}"
                            self.text_area.tag_add(img_tag, current_pos)
                            
                            # Stocker les métadonnées de l'image
                            self._tag_cache[img_tag] = {
                                "src": src,
                                "width": w,
                                "height": h,
                                "alt": alt
                            }
                            
                            # Mettre à jour la position courante
                            current_pos = self.text_area.index(f"{current_pos}+1c")
                            
                            # Remplacer l'image par un espace dans le contenu HTML pour ne pas la traiter à nouveau
                            img.replace_with(" ")
                            
                        except Exception as img_error:
                            logger.error(f"Erreur lors du chargement de l'image base64: {img_error}")
                
                # Traiter le reste du contenu paragraphe par paragraphe
                for paragraph in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    paragraph_text = paragraph.get_text()
                    if not paragraph_text.strip():
                        continue
                    
                    # Insérer le texte
                    self.text_area.insert(current_pos, paragraph_text + "\n")
                    
                    # Récupérer la position avant et après l'insertion
                    start_pos = current_pos
                    current_pos = self.text_area.index(f"{start_pos}+{len(paragraph_text)}c")
                    
                    # Appliquer les styles
                    if paragraph.find('strong') or paragraph.find('b'):
                        self.text_area.tag_add("bold", start_pos, current_pos)
                    
                    if paragraph.find('em') or paragraph.find('i'):
                        self.text_area.tag_add("italic", start_pos, current_pos)
                    
                    if paragraph.find('u'):
                        self.text_area.tag_add("underline", start_pos, current_pos)
                    
                    if paragraph.find('strike') or paragraph.find('s'):
                        self.text_area.tag_add("strike", start_pos, current_pos)
                    
                    if paragraph.find('mark'):
                        self.text_area.tag_add("highlight", start_pos, current_pos)
                    
                    # Traiter l'alignement
                    if 'style' in paragraph.attrs:
                        paragraph_style = paragraph['style']
                        if 'text-align: center' in paragraph_style:
                            self.text_area.tag_add("center", start_pos, current_pos)
                        elif 'text-align: right' in paragraph_style:
                            self.text_area.tag_add("right", start_pos, current_pos)
                        else:
                            self.text_area.tag_add("left", start_pos, current_pos)
                    
                    # Mettre à jour la position courante pour le prochain paragraphe
                    current_pos = self.text_area.index(f"{current_pos}+1c")
            else:
                # Si ce n'est pas du HTML, insérer comme texte brut
                self.text_area.insert(tk.END, content)
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement du contenu: {e}")
            # En cas d'erreur, charger le contenu brut
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, content)
    
    def get_content(self):
        """Retourne le contenu actuel de l'éditeur de texte"""
        try:
            return self.get_html_content()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du contenu: {e}")
            return self.text_area.get("1.0", tk.END)

    def add_variables(self, variables):
        """
        Ajoute des variables à la liste des variables disponibles
        
        Args:
            variables: Liste des variables à ajouter
        """
        try:
            # Mettre à jour la liste des variables
            self.variable_options.extend(variables)
            
            # Mettre à jour le menu déroulant des variables
            if hasattr(self, 'variable_dropdown'):
                self.variable_dropdown.configure(values=self.variable_options)
            
            logger.info(f"{len(variables)} variables ajoutées à l'éditeur")
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des variables: {e}")

    def get_html_content(self):
        """
        Convertit le contenu de l'éditeur en HTML
        
        Returns:
            str: Contenu au format HTML
        """
        try:
            html_content = []
            current_paragraph = []
            last_pos = "1.0"
            
            logger.info("Début de la conversion en HTML")
            # Vérifier les images stockées dans le cache
            image_tags = [tag for tag in self._tag_cache.keys() if tag.startswith("img_")]
            logger.info(f"Nombre d'images dans le cache: {len(image_tags)}")
            
            # Parcourir tout le contenu en identifiant les images et le texte
            for pos in range(1, int(self.text_area.index(tk.END).split('.')[0]) + 1):
                line_start = f"{pos}.0"
                if pos == int(self.text_area.index(tk.END).split('.')[0]):
                    line_end = tk.END
                else:
                    line_end = f"{pos}.end"
                
                # Vérifier les dumps pour les images
                dump_info = self.text_area.dump(line_start, line_end, tag=True, image=True, text=True)
                for dump_type, dump_val, index in dump_info:
                    if dump_type == "image":
                        # C'est une image, trouver le tag correspondant
                        img_tags = [tag for tag in self.text_area.tag_names(index) if tag.startswith("img_")]
                        logger.info(f"Image trouvée à la position {index} avec tags: {img_tags}")
                        
                        if img_tags and img_tags[0] in self._tag_cache:
                            img_data = self._tag_cache[img_tags[0]]
                            logger.info(f"Données de l'image trouvées dans le cache: {img_data.get('src', '')[:30]}...")
                            
                            # Ajouter le paragraphe actuel s'il y en a un
                            if current_paragraph:
                                html_content.append("<p>" + "".join(current_paragraph) + "</p>")
                                current_paragraph = []
                            
                            # Ajouter l'image
                            img_html = f'<img src="{img_data["src"]}" alt="{img_data["alt"]}" '
                            img_html += f'width="{img_data["width"]}" height="{img_data["height"]}" />'
                            html_content.append(img_html)
                            logger.info(f"Balise image HTML ajoutée: {img_html[:50]}...")
                        else:
                            logger.warning(f"Image trouvée mais pas de données dans le cache pour les tags: {img_tags}")
                    
                    elif dump_type == "text":
                        # Ignorer les sauts de ligne à la fin des paragraphes
                        if dump_val == "\n":
                            if current_paragraph:
                                html_content.append("<p>" + "".join(current_paragraph) + "</p>")
                                current_paragraph = []
                            continue
                        
                        # Traiter les tags pour ce segment de texte
                        tags = self.text_area.tag_names(index)
                        text_val = dump_val
                        
                        # Appliquer les styles
                        if "bold" in tags:
                            text_val = f"<strong>{text_val}</strong>"
                        if "italic" in tags:
                            text_val = f"<em>{text_val}</em>"
                        if "underline" in tags:
                            text_val = f"<u>{text_val}</u>"
                        if "strike" in tags:
                            text_val = f"<s>{text_val}</s>"
                        if "highlight" in tags:
                            text_val = f'<mark>{text_val}</mark>'
                        if "variable" in tags:
                            text_val = f'<span class="variable">{text_val}</span>'
                        
                        # Alignement
                        if "right" in tags:
                            text_val = f'<span style="text-align: right">{text_val}</span>'
                        elif "center" in tags:
                            text_val = f'<span style="text-align: center">{text_val}</span>'
                        
                        current_paragraph.append(text_val)
            
            # Ajouter le dernier paragraphe s'il y en a un
            if current_paragraph:
                html_content.append("<p>" + "".join(current_paragraph) + "</p>")
            
            # Assembler le tout dans un document HTML
            final_html = "<html><body>" + "".join(html_content) + "</body></html>"
            
            # Vérifier si le HTML contient des images
            img_count = final_html.count("<img ")
            logger.info(f"HTML final contient {img_count} balises <img>")
            if img_count > 0:
                logger.info(f"Exemple de balise <img> dans le HTML: {final_html[final_html.find('<img '):final_html.find('/>')+2]}")
            
            # Journaliser un échantillon du HTML final pour le débogage
            html_preview = final_html[:1000] + "..." if len(final_html) > 1000 else final_html
            logger.info(f"HTML final (aperçu): {html_preview}")
            
            return final_html
            
        except Exception as e:
            logger.error(f"Erreur lors de la conversion en HTML: {e}")
            # En cas d'erreur, retourner le contenu brut
            content = self.text_area.get("1.0", tk.END)
            return content  # En cas d'erreur, retourner le contenu brut

    def insert_image(self):
        """
        Insère une image à la position du curseur
        L'image est sélectionnée par l'utilisateur via une boîte de dialogue de fichier
        """
        try:
            # Ouvrir la boîte de dialogue de sélection de fichier
            file_path = filedialog.askopenfilename(
                title="Sélectionner une image",
                filetypes=[
                    ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                    ("Tous les fichiers", "*.*")
                ]
            )
            
            if not file_path:
                return  # L'utilisateur a annulé
            
            # Vérifier la taille de l'image
            img = Image.open(file_path)
            max_width = 800  # Largeur maximale en pixels
            max_height = 600  # Hauteur maximale en pixels
            
            # Redimensionner si l'image est trop grande
            width, height = img.size
            if width > max_width or height > max_height:
                ratio = min(max_width / width, max_height / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Créer un identifiant unique pour l'image
            img_id = f"img_{os.path.basename(file_path).replace('.', '_')}_{len(self._tag_cache)}"
            
            # Convertir l'image en format PhotoImage pour l'affichage
            photo = ImageTk.PhotoImage(img)
            
            # Stocker l'image pour éviter qu'elle ne soit supprimée par le garbage collector
            self._tag_cache[img_id] = photo
            
            # Insérer l'image dans le texte à la position actuelle du curseur
            current_index = self.text_area.index(tk.INSERT)
            self.text_area.image_create(current_index, image=photo)
            
            # Stocker le chemin de l'image pour la récupération lors de la sauvegarde du contenu
            # Encodage de l'image en base64 pour pouvoir la stocker dans le HTML
            with open(file_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Créer un tag pour l'image avec les informations nécessaires
            img_tag = f"img_{current_index.replace('.', '_')}"
            self.text_area.tag_add(img_tag, current_index)
            self.text_area.tag_configure(img_tag, foreground='blue')  # Marquer visuellement pour le debug
            
            # Stocker les métadonnées de l'image
            file_ext = os.path.splitext(file_path)[1][1:].lower()
            mime_type = f"image/{file_ext}"
            if file_ext == "jpg":
                mime_type = "image/jpeg"
            
            # Stocker les informations sur l'image dans le cache
            self._tag_cache[img_tag] = {
                "src": f"data:{mime_type};base64,{img_data}",
                "width": width,
                "height": height,
                "alt": os.path.basename(file_path)
            }
            
            logger.info(f"Image insérée: {os.path.basename(file_path)}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion de l'image: {e}")
            from tkinter import messagebox
            messagebox.showerror("Erreur", f"Impossible d'insérer l'image: {str(e)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = ctk.CTk()
    root.title("Vynal Docs Automator - RichTextEditor")
    editor = RichTextEditor(root, initial_content="Bienvenue dans l'éditeur de texte enrichi !")
    editor.pack(fill=ctk.BOTH, expand=True)
    root.mainloop()