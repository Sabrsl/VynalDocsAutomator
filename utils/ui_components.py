import customtkinter as ctk
import math
import logging

class LoadingSpinner(ctk.CTkFrame):
    """Composant d'indicateur de chargement animé"""
    
    def __init__(self, parent, size: int = 20, thickness: int = 2, speed: float = 0.15, **kwargs):
        """
        Initialise le spinner
        
        Args:
            parent: Widget parent
            size: Taille du spinner en pixels
            thickness: Épaisseur du trait en pixels
            speed: Vitesse de rotation (plus petit = plus rapide)
            **kwargs: Arguments supplémentaires pour le frame
        """
        super().__init__(parent, width=size, height=size, **kwargs)
        
        self.size = size
        self.thickness = thickness
        self.speed = speed
        
        # Angle de rotation actuel
        self.angle = 0
        
        # ID de l'animation
        self.after_id = None
        
        # Créer le canvas
        fg_color = self.cget("fg_color")
        if isinstance(fg_color, tuple):
            # Si c'est un tuple (mode clair/sombre), prendre la couleur appropriée
            bg_color = fg_color[1] if self._get_appearance_mode() == "dark" else fg_color[0]
        elif isinstance(fg_color, str):
            # Si c'est une chaîne, la diviser et prendre la couleur appropriée
            colors = fg_color.split()
            bg_color = colors[1] if self._get_appearance_mode() == "dark" else colors[0]
        else:
            # Fallback sur une couleur par défaut
            bg_color = "#2B2B2B" if self._get_appearance_mode() == "dark" else "#E5E5E5"
        
        self.canvas = ctk.CTkCanvas(
            self,
            width=size,
            height=size,
            bg=bg_color,
            highlightthickness=0
        )
        self.canvas.pack(expand=True)
        
        # Masquer par défaut
        self.pack_forget()
    
    def show(self):
        """Affiche et démarre l'animation du spinner"""
        self.pack()
        self._start_animation()
    
    def hide(self):
        """Cache et arrête l'animation du spinner"""
        self._stop_animation()
        self.pack_forget()
    
    def _start_animation(self):
        """Démarre l'animation du spinner"""
        if self.after_id is None:
            self._animate()
    
    def _stop_animation(self):
        """Arrête l'animation du spinner"""
        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None
    
    def _animate(self):
        """Anime le spinner"""
        # Effacer le canvas
        self.canvas.delete("spinner")
        
        # Calculer les coordonnées de l'arc
        center = self.size / 2
        radius = (self.size - self.thickness) / 2
        
        # Dessiner l'arc
        start = self.angle
        extent = 270  # L'arc couvre 270 degrés
        
        self.canvas.create_arc(
            self.thickness,
            self.thickness,
            self.size - self.thickness,
            self.size - self.thickness,
            start=start,
            extent=extent,
            outline="#3498db",
            width=self.thickness,
            style="arc",
            tags="spinner"
        )
        
        # Mettre à jour l'angle
        self.angle = (self.angle + 5) % 360
        
        # Planifier la prochaine frame
        self.after_id = self.after(int(self.speed * 1000), self._animate)
    
    def destroy(self):
        """Nettoie et détruit le spinner"""
        self._stop_animation()
        super().destroy()
        
    def _get_appearance_mode(self) -> str:
        """
        Obtient le mode d'apparence actuel (clair/sombre)
        
        Returns:
            str: "light" ou "dark"
        """
        try:
            return ctk.get_appearance_mode().lower()
        except:
            return "dark"  # Mode sombre par défaut en cas d'erreur 

class ThemeManager:
    """Gestionnaire de thème pour l'application"""
    
    _current_theme = "dark"  # Thème par défaut
    _theme_listeners = []
    
    @classmethod
    def set_theme(cls, theme: str):
        """
        Définit le thème actuel de l'application
        
        Args:
            theme (str): Le thème à utiliser ('light' ou 'dark')
        """
        if theme.lower() not in ['light', 'dark']:
            raise ValueError("Le thème doit être 'light' ou 'dark'")
        
        cls._current_theme = theme.lower()
        
        # Notifier les listeners du changement de thème
        for listener in cls._theme_listeners:
            try:
                listener(cls._current_theme)
            except Exception as e:
                logging.getLogger("VynalDocsAutomator").error(f"Erreur lors de la notification du changement de thème: {e}")
    
    @classmethod
    def get_theme(cls) -> str:
        """
        Retourne le thème actuel
        
        Returns:
            str: Le thème actuel ('light' ou 'dark')
        """
        return cls._current_theme
    
    @classmethod
    def add_theme_listener(cls, listener):
        """
        Ajoute un listener pour les changements de thème
        
        Args:
            listener: Fonction à appeler lors du changement de thème
        """
        if listener not in cls._theme_listeners:
            cls._theme_listeners.append(listener)
    
    @classmethod
    def remove_theme_listener(cls, listener):
        """
        Supprime un listener
        
        Args:
            listener: Fonction à supprimer des listeners
        """
        if listener in cls._theme_listeners:
            cls._theme_listeners.remove(listener)
    
    @classmethod
    def get_colors(cls, theme=None):
        """
        Retourne les couleurs pour le thème spécifié ou le thème actuel
        
        Args:
            theme (str, optional): Le thème pour lequel obtenir les couleurs
        
        Returns:
            dict: Dictionnaire des couleurs pour le thème
        """
        theme = theme or cls._current_theme
        
        if theme == "dark":
            return {
                "primary": "#2D7AF6",
                "success": "#28a745",
                "warning": "#ffc107",
                "danger": "#dc3545",
                "info": "#17a2b8",
                "background": "#1E1E1E",
                "surface": "#2D2D2D",
                "text": "#FFFFFF",
                "text_secondary": "#B3B3B3"
            }
        else:
            return {
                "primary": "#3B8ED0",
                "success": "#34c759",
                "warning": "#ffcc00",
                "danger": "#ff3b30",
                "info": "#5ac8fa",
                "background": "#F5F5F5",
                "surface": "#FFFFFF",
                "text": "#000000",
                "text_secondary": "#666666"
            } 