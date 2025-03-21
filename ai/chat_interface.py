import tkinter as tk
from tkinter import ttk, font, scrolledtext
import logging
import threading
import queue
import time
# Import la version modifiée de AIModel depuis le module ai
from ai import AIModel

class AIChatInterface:
    """
    Interface graphique moderne pour interagir avec un modèle d'IA de traitement de documents.
    Supporte des fonctionnalités avancées comme le streaming de réponses, les indications visuelles
    d'activité, et une UI adaptative.
    """
    
    COLORS = {
        "background": "#1A202C",     # Fond gris anthracite
        "surface": "#2D3748",        # Surface gris foncé pour cartes et boutons
        "primary": "#4A90E2",        # Bleu pro pour boutons actifs
        "secondary": "#718096",      # Gris moyen pour assistant
        "accent": "#A0AEC0",         # Gris clair pour accents et hover
        "error": "#F56565",          # Rouge doux pour erreurs
        "text_primary": "#E2E8F0",   # Texte principal blanc doux
        "text_secondary": "#A0AEC0", # Texte secondaire gris
        "welcome": "#A0AEC0",        # Gris pour messages d'accueil
        "success": "#68D391",        # Vert doux pour succès
    }
    
    def __init__(self, parent):
        """
        Initialise l'interface de chat.
        
        Args:
            parent: Widget parent Tkinter
        """
        self.parent = parent
        self.frame = tk.Frame(parent, bg=self.COLORS["background"])
        self.ai = AIModel()
        
        # File d'attente pour la communication entre threads
        self.response_queue = queue.Queue()
        
        # Configuration du style
        self.configure_style()
        
        # Configuration de l'interface utilisateur
        self.setup_ui()
        
        # Démarrer le vérificateur de file d'attente
        self.parent.after(100, self.check_queue)
        
        # Afficher un message de bienvenue
        self.display_welcome_message()
        
        # Logger l'initialisation
        logging.info("Interface de chat IA initialisée")
    
    def configure_style(self):
        """Configure le style global de l'interface"""
        style = ttk.Style()
        
        # Configurer le thème global si disponible
        try:
            style.theme_use("clam")  # Utiliser un thème moderne si disponible
        except tk.TclError:
            pass  # Ignorer si le thème n'est pas disponible
        
        # Style simple pour les boutons ttk
        style.configure(
            "TButton",
            background=self.COLORS["primary"],
            foreground=self.COLORS["text_primary"],
            borderwidth=0,
            relief="flat",
            padding=(10, 5)
        )
    
    def setup_ui(self):
        """Met en place tous les éléments de l'interface utilisateur"""
        # Configurer le frame principal
        self.frame.pack(fill="both", expand=True)
        
        # En-tête épuré
        self.header_frame = tk.Frame(self.frame, bg=self.COLORS["background"])
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Typographie moderne pour l'en-tête - utiliser la police système par défaut si Segoe UI n'est pas disponible
        try:
            header_font = font.Font(family="Segoe UI", size=16, weight="bold")
        except:
            header_font = font.Font(size=16, weight="bold")
            
        self.header_label = tk.Label(
            self.header_frame,
            text="Assistant Documents",
            font=header_font,
            foreground=self.COLORS["text_primary"],
            background=self.COLORS["background"]
        )
        self.header_label.pack(side="left", pady=10)
        
        # Statut de l'IA avec design minimaliste
        self.status_frame = tk.Frame(self.header_frame, bg=self.COLORS["background"])
        self.status_frame.pack(side="right", pady=10)
        
        # Utiliser la police système pour assurer la compatibilité
        try:
            status_font = font.Font(family="Segoe UI", size=12)
        except:
            status_font = font.Font(size=12)
            
        self.status_indicator = tk.Label(
            self.status_frame,
            text="●",
            foreground=self.COLORS["secondary"],
            background=self.COLORS["background"],
            font=status_font
        )
        self.status_indicator.pack(side="left", padx=(0, 5))
        
        try:
            status_label_font = font.Font(family="Segoe UI", size=10)
        except:
            status_label_font = font.Font(size=10)
            
        self.status_label = tk.Label(
            self.status_frame,
            text="Prêt",
            foreground=self.COLORS["text_secondary"],
            background=self.COLORS["background"],
            font=status_label_font
        )
        self.status_label.pack(side="left")
        
        # Zone de chat avec bords arrondis (simulation via padding)
        self.chat_container = tk.Frame(self.frame, bg=self.COLORS["background"])
        self.chat_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Police compatible pour le chat
        try:
            chat_font = font.Font(family="Segoe UI", size=10)
        except:
            chat_font = font.Font(size=10)
        
        # Chat avec ScrolledText simplifiée pour assurer la compatibilité
        self.chat_text = scrolledtext.ScrolledText(
            self.chat_container,
            wrap="word",
            height=20,
            background=self.COLORS["background"],  # Fond de la même couleur que le container
            foreground=self.COLORS["text_primary"],
            borderwidth=1,
            relief="solid",
            padx=15,
            pady=15,
            font=chat_font
        )
        self.chat_text.pack(fill="both", expand=True)
        
        # Zone de saisie flottante avec style moderne
        self.input_frame = tk.Frame(self.frame, bg=self.COLORS["background"])
        self.input_frame.pack(fill="x", padx=20, pady=(5, 20))
        
        # Conteneur pour zone de saisie avec style flottant
        self.input_container = tk.Frame(
            self.input_frame,
            bg=self.COLORS["background"],  # Même couleur que le fond
            padx=2,
            pady=2,
            highlightbackground=self.COLORS["accent"],
            highlightthickness=1,  # Bordure fine
            highlightcolor=self.COLORS["primary"]
        )
        self.input_container.pack(fill="x", expand=True, side="left", padx=(0, 10))
        
        # Police compatible pour la saisie
        try:
            entry_font = font.Font(family="Segoe UI", size=10)
        except:
            entry_font = font.Font(size=10)
            
        # Zone de texte avec style simplifié
        self.message_entry = tk.Text(
            self.input_container,
            height=2,
            wrap="word",
            background=self.COLORS["background"],  # Même couleur que le fond
            foreground=self.COLORS["text_primary"],
            borderwidth=0,
            relief="flat",
            padx=10,
            pady=5,
            font=entry_font
        )
        self.message_entry.pack(fill="x", expand=True, side="left")
        
        # Ajouter un placeholder moderne
        self.placeholder_text = "Envoyez un message..."
        self.message_entry.insert("1.0", self.placeholder_text)
        self.message_entry.config(foreground=self.COLORS["text_secondary"])
        
        # Gestion du placeholder et focus
        self.message_entry.bind("<FocusIn>", self.on_entry_focus_in)
        self.message_entry.bind("<FocusOut>", self.on_entry_focus_out)
        
        # Bouton d'envoi avec une icône de flèche (style ChatGPT)
        self.send_button = tk.Button(
            self.input_container,
            text="↑",  # Flèche vers le haut
            command=self.send_message,
            bg=self.COLORS["primary"],
            fg="#FFFFFF",
            relief="flat",
            padx=0,
            pady=0,
            font=("Segoe UI", 14, "bold") if "Segoe UI" in font.families() else (None, 14, "bold"),
            width=2,  # Largeur fixe pour rendre le bouton rond
            height=1,  # Hauteur fixe
            cursor="hand2",  # Pointeur de type main
            activebackground="#3A7BC8",  # Couleur au survol
            activeforeground="#FFFFFF"  # Couleur du texte au survol
        )
        self.send_button.pack(side="right", padx=(5, 5), pady=(5, 5))
        
        # Arrondir les bordures du bouton (simulation)
        self.send_button.configure(bd=0, highlightthickness=0)
        
        # Gérer l'événement Entrée pour envoyer le message
        self.message_entry.bind("<Return>", self.on_enter_pressed)
        self.message_entry.bind("<Shift-Return>", lambda e: None)  # Permet de faire un retour à la ligne avec Shift+Enter
        
        # Configurer les tags de style pour le texte
        self.configure_text_tags()
        
        # Forcer la mise à jour de l'interface
        self.frame.update()
        self.parent.update_idletasks()
    
    def configure_text_tags(self):
        """Configure les tags de style pour le texte du chat"""
        # Utiliser des polices de système au lieu de forcer Segoe UI
        try:
            ui_font = font.Font(family="Segoe UI", size=11)  # Police plus grande
            ui_font_bold = font.Font(family="Segoe UI", size=11, weight="bold")
            ui_font_italic = font.Font(family="Segoe UI", size=11, slant="italic")
            ui_font_small = font.Font(family="Segoe UI", size=10)
            ui_font_title = font.Font(family="Segoe UI", size=16, weight="bold")
        except:
            ui_font = font.Font(size=11)
            ui_font_bold = font.Font(size=11, weight="bold")
            ui_font_italic = font.Font(size=11, slant="italic")
            ui_font_small = font.Font(size=10)
            ui_font_title = font.Font(size=16, weight="bold")
        
        # Style pour les messages utilisateur - pas de fond coloré
        self.chat_text.tag_configure(
            "user",
            foreground="#FFFFFF",  # Texte blanc pour meilleure lisibilité
            background=self.COLORS["background"],  # Même fond que la zone de chat
            font=ui_font,
            justify="right",  # Aligné à droite
            lmargin1=80,  # Grande marge à gauche
            lmargin2=80,
            rmargin=20
        )
        
        # Style pour le préfixe utilisateur
        self.chat_text.tag_configure(
            "user_prefix",
            foreground=self.COLORS["text_secondary"],
            background=self.COLORS["background"],
            font=ui_font_small,
            justify="right"  # Aligné à droite
        )
        
        # Style pour les messages de l'assistant - pas de fond coloré
        self.chat_text.tag_configure(
            "assistant", 
            foreground=self.COLORS["text_primary"],
            background=self.COLORS["background"],  # Même fond que la zone de chat
            font=ui_font,
            lmargin1=20,
            lmargin2=20,
            rmargin=80  # Grande marge à droite
        )
        
        # Style pour le préfixe assistant
        self.chat_text.tag_configure(
            "assistant_prefix",
            foreground=self.COLORS["text_secondary"],
            background=self.COLORS["background"],
            font=ui_font_small
        )
        
        # Tag pour l'icône robot - plus visible
        self.chat_text.tag_configure(
            "assistant_icon",
            foreground=self.COLORS["primary"],
            background=self.COLORS["background"],
            font=font.Font(family="Segoe UI", size=14) if "Segoe UI" in font.families() else font.Font(size=14)
        )
        
        # Style pour les erreurs - garder un fond pour les messages d'erreur
        self.chat_text.tag_configure(
            "error",
            foreground="#FFFFFF",
            background=self.COLORS["error"],
            font=ui_font_bold,
            lmargin1=20,
            lmargin2=20
        )
        
        # Style pour les messages de bienvenue
        self.chat_text.tag_configure(
            "welcome",
            foreground=self.COLORS["text_primary"],
            background=self.COLORS["background"],
            font=ui_font,
            lmargin1=20,
            lmargin2=20
        )
        
        # Style pour les titres de bienvenue
        self.chat_text.tag_configure(
            "welcome_title",
            foreground=self.COLORS["primary"],
            background=self.COLORS["background"],
            font=ui_font_title,
            lmargin1=20,
            lmargin2=20
        )
        
        # Style pour l'indication de réflexion
        self.chat_text.tag_configure(
            "thinking",
            foreground=self.COLORS["text_secondary"],
            background=self.COLORS["background"],
            font=ui_font_italic,
            lmargin1=20,
            lmargin2=20
        )
        
        # Style pour les astuces
        self.chat_text.tag_configure(
            "tip",
            foreground=self.COLORS["text_primary"],
            background=self.COLORS["background"],
            font=ui_font_italic,
            lmargin1=35,  # Marge plus grande pour compenser le badge
            lmargin2=35
        )
        
        # Style pour le badge d'astuce
        self.chat_text.tag_configure(
            "tip_badge",
            foreground=self.COLORS["background"],
            background=self.COLORS["primary"],
            font=ui_font_small
        )
    
    def on_entry_focus_in(self, event):
        """Gère l'événement de focus sur la zone de saisie"""
        current_text = self.message_entry.get("1.0", "end-1c")
        if current_text == self.placeholder_text:
            self.message_entry.delete("1.0", "end")
            self.message_entry.config(foreground=self.COLORS["text_primary"])
        # Si le texte commence par le placeholder, le supprimer
        elif current_text.startswith(self.placeholder_text):
            clean_text = current_text.replace(self.placeholder_text, "").strip()
            self.message_entry.delete("1.0", "end")
            self.message_entry.insert("1.0", clean_text)
            self.message_entry.config(foreground=self.COLORS["text_primary"])
    
    def on_entry_focus_out(self, event):
        """Gère l'événement de perte de focus sur la zone de saisie"""
        if not self.message_entry.get("1.0", "end-1c").strip():
            self.message_entry.delete("1.0", "end")
            self.message_entry.insert("1.0", self.placeholder_text)
            self.message_entry.config(foreground=self.COLORS["text_secondary"])
    
    def on_enter_pressed(self, event):
        """Gère l'événement de la touche Entrée pressée"""
        if not event.state & 0x1:  # Si Shift n'est pas enfoncé
            self.send_message()
            return "break"  # Empêche l'insertion d'un retour à la ligne
    
    def display_welcome_message(self):
        """Affiche un message de bienvenue pour expliquer les fonctionnalités"""
        welcome_message = """
Je peux vous aider à :

• 📄 Créer un nouveau document
• 🧩 Utiliser un modèle existant
• 📝 Remplir des modèles avec vos informations

Pour commencer, demandez-moi simplement ce que vous souhaitez faire.
"""
        # Utiliser notre nouvelle méthode add_message
        self.add_message(welcome_message, "welcome")
    
    def safe_insert_text(self, text, tag=None):
        """
        Insère du texte de manière sécurisée dans le widget Text
        
        Args:
            text (str): Le texte à insérer
            tag (str, optional): Le tag de style à appliquer
        """
        try:
            # Utiliser la méthode add_message pour toutes les insertions de texte
            if tag == "user":
                self.add_message(text, "user")
            elif tag == "assistant":
                self.add_message(text, "assistant")
            elif tag == "error":
                self.add_message(text, "error")
            elif tag == "tip":
                # Cas spécial pour les astuces
                self.chat_text.configure(state="normal")
                self.chat_text.insert("end", "\n\n")
                self.chat_text.insert("end", "💡 ", "tip_badge")
                self.chat_text.insert("end", text, "tip")
                self.chat_text.see("end")
                self.chat_text.configure(state="disabled")
                self.chat_text.update()
                self.parent.update_idletasks()
            else:
                # Pour les autres types de messages
                self.add_message(text, tag or "assistant")
                
        except Exception as e:
            logging.error(f"Erreur lors de l'insertion de texte: {e}")
            
    def add_message(self, message, sender="assistant"):
        """Ajoute un message au chat et défile vers le bas"""
        self.chat_text.configure(state="normal")
        
        # Vide la zone de réflexion si elle existe
        self.clear_thinking_indicator()
        
        # Ajoute un espace avant chaque nouveau message
        if self.chat_text.get("1.0", "end-1c") != "":
            self.chat_text.insert("end", "\n\n")
        
        # Si c'est un message de l'utilisateur
        if sender == "user":
            self.chat_text.insert("end", f"{message}", "user")
            self.chat_text.insert("end", "\n")
            self.chat_text.insert("end", "Vous", "user_prefix")
        
        # Si c'est un message de l'assistant
        elif sender == "assistant":
            self.chat_text.insert("end", "🤖 ", "assistant_icon")
            self.chat_text.insert("end", "Assistant\n", "assistant_prefix")
            self.chat_text.insert("end", f"{message}", "assistant")
        
        # Si c'est un message d'erreur
        elif sender == "error":
            self.chat_text.insert("end", f"❌ Erreur: {message}", "error")
        
        # Si c'est un message de bienvenue
        elif sender == "welcome":
            # Ajoute le titre de bienvenue
            self.chat_text.insert("end", "Bienvenue dans l'Assistant Vynal!\n\n", "welcome_title")
            
            # Ajoute le message de bienvenue
            self.chat_text.insert("end", message, "welcome")
            
            # Ajoute une astuce
            self.chat_text.insert("end", "\n\n")
            self.chat_text.insert("end", "💡 ", "tip_badge")
            self.chat_text.insert("end", "Astuce: Posez des questions sur vos fichiers ou demandez de l'aide pour naviguer dans l'application.", "tip")
        
        # Défile vers le bas pour voir le dernier message
        self.chat_text.see("end")
        
        # Désactive l'édition de la zone de texte
        self.chat_text.configure(state="disabled")
        
        # Mise à jour forcée pour assurer le rendu
        self.chat_text.update()
        self.parent.update_idletasks()
        
    def clear_thinking_indicator(self):
        """Efface l'indicateur de réflexion s'il existe"""
        last_thinking_pos = self.chat_text.search("Assistant en cours de réflexion...", "1.0", "end", backwards=True)
        if last_thinking_pos:
            line_start = self.chat_text.index(f"{last_thinking_pos} linestart")
            line_end = self.chat_text.index(f"{last_thinking_pos} lineend+2c")  # +2c pour inclure le \n\n
            self.chat_text.delete(line_start, line_end)
    
    def update_streaming_text(self, new_text, tag="assistant"):
        """
        Met à jour le texte en streaming
        
        Args:
            new_text (str): Le nouveau texte à ajouter
            tag (str): Le tag de style à appliquer
        """
        try:
            self.chat_text.config(state="normal")
            
            # Trouver la dernière position où se trouve le texte de chargement
            last_pos = self.chat_text.search("Assistant en cours de réflexion...", "1.0", "end", backwards=True)
            
            if last_pos:
                # Calculer la position de début et de fin du message
                line_start = self.chat_text.index(f"{last_pos} linestart")
                line_end = self.chat_text.index(f"{last_pos} lineend+2c")  # +2c pour le \n\n
                
                # Supprimer l'ancien texte
                self.chat_text.delete(line_start, line_end)
                
                # Insérer le nouveau texte
                self.chat_text.insert(line_start, new_text)
                
                # Appliquer le style
                self.chat_text.tag_add(tag, line_start, f"{line_start} + {len(new_text)}c")
                
                # Ajouter des sauts de ligne
                self.chat_text.insert(f"{line_start} + {len(new_text)}c", "\n\n")
                
                # S'assurer que le texte est visible
                self.chat_text.see("end")
            
            self.chat_text.config(state="disabled")
            
            # Force la mise à jour de l'interface
            self.parent.update_idletasks()
            
        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour du texte en streaming: {e}", exc_info=True)
    
    def update_status(self, is_thinking=False):
        """
        Met à jour l'indicateur de statut
        
        Args:
            is_thinking (bool): True si l'IA est en train de réfléchir
        """
        if is_thinking:
            self.status_indicator.config(foreground="#F59E0B")  # Jaune/orange
            self.status_label.config(text="En cours de réponse")
        else:
            self.status_indicator.config(foreground=self.COLORS["secondary"])
            self.status_label.config(text="Prêt")
    
    def send_message(self):
        """Envoie le message et gère la réponse de l'IA"""
        # Obtenir le texte de l'entrée
        message_text = self.message_entry.get("1.0", "end-1c").strip()
        
        # Si le message est vide ou contient seulement le placeholder, ne rien faire
        if not message_text or message_text == self.placeholder_text:
            return
        
        # Vérifier si le message contient le placeholder et le supprimer
        if self.placeholder_text in message_text:
            message = message_text.replace(self.placeholder_text, "").strip()
        else:
            message = message_text
            
        if not message:
            return
            
        # Journaliser le message réel envoyé
        print(f"DEBUG - Message envoyé à l'IA: '{message}'")
        
        # Afficher le message de l'utilisateur avec le style simplifié
        self.add_message(message, "user")
        
        # Réinitialiser l'entrée
        self.message_entry.delete("1.0", "end")
        self.message_entry.focus_set()
        self.message_entry.config(foreground=self.COLORS["text_primary"])
        
        # Ajouter le message à l'historique
        self.ai.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # Afficher un indicateur de chargement
        self.chat_text.config(state="normal")
        start_pos = self.chat_text.index("end-1c")
        self.chat_text.insert("end", "\n\nAssistant en cours de réflexion...")
        self.chat_text.tag_add("thinking", start_pos, "end-1c")
        self.chat_text.see("end")
        self.chat_text.config(state="disabled")
        
        # Mettre à jour le statut
        self.update_status(is_thinking=True)
        
        # Force une mise à jour de l'interface pour montrer l'indicateur de chargement
        self.parent.update_idletasks()
        
        # Désactiver l'interface pendant la génération
        self.message_entry.config(state="disabled")
        self.send_button.config(state="disabled")
        
        # Démarrer la génération dans un thread séparé
        threading.Thread(target=self.generate_response, args=(message,), daemon=True).start()
        
    def generate_response(self, message):
        """
        Génère une réponse de l'IA dans un thread séparé
        
        Args:
            message (str): Le message de l'utilisateur
        """
        try:
            # Obtenir la réponse directement de model_patch.py
            response = self.ai.generate_response(message)
            
            # Journal de débogage
            print(f"DEBUG - Réponse reçue : {response}")
            
            # Mettre la réponse dans la file d'attente
            self.response_queue.put({
                "type": "response",
                "content": response,
                "state": self.ai.current_context.get("state", "initial"),
                "last_action": self.ai.current_context.get("last_action", None)
            })
            
        except Exception as e:
            error_message = f"Erreur : {str(e)}"
            self.response_queue.put({
                "type": "error",
                "content": error_message
            })
            print(f"DEBUG - Exception dans generate_response: {str(e)}")
            logging.error(f"Erreur lors de la génération de réponse: {e}", exc_info=True)
    
    def check_queue(self):
        """Vérifie la file d'attente pour les messages du thread de génération"""
        try:
            if not self.response_queue.empty():
                item = self.response_queue.get_nowait()
                
                # Supprimer l'indicateur de chargement quelle que soit la réponse
                self.clear_thinking_indicator()
                
                if item["type"] == "response":
                    response = item["content"]
                    if response:
                        self.add_message(response, "assistant")
                        # Ajouter la réponse à l'historique
                        self.ai.conversation_history.append({
                            "role": "assistant",
                            "content": response
                        })
                    else:
                        # Message par défaut en cas de réponse vide
                        default_response = "Je n'ai pas pu traiter votre demande. Veuillez réessayer."
                        self.add_message(default_response, "assistant")
                        self.ai.conversation_history.append({
                            "role": "assistant",
                            "content": default_response
                        })
                
                elif item["type"] == "error":
                    # Afficher l'erreur
                    self.add_message(item["content"], "error")
                
                # Réactiver l'interface
                self.message_entry.config(state="normal")
                self.send_button.config(state="normal")
                
                # Focus sur l'entrée de message
                self.message_entry.focus_set()
                
                # Réinitialiser le statut
                self.update_status(is_thinking=False)
                
                # Gérer le placeholder si nécessaire
                if not self.message_entry.get("1.0", "end-1c").strip():
                    self.message_entry.delete("1.0", "end")
                    self.message_entry.insert("1.0", self.placeholder_text)
                    self.message_entry.config(foreground=self.COLORS["text_secondary"])
                
                # Forcer une mise à jour de l'interface
                self.parent.update_idletasks()
        
        except Exception as e:
            logging.error(f"Erreur lors de la vérification de la file d'attente: {e}", exc_info=True)
        
        # Reprogrammer la vérification
        self.parent.after(100, self.check_queue)