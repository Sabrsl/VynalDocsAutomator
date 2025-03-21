#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests unitaires pour l'interface d'administration
"""

import unittest
import customtkinter as ctk
import os
import shutil
from datetime import datetime, timedelta
from admin.views.system_logs_view import SystemLogsView

class MockModel:
    """Modèle fictif pour les tests"""
    def __init__(self, test_dir):
        self.test_dir = test_dir
        self.logs_dir = os.path.join(test_dir, "logs")
        self.admin_dir = os.path.join(test_dir, "admin")
        
    def get_logs_dir(self):
        return self.logs_dir
        
    def get_admin_dir(self):
        return self.admin_dir

class TestSystemLogsView(unittest.TestCase):
    """Tests pour la vue des journaux système"""

    @classmethod
    def setUpClass(cls):
        """Configuration initiale pour tous les tests"""
        cls.test_dir = os.path.join(os.path.dirname(__file__), "test_data")
        cls.logs_dir = os.path.join(cls.test_dir, "logs")
        cls.admin_dir = os.path.join(cls.test_dir, "admin")
        
        # Create test directories
        os.makedirs(cls.logs_dir, exist_ok=True)
        os.makedirs(cls.admin_dir, exist_ok=True)

    def setUp(self):
        """Configuration avant chaque test"""
        self.root = ctk.CTk()
        self.model = MockModel(self.test_dir)
        self.view = SystemLogsView(self.root, self.model)
        
        # Create a test log file
        self.test_log_path = os.path.join(self.logs_dir, "test.log")
        with open(self.test_log_path, "w", encoding="utf-8") as f:
            f.write("2024-03-20 10:00:00 INFO Test message 1\n")
            f.write("2024-03-20 10:01:00 ERROR Test error message\n")
            f.write("2024-03-20 10:02:00 INFO Test message 2\n")
        
        # S'assurer que le fichier est bien créé
        self.assertTrue(os.path.exists(self.test_log_path))

    def test_init(self):
        """Test initialization of the view"""
        self.assertIsNotNone(self.view)
        self.assertEqual(self.view.current_log_file, "")
        self.assertEqual(self.view.filter_vars["level"].get(), "ALL")

    def test_load_log_file(self):
        """Test loading a log file"""
        # Set the current log file
        self.view.current_log_file = self.test_log_path
        
        # Load the test log file
        self.view.load_log_file(self.test_log_path)
        self.root.update()  # Process Tkinter events
        
        # Get text content
        self.view.logs_text.configure(state="normal")
        content = self.view.logs_text.get("1.0", "end-1c")
        self.view.logs_text.configure(state="disabled")
        
        # Verify content
        self.assertIn("Test message 1", content)
        self.assertIn("Test error message", content)
        self.assertIn("Test message 2", content)

    def test_filter_log_lines(self):
        """Test log filtering"""
        # Set the current log file
        self.view.current_log_file = self.test_log_path
        
        # Load the test log file
        self.view.load_log_file(self.test_log_path)
        self.root.update()
        
        # Test level filter
        self.view.filter_vars["level"].set("ERROR")
        self.view.apply_filters()
        self.root.update()
        
        # Get text content
        self.view.logs_text.configure(state="normal")
        content = self.view.logs_text.get("1.0", "end-1c")
        self.view.logs_text.configure(state="disabled")
        
        # Verify content
        self.assertIn("Test error message", content)
        self.assertNotIn("Test message 1", content)
        self.assertNotIn("Test message 2", content)

    def test_export_logs(self):
        """Test log export"""
        # Set the current log file
        self.view.current_log_file = self.test_log_path
        
        # Load the test log file
        self.view.load_log_file(self.test_log_path)
        self.root.update()
        
        # Export logs
        export_path = os.path.join(self.logs_dir, "exports", "test_export.log")
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        
        self.view.export_logs(export_path)
        self.root.update()
        
        # Verify export
        self.assertTrue(os.path.exists(export_path))
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Test message 1", content)
            self.assertIn("Test error message", content)
            self.assertIn("Test message 2", content)

    def test_add_security_alert(self):
        """Test adding security alerts"""
        initial_count = len(self.view.security_alerts)
        self.view.add_security_alert("Test alert", "INFO")
        self.root.update()
        
        self.assertEqual(len(self.view.security_alerts), initial_count + 1)
        self.assertIn("Test alert", str(self.view.security_alerts[-1]))

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)
        
        # Nettoyer les exports
        export_dir = os.path.join(self.logs_dir, "exports")
        if os.path.exists(export_dir):
            shutil.rmtree(export_dir)
        
        self.root.destroy()

    @classmethod
    def tearDownClass(cls):
        """Nettoyage final après tous les tests"""
        # Supprimer les répertoires de test
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

if __name__ == '__main__':
    unittest.main()