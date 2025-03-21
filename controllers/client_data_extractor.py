import re
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import os
from pathlib import Path

logger = logging.getLogger("VynalDocsAutomator.ClientDataExtractor")

class ClientDataExtractor:
    """
    Extracteur de données client automatique.
    Analyse les documents pour en extraire les informations client pertinentes.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise l'extracteur de données client.
        
        Args:
            config_path: Chemin vers le fichier de configuration (optionnel)
        """
        self.patterns = self._load_patterns(config_path)
        self.confidence_threshold = 0.8
        self.cache = {}
        self.stats = {
            'processed_docs': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'avg_confidence': 0.0,
            'last_extraction_time': None
        }
        
        # Initialiser les extracteurs spécialisés
        self._initialize_extractors()
        
        logger.info("ClientDataExtractor initialisé")
    
    def _load_patterns(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Charge les patterns d'extraction depuis la configuration"""
        default_patterns = {
            'name': {
                'patterns': [
                    r'M(?:me|lle|\.)\s+([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)*)',
                    r'Nom\s*:\s*([A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)*)',
                ],
                'priority': 1
            },
            'email': {
                'patterns': [
                    r'[\w\.-]+@[\w\.-]+\.\w+',
                    r'[Ee]mail\s*:\s*([\w\.-]+@[\w\.-]+\.\w+)'
                ],
                'priority': 2
            },
            'phone': {
                'patterns': [
                    r'(?:0|\+33|0033)[1-9](?:[\s.-]*\d{2}){4}',
                    r'[Tt]él(?:éphone)?\s*:\s*((?:0|\+33|0033)[1-9](?:[\s.-]*\d{2}){4})'
                ],
                'priority': 2
            },
            'address': {
                'patterns': [
                    r'\d{1,4}(?:,?\s+[-a-zÀ-ÿ]+)+\s+\d{5}\s+[a-zÀ-ÿ\s]+',
                    r'[Aa]dresse\s*:\s*(\d{1,4}(?:,?\s+[-a-zÀ-ÿ]+)+\s+\d{5}\s+[a-zÀ-ÿ\s]+)'
                ],
                'priority': 3
            },
            'company': {
                'patterns': [
                    r'(?:SARL|SA|SAS|EURL|SASU)\s+([A-Z][A-Za-zÀ-ÿ\s]+)',
                    r'[Ss]ociété\s*:\s*([A-Z][A-Za-zÀ-ÿ\s]+)'
                ],
                'priority': 2
            },
            'siret': {
                'patterns': [
                    r'(?:SIRET|siret)\s*:?\s*(\d{14})',
                    r'\b\d{14}\b'
                ],
                'priority': 3
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    custom_patterns = json.load(f)
                    # Fusion intelligente des patterns
                    for key, value in custom_patterns.items():
                        if key in default_patterns:
                            default_patterns[key]['patterns'].extend(value.get('patterns', []))
                            if 'priority' in value:
                                default_patterns[key]['priority'] = value['priority']
                        else:
                            default_patterns[key] = value
            except Exception as e:
                logger.error(f"Erreur lors du chargement des patterns: {e}")
        
        return default_patterns
    
    def _initialize_extractors(self):
        """Initialise les extracteurs spécialisés"""
        try:
            # Import conditionnel des dépendances optionnelles
            import spacy
            self.nlp = spacy.load("fr_core_news_sm")
            self.has_spacy = True
        except ImportError:
            logger.warning("Spacy non disponible, utilisation des patterns regex uniquement")
            self.has_spacy = False
    
    def extract_client_data(self, document_text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extrait les données client d'un document.
        
        Args:
            document_text: Texte du document
            context: Contexte supplémentaire (optionnel)
            
        Returns:
            Dict[str, Any]: Données client extraites avec scores de confiance
        """
        start_time = datetime.now()
        success = False
        
        try:
            # Vérifier le cache
            cache_key = hash(document_text[:1000])  # Utiliser le début du document comme clé
            if cache_key in self.cache:
                logger.debug("Utilisation du cache pour l'extraction")
                return self.cache[cache_key]
            
            # Initialiser le résultat
            result = {
                'extracted_data': {},
                'confidence_scores': {},
                'metadata': {
                    'extraction_time': None,
                    'method_used': [],
                    'context_used': bool(context)
                }
            }
            
            # 1. Extraction par patterns regex
            pattern_extractions = self._extract_by_patterns(document_text)
            result['extracted_data'].update(pattern_extractions)
            
            # 2. Extraction par NLP si disponible
            if self.has_spacy:
                nlp_extractions = self._extract_by_nlp(document_text)
                self._merge_extractions(result['extracted_data'], nlp_extractions)
                result['metadata']['method_used'].append('nlp')
            
            # 3. Utiliser le contexte si fourni
            if context:
                self._enrich_with_context(result['extracted_data'], context)
                result['metadata']['method_used'].append('context')
            
            # 4. Calculer les scores de confiance
            result['confidence_scores'] = self._calculate_confidence_scores(
                result['extracted_data'],
                pattern_extractions
            )
            
            # 5. Valider et nettoyer les données
            result['extracted_data'] = self._validate_and_clean_data(result['extracted_data'])
            
            # Mettre à jour les statistiques
            processing_time = (datetime.now() - start_time).total_seconds()
            result['metadata']['extraction_time'] = processing_time
            
            # Mettre en cache
            self.cache[cache_key] = result
            
            # Marquer comme succès si des données ont été trouvées
            success = bool(result['extracted_data'])
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des données: {e}")
            success = False
            return {
                'extracted_data': {},
                'confidence_scores': {},
                'metadata': {
                    'error': str(e),
                    'extraction_time': (datetime.now() - start_time).total_seconds()
                }
            }
        finally:
            # Mettre à jour les statistiques
            self._update_stats(success, start_time)
    
    def _extract_by_patterns(self, text: str) -> Dict[str, str]:
        """Extrait les données en utilisant les patterns regex"""
        results = {}
        
        for field, config in self.patterns.items():
            for pattern in config['patterns']:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Prendre le groupe capturé ou le match complet
                    value = match.group(1) if match.groups() else match.group(0)
                    if value:
                        results[field] = value.strip()
                        break  # Prendre la première correspondance valide
        
        return results
    
    def _extract_by_nlp(self, text: str) -> Dict[str, str]:
        """Extrait les données en utilisant le traitement NLP"""
        if not self.has_spacy:
            return {}
        
        results = {}
        doc = self.nlp(text)
        
        # Extraction des entités nommées
        for ent in doc.ents:
            if ent.label_ == 'PER' and 'name' not in results:
                results['name'] = ent.text
            elif ent.label_ == 'ORG' and 'company' not in results:
                results['company'] = ent.text
            elif ent.label_ == 'LOC' and 'address' not in results:
                results['address'] = ent.text
        
        return results
    
    def _merge_extractions(self, base: Dict[str, str], new: Dict[str, str]) -> None:
        """Fusionne les extractions en privilégiant les données existantes"""
        for key, value in new.items():
            if key not in base or not base[key]:
                base[key] = value
    
    def _enrich_with_context(self, data: Dict[str, str], context: Dict[str, Any]) -> None:
        """Enrichit les données extraites avec le contexte"""
        for key, value in context.items():
            if key not in data or not data[key]:
                data[key] = value
    
    def _calculate_confidence_scores(
        self, 
        extracted_data: Dict[str, str],
        pattern_matches: Dict[str, str]
    ) -> Dict[str, float]:
        """Calcule les scores de confiance pour chaque champ"""
        scores = {}
        
        for field, value in extracted_data.items():
            if not value:
                scores[field] = 0.0
                continue
            
            base_score = 0.5
            
            # Augmenter le score si trouvé par pattern
            if field in pattern_matches and pattern_matches[field] == value:
                base_score += 0.3
            
            # Ajuster selon la priorité du champ
            if field in self.patterns:
                priority = self.patterns[field].get('priority', 2)
                base_score *= (1 + (3 - priority) * 0.1)
            
            # Vérifications spécifiques par type
            if field == 'email' and '@' in value:
                base_score += 0.2
            elif field == 'phone' and re.match(r'^\+?[0-9\s.-]{10,}$', value):
                base_score += 0.2
            elif field == 'siret' and len(re.findall(r'\d', value)) == 14:
                base_score += 0.2
            
            scores[field] = min(1.0, base_score)
        
        return scores
    
    def _validate_and_clean_data(self, data: Dict[str, str]) -> Dict[str, str]:
        """Valide et nettoie les données extraites"""
        cleaned = {}
        
        for field, value in data.items():
            if not value:
                continue
                
            # Nettoyage de base
            value = value.strip()
            
            # Validations et nettoyages spécifiques
            if field == 'email':
                if '@' in value and '.' in value.split('@')[1]:
                    cleaned[field] = value.lower()
            
            elif field == 'phone':
                # Normaliser le format du téléphone
                phone = re.sub(r'[^\d+]', '', value)
                if len(phone) >= 10:
                    cleaned[field] = phone
            
            elif field == 'name':
                # Capitaliser le nom
                words = value.split()
                cleaned[field] = ' '.join(w.capitalize() for w in words)
            
            elif field == 'address':
                # Nettoyer l'adresse
                cleaned[field] = ' '.join(value.split())
            
            elif field == 'siret':
                # Garder uniquement les chiffres
                siret = re.sub(r'\D', '', value)
                if len(siret) == 14:
                    cleaned[field] = siret
            
            else:
                cleaned[field] = value
        
        return cleaned
    
    def _update_stats(self, success: bool, start_time: datetime) -> None:
        """Met à jour les statistiques d'extraction"""
        self.stats['processed_docs'] += 1
        if success:
            self.stats['successful_extractions'] += 1
        else:
            self.stats['failed_extractions'] += 1
        
        processing_time = (datetime.now() - start_time).total_seconds()
        self.stats['last_extraction_time'] = datetime.now().isoformat()
        
        # Sauvegarder les stats périodiquement
        if self.stats['processed_docs'] % 10 == 0:
            self._save_stats()
    
    def _save_stats(self) -> None:
        """Sauvegarde les statistiques dans un fichier"""
        try:
            stats_dir = Path("data/stats")
            stats_dir.mkdir(parents=True, exist_ok=True)
            
            stats_file = stats_dir / "client_extractor_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des statistiques: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'extraction"""
        return self.stats
    
    def clear_cache(self) -> None:
        """Vide le cache d'extraction"""
        self.cache.clear()
        logger.info("Cache d'extraction vidé") 