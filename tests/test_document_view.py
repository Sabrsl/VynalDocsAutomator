#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests pour la vue de gestion des documents
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
import customtkinter as ctk

from views.document_view import DocumentView, DocumentValidationError, FileSecurityError

class TestDocumentView(unittest.TestCase):
    """Tests pour la classe DocumentView"""
    
    def setUp(self):
        """Préparation des tests"""
        # Créer une fenêtre Tkinter factice
        self.root = ctk.CTk()
        
        # Créer un modèle factice
        self.model = Mock()
        self.model.documents = []
        self.model.clients = []
        self.model.templates = []
        
        # Créer une instance de DocumentView
        self.view = DocumentView(self.root, self.model)
        
        # Créer un répertoire temporaire pour les tests
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Nettoyage après les tests"""
        # Nettoyer le répertoire temporaire
        shutil.rmtree(self.temp_dir)
        
        # Fermer la fenêtre
        self.root.destroy()
    
    def test_sanitize_path(self):
        """Test de la sanitization des chemins de fichiers"""
        # Test avec un chemin valide
        path = os.path.join("documents", "test.pdf")
        sanitized = self.view._sanitize_path(path)
        self.assertEqual(sanitized, path)
        
        # Test avec une tentative de traversée de répertoire
        path = "../../etc/passwd"
        sanitized = self.view._sanitize_path(path)
        self.assertEqual(sanitized, "")
        
        # Test avec des caractères non autorisés
        path = "test<file>.pdf"
        sanitized = self.view._sanitize_path(path)
        self.assertEqual(sanitized, "")
    
    def test_validate_file_type(self):
        """Test de la validation des types de fichiers"""
        # Créer un fichier PDF valide
        pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n%EOF")
        
        # Test avec un fichier PDF valide
        self.assertTrue(self.view._is_valid_file_type(pdf_path))
        
        # Test avec un fichier invalide
        invalid_path = os.path.join(self.temp_dir, "test.exe")
        with open(invalid_path, "wb") as f:
            f.write(b"invalid content")
        
        self.assertFalse(self.view._is_valid_file_type(invalid_path))
        
        # Test avec un fichier vide
        empty_path = os.path.join(self.temp_dir, "empty.txt")
        with open(empty_path, "wb") as f:
            f.write(b"")
        
        self.assertFalse(self.view._is_valid_file_type(empty_path))
    
    def test_file_type_cache(self):
        """Test du cache des types de fichiers"""
        # Créer un fichier de test
        test_path = os.path.join(self.temp_dir, "test.pdf")
        with open(test_path, "wb") as f:
            f.write(b"%PDF-1.4\n%EOF")
        
        # Premier appel (pas dans le cache)
        self.assertTrue(self.view._is_valid_file_type(test_path))
        
        # Deuxième appel (devrait être dans le cache)
        self.assertTrue(test_path in self.view._file_type_cache)
        
        # Vérifier que le cache est utilisé
        with patch.object(self.view, '_is_valid_file_type') as mock_validate:
            self.view._is_valid_file_type(test_path)
            mock_validate.assert_not_called()
    
    def test_file_size_validation(self):
        """Test de la validation de la taille des fichiers"""
        # Créer un fichier de test
        test_path = os.path.join(self.temp_dir, "test.txt")
        
        # Test avec un fichier valide
        with open(test_path, "wb") as f:
            f.write(b"test content")
        
        self.assertTrue(self.view._is_valid_file_type(test_path))
        
        # Test avec un fichier trop volumineux
        large_path = os.path.join(self.temp_dir, "large.txt")
        with open(large_path, "wb") as f:
            f.write(b"0" * (self.view.MAX_FILE_SIZE + 1))
        
        self.assertFalse(self.view._is_valid_file_type(large_path))

if __name__ == '__main__':
    unittest.main() 