#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue des journaux système pour l'interface d'administration
"""

import logging
import customtkinter as ctk
import tkinter as tk
from datetime import datetime, timedelta
import os
import re
import glob
from typing import List, Dict, Any, Optional, Union, Callable

logger = logging.getLogger("VynalDocsAutomator.Admin.SystemLogsView")

class SystemLogsView:
    """
    Vue pour visualiser les journaux système et les événements
    Permet de filtrer, analyser et exporter les logs
    """
    
    def __init__(self, parent: ctk.CTkFrame, app_model: Any) -> None:
        """
        Initialise la vue des journaux système
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        self.current_log_file = ""  # Initialize as empty string
        self.log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self.security_alerts = []  # Initialize security alerts list
        
        # Créer les répertoires nécessaires
        logs_dir = self.get_logs_dir()
        os.makedirs(logs_dir, exist_ok=True)
        
        # Créer également les répertoires d'export
        os.makedirs(os.path.join(logs_dir, "exports"), exist_ok=True)
        os.makedirs(os.path.join(logs_dir, "security"), exist_ok=True)
        
        if hasattr(self.model, 'admin_dir'):
            alerts_dir = os.path.join(self.model.admin_dir, 'data')
            os.makedirs(alerts_dir, exist_ok=True)
        
        # Variables pour les filtres
        self.filter_vars = {
            "level": ctk.StringVar(value="ALL"),
            "search": ctk.StringVar(),
            "date_range": ctk.StringVar(value="Aujourd'hui")  # Valeur initiale normalisée
        }
        
        # Cadre principal de la vue
        self.frame = ctk.CTkFrame(parent)
        
        # Création de l'interface
        self.create_widgets()
        
        # Charger la liste des fichiers de log
        self.reload_logs()
        
        logger.info("SystemLogsView initialisée")

    def show(self):
        """Affiche la vue des journaux système"""
        self.frame.pack(fill=ctk.BOTH, expand=True)
        # Recharger les logs quand la vue devient visible
        self.reload_logs()
        logger.info("Vue des journaux système affichée")

    def hide(self):
        """Cache la vue des journaux système"""
        self.frame.pack_forget()
        logger.info("Vue des journaux système masquée")
    
    def _delayed_filter(self) -> None:
        """
        Applique les filtres après un délai pour éviter les mises à jour trop fréquentes
        """
        if self._filter_after_id:
            self.frame.after_cancel(self._filter_after_id)
        
        self._filter_after_id = self.frame.after(300, self.apply_filters)
    
    def create_widgets(self) -> None:
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
        
        # Conteneur principal avec trois colonnes
        self.main_container = ctk.CTkFrame(self.frame)
        self.main_container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Configuration des colonnes avec des poids fixes
        self.main_container.grid_columnconfigure(0, weight=2, minsize=200)  # Filtres
        self.main_container.grid_columnconfigure(1, weight=5, minsize=400)  # Logs
        self.main_container.grid_columnconfigure(2, weight=3, minsize=250)  # Alertes
        
        # Configuration de la ligne principale
        self.main_container.grid_rowconfigure(0, weight=1)
        
        # Cadre pour les filtres avec taille minimale
        self.filters_frame = ctk.CTkFrame(self.main_container)
        self.filters_frame.grid(
            row=0,
            column=0,
            padx=(5, 5),
            pady=5,
            sticky="nsew"
        )
        
        # Cadre pour les logs avec taille minimale
        self.logs_frame = ctk.CTkFrame(self.main_container)
        self.logs_frame.grid(
            row=0,
            column=1,
            padx=10,
            pady=5,
            sticky="nsew"
        )
        
        # Cadre pour les alertes de sécurité avec taille minimale
        self.security_frame = ctk.CTkFrame(self.main_container)
        self.security_frame.grid(
            row=0,
            column=2,
            padx=(5, 5),
            pady=5,
            sticky="nsew"
        )
        
        # Empêcher le redimensionnement des frames internes
        self.filters_frame.grid_propagate(False)
        self.logs_frame.grid_propagate(False)
        self.security_frame.grid_propagate(False)
        
        # Créer les composants de filtrage
        self.create_filters()
        
        # Créer la zone d'affichage des logs
        self.create_logs_view()
        
        # Créer la zone d'alertes de sécurité
        self.create_security_alerts_view()
    
    def create_filters(self) -> None:
        """
        Crée les composants de filtrage des logs
        """
        # Titre de la section plus compact
        ctk.CTkLabel(
            self.filters_frame,
            text="Filtres",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=3, pady=2)
        
        # Sélection du fichier de log
        self.log_file_frame = ctk.CTkFrame(self.filters_frame, fg_color="transparent")
        self.log_file_frame.pack(fill=ctk.X, padx=3, pady=1)
        
        ctk.CTkLabel(
            self.log_file_frame,
            text="Fichier:",
            font=ctk.CTkFont(size=11),
            anchor="w"
        ).pack(anchor="w")
        
        # Frame pour la liste déroulante et le bouton parcourir
        dropdown_frame = ctk.CTkFrame(self.log_file_frame, fg_color="transparent")
        dropdown_frame.pack(fill=ctk.X, pady=1)
        
        # Liste déroulante très compacte
        self.log_files_dropdown = ctk.CTkOptionMenu(
            dropdown_frame,
            values=["Chargement..."],
            command=self.on_log_file_changed,
            width=80,
            height=25,
            font=ctk.CTkFont(size=11)
        )
        self.log_files_dropdown.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=(0, 1))
        
        # Bouton parcourir minimal
        ctk.CTkButton(
            dropdown_frame,
            text="...",
            command=self.browse_log_file,
            width=20,
            height=25,
            font=ctk.CTkFont(size=11)
        ).pack(side=ctk.RIGHT)
        
        # Filtres
        filters_container = ctk.CTkFrame(self.filters_frame, fg_color="transparent")
        filters_container.pack(fill=ctk.X, padx=3, pady=1)
        
        # Filtre par niveau
        level_frame = ctk.CTkFrame(filters_container, fg_color="transparent")
        level_frame.pack(fill=ctk.X, pady=1)
        
        ctk.CTkLabel(
            level_frame,
            text="Niveau:",
            font=ctk.CTkFont(size=11),
            anchor="w"
        ).pack(anchor="w")
        
        # Ajouter "ALL" au début de la liste des niveaux
        level_options = ["ALL"] + self.log_levels
        
        level_dropdown = ctk.CTkOptionMenu(
            level_frame,
            values=level_options,
            variable=self.filter_vars["level"],
            width=100,
            height=25,
            font=ctk.CTkFont(size=11)
        )
        level_dropdown.pack(fill=ctk.X, pady=1)
        
        # Filtre par texte (recherche)
        search_frame = ctk.CTkFrame(filters_container, fg_color="transparent")
        search_frame.pack(fill=ctk.X, pady=1)
        
        ctk.CTkLabel(
            search_frame,
            text="Rechercher:",
            font=ctk.CTkFont(size=11),
            anchor="w"
        ).pack(anchor="w")
        
        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.filter_vars["search"],
            height=25,
            font=ctk.CTkFont(size=11)
        )
        search_entry.pack(fill=ctk.X, pady=1)
        
        # Filtre par date
        date_frame = ctk.CTkFrame(filters_container, fg_color="transparent")
        date_frame.pack(fill=ctk.X, pady=1)
        
        ctk.CTkLabel(
            date_frame,
            text="Période:",
            font=ctk.CTkFont(size=11),
            anchor="w"
        ).pack(anchor="w")
        
        date_options = ["Aujourd'hui", "Cette semaine", "Ce mois", "Tout"]
        
        date_dropdown = ctk.CTkOptionMenu(
            date_frame,
            values=date_options,
            variable=self.filter_vars["date_range"],
            width=100,
            height=25,
            font=ctk.CTkFont(size=11)
        )
        date_dropdown.pack(fill=ctk.X, pady=1)
        
        # Bouton d'effacement des filtres
        clear_filters_btn = ctk.CTkButton(
            filters_container,
            text="Effacer les filtres",
            command=self.clear_filters,
            height=25,
            font=ctk.CTkFont(size=11)
        )
        clear_filters_btn.pack(fill=ctk.X, pady=2)
        
        # Statistiques des logs
        stats_frame = ctk.CTkFrame(self.filters_frame)
        stats_frame.pack(fill=ctk.X, padx=3, pady=2)
        
        ctk.CTkLabel(
            stats_frame,
            text="Statistiques",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", padx=3, pady=1)
        
        self.stats_container = ctk.CTkFrame(stats_frame, fg_color="transparent")
        self.stats_container.pack(fill=ctk.X, padx=3, pady=1)
        
        # Boutons d'action
        actions_frame = ctk.CTkFrame(self.filters_frame, fg_color="transparent")
        actions_frame.pack(fill=ctk.X, padx=3, pady=2)
        
        export_btn = ctk.CTkButton(
            actions_frame,
            text="Exporter les logs",
            command=self.export_logs,
            height=25,
            font=ctk.CTkFont(size=11)
        )
        export_btn.pack(fill=ctk.X, pady=1)
        
        clear_logs_btn = ctk.CTkButton(
            actions_frame,
            text="Nettoyer les anciens logs",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.confirm_clear_old_logs,
            height=25,
            font=ctk.CTkFont(size=11)
        )
        clear_logs_btn.pack(fill=ctk.X, pady=1)
    
    def create_logs_view(self) -> None:
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
    
    def create_security_alerts_view(self) -> None:
        """
        Crée la zone d'affichage des alertes de sécurité
        """
        # Titre de la section avec une hauteur fixe et un style amélioré
        security_header = ctk.CTkFrame(self.security_frame, fg_color="#2c3e50", height=40)
        security_header.pack(fill=ctk.X, pady=(0, 5))
        security_header.pack_propagate(False)
        
        # Titre plus compact avec icône
        ctk.CTkLabel(
            security_header,
            text="🚨 Alertes",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=8)
        
        # Zone défilante pour les alertes avec marges réduites
        self.alerts_container = ctk.CTkScrollableFrame(self.security_frame)
        self.alerts_container.pack(fill=ctk.BOTH, expand=True, padx=5, pady=5)
        
        # Compteur d'alertes
        self.alerts_count = ctk.CTkLabel(
            self.security_frame,
            text="0 alertes",
            font=ctk.CTkFont(size=12),
            text_color="#e74c3c"
        )
        self.alerts_count.pack(pady=5)
        
        # Boutons d'action avec espacement optimisé
        actions_frame = ctk.CTkFrame(self.security_frame, fg_color="transparent")
        actions_frame.pack(fill=ctk.X, padx=5, pady=(0, 5))
        
        ctk.CTkButton(
            actions_frame,
            text="Exporter les alertes",
            command=self.export_security_alerts
        ).pack(fill=ctk.X, pady=(0, 2))
        
        ctk.CTkButton(
            actions_frame,
            text="Effacer les alertes",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.clear_security_alerts
        ).pack(fill=ctk.X, pady=(0, 2))
    
    def reload_logs(self) -> None:
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
    
    def on_log_file_changed(self, file_name: str) -> None:
        """
        Gère le changement de fichier de log
        
        Args:
            file_name: Nom du fichier sélectionné
        """
        self.current_log_file = file_name
        self.load_log_file(file_name)
    
    def load_log_file(self, file_name: str) -> None:
        """
        Charge le contenu d'un fichier de log
        
        Args:
            file_name: Nom ou chemin du fichier à charger
        """
        try:
            if not file_name or file_name == "Aucun fichier de log trouvé":
                self.clear_logs_text()
                self.initial_message.pack(expand=True)
                return
            
            # Cacher le message initial
            if hasattr(self, 'initial_message') and self.initial_message.winfo_ismapped():
                self.initial_message.pack_forget()
            
            # Déterminer le chemin du fichier
            if os.path.isabs(file_name):
                log_path = file_name
                display_name = os.path.basename(file_name)
            else:
                log_path = os.path.join(self.get_logs_dir(), file_name)
                display_name = file_name
            
            if not os.path.exists(log_path):
                self.show_message("Erreur", f"Le fichier {display_name} n'existe pas", "error")
                return
            
            # Mettre à jour le titre
            self.logs_title.configure(text=f"Logs: {display_name}")
            
            # Lire le contenu du fichier
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                log_lines = f.readlines()
            
            # Mettre à jour les statistiques
            self.update_log_stats(log_lines)
            
            # Afficher les logs
            self.display_logs(log_lines)
            
            logger.info(f"Fichier de log {display_name} chargé ({len(log_lines)} lignes)")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier de log {file_name}: {e}")
            self.show_message("Erreur", f"Impossible de charger le fichier: {e}", "error")
    
    def display_logs(self, log_lines: List[str]) -> None:
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
            line = line.rstrip()  # Remove trailing whitespace
            if not line:  # Skip empty lines
                continue
                
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
                    self.logs_text.insert("end", line + "\n", level)
                else:
                    self.logs_text.insert("end", line + "\n")
        
        # Rendre le widget en lecture seule
        self.logs_text.configure(state="disabled")
        
        # Défiler jusqu'en haut
        self.logs_text.see("1.0")
    
    def filter_log_lines(self, log_lines: List[str]) -> List[str]:
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
        
        logger.debug(f"Applying filters: level={level_filter}, search={search_filter}, date_range={date_range}")
        
        filtered_lines = []
        
        # Filtrer les lignes
        for line in log_lines:
            line = line.rstrip()
            if not line:  # Skip empty lines
                continue
            
            # Vérifier le niveau
            if level_filter != "ALL":
                level = self.extract_log_level(line)
                logger.debug(f"Line: {line}")
                logger.debug(f"Extracted level: {level}")
                if not level or level != level_filter:
                    logger.debug(f"Skipping line due to level mismatch: {line}")
                    continue
            
            # Vérifier le texte
            if search_filter and search_filter not in line.lower():
                logger.debug(f"Skipping line due to text mismatch: {line}")
                continue
            
            # Vérifier la date
            if date_range.lower() != "tout":
                timestamp = self.extract_timestamp(line)
                if timestamp:
                    log_date = self.parse_timestamp(timestamp)
                    if not log_date or not self.is_date_in_range(log_date, date_range):
                        logger.debug(f"Skipping line due to date mismatch: {line}")
                        continue
            
            # Si tous les filtres passent, ajouter la ligne
            logger.debug(f"Adding line: {line}")
            filtered_lines.append(line)
        
        logger.debug(f"Filtered {len(log_lines)} lines to {len(filtered_lines)} lines")
        return filtered_lines
    
    def extract_log_level(self, log_line: str) -> Optional[str]:
        """
        Extrait le niveau de log d'une ligne
        
        Args:
            log_line: Ligne de log
            
        Returns:
            str: Niveau de log ou None si non trouvé
        """
        # Chercher le niveau de log après un timestamp
        timestamp = self.extract_timestamp(log_line)
        if timestamp:
            remaining = log_line[len(timestamp):].strip()
            for level in self.log_levels:
                if remaining.startswith(level):
                    logger.debug(f"Found level {level} after timestamp in: {log_line}")
                    return level
        
        # Chercher le niveau de log entre crochets
        for level in self.log_levels:
            if f"[{level}]" in log_line:
                logger.debug(f"Found level {level} in brackets in: {log_line}")
                return level
        
        # Chercher le niveau de log avec un espace avant et après
        for level in self.log_levels:
            if f" {level} " in log_line:
                logger.debug(f"Found level {level} with spaces in: {log_line}")
                return level
        
        logger.debug(f"No level found in: {log_line}")
        return None
    
    def extract_timestamp(self, log_line: str) -> str:
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
    
    def parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
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
    
    def is_date_in_range(self, date: datetime, date_range: str) -> bool:
        """
        Vérifie si une date est dans une plage donnée
        
        Args:
            date: Date à vérifier
            date_range: Plage de dates ('Aujourd'hui', 'Cette semaine', 'Ce mois', 'Tout')
            
        Returns:
            bool: True si la date est dans la plage, False sinon
        """
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        
        if date_range.lower() == "aujourd'hui":
            return date >= today_start
        
        elif date_range.lower() == "cette semaine":
            # Calculer le début de la semaine (lundi)
            days_since_monday = now.weekday()
            week_start = today_start - timedelta(days=days_since_monday)
            return date >= week_start
        
        elif date_range.lower() == "ce mois":
            # Début du mois
            month_start = datetime(now.year, now.month, 1, 0, 0, 0)
            return date >= month_start
        
        # Pour "tout" ou toute autre valeur, retourner True
        return True
    
    def update_log_stats(self, log_lines: List[str]) -> None:
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
    
    def clear_logs_text(self) -> None:
        """
        Efface le contenu du widget texte
        """
        self.logs_text.configure(state="normal")
        self.logs_text.delete("1.0", "end")
        self.logs_text.configure(state="disabled")
        
        # Réinitialiser le titre et le compteur
        self.logs_title.configure(text="Logs système")
        self.logs_count.configure(text="0 entrées")
    
    def apply_filters(self) -> None:
        """
        Applique les filtres actuels et rafraîchit l'affichage
        """
        try:
            if not self.current_log_file:
                return
            
            logger.debug(f"Applying filters to {self.current_log_file}")
            
            # Read the current log file
            with open(self.current_log_file, 'r', encoding='utf-8', errors='replace') as f:
                log_lines = f.readlines()
            
            logger.debug(f"Read {len(log_lines)} lines from file")
            
            # Apply filters and update display
            self.display_logs(log_lines)
            
            logger.debug("Filters applied")
        except Exception as e:
            logger.error(f"Erreur lors de l'application des filtres: {e}")
            self.show_message("Erreur", f"Impossible d'appliquer les filtres: {e}", "error")
    
    def clear_filters(self) -> None:
        """
        Réinitialise tous les filtres
        """
        self.filter_vars["level"].set("ALL")
        self.filter_vars["search"].set("")
        self.filter_vars["date_range"].set("Tout")
        
        # Appliquer les filtres après réinitialisation
        self.apply_filters()
    
    def export_logs(self, export_path: Optional[str] = None) -> None:
        """
        Exporte les logs filtrés actuels dans un fichier
        
        Args:
            export_path: Optional path for the export file. If not provided, a default path will be generated.
        """
        try:
            if not self.current_log_file and not export_path:
                self.show_message("Erreur", "Aucun fichier de log n'est sélectionné", "error")
                return
            
            if export_path is None:
                # Créer un nom de fichier pour l'export
                base_name = os.path.splitext(os.path.basename(self.current_log_file))[0]
                export_name = f"{base_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                export_path = os.path.join(self.get_logs_dir(), "exports", export_name)
            
            # Créer le répertoire d'export s'il n'existe pas
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            # Récupérer le contenu actuel
            content = self.logs_text.get("1.0", "end-1c")  # Remove trailing newline
            
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

    def get_logs_dir(self) -> str:
        """
        Retourne le chemin du répertoire des logs
        
        Returns:
            str: Chemin du répertoire des logs
        """
        if hasattr(self.model, 'logs_dir'):
            return self.model.logs_dir
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')

    def show_message(self, title: str, message: str, level: str = "info") -> None:
        """
        Affiche une boîte de dialogue avec un message
        
        Args:
            title: Titre de la boîte de dialogue
            message: Message à afficher
            level: Niveau du message (info, warning, error, success)
        """
        dialog = ctk.CTkToplevel(self.frame)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        dialog.transient(self.frame)
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Icône en fonction du niveau
        if level == "error":
            icon = "❌"
            color = "#e74c3c"
        elif level == "warning":
            icon = "⚠️"
            color = "#f39c12"
        elif level == "success":
            icon = "✅"
            color = "#2ecc71"
        else:
            icon = "ℹ️"
            color = "#3498db"
        
        # Message
        message_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        message_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            message_frame,
            text=icon,
            font=ctk.CTkFont(size=48)
        ).pack(pady=10)
        
        ctk.CTkLabel(
            message_frame,
            text=message,
            font=ctk.CTkFont(size=12),
            wraplength=300,
            text_color=color
        ).pack(pady=10)
        
        # Bouton OK
        ctk.CTkButton(
            dialog,
            text="OK",
            command=dialog.destroy
        ).pack(pady=10)
        
        # Gestion des touches de clavier
        dialog.bind("<Return>", lambda e: dialog.destroy())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    def browse_log_file(self) -> None:
        """
        Ouvre une boîte de dialogue pour sélectionner un fichier de log
        """
        try:
            # Ouvrir la boîte de dialogue de sélection de fichier
            file_path = tk.filedialog.askopenfilename(
                title="Sélectionner un fichier de log",
                initialdir=self.get_logs_dir(),
                filetypes=[
                    ("Fichiers log", "*.log"),
                    ("Fichiers texte", "*.txt"),
                    ("Tous les fichiers", "*.*")
                ]
            )
            
            if file_path:
                # Mettre à jour la liste déroulante
                self.log_files_dropdown.configure(values=[file_path])
                self.log_files_dropdown.set(file_path)
                
                # Charger le fichier sélectionné
                self.current_log_file = file_path
                self.load_log_file(file_path)
                
                logger.info(f"Fichier de log sélectionné: {file_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du fichier: {e}")
            self.show_message("Erreur", f"Impossible de sélectionner le fichier: {e}", "error")

    def get_log_files(self) -> List[str]:
        """
        Récupère la liste des fichiers de log disponibles
        
        Returns:
            list: Liste des chemins des fichiers de log
        """
        try:
            logs_dir = self.get_logs_dir()
            log_files = []
            
            # Rechercher les fichiers .log et .txt
            for ext in ["*.log", "*.txt"]:
                log_files.extend(glob.glob(os.path.join(logs_dir, "**", ext), recursive=True))
            
            # Trier par date de modification (plus récent en premier)
            log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            return log_files
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des fichiers de log: {e}")
            return []

    def add_security_alert(self, message: str, level: str = "INFO") -> None:
        """
        Ajoute une alerte de sécurité
        
        Args:
            message: Message de l'alerte
            level: Niveau de l'alerte (INFO, WARNING, ERROR)
        """
        try:
            # Create alert data
            alert_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": message,
                "level": level
            }
            
            # Add to alerts list
            self.security_alerts.append(alert_data)
            
            # Create alert frame
            alert_frame = ctk.CTkFrame(self.alerts_container)
            alert_frame.pack(fill=ctk.X, padx=5, pady=2)
            
            # Header with timestamp and level
            header = ctk.CTkFrame(alert_frame, fg_color="transparent")
            header.pack(fill=ctk.X, padx=5, pady=2)
            
            # Level icon and color
            if level == "ERROR":
                icon = "❌"
                color = "#e74c3c"
            elif level == "WARNING":
                icon = "⚠️"
                color = "#f39c12"
            else:
                icon = "ℹ️"
                color = "#3498db"
            
            ctk.CTkLabel(
                header,
                text=f"{icon} {level}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=color
            ).pack(side=ctk.LEFT)
            
            ctk.CTkLabel(
                header,
                text=alert_data["timestamp"],
                font=ctk.CTkFont(size=10),
                text_color="gray"
            ).pack(side=ctk.RIGHT)
            
            # Message
            ctk.CTkLabel(
                alert_frame,
                text=message,
                font=ctk.CTkFont(size=12),
                wraplength=200,
                justify="left"
            ).pack(fill=ctk.X, padx=5, pady=2)
            
            # Update alert count
            self.alerts_count.configure(text=f"{len(self.security_alerts)} alertes")
            
            logger.info(f"Alerte de sécurité ajoutée: {message}")
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de l'alerte: {e}")
            self.show_message("Erreur", f"Impossible d'ajouter l'alerte: {e}", "error")

    def show_device_info(self, device_info: Dict[str, Any]) -> None:
        """
        Affiche les informations détaillées sur l'appareil
        
        Args:
            device_info (dict): Informations sur l'appareil
        """
        if not device_info:
            self.show_message("Erreur", "Aucune information sur l'appareil n'est disponible", "warning")
            return
            
        dialog = ctk.CTkToplevel(self.frame)
        dialog.title("Informations sur l'appareil")
        dialog.geometry("500x400")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        dialog.transient(self.frame)
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Zone défilante pour les informations
        scroll_frame = ctk.CTkScrollableFrame(dialog)
        scroll_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Afficher toutes les informations disponibles
        for key, value in device_info.items():
            if isinstance(value, dict):
                # Créer une section pour les sous-dictionnaires
                section_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                section_frame.pack(fill=ctk.X, pady=5)
                
                ctk.CTkLabel(
                    section_frame,
                    text=key.replace('_', ' ').title(),
                    font=ctk.CTkFont(size=12, weight="bold")
                ).pack(anchor="w")
                
                for sub_key, sub_value in value.items():
                    ctk.CTkLabel(
                        section_frame,
                        text=f"{sub_key}: {sub_value}",
                        font=ctk.CTkFont(size=11),
                        anchor="w"
                    ).pack(fill=ctk.X, padx=10)
            else:
                ctk.CTkLabel(
                    scroll_frame,
                    text=f"{key}: {value}",
                    font=ctk.CTkFont(size=11),
                    anchor="w"
                ).pack(fill=ctk.X)
        
        # Bouton Fermer
        ctk.CTkButton(
            dialog,
            text="Fermer",
            command=dialog.destroy
        ).pack(pady=10)
        
        # Gestion des touches de clavier
        dialog.bind("<Return>", lambda e: dialog.destroy())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    def confirm_clear_old_logs(self) -> None:
        """
        Affiche une boîte de dialogue de confirmation pour nettoyer les anciens logs
        """
        dialog = ctk.CTkToplevel(self.frame)
        dialog.title("Confirmation")
        dialog.geometry("400x250")
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()
        dialog.transient(self.frame)
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Message
        message_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        message_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            message_frame,
            text="⚠️",
            font=ctk.CTkFont(size=48)
        ).pack(pady=10)
        
        ctk.CTkLabel(
            message_frame,
            text="Êtes-vous sûr de vouloir supprimer les anciens fichiers de log ?\nCette action est irréversible.",
            font=ctk.CTkFont(size=12),
            wraplength=300,
            text_color="#f39c12"
        ).pack(pady=10)
        
        # Boutons
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.pack(fill=ctk.X, padx=20, pady=10)
        
        ctk.CTkButton(
            buttons_frame,
            text="Annuler",
            fg_color="transparent",
            hover_color="#34495e",
            command=dialog.destroy
        ).pack(side=ctk.LEFT, expand=True, padx=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="Supprimer",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=lambda: [dialog.destroy(), self.clear_old_logs()]
        ).pack(side=ctk.RIGHT, expand=True, padx=5)
        
        # Gestion des touches de clavier
        dialog.bind("<Return>", lambda e: dialog.destroy())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    def clear_old_logs(self) -> None:
        """
        Supprime les anciens fichiers de log (plus vieux que 30 jours)
        """
        try:
            logs_dir = self.get_logs_dir()
            now = datetime.now()
            count = 0
            
            # Parcourir tous les fichiers de log
            for ext in ["*.log", "*.txt"]:
                for file_path in glob.glob(os.path.join(logs_dir, "**", ext), recursive=True):
                    # Ignorer les fichiers dans le dossier exports
                    if "exports" in file_path:
                        continue
                    
                    # Vérifier l'âge du fichier
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    age = now - mtime
                    
                    # Supprimer si plus vieux que 30 jours
                    if age.days > 30:
                        try:
                            os.remove(file_path)
                            count += 1
                            logger.info(f"Fichier supprimé: {file_path}")
                        except Exception as e:
                            logger.error(f"Impossible de supprimer {file_path}: {e}")
            
            # Recharger la liste des fichiers
            self.reload_logs()
            
            # Afficher un message de confirmation
            if count > 0:
                self.show_message(
                    "Nettoyage terminé",
                    f"{count} fichier(s) de log ont été supprimés",
                    "success"
                )
            else:
                self.show_message(
                    "Information",
                    "Aucun fichier de log à supprimer",
                    "info"
                )
            
            logger.info(f"{count} fichiers de log supprimés")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des logs: {e}")
            self.show_message("Erreur", f"Impossible de nettoyer les logs: {e}", "error")

    def export_security_alerts(self) -> None:
        """
        Exporte les alertes de sécurité actuelles dans un fichier
        """
        try:
            # Vérifier s'il y a des alertes à exporter
            alerts = self.alerts_container.winfo_children()
            if not alerts:
                self.show_message("Information", "Aucune alerte à exporter", "info")
                return

            # Créer un nom de fichier pour l'export
            export_name = f"security_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            export_path = os.path.join(self.get_logs_dir(), "security", export_name)

            # Créer le répertoire d'export s'il n'existe pas
            os.makedirs(os.path.dirname(export_path), exist_ok=True)

            # Préparer le contenu de l'export
            content = []
            for alert_frame in alerts:
                # Extraire les informations de l'alerte
                header = alert_frame.winfo_children()[0]  # En-tête de l'alerte
                details = alert_frame.winfo_children()[1]  # Détails de l'alerte

                # Récupérer le texte des labels
                alert_type = header.winfo_children()[0].cget("text")
                timestamp = header.winfo_children()[1].cget("text")
                alert_details = [child.cget("text") for child in details.winfo_children() if isinstance(child, ctk.CTkLabel)]

                # Formater l'alerte
                content.append(f"=== {alert_type} ===")
                content.append(f"Timestamp: {timestamp}")
                content.extend(alert_details)
                content.append("-" * 50)

            # Écrire dans le fichier d'export
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(content))

            self.show_message(
                "Export réussi",
                f"Les alertes de sécurité ont été exportées vers:\n{export_path}",
                "success"
            )

            logger.info(f"Alertes de sécurité exportées vers {export_path}")
        except Exception as e:
            logger.error(f"Erreur lors de l'export des alertes de sécurité: {e}")
            self.show_message("Erreur", f"Impossible d'exporter les alertes: {e}", "error")

    def clear_security_alerts(self) -> None:
        """
        Supprime toutes les alertes de sécurité affichées
        """
        try:
            # Supprimer toutes les alertes
            for widget in self.alerts_container.winfo_children():
                widget.destroy()

            # Mettre à jour le compteur
            self.alerts_count.configure(text="0 alertes")

            self.show_message(
                "Nettoyage terminé",
                "Toutes les alertes ont été supprimées",
                "success"
            )

            logger.info("Alertes de sécurité supprimées")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des alertes: {e}")
            self.show_message("Erreur", f"Impossible de supprimer les alertes: {e}", "error")