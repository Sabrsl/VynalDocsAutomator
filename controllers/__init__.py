class AppController:
    def __init__(self, app_model, main_view):
        self.model = app_model
        self.view = main_view
        
        logger.info("Initialisation du contrôleur principal...")
        
        # Importer localement pour éviter les imports circulaires
        from controllers.client_controller import ClientController
        from controllers.document_controller import DocumentController
        from controllers.template_controller import TemplateController
        
        self.client_controller = ClientController(app_model, main_view.views["clients"])
        self.document_controller = DocumentController(app_model, main_view.views["documents"])
        self.template_controller = TemplateController(app_model, main_view.views["templates"])
        
        # Connecter les événements et configurer les handlers
        self.client_controller.connect_events()
        self.document_controller.connect_events()
        self.template_controller.connect_events()
        self.setup_event_handlers()
        
        logger.info("AppController initialisé avec succès")
