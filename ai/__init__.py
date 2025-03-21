from .model import AIModel
from .dashboard_integration import add_ai_tab
from .model_patch import patch_ai_model
from .exception_handler import patch_with_exception_handling
from .universal_responder import UniversalResponder

# Créer un répondeur universel
universal_responder = UniversalResponder()

# Appliquer les patches au modèle d'IA dans l'ordre optimal:
# 1. D'abord le gestionnaire d'exceptions pour attraper les erreurs
AIModel = patch_with_exception_handling(AIModel)
# 2. Ensuite le répondeur universel pour l'interception des commandes générales
AIModel = universal_responder.apply_to_ai_model(AIModel)
# 3. Enfin, le patch principal qui implémente les fonctionnalités de documents (doit être appliqué en dernier)
AIModel = patch_ai_model(AIModel)

# Logs de débogage pour vérifier l'application des patches
print("DEBUG - Tous les patches ont été appliqués à AIModel")
print(f"DEBUG - Ordre des patches: 1) exception_handler, 2) universal_responder, 3) model_patch")

__all__ = ['AIModel', 'add_ai_tab'] 