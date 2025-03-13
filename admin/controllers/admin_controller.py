#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contrôleur d'administration pour l'application Vynal Docs Automator
Gère la communication entre les vues administratives et les modèles
"""

import logging
import os
import shutil
import json
from datetime import datetime
import threading
import time
import zipfile
import tarfile
import customtkinter as ctk

logger = logging.getLogger("VynalDocsAutomator.Admin.Controller")

class AdminController:
    """
    Contrôleur principal pour l'interface d'administration
    Coordonne les actions entre les vues et les modèles
    """
    
    def __init__(self, admin_main, app_model):
        """
        Initialise le contrôleur d'administration
        
        Args:
            admin_main: Instance principale de l'interface d'administration
            app_model: Modèle de l'application principale
        """
        self.admin_main = admin_main
        self.app_model = app_model
        
        # Initialiser le gestionnaire de permissions
        from admin.utils.admin_permissions import AdminPermissions
        self.permissions = AdminPermissions(app_model)
        
        # Référence aux vues administatives
        self.dashboard_view = None
        self.user_management_view = None
        self.system_logs_view = None
        self.settings_view = None
        
        # Variables de suivi
        self.backup_in_progress = False
        self.integrity_check_in_progress = False
        self.optimization_in_progress = False
        self.system_monitor_thread = None
        self.stop_monitoring = False
        
        # Journal des activités d'administration
        self.admin_activities = []
        
        # Initialiser les vues
        self.init_views()
        
        # Démarrer la surveillance du système
        self.start_system_monitoring()
        
        logger.info("Contrôleur d'administration initialisé")
    
    def init_views(self):
        """
        Initialise les références aux vues et configure les callbacks
        """
        if hasattr(self.admin_main, 'views'):
            # Récupérer les références aux vues
            self.dashboard_view = self.admin_main.views.get('dashboard')
            self.user_management_view = self.admin_main.views.get('users')
            self.system_logs_view = self.admin_main.views.get('system')
            self.settings_view = self.admin_main.views.get('settings')
            
            # Configurer les callbacks pour le tableau de bord
            if self.dashboard_view:
                # Remplacer les méthodes par défaut par nos implémentations
                self.dashboard_view.perform_backup = self.perform_backup
                self.dashboard_view.check_integrity = self.check_integrity
                self.dashboard_view.optimize_app = self.optimize_app
                self.dashboard_view.handle_alert_action = self.handle_alert_action
            
            # Autres configurations de callbacks peuvent être ajoutées ici
            
            logger.info("Références aux vues administratives initialisées")
    
    def start_system_monitoring(self):
        """
        Démarre la surveillance du système en arrière-plan
        """
        self.stop_monitoring = False
        
        def monitor_system():
            while not self.stop_monitoring:
                try:
                    # Mettre à jour les données du système si le tableau de bord est visible
                    if self.dashboard_view and self.dashboard_view.frame.winfo_ismapped():
                        # Vérifier les seuils critiques
                        self.check_system_thresholds()
                        
                        # Mettre à jour l'interface si dans le thread principal
                        self.admin_main.parent.after(0, self.dashboard_view.update_view)
                except Exception as e:
                    logger.error(f"Erreur lors de la surveillance du système: {e}")
                
                # Pause avant la prochaine mise à jour
                time.sleep(5)  # Actualisation toutes les 5 secondes
        
        # Démarrer dans un thread séparé
        self.system_monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        self.system_monitor_thread.start()
        
        logger.info("Surveillance du système démarrée")
    
    def stop_system_monitoring(self):
        """
        Arrête la surveillance du système
        """
        self.stop_monitoring = True
        if self.system_monitor_thread:
            self.system_monitor_thread.join(timeout=1.0)
        logger.info("Surveillance du système arrêtée")
    
    def check_system_thresholds(self):
        """
        Vérifie les seuils critiques du système et génère des alertes si nécessaire
        """
        try:
            import psutil
            
            # Vérifier l'utilisation du CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > 80:
                self.add_system_alert(
                    "Utilisation CPU élevée",
                    f"L'utilisation du CPU est de {cpu_percent}%, ce qui peut affecter les performances.",
                    "warning"
                )
            
            # Vérifier l'utilisation de la mémoire
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                self.add_system_alert(
                    "Mémoire faible",
                    f"Utilisation de la mémoire: {memory.percent}%. Pensez à fermer des applications inutilisées.",
                    "warning"
                )
            
            # Vérifier l'espace disque
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.add_system_alert(
                    "Espace disque faible",
                    f"Il reste seulement {100 - disk.percent}% d'espace disque libre.",
                    "critical" if disk.percent > 95 else "warning"
                )
            
            # Vérifier les mises à jour (simulation)
            if self.is_update_available():
                self.add_system_alert(
                    "Mise à jour disponible",
                    "Une nouvelle version de l'application est disponible.",
                    "info",
                    "Mettre à jour"
                )
            
            # Vérifier la date de la dernière sauvegarde
            last_backup = self.get_last_backup_time()
            if last_backup and (datetime.now() - last_backup).days > 7:
                self.add_system_alert(
                    "Sauvegarde obsolète",
                    f"La dernière sauvegarde date de {(datetime.now() - last_backup).days} jours.",
                    "warning",
                    "Sauvegarder maintenant"
                )
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des seuils système: {e}")
    
    def add_system_alert(self, title, message, level="info", action=None):
        """
        Ajoute une alerte système
        
        Args:
            title: Titre de l'alerte
            message: Message détaillé
            level: Niveau de l'alerte ('info', 'warning', 'critical')
            action: Action possible (texte du bouton)
        """
        # Vérifier si une alerte similaire existe déjà
        for alert in self.app_model.system_alerts if hasattr(self.app_model, 'system_alerts') else []:
            if alert.get("title") == title and alert.get("level") == level:
                # Mettre à jour l'alerte existante plutôt qu'en ajouter une nouvelle
                alert["timestamp"] = datetime.now().isoformat()
                alert["message"] = message
                alert["action"] = action
                return
        
        # Créer une nouvelle alerte
        new_alert = {
            "title": title,
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat(),
            "action": action
        }
        
        # Ajouter au modèle si possible
        if hasattr(self.app_model, 'system_alerts'):
            self.app_model.system_alerts.append(new_alert)
        elif hasattr(self.app_model, 'add_system_alert'):
            self.app_model.add_system_alert(new_alert)
        
        logger.info(f"Alerte système ajoutée: {title} ({level})")
    
    def add_admin_activity(self, description, details=None, user=None):
        """
        Ajoute une activité administrative au journal
        
        Args:
            description: Description de l'activité
            details: Détails supplémentaires
            user: Utilisateur qui a effectué l'action
        """
        # Créer l'enregistrement d'activité
        activity = {
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "type": "admin"
        }
        
        if details:
            activity["details"] = details
        
        if user:
            activity["user"] = user
        else:
            # Récupérer l'utilisateur courant si disponible
            if hasattr(self.app_model, 'current_user') and self.app_model.current_user:
                activity["user"] = self.app_model.current_user.get('username', 'Admin')
            else:
                activity["user"] = "Admin"
        
        # Ajouter au journal local
        self.admin_activities.append(activity)
        
        # Ajouter au modèle si possible
        if hasattr(self.app_model, 'add_activity'):
            self.app_model.add_activity(activity)
        
        logger.info(f"Activité administrative ajoutée: {description}")
    
    def perform_backup(self):
        """
        Effectue une sauvegarde complète des données de l'application
        
        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        # Vérifier les permissions
        try:
            self.permissions.check_permission('admin.system.backup')
        except PermissionDenied:
            if self.dashboard_view:
                self.dashboard_view.show_message(
                    "Accès refusé", 
                    "Vous n'avez pas les permissions nécessaires pour effectuer une sauvegarde.", 
                    message_type="error"
                )
            return False
        
        if self.backup_in_progress:
            logger.warning("Une sauvegarde est déjà en cours")
            return False
        
        self.backup_in_progress = True
        
        def backup_task():
            success = False
            try:
                # Afficher un message de progression
                if self.dashboard_view:
                    self.admin_main.parent.after(0, lambda: self.dashboard_view.show_message(
                        "Sauvegarde", "Sauvegarde des données en cours...", is_progress=True
                    ))
                
                # Déterminer le répertoire des données
                data_dir = self.get_data_dir()
                backup_dir = self.get_backup_dir()
                
                # Créer le répertoire de sauvegarde s'il n'existe pas
                os.makedirs(backup_dir, exist_ok=True)
                
                # Générer un nom de fichier pour la sauvegarde
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_format = self.get_backup_format()
                backup_file = os.path.join(backup_dir, f"backup_{timestamp}.{backup_format}")
                
                # Effectuer la sauvegarde selon le format
                if backup_format == "zip":
                    with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        self.add_dir_to_archive(zipf, data_dir, os.path.basename(data_dir))
                
                elif backup_format in ["tar", "tar.gz"]:
                    mode = "w:gz" if backup_format == "tar.gz" else "w"
                    with tarfile.open(backup_file, mode) as tarf:
                        tarf.add(data_dir, arcname=os.path.basename(data_dir))
                
                # Nettoyer les anciennes sauvegardes
                self.cleanup_old_backups()
                
                # Mettre à jour le timestamp de la dernière sauvegarde
                self.update_last_backup_time()
                
                # Ajouter une activité administrative
                self.add_admin_activity(
                    "Sauvegarde complète effectuée",
                    f"Sauvegarde créée: {os.path.basename(backup_file)}"
                )
                
                success = True
                
                # Afficher un message de succès
                if self.dashboard_view:
                    self.admin_main.parent.after(0, lambda: self.dashboard_view.show_message(
                        "Sauvegarde terminée", 
                        f"Les données ont été sauvegardées avec succès dans:\n{backup_file}", 
                        message_type="success"
                    ))
                
                logger.info(f"Sauvegarde complète effectuée: {backup_file}")
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde: {e}")
                
                # Afficher un message d'erreur
                if self.dashboard_view:
                    self.admin_main.parent.after(0, lambda: self.dashboard_view.show_message(
                        "Erreur de sauvegarde", 
                        f"Une erreur est survenue: {e}", 
                        message_type="error"
                    ))
            finally:
                self.backup_in_progress = False
                
                # Mettre à jour la vue
                if self.dashboard_view:
                    self.admin_main.parent.after(0, self.dashboard_view.update_view)
                
                return success
        
        # Exécuter la tâche dans un thread séparé
        threading.Thread(target=backup_task, daemon=True).start()
        return True
    
    def check_integrity(self):
        """
        Vérifie l'intégrité des données de l'application
        
        Returns:
            bool: True si la vérification a réussi, False sinon
        """
        if self.integrity_check_in_progress:
            logger.warning("Une vérification d'intégrité est déjà en cours")
            return False
        
        self.integrity_check_in_progress = True
        
        def integrity_check_task():
            success = False
            try:
                # Afficher un message de progression
                if self.dashboard_view:
                    self.admin_main.parent.after(0, lambda: self.dashboard_view.show_message(
                        "Vérification", "Vérification de l'intégrité des données...", is_progress=True
                    ))
                
                # Simuler une vérification d'intégrité
                time.sleep(2)  # Simule un traitement long
                
                # Dans une implémentation réelle, vous devriez:
                # 1. Vérifier la structure des fichiers de données
                # 2. Vérifier la cohérence des données (références, clés étrangères, etc.)
                # 3. Tenter de corriger les problèmes si possible
                
                # Ici, nous simulons simplement une vérification réussie
                all_ok = True
                issues_found = []
                
                # Vérification des fichiers JSON
                data_dir = self.get_data_dir()
                for root, _, files in os.walk(data_dir):
                    for file in files:
                        if file.endswith('.json'):
                            file_path = os.path.join(root, file)
                            try:
                                # Tenter de charger le fichier JSON
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    json.load(f)
                            except json.JSONDecodeError as e:
                                all_ok = False
                                issues_found.append(f"Fichier JSON corrompu: {file} ({e})")
                
                # Ajouter une activité administrative
                self.add_admin_activity(
                    "Vérification d'intégrité effectuée",
                    f"Résultat: {'Aucun problème détecté' if all_ok else f'{len(issues_found)} problèmes trouvés'}"
                )
                
                success = True
                
                # Afficher le résultat
                if self.dashboard_view:
                    if all_ok:
                        self.admin_main.parent.after(0, lambda: self.dashboard_view.show_message(
                            "Vérification terminée", 
                            "Aucun problème d'intégrité détecté dans les données.", 
                            message_type="success"
                        ))
                    else:
                        issues_text = "\n".join(issues_found[:5])
                        if len(issues_found) > 5:
                            issues_text += f"\n... et {len(issues_found) - 5} autres problèmes."
                        
                        self.admin_main.parent.after(0, lambda: self.dashboard_view.show_message(
                            "Problèmes détectés", 
                            f"{len(issues_found)} problèmes d'intégrité détectés:\n\n{issues_text}", 
                            message_type="warning"
                        ))
                
                logger.info(f"Vérification d'intégrité effectuée: {len(issues_found)} problèmes trouvés")
            except Exception as e:
                logger.error(f"Erreur lors de la vérification d'intégrité: {e}")
                
                # Afficher un message d'erreur
                if self.dashboard_view:
                    self.admin_main.parent.after(0, lambda: self.dashboard_view.show_message(
                        "Erreur de vérification", 
                        f"Une erreur est survenue: {e}", 
                        message_type="error"
                    ))
            finally:
                self.integrity_check_in_progress = False
                
                # Mettre à jour la vue
                if self.dashboard_view:
                    self.admin_main.parent.after(0, self.dashboard_view.update_view)
                
                return success
        
        # Exécuter la tâche dans un thread séparé
        threading.Thread(target=integrity_check_task, daemon=True).start()
        return True
    
    def optimize_app(self):
        """
        Optimise les performances de l'application
        
        Returns:
            bool: True si l'optimisation a réussi, False sinon
        """
        if self.optimization_in_progress:
            logger.warning("Une optimisation est déjà en cours")
            return False
        
        self.optimization_in_progress = True
        
        def optimization_task():
            success = False
            try:
                # Afficher un message de progression
                if self.dashboard_view:
                    self.admin_main.parent.after(0, lambda: self.dashboard_view.show_message(
                        "Optimisation", "Optimisation des performances en cours...", is_progress=True
                    ))
                
                # Simuler une optimisation
                time.sleep(2.5)  # Simule un traitement long
                
                # Dans une implémentation réelle, vous pourriez:
                # 1. Nettoyer les fichiers temporaires
                # 2. Compacter les bases de données
                # 3. Défragmenter les fichiers de données
                # 4. Précompiler des ressources
                
                # Ici, nous effectuons quelques optimisations simples
                
                # 1. Nettoyer les fichiers temporaires
                temp_dir = os.path.join(self.get_data_dir(), "temp")
                if os.path.exists(temp_dir):
                    for item in os.listdir(temp_dir):
                        item_path = os.path.join(temp_dir, item)
                        try:
                            if os.path.isfile(item_path):
                                os.unlink(item_path)
                            elif os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                        except Exception as e:
                            logger.warning(f"Erreur lors de la suppression de {item_path}: {e}")
                
                # 2. Nettoyer les anciens logs
                logs_dir = self.get_logs_dir()
                if os.path.exists(logs_dir):
                    now = datetime.now()
                    for log_file in os.listdir(logs_dir):
                        if log_file.endswith('.log'):
                            log_path = os.path.join(logs_dir, log_file)
                            file_time = datetime.fromtimestamp(os.path.getmtime(log_path))
                            
                            # Supprimer les logs de plus de 30 jours
                            if (now - file_time).days > 30:
                                try:
                                    os.unlink(log_path)
                                    logger.info(f"Log ancien supprimé: {log_file}")
                                except Exception as e:
                                    logger.warning(f"Erreur lors de la suppression de {log_path}: {e}")
                
                # Ajouter une activité administrative
                self.add_admin_activity(
                    "Optimisation effectuée",
                    "Fichiers temporaires et anciens logs nettoyés"
                )
                
                success = True
                
                # Afficher un message de succès
                if self.dashboard_view:
                    self.admin_main.parent.after(0, lambda: self.dashboard_view.show_message(
                        "Optimisation terminée", 
                        "L'application a été optimisée avec succès.", 
                        message_type="success"
                    ))
                
                logger.info("Optimisation de l'application effectuée avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de l'optimisation: {e}")
                
                # Afficher un message d'erreur
                if self.dashboard_view:
                    self.admin_main.parent.after(0, lambda: self.dashboard_view.show_message(
                        "Erreur d'optimisation", 
                        f"Une erreur est survenue: {e}", 
                        message_type="error"
                    ))
            finally:
                self.optimization_in_progress = False
                
                # Mettre à jour la vue
                if self.dashboard_view:
                    self.admin_main.parent.after(0, self.dashboard_view.update_view)
                
                return success
        
        # Exécuter la tâche dans un thread séparé
        threading.Thread(target=optimization_task, daemon=True).start()
        return True
    
    def handle_alert_action(self, alert):
        """
        Gère l'action associée à une alerte
        
        Args:
            alert: Dictionnaire contenant les données de l'alerte
        """
        title = alert.get("title", "")
        action = alert.get("action", "")
        
        # Traiter différentes actions selon le titre de l'alerte
        if "Espace disque" in title:
            # Lancer la vérification de l'espace disque et suggérer des fichiers à supprimer
            if self.dashboard_view:
                self.dashboard_view.show_message(
                    "Vérification de l'espace disque",
                    "Vérification en cours...",
                    is_progress=True
                )
                
                # Simuler une vérification
                self.admin_main.parent.after(2000, lambda: self.show_disk_space_report())
        
        elif "Mise à jour" in title:
            # Lancer le processus de mise à jour
            if self.dashboard_view:
                self.dashboard_view.show_message(
                    "Mise à jour",
                    "Vérification des mises à jour disponibles...",
                    is_progress=True
                )
                
                # Simuler une vérification
                self.admin_main.parent.after(2000, lambda: self.show_update_info())
        
        elif "Sauvegarde" in title and action == "Sauvegarder maintenant":
            # Lancer une sauvegarde
            self.perform_backup()
        
        logger.info(f"Action traitée pour l'alerte: {title}")
    
    def show_disk_space_report(self):
        """
        Affiche un rapport sur l'utilisation de l'espace disque
        """
        try:
            import psutil
            
            # Obtenir l'utilisation du disque
            disk = psutil.disk_usage('/')
            
            # Construire un rapport
            report = f"Utilisation du disque: {disk.percent}%\n"
            report += f"Espace total: {self.format_bytes(disk.total)}\n"
            report += f"Espace utilisé: {self.format_bytes(disk.used)}\n"
            report += f"Espace libre: {self.format_bytes(disk.free)}\n\n"
            
            # Suggérer des actions
            report += "Suggestions pour libérer de l'espace:\n\n"
            report += "1. Supprimer les anciennes sauvegardes\n"
            report += "2. Nettoyer les fichiers temporaires\n"
            report += "3. Archiver d'anciens documents\n"
            
            # Afficher le rapport
            if self.dashboard_view:
                self.dashboard_view.show_message(
                    "Rapport d'espace disque",
                    report,
                    message_type="info"
                )
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport d'espace disque: {e}")
            
            if self.dashboard_view:
                self.dashboard_view.show_message(
                    "Erreur",
                    f"Impossible de générer le rapport: {e}",
                    message_type="error"
                )
    
    def show_update_info(self):
        """
        Affiche les informations sur la mise à jour disponible
        """
        # Simuler les informations de mise à jour
        current_version = self.app_model.config.get("app.version", "1.0.0")
        new_version = "1.1.0"  # Simulé
        
        # Construire le message
        message = f"Une nouvelle version de l'application est disponible!\n\n"
        message += f"Version actuelle: {current_version}\n"
        message += f"Nouvelle version: {new_version}\n\n"
        message += "Nouveautés:\n"
        message += "- Améliorations de l'interface utilisateur\n"
        message += "- Nouvelles fonctionnalités de gestion documentaire\n"
        message += "- Corrections de bugs\n\n"
        message += "Pour mettre à jour, téléchargez la nouvelle version depuis notre site web."
        
        # Afficher le message
        if self.dashboard_view:
            self.dashboard_view.show_message(
                "Mise à jour disponible",
                message,
                message_type="info"
            )
    
    def is_update_available(self):
        """
        Vérifie si une mise à jour est disponible
        
        Returns:
            bool: True si une mise à jour est disponible, False sinon
        """
        # Dans une implémentation réelle, vous devriez vérifier en ligne
        # Ici, nous simulons qu'une mise à jour est disponible une fois sur cinq
        import random
        return random.random() < 0.2
    
    def get_last_backup_time(self):
        """
        Récupère la date de la dernière sauvegarde
        
        Returns:
            datetime: Date de la dernière sauvegarde ou None si aucune sauvegarde
        """
        backup_dir = self.get_backup_dir()
        if not os.path.exists(backup_dir):
            return None
        
        backup_files = []
        for file in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, file)
            if os.path.isfile(file_path) and file.startswith("backup_"):
                backup_files.append(file_path)
        
        if not backup_files:
            return None
        
        # Trier par date de modification
        backup_files.sort(key=os.path.getmtime, reverse=True)
        
        # Retourner la date de la dernière sauvegarde
        return datetime.fromtimestamp(os.path.getmtime(backup_files[0]))
    
    def update_last_backup_time(self):
        """
        Met à jour la date de la dernière sauvegarde
        """
        # Simuler la mise à jour
        # Dans une implémentation réelle, vous pourriez stocker cette valeur dans la configuration
        pass
    
    def cleanup_old_backups(self):
        """
        Supprime les anciennes sauvegardes en fonction du nombre maximum à conserver
        """
        backup_dir = self.get_backup_dir()
        backup_files = []
        
        for file in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, file)
            if os.path.isfile(file_path) and file.startswith("backup_"):
                backup_files.append(file_path)
        
        # Trier par date de modification (plus ancien en premier)
        backup_files.sort(key=os.path.getmtime)
        
        # Déterminer le nombre maximum de sauvegardes à conserver
        max_backups = self.get_max_backups()
        
        # Supprimer les sauvegardes excédentaires
        if len(backup_files) > max_backups:
            for file_path in backup_files[:-max_backups]:
                try:
                    os.remove(file_path)
                    logger.info(f"Ancienne sauvegarde supprimée: {os.path.basename(file_path)}")
                except Exception as e:
                    logger.error(f"Erreur lors de la suppression de {file_path}: {e}")
    
    def add_dir_to_archive(self, archive, dir_path, base_dir=""):
        """
        Ajoute récursivement un répertoire à une archive ZIP
        
        Args:
            archive: Objet ZipFile
            dir_path: Chemin du répertoire à ajouter
            base_dir: Répertoire de base dans l'archive
        """
        for root, dirs, files in os.walk(dir_path):
            # Calculer le chemin relatif
            rel_dir = os.path.relpath(root, dir_path)
            
            # Créer l'entrée du répertoire dans l'archive
            if rel_dir != '.':
                archive_dir = os.path.join(base_dir, rel_dir)
            else:
                archive_dir = base_dir
            
            # Ajouter chaque fichier à l'archive
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.join(archive_dir, file)
                archive.write(file_path, arcname)
    
    def get_data_dir(self):
        """
        Récupère le répertoire des données
        
        Returns:
            str: Chemin vers le répertoire des données
        """
        # Récupérer depuis le modèle si disponible
        if hasattr(self.app_model, 'data_dir'):
            return self.app_model.data_dir
        
        # Récupérer depuis la configuration
        if hasattr(self.app_model, 'config'):
            data_dir = self.app_model.config.get('storage.data_dir')
            if data_dir:
                return data_dir
        
        # Répertoire par défaut
        return os.path.join(os.path.expanduser("~"), ".vynal_docs_automator", "data")
    
    def get_logs_dir(self):
        """
        Récupère le répertoire des logs
        
        Returns:
            str: Chemin vers le répertoire des logs
        """
        # Récupérer depuis le modèle si disponible
        if hasattr(self.app_model, 'logs_dir'):
            return self.app_model.logs_dir
        
        # Récupérer depuis la configuration
        if hasattr(self.app_model, 'config'):
            logs_dir = self.app_model.config.get('storage.logs_dir')
            if logs_dir:
                return logs_dir
        
        # Répertoire par défaut
        return os.path.join(os.path.expanduser("~"), ".vynal_docs_automator", "logs")
    
    def get_backup_dir(self):
        """
        Récupère le répertoire des sauvegardes
        
        Returns:
            str: Chemin vers le répertoire des sauvegardes
        """
        # Récupérer depuis le modèle si disponible
        if hasattr(self.app_model, 'backup_dir'):
            return self.app_model.backup_dir
        
        # Récupérer depuis la configuration
        if hasattr(self.app_model, 'config'):
            backup_dir = self.app_model.config.get('storage.backup_dir')
            if backup_dir:
                return backup_dir
        
        # Répertoire par défaut
        return os.path.join(os.path.expanduser("~"), ".vynal_docs_automator", "backups")
    
    def get_backup_format(self):
        """
        Récupère le format de sauvegarde
        
        Returns:
            str: Format de sauvegarde ('zip', 'tar', 'tar.gz')
        """
        # Récupérer depuis la configuration
        if hasattr(self.app_model, 'config'):
            format = self.app_model.config.get('storage.backup_format')
            if format in ['zip', 'tar', 'tar.gz']:
                return format
        
        # Format par défaut
        return "zip"
    
    def get_max_backups(self):
        """
        Récupère le nombre maximum de sauvegardes à conserver
        
        Returns:
            int: Nombre maximum de sauvegardes
        """
        # Récupérer depuis la configuration
        if hasattr(self.app_model, 'config'):
            try:
                count = int(self.app_model.config.get('storage.backup_count', 5))
                return max(1, count)  # Au moins 1
            except (ValueError, TypeError):
                pass
        
        # Valeur par défaut
        return 5
    
    def format_bytes(self, bytes_value):
        """
        Formate une valeur en octets en une chaîne lisible (Ko, Mo, Go)
        
        Args:
            bytes_value: Valeur en octets
            
        Returns:
            str: Chaîne formatée
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    def get_admin_activities(self):
        """
        Récupère les activités administratives récentes
        
        Returns:
            list: Liste des activités administratives
        """
        # Si le modèle a une méthode pour récupérer les activités, l'utiliser
        if hasattr(self.app_model, 'get_activities'):
            activities = self.app_model.get_activities(activity_type="admin", limit=10)
            if activities:
                return activities
        
        # Sinon, utiliser le journal local
        return sorted(self.admin_activities, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
    
    def get_system_alerts(self):
        """
        Récupère les alertes système actives
        
        Returns:
            list: Liste des alertes système
        """
        # Si le modèle a des alertes système, les utiliser
        if hasattr(self.app_model, 'system_alerts'):
            return sorted(self.app_model.system_alerts, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Sinon, créer quelques alertes par défaut pour la démonstration
        return [
            {
                "title": "Démo d'alerte",
                "message": "Ceci est une alerte de démonstration",
                "level": "info",
                "timestamp": datetime.now().isoformat(),
                "action": "Ignorer"
            }
        ]
    
    def manage_user(self, action, user_data=None):
        """
        Gère les opérations sur les utilisateurs
        
        Args:
            action: Action à effectuer ('create', 'update', 'delete')
            user_data: Données de l'utilisateur (pour create/update)
            
        Returns:
            tuple: (success, message)
        """
        # Vérifier les permissions
        try:
            if action == "create":
                self.permissions.check_permission('admin.users.create')
            elif action == "update":
                self.permissions.check_permission('admin.users.edit')
            elif action == "delete":
                self.permissions.check_permission('admin.users.delete')
            else:
                return False, f"Action non reconnue: {action}"
        except PermissionDenied:
            return False, "Vous n'avez pas les permissions nécessaires pour cette action"
        
        if action == "create":
            # Vérifier les données requises
            if not user_data or 'email' not in user_data:
                return False, "Email requis"
            
            # Vérifier si l'utilisateur existe déjà
            if hasattr(self.app_model, 'users'):
                for user in self.app_model.users:
                    if user.get('email') == user_data.get('email'):
                        return False, "Un utilisateur avec cet email existe déjà"
            
            # Générer un ID pour le nouvel utilisateur
            user_data['id'] = self.generate_user_id()
            user_data['created_at'] = datetime.now().isoformat()
            
            # Ajouter l'utilisateur au modèle
            if hasattr(self.app_model, 'add_user'):
                success = self.app_model.add_user(user_data)
            elif hasattr(self.app_model, 'users'):
                self.app_model.users.append(user_data)
                success = True
            else:
                return False, "Modèle d'utilisateur non disponible"
            
            # Ajouter une activité administrative
            if success:
                self.add_admin_activity(
                    "Nouvel utilisateur créé",
                    f"Email: {user_data.get('email')}, Rôle: {user_data.get('role', 'user')}"
                )
                return True, "Utilisateur créé avec succès"
            else:
                return False, "Erreur lors de la création de l'utilisateur"
        
        elif action == "update":
            # Vérifier les données requises
            if not user_data or 'id' not in user_data:
                return False, "ID utilisateur requis"
            
            # Mettre à jour l'utilisateur dans le modèle
            user_data['updated_at'] = datetime.now().isoformat()
            
            if hasattr(self.app_model, 'update_user'):
                success = self.app_model.update_user(user_data)
            elif hasattr(self.app_model, 'users'):
                # Rechercher et mettre à jour l'utilisateur
                for i, user in enumerate(self.app_model.users):
                    if user.get('id') == user_data.get('id'):
                        self.app_model.users[i] = user_data
                        success = True
                        break
                else:
                    return False, "Utilisateur non trouvé"
            else:
                return False, "Modèle d'utilisateur non disponible"
            
            # Ajouter une activité administrative
            if success:
                self.add_admin_activity(
                    "Utilisateur mis à jour",
                    f"Email: {user_data.get('email')}, Rôle: {user_data.get('role', 'user')}"
                )
                return True, "Utilisateur mis à jour avec succès"
            else:
                return False, "Erreur lors de la mise à jour de l'utilisateur"
        
        elif action == "delete":
            # Vérifier les données requises
            if not user_data or 'id' not in user_data:
                return False, "ID utilisateur requis"
            
            # Supprimer l'utilisateur du modèle
            if hasattr(self.app_model, 'delete_user'):
                success = self.app_model.delete_user(user_data.get('id'))
            elif hasattr(self.app_model, 'users'):
                # Rechercher et supprimer l'utilisateur
                for i, user in enumerate(self.app_model.users):
                    if user.get('id') == user_data.get('id'):
                        del self.app_model.users[i]
                        success = True
                        break
                else:
                    return False, "Utilisateur non trouvé"
            else:
                return False, "Modèle d'utilisateur non disponible"
            
            # Ajouter une activité administrative
            if success:
                self.add_admin_activity(
                    "Utilisateur supprimé",
                    f"Email: {user_data.get('email')}"
                )
                return True, "Utilisateur supprimé avec succès"
            else:
                return False, "Erreur lors de la suppression de l'utilisateur"
    
    def generate_user_id(self):
        """
        Génère un ID unique pour un utilisateur
        
        Returns:
            str: ID unique
        """
        # Récupérer les utilisateurs existants
        users = []
        if hasattr(self.app_model, 'users'):
            users = self.app_model.users
        
        # Chercher le plus grand ID
        max_id = 0
        for user in users:
            if 'id' in user and user['id'].startswith('usr_'):
                try:
                    id_num = int(user['id'][4:])
                    max_id = max(max_id, id_num)
                except ValueError:
                    pass
        
        # Générer un nouvel ID
        return f"usr_{max_id + 1:03d}"
    
    def update_settings(self, settings):
        """
        Met à jour les paramètres de l'application
        
        Args:
            settings: Dictionnaire des paramètres à mettre à jour
            
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        # Vérifier les permissions
        try:
            self.permissions.check_permission('admin.settings.edit')
        except PermissionDenied:
            return False
        
        try:
            # Vérifier si le modèle possède une méthode de mise à jour des paramètres
            if hasattr(self.app_model, 'update_config'):
                for key, value in settings.items():
                    self.app_model.update_config(key, value)
            elif hasattr(self.app_model, 'config'):
                # Mettre à jour directement les attributs de configuration
                for key, value in settings.items():
                    if hasattr(self.app_model.config, 'update'):
                        self.app_model.config.update(key, value)
                    else:
                        # Mettre à jour avec notation par points (a.b.c)
                        parts = key.split('.')
                        config = self.app_model.config
                        for part in parts[:-1]:
                            if not hasattr(config, part):
                                setattr(config, part, {})
                            config = getattr(config, part)
                        setattr(config, parts[-1], value)
            else:
                # Stocker dans un fichier JSON
                config_file = os.path.join(
                    os.path.expanduser("~"), ".vynal_docs_automator", "config.json"
                )
                
                # Créer le répertoire si nécessaire
                os.makedirs(os.path.dirname(config_file), exist_ok=True)
                
                # Charger la configuration existante
                config = {}
                if os.path.exists(config_file):
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                
                # Mettre à jour les paramètres
                for key, value in settings.items():
                    # Mettre à jour avec notation par points (a.b.c)
                    parts = key.split('.')
                    current = config
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = value
                
                # Sauvegarder la configuration
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
            
            # Ajouter une activité administrative
            self.add_admin_activity(
                "Paramètres mis à jour",
                f"{len(settings)} paramètres modifiés"
            )
            
            logger.info(f"Paramètres mis à jour ({len(settings)} paramètres)")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des paramètres: {e}")
            return False
    
    def reset_settings(self):
        """
        Réinitialise les paramètres de l'application aux valeurs par défaut
        
        Returns:
            bool: True si la réinitialisation a réussi, False sinon
        """
        try:
            # Valeurs par défaut
            defaults = {
                "app.name": "Vynal Docs Automator",
                "app.company_name": "Vynal Agency LTD",
                "app.language": "fr",
                "app.theme": "dark",
                "app.font": "Roboto",
                "app.font_size": "12",
                "app.border_radius": "10",
                "storage.data_dir": os.path.join(os.path.expanduser("~"), ".vynal_docs_automator", "data"),
                "storage.logs_dir": os.path.join(os.path.expanduser("~"), ".vynal_docs_automator", "logs"),
                "storage.backup_dir": os.path.join(os.path.expanduser("~"), ".vynal_docs_automator", "backups"),
                "storage.backup_format": "zip",
                "storage.auto_backup_interval": "7",
                "storage.backup_count": "5",
                "notifications.enabled": "true",
                "notifications.email_enabled": "false",
                "notifications.error_notifications": "true",
                "notifications.update_notifications": "true",
                "security.require_login": "true",
                "security.session_timeout": "30",
                "security.require_strong_password": "true",
                "security.max_login_attempts": "5",
                "security.lockout_duration": "15",
                "admin.debug_mode": "false",
                "admin.log_level": "INFO",
                "admin.log_retention": "30",
                "admin.max_log_size": "10",
                "admin.remote_access": "false"
            }
            
            # Mettre à jour les paramètres avec les valeurs par défaut
            if self.update_settings(defaults):
                # Ajouter une activité administrative
                self.add_admin_activity(
                    "Paramètres réinitialisés",
                    "Tous les paramètres ont été réinitialisés aux valeurs par défaut"
                )
                logger.info("Paramètres réinitialisés aux valeurs par défaut")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation des paramètres: {e}")
            return False
    
    def apply_theme(self, theme_name):
        """
        Applique un thème à l'interface utilisateur
        
        Args:
            theme_name: Nom du thème ('light', 'dark')
            
        Returns:
            bool: True si le thème a été appliqué, False sinon
        """
        try:
            # Définir le mode d'apparence global
            ctk.set_appearance_mode(theme_name)
            
            # Mettre à jour la configuration
            self.update_settings({"app.theme": theme_name})
            
            # Ajouter une activité administrative
            self.add_admin_activity(
                "Thème modifié",
                f"Thème défini sur '{theme_name}'"
            )
            
            logger.info(f"Thème appliqué: {theme_name}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'application du thème: {e}")
            return False