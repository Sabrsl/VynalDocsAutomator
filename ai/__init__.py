from .model import AIModel

# Désactivation de tous les patches pour utiliser seulement Llama
# from .dashboard_integration import add_ai_tab
# from .model_patch import patch_ai_model
# from .exception_handler import patch_with_exception_handling
# from .universal_responder import UniversalResponder

# Commenté pour désactiver les patches
# universal_responder = UniversalResponder()

# Désactivation de tous les patches
# AIModel = patch_with_exception_handling(AIModel)
# AIModel = universal_responder.apply_to_ai_model(AIModel)
# AIModel = patch_ai_model(AIModel)

# Logs de débogage
print("DEBUG - Tous les patches ont été désactivés - utilisation du modèle Llama3 pour chatAI direct")
print("DEBUG - Le chat utilisera maintenant uniquement Llama avec un prompt d'expert juridique")

__all__ = ['AIModel'] 