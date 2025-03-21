#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from utils.lazy_loader import ModelType, ModelMetadata

@dataclass
class Document:
    """Modèle de document analysé avec chargement différé"""
    
    # Métadonnées du document
    file_path: str
    document_type: Optional[str] = None
    creation_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    
    # Données extraites (chargement différé)
    _extracted_data: Optional[Dict[str, Any]] = None
    _confidence_scores: Optional[Dict[str, float]] = None
    
    # Statut de l'analyse
    is_analyzed: bool = False
    analysis_date: Optional[datetime] = None
    analysis_duration: Optional[float] = None
    
    # Validation
    is_valid: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    @property
    def extracted_data(self) -> Dict[str, Any]:
        """Charge les données extraites à la demande"""
        if self._extracted_data is None:
            self._extracted_data = {}
        return self._extracted_data
        
    @property
    def confidence_scores(self) -> Dict[str, float]:
        """Charge les scores de confiance à la demande"""
        if self._confidence_scores is None:
            self._confidence_scores = {}
        return self._confidence_scores
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le document en dictionnaire"""
        return {
            'file_path': self.file_path,
            'document_type': self.document_type,
            'creation_date': self.creation_date.isoformat(),
            'last_modified': self.last_modified.isoformat(),
            'extracted_data': self.extracted_data,
            'confidence_scores': self.confidence_scores,
            'is_analyzed': self.is_analyzed,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'analysis_duration': self.analysis_duration,
            'is_valid': self.is_valid,
            'validation_errors': self.validation_errors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Crée un document à partir d'un dictionnaire"""
        return cls(
            file_path=data['file_path'],
            document_type=data.get('document_type'),
            creation_date=datetime.fromisoformat(data['creation_date']),
            last_modified=datetime.fromisoformat(data['last_modified']),
            _extracted_data=data.get('extracted_data'),
            _confidence_scores=data.get('confidence_scores'),
            is_analyzed=data.get('is_analyzed', False),
            analysis_date=datetime.fromisoformat(data['analysis_date']) if data.get('analysis_date') else None,
            analysis_duration=data.get('analysis_duration'),
            is_valid=data.get('is_valid', False),
            validation_errors=data.get('validation_errors', [])
        )
    
    def update_extracted_data(self, data: Dict[str, Any], confidence_scores: Optional[Dict[str, float]] = None):
        """Met à jour les données extraites et les scores de confiance"""
        if self._extracted_data is None:
            self._extracted_data = {}
        self._extracted_data.update(data)
        
        if confidence_scores:
            if self._confidence_scores is None:
                self._confidence_scores = {}
            self._confidence_scores.update(confidence_scores)
            
        self.last_modified = datetime.now()
    
    def validate(self) -> bool:
        """Valide les données extraites"""
        self.validation_errors = []
        
        # Vérification des champs requis selon le type de document
        if self.document_type == 'business':
            required_fields = ['client_name', 'amount', 'date']
        elif self.document_type == 'identity':
            required_fields = ['full_name', 'birth_date', 'id_number']
        elif self.document_type == 'legal':
            required_fields = ['title', 'parties', 'date']
        else:
            required_fields = []
        
        # Vérification de la présence des champs requis
        for field in required_fields:
            if field not in self.extracted_data:
                self.validation_errors.append(f"Champ requis manquant: {field}")
        
        # Vérification des scores de confiance
        for field, score in self.confidence_scores.items():
            if score < 0.6:  # Seuil de confiance minimal
                self.validation_errors.append(f"Score de confiance trop faible pour {field}: {score}")
        
        self.is_valid = len(self.validation_errors) == 0
        return self.is_valid
    
    def __str__(self) -> str:
        """Représentation textuelle du document"""
        status = "Analysé" if self.is_analyzed else "Non analysé"
        validation = "Valide" if self.is_valid else "Non valide"
        return f"Document({self.file_path}, type={self.document_type}, status={status}, validation={validation})" 