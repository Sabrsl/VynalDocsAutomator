#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vynal Docs Automator - Lanceur avec écran de démarrage
Lance l'application avec un écran de démarrage
"""

import os
import sys
import time
import socket
import threading
import subprocess
import json
import argparse
import customtkinter as ctk
import logging
import tkinter as tk
import hashlib
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw

# Import de la configuration globale
from config import (
    APP_NAME, WINDOW_SIZE, MIN_WINDOW_SIZE,
    setup_logging, ensure_directories
)

# Import de ConfigManager pour charger la configuration
from utils.config_manager import ConfigManager

# Port pour la communication entre les processus
SYNC_PORT = 12345

# Vérification anti-récursion
RECURSION_FLAG_FILE = ".splash_running"

def check_recursion():
    """
    Vérifie si une instance de l'écran de démarrage est déjà en cours d'exécution
    pour éviter les appels en boucle.
    
    Returns:
        bool: True si une instance est déjà en cours d'exécution, False sinon
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        flag_file = os.path.join(current_dir, RECURSION_FLAG_FILE)
        
        if os.path.exists(flag_file):
            # Vérifier si le fichier est récent (moins de 10 secondes)
            try:
                file_age = time.time() - os.path.getmtime(flag_file)
                if file_age < 10:
                    print("Une instance de l'écran de démarrage est déjà en cours d'exécution.")
                    return True
                else:
                    # Le fichier est trop ancien, le supprimer
                    try:
                        os.remove(flag_file)
                    except Exception as e:
                        print(f"Erreur lors de la suppression du fichier drapeau ancien: {e}")
            except Exception as e:
                print(f"Erreur lors de la vérification de l'âge du fichier drapeau: {e}")
                # En cas d'erreur, supprimer le fichier par précaution
                try:
                    os.remove(flag_file)
                except:
                    pass
        
        # Créer le fichier drapeau
        try:
            with open(flag_file, 'w') as f:
                f.write(str(int(time.time())))
        except Exception as e:
            print(f"Erreur lors de la création du fichier drapeau: {e}")
            
        return False
    except Exception as e:
        print(f"Erreur lors de la vérification de récursion: {e}")
        return False  # En cas d'erreur, permettre l'exécution

