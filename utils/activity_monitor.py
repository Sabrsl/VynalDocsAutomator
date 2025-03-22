#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Moniteur d'activité pour le verrouillage automatique de l'application
après une période d'inactivité.
"""

import time
import logging
import threading
from datetime import datetime, timedelta

logger = logging.getLogger("VynalDocsAutomator.ActivityMonitor")

class ActivityMonitor:
    """
    Moniteur d'activité qui détecte l'inactivité de l'utilisateur
    et déclenche un verrouillage automatique après une période définie.
    """
    
    def __init__(self, lock_callback, config_manager, check_interval=5):
        """
        Initialise le moniteur d'activité.
        
        Args:
            lock_callback: Fonction à appeler pour verrouiller l'application
            config_manager: Gestionnaire de configuration pour accéder aux paramètres
            check_interval: Intervalle en secondes pour vérifier l'inactivité
        """
        self.lock_callback = lock_callback
        self.config_manager = config_manager
        self.check_interval = check_interval
        
        # Dernière activité détectée (timestamp)
        self.last_activity = datetime.now()
        
        # État du moniteur
        self.running = False
        self.thread = None
        
        # Flag pour indiquer si l'application est déjà verrouillée
        self.is_locked = False
        
        logger.info("Moniteur d'activité initialisé")
    
    def start(self):
        """Démarre le moniteur d'activité"""
        if self.running:
            return
        
        # Vérifier que les conditions pour le verrouillage automatique sont remplies
        if not self._should_monitor():
            logger.info("Verrouillage automatique désactivé ou mot de passe non configuré")
            return
        
        self.running = True
        self.last_activity = datetime.now()
        self.is_locked = False
        
        # Démarrer le thread de surveillance
        self.thread = threading.Thread(target=self._monitor_activity, daemon=True)
        self.thread.start()
        
        logger.info("Moniteur d'activité démarré")
    
    def stop(self):
        """Arrête le moniteur d'activité"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
            self.thread = None
        
        logger.info("Moniteur d'activité arrêté")
    
    def reset(self):
        """Réinitialise le timer d'activité"""
        self.last_activity = datetime.now()
        
        # Si l'application était verrouillée, changer l'état
        if self.is_locked:
            self.is_locked = False
            logger.debug("Moniteur d'activité réinitialisé après déverrouillage")
    
    def _should_monitor(self):
        """
        Vérifie si le moniteur doit être actif en fonction des paramètres.
        
        Returns:
            bool: True si le moniteur doit être actif, False sinon
        """
        try:
            # Vérifier si le verrouillage automatique est activé
            auto_lock = self.config_manager.get("security.auto_lock", False)
            
            # Vérifier si un mot de passe est configuré
            require_password = self.config_manager.get("security.require_password", False)
            
            return auto_lock and require_password
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des paramètres de verrouillage: {e}")
            return False
    
    def _monitor_activity(self):
        """Thread de surveillance de l'activité"""
        try:
            while self.running:
                # Vérifier si les conditions ont changé
                if not self._should_monitor():
                    logger.info("Conditions de verrouillage automatique non remplies, arrêt du moniteur")
                    self.running = False
                    break
                
                # Vérifier si l'application est déjà verrouillée
                if self.is_locked:
                    time.sleep(self.check_interval)
                    continue
                
                # Obtenir le délai de verrouillage en minutes
                lock_time_minutes = self.config_manager.get("security.lock_time", 10)
                
                # Calculer l'intervalle d'inactivité
                now = datetime.now()
                inactivity_duration = now - self.last_activity
                
                # Convertir en timedelta pour comparaison
                lock_threshold = timedelta(minutes=lock_time_minutes)
                
                # Si l'inactivité dépasse le seuil, verrouiller l'application
                if inactivity_duration >= lock_threshold:
                    logger.info(f"Inactivité détectée ({inactivity_duration.total_seconds()/60:.1f} minutes), verrouillage automatique")
                    
                    # Marquer comme verrouillé
                    self.is_locked = True
                    
                    # Appeler le callback de verrouillage
                    self.lock_callback()
                
                # Attendre avant la prochaine vérification
                time.sleep(self.check_interval)
                
        except Exception as e:
            logger.error(f"Erreur dans le thread de surveillance d'activité: {e}")
            self.running = False
    
    def register_activity(self, event=None):
        """
        Enregistre une activité utilisateur.
        
        Args:
            event: Événement Tkinter (optionnel)
        """
        if not self.running:
            return
        
        # Ne pas réinitialiser si l'application est verrouillée
        if self.is_locked:
            return
        
        # Mettre à jour le timestamp de dernière activité
        self.last_activity = datetime.now() 