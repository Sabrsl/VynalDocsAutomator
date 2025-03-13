#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'administration pour l'application Vynal Docs Automator
Permet la gestion des utilisateurs, paramètres système et surveillance
"""

__version__ = '1.0.0'

# Importations du module principal
from admin.admin_main import AdminMain

# Importations des modèles
from admin.models.admin_model import AdminModel

# Importations des contrôleurs
from admin.controllers.admin_controller import AdminController
from admin.controllers.user_management_controller import UserManagementController

# Importations des vues
from admin.views.admin_dashboard_view import AdminDashboardView
from admin.views.user_management_view import UserManagementView
from admin.views.permissions_view import PermissionsView
from admin.views.system_logs_view import SystemLogsView
from admin.views.settings_view import AdminSettingsView

# Importations des utilitaires
from admin.utils.admin_permissions import AdminPermissions, PermissionDenied, admin_required, manager_required

# Fonction pratique pour démarrer l'interface d'administration
def start_admin(parent, app_model):
    """
    Démarre l'interface d'administration
    
    Args:
        parent: Widget parent (peut être None pour une fenêtre séparée)
        app_model: Modèle de l'application principale
        
    Returns:
        AdminMain: Instance de l'interface d'administration
    """
    admin = AdminMain(parent, app_model)
    admin.show()
    return admin

# Exposer les classes et fonctions principales
__all__ = [
    'AdminMain', 
    'AdminModel',
    'AdminController', 
    'UserManagementController',
    'AdminDashboardView', 
    'UserManagementView', 
    'PermissionsView', 
    'SystemLogsView', 
    'AdminSettingsView',
    'AdminPermissions', 
    'PermissionDenied', 
    'admin_required', 
    'manager_required',
    'start_admin'
]