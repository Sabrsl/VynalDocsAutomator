def _setup_application(self):
    """Configure l'application et initialise les composants"""
    # Configurer le thème
    self._setup_theme()
    
    # Optimiser les performances
    from utils.performance_optimizer import PerformanceOptimizer
    PerformanceOptimizer.optimize_application(self.root)
    
    # Initialiser le modèle de données
    self.model = AppModel()
    
    # Initialiser le contrôleur
    self.controller = AppController(self.model, self) 