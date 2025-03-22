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
        "warning": "#F6AD55",        # Orange doux pour avertissements
        "info": "#63B3ED",           # Bleu doux pour information
    }
    
    def __init__(self, parent):
        """
        Initialise l'interface de chat.
        
        Args:
            parent: Widget parent Tkinter
        """
        self.parent = parent
        self.frame = tk.Frame(parent, bg=self.COLORS["background"])
        self.ai = None  # Initialisation différée
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        
        # File d'attente pour la communication entre threads
        self.response_queue = queue.Queue()
        
        # Configuration du style
        self.configure_style()
        
        # Configuration de l'interface utilisateur
        self.setup_ui()
        
        # Démarrer le vérificateur de file d'attente
        self.parent.after(100, self.check_queue)
        
        # Initialiser l'IA
        self.initialize_ai()
        
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
        
        # Initialiser les polices pour les messages
        try:
            self.message_font = font.Font(family="Segoe UI", size=11)
            self.user_tag_font = font.Font(family="Segoe UI", size=11, weight="bold")
            self.ai_tag_font = font.Font(family="Segoe UI", size=11, weight="bold")
            self.system_font = font.Font(family="Segoe UI", size=10, slant="italic")
        except:
            # Fallback vers les polices système
            self.message_font = font.Font(size=11)
            self.user_tag_font = font.Font(size=11, weight="bold")
            self.ai_tag_font = font.Font(size=11, weight="bold")
            self.system_font = font.Font(size=10, slant="italic")
        
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
            text="Vynal•GPT",
            font=header_font,
            foreground=self.COLORS["text_primary"],
            background=self.COLORS["background"]
        )
        self.header_label.pack(side="left", pady=10)
        
        # Bouton de réinitialisation à côté du titre
        self.reset_button = tk.Button(
            self.header_frame,
            text="🔄",  # Icône de rafraîchissement
            command=self.reset_chat,
            bg=self.COLORS["background"],
            fg=self.COLORS["text_primary"],
            relief="flat",
            padx=5,
            pady=0,
            font=("Segoe UI", 14) if "Segoe UI" in font.families() else (None, 14),
            cursor="hand2",  # Pointeur de type main
            activebackground=self.COLORS["surface"],  # Couleur au survol
            activeforeground=self.COLORS["text_primary"]  # Couleur du texte au survol
        )
        self.reset_button.pack(side="left", padx=(10, 0), pady=10)
        
        # Info-bulle pour le bouton de réinitialisation
        self.create_tooltip(self.reset_button, "Réinitialiser la conversation")
        
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
Je suis Vynal•GPT, votre assistant spécialisé en création et rédaction de documents professionnels.

Je peux vous aider à :

• 📝 Rédiger des documents complets (contrats, lettres, attestations, rapports...)
• 📋 Structurer professionnellement vos contenus (titres, sections, articles)
• ✏️ Améliorer vos textes existants (corrections, reformulations, optimisations)
• 📊 Formater le contenu pour une lisibilité optimale
• 🔍 Expliquer des termes juridiques, techniques ou administratifs
• 📄 Personnaliser les documents avec vos informations spécifiques

Pour obtenir un document, précisez simplement :
- Le type exact de document souhaité
- Le contexte professionnel
- Les informations essentielles à inclure
- Toute exigence particulière de format ou de ton

