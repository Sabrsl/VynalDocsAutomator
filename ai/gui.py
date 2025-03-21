import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
from model import AIModel
import logging
import sys

logger = logging.getLogger('AI.GUI')

# Instance globale de l'IA
ai_instance = None

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Assistant IA - Chat")
        self.root.geometry("800x600")
        
        # Configuration du style
        self.style = ttk.Style()
        self.style.configure("Custom.TFrame", background="#f0f0f0")
        self.style.configure("Custom.TButton", padding=5)
        
        # Création du conteneur principal
        self.main_frame = ttk.Frame(root, style="Custom.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Zone d'affichage des messages
        self.chat_frame = ttk.Frame(self.main_frame)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            bg="white",
            fg="#333333"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_display.config(state=tk.DISABLED)
        
        # Zone de saisie
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.input_entry = ttk.Entry(
            self.input_frame,
            font=("Segoe UI", 11)
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_entry.bind("<Return>", self.send_message)
        
        # Bouton d'envoi
        self.send_button = ttk.Button(
            self.input_frame,
            text="Envoyer",
            command=self.send_message,
            style="Custom.TButton"
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Configuration des tags pour les couleurs
        self.chat_display.tag_config("user", foreground="#007AFF")
        self.chat_display.tag_config("assistant", foreground="#34C759")
        self.chat_display.tag_config("error", foreground="#FF3B30")
        
        try:
            # Utiliser l'instance globale de l'IA
            global ai_instance
            if ai_instance is None:
                ai_instance = AIModel()
            self.ai = ai_instance
            
            # Message de bienvenue
            self.display_message("Assistant IA : Bonjour ! Je suis votre assistant IA. Comment puis-je vous aider ?\n", "assistant")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de l'IA : {e}")
            messagebox.showerror("Erreur", "Impossible d'initialiser l'IA. Veuillez vérifier que Ollama est en cours d'exécution.")
            self.root.destroy()
            sys.exit(1)
        
    def send_message(self, event=None):
        """
        Gère l'envoi du message utilisateur et démarre le thread pour obtenir une réponse.
        """
        message = self.input_entry.get().strip()
        if not message:
            return
            
        # Désactiver l'interface pendant le traitement
        self.input_entry.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        
        # Afficher le message de l'utilisateur
        self.display_message(f"Vous : {message}\n", "user")
        self.input_entry.delete(0, tk.END)
        
        # Démarrer le traitement dans un thread séparé
        threading.Thread(target=self.get_response, args=(message,), daemon=True).start()
        
    def get_response(self, message):
        """
        Obtient et affiche la réponse de l'IA en temps réel.
        """
        try:
            self.display_message("Assistant IA : ", "assistant")
            
            # Obtenir la réponse de l'IA
            response = self.ai.generate_response(message)
            
            # Afficher la réponse en temps réel
            if hasattr(response, '__iter__') and not isinstance(response, str):
                for chunk in response:
                    if chunk is not None:
                        self.display_message(chunk, "assistant")
            else:
                self.display_message(str(response), "assistant")
                
            self.display_message("\n", "assistant")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de la réponse : {e}")
            self.display_message("Une erreur s'est produite. Veuillez réessayer.\n", "error")
            
        finally:
            # Réactiver l'interface
            self.root.after(0, self.enable_input)
            
    def enable_input(self):
        """
        Réactive l'interface utilisateur.
        """
        self.input_entry.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)
        self.input_entry.focus()
        
    def display_message(self, message, tag=None):
        """
        Affiche un message dans la zone de chat.
        """
        self.chat_display.config(state=tk.NORMAL)
        if tag:
            self.chat_display.insert(tk.END, message, tag)
        else:
            self.chat_display.insert(tk.END, message)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

def main():
    try:
        root = tk.Tk()
        app = ChatApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de l'interface : {e}")
        messagebox.showerror("Erreur", "Impossible de démarrer l'interface graphique.")
        sys.exit(1)

if __name__ == "__main__":
    main() 