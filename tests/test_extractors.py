#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests des extracteurs de documents
"""

import unittest
import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from doc_analyzer.extractors import IdentityDocExtractor, BusinessDocExtractor
from pprint import pprint

class TestExtractors(unittest.TestCase):
    def setUp(self):
        self.identity_extractor = IdentityDocExtractor()
        self.business_extractor = BusinessDocExtractor()

    def test_identity_doc_fr(self):
        """Test d'extraction d'une CNI française"""
        text = """
        RÉPUBLIQUE FRANÇAISE
        CARTE NATIONALE D'IDENTITÉ
        N° CNI: 123456789012
        """
        result = self.identity_extractor.extract(text)
        print("\nRésultat CNI française:")
        pprint(result)
        
        # Vérification du type et pays
        self.assertEqual(result["document_type"], "cni")
        self.assertEqual(result["country"], "fr")
        self.assertEqual(result["document_number"], "123456789012")

    def test_identity_doc_ma(self):
        """Test d'extraction d'une CIN marocaine"""
        text = """
        المملكة المغربية
        ROYAUME DU MAROC
        CARTE D'IDENTITÉ NATIONALE
        CIN: AB123456
        """
        result = self.identity_extractor.extract(text)
        print("\nRésultat CIN marocaine:")
        pprint(result)
        
        # Vérification du type et pays
        self.assertEqual(result["document_type"], "cni")
        self.assertEqual(result["country"], "ma")
        self.assertEqual(result["document_number"], "AB123456")

    def test_business_doc_fr(self):
        """Test d'extraction d'une facture française"""
        text = """
        FACTURE N° F2024-001
        SIRET: 123 456 789 00012
        """
        result = self.business_extractor.extract(text)
        print("\nRésultat facture française:")
        pprint(result)
        
        # Vérification du type
        self.assertEqual(result["business_type"], "facture")
        self.assertEqual(result.get("sender", {}).get("siret"), "12345678900012")

    def test_business_doc_ma(self):
        """Test d'extraction d'une facture marocaine"""
        text = """
        FACTURE N° 2024/123
        ICE: 123456789000012
        """
        result = self.business_extractor.extract(text)
        print("\nRésultat facture marocaine:")
        pprint(result)
        
        # Vérification du type
        self.assertEqual(result["business_type"], "facture")
        self.assertEqual(result.get("sender", {}).get("ice"), "123456789000012")

if __name__ == '__main__':
    unittest.main() 