def cleanup_recursion_flag():
    """Supprime le fichier drapeau anti-récursion"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        flag_file = os.path.join(current_dir, RECURSION_FLAG_FILE)
        if os.path.exists(flag_file):
            os.remove(flag_file)
    except Exception as e:
        print(f"Erreur lors de la suppression du fichier drapeau: {e}")

# Nouvelle fonction pour vérifier le mot de passe avant le lancement
def check_password():
    """
    Vérifie le mot de passe avant de lancer l'application.
    Si le mot de passe est correct, lance l'application.
    Sinon, ferme le programme.
    
    Returns:
        bool: True si le mot de passe est correct, False sinon
    """
    # Charger la configuration pour vérifier si un mot de passe est requis
    try:
        config = ConfigManager()
        require_password = config.get("security.require_password", False)
        password_hash = config.get("security.password_hash", "")
        
        if not require_password or not password_hash:
            # Aucun mot de passe requis
            return True
        
        # Importer la classe LoginView
        from views.login_view import LoginView
        
        # Créer une fenêtre temporaire pour héberger la vue de connexion
        temp_root = tk.Tk()
        temp_root.withdraw()  # Cacher la fenêtre temporaire
        
        # Variables pour stocker le résultat de l'authentification
        auth_result = [False]
        
        # Fonction de callback pour l'authentification réussie
        def on_auth_success():
            auth_result[0] = True
            temp_root.quit()
        
        # Créer la vue de connexion
        login_view = LoginView(temp_root, on_auth_success)
        
        # Afficher la vue de connexion
        login_view.show(password_hash)
        
        # Attendre que l'authentification soit terminée
        temp_root.mainloop()
        
        # Détruire la fenêtre temporaire
        try:
            temp_root.destroy()
        except:
            pass
        
        # Retourner le résultat de l'authentification
        return auth_result[0]
    
    except Exception as e:
        print(f"Erreur lors de la vérification du mot de passe: {e}")
        # En cas d'erreur, autoriser l'accès pour éviter de bloquer l'application
        messagebox.showerror("Erreur", f"Une erreur est survenue lors de la vérification du mot de passe: {e}")
        return False

class SplashScreen:
    def __init__(self, root, app_name="Vynal Docs Automator", width=550, height=300, demo_mode=False):
        self.root = root
        self.app_name = app_name
        
        # Configurer la fenêtre avec un fond transparent pour les coins arrondis
        self.root.overrideredirect(True)
        self.root.geometry(f"{width}x{height}")
        self.root.configure(bg="#161616")  # Couleur qui sera transparente
        self.root.attributes("-transparentcolor", "#161616")
        
        # Centrer la fenêtre
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Garder la fenêtre au premier plan
        self.root.attributes('-topmost', True)
        
        # Couleurs
        self.bg_color = "#16161A"  # Fond sombre élégant différent de la couleur transparente
        self.accent_color = "#3498db"  # Bleu moderne
        self.text_color = "#FFFFFF"
        self.secondary_color = "#94A1B2"
        
        # Variables pour l'animation de fermeture
        self.fade_steps = 10  # Réduction du nombre d'étapes pour une transition plus rapide
        self.fade_delay = 1   # Délai minimal entre chaque étape
        self.current_opacity = 1.0
        
        # Créer le cadre principal avec coins arrondis
        self.create_rounded_background(width, height, 15)
        
        # Créer les widgets
        self.create_widgets()
        
        # Initialiser la barre de progression
        self.progress = 0
        
        # Démarrer l'animation
        self.update_progress()
        
        # Mode démo
        self.demo_mode = demo_mode
    
    def create_rounded_background(self, width, height, radius=15):
        """Crée un fond avec des coins arrondis"""
        # Créer une image avec des coins arrondis
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Dessiner un rectangle avec coins arrondis
        draw.rounded_rectangle([(0, 0), (width, height)], radius, fill=(22, 22, 26, 255))  # Couleur du fond
        
        # Convertir l'image pour Tkinter
        self.bg_image = ImageTk.PhotoImage(image)
        
        # Afficher l'image comme fond
        self.bg_label = tk.Label(self.root, image=self.bg_image, borderwidth=0, highlightthickness=0, bg="#161616")
        self.bg_label.place(x=0, y=0)
    
    def create_widgets(self):
        # Créer un cadre pour le contenu qui sera placé sur le fond arrondi
        content_frame = tk.Frame(self.root, bg=self.bg_color)
        content_frame.place(x=40, y=30, width=470, height=240)
        
        # En-tête
        header_frame = tk.Frame(content_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X)
        
        # Nom de l'app
        title_label = tk.Label(
            header_frame, 
            text=self.app_name, 
            font=("Arial", 22, "bold"),
            fg=self.text_color,
            bg=self.bg_color
        )
        title_label.pack(anchor=tk.W, pady=(0, 3))
        
        # Sous-titre
        subtitle_label = tk.Label(
            header_frame, 
            text="Gestion de documents", 
            font=("Arial", 10),
            fg=self.secondary_color,
            bg=self.bg_color
        )
        subtitle_label.pack(anchor=tk.W)
        
        # Ligne séparatrice
        separator = tk.Frame(content_frame, height=1, bg="#242629")
        separator.pack(fill=tk.X, pady=(25, 25))
        
        # Message de chargement
        self.loading_label = tk.Label(
            content_frame, 
            text="Initialisation", 
            font=("Arial", 11),
            fg=self.secondary_color,
            bg=self.bg_color,
            anchor=tk.W
        )
        self.loading_label.pack(fill=tk.X, pady=(0, 15))
        
        # Barre de progression
        progress_frame = tk.Frame(content_frame, bg=self.bg_color)
        progress_frame.pack(fill=tk.X)
        
        # Style moderne pour la barre de progression
        style = ttk.Style()
        style.theme_use('default')
        style.configure(
            "Modern.Horizontal.TProgressbar",
            thickness=3,
            troughcolor="#242629",
            background=self.accent_color
        )
        
        # Barre de progression
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            orient="horizontal",
            style="Modern.Horizontal.TProgressbar",
            length=470,
            mode="determinate"
        )
        self.progress_bar.pack(fill=tk.X)
        
        # Pied de page
        footer_frame = tk.Frame(content_frame, bg=self.bg_color)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 0))
        
        # Version discrète
        version_label = tk.Label(
            footer_frame,
            text="v1.0",
            font=("Arial", 8),
            fg="#72757E",
            bg=self.bg_color
        )
        version_label.pack(side=tk.RIGHT)
    
    def update_progress(self):
        if self.progress < 95:  # Laisser 5% pour l'attente de l'application principale
            # Augmenter plus rapidement la progression
            increment = 4 if self.progress < 50 else 3
            self.progress += increment
            self.progress_bar["value"] = self.progress
            
            # Mettre à jour le message de chargement
            if self.progress < 30:
                self.loading_label.config(text="Initialisation des composants...")
            elif self.progress < 60:
                self.loading_label.config(text="Chargement des données...")
            elif self.progress < 90:
                self.loading_label.config(text="Préparation de l'interface...")
            else:
                self.loading_label.config(text="Finalisation...")
            
            # Planifier la prochaine mise à jour plus rapidement
            self.root.after(10, self.update_progress)
    
    def wait_for_app(self):
        """Attend que l'application principale soit prête"""
        self.loading_label.config(text="Attente du tableau de bord...")
        self.progress = 95
        self.progress_bar["value"] = 95
    
    def complete(self):
        """Complète la barre de progression et ferme l'écran de démarrage avec transition"""
        # Mettre à jour la barre de progression à 100%
        self.progress = 100
        self.progress_bar["value"] = 100
        self.loading_label.config(text="Chargement terminé!")
        self.root.update()
        
        # Commencer immédiatement la transition rapide
        self.start_fade_out()
    
    def start_fade_out(self):
        """Commence l'animation de fondu avant fermeture"""
        # Créer un effet de fondu en sortie
        self.fade_out_effect()
    
    def fade_out_effect(self):
        """Crée une animation de fondu avant fermeture"""
        if self.current_opacity > 0:
            # Réduire l'opacité plus rapidement
            self.current_opacity -= 1.0 / self.fade_steps
            if self.current_opacity < 0:
                self.current_opacity = 0
                
            # Appliquer l'opacité (fonctionne sous Windows)
            try:
                self.root.attributes("-alpha", self.current_opacity)
            except:
                # Solution de secours pour les systèmes sans support d'opacité
                # Réduire la taille plus rapidement
                current_geometry = self.root.geometry()
                width, height = map(int, current_geometry.split('+')[0].split('x'))
                new_width = int(width * 0.98)  # Réduction plus rapide
                new_height = int(height * 0.98)
                center_x = self.root.winfo_x() + (width - new_width) // 2
                center_y = self.root.winfo_y() + (height - new_height) // 2
                self.root.geometry(f"{new_width}x{new_height}+{center_x}+{center_y}")
            
            # Continuer l'animation avec délai minimal
            self.root.after(self.fade_delay, self.fade_out_effect)
        else:
            # Animation terminée, fermer la fenêtre
            self._destroy_window()
    
    def _destroy_window(self):
        """Détruit la fenêtre de l'écran de démarrage"""
        try:
            # Désactiver l'attribut topmost avant de fermer
            self.root.attributes('-topmost', False)
            # Fermer la fenêtre
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"Erreur lors de la fermeture de l'écran de démarrage: {e}")

