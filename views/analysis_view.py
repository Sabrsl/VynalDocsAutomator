import customtkinter as ctk
from typing import Optional, Dict, List, Any
import logging
from doc_analyzer import DocumentAnalyzer
from doc_analyzer.ui.analysis_widgets import AnalysisResultWidget
from utils.ui_components import LoadingSpinner
import os
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time

logger = logging.getLogger("Vynal Docs Automator.views.analysis_view")

class AnalysisView:
    """
    Vue pour l'analyse des documents
    Permet d'analyser les documents et d'afficher les résultats
    """
    
    def __init__(self, parent: ctk.CTkFrame, app_model: Any):
        """
        Initialise la vue d'analyse
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        
        # Créer le cadre principal
        self.frame = ctk.CTkFrame(parent)
        
        # Initialiser l'analyseur de documents
        try:
            self.doc_analyzer = DocumentAnalyzer()
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de l'analyseur: {e}")
            self.doc_analyzer = None
        
        # Variables d'état
        self.current_document = None
        self.analysis_results = {}
        self.is_analyzing = False
        
        # Créer les widgets
        self.create_widgets()
        
        logger.info("Vue d'analyse initialisée")
    
    def show(self):
        """Affiche la vue"""
        if self.frame is not None:
            self.frame.pack(fill=ctk.BOTH, expand=True)
            logger.debug("Vue d'analyse affichée")
    
    def hide(self):
        """Cache la vue"""
        if self.frame is not None:
            self.frame.pack_forget()
            logger.debug("Vue d'analyse masquée")
    
    def update_view(self):
        """Met à jour la vue"""
        # Mettre à jour l'état des boutons selon la disponibilité de l'analyseur
        if self.doc_analyzer is None:
            self.analyze_btn.configure(state="disabled")
            self.update_status("Analyseur non disponible")
        else:
            self.analyze_btn.configure(state="normal")
        
        # S'assurer que le bouton d'analyse par lot reste toujours désactivé
        self.batch_analyze_btn.configure(
            state="disabled",
            fg_color=("gray75", "gray25")
        )
    
    def create_widgets(self):
        """
        Crée les widgets de la vue
        """
        # Barre d'outils avec un style moderne
        self.toolbar = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.toolbar.pack(fill=ctk.X, padx=20, pady=(20, 10))
        
        # Titre de la section
        title_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        title_frame.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="Analyse de Documents",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title_label.pack(side=ctk.LEFT)
        
        # Description
        description = ctk.CTkLabel(
            title_frame,
            text="Analysez vos documents et extrayez automatiquement les informations importantes",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60")
        )
        description.pack(side=ctk.LEFT, padx=20)
        
        # Boutons d'action dans un cadre séparé
        button_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        button_frame.pack(side=ctk.RIGHT)
        
        # Bouton Analyser avec icône et style moderne
        self.analyze_btn = ctk.CTkButton(
            button_frame,
            text="Analyser un document",
            command=self.analyze_document,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            corner_radius=8,
            border_spacing=10,
            fg_color=("#2D5BA3", "#1A3B6E"),  # Bleu professionnel
            hover_color=("#234780", "#142D54")
        )
        self.analyze_btn.pack(side=ctk.LEFT, padx=(0, 10))
        
        # Bouton Analyser en lot (désactivé)
        self.batch_analyze_btn = ctk.CTkButton(
            button_frame,
            text="Analyse par lot",
            command=self.batch_analyze,
            font=ctk.CTkFont(size=13),
            height=40,
            corner_radius=8,
            border_spacing=10,
            state="disabled",
            fg_color=("gray75", "gray25"),
            hover_color=("gray65", "gray35")
        )
        self.batch_analyze_btn.pack(side=ctk.LEFT)
        
        # Indicateur de chargement avec style moderne
        self.loading_spinner = LoadingSpinner(button_frame)
        self.loading_spinner.pack(side=ctk.LEFT, padx=15)
        self.loading_spinner.hide()
        
        # Zone principale de contenu avec un style moderne
        self.content_frame = ctk.CTkScrollableFrame(
            self.frame,
            fg_color=("gray95", "gray10"),
            corner_radius=15
        )
        self.content_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=(10, 20))
        
        # Message d'accueil moderne
        welcome_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        welcome_frame.pack(fill=ctk.BOTH, expand=True, padx=40, pady=40)
        
        # Icône ou illustration
        icon_label = ctk.CTkLabel(
            welcome_frame,
            text="📄",  # Vous pouvez remplacer par une vraie image
            font=ctk.CTkFont(size=48),
            text_color=("gray40", "gray60")
        )
        icon_label.pack(pady=(0, 20))
        
        # Message principal
        self.no_analysis_label = ctk.CTkLabel(
            welcome_frame,
            text="Commencez par analyser un document",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("gray20", "gray80")
        )
        self.no_analysis_label.pack()
        
        # Sous-titre avec instructions
        instructions_label = ctk.CTkLabel(
            welcome_frame,
            text="Cliquez sur 'Analyser un document' pour commencer\nFormats supportés : PDF, DOCX, TXT",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60")
        )
        instructions_label.pack(pady=(10, 0))
        
        # Zone des résultats (initialement cachée)
        self.results_frame = ctk.CTkFrame(self.content_frame)
        
        # Barre d'état moderne
        self.status_bar = ctk.CTkFrame(
            self.frame,
            height=30,
            fg_color=("gray90", "gray15")
        )
        self.status_bar.pack(side=ctk.BOTTOM, fill=ctk.X)
        
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Prêt",
            font=ctk.CTkFont(size=12),
            anchor="w",
            text_color=("gray40", "gray60")
        )
        self.status_label.pack(side=ctk.LEFT, padx=15, pady=5)
    
    def analyze_document(self):
        """Lance l'analyse d'un document"""
        if self.doc_analyzer is None:
            self.show_error("Analyseur non disponible", "L'analyseur de documents n'est pas initialisé.")
            return
        
        try:
            # Ouvrir la boîte de dialogue de sélection de fichier
            file_path = ctk.filedialog.askopenfilename(
                title="Sélectionner un document à analyser",
                filetypes=[
                    ("Documents", "*.pdf;*.doc;*.docx;*.txt"),
                    ("PDF", "*.pdf"),
                    ("Word", "*.doc;*.docx"),
                    ("Texte", "*.txt"),
                    ("Tous les fichiers", "*.*")
                ]
            )
            
            if not file_path:
                return  # L'utilisateur a annulé
            
            # Afficher le chargement
            self.show_loading(True)
            filename = os.path.basename(file_path)
            self.update_status(f"Analyse de {filename} en cours...")
            
            # Créer un label temporaire pour informer l'utilisateur
            info_label = ctk.CTkLabel(
                self.content_frame,
                text=f"Analyse de {filename} en cours...\nCette opération peut prendre quelques instants.",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray70")
            )
            # Cacher le message "aucune analyse" temporairement
            self.no_analysis_label.pack_forget()
            info_label.pack(pady=40)
            
            # Lancer l'analyse dans un thread séparé pour ne pas bloquer l'interface
            def analyze():
                try:
                    # Analyser le document
                    results = self.doc_analyzer.analyze_document(file_path)
                    
                    if results:
                        # Supprimer le message temporaire
                        self.frame.after(0, lambda: info_label.destroy())
                        # Mettre à jour l'interface dans le thread principal
                        self.frame.after(0, lambda: self.display_results(results))
                        self.frame.after(0, lambda: self.update_status(f"Analyse de {filename} terminée"))
                    else:
                        self.frame.after(0, lambda: info_label.destroy())
                        self.frame.after(0, lambda: self.no_analysis_label.pack(pady=40))
                        self.frame.after(0, lambda: self.show_error(
                            "Erreur d'analyse",
                            "Impossible d'analyser le document. Vérifiez qu'il est dans un format supporté."
                        ))
                except Exception as error:
                    logger.error(f"Erreur lors de l'analyse du document {file_path}: {error}")
                    self.frame.after(0, lambda: info_label.destroy())
                    self.frame.after(0, lambda: self.no_analysis_label.pack(pady=40))
                    self.frame.after(0, lambda err=error: self.show_error(
                        "Erreur d'analyse",
                        f"Une erreur est survenue lors de l'analyse : {str(err)}"
                    ))
                finally:
                    self.frame.after(0, lambda: self.show_loading(False))
            
            # Lancer l'analyse dans un thread
            thread = threading.Thread(target=analyze)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.show_error("Erreur", f"Une erreur est survenue : {str(e)}")
            self.show_loading(False)
    
    def batch_analyze(self):
        """Lance l'analyse par lot de documents"""
        try:
            # Sélectionner les fichiers
            file_paths = ctk.filedialog.askopenfilenames(
                title="Sélectionner les documents à analyser",
                filetypes=[
                    ("Documents", "*.pdf;*.doc;*.docx;*.txt"),
                    ("PDF", "*.pdf"),
                    ("Word", "*.doc;*.docx"),
                    ("Texte", "*.txt"),
                    ("Tous les fichiers", "*.*")
                ]
            )
            
            if not file_paths:
                return  # L'utilisateur a annulé
            
            # Afficher le chargement
            self.show_loading(True)
            
            # Créer le cadre pour l'analyse par lot
            batch_frame = ctk.CTkFrame(self.content_frame)
            batch_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            
            # Titre du lot
            batch_title = ctk.CTkLabel(
                batch_frame,
                text="Analyse par lot en cours...",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            batch_title.pack(pady=(0, 10))
            
            # Cadre de progression
            progress_frame = ctk.CTkFrame(batch_frame)
            progress_frame.pack(fill=ctk.X, padx=10, pady=5)
            
            progress_bar = ctk.CTkProgressBar(progress_frame)
            progress_bar.pack(fill=ctk.X, side=ctk.LEFT, expand=True, padx=(0, 10))
            progress_bar.set(0)
            
            progress_label = ctk.CTkLabel(
                progress_frame,
                text="0%",
                font=ctk.CTkFont(size=12)
            )
            progress_label.pack(side=ctk.RIGHT)
            
            # Label pour le fichier en cours
            current_file_label = ctk.CTkLabel(
                batch_frame,
                text="Préparation de l'analyse...",
                font=ctk.CTkFont(size=12)
            )
            current_file_label.pack(pady=5)
            
            # Liste des résultats
            results_frame = ctk.CTkScrollableFrame(batch_frame)
            results_frame.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
            
            # Dictionnaire pour suivre le statut de chaque fichier
            file_status = {}
            
            # Créer les labels de statut pour chaque fichier
            for file_path in file_paths:
                file_frame = ctk.CTkFrame(results_frame)
                file_frame.pack(fill=ctk.X, padx=5, pady=2)
                
                filename = os.path.basename(file_path)
                name_label = ctk.CTkLabel(
                    file_frame,
                    text=filename,
                    font=ctk.CTkFont(size=12),
                    anchor="w"
                )
                name_label.pack(side=ctk.LEFT, padx=5)
                
                status_label = ctk.CTkLabel(
                    file_frame,
                    text="En attente",
                    font=ctk.CTkFont(size=12),
                    text_color=("gray50", "gray70")
                )
                status_label.pack(side=ctk.RIGHT, padx=5)
                
                file_status[file_path] = {
                    "frame": file_frame,
                    "name_label": name_label,
                    "status_label": status_label
                }
            
            def analyze_batch():
                """Fonction d'analyse par lot exécutée dans un thread séparé"""
                try:
                    total_files = len(file_paths)
                    success_count = 0
                    fail_count = 0
                    
                    for i, file_path in enumerate(file_paths, 1):
                        try:
                            # Mettre à jour la progression
                            progress = i / total_files
                            self.frame.after(0, lambda p=progress: progress_bar.set(p))
                            self.frame.after(0, lambda p=progress: progress_label.configure(
                                text="{:.0%}".format(p)
                            ))
                            
                            # Mettre à jour le fichier en cours
                            filename = os.path.basename(file_path)
                            self.frame.after(0, lambda f=filename: current_file_label.configure(
                                text="Analyse de {}".format(f)
                            ))
                            
                            # Mettre à jour le statut du fichier
                            self.frame.after(0, lambda fp=file_path: file_status[fp]["status_label"].configure(
                                text="En cours",
                                text_color=("blue", "light blue")
                            ))
                            
                            # Analyser le document
                            results = self.doc_analyzer.analyze_document(file_path)
                            
                            if results:
                                success_count += 1
                                self.frame.after(0, lambda fp=file_path: file_status[fp]["status_label"].configure(
                                    text="Succès",
                                    text_color=("green", "light green")
                                ))
                            else:
                                fail_count += 1
                                self.frame.after(0, lambda fp=file_path: file_status[fp]["status_label"].configure(
                                    text="Échec",
                                    text_color=("red", "red")
                                ))
                        except Exception as e:
                            logger.error("Erreur lors de l'analyse de {}: {}".format(file_path, e))
                            fail_count += 1
                            self.frame.after(0, lambda fp=file_path: file_status[fp]["status_label"].configure(
                                text="Erreur",
                                text_color=("red", "red")
                            ))
                    
                    # Afficher le résumé final
                    summary = "Analyse par lot terminée: {} réussis, {} échoués sur {} documents".format(
                        success_count, fail_count, total_files
                    )
                    self.frame.after(0, lambda: batch_title.configure(text=summary))
                    self.frame.after(0, lambda: current_file_label.configure(text="Traitement terminé"))
                    
                    status_message = "Analyse par lot terminée: {}/{} documents traités avec succès".format(
                        success_count, total_files
                    )
                    self.frame.after(0, lambda: self.update_status(status_message))
                    self.frame.after(0, lambda: self.show_loading(False))
                
                except Exception as e:
                    error_message = "Une erreur est survenue lors de l'analyse par lot : {}".format(str(e))
                    self.frame.after(0, lambda: self.show_error("Erreur d'analyse", error_message))
                    self.frame.after(0, lambda: self.show_loading(False))
            
            # Lancer l'analyse dans un thread
            thread = threading.Thread(target=analyze_batch)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            error_message = "Une erreur est survenue : {}".format(str(e))
            self.show_error("Erreur", error_message)
            self.show_loading(False)
    
    def _extract_from_results(self, results):
        """
        Extrait le texte et les variables des résultats d'analyse
        
        Args:
            results: Résultats de l'analyse
            
        Returns:
            tuple: (texte extrait, variables extraites)
        """
        extracted_text = ""
        extracted_variables = {}
        
        # Vérifier si les résultats sont un dictionnaire
        if not isinstance(results, dict):
            logger.warning(f"Les résultats ne sont pas un dictionnaire: {type(results)}")
            if isinstance(results, str):
                extracted_text = results
            else:
                extracted_text = str(results)
            return extracted_text, extracted_variables
        
        # Vérifier s'il y a une erreur dans les résultats
        if 'error' in results:
            logger.warning(f"Erreur dans les résultats: {results['error']}")
            error_message = results.get('error', "Erreur inconnue lors de l'analyse")
            
            # Utiliser le texte d'erreur comme texte extrait
            extracted_text = f"ERREUR: {error_message}\n\n"
            
            # Si un texte est disponible malgré l'erreur, l'ajouter
            if 'text' in results and results['text']:
                extracted_text += results['text']
            # Sinon, essayer de lire le contenu du fichier si c'est un fichier texte
            elif 'file_path' in results:
                file_path = results['file_path']
                if os.path.exists(file_path) and file_path.lower().endswith(('.txt', '.md', '.csv')):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            file_content = f.read()
                        extracted_text += f"\nContenu du fichier:\n{file_content}"
                    except Exception as e:
                        logger.error(f"Erreur lors de la lecture du fichier: {e}")
            
            # Ajouter des variables par défaut pour permettre la création de modèle
            if 'file_path' in results:
                filename = os.path.basename(results['file_path'])
                extracted_variables = {
                    "document_name": filename,
                    "document_type": "autre",
                    "date": "01/01/2023",
                    "error": error_message
                }
            
            return extracted_text, extracted_variables
        
        # Extraire le texte des résultats
        if 'text' in results:
            extracted_text = results['text']
        
        # Extraire les variables des différentes sections des résultats
        sections = ['personal_data', 'legal_data', 'identity_data', 'contract_data', 'business_data']
        
        for section in sections:
            if section in results and isinstance(results[section], dict):
                # Ajouter les variables de cette section
                for key, value in results[section].items():
                    if isinstance(value, (str, int, float, bool)):
                        extracted_variables[key] = value
                    elif isinstance(value, dict):
                        # Pour les dictionnaires imbriqués, aplatir avec des préfixes
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, (str, int, float, bool)):
                                extracted_variables[f"{key}_{sub_key}"] = sub_value
        
        # Si des variables sont directement disponibles, les utiliser
        if 'variables' in results and isinstance(results['variables'], dict):
            for key, value in results['variables'].items():
                if isinstance(value, (str, int, float, bool)):
                    extracted_variables[key] = value
        
        # Si aucun texte n'a été extrait, utiliser un message par défaut
        if not extracted_text:
            logger.warning("Aucun texte extrait des résultats")
            extracted_text = "Aucun texte n'a pu être extrait de ce document."
        
        # Si aucune variable n'a été extraite, utiliser des valeurs par défaut
        if not extracted_variables and 'file_path' in results:
            filename = os.path.basename(results['file_path'])
            extracted_variables = {
                "document_name": filename,
                "document_type": "autre",
                "date": "01/01/2023"
            }
        
        return extracted_text, extracted_variables

    def display_results(self, results):
        """Affiche les résultats de l'analyse"""
        try:
            # Nettoyer la vue actuelle
            self.clean_view()
            
            # Créer un frame pour les résultats avec un style moderne
            results_frame = ctk.CTkFrame(
                self.content_frame,
                fg_color=("gray95", "gray10"),
                corner_radius=15
            )
            results_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)
            
            # En-tête des résultats
            header_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
            header_frame.pack(fill=ctk.X, padx=20, pady=(20, 10))
            
            # Afficher le nom du fichier avec une icône
            filename = os.path.basename(results.get('file_path', 'Document'))
            file_type = filename.split('.')[-1].lower() if '.' in filename else ''
            
            # Choisir l'icône en fonction du type de fichier
            file_icon = "📄"
            if file_type == 'pdf':
                file_icon = "📕"
            elif file_type in ['doc', 'docx']:
                file_icon = "📘"
            elif file_type == 'txt':
                file_icon = "📝"
            
            file_label = ctk.CTkLabel(
                header_frame, 
                text=f"{file_icon} {filename}",
                font=ctk.CTkFont(size=18, weight="bold"),
                anchor="w"
            )
            file_label.pack(side=ctk.LEFT)
            
            # Frame pour les boutons d'action
            action_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            action_frame.pack(side=ctk.RIGHT)
            
            # Bouton pour créer un modèle avec style moderne
            create_template_btn = ctk.CTkButton(
                action_frame,
                text="✨ Créer un modèle",
                command=lambda: self._show_template_form(results),
                font=ctk.CTkFont(size=13),
                height=32,
                corner_radius=8,
                fg_color=("#2D5BA3", "#1A3B6E"),
                hover_color=("#234780", "#142D54")
            )
            create_template_btn.pack(side=ctk.RIGHT, padx=5)
            
            # Extraire le texte et les variables
            extracted_text, extracted_variables = self._extract_from_results(results)
            
            # Créer un onglet pour l'affichage avec style moderne
            tabs_frame = ctk.CTkTabview(
                results_frame,
                fg_color=("gray90", "gray15"),
                segmented_button_fg_color=("gray85", "gray20"),
                segmented_button_selected_color=("#2D5BA3", "#1A3B6E"),
                segmented_button_unselected_hover_color=("gray80", "gray25")
            )
            tabs_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=10)
            
            # Ajouter les onglets
            tabs_frame.add("📝 Texte")
            tabs_frame.add("✏️ Éditeur")
            tabs_frame.add("🔍 Variables")
            
            # Onglet 1: Texte brut avec style moderne
            text_tab = tabs_frame.tab("📝 Texte")
            
            text_widget = ctk.CTkTextbox(
                text_tab,
                wrap=ctk.WORD,
                font=ctk.CTkFont(family="Consolas", size=12),
                fg_color=("white", "gray17"),
                border_width=1,
                border_color=("gray75", "gray30"),
                corner_radius=8
            )
            text_widget.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
            
            # Insérer le contenu avec formatage
            text_widget.insert(ctk.END, extracted_text)
            text_widget.configure(state='disabled')
            
            # Onglet 2: Éditeur de texte riche
            editor_tab = tabs_frame.tab("✏️ Éditeur")
            
            try:
                # Importer l'éditeur de texte riche
                from utils.rich_text_editor import RichTextEditor
                
                # Formater les variables pour l'éditeur
                formatted_variables = []
                for var_name, var_value in extracted_variables.items():
                    var_text = f"{{{{{var_name}}}}}"
                    formatted_variables.append(var_text)
                
                # Créer l'éditeur avec style moderne
                editor = RichTextEditor(
                    editor_tab,
                    initial_content=str(extracted_text),
                    variable_options=formatted_variables,
                    height=400,
                    fg_color=("white", "gray17"),
                    border_color=("gray75", "gray30")
                )
                editor.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
                
                # Configurer le tag pour le surlignage des variables
                editor.text_area.tag_configure("variable_highlight", background="#FFE5B4")
                
                # Surligner les variables dans le texte
                for var_name, var_value in extracted_variables.items():
                    if isinstance(var_value, str):
                        # Rechercher toutes les occurrences de la valeur dans le texte
                        start_pos = "1.0"
                        while True:
                            start_pos = editor.text_area.search(var_value, start_pos, ctk.END, nocase=True)
                            if not start_pos:
                                break
                            end_pos = f"{start_pos}+{len(var_value)}c"
                            editor.text_area.tag_add("variable_highlight", start_pos, end_pos)
                            start_pos = end_pos
                
                # Boutons d'action de l'éditeur
                editor_actions = ctk.CTkFrame(editor_tab, fg_color="transparent")
                editor_actions.pack(fill=ctk.X, padx=10, pady=(0, 10))
                
            except ImportError as e:
                self._show_editor_error(editor_tab, "L'éditeur de texte riche n'est pas disponible.\nVeuillez utiliser l'onglet 'Texte'.")
            except Exception as e:
                self._show_editor_error(editor_tab, f"Impossible de charger l'éditeur:\n{str(e)}")
            
            # Onglet 3: Variables détectées
            variables_tab = tabs_frame.tab("🔍 Variables")
            
            if extracted_variables:
                # Créer une grille pour afficher les variables
                variables_frame = ctk.CTkScrollableFrame(
                    variables_tab,
                    fg_color="transparent"
                )
                variables_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
                
                # En-tête des colonnes
                header_frame = ctk.CTkFrame(variables_frame, fg_color="transparent")
                header_frame.pack(fill=ctk.X, pady=(0, 10))
                
                ctk.CTkLabel(
                    header_frame,
                    text="Variable",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    width=150
                ).pack(side=ctk.LEFT, padx=5)
                
                ctk.CTkLabel(
                    header_frame,
                    text="Valeur",
                    font=ctk.CTkFont(size=12, weight="bold")
                ).pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5)
                
                # Afficher chaque variable dans une ligne
                for var_name, var_value in extracted_variables.items():
                    var_frame = ctk.CTkFrame(variables_frame, fg_color="transparent")
                    var_frame.pack(fill=ctk.X, pady=2)
                    
                    name_label = ctk.CTkLabel(
                        var_frame,
                        text=var_name,
                        font=ctk.CTkFont(size=12),
                        width=150,
                        anchor="w"
                    )
                    name_label.pack(side=ctk.LEFT, padx=5)
                    
                    value_label = ctk.CTkLabel(
                        var_frame,
                        text=str(var_value),
                        font=ctk.CTkFont(size=12),
                        anchor="w"
                    )
                    value_label.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5)
            else:
                # Message si aucune variable détectée
                no_vars_label = ctk.CTkLabel(
                    variables_tab,
                    text="Aucune variable détectée dans ce document",
                    font=ctk.CTkFont(size=14),
                    text_color=("gray40", "gray60")
                )
                no_vars_label.pack(pady=20)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des résultats: {e}")
            self.show_error(
                "Erreur",
                "Une erreur est survenue lors de l'affichage des résultats. Veuillez réessayer."
            )
    
    def _show_editor_error(self, parent, message):
        """Affiche un message d'erreur stylisé pour l'éditeur"""
        error_frame = ctk.CTkFrame(
            parent,
            fg_color=("gray95", "gray10"),
            border_width=1,
            border_color=("red", "#AA4444"),
            corner_radius=8
        )
        error_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        error_icon = ctk.CTkLabel(
            error_frame,
            text="⚠️",
            font=ctk.CTkFont(size=48),
            text_color=("red", "#FF6666")
        )
        error_icon.pack(pady=(20, 10))
        
        error_label = ctk.CTkLabel(
            error_frame,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color=("red", "#FF6666")
        )
        error_label.pack(pady=(0, 20))

    def _create_template_from_editor(self, editor, variables, filename):
        """Crée un modèle à partir du contenu de l'éditeur"""
        try:
            # Récupérer le contenu de l'éditeur
            content = editor.get_content()
            
            # Préparer les données du modèle
            template_data = {
                "name": "Modèle depuis {}".format(filename),
                "type": "autre",
                "description": "Modèle créé à partir de l'analyse de {}".format(filename),
                "content": content,
                "variables": variables,
                "folder": "import",
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Afficher le formulaire de modèle
            self._show_template_form(template_data)
            
        except Exception as e:
            logger.error("Erreur lors de la création du modèle depuis l'éditeur: {}".format(e))
            self.show_error(
                "Erreur",
                "Impossible de créer le modèle à partir de l'éditeur. Veuillez réessayer."
            )

    def _show_template_form(self, results):
        """Affiche le formulaire de modèle avec les résultats de l'analyse"""
        try:
            # Si results est un dictionnaire de données de modèle, l'utiliser directement
            if isinstance(results, dict) and all(k in results for k in ["name", "content", "variables"]):
                template_data = results
            else:
                # Extraire le texte et les variables de manière robuste
                extracted_text, extracted_variables = self._extract_from_results(results)
                
                # Préparer les données du modèle
                filename = os.path.basename(results.get('file_path', 'Document'))
                template_data = {
                    "name": f"Modèle depuis {filename}",
                    "type": "autre",
                    "description": f"Modèle créé à partir de l'analyse de {filename}",
                    "content": extracted_text,
                    "variables": extracted_variables,
                    "folder": "import",
                    "created_at": datetime.datetime.now().isoformat(),
                    "from_analysis": True
                }
            
            # Trouver la fenêtre principale
            root = self.parent
            while hasattr(root, 'master') and root.master is not None:
                root = root.master
            
            # Créer et afficher le formulaire de modèle
            from views.template_view import TemplateFormView
            template_form = TemplateFormView(
                root, 
                self.model,
                template_data=template_data,
                update_view_callback=None
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du formulaire de modèle: {e}")
            self.show_error(
                "Erreur", 
                "Impossible d'ouvrir le formulaire de modèle. Veuillez réessayer."
            )

    def clean_view(self):
        """Nettoie la vue actuelle en supprimant tous les widgets enfants"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Cacher le message "aucune analyse" s'il existe
        if hasattr(self, 'no_analysis_label'):
            self.no_analysis_label.pack_forget()

    def toggle_buttons_state(self):
        """Met à jour l'état des boutons selon les conditions actuelles"""
        if hasattr(self, 'doc_analyzer') and self.doc_analyzer is None:
            self.analyze_btn.configure(
                state="disabled",
                fg_color=("gray70", "gray30")
            )
            self.batch_analyze_btn.configure(
                state="disabled",
                fg_color=("gray70", "gray30")
            )
        else:
            self.analyze_btn.configure(
                state="normal",
                fg_color=("#3B8ED0", "#1F6AA5")
            )
            self.batch_analyze_btn.configure(
                state="disabled",
                fg_color=("gray75", "gray25")
            )

    def _update_document_counter(self):
        """Met à jour le compteur de documents (méthode factice pour compatibilité)"""
        # Cette méthode est un placeholder pour assurer la compatibilité
        # avec le code qui l'appelle, mais n'a pas d'effet dans cette classe
        pass

    def show_loading(self, show: bool = True):
        """
        Affiche ou masque l'indicateur de chargement
        
        Args:
            show: True pour afficher, False pour masquer
        """
        if show:
            self.loading_spinner.show()
            self.analyze_btn.configure(
                state="disabled",
                fg_color=("gray70", "gray30")
            )
            self.batch_analyze_btn.configure(
                state="disabled",
                fg_color=("gray70", "gray30")
            )
        else:
            self.loading_spinner.hide()
            self.analyze_btn.configure(
                state="normal",
                fg_color=("#3B8ED0", "#1F6AA5")
            )
            self.batch_analyze_btn.configure(
                state="disabled",
                fg_color=("gray75", "gray25")
            )

    def show_error(self, title: str, message: str):
        """
        Affiche un message d'erreur
        
        Args:
            title: Titre de l'erreur
            message: Message d'erreur
        """
        messagebox.showerror(title, message)

    def update_status(self, message: str):
        """
        Met à jour le message de statut
        
        Args:
            message: Nouveau message
        """
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)