Comment puis-je vous assister aujourd'hui ?
"""
        # Utiliser notre méthode add_message
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
            self.chat_text.insert("end", "Vynal•GPT\n", "assistant_prefix")
            self.chat_text.insert("end", f"{message}", "assistant")
        
        # Si c'est un message d'erreur
        elif sender == "error":
            self.chat_text.insert("end", f"❌ Erreur: {message}", "error")
        
        # Si c'est un message de bienvenue
        elif sender == "welcome":
            # Ajoute le titre de bienvenue
            self.chat_text.insert("end", "Bienvenue dans Vynal•GPT\n\n", "welcome_title")
            
            # Ajoute le message de bienvenue
            self.chat_text.insert("end", message, "welcome")
            
            # Ajoute une astuce
            self.chat_text.insert("end", "\n\n")
            self.chat_text.insert("end", "💡 ", "tip_badge")
            self.chat_text.insert("end", "Astuce: Soyez précis et détaillé dans vos demandes pour obtenir un document parfaitement adapté à vos besoins professionnels. Plus votre requête est spécifique, meilleur sera le résultat.", "tip")
        
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
    
    def initialize_ai(self):
        """Initialise le modèle d'IA avec traitement des erreurs"""
        try:
            from ai import AIModel
            self.ai = AIModel()
            self.connection_attempts = 0
            logging.info("Modèle AI initialisé avec succès")
            
            # Vérifier la connexion à l'API
            self.display_status_message("Vérification de la connexion au modèle...")
            self.parent.update_idletasks()
            
            # Test simple
            test_result = self.ai._verify_model()
            if test_result:
                self.display_status_message("Connexion au modèle établie.", "success")
            else:
                self.display_status_message("Impossible de se connecter au modèle LLaMa. Vérifiez qu'Ollama est en cours d'exécution.", "error")
                self.display_chat_message("⚠️ Attention: Le modèle LLaMa n'est pas disponible. Vérifiez qu'Ollama est en cours d'exécution et redémarrez l'application.", "error")
        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation du modèle AI: {e}")
            self.display_status_message(f"Erreur d'initialisation: {e}", "error")
            self.display_chat_message(f"⚠️ Erreur: Impossible d'initialiser le modèle AI. Détails: {e}", "error")

    def send_message(self):
        """Envoie le message de l'utilisateur à l'IA"""
        # Récupérer le message
        user_message = self.message_entry.get("1.0", "end-1c").strip()
        
        # Ne pas envoyer de message vide
        if not user_message or user_message == self.placeholder_text:
            return
        
        # Vérifier si le modèle AI est disponible
        if self.ai is None:
            self.initialize_ai()
            if self.ai is None:
                # Toujours pas disponible après tentative de réinitialisation
                self.display_chat_message("⚠️ Le modèle n'est pas disponible. Tentative de reconnexion...", "error")
                self.retry_connection()
                return
            
        # Effacer le champ de texte
        self.message_entry.delete("1.0", "end")
        self.message_entry.focus_set()
        
        # Ajouter le message utilisateur à l'interface
        self.display_user_message(user_message)
        
        # Indiquer que l'IA est en train de répondre
        self.set_ai_status("thinking")
        
        # Traiter le message dans un thread séparé
        threading.Thread(target=self.process_message, args=(user_message,), daemon=True).start()
    
    def process_message(self, message):
        """Traite le message dans un thread séparé"""
        try:
            # Obtenir la réponse du modèle AI
            for chunk in self.ai.generate_response(message, stream=True):
                self.response_queue.put(("chunk", chunk))
            
            # Indiquer que le traitement est terminé
            self.response_queue.put(("end", None))
        except Exception as e:
            logging.error(f"Erreur lors du traitement du message: {e}")
            error_message = f"Une erreur est survenue: {str(e)}"
            self.response_queue.put(("error", error_message))
            
            # Vérifier si c'est une erreur de connexion et tenter une reconnexion
            if "connexion" in str(e).lower() or "connection" in str(e).lower():
                self.retry_connection()
    
    def retry_connection(self):
        """Tente de se reconnecter au modèle AI"""
        if self.connection_attempts < self.max_connection_attempts:
            self.connection_attempts += 1
            self.display_status_message(f"Tentative de reconnexion ({self.connection_attempts}/{self.max_connection_attempts})...", "warning")
            
            # Attendre un peu avant de réessayer
            def delayed_retry():
                self.initialize_ai()
                if self.ai is not None and self.ai._verify_model():
                    self.display_status_message("Reconnexion réussie", "success")
                    self.display_chat_message("✅ Connexion au modèle rétablie", "success")
                else:
                    self.display_status_message("Échec de la reconnexion", "error")
                    if self.connection_attempts < self.max_connection_attempts:
                        self.parent.after(2000, self.retry_connection)
                    else:
                        self.display_chat_message("❌ Impossible de se connecter au modèle après plusieurs tentatives. Vérifiez qu'Ollama est en cours d'exécution.", "error")
            
            self.parent.after(2000, delayed_retry)
        else:
            self.display_status_message("Nombre maximal de tentatives atteint", "error")

    def check_queue(self):
        """Vérifie la file d'attente pour les réponses du thread de traitement"""
        try:
            # Récupérer les messages sans bloquer
            while not self.response_queue.empty():
                msg_type, content = self.response_queue.get_nowait()
                
                if msg_type == "chunk":
                    # Ajouter un morceau de la réponse
                    self.display_ai_response_chunk(content)
                elif msg_type == "end":
                    # Indiquer que l'IA a fini de répondre
                    self.set_ai_status("ready")
                elif msg_type == "error":
                    # Afficher un message d'erreur
                    self.display_chat_message(content, "error")
                    self.set_ai_status("error")
        except queue.Empty:
            pass
        
        # Continuer à vérifier
        self.parent.after(100, self.check_queue)
    
    def display_status_message(self, message, status_type="info"):
        """Affiche un message de statut"""
        # Couleur selon le type de statut
        colors = {
            "info": self.COLORS["secondary"],
            "success": self.COLORS["success"],
            "warning": self.COLORS["warning"],
            "error": self.COLORS["error"]
        }
        
        color = colors.get(status_type, self.COLORS["secondary"])
        
        # Mettre à jour le statut
        self.status_indicator.config(foreground=color)
        self.status_label.config(text=message, foreground=color)
        
        # Forcer la mise à jour
        self.parent.update_idletasks()
    
    def set_ai_status(self, status):
        """Configure l'état visuel de l'IA"""
        statuses = {
            "ready": {"text": "●", "color": self.COLORS["success"], "status": "Prêt"},
            "thinking": {"text": "●", "color": self.COLORS["warning"], "status": "En attente de réponse..."},
            "error": {"text": "●", "color": self.COLORS["error"], "status": "Erreur"}
        }
        
        if status in statuses:
            status_info = statuses[status]
            self.status_indicator.config(text=status_info["text"], foreground=status_info["color"])
            self.status_label.config(text=status_info["status"])
        
        # Forcer la mise à jour
        self.parent.update_idletasks()

    def display_user_message(self, message):
        """Affiche un message de l'utilisateur dans le chat"""
        self.chat_text.config(state="normal")
        
        # Ajouter un peu d'espace si nécessaire
        if self.chat_text.index("end-1c linestart") != self.chat_text.index("1.0"):
            self.chat_text.insert("end", "\n\n")
        
        # Tag pour l'utilisateur
        user_tag_start = self.chat_text.index("end-1c")
        self.chat_text.insert("end", "Vous: ", "user_tag")
        self.chat_text.tag_add("user_tag", user_tag_start, "end-1c")
        self.chat_text.tag_config("user_tag", foreground=self.COLORS["primary"], font=self.user_tag_font)
        
        # Message de l'utilisateur
        message_start = self.chat_text.index("end-1c")
        self.chat_text.insert("end", message, "user_message")
        self.chat_text.tag_add("user_message", message_start, "end-1c")
        self.chat_text.tag_config("user_message", foreground=self.COLORS["text_primary"], font=self.message_font)
        
        # Faire défiler vers le bas
        self.chat_text.see("end")
        self.chat_text.config(state="disabled")
    
    def display_ai_response_chunk(self, chunk):
        """Affiche un morceau de réponse de l'IA dans le chat"""
        self.chat_text.config(state="normal")
        
        # Si c'est le premier morceau, ajouter l'en-tête
        if not hasattr(self, 'ai_response_started') or not self.ai_response_started:
            # Ajouter un peu d'espace
            if self.chat_text.index("end-1c linestart") != self.chat_text.index("1.0"):
                self.chat_text.insert("end", "\n\n")
            
            # Tag pour l'assistant
            ai_tag_start = self.chat_text.index("end-1c")
            self.chat_text.insert("end", "Vynal•GPT: ", "ai_tag")
            self.chat_text.tag_add("ai_tag", ai_tag_start, "end-1c")
            self.chat_text.tag_config("ai_tag", foreground=self.COLORS["secondary"], font=self.ai_tag_font)
            
            # Marquer que la réponse a commencé
            self.ai_response_started = True
            self.ai_response_start = self.chat_text.index("end-1c")
        
        # Ajouter le morceau de la réponse
        chunk_start = self.chat_text.index("end-1c")
        self.chat_text.insert("end", chunk, "ai_message")
        self.chat_text.tag_add("ai_message", chunk_start, "end-1c")
        self.chat_text.tag_config("ai_message", foreground=self.COLORS["text_primary"], font=self.message_font)
        
        # Faire défiler vers le bas
        self.chat_text.see("end")
        self.chat_text.config(state="disabled")
        
        # Forcer la mise à jour
        self.parent.update_idletasks()
    
    def display_chat_message(self, message, message_type="info"):
        """Affiche un message système dans le chat"""
        # Couleur selon le type
        colors = {
            "info": self.COLORS["info"],
            "success": self.COLORS["success"],
            "warning": self.COLORS["warning"],
            "error": self.COLORS["error"]
        }
        color = colors.get(message_type, self.COLORS["info"])
        
        self.chat_text.config(state="normal")
        
        # Ajouter un peu d'espace
        if self.chat_text.index("end-1c linestart") != self.chat_text.index("1.0"):
            self.chat_text.insert("end", "\n\n")
        
        # Message système
        system_start = self.chat_text.index("end-1c")
        self.chat_text.insert("end", message, "system_message")
        self.chat_text.tag_add("system_message", system_start, "end-1c")
        self.chat_text.tag_config("system_message", foreground=color, font=self.system_font)
        
        # Faire défiler vers le bas
        self.chat_text.see("end")
        self.chat_text.config(state="disabled")
        
        # Réinitialiser le statut de la réponse AI
        self.ai_response_started = False

    def create_tooltip(self, widget, text):
        """Crée une info-bulle pour un widget"""
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Créer une fenêtre toplevel
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(self.tooltip, text=text, background=self.COLORS["surface"],
                            foreground=self.COLORS["text_primary"], relief="solid", borderwidth=1,
                            font=("Segoe UI", 9) if "Segoe UI" in font.families() else (None, 9),
                            padx=5, pady=2)
            label.pack()
            
        def leave(event):
            if hasattr(self, "tooltip"):
                self.tooltip.destroy()
                
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
        
    def reset_chat(self):
        """Réinitialise le chat et l'historique de conversation"""
        try:
            # Effacer complètement le contenu du chat
            self.chat_text.configure(state="normal")
            self.chat_text.delete("1.0", "end")
            
            # Forcer la mise à jour de l'interface
            self.chat_text.update()
            self.parent.update_idletasks()
            
            # Réinitialiser le statut
            self.chat_text.configure(state="disabled")
            
            # Réinitialiser tous les attributs liés à l'état du chat
            self.ai_response_started = False
            
            # Réinitialiser l'historique du modèle AI si disponible
            if self.ai:
                # Réinitialiser complètement l'historique de conversation
                self.ai.conversation_history = [{"role": "system", "content": self.ai.system_prompt}]
                self.ai.conversation_state = {}
                
                # Afficher un message de confirmation
                self.display_status_message("Conversation réinitialisée", "success")
            else:
                # Si l'AI n'est pas initialisée, essayer de l'initialiser
                self.initialize_ai()
                self.display_status_message("Initialisation du modèle AI", "info")
            
            # Nettoyer toute autre donnée résiduelle
            if hasattr(self, 'response_queue'):
                while not self.response_queue.empty():
                    try:
                        self.response_queue.get_nowait()
                    except:
                        pass
            
            # Recréer complètement le widget de chat si nécessaire
            if self.chat_text.get("1.0", "end-1c") != "":
                # Détruire et recréer le widget de chat
                self.chat_text.destroy()
                
                # Recréer le widget
                try:
                    chat_font = font.Font(family="Segoe UI", size=10)
                except:
                    chat_font = font.Font(size=10)
                
                self.chat_text = scrolledtext.ScrolledText(
                    self.chat_container,
                    wrap="word",
                    height=20,
                    background=self.COLORS["background"],
                    foreground=self.COLORS["text_primary"],
                    borderwidth=1,
                    relief="solid",
                    padx=15,
                    pady=15,
                    font=chat_font
                )
                self.chat_text.pack(fill="both", expand=True)
                
                # Reconfigurer les tags de style
                self.configure_text_tags()
            
            # Afficher à nouveau le message de bienvenue
            self.display_welcome_message()
            
            # Remettre le focus sur la zone de texte
            self.message_entry.focus_set()
            
            # Forcer une dernière mise à jour
            self.frame.update()
            self.parent.update_idletasks()
            
        except Exception as e:
            logging.error(f"Erreur lors de la réinitialisation du chat: {e}", exc_info=True)
            self.display_status_message(f"Erreur lors de la réinitialisation", "error")