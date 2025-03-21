#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitaires de sécurité pour la gestion des tentatives de connexion
"""

import os
import json
import time
import socket
import logging
import platform
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

logger = logging.getLogger("VynalDocsAutomator.SecurityUtils")

class LoginAttemptManager:
    """Gestionnaire des tentatives de connexion"""
    
    def __init__(self, max_attempts: int = 3):
        """
        Initialise le gestionnaire de tentatives
        
        Args:
            max_attempts: Nombre maximum de tentatives avant blocage
        """
        self.max_attempts = max_attempts
        self.attempts_file = os.path.join("data", "login_attempts.json")
        self.lockout_delays = [60, 300, 900]  # 1min, 5min, 15min
        self._load_attempts()
    
    def _load_attempts(self):
        """Charge l'historique des tentatives"""
        try:
            if os.path.exists(self.attempts_file):
                with open(self.attempts_file, 'r') as f:
                    self.attempts = json.load(f)
            else:
                self.attempts = {}
        except Exception as e:
            logger.error(f"Erreur lors du chargement des tentatives: {e}")
            self.attempts = {}
    
    def _save_attempts(self):
        """Sauvegarde l'historique des tentatives"""
        try:
            os.makedirs(os.path.dirname(self.attempts_file), exist_ok=True)
            with open(self.attempts_file, 'w') as f:
                json.dump(self.attempts, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des tentatives: {e}")
    
    def _get_device_info(self) -> Dict[str, str]:
        """
        Récupère les informations détaillées sur l'appareil et l'environnement
        
        Returns:
            dict: Informations sur l'appareil et l'environnement
        """
        info = {}
        try:
            # Informations réseau
            hostname = socket.gethostname()
            info["hostname"] = hostname
            info["ip_local"] = socket.gethostbyname(hostname)
            
            # Essayer de récupérer l'IP publique
            try:
                import urllib.request
                external_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
                info["ip_public"] = external_ip
            except:
                info["ip_public"] = "unknown"
            
            # Informations système
            info["os_name"] = os.name
            info["platform"] = platform.platform()
            info["system"] = platform.system()
            info["release"] = platform.release()
            info["version"] = platform.version()
            info["machine"] = platform.machine()
            info["processor"] = platform.processor()
            info["architecture"] = platform.architecture()[0]
            
            # Informations Python
            info["python_version"] = platform.python_version()
            info["python_implementation"] = platform.python_implementation()
            
            # Variables d'environnement (sélectionnées)
            env_vars = ["USERNAME", "COMPUTERNAME", "USERDOMAIN", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE"]
            info["environment"] = {var: os.environ.get(var, "unknown") for var in env_vars}
            
            # Informations sur l'écran
            try:
                import tkinter as tk
                root = tk.Tk()
                info["screen_width"] = root.winfo_screenwidth()
                info["screen_height"] = root.winfo_screenheight()
                root.destroy()
            except:
                info["screen_width"] = "unknown"
                info["screen_height"] = "unknown"
            
            # Informations sur le disque
            try:
                import psutil
                disk = psutil.disk_usage('/')
                info["disk"] = {
                    "total": f"{disk.total / (1024**3):.2f} GB",
                    "used": f"{disk.used / (1024**3):.2f} GB",
                    "free": f"{disk.free / (1024**3):.2f} GB",
                    "percent": f"{disk.percent}%"
                }
                
                # Informations sur la mémoire
                memory = psutil.virtual_memory()
                info["memory"] = {
                    "total": f"{memory.total / (1024**3):.2f} GB",
                    "available": f"{memory.available / (1024**3):.2f} GB",
                    "percent": f"{memory.percent}%"
                }
                
                # Informations sur le CPU
                info["cpu"] = {
                    "cores_physical": psutil.cpu_count(logical=False),
                    "cores_logical": psutil.cpu_count(logical=True),
                    "frequency": f"{psutil.cpu_freq().current:.2f} MHz",
                    "usage_percent": f"{psutil.cpu_percent()}%"
                }
                
                # Informations sur les processus
                info["processes"] = {
                    "total": len(psutil.pids()),
                    "running": len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'running'])
                }
            except:
                pass
            
            # Informations sur la langue et la localisation
            import locale
            info["locale"] = {
                "default": locale.getdefaultlocale()[0],
                "preferred": locale.getpreferredencoding()
            }
            
            # Informations sur le fuseau horaire
            from datetime import datetime
            import time
            info["timezone"] = {
                "name": time.tzname[0],
                "offset": datetime.now().astimezone().strftime('%z'),
                "dst": time.daylight
            }
            
            # Informations sur la date et l'heure
            now = datetime.now()
            info["timestamp"] = {
                "datetime": now.isoformat(),
                "timestamp": int(now.timestamp()),
                "timezone": str(now.astimezone().tzinfo)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos appareil: {e}")
            info["error"] = str(e)
        
        return info
    
    def _get_device_id(self) -> str:
        """
        Génère un identifiant unique pour l'appareil
        
        Returns:
            str: Identifiant de l'appareil
        """
        info = self._get_device_info()
        return f"{info.get('hostname', 'unknown')}_{info.get('ip', 'unknown')}"
    
    def record_attempt(self, success: bool):
        """
        Enregistre une tentative de connexion
        
        Args:
            success: True si la tentative est réussie, False sinon
        """
        device_id = self._get_device_id()
        now = datetime.now().isoformat()
        
        if device_id not in self.attempts:
            self.attempts[device_id] = {
                "count": 0,
                "lockout_level": 0,
                "last_attempt": None,
                "lockout_until": None,
                "device_info": self._get_device_info(),
                "history": []
            }
        
        device = self.attempts[device_id]
        
        # Enregistrer la tentative
        device["history"].append({
            "timestamp": now,
            "success": success,
            "device_info": self._get_device_info()
        })
        
        # Limiter l'historique à 100 entrées
        if len(device["history"]) > 100:
            device["history"] = device["history"][-100:]
        
        if success:
            # Réinitialiser le compteur en cas de succès
            device["count"] = 0
            device["lockout_level"] = 0
            device["lockout_until"] = None
        else:
            # Incrémenter le compteur d'échecs
            device["count"] += 1
            
            # Appliquer le blocage si nécessaire
            if device["count"] >= self.max_attempts:
                device["lockout_level"] = min(device["lockout_level"] + 1, len(self.lockout_delays) - 1)
                delay = self.lockout_delays[device["lockout_level"]]
                device["lockout_until"] = (datetime.now() + timedelta(seconds=delay)).isoformat()
        
        device["last_attempt"] = now
        self._save_attempts()
        
        if not success:
            logger.warning(
                f"Tentative de connexion échouée depuis {device_id}. "
                f"Tentative {device['count']}/{self.max_attempts}"
            )
    
    def can_attempt(self) -> Tuple[bool, Optional[timedelta]]:
        """
        Vérifie si une nouvelle tentative est autorisée
        
        Returns:
            tuple: (peut_essayer, temps_restant)
        """
        device_id = self._get_device_id()
        if device_id not in self.attempts:
            return True, None
        
        device = self.attempts[device_id]
        if not device.get("lockout_until"):
            return True, None
        
        lockout_until = datetime.fromisoformat(device["lockout_until"])
        now = datetime.now()
        
        if now < lockout_until:
            return False, lockout_until - now
        
        # Réinitialiser après la période de blocage
        if now >= lockout_until:
            device["count"] = 0
            device["lockout_until"] = None
            self._save_attempts()
            return True, None
        
        return True, None
    
    def get_remaining_attempts(self) -> int:
        """
        Retourne le nombre de tentatives restantes
        
        Returns:
            int: Nombre de tentatives restantes
        """
        device_id = self._get_device_id()
        if device_id not in self.attempts:
            return self.max_attempts
        
        return max(0, self.max_attempts - self.attempts[device_id]["count"])
    
    def reset_attempts(self):
        """Réinitialise les tentatives pour l'appareil actuel"""
        device_id = self._get_device_id()
        if device_id in self.attempts:
            self.attempts[device_id]["count"] = 0
            self.attempts[device_id]["lockout_level"] = 0
            self.attempts[device_id]["lockout_until"] = None
            self._save_attempts() 