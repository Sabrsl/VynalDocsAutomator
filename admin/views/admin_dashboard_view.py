#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vue du tableau de bord administrateur pour l'application Vynal Docs Automator
Version améliorée avec meilleure gestion de l'espace
"""

import logging
import customtkinter as ctk
from datetime import datetime, timedelta
import os
import platform
import psutil

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
        
        # Création de l'interface
        self.create_widgets()
        
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
        Met à jour la vue avec les données actuelles
        """
        # Mettre à jour les statistiques
        self.update_statistics()
        
        # Mettre à jour les informations système
        self.update_system_info()
        
        # Mettre à jour les activités récentes
        self.update_activities()
        
        # Mettre à jour les alertes
        self.update_alerts()
        
        logger.info("Vue du tableau de bord administrateur mise à jour")
    
    def update_statistics(self):
        """
        Met à jour les statistiques affichées
        """
        try:
            # Nombre d'utilisateurs (à adapter selon votre modèle)
            if hasattr(self.model, 'users'):
                users_count = len(self.model.users)
                active_users = sum(1 for user in self.model.users if self.is_user_active_today(user))
            else:
                users_count = 0
                active_users = 0
            
            self.user_card["value"].configure(text=str(users_count))
            self.user_card["subtitle"].configure(text=f"Actifs aujourd'hui: {active_users}")
            
            # Nombre de documents
            documents_count = len(self.model.documents) if hasattr(self.model, 'documents') else 0
            documents_this_week = self.count_documents_this_week()
            
            self.document_card["value"].configure(text=str(documents_count))
            self.document_card["subtitle"].configure(text=f"Créés cette semaine: {documents_this_week}")
            
            # Nombre de modèles
            templates_count = len(self.model.templates) if hasattr(self.model, 'templates') else 0
            templates_used = self.count_templates_used_this_week()
            
            self.template_card["value"].configure(text=str(templates_count))
            self.template_card["subtitle"].configure(text=f"Utilisés cette semaine: {templates_used}")
            
            # Nombre d'erreurs (à adapter selon votre gestion des logs)
            error_count = self.count_errors_last_24h()
            
            self.error_card["value"].configure(text=str(error_count))
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des statistiques: {e}")
    
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
        Affiche la vue du tableau de bord
        """
        self.frame.pack(fill=ctk.BOTH, expand=True)
        self.update_view()
    
    def hide(self):
        """
        Masque la vue du tableau de bord
        """
        self.frame.pack_forget()
    
    # Méthodes ajoutées pour résoudre les problèmes de compatibilité
    
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