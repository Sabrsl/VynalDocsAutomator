# __init__.py

"""
Reconnaissance de données dans les documents
"""

from .name_recognizer import NameRecognizer
from .phone_recognizer import PhoneRecognizer
from .address_recognizer import AddressRecognizer
from .id_recognizer import IDRecognizer

__all__ = [
    'NameRecognizer',
    'PhoneRecognizer',
    'AddressRecognizer',
    'IDRecognizer'
]
