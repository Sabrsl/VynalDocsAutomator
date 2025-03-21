#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitaires pour la gestion des dialogues dans l'application
"""

import customtkinter as ctk
import logging
import threading
import weakref
from typing import Optional, Callable
import tkinter.messagebox as messagebox

logger = logging.getLogger("VynalDocsAutomator.DialogUtils")

class DialogUtils:
    """
    Classe utilitaire pour gérer les dialogues et messages de l'application
    """
    
    # Couleurs pour les différents types de messages
    COLORS = {
        "success": "#2ecc71",  # Vert
        "error": "#e74c3c",    # Rouge
        "warning": "#f1c40f",  # Jaune
        "info": "#3498db"      # Bleu
    }
    
    # Cache des dialogues actifs
    _active_dialogs = weakref.WeakSet()
    _dialog_lock = threading.Lock()
    
    @classmethod
    def _cleanup_dialog(cls, dialog):
        """Nettoie un dialogue du cache"""
        with cls._dialog_lock:
            if dialog in cls._active_dialogs:
                cls._active_dialogs.remove(dialog)
    
    @classmethod
    def _create_dialog(cls, parent, title, message, dialog_type="info", callback=None):
        """
        Crée un dialogue personnalisé
        
        Args:
            parent: Widget parent
            title: Titre du dialogue
            message: Message à afficher
            dialog_type: Type de dialogue (success, error, warning, info)
            callback: Fonction à appeler à la fermeture
        """
        dialog = ctk.CTkToplevel(parent)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()
        
        # Centrer la fenêtre
        cls._center_dialog(dialog)
        
        # Frame principal avec padding
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Icône selon le type
        icon = "✓" if dialog_type == "success" else "❌" if dialog_type == "error" else "⚠️" if dialog_type == "warning" else "ℹ️"
        
        # Titre avec icône
        title_label = ctk.CTkLabel(
            main_frame,
            text=f"{icon} {title}",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Message
        message_label = ctk.CTkLabel(
            main_frame,
            text=message,
            wraplength=360
        )
        message_label.pack(pady=10)
        
        # Bouton OK
        def on_close():
            if callback:
                callback()
            dialog.destroy()
            cls._cleanup_dialog(dialog)
        
        ok_button = ctk.CTkButton(
            main_frame,
            text="OK",
            width=100,
            fg_color=cls.COLORS[dialog_type],
            hover_color=cls.COLORS[dialog_type],
            command=on_close
        )
        ok_button.pack(pady=10)
        
        # Ajouter au cache
        with cls._dialog_lock:
            cls._active_dialogs.add(dialog)
        
        # Gérer la fermeture
        dialog.protocol("WM_DELETE_WINDOW", on_close)
        
        return dialog
    
    @staticmethod
    def _center_dialog(dialog):
        """Centre un dialogue à l'écran"""
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    @staticmethod
    def show_message(parent, title, message, message_type="info", callback=None):
        """
        Affiche un message dans une boîte de dialogue
        
        Args:
            parent: Widget parent
            title: Titre du message
            message: Contenu du message
            message_type: Type de message (success, error, warning, info)
            callback: Fonction à appeler après fermeture
        """
        try:
            # Personnaliser l'icône en fonction du type de message
            icon = "ℹ️"  # Info par défaut
            if message_type == "success":
                icon = "✅"
            elif message_type == "warning":
                icon = "⚠️"
            elif message_type == "error":
                icon = "❌"
            
            dialog = ctk.CTkToplevel(parent)
            dialog.title(title)
            dialog.geometry("400x200")
            dialog.resizable(False, False)
            
            # Rendre la fenêtre modale
            dialog.transient(parent)
            dialog.grab_set()
            
            # Centrer la fenêtre
            dialog.update_idletasks()
            screen_width = dialog.winfo_screenwidth()
            screen_height = dialog.winfo_screenheight()
            x = (screen_width - dialog.winfo_width()) // 2
            y = (screen_height - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")
            
            # Contenu
            frame = ctk.CTkFrame(dialog, fg_color="transparent")
            frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
            
            # Icône et titre
            header_frame = ctk.CTkFrame(frame, fg_color="transparent")
            header_frame.pack(fill=ctk.X, pady=(0, 10))
            
            icon_label = ctk.CTkLabel(header_frame, text=icon, font=ctk.CTkFont(size=24))
            icon_label.pack(side=ctk.LEFT, padx=5)
            
            title_label = ctk.CTkLabel(
                header_frame, 
                text=title,
                font=ctk.CTkFont(size=16, weight="bold")
            )
            title_label.pack(side=ctk.LEFT, padx=5)
            
            # Message
            message_label = ctk.CTkLabel(
                frame,
                text=message,
                wraplength=350,
                justify="left"
            )
            message_label.pack(pady=10)
            
            # Bouton OK
            def on_ok():
                dialog.grab_release()
                dialog.destroy()
                if callback:
                    callback()
            
            ok_button = ctk.CTkButton(
                frame,
                text="OK",
                command=on_ok,
                width=100
            )
            ok_button.pack(pady=10)
            
            # Focus sur le bouton OK
            dialog.after(100, lambda: ok_button.focus())
            
            # Ajouter raccourci clavier pour fermer la boîte de dialogue avec Entrée ou Échap
            dialog.bind("<Return>", lambda e: on_ok())
            dialog.bind("<Escape>", lambda e: on_ok())
            
            # Rendre la boîte de dialogue modale
            dialog.wait_window()
            
            logger.debug(f"Message affiché: {message_type} - {title}")
            return dialog
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du message: {e}")
            # Fallback sur messagebox en cas d'erreur
            if message_type == "success":
                messagebox.showinfo(title, message)
            elif message_type == "warning":
                messagebox.showwarning(title, message)
            elif message_type == "error":
                messagebox.showerror(title, message)
            else:
                messagebox.showinfo(title, message)
            if callback:
                callback()
            return None
    
    @classmethod
    def show_confirmation(cls, parent, title, message, callback=None):
        """
        Affiche une boîte de dialogue de confirmation
        
        Args:
            parent: Widget parent
            title: Titre du message
            message: Contenu du message
            callback: Fonction à appeler avec le résultat (True/False)
        """
        dialog = ctk.CTkToplevel(parent)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()
        
        # Centrer la fenêtre
        cls._center_dialog(dialog)
        
        # Frame principal
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Message
        message_label = ctk.CTkLabel(
            main_frame,
            text=message,
            wraplength=360
        )
        message_label.pack(pady=20)
        
        # Frame pour les boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(pady=10)
        
        def on_confirm(result):
            if callback:
                callback(result)
            dialog.destroy()
            cls._cleanup_dialog(dialog)
        
        # Boutons
        ctk.CTkButton(
            button_frame,
            text="Oui",
            width=100,
            fg_color=cls.COLORS["success"],
            hover_color=cls.COLORS["success"],
            command=lambda: on_confirm(True)
        ).pack(side=ctk.LEFT, padx=10)
        
        ctk.CTkButton(
            button_frame,
            text="Non",
            width=100,
            fg_color=cls.COLORS["error"],
            hover_color=cls.COLORS["error"],
            command=lambda: on_confirm(False)
        ).pack(side=ctk.LEFT, padx=10)
        
        # Ajouter au cache
        with cls._dialog_lock:
            cls._active_dialogs.add(dialog)
        
        return dialog
    
    @classmethod
    def show_toast(cls, parent, message, message_type="success", duration=2000):
        """
        Affiche un message toast temporaire
        
        Args:
            parent: Widget parent
            message: Message à afficher
            message_type: Type de message (success, error, warning, info)
            duration: Durée d'affichage en millisecondes
        """
        try:
            # Créer le toast
            toast = ctk.CTkFrame(parent, fg_color=cls.COLORS[message_type])
            
            # Message
            message_label = ctk.CTkLabel(
                toast,
                text=message,
                text_color="white",
                font=ctk.CTkFont(size=12)
            )
            message_label.pack(padx=20, pady=10)
            
            # Positionner en bas de l'écran
            toast.place(relx=0.5, rely=0.95, anchor="center")
            
            # Faire disparaître après la durée spécifiée
            parent.after(duration, toast.destroy)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du toast: {e}")
    
    @staticmethod
    def validate_required_fields(parent, required_fields):
        """
        Valide les champs requis
        
        Args:
            parent: Widget parent
            required_fields: Liste de tuples (valeur, nom_champ)
        
        Returns:
            bool: True si tous les champs sont valides
        """
        missing_fields = [name for value, name in required_fields if not value or not value.strip()]
        
        if missing_fields:
            message = "Les champs suivants sont obligatoires :\n"
            message += "\n".join([f"- {field}" for field in missing_fields])
            
            DialogUtils.show_message(
                parent,
                "Champs obligatoires",
                message,
                "warning"
            )
            return False
        
        return True 