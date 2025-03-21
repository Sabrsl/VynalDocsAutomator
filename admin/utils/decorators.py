from functools import wraps
from admin.utils.admin_permissions import AdminPermissions
from admin.utils.exceptions import PermissionDenied

def admin_required(func):
    """Décorateur pour vérifier si l'utilisateur est administrateur."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.app_model.current_user or AdminPermissions.ADMIN not in self.app_model.current_user.roles:
            raise PermissionDenied("Cette action nécessite des droits d'administrateur.")
        return func(self, *args, **kwargs)
    return wrapper

def manager_required(func):
    """Décorateur pour vérifier si l'utilisateur est manager ou administrateur."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.app_model.current_user or not any(role in [AdminPermissions.ADMIN, AdminPermissions.MANAGER] for role in self.app_model.current_user.roles):
            raise PermissionDenied("Cette action nécessite des droits de manager ou d'administrateur.")
        return func(self, *args, **kwargs)
    return wrapper

def password_reset_required(func):
    """Décorateur pour vérifier si l'utilisateur a les droits de réinitialisation de mot de passe."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.app_model.current_user or not any(role in [AdminPermissions.ADMIN, AdminPermissions.MANAGER] for role in self.app_model.current_user.roles):
            raise PermissionDenied("Cette action nécessite les droits de réinitialisation de mot de passe.")
        return func(self, *args, **kwargs)
    return wrapper 