def create_sync_server():
    """Crée un serveur pour synchroniser l'écran de démarrage et l'application principale"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind(('127.0.0.1', SYNC_PORT))
        server.listen(1)
        server.settimeout(30)  # Timeout de 30 secondes
        return server
    except Exception as e:
        print(f"Erreur lors de la création du serveur de synchronisation: {e}")
        return None

def cleanup_sync_file():
    """Supprime le fichier de synchronisation"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sync_file = os.path.join(current_dir, ".sync_splash")
        if os.path.exists(sync_file):
            os.remove(sync_file)
    except Exception as e:
        print(f"Erreur lors de la suppression du fichier de synchronisation: {e}")

def launch_app_with_sync():
    """Lance l'application principale avec synchronisation"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Supprimer le fichier de synchronisation s'il existe déjà
    sync_file = os.path.join(current_dir, ".sync_splash")
    if os.path.exists(sync_file):
        try:
            os.remove(sync_file)
        except Exception as e:
            print(f"Erreur lors de la suppression du fichier de synchronisation existant: {e}")
    
    # Créer un fichier temporaire pour indiquer que l'application doit se synchroniser
    try:
        with open(sync_file, 'w') as f:
            f.write(str(SYNC_PORT))
    except Exception as e:
        print(f"Erreur lors de la création du fichier de synchronisation: {e}")
        return
    
    # Lancer l'application principale avec le flag anti-récursion
    try:
        subprocess.Popen([sys.executable, os.path.join(current_dir, "main.py"), "--no-splash-recursion"])
    except Exception as e:
        print(f"Erreur lors du lancement de l'application principale: {e}")
        # Supprimer le fichier de synchronisation en cas d'erreur
        cleanup_sync_file()
        return
    
    # Supprimer le fichier de synchronisation après un délai
    def cleanup_sync_file_delayed():
        time.sleep(10)  # Attendre 10 secondes
        cleanup_sync_file()
    
    threading.Thread(target=cleanup_sync_file_delayed, daemon=True).start()

def launch_main_app():
    # Créer un serveur pour la synchronisation
    server = create_sync_server()
    if not server:
        print("Impossible de créer le serveur de synchronisation, lancement sans synchronisation")
        return
    
    # Fonction pour attendre la connexion de l'application principale
    def wait_for_main_app():
        try:
            # Indiquer que nous attendons l'application principale
            splash.wait_for_app()
            
            # Lancer l'application principale
            launch_app_with_sync()
            
            # Accepter la connexion
            server.settimeout(30)  # Timeout de 30 secondes
            
            try:
                client, _ = server.accept()
                
                # Recevoir le message
                client.settimeout(5)  # Timeout de 5 secondes pour la réception
                data = client.recv(1024)
                
                try:
                    message = json.loads(data.decode('utf-8'))
                    
                    # Si l'application principale est prête, fermer immédiatement l'écran de démarrage
                    if message.get('status') == 'ready':
                        # Envoyer une confirmation
                        client.send(json.dumps({'status': 'closing'}).encode('utf-8'))
                        
                        # Fermer immédiatement le splash screen
                        splash_root.after(0, lambda: splash.complete())
                except json.JSONDecodeError:
                    print("Erreur de décodage JSON du message reçu")
                    splash_root.after(0, lambda: splash.complete())
                finally:
                    # Fermer la connexion
                    client.close()
            except socket.timeout:
                # En cas de timeout, fermer l'écran de démarrage
                print("Timeout en attendant l'application principale")
                splash_root.after(0, lambda: splash.complete())
            except ConnectionError:
                print("Erreur de connexion avec l'application principale")
                splash_root.after(0, lambda: splash.complete())
        except Exception as e:
            print(f"Erreur lors de la synchronisation: {e}")
            # En cas d'erreur, fermer l'écran de démarrage
            splash_root.after(0, lambda: splash.complete())
        finally:
            # Fermer le serveur
            try:
                server.close()
            except:
                pass
    
    # Démarrer le thread pour attendre l'application principale
    threading.Thread(target=wait_for_main_app, daemon=True).start()

def create_main_window():
    """Crée la fenêtre principale de l'application"""
    # Configurer le thème global
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    # Créer la fenêtre principale
    root = ctk.CTk()
    root.title(APP_NAME)
    root.geometry(WINDOW_SIZE)
    root.minsize(*MIN_WINDOW_SIZE)
    
    # Optimiser les performances
    try:
        from utils.performance_optimizer import PerformanceOptimizer
        logger.info("Application des optimisations de performance")
        PerformanceOptimizer.optimize_application(root)
    except Exception as e:
        logger.warning(f"Impossible d'appliquer les optimisations de performance: {e}")
    
    return root

