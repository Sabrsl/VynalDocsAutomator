#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue du tableau de bord administrateur pour l'application Vynal Docs Automator
Version améliorée avec meilleure gestion de l'espace et performances optimisées
"""

import logging
import customtkinter as ctk
from datetime import datetime, timedelta
import os
import platform
import psutil
import threading
import queue
import time
from functools import lru_cache
from typing import Dict, Any, Optional

logger = logging.getLogger("VynalDocsAutomator.Admin.DashboardView")

class AdminDashboardView:
    """
    Vue du tableau de bord administrateur
    Affiche un résumé des statistiques d'utilisation, l'état du système et les informations importantes
    """
    
    def __init__(self, parent, app_model):
        """
        Initialise la vue du tableau de bord administrateur
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        
        # Cadre principal de la vue
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        
        # File d'attente pour les mises à jour asynchrones
        self.update_queue = queue.Queue()
        
        # Cache des données
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
        
        # État de chargement
        self.loading = False
        
        # Création de l'interface
        self.create_widgets()
        
        # Démarrer le thread de mise à jour
        self.update_thread = None
        self.stop_thread = False
        
        self._is_running = True
        self._update_interval = 5000  # 5 secondes
        self._update_after_id = None
        
        logger.info("AdminDashboardView initialisée")
    
    def create_widgets(self):
        """
        Crée les widgets du tableau de bord administrateur
        """
        # Cadre pour le titre de la page
        self.header_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.header_frame.pack(fill=ctk.X, pady=(0, 10))
        
        # Titre principal
        ctk.CTkLabel(
            self.header_frame,
            text="Tableau de bord administrateur",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", padx=20, pady=10)
        
        # Conteneur principal
        self.main_container = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.main_container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Ligne 1: Statistiques principales
        self.stats_frame = ctk.CTkFrame(self.main_container)
        self.stats_frame.pack(fill=ctk.X, pady=5)
        
        # Configuration avec grid pour les cartes de statistiques
        self.stats_frame.columnconfigure(0, weight=1)
        self.stats_frame.columnconfigure(1, weight=1)
        self.stats_frame.columnconfigure(2, weight=1)
        self.stats_frame.columnconfigure(3, weight=1)
        
        # Créer les cartes de statistiques
        self.user_card = self.create_stat_card(
            self.stats_frame,
            "Utilisateurs",
            "👥",
            "0",
            "Actifs aujourd'hui: 0",
            0, 0
        )
        
        self.document_card = self.create_stat_card(
            self.stats_frame,
            "Documents",
            "📄",
            "0",
            "Créés cette semaine: 0",
            0, 1
        )
        
        self.template_card = self.create_stat_card(
            self.stats_frame,
            "Modèles",
            "📋",
            "0",
            "Utilisés cette semaine: 0",
            0, 2
        )
        
        self.error_card = self.create_stat_card(
            self.stats_frame,
            "Erreurs",
            "⚠️",
            "0",
            "Dernières 24h",
            0, 3
        )
        
        # Conteneur pour les sections du milieu et du bas
        content_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content_container.pack(fill=ctk.BOTH, expand=True, pady=5)
        
        # Utiliser un système de grille pour les sections
        content_container.columnconfigure(0, weight=1)
        content_container.columnconfigure(1, weight=1)
        content_container.rowconfigure(0, weight=1)
        content_container.rowconfigure(1, weight=1)
        
        # Ligne 2: État du système et actions administratives
        self.system_frame = ctk.CTkFrame(content_container)
        self.system_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Titre de la section système
        ctk.CTkLabel(
            self.system_frame,
            text="État du système",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=10)
        
        # Tableau d'informations système
        self.system_info_table = ctk.CTkFrame(self.system_frame, fg_color="transparent")
        self.system_info_table.pack(fill=ctk.BOTH, expand=True, padx=15, pady=5)
        
        # Informations système
        self.system_info = {}
        system_info_items = [
            {"label": "Système d'exploitation", "key": "os"},
            {"label": "Version Python", "key": "python_version"},
            {"label": "Utilisation CPU", "key": "cpu_usage"},
            {"label": "Utilisation mémoire", "key": "memory_usage"},
            {"label": "Espace disque", "key": "disk_space"},
            {"label": "Uptime application", "key": "uptime"}
        ]
        
        for i, item in enumerate(system_info_items):
            row_frame = ctk.CTkFrame(self.system_info_table, fg_color="transparent")
            row_frame.pack(fill=ctk.X, pady=2)
            
            ctk.CTkLabel(
                row_frame,
                text=item["label"],
                width=150,
                anchor="w",
                font=ctk.CTkFont(size=12)
            ).pack(side=ctk.LEFT)
            
            value_label = ctk.CTkLabel(
                row_frame,
                text="Chargement...",
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold")
            )
            value_label.pack(side=ctk.LEFT, padx=10)
            
            self.system_info[item["key"]] = value_label
        
        # Section Actions administratives
        self.admin_actions_frame = ctk.CTkFrame(content_container)
        self.admin_actions_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Titre de la section
        ctk.CTkLabel(
            self.admin_actions_frame,
            text="Actions administratives",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=10)
        
        # Container pour les actions
        actions_container = ctk.CTkFrame(self.admin_actions_frame, fg_color="transparent")
        actions_container.pack(fill=ctk.BOTH, expand=True, padx=15, pady=5)
        
        # Action: Sauvegarde des données
        backup_frame = ctk.CTkFrame(actions_container, fg_color="transparent")
        backup_frame.pack(fill=ctk.X, pady=5)
        
        ctk.CTkLabel(
            backup_frame,
            text="Sauvegarde des données",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            backup_frame,
            text="Créer une sauvegarde complète des données de l'application",
            font=ctk.CTkFont(size=12),
            wraplength=350  # Augmenter la largeur pour éviter la troncature
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkButton(
            backup_frame,
            text="Lancer la sauvegarde",
            command=self.perform_backup_stub
        ).pack(anchor="w", pady=5)
        
        # Action: Vérification d'intégrité
        integrity_frame = ctk.CTkFrame(actions_container, fg_color="transparent")
        integrity_frame.pack(fill=ctk.X, pady=5)
        
        ctk.CTkLabel(
            integrity_frame,
            text="Vérification d'intégrité",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            integrity_frame,
            text="Vérifier l'intégrité des données et réparer les problèmes",
            font=ctk.CTkFont(size=12),
            wraplength=350  # Augmenter la largeur pour éviter la troncature
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkButton(
            integrity_frame,
            text="Vérifier l'intégrité",
            command=self.check_integrity_stub
        ).pack(anchor="w", pady=5)
        
        # Action: Optimisation
        optimize_frame = ctk.CTkFrame(actions_container, fg_color="transparent")
        optimize_frame.pack(fill=ctk.X, pady=5)
        
        ctk.CTkLabel(
            optimize_frame,
            text="Optimisation",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            optimize_frame,
            text="Optimiser les performances de l'application",
            font=ctk.CTkFont(size=12),
            wraplength=350  # Augmenter la largeur pour éviter la troncature
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkButton(
            optimize_frame,
            text="Optimiser",
            command=self.optimize_app_stub
        ).pack(anchor="w", pady=5)
        
        # Ligne 3: Activités administratives et alertes système
        # Section Activités récentes
        self.activities_frame = ctk.CTkFrame(content_container)
        self.activities_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # Titre
        ctk.CTkLabel(
            self.activities_frame,
            text="Activités administratives récentes",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=10)
        
        # Zone défilante pour les activités
        self.activities_list_frame = ctk.CTkScrollableFrame(self.activities_frame, height=150)
        self.activities_list_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        # Message si aucune activité
        self.no_activities_label = ctk.CTkLabel(
            self.activities_list_frame,
            text="Aucune activité récente",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.no_activities_label.pack(pady=20)
        
        # Section Alertes système
        self.alerts_frame = ctk.CTkFrame(content_container)
        self.alerts_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        # Titre
        ctk.CTkLabel(
            self.alerts_frame,
            text="Alertes système",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=10)
        
        # Zone pour les alertes
        self.alerts_list_frame = ctk.CTkScrollableFrame(self.alerts_frame, height=150)
        self.alerts_list_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        # Message si aucune alerte
        self.no_alerts_label = ctk.CTkLabel(
            self.alerts_list_frame,
            text="Aucune alerte active",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.no_alerts_label.pack(pady=20)
    
    def create_stat_card(self, parent, title, icon, value, subtitle, row, col):
        """
        Crée une carte de statistique pour le tableau de bord
        
        Args:
            parent: Widget parent
            title: Titre de la carte
            icon: Icône à afficher
            value: Valeur principale
            subtitle: Texte secondaire
            row: Ligne dans la grille
            col: Colonne dans la grille
            
        Returns:
            dict: Dictionnaire contenant les widgets de la carte
        """
        card = ctk.CTkFrame(parent, fg_color=("#e1e5eb", "#343b48"))
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(fill=ctk.X, padx=10, pady=(10, 5))
        
        # Titre et icône
        icon_label = ctk.CTkLabel(top_frame, text=icon, font=ctk.CTkFont(size=24))
        icon_label.pack(side=ctk.LEFT)
        
        title_label = ctk.CTkLabel(top_frame, text=title, font=ctk.CTkFont(size=14))
        title_label.pack(side=ctk.LEFT, padx=10)
        
        # Valeur principale
        value_label = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=28, weight="bold"))
        value_label.pack(pady=(5, 5))
        
        # Sous-titre/explication
        subtitle_label = ctk.CTkLabel(card, text=subtitle, font=ctk.CTkFont(size=12), text_color="gray")
        subtitle_label.pack(pady=(0, 10))
        
        return {
            "frame": card,
            "icon": icon_label,
            "title": title_label,
            "value": value_label,
            "subtitle": subtitle_label
        }
    
    def create_activity_item(self, parent, activity):
        """
        Crée un élément d'activité administrative
        
        Args:
            parent: Widget parent
            activity: Dictionnaire contenant les données d'activité
            
        Returns:
            ctk.CTkFrame: Cadre contenant l'élément d'activité
        """
        item = ctk.CTkFrame(parent, fg_color=("gray95", "gray20"))
        item.pack(fill=ctk.X, pady=2)
        
        try:
            timestamp = datetime.fromisoformat(activity["timestamp"])
            formatted_time = timestamp.strftime("%d/%m/%Y %H:%M")
        except Exception:
            formatted_time = activity.get("timestamp", "")
        
        # Ligne supérieure: description et temps
        top_frame = ctk.CTkFrame(item, fg_color="transparent")
        top_frame.pack(fill=ctk.X, padx=10, pady=(10, 5))
        
        description = ctk.CTkLabel(
            top_frame,
            text=activity.get("description", ""),
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        description.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
        
        time_label = ctk.CTkLabel(
            top_frame,
            text=formatted_time,
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        time_label.pack(side=ctk.RIGHT, padx=5)
        
        # Ligne inférieure: détails
        if "details" in activity and activity["details"]:
            details_frame = ctk.CTkFrame(item, fg_color="transparent")
            details_frame.pack(fill=ctk.X, padx=10, pady=(0, 10))
            
            details_label = ctk.CTkLabel(
                details_frame,
                text=activity["details"],
                anchor="w",
                font=ctk.CTkFont(size=12),
                text_color="gray",
                wraplength=350  # Augmenter pour éviter la troncature
            )
            details_label.pack(anchor="w")
        
        # Utilisateur
        if "user" in activity and activity["user"]:
            user_frame = ctk.CTkFrame(item, fg_color="transparent")
            user_frame.pack(fill=ctk.X, padx=10, pady=(0, 10))
            
            user_label = ctk.CTkLabel(
                user_frame,
                text=f"Par: {activity['user']}",
                anchor="w",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            user_label.pack(side=ctk.LEFT)
        
        return item
    
    def create_alert_item(self, parent, alert):
        """
        Crée un élément d'alerte
        
        Args:
            parent: Widget parent
            alert: Dictionnaire contenant les données de l'alerte
            
        Returns:
            ctk.CTkFrame: Cadre contenant l'élément d'alerte
        """
        # Définir la couleur en fonction du niveau d'alerte
        level = alert.get("level", "info")
        if level == "critical":
            bg_color = ("#ffcccc", "#5c2d2d")
            level_icon = "🔴"
        elif level == "warning":
            bg_color = ("#ffe6cc", "#5c452d")
            level_icon = "🟠"
        elif level == "info":
            bg_color = ("#cce5ff", "#2d3e5c")
            level_icon = "🔵"
        else:
            bg_color = ("gray95", "gray20")
            level_icon = "⚪"
        
        item = ctk.CTkFrame(parent, fg_color=bg_color)
        item.pack(fill=ctk.X, pady=2)
        
        # En-tête avec niveau et titre
        header_frame = ctk.CTkFrame(item, fg_color="transparent")
        header_frame.pack(fill=ctk.X, padx=10, pady=(10, 5))
        
        level_label = ctk.CTkLabel(
            header_frame,
            text=f"{level_icon} {level.capitalize()}",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        level_label.pack(side=ctk.LEFT)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=alert.get("title", "Alerte sans titre"),
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        title_label.pack(side=ctk.LEFT, padx=10)
        
        # Horodatage
        try:
            timestamp = datetime.fromisoformat(alert.get("timestamp", datetime.now().isoformat()))
            formatted_time = timestamp.strftime("%d/%m/%Y %H:%M")
        except Exception:
            formatted_time = alert.get("timestamp", "")
        
        time_label = ctk.CTkLabel(
            header_frame,
            text=formatted_time,
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        time_label.pack(side=ctk.RIGHT)
        
        # Message de l'alerte
        if "message" in alert and alert["message"]:
            message_frame = ctk.CTkFrame(item, fg_color="transparent")
            message_frame.pack(fill=ctk.X, padx=10, pady=(0, 10))
            
            message_label = ctk.CTkLabel(
                message_frame,
                text=alert["message"],
                anchor="w",
                font=ctk.CTkFont(size=12),
                wraplength=350  # Augmenter pour éviter la troncature
            )
            message_label.pack(anchor="w")
        
        # Bouton d'action si nécessaire
        if "action" in alert and alert["action"]:
            action_frame = ctk.CTkFrame(item, fg_color="transparent")
            action_frame.pack(fill=ctk.X, padx=10, pady=(0, 10))
            
            action_button = ctk.CTkButton(
                action_frame,
                text=alert["action"],
                width=100,
                height=25,
                font=ctk.CTkFont(size=11),
                command=lambda: self.handle_alert_action_stub(alert)
            )
            action_button.pack(side=ctk.LEFT)
        
        return item
    
    def update_view(self):
        """
        Met à jour la vue avec les données actuelles de manière asynchrone
        """
        if not self._is_running:
            return
            
        try:
            # Mettre à jour les statistiques de manière asynchrone
            self.frame.after(0, self._update_statistics)
            
            # Mettre à jour les informations système
            self.frame.after(0, self._update_system_info)
            
            # Mettre à jour les activités et alertes
            self.frame.after(0, self.update_activities)
            self.frame.after(0, self.update_alerts)
            
            # Planifier la prochaine mise à jour
            self._update_after_id = self.frame.after(self._update_interval, self.update_view)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la vue: {e}")
            # Réessayer dans 30 secondes en cas d'erreur
            self._update_after_id = self.frame.after(30000, self.update_view)
    
    def _update_statistics(self):
        """
        Met à jour les statistiques de manière asynchrone
        """
        try:
            # Récupérer les statistiques depuis le cache ou les calculer
            stats = self._get_cached_stats()
            
            # Mettre à jour l'interface avec les nouvelles statistiques
            self.user_card["value"].configure(text=str(stats.get("total_users", 0)))
            self.document_card["value"].configure(text=str(stats.get("total_documents", 0)))
            self.template_card["value"].configure(text=str(stats.get("total_templates", 0)))
            self.error_card["value"].configure(text=str(stats.get("total_errors", 0)))
            
            # Mettre à jour les sous-titres
            self.user_card["subtitle"].configure(text=f"Actifs aujourd'hui: {stats.get('active_users', 0)}")
            self.document_card["subtitle"].configure(text=f"Créés cette semaine: {stats.get('weekly_docs', 0)}")
            self.template_card["subtitle"].configure(text=f"Utilisés cette semaine: {stats.get('weekly_templates', 0)}")
            self.error_card["subtitle"].configure(text=f"Dernières 24h: {stats.get('recent_errors', 0)}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des statistiques: {e}")
            # Afficher un message d'erreur à l'utilisateur
            self._show_error_message("Erreur de mise à jour", "Impossible de mettre à jour les statistiques")

    @lru_cache(maxsize=1)
    def _get_cached_stats(self):
        """
        Récupère les statistiques avec mise en cache
        """
        try:
            stats = {}
            
            # Statistiques utilisateurs
            stats["total_users"] = len(getattr(self.model, "users", []))
            stats["active_users"] = sum(1 for user in getattr(self.model, "users", []) 
                                      if self.is_user_active_today(user))
            
            # Statistiques documents
            stats["total_documents"] = len(getattr(self.model, "documents", []))
            stats["weekly_docs"] = sum(1 for doc in getattr(self.model, "documents", [])
                                     if self._is_created_this_week(doc))
            
            # Statistiques modèles
            stats["total_templates"] = len(getattr(self.model, "templates", []))
            stats["weekly_templates"] = sum(1 for template in getattr(self.model, "templates", [])
                                          if self._is_used_this_week(template))
            
            # Statistiques erreurs
            error_logs = self._get_recent_error_logs()
            stats["total_errors"] = len(error_logs)
            stats["recent_errors"] = sum(1 for log in error_logs 
                                       if self._is_within_last_24h(log))
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {e}")
            return {}

    def _show_error_message(self, title, message):
        """
        Affiche un message d'erreur à l'utilisateur
        """
        if hasattr(self, 'error_dialog'):
            self.error_dialog.destroy()
        
        self.error_dialog = ctk.CTkToplevel(self.frame)
        self.error_dialog.title(title)
        self.error_dialog.geometry("300x150")
        
        # Centrer la fenêtre
        self.error_dialog.update_idletasks()
        x = self.frame.winfo_rootx() + (self.frame.winfo_width() - 300) // 2
        y = self.frame.winfo_rooty() + (self.frame.winfo_height() - 150) // 2
        self.error_dialog.geometry(f"+{x}+{y}")
        
        # Message
        ctk.CTkLabel(
            self.error_dialog,
            text=message,
            wraplength=250
        ).pack(pady=20)
        
        # Bouton OK
        ctk.CTkButton(
            self.error_dialog,
            text="OK",
            command=self.error_dialog.destroy
        ).pack(pady=10)

    def _update_system_info(self):
        """
        Met à jour les informations système de manière asynchrone
        """
        try:
            # Récupérer les informations système
            system_info = self._get_system_info()
            
            # Mettre à jour l'interface
            for key, value in system_info.items():
                if key in self.system_info:
                    self.system_info[key].configure(text=value)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des informations système: {e}")
            self._show_error_message("Erreur système", "Impossible de mettre à jour les informations système")

    def _get_system_info(self):
        """
        Récupère les informations système de manière optimisée
        """
        try:
            info = {}
            
            # OS et version Python (ne change pas souvent)
            if not hasattr(self, '_static_info'):
                self._static_info = {
                    'os': f"{platform.system()} {platform.release()}",
                    'python_version': platform.python_version()
                }
            info.update(self._static_info)
            
            # CPU et mémoire (mise à jour fréquente)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            info['cpu_usage'] = f"{cpu_percent}%"
            info['memory_usage'] = f"{memory.percent}%"
            
            # Espace disque (mise à jour moins fréquente)
            if not hasattr(self, '_disk_info') or time.time() - getattr(self, '_last_disk_check', 0) > 300:
                disk = psutil.disk_usage('/')
                self._disk_info = f"{disk.percent}% utilisé"
                self._last_disk_check = time.time()
            info['disk_space'] = self._disk_info
            
            # Uptime application
            if hasattr(self.model, 'start_time'):
                uptime = datetime.now() - self.model.start_time
                hours = uptime.total_seconds() // 3600
                minutes = (uptime.total_seconds() % 3600) // 60
                info['uptime'] = f"{int(hours)}h {int(minutes)}m"
            else:
                info['uptime'] = "N/A"
            
            return info
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des informations système: {e}")
            return {}

    def _is_created_this_week(self, doc):
        """
        Vérifie si un document a été créé cette semaine
        """
        if not hasattr(doc, 'created_at'):
            return False
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        return doc.created_at >= start_of_week

    def _is_used_this_week(self, template):
        """
        Vérifie si un modèle a été utilisé cette semaine de manière plus robuste
        
        Args:
            template: Objet modèle à vérifier
            
        Returns:
            bool: True si le modèle a été utilisé cette semaine, False sinon
        """
        try:
            # Vérifier si le modèle est valide
            if not template or not isinstance(template, (dict, object)):
                logger.warning(f"Modèle invalide détecté: {template}")
                return False
            
            # Obtenir la date de dernière utilisation
            last_used = None
            if isinstance(template, dict):
                last_used = template.get('last_used')
            else:
                last_used = getattr(template, 'last_used', None)
            
            if not last_used:
                return False
            
            # Convertir en datetime si nécessaire
            if isinstance(last_used, str):
                try:
                    last_used = datetime.fromisoformat(last_used)
                except ValueError:
                    logger.error(f"Format de date invalide pour le modèle: {last_used}")
                    return False
                
            # Vérifier si utilisé cette semaine
            now = datetime.now()
            start_of_week = now - timedelta(days=now.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            
            return last_used >= start_of_week
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'utilisation du modèle: {e}")
            return False

    def get_template_statistics(self) -> Dict[str, Any]:
        """
        Récupère les statistiques détaillées des modèles
        
        Returns:
            Dict[str, Any]: Statistiques des modèles
        """
        try:
            stats = {
                "total": 0,
                "used_this_week": 0,
                "active": 0,
                "errors": 0
            }
            
            # Récupérer les modèles
            templates = []
            if hasattr(self.model, 'get_templates'):
                try:
                    templates = self.model.get_templates()
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération des modèles: {e}")
                    return stats
            
            # Calculer les statistiques
            now = datetime.now()
            thirty_days_ago = now - timedelta(days=30)
            
            for template in templates:
                try:
                    stats["total"] += 1
                    
                    # Vérifier si utilisé cette semaine
                    if self._is_used_this_week(template):
                        stats["used_this_week"] += 1
                    
                    # Vérifier si actif (utilisé dans les 30 derniers jours)
                    last_used = self._get_template_last_used(template)
                    if last_used and last_used >= thirty_days_ago:
                        stats["active"] += 1
                    
                    # Vérifier les erreurs
                    if self._has_template_errors(template):
                        stats["errors"] += 1
                    
                except Exception as e:
                    logger.error(f"Erreur lors du calcul des statistiques pour le modèle: {e}")
                    stats["errors"] += 1
                
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques des modèles: {e}")
            return {
                "total": 0,
                "used_this_week": 0,
                "active": 0,
                "errors": 0
            }

    def _get_template_last_used(self, template) -> Optional[datetime]:
        """
        Récupère la date de dernière utilisation d'un modèle
        
        Args:
            template: Objet modèle
            
        Returns:
            Optional[datetime]: Date de dernière utilisation ou None
        """
        try:
            last_used = None
            
            # Récupérer la date selon le type d'objet
            if isinstance(template, dict):
                last_used = template.get('last_used')
            else:
                last_used = getattr(template, 'last_used', None)
            
            # Convertir en datetime si nécessaire
            if isinstance(last_used, str):
                last_used = datetime.fromisoformat(last_used)
            
            return last_used
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la date de dernière utilisation: {e}")
            return None

    def _has_template_errors(self, template) -> bool:
        """
        Vérifie si un modèle a des erreurs
        
        Args:
            template: Objet modèle
            
        Returns:
            bool: True si le modèle a des erreurs, False sinon
        """
        try:
            # Vérifier les erreurs selon le type d'objet
            if isinstance(template, dict):
                return bool(template.get('has_errors') or template.get('error_count', 0) > 0)
            else:
                return bool(getattr(template, 'has_errors', False) or getattr(template, 'error_count', 0) > 0)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des erreurs du modèle: {e}")
            return True

    def update_template_card(self):
        """
        Met à jour la carte des modèles avec les dernières statistiques
        """
        try:
            # Récupérer les statistiques
            stats = self.get_template_statistics()
            
            # Mettre à jour la carte
            if hasattr(self, 'template_card'):
                self.template_card["value"].configure(text=str(stats["total"]))
                self.template_card["subtitle"].configure(
                    text=f"Utilisés cette semaine: {stats['used_this_week']}"
                )
                
                # Mettre à jour la couleur selon les erreurs
                if stats["errors"] > 0:
                    self.template_card["frame"].configure(
                        fg_color=("#ffcccc", "#5c2d2d")
                    )
                else:
                    self.template_card["frame"].configure(
                        fg_color=("#e1e5eb", "#343b48")
                    )
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la carte des modèles: {e}")
            if hasattr(self, 'template_card'):
                self.template_card["value"].configure(text="Erreur")
                self.template_card["subtitle"].configure(text="Impossible de charger les données")

    def update_system_info(self):
        """
        Met à jour les informations système
        """
        try:
            # Système d'exploitation
            os_info = f"{platform.system()} {platform.version()}"
            self.system_info["os"].configure(text=os_info)
            
            # Version Python
            python_version = platform.python_version()
            self.system_info["python_version"].configure(text=python_version)
            
            # Utilisation CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.system_info["cpu_usage"].configure(text=f"{cpu_percent}%")
            
            # Utilisation mémoire
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = self.format_bytes(memory.used)
            memory_total = self.format_bytes(memory.total)
            self.system_info["memory_usage"].configure(text=f"{memory_percent}% ({memory_used} / {memory_total})")
            
            # Espace disque
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = self.format_bytes(disk.used)
            disk_total = self.format_bytes(disk.total)
            self.system_info["disk_space"].configure(text=f"{disk_percent}% ({disk_used} / {disk_total})")
            
            # Uptime de l'application (à adapter selon votre méthode de suivi)
            if hasattr(self.model, 'start_time'):
                uptime_seconds = (datetime.now() - self.model.start_time).total_seconds()
                uptime_str = self.format_uptime(uptime_seconds)
            else:
                uptime_str = "Non disponible"
                
            self.system_info["uptime"].configure(text=uptime_str)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des informations système: {e}")
    
    def update_activities(self):
        """
        Met à jour la liste des activités administratives récentes
        """
        try:
            # Effacer les anciennes activités
            for widget in self.activities_list_frame.winfo_children():
                if widget != self.no_activities_label:
                    widget.destroy()
            
            # Récupérer les activités administratives
            admin_activities = self.get_admin_activities()
            
            if admin_activities:
                self.no_activities_label.pack_forget()
                
                # Ajouter les nouvelles activités
                for activity in admin_activities:
                    self.create_activity_item(self.activities_list_frame, activity)
            else:
                self.no_activities_label.pack(pady=20)
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des activités: {e}")
    
    def update_alerts(self):
        """
        Met à jour la liste des alertes système
        """
        try:
            # Effacer les anciennes alertes
            for widget in self.alerts_list_frame.winfo_children():
                if widget != self.no_alerts_label:
                    widget.destroy()
            
            # Récupérer les alertes système
            system_alerts = self.get_system_alerts()
            
            if system_alerts:
                self.no_alerts_label.pack_forget()
                
                # Ajouter les nouvelles alertes
                for alert in system_alerts:
                    self.create_alert_item(self.alerts_list_frame, alert)
            else:
                self.no_alerts_label.pack(pady=20)
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des alertes: {e}")
    
    def is_user_active_today(self, user):
        """
        Vérifie si un utilisateur a été actif aujourd'hui
        
        Args:
            user: Objet utilisateur
            
        Returns:
            bool: True si l'utilisateur a été actif aujourd'hui, False sinon
        """
        # À adapter selon votre modèle de données
        if hasattr(user, 'last_activity'):
            today = datetime.now().date()
            last_activity_date = user.last_activity.date() if isinstance(user.last_activity, datetime) else user.last_activity
            return last_activity_date == today
        return False
    
    def count_documents_this_week(self):
        """
        Compte le nombre de documents créés cette semaine
        
        Returns:
            int: Nombre de documents créés cette semaine
        """
        # À adapter selon votre modèle de données
        count = 0
        if hasattr(self.model, 'documents'):
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            
            for doc in self.model.documents:
                if hasattr(doc, 'created_at'):
                    doc_date = doc.created_at if isinstance(doc.created_at, datetime) else datetime.fromisoformat(doc.created_at)
                    if doc_date >= week_start:
                        count += 1
        return count
    
    def count_templates_used_this_week(self):
        """
        Compte le nombre de modèles utilisés cette semaine
        
        Returns:
            int: Nombre de modèles utilisés cette semaine
        """
        # À adapter selon votre modèle de données
        # Ceci est un exemple simplifié
        return 0
    
    def count_errors_last_24h(self):
        """
        Compte le nombre d'erreurs dans les dernières 24 heures
        
        Returns:
            int: Nombre d'erreurs dans les dernières 24 heures
        """
        # À adapter selon votre système de journalisation
        # Exemple simplifié
        return 0
    
    def get_admin_activities(self):
        """
        Récupère les activités administratives récentes
        
        Returns:
            list: Liste des activités administratives
        """
        # Récupérer depuis le modèle si disponible
        if hasattr(self.model, 'admin_activities'):
            return self.model.admin_activities
        
        # Sinon, renvoyer des données de démo
        return [
            {
                "description": "Sauvegarde du système",
                "details": "Sauvegarde complète effectuée avec succès",
                "timestamp": datetime.now().isoformat(),
                "user": "Admin"
            },
            {
                "description": "Paramètres modifiés",
                "details": "Modification des paramètres de notification",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "user": "Admin"
            },
            {
                "description": "Vérification d'intégrité",
                "details": "Aucun problème détecté",
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "user": "Système"
            }
        ]
    
    def get_system_alerts(self):
        """
        Récupère les alertes système actuelles
        
        Returns:
            list: Liste des alertes système
        """
        # Récupérer depuis le modèle si disponible
        # Récupérer depuis le modèle si disponible
        if hasattr(self.model, 'system_alerts'):
            return self.model.system_alerts
        
        # Sinon, renvoyer des données de démo
        return [
            {
                "title": "Espace disque faible",
                "message": "Il reste moins de 15% d'espace disque libre.",
                "level": "warning",
                "timestamp": datetime.now().isoformat(),
                "action": "Vérifier"
            },
            {
                "title": "Mise à jour disponible",
                "message": "Une nouvelle version (1.1.0) est disponible.",
                "level": "info",
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "action": "Mettre à jour"
            }
        ]
    
    def format_bytes(self, size_bytes):
        """
        Formate une taille en octets en une chaîne lisible
        
        Args:
            size_bytes: Taille en octets
            
        Returns:
            str: Taille formatée
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
            
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def format_uptime(self, seconds):
        """
        Formate une durée en secondes en une chaîne lisible
        
        Args:
            seconds: Durée en secondes
            
        Returns:
            str: Durée formatée
        """
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{int(days)} jours")
        if hours > 0 or days > 0:
            parts.append(f"{int(hours)} heures")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{int(minutes)} minutes")
        
        if not parts:
            return f"{int(seconds)} secondes"
        
        return ", ".join(parts)
    
    def show(self):
        """
        Affiche la vue et démarre les mises à jour
        """
        self._is_running = True
        self.frame.pack(fill=ctk.BOTH, expand=True)
        self.update_view()
    
    def hide(self):
        """
        Masque la vue et arrête les mises à jour
        """
        self._is_running = False
        if self._update_after_id:
            self.frame.after_cancel(self._update_after_id)
            self._update_after_id = None
        self.frame.pack_forget()
    
    def start_update_thread(self):
        """
        Démarre le thread de mise à jour en arrière-plan
        """
        if not self.update_thread or not self.update_thread.is_alive():
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
    
    def _update_loop(self):
        """
        Boucle de mise à jour en arrière-plan
        """
        while not self.stop_thread:
            try:
                self.update_statistics_async()
                self.update_system_info_async()
                time.sleep(5)  # Attendre 5 secondes entre les mises à jour
            except Exception as e:
                logger.error(f"Erreur dans la boucle de mise à jour: {e}")
    
    @lru_cache(maxsize=32)
    def get_cached_data(self, key: str, timeout: int = 300) -> Optional[Any]:
        """
        Récupère les données du cache si elles sont valides
        """
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp < timeout:
                return data
        return None
    
    def set_cached_data(self, key: str, data: Any):
        """
        Stocke les données dans le cache
        """
        self._cache[key] = (time.time(), data)
    
    def load_initial_data(self):
        """
        Charge les données initiales de manière asynchrone
        """
        self.show_loading_indicator()
        threading.Thread(target=self._load_initial_data_async, daemon=True).start()
    
    def _load_initial_data_async(self):
        """
        Charge les données initiales en arrière-plan
        """
        try:
            # Charger les statistiques de base rapidement
            basic_stats = self.get_basic_statistics()
            self.update_queue.put(("basic_stats", basic_stats))

            # Charger les données plus lourdes ensuite
            detailed_stats = self.get_detailed_statistics()
            self.update_queue.put(("detailed_stats", detailed_stats))

            system_info = self.get_system_info()
            self.update_queue.put(("system_info", system_info))

            # Traiter les mises à jour dans l'interface utilisateur
            self.frame.after(100, self._process_updates)
        except Exception as e:
            logger.error(f"Erreur lors du chargement initial: {e}")
        finally:
            self.hide_loading_indicator()
    
    def _process_updates(self):
        """
        Traite les mises à jour de l'interface utilisateur
        """
        try:
            while not self.update_queue.empty():
                update_type, data = self.update_queue.get_nowait()
                self._apply_update(update_type, data)
        except queue.Empty:
            pass
        finally:
            # Replanifier le traitement s'il y a encore des mises à jour
            if not self.update_queue.empty():
                self.frame.after(100, self._process_updates)
    
    def _apply_update(self, update_type: str, data: Any):
        """
        Applique une mise à jour à l'interface utilisateur
        """
        try:
            if update_type == "basic_stats":
                self.update_basic_statistics_ui(data)
            elif update_type == "detailed_stats":
                self.update_detailed_statistics_ui(data)
            elif update_type == "system_info":
                self.update_system_info_ui(data)
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la mise à jour {update_type}: {e}")
    
    def show_loading_indicator(self):
        """Affiche l'indicateur de chargement"""
        if not hasattr(self, 'loading_frame'):
            self.loading_frame = ctk.CTkFrame(self.frame)
            self.loading_frame.place(relx=0.5, rely=0.5, anchor="center")
            
            # Label de chargement
            self.loading_label = ctk.CTkLabel(
                self.loading_frame,
                text="Chargement en cours...",
                font=ctk.CTkFont(size=14)
            )
            self.loading_label.pack(pady=10)
            
            # Barre de progression
            self.loading_progress = ctk.CTkProgressBar(self.loading_frame)
            self.loading_progress.pack(pady=5)
            self.loading_progress.start()
        else:
            self.loading_frame.place(relx=0.5, rely=0.5, anchor="center")

    def hide_loading_indicator(self):
        """Cache l'indicateur de chargement"""
        if hasattr(self, 'loading_frame'):
            self.loading_frame.place_forget()
            self.loading_progress.stop()

    def get_basic_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques de base rapidement"""
        cached_data = self.get_cached_data("basic_stats")
        if cached_data:
            return cached_data

        stats = {
            "users_count": len(self.model.get_users()) if hasattr(self.model, 'get_users') else 0,
            "docs_count": len(self.model.get_documents()) if hasattr(self.model, 'get_documents') else 0,
            "templates_count": len(self.model.get_templates()) if hasattr(self.model, 'get_templates') else 0
        }
        
        self.set_cached_data("basic_stats", stats)
        return stats

    def get_detailed_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques détaillées (plus lent)"""
        cached_data = self.get_cached_data("detailed_stats")
        if cached_data:
            return cached_data

        stats = {
            "active_users": self.count_active_users(),
            "weekly_docs": self.count_documents_this_week(),
            "weekly_templates": self.count_templates_used_this_week(),
            "recent_errors": self.count_errors_last_24h()
        }
        
        self.set_cached_data("detailed_stats", stats)
        return stats

    def update_basic_statistics_ui(self, stats: Dict[str, Any]):
        """Met à jour l'interface avec les statistiques de base"""
        if hasattr(self, 'user_card'):
            self.user_card.configure(text=str(stats["users_count"]))
        if hasattr(self, 'document_card'):
            self.document_card.configure(text=str(stats["docs_count"]))
        if hasattr(self, 'template_card'):
            self.template_card.configure(text=str(stats["templates_count"]))

    def update_detailed_statistics_ui(self, stats: Dict[str, Any]):
        """Met à jour l'interface avec les statistiques détaillées"""
        if hasattr(self, 'user_card_subtitle'):
            self.user_card_subtitle.configure(text=f"Actifs aujourd'hui: {stats['active_users']}")
        if hasattr(self, 'document_card_subtitle'):
            self.document_card_subtitle.configure(text=f"Créés cette semaine: {stats['weekly_docs']}")
        if hasattr(self, 'template_card_subtitle'):
            self.template_card_subtitle.configure(text=f"Utilisés cette semaine: {stats['weekly_templates']}")
        if hasattr(self, 'error_card_subtitle'):
            self.error_card_subtitle.configure(text=f"Dernières 24h: {stats['recent_errors']}")

    def update_system_info_ui(self, info: Dict[str, Any]):
        """Met à jour l'interface avec les informations système"""
        if hasattr(self, 'system_info_frame'):
            cpu_usage = info.get('cpu_usage', 0)
            memory_usage = info.get('memory_usage', 0)
            disk_usage = info.get('disk_usage', 0)
            
            if hasattr(self, 'cpu_progress'):
                self.cpu_progress.set(cpu_usage / 100)
                self.cpu_label.configure(text=f"CPU: {cpu_usage:.1f}%")
            
            if hasattr(self, 'memory_progress'):
                self.memory_progress.set(memory_usage / 100)
                self.memory_label.configure(text=f"Mémoire: {memory_usage:.1f}%")
            
            if hasattr(self, 'disk_progress'):
                self.disk_progress.set(disk_usage / 100)
                self.disk_label.configure(text=f"Disque: {disk_usage:.1f}%")

    def update_statistics_async(self):
        """Met à jour les statistiques de manière asynchrone"""
        try:
            basic_stats = self.get_basic_statistics()
            self.update_queue.put(("basic_stats", basic_stats))
            
            detailed_stats = self.get_detailed_statistics()
            self.update_queue.put(("detailed_stats", detailed_stats))
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des statistiques: {e}")

    def update_system_info_async(self):
        """Met à jour les informations système de manière asynchrone"""
        try:
            system_info = self.get_system_info()
            self.update_queue.put(("system_info", system_info))
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des informations système: {e}")
    
    def perform_backup_stub(self):
        """
        Méthode de substitution pour la sauvegarde
        """
        self.show_message(
            "Information",
            "La fonctionnalité de sauvegarde est en cours d'implémentation.",
            "info"
        )
        
        # Essayer d'appeler la méthode du contrôleur si disponible
        if hasattr(self.model, 'perform_backup'):
            return self.model.perform_backup()
        return False
    
    def check_integrity_stub(self):
        """
        Méthode de substitution pour la vérification d'intégrité
        """
        self.show_message(
            "Information",
            "La fonctionnalité de vérification d'intégrité est en cours d'implémentation.",
            "info"
        )
        
        # Essayer d'appeler la méthode du contrôleur si disponible
        if hasattr(self.model, 'check_integrity'):
            return self.model.check_integrity()
        return False
    
    def optimize_app_stub(self):
        """
        Méthode de substitution pour l'optimisation
        """
        self.show_message(
            "Information",
            "La fonctionnalité d'optimisation est en cours d'implémentation.",
            "info"
        )
        
        # Essayer d'appeler la méthode du contrôleur si disponible
        if hasattr(self.model, 'optimize_app'):
            return self.model.optimize_app()
        return False
    
    def handle_alert_action_stub(self, alert):
        """
        Méthode de substitution pour gérer les actions d'alerte
        """
        self.show_message(
            "Action d'alerte",
            f"Action '{alert.get('action')}' pour l'alerte '{alert.get('title')}'",
            "info"
        )
        
        # Essayer d'appeler la méthode du contrôleur si disponible
        if hasattr(self.model, 'handle_alert_action'):
            return self.model.handle_alert_action(alert)
        return False
    
    def show_message(self, title, message, message_type="info", is_progress=False):
        """
        Affiche un message dans une boîte de dialogue
        
        Args:
            title: Titre du message
            message: Contenu du message
            message_type: Type de message ('info', 'success', 'warning', 'error')
            is_progress: Indique s'il s'agit d'un message de progression
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
        
        if is_progress:
            # Ajouter une barre de progression
            progress = ctk.CTkProgressBar(content_frame)
            progress.pack(fill=ctk.X, pady=10)
            progress.configure(mode="indeterminate")
            progress.start()
        else:
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

    def cleanup(self):
        """
        Nettoie les ressources utilisées par la vue
        """
        self._is_running = False
        if self._update_after_id:
            self.frame.after_cancel(self._update_after_id)
            self._update_after_id = None
        
        # Vider la file d'attente
        while not self.update_queue.empty():
            try:
                self.update_queue.get_nowait()
            except queue.Empty:
                break
        
        # Nettoyer les widgets
        for widget in self.frame.winfo_children():
            widget.destroy()
        
        logger.info("Nettoyage du tableau de bord effectué")