#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Package des vues pour l'application Vynal Docs Automator
"""

from views.main_view import MainView
from views.dashboard_view import DashboardView
from views.client_view import ClientView
from views.document_view import DocumentView
from views.template_view import TemplateView
from views.settings_view import SettingsView

__all__ = [
    'MainView',
    'DashboardView',
    'ClientView',
    'DocumentView',
    'TemplateView',
    'SettingsView'
]