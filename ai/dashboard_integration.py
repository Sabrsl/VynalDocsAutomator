import tkinter as tk
from tkinter import ttk
import logging
from .chat_interface import AIChatInterface

# Variable globale pour suivre l'état de l'onglet IA
_ai_tab_added = False

def add_ai_tab(dashboard):
    """
    Ajoute un onglet IA au tableau de bord existant.
    
    Args:
        dashboard: L'instance du tableau de bord principal
    """
    global _ai_tab_added
    logger = logging.getLogger('AI.DashboardIntegration')
    
    try:
        # Vérifier si l'onglet existe déjà
        if _ai_tab_added or "Assistant IA" in dashboard.notebook._name_list:
            logger.info("Onglet Assistant IA déjà présent")
            return None
            
        # Créer l'onglet IA
        ai_tab = dashboard.notebook.add("Assistant IA")
        logger.info("Onglet Assistant IA créé")
        
        # Créer un cadre pour l'interface de chat (utiliser tk.Frame au lieu de ttk.Frame)
        chat_frame = tk.Frame(ai_tab, bg="#1A202C")  # Utiliser la même couleur de fond
        chat_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Créer et ajouter l'interface de chat
        chat_interface = AIChatInterface(chat_frame)
        chat_interface.frame.pack(fill="both", expand=True)
        logger.info("Interface de chat créée")
        
        # Forcer la mise à jour de l'interface
        chat_frame.update()
        ai_tab.update()
        dashboard.notebook.update()
        logger.info("Interface mise à jour")
        
        # Marquer l'onglet comme ajouté
        _ai_tab_added = True
        
        return chat_interface
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de l'onglet IA: {e}")
        return None 