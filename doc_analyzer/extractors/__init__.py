"""
Module d'extracteurs de documents pour Vynal Docs Automator
"""

from .identity_docs import IdentityDocExtractor
from .business_docs import BusinessDocExtractor
from .personal_data import PersonalDataExtractor
from .legal_docs import LegalDocsExtractor
from .contracts import ContractExtractor

__all__ = [
    'IdentityDocExtractor',
    'BusinessDocExtractor',
    'PersonalDataExtractor',
    'LegalDocsExtractor',
    'ContractExtractor'
]