if __name__ == "__main__":
    # Vérifier si une instance est déjà en cours d'exécution
    if check_recursion():
        # Si c'est le cas, lancer directement l'application principale sans splash
        current_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.Popen([sys.executable, os.path.join(current_dir, "main.py"), "--no-splash"])
        sys.exit(0)
    
    try:
        # Analyser les arguments de ligne de commande
        parser = argparse.ArgumentParser(description="Lance Vynal Docs Automator avec un écran de démarrage")
        parser.add_argument("--demo", action="store_true", help="Mode démo pour voir les animations")
        parser.add_argument("--skip-auth", action="store_true", help="Ignorer l'authentification (pour le développement)")
        args = parser.parse_args()
        
        # Vérifier le mot de passe avant de lancer l'application
        if not args.skip_auth and not args.demo:
            if not check_password():
                print("Authentification échouée. L'application ne sera pas démarrée.")
                sys.exit(1)
        
        # Afficher des informations de débogage
        print("Démarrage de l'écran de démarrage...")
        print(f"Version de PIL: {Image.__version__}")
        print(f"Version de Tkinter: {tk.TkVersion}")
        
        # Créer et afficher l'écran de démarrage
        splash_root = tk.Tk()
        splash = SplashScreen(splash_root, demo_mode=args.demo)
        
        # Lancer l'application principale avec synchronisation (sauf en mode démo)
        if not args.demo:
            print("Lancement de l'application principale...")
            # Utiliser le mécanisme de synchronisation et passer le flag --skip-auth
            # Modifier launch_app_with_sync pour ajouter le flag --skip-auth
            def modified_launch_app_with_sync():
                current_dir = os.path.dirname(os.path.abspath(__file__))
                
                # Supprimer le fichier de synchronisation s'il existe déjà
                sync_file = os.path.join(current_dir, ".sync_splash")
                if os.path.exists(sync_file):
                    try:
                        os.remove(sync_file)
                    except Exception as e:
                        print(f"Erreur lors de la suppression du fichier de synchronisation existant: {e}")
                
                # Créer un fichier temporaire pour indiquer que l'application doit se synchroniser
                try:
                    with open(sync_file, 'w') as f:
                        f.write(str(SYNC_PORT))
                except Exception as e:
                    print(f"Erreur lors de la création du fichier de synchronisation: {e}")
                    return
                
                # Lancer l'application principale avec les flags appropriés
                try:
                    subprocess.Popen([sys.executable, os.path.join(current_dir, "main.py"), 
                                     "--no-splash-recursion", "--skip-auth"])
                except Exception as e:
                    print(f"Erreur lors du lancement de l'application principale: {e}")
                    # Supprimer le fichier de synchronisation en cas d'erreur
                    cleanup_sync_file()
                    return
                
                # Supprimer le fichier de synchronisation après un délai
                def cleanup_sync_file_delayed():
                    time.sleep(10)  # Attendre 10 secondes
                    cleanup_sync_file()
                
                threading.Thread(target=cleanup_sync_file_delayed, daemon=True).start()
            
            # Utiliser la version modifiée pour lancer l'application
            launch_app_with_sync = modified_launch_app_with_sync
            
            # Lancer l'application principale avec le mécanisme de synchronisation
            launch_main_app()
        else:
            print("Mode démo - L'application principale ne sera pas lancée")
        
        # Démarrer la boucle principale
        print("Démarrage de la boucle principale...")
        splash_root.mainloop()
        print("Fin de l'écran de démarrage")
    finally:
        # Nettoyer le fichier drapeau anti-récursion
        cleanup_recursion_flag()
