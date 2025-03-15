#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue des journaux système pour l'interface d'administration
"""

import logging
import customtkinter as ctk
from datetime import datetime, timedelta
import os
import re
import glob

logger = logging.getLogger("VynalDocsAutomator.Admin.SystemLogsView")

class SystemLogsView:
    """
    Vue pour visualiser les journaux système et les événements
    Permet de filtrer, analyser et exporter les logs
    """
    
    def __init__(self, parent, app_model):
        """
        Initialise la vue des journaux système
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        self.current_log_file = None
        self.log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        # Variables pour les filtres
        self.filter_vars = {
            "level": ctk.StringVar(value="ALL"),
            "search": ctk.StringVar(),
            "date_range": ctk.StringVar(value="today")
        }
        
        # Cadre principal de la vue
        self.frame = ctk.CTkFrame(parent)
        
        # Création de l'interface
        self.create_widgets()
        
        # Associer les callbacks aux filtres
        self.filter_vars["level"].trace_add("write", lambda *args: self.apply_filters())
        self.filter_vars["search"].trace_add("write", lambda *args: self.apply_filters())
        self.filter_vars["date_range"].trace_add("write", lambda *args: self.apply_filters())
        
        logger.info("SystemLogsView initialisée")
    
    def create_widgets(self):
        """
        Crée les widgets de la vue des journaux système
        """
        # Cadre pour le titre de la page
        self.header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.header_frame.pack(fill=ctk.X, pady=(0, 10))
        
        # Titre principal
        ctk.CTkLabel(
            self.header_frame,
            text="Journaux système",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side=ctk.LEFT, anchor="w", padx=20, pady=10)
        
        # Bouton d'actualisation
        refresh_btn = ctk.CTkButton(
            self.header_frame,
            text="Actualiser",
            width=100,
            command=self.reload_logs
        )
        refresh_btn.pack(side=ctk.RIGHT, padx=20, pady=10)
        
        # Conteneur principal
        self.main_container = ctk.CTkFrame(self.frame)
        self.main_container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Division en deux zones: filtres à gauche, logs à droite
        self.main_container.columnconfigure(0, weight=1)  # Filtres
        self.main_container.columnconfigure(1, weight=4)  # Logs
        
        # Cadre pour les filtres
        self.filters_frame = ctk.CTkFrame(self.main_container)
        self.filters_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Cadre pour les logs
        self.logs_frame = ctk.CTkFrame(self.main_container)
        self.logs_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Créer les composants de filtrage
        self.create_filters()
        
        # Créer la zone d'affichage des logs
        self.create_logs_view()
    
    def create_filters(self):
        """
        Crée les composants de filtrage des logs
        """
        # Titre de la section
        ctk.CTkLabel(
            self.filters_frame,
            text="Filtres",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=10)
        
        # Sélection du fichier de log
        self.log_file_frame = ctk.CTkFrame(self.filters_frame, fg_color="transparent")
        self.log_file_frame.pack(fill=ctk.X, padx=15, pady=5)
        
        ctk.CTkLabel(
            self.log_file_frame,
            text="Fichier de log:",
            anchor="w"
        ).pack(anchor="w")
        
        self.log_files_dropdown = ctk.CTkOptionMenu(
            self.log_file_frame,
            values=["Chargement..."],
            command=self.on_log_file_changed
        )
        self.log_files_dropdown.pack(fill=ctk.X, pady=5)
        
        # Filtres
        filters_container = ctk.CTkFrame(self.filters_frame, fg_color="transparent")
        filters_container.pack(fill=ctk.X, padx=15, pady=5)
        
        # Filtre par niveau
        level_frame = ctk.CTkFrame(filters_container, fg_color="transparent")
        level_frame.pack(fill=ctk.X, pady=5)
        
        ctk.CTkLabel(
            level_frame,
            text="Niveau:",
            anchor="w"
        ).pack(anchor="w")
        
        # Ajouter "ALL" au début de la liste des niveaux
        level_options = ["ALL"] + self.log_levels
        
        level_dropdown = ctk.CTkOptionMenu(
            level_frame,
            values=level_options,
            variable=self.filter_vars["level"]
        )
        level_dropdown.pack(fill=ctk.X, pady=5)
        
        # Filtre par texte (recherche)
        search_frame = ctk.CTkFrame(filters_container, fg_color="transparent")
        search_frame.pack(fill=ctk.X, pady=5)
        
        ctk.CTkLabel(
            search_frame,
            text="Recherche:",
            anchor="w"
        ).pack(anchor="w")
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Rechercher dans les logs...",
            textvariable=self.filter_vars["search"]
        )
        search_entry.pack(fill=ctk.X, pady=5)
        
        # Filtre par plage de dates
        date_frame = ctk.CTkFrame(filters_container, fg_color="transparent")
        date_frame.pack(fill=ctk.X, pady=5)
        
        ctk.CTkLabel(
            date_frame,
            text="Période:",
            anchor="w"
        ).pack(anchor="w")
        
        date_options = [
            "today",
            "yesterday",
            "last_7_days",
            "last_30_days",
            "all"
        ]
        
        date_dropdown = ctk.CTkOptionMenu(
            date_frame,
            values=date_options,
            variable=self.filter_vars["date_range"]
        )
        date_dropdown.pack(fill=ctk.X, pady=5)
        
        # Bouton d'effacement des filtres
        clear_filters_btn = ctk.CTkButton(
            filters_container,
            text="Effacer les filtres",
            command=self.clear_filters
        )
        clear_filters_btn.pack(fill=ctk.X, pady=10)
        
        # Statistiques des logs
        stats_frame = ctk.CTkFrame(self.filters_frame)
        stats_frame.pack(fill=ctk.X, padx=15, pady=15)
        
        ctk.CTkLabel(
            stats_frame,
            text="Statistiques",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        self.stats_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        self.stats_container.pack(fill=ctk.X, padx=10, pady=5)
        
        # Les statistiques seront ajoutées dynamiquement
        
        # Boutons d'action
        actions_frame = ctk.CTkFrame(self.filters_frame, fg_color="transparent")
        actions_frame.pack(fill=ctk.X, padx=15, pady=10)
        
        export_btn = ctk.CTkButton(
            actions_frame,
            text="Exporter les logs",
            command=self.export_logs
        )
        export_btn.pack(fill=ctk.X, pady=5)
        
        clear_logs_btn = ctk.CTkButton(
            actions_frame,
            text="Nettoyer les anciens logs",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.confirm_clear_old_logs
        )
        clear_logs_btn.pack(fill=ctk.X, pady=5)
    
    def create_logs_view(self):
        """
        Crée la zone d'affichage des logs
        """
        # Titre de la section
        logs_header = ctk.CTkFrame(self.logs_frame, fg_color="transparent")
        logs_header.pack(fill=ctk.X, padx=15, pady=10)
        
        self.logs_title = ctk.CTkLabel(
            logs_header,
            text="Logs système",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.logs_title.pack(side=ctk.LEFT)
        
        self.logs_count = ctk.CTkLabel(
            logs_header,
            text="0 entrées",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.logs_count.pack(side=ctk.RIGHT)
        
        # Zone de texte pour afficher les logs
        self.logs_container = ctk.CTkScrollableFrame(self.logs_frame)
        self.logs_container.pack(fill=ctk.BOTH, expand=True, padx=15, pady=10)
        
        # Créer un widget texte pour afficher les logs
        self.logs_text = ctk.CTkTextbox(self.logs_container, wrap="none", height=500, font=ctk.CTkFont(family="Courier", size=12))
        self.logs_text.pack(fill=ctk.BOTH, expand=True)
        self.logs_text.configure(state="disabled")  # Rendre le texte en lecture seule
        
        # Configurer les styles de texte pour les différents niveaux de log
        self.logs_text.tag_config("CRITICAL", foreground="#c0392b")
        self.logs_text.tag_config("ERROR", foreground="#e74c3c")
        self.logs_text.tag_config("WARNING", foreground="#f39c12")
        self.logs_text.tag_config("INFO", foreground="#2ecc71")
        self.logs_text.tag_config("DEBUG", foreground="#3498db")
        self.logs_text.tag_config("TIMESTAMP", foreground="#7f8c8d")
        
        # Message initial
        self.initial_message = ctk.CTkLabel(
            self.logs_container,
            text="Sélectionnez un fichier de log pour afficher son contenu",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.initial_message.pack(expand=True)
        
        # Barre de pagination (si nécessaire pour les gros fichiers)
        self.pagination_frame = ctk.CTkFrame(self.logs_frame, fg_color="transparent", height=30)
        self.pagination_frame.pack(fill=ctk.X, padx=15, pady=(0, 10))
        self.pagination_frame.pack_propagate(False)  # Fixer la hauteur
    
    def reload_logs(self):
        """
        Recharge la liste des fichiers de log et rafraîchit la vue
        """
        try:
            # Récupérer la liste des fichiers de log
            log_files = self.get_log_files()
            
            # Mettre à jour la liste déroulante
            if log_files:
                self.log_files_dropdown.configure(values=log_files)
                self.log_files_dropdown.set(log_files[0])
                self.current_log_file = log_files[0]
                
                # Charger le contenu du fichier sélectionné
                self.load_log_file(self.current_log_file)
            else:
                self.log_files_dropdown.configure(values=["Aucun fichier de log trouvé"])
                self.log_files_dropdown.set("Aucun fichier de log trouvé")
                self.current_log_file = None
                
                # Afficher un message
                self.clear_logs_text()
                self.initial_message.pack(expand=True)
            
            logger.info("Liste des fichiers de log rechargée")
        except Exception as e:
            logger.error(f"Erreur lors du rechargement des logs: {e}")
            self.show_message("Erreur", f"Impossible de charger les fichiers de log: {e}", "error")
    
    def on_log_file_changed(self, file_name):
        """
        Gère le changement de fichier de log
        
        Args:
            file_name: Nom du fichier sélectionné
        """
        self.current_log_file = file_name
        self.load_log_file(file_name)
    
    def load_log_file(self, file_name):
        """
        Charge le contenu d'un fichier de log
        
        Args:
            file_name: Nom du fichier à charger
        """
        try:
            if not file_name or file_name == "Aucun fichier de log trouvé":
                self.clear_logs_text()
                self.initial_message.pack(expand=True)
                return
            
            # Cacher le message initial
            self.initial_message.pack_forget()
            
            # Chemin complet du fichier
            log_path = os.path.join(self.get_logs_dir(), file_name)
            
            if not os.path.exists(log_path):
                self.show_message("Erreur", f"Le fichier {file_name} n'existe pas", "error")
                return
            
            # Mettre à jour le titre
            self.logs_title.configure(text=f"Logs: {file_name}")
            
            # Lire le contenu du fichier
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                log_lines = f.readlines()
            
            # Mettre à jour les statistiques
            self.update_log_stats(log_lines)
            
            # Afficher les logs
            self.display_logs(log_lines)
            
            logger.info(f"Fichier de log {file_name} chargé ({len(log_lines)} lignes)")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier de log {file_name}: {e}")
            self.show_message("Erreur", f"Impossible de charger le fichier: {e}", "error")
    
    def display_logs(self, log_lines):
        """
        Affiche les lignes de log dans le widget texte
        
        Args:
            log_lines: Liste des lignes de log
        """
        # Rendre le widget modifiable
        self.logs_text.configure(state="normal")
        
        # Effacer le contenu actuel
        self.logs_text.delete("1.0", "end")
        
        # Filtrer les lignes en fonction des filtres actuels
        filtered_lines = self.filter_log_lines(log_lines)
        
        # Mettre à jour le compteur de lignes
        self.logs_count.configure(text=f"{len(filtered_lines)} entrées sur {len(log_lines)}")
        
        # Afficher les lignes filtrées
        for line in filtered_lines:
            # Analyser le niveau de log pour appliquer la coloration
            level = self.extract_log_level(line)
            timestamp = self.extract_timestamp(line)
            
            if timestamp:
                # Insérer le timestamp avec son tag
                self.logs_text.insert("end", timestamp + " ", "TIMESTAMP")
                
                # Insérer le reste de la ligne avec le tag de niveau approprié
                remaining_text = line[len(timestamp):].rstrip()
                
                if level:
                    self.logs_text.insert("end", remaining_text + "\n", level)
                else:
                    self.logs_text.insert("end", remaining_text + "\n")
            else:
                # Si aucun timestamp n'est trouvé, insérer toute la ligne
                if level:
                    self.logs_text.insert("end", line, level)
                else:
                    self.logs_text.insert("end", line)
        
        # Rendre le widget en lecture seule
        self.logs_text.configure(state="disabled")
        
        # Défiler jusqu'en haut
        self.logs_text.see("1.0")
    
    def filter_log_lines(self, log_lines):
        """
        Filtre les lignes de log en fonction des filtres actuels
        
        Args:
            log_lines: Liste des lignes de log
            
        Returns:
            list: Lignes filtrées
        """
        # Récupérer les valeurs des filtres
        level_filter = self.filter_vars["level"].get()
        search_filter = self.filter_vars["search"].get().lower()
        date_range = self.filter_vars["date_range"].get()
        
        # Filtrer par niveau
        if level_filter != "ALL":
            log_lines = [line for line in log_lines if f" {level_filter} " in line]
        
        # Filtrer par texte
        if search_filter:
            log_lines = [line for line in log_lines if search_filter in line.lower()]
        
        # Filtrer par date
        if date_range != "all":
            date_filtered_lines = []
            
            for line in log_lines:
                timestamp = self.extract_timestamp(line)
                if timestamp:
                    log_date = self.parse_timestamp(timestamp)
                    if log_date and self.is_date_in_range(log_date, date_range):
                        date_filtered_lines.append(line)
                else:
                    # Si la ligne n'a pas de timestamp, on l'inclut par défaut
                    date_filtered_lines.append(line)
            
            log_lines = date_filtered_lines
        
        return log_lines
    
    def extract_log_level(self, log_line):
        """
        Extrait le niveau de log d'une ligne
        
        Args:
            log_line: Ligne de log
            
        Returns:
            str: Niveau de log ou None si non trouvé
        """
        for level in self.log_levels:
            if f" {level} " in log_line:
                return level
        return None
    
    def extract_timestamp(self, log_line):
        """
        Extrait le timestamp d'une ligne de log
        
        Args:
            log_line: Ligne de log
            
        Returns:
            str: Timestamp ou chaîne vide si non trouvé
        """
        # Essayer différents formats de timestamp
        # Format: 2023-04-15 14:32:21,123
        match = re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}', log_line)
        if match:
            return match.group(0)
        
        # Format: 15/04/2023 14:32:21
        match = re.match(r'^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', log_line)
        if match:
            return match.group(0)
        
        return ""
    
    def parse_timestamp(self, timestamp_str):
        """
        Convertit une chaîne de timestamp en objet datetime
        
        Args:
            timestamp_str: Chaîne de timestamp
            
        Returns:
            datetime: Objet datetime ou None en cas d'erreur
        """
        try:
            # Essayer différents formats
            formats = [
                "%Y-%m-%d %H:%M:%S,%f",  # 2023-04-15 14:32:21,123
                "%d/%m/%Y %H:%M:%S"      # 15/04/2023 14:32:21
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    def is_date_in_range(self, date, date_range):
        """
        Vérifie si une date est dans une plage donnée
        
        Args:
            date: Date à vérifier
            date_range: Plage de dates ('today', 'yesterday', 'last_7_days', 'last_30_days', 'all')
            
        Returns:
            bool: True si la date est dans la plage, False sinon
        """
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        
        if date_range == "today":
            return date >= today_start
        
        elif date_range == "yesterday":
            yesterday_start = today_start - timedelta(days=1)
            return yesterday_start <= date < today_start
        
        elif date_range == "last_7_days":
            days_7_ago = today_start - timedelta(days=7)
            return date >= days_7_ago
        
        elif date_range == "last_30_days":
            days_30_ago = today_start - timedelta(days=30)
            return date >= days_30_ago
        
        # Pour "all" ou toute autre valeur, retourner True
        return True
    
    def update_log_stats(self, log_lines):
        """
        Met à jour les statistiques des logs
        
        Args:
            log_lines: Liste des lignes de log
        """
        # Effacer les anciennes statistiques
        for widget in self.stats_container.winfo_children():
            widget.destroy()
        
        # Compter les occurrences de chaque niveau
        level_counts = {level: 0 for level in self.log_levels}
        
        for line in log_lines:
            for level in self.log_levels:
                if f" {level} " in line:
                    level_counts[level] += 1
                    break
        
        # Créer les étiquettes de statistiques
        for level, count in level_counts.items():
            if level == "DEBUG":
                color = "#2980b9"
            elif level == "INFO":
                color = "#27ae60"
            elif level == "WARNING":
                color = "#f39c12"
            elif level == "ERROR":
                color = "#e74c3c"
            elif level == "CRITICAL":
                color = "#c0392b"
            else:
                color = "gray"
            
            stat_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            stat_frame.pack(fill=ctk.X, pady=2)
            
            ctk.CTkLabel(
                stat_frame,
                text=level,
                anchor="w",
                width=100,
                font=ctk.CTkFont(size=12),
                text_color=color
            ).pack(side=ctk.LEFT)
            
            ctk.CTkLabel(
                stat_frame,
                text=str(count),
                anchor="e",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=color
            ).pack(side=ctk.RIGHT)
    
    def clear_logs_text(self):
        """
        Efface le contenu du widget texte
        """
        self.logs_text.configure(state="normal")
        self.logs_text.delete("1.0", "end")
        self.logs_text.configure(state="disabled")
        
        # Réinitialiser le titre et le compteur
        self.logs_title.configure(text="Logs système")
        self.logs_count.configure(text="0 entrées")
    
    def apply_filters(self):
        """
        Applique les filtres actuels et rafraîchit l'affichage
        """
        if self.current_log_file:
            self.load_log_file(self.current_log_file)
    
    def clear_filters(self):
        """
        Réinitialise tous les filtres
        """
        self.filter_vars["level"].set("ALL")
        self.filter_vars["search"].set("")
        self.filter_vars["date_range"].set("all")
    
    def export_logs(self):
        """
        Exporte les logs filtrés actuels dans un fichier
        """
        try:
            if not self.current_log_file:
                self.show_message("Erreur", "Aucun fichier de log n'est sélectionné", "error")
                return
            
            # Créer un nom de fichier pour l'export
            base_name = os.path.splitext(self.current_log_file)[0]
            export_name = f"{base_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            export_path = os.path.join(self.get_logs_dir(), "exports", export_name)
            
            # Créer le répertoire d'export s'il n'existe pas
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            # Récupérer le contenu actuel
            content = self.logs_text.get("1.0", "end")
            
            # Écrire dans le fichier d'export
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.show_message(
                "Export réussi", 
                f"Les logs ont été exportés vers:\n{export_path}", 
                "success"
            )
            
            logger.info(f"Logs exportés vers {export_path}")
        except Exception as e:
            logger.error(f"Erreur lors de l'export des logs: {e}")
            self.show_message("Erreur", f"Impossible d'exporter les logs: {e}", "error")
    
    def confirm_clear_old_logs(self):
        """
        Demande confirmation avant de nettoyer les anciens logs
        """
        # Créer une boîte de dialogue de confirmation
        dialog = ctk.CTkToplevel(self.frame)
        dialog.title("Confirmer le nettoyage")
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
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Contenu de la boîte de dialogue
        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Message d'avertissement
        warning_label = ctk.CTkLabel(
            content_frame,
            text="⚠️ Attention",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#e74c3c"
        )
        warning_label.pack(pady=(0, 10))
        
        # Message détaillé
        message_label = ctk.CTkLabel(
            content_frame,
            text="Vous êtes sur le point de supprimer tous les fichiers de log datant de plus de 30 jours.\n\nCette action est irréversible.",
            wraplength=360
        )
        message_label.pack(pady=10)
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, pady=10)
        
        # Bouton Annuler
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            command=dialog.destroy
        )
        cancel_btn.pack(side=ctk.LEFT, padx=5)
        
        # Bouton Confirmer
        confirm_btn = ctk.CTkButton(
            buttons_frame,
            text="Confirmer",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=lambda: self.clear_old_logs(dialog)
        )
        confirm_btn.pack(side=ctk.RIGHT, padx=5)
    
    def clear_old_logs(self, dialog=None):
        """
        Supprime les fichiers de log datant de plus de 30 jours
        
        Args:
            dialog: Boîte de dialogue à fermer après l'opération
        """
        try:
            # Fermer la boîte de dialogue
            if dialog:
                dialog.destroy()
            
            logs_dir = self.get_logs_dir()
            deleted_count = 0
            cutoff_date = datetime.now() - timedelta(days=30)
            
            # Parcourir tous les fichiers de log
            for log_file in os.listdir(logs_dir):
                if log_file.endswith('.log'):
                    log_path = os.path.join(logs_dir, log_file)
                    
                    # Obtenir la date de modification
                    mod_time = os.path.getmtime(log_path)
                    mod_date = datetime.fromtimestamp(mod_time)
                    
                    # Supprimer si plus ancien que la date limite
                    if mod_date < cutoff_date:
                        os.remove(log_path)
                        deleted_count += 1
            
            # Recharger la liste des logs
            self.reload_logs()
            
            # Afficher un message de réussite
            self.show_message(
                "Nettoyage terminé", 
                f"{deleted_count} fichiers de log ont été supprimés", 
                "success"
            )
            
            logger.info(f"{deleted_count} anciens fichiers de log supprimés")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des anciens logs: {e}")
            self.show_message("Erreur", f"Impossible de nettoyer les logs: {e}", "error")
    
    def get_log_files(self):
        """
        Récupère la liste des fichiers de log
        
        Returns:
            list: Liste des noms de fichiers de log
        """
        try:
            logs_dir = self.get_logs_dir()
            
            # Créer le répertoire s'il n'existe pas
            os.makedirs(logs_dir, exist_ok=True)
            
            # Récupérer les fichiers .log
            log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
            
            # Trier par date de modification (du plus récent au plus ancien)
            log_files.sort(
                key=lambda x: os.path.getmtime(os.path.join(logs_dir, x)),
                reverse=True
            )
            
            return log_files
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des fichiers de log: {e}")
            return []
    
    def get_logs_dir(self):
        """
        Récupère le répertoire des logs
        
        Returns:
            str: Chemin vers le répertoire des logs
        """
        # Utiliser le répertoire de logs de l'application si disponible
        if hasattr(self.model, 'logs_dir'):
            return self.model.logs_dir
        
        # Sinon, utiliser un répertoire par défaut
        return os.path.join(os.path.expanduser("~"), ".vynal_docs_automator", "logs")
    
    def show_message(self, title, message, message_type="info"):
        """
        Affiche un message dans une boîte de dialogue
        
        Args:
            title: Titre du message
            message: Contenu du message
            message_type: Type de message ('info', 'success', 'warning', 'error')
        """
        # Déterminer l'icône en fonction du type de message
        if message_type == "error":
            icon = "❌"
            color = "#e74c3c"
        elif message_type == "warning":
            icon = "⚠️"
            color = "#f39c12"
        elif message_type == "success":
            icon = "✅"
            color = "#2ecc71"
        else:
            icon = "ℹ️"
            color = "#3498db"
        
        # Créer la boîte de dialogue
        dialog = ctk.CTkToplevel(self.frame)
        dialog.title(title)
        dialog.geometry("400x180")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Contenu du message
        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Icône et titre
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill=ctk.X, pady=(0, 10))
        
        icon_label = ctk.CTkLabel(header_frame, text=icon, font=ctk.CTkFont(size=24))
        icon_label.pack(side=ctk.LEFT, padx=(0, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=color
        )
        title_label.pack(side=ctk.LEFT)
        
        # Message
        message_label = ctk.CTkLabel(
            content_frame,
            text=message,
            wraplength=360,
            justify="left"
        )
        message_label.pack(fill=ctk.X, pady=10)
        
        # Bouton OK
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, pady=10)
        
        ok_button = ctk.CTkButton(
            button_frame,
            text="OK",
            width=100,
            command=dialog.destroy
        )
        ok_button.pack(side=ctk.RIGHT)
    
    def show(self):
        """
        Affiche la vue des journaux système
        """
        self.frame.pack(fill=ctk.BOTH, expand=True)
        
        # Charger les fichiers de log
        self.reload_logs()
    
    def hide(self):
        """
        Masque la vue des journaux système
        """
        self.frame.pack_forget()