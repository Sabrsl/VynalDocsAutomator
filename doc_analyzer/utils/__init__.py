# __init__.py

"""
Utilitaires pour Vynal Docs Automator
"""

from .validators import (
    validate_date, validate_amount, validate_name, validate_entity,
    validate_id_number, validate_email, validate_phone, validate_address,
    validate_siret, validate_vat_number, validate_iban, validate_bic,
    validate_field, validate_document_data, validate_extraction_results,
    validate_coordinates, validate_merge_data, check_data_consistency
)
from .text_processor import TextProcessor

__all__ = [
    'validate_date', 'validate_amount', 'validate_name', 'validate_entity',
    'validate_id_number', 'validate_email', 'validate_phone', 'validate_address',
    'validate_siret', 'validate_vat_number', 'validate_iban', 'validate_bic',
    'validate_field', 'validate_document_data', 'validate_extraction_results',
    'validate_coordinates', 'validate_merge_data', 'check_data_consistency',
    'TextProcessor'
]