else:
    # Si le module est importé, vérifier d'abord la récursion
    if not check_recursion():
        # Vérifier le mot de passe avant de lancer l'application
        if not check_password():
            print("Authentification échouée. L'application ne sera pas démarrée.")
            sys.exit(1)
        
        # Créer et afficher l'écran de démarrage
        splash_root = tk.Tk()
        splash = SplashScreen(splash_root)
        
        # Utiliser la même approche pour lancer l'application principale avec synchronisation
        def modified_launch_app_with_sync():
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Supprimer le fichier de synchronisation s'il existe déjà
            sync_file = os.path.join(current_dir, ".sync_splash")
            if os.path.exists(sync_file):
                try:
                    os.remove(sync_file)
                except Exception as e:
                    print(f"Erreur lors de la suppression du fichier de synchronisation existant: {e}")
            
            # Créer un fichier temporaire pour indiquer que l'application doit se synchroniser
            try:
                with open(sync_file, 'w') as f:
                    f.write(str(SYNC_PORT))
            except Exception as e:
                print(f"Erreur lors de la création du fichier de synchronisation: {e}")
                return
            
            # Lancer l'application principale avec les flags appropriés
            try:
                subprocess.Popen([sys.executable, os.path.join(current_dir, "main.py"), 
                                 "--no-splash-recursion", "--skip-auth"])
            except Exception as e:
                print(f"Erreur lors du lancement de l'application principale: {e}")
                # Supprimer le fichier de synchronisation en cas d'erreur
                cleanup_sync_file()
                return
            
            # Supprimer le fichier de synchronisation après un délai
            def cleanup_sync_file_delayed():
                time.sleep(10)  # Attendre 10 secondes
                cleanup_sync_file()
            
            threading.Thread(target=cleanup_sync_file_delayed, daemon=True).start()
        
        # Utiliser la version modifiée pour lancer l'application
        launch_app_with_sync = modified_launch_app_with_sync
        
        # Lancer l'application principale avec le mécanisme de synchronisation
        launch_main_app()
        
        # Démarrer la boucle principale
        splash_root.mainloop()
        
        # Nettoyer le fichier drapeau anti-récursion
        cleanup_recursion_flag()
    else:
        # Si une instance est déjà en cours d'exécution, ne rien faire
        pass