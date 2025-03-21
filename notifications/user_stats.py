#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de gestion des statistiques par utilisateur pour Vynal Docs Automator
Stocke et gère les statistiques de gain de temps pour chaque utilisateur
"""

import json
import os
from datetime import datetime
from .time_saving import TimeSavingCalculator

class UserStats:
    """Gestionnaire des statistiques par utilisateur"""
    
    def __init__(self, stats_file="user_stats.json"):
        """
        Initialise le gestionnaire de statistiques
        
        Args:
            stats_file (str): Chemin du fichier de statistiques
        """
        self.stats_file = stats_file
        self.calculator = TimeSavingCalculator()
        self.stats = self._load_stats()
    
    def _load_stats(self):
        """Charge les statistiques depuis le fichier"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _save_stats(self):
        """Sauvegarde les statistiques dans le fichier"""
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=4)
    
    def get_user_stats(self, user_id):
        """
        Récupère les statistiques d'un utilisateur
        
        Args:
            user_id (str): Identifiant de l'utilisateur
            
        Returns:
            dict: Statistiques de l'utilisateur
        """
        if user_id not in self.stats:
            self.stats[user_id] = {
                "total_documents": 0,
                "last_notification": None,
                "documents_since_notification": 0,
                "total_time_saved": 0,  # en minutes
                "created_at": datetime.now().isoformat(),
                "sessions": []  # historique des sessions
            }
        return self.stats[user_id]
    
    def update_user_stats(self, user_id, documents_created=1):
        """
        Met à jour les statistiques d'un utilisateur
        
        Args:
            user_id (str): Identifiant de l'utilisateur
            documents_created (int): Nombre de documents créés
        """
        stats = self.get_user_stats(user_id)
        
        # Mettre à jour le nombre total de documents
        stats["total_documents"] += documents_created
        stats["documents_since_notification"] += documents_created
        
        # Calculer le temps économisé pour cette session
        hours, minutes = self.calculator.calculate_time_saved(documents_created)
        time_saved_minutes = hours * 60 + minutes
        
        # Ajouter la session à l'historique
        stats["sessions"].append({
            "date": datetime.now().isoformat(),
            "documents": documents_created,
            "time_saved": time_saved_minutes
        })
        
        # Mettre à jour le temps total économisé
        stats["total_time_saved"] += time_saved_minutes
        
        # Mettre à jour la date de dernière notification
        stats["last_notification"] = datetime.now().isoformat()
        
        self._save_stats()
    
    def reset_notification_counter(self, user_id):
        """
        Réinitialise le compteur de notifications d'un utilisateur
        
        Args:
            user_id (str): Identifiant de l'utilisateur
        """
        if user_id in self.stats:
            self.stats[user_id]["documents_since_notification"] = 0
            self._save_stats()
    
    def should_show_notification(self, user_id):
        """
        Vérifie si une notification doit être affichée
        
        Args:
            user_id (str): Identifiant de l'utilisateur
            
        Returns:
            bool: True si une notification doit être affichée
        """
        stats = self.get_user_stats(user_id)
        return stats["documents_since_notification"] >= 5
    
    def get_user_summary(self, user_id):
        """
        Récupère un résumé des statistiques d'un utilisateur
        
        Args:
            user_id (str): Identifiant de l'utilisateur
            
        Returns:
            dict: Résumé des statistiques
        """
        stats = self.get_user_stats(user_id)
        total_minutes = stats["total_time_saved"]
        total_hours = total_minutes // 60
        remaining_minutes = total_minutes % 60
        
        # Calculer la moyenne par document
        if stats["total_documents"] > 0:
            avg_minutes = total_minutes / stats["total_documents"]
            avg_hours = int(avg_minutes // 60)
            avg_minutes = int(avg_minutes % 60)
        else:
            avg_hours = avg_minutes = 0
        
        return {
            "total_documents": stats["total_documents"],
            "total_time_saved": self.calculator.format_time(total_hours, remaining_minutes),
            "average_time_per_doc": self.calculator.format_time(avg_hours, avg_minutes),
            "sessions": stats["sessions"]
        } 