import os
import logging
import traceback
from typing import Dict, List, Any, Optional, Tuple
import re
import json
from datetime import datetime

logger = logging.getLogger("VynalDocsAutomator.DocumentCreator")

class DocumentCreator:
    def __init__(self):
        """
        Initialise le créateur de documents
        """
        self.ai_processor = None  # Initialisé à la demande
        self.current_template = None
        self.current_analysis = None
        self.required_variables = None
        self.cache = {}  # Cache pour les analyses de template
        self.last_error = None
        self.processing_status = "ready"
        self.validation_errors = []
        self.stats = {
            'created_docs': 0,
            'successful_creations': 0,
            'failed_creations': 0,
            'validation_failures': 0,
            'avg_creation_time': 0,
            'last_creation_time': None,
            'cache_hits': 0,
            'cache_misses': 0
        }
        self._initialize_stats()

    def _initialize_stats(self):
        """Initialise ou charge les statistiques depuis un fichier"""
        stats_file = "data/creator_stats.json"
        try:
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    saved_stats = json.load(f)
                    self.stats.update(saved_stats)
        except Exception:
            # En cas d'erreur, on garde les stats par défaut
            pass

    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du créateur
        
        Returns:
            Dict[str, Any]: Statistiques d'utilisation
        """
        return self.stats

    def clear_cache(self) -> None:
        """Vide le cache du créateur"""
        self.cache.clear()

    def _update_stats(self, success: bool, creation_time: float):
        """
        Met à jour les statistiques après une création
        
        Args:
            success (bool): Si la création a réussi
            creation_time (float): Temps de création en secondes
        """
        self.stats['created_docs'] += 1
        if success:
            self.stats['successful_creations'] += 1
        else:
            self.stats['failed_creations'] += 1

        # Mise à jour du temps moyen (moyenne mobile)
        if self.stats['avg_creation_time'] == 0:
            self.stats['avg_creation_time'] = creation_time
        else:
            self.stats['avg_creation_time'] = (
                0.7 * self.stats['avg_creation_time'] + 
                0.3 * creation_time
            )
        
        self.stats['last_creation_time'] = datetime.now().isoformat()

        # Sauvegarder les stats périodiquement
        if self.stats['created_docs'] % 10 == 0:  # Tous les 10 documents
            self._save_stats()

    def _save_stats(self):
        """Sauvegarde les statistiques dans un fichier"""
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/creator_stats.json", 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception:
            # Échec silencieux - la sauvegarde n'est pas critique
            pass

    def _initialize_ai_processor(self):
        """
        Initialise le processeur IA à la demande pour optimiser le démarrage
        """
        if self.ai_processor is None:
            try:
                from controllers.ai_document_processor import AIDocumentProcessor
                self.ai_processor = AIDocumentProcessor()
                logger.info("AIDocumentProcessor initialisé")
                return True
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation de l'AIDocumentProcessor: {e}")
                self.last_error = str(e)
                return False
        return True

    def analyze_template(self, template_path: str) -> Dict:
        """
        Analyse un template pour identifier les variables nécessaires
        
        Args:
            template_path: Chemin vers le template à analyser
            
        Returns:
            Dict contenant les variables identifiées et leur description
        """
        try:
            # Vérifier le cache pour éviter de réanalyser un template déjà traité
            if template_path in self.cache:
                logger.info(f"Utilisation du cache pour le template: {template_path}")
                cached_result = self.cache[template_path]
                
                # Réinitialiser l'état courant avec les données du cache
                self.current_template = template_path
                self.current_analysis = cached_result.get('analysis', {})
                self.required_variables = cached_result.get('required', {})
                
                return cached_result
            
            # Initialiser l'état
            self.current_template = template_path
            self.processing_status = "analyzing"
            
            # Vérifier que le processeur IA est initialisé
            if not self._initialize_ai_processor():
                return {'error': f"Erreur d'initialisation: {self.last_error}"}
            
            # Vérifier que le template existe
            if not os.path.exists(template_path):
                error_msg = f"Le fichier template n'existe pas: {template_path}"
                logger.error(error_msg)
                self.last_error = error_msg
                self.processing_status = "error"
                return {'error': error_msg}
            
            # Lire le contenu du template si c'est un chemin de fichier
            template_content = ""
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(template_path, 'r', encoding='latin-1') as f:
                        template_content = f.read()
                except Exception as inner_e:
                    error_msg = f"Erreur lors de la lecture du template: {inner_e}"
                    logger.error(error_msg)
                    self.last_error = error_msg
                    self.processing_status = "error"
                    return {'error': error_msg}
            
            # Analyser le document avec l'IA
            analysis = self.ai_processor.analyze_document(template_content)
            
            # Sauvegarder l'analyse
            self.current_analysis = analysis
            
            # Si l'analyse n'a pas trouvé de variables, renvoyer une erreur enrichie
            if not analysis.get('variables'):
                logger.warning(f"Aucune variable trouvée dans le template: {template_path}")
                # Essayer l'analyse contextuelle
                detailed_analysis = self._enrich_empty_analysis(template_content)
                self.current_analysis = detailed_analysis
                analysis = detailed_analysis
            
            # Extraire les variables requises
            self.required_variables = {
                name: info for name, info in analysis.get('variables', {}).items()
                if info.get('required', True)
            }
            
            # Préparer le résultat
            result = {
                'variables': analysis.get('variables', {}),
                'required': self.required_variables,
                'analysis': analysis,
                'analysis_type': analysis.get('analysis_type', 'standard')
            }
            
            # Sauvegarder dans le cache
            self.cache[template_path] = result
            
            # Mettre à jour le statut
            self.processing_status = "analyzed"
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du template: {e}")
            logger.debug(traceback.format_exc())
            self.last_error = str(e)
            self.processing_status = "error"
            return {'error': str(e)}

    def _enrich_empty_analysis(self, document_content: str) -> Dict:
        """
        Enrichit une analyse vide avec des informations contextuelles
        et des variables par défaut
        """
        try:
            # Utiliser le processeur IA pour une analyse contextuelle approfondie
            if hasattr(self.ai_processor, '_analyze_document_contextually'):
                contextual_result = self.ai_processor._analyze_document_contextually(document_content)
                
                if contextual_result and contextual_result.get('variables'):
                    # Post-traiter les variables pour améliorer les types et descriptions
                    if hasattr(self.ai_processor, '_post_process_variables'):
                        variables = self.ai_processor._post_process_variables(contextual_result.get('variables', {}))
                        contextual_result['variables'] = variables
                    
                    logger.info(f"Analyse contextuelle a trouvé {len(contextual_result.get('variables', {}))} variables")
                    return {
                        'variables': contextual_result.get('variables', {}),
                        'analysis_type': 'contextual',
                        'from_analysis': True
                    }
            
            # Si l'analyse contextuelle échoue, extraire au moins les patterns courants
            if hasattr(self.ai_processor, '_extract_common_patterns'):
                patterns_result = self.ai_processor._extract_common_patterns(document_content)
                
                if patterns_result:
                    logger.info(f"Extraction de patterns a trouvé {len(patterns_result)} variables")
                    return {
                        'variables': patterns_result,
                        'analysis_type': 'patterns',
                        'from_analysis': True
                    }
            
            # En dernier recours, ajouter des variables par défaut
            default_variables = {
                "nom": {
                    "description": "Nom complet",
                    "type": "text",
                    "required": True,
                    "current_value": ""
                },
                "date": {
                    "description": "Date du document",
                    "type": "date",
                    "required": True,
                    "current_value": ""
                },
                "montant": {
                    "description": "Montant ou somme",
                    "type": "amount",
                    "required": True,
                    "current_value": ""
                },
                "reference": {
                    "description": "Numéro de référence",
                    "type": "reference",
                    "required": False,
                    "current_value": ""
                }
            }
            
            return {
                'variables': default_variables,
                'analysis_type': 'default',
                'from_analysis': True
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement de l'analyse: {e}")
            logger.debug(traceback.format_exc())
            
            # Variables minimales en cas d'erreur
            return {
                'variables': {
                    "contenu_document": {
                        "description": "Contenu du document",
                        "type": "text",
                        "required": True,
                        "current_value": ""
                    }
                },
                'analysis_type': 'minimal',
                'from_analysis': True
            }

    def validate_template(self, template_path: str) -> Tuple[bool, List[str]]:
        """
        Valide un template avant utilisation
        
        Args:
            template_path: Chemin vers le template
            
        Returns:
            Tuple[bool, List[str]]: (succès, messages d'erreur)
        """
        errors = []
        
        try:
            # 1. Vérifier l'existence du fichier
            if not os.path.exists(template_path):
                errors.append(f"Le template n'existe pas: {template_path}")
                return False, errors
            
            # 2. Vérifier le type de fichier
            _, ext = os.path.splitext(template_path)
            allowed_extensions = ['.docx', '.doc', '.txt', '.odt']
            if ext.lower() not in allowed_extensions:
                errors.append(f"Type de fichier non supporté: {ext}")
                return False, errors
            
            # 3. Vérifier la taille du fichier
            max_size_mb = 10
            size_mb = os.path.getsize(template_path) / (1024 * 1024)
            if size_mb > max_size_mb:
                errors.append(f"Fichier trop volumineux: {size_mb:.1f}MB (max {max_size_mb}MB)")
                return False, errors
            
            # 4. Vérifier le contenu du fichier
            try:
                with open(template_path, 'rb') as f:
                    content = f.read(1024)  # Lire les premiers 1024 octets
                    if not content.strip():
                        errors.append("Le fichier est vide")
                        return False, errors
            except Exception as e:
                errors.append(f"Erreur lors de la lecture du fichier: {str(e)}")
                return False, errors
            
            return True, []
            
        except Exception as e:
            errors.append(f"Erreur lors de la validation du template: {str(e)}")
            return False, errors

    def validate_variables(self, variables: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valide les variables avant la création du document
        
        Args:
            variables: Dictionnaire des variables à valider
            
        Returns:
            Tuple[bool, List[str]]: (succès, messages d'erreur)
        """
        errors = []
        
        try:
            if not variables:
                errors.append("Aucune variable fournie")
                return False, errors
            
            # Vérifier les variables requises
            if self.required_variables:
                for var_name in self.required_variables:
                    if var_name not in variables:
                        errors.append(f"Variable requise manquante: {var_name}")
                    elif not variables[var_name]:
                        errors.append(f"Variable requise vide: {var_name}")
            
            # Vérifier les types et formats des variables
            if self.current_analysis and 'variables' in self.current_analysis:
                for var_name, var_value in variables.items():
                    var_info = self.current_analysis['variables'].get(var_name, {})
                    var_type = var_info.get('type', 'text')
                    
                    # Validation selon le type
                    if var_type == 'date':
                        if not self._validate_date(var_value):
                            errors.append(f"Format de date invalide pour {var_name}: {var_value}")
                    elif var_type == 'email':
                        if not self._validate_email(var_value):
                            errors.append(f"Format d'email invalide pour {var_name}: {var_value}")
                    elif var_type == 'phone':
                        if not self._validate_phone(var_value):
                            errors.append(f"Format de téléphone invalide pour {var_name}: {var_value}")
                    elif var_type == 'number':
                        if not self._validate_number(var_value):
                            errors.append(f"Format de nombre invalide pour {var_name}: {var_value}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Erreur lors de la validation des variables: {str(e)}")
            return False, errors

    def _validate_date(self, value: str) -> bool:
        """Valide une date"""
        try:
            if not value:
                return False
            # Accepter plusieurs formats de date
            formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y']
            for fmt in formats:
                try:
                    datetime.strptime(value, fmt)
                    return True
                except ValueError:
                    continue
            return False
        except:
            return False

    def _validate_email(self, value: str) -> bool:
        """Valide un email"""
        if not value:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))

    def _validate_phone(self, value: str) -> bool:
        """Valide un numéro de téléphone"""
        if not value:
            return False
        pattern = r'^\+?[\d\s\-\.()]+$'
        return bool(re.match(pattern, value))

    def _validate_number(self, value: str) -> bool:
        """Valide un nombre"""
        try:
            float(value)
            return True
        except:
            return False

    def create_personalized_document(self, variables: Dict[str, str], output_path: str = None) -> Dict:
        """
        Crée un document personnalisé avec les variables fournies
        
        Args:
            variables: Dict des variables et leurs valeurs
            output_path: Chemin de sortie pour le document (optionnel)
            
        Returns:
            Dict contenant le statut et le résultat
        """
        start_time = datetime.now()
        
        try:
            logger.info("Début de la création du document personnalisé")
            
            # 1. Validation initiale
            if not self.current_template:
                logger.error("Aucun template n'a été analysé")
                raise ValueError("Aucun template n'a été analysé")
            
            logger.info(f"Template à utiliser: {self.current_template}")
            
            # 2. Valider le template
            logger.info("Validation du template...")
            template_valid, template_errors = self.validate_template(self.current_template)
            if not template_valid:
                logger.error(f"Validation du template échouée: {template_errors}")
                self.validation_errors = template_errors
                self.stats['validation_failures'] += 1
                return {
                    'status': 'error',
                    'message': 'Validation du template échouée',
                    'errors': template_errors
                }
            
            logger.info("Template validé avec succès")
            
            # 3. Valider les variables
            logger.info("Validation des variables...")
            logger.debug(f"Variables à valider: {variables}")
            
            variables_valid, variable_errors = self.validate_variables(variables)
            if not variables_valid:
                logger.error(f"Validation des variables échouée: {variable_errors}")
                self.validation_errors = variable_errors
                self.stats['validation_failures'] += 1
                return {
                    'status': 'error',
                    'message': 'Validation des variables échouée',
                    'errors': variable_errors
                }
            
            logger.info("Variables validées avec succès")
            
            # 4. Initialiser le processeur IA
            logger.info("Initialisation du processeur IA...")
            if not self._initialize_ai_processor():
                logger.error(f"Erreur d'initialisation du processeur IA: {self.last_error}")
                return {
                    'status': 'error',
                    'message': f"Erreur d'initialisation: {self.last_error}"
                }
            
            logger.info("Processeur IA initialisé avec succès")
            
            # 5. Créer le document
            logger.info("Création du document...")
            self.processing_status = "creating"
            
            # Prétraiter les variables
            processed_variables = self._process_variables(variables, self.current_analysis.get('variables', {}))
            logger.debug(f"Variables prétraitées: {processed_variables}")
            
            result = self.ai_processor.fill_template(
                self.current_template,
                processed_variables
            )
            
            # 6. Vérifier le résultat
            if isinstance(result, dict) and result.get('error'):
                logger.error(f"Erreur lors de la création: {result['error']}")
                self.stats['failed_creations'] += 1
                return {
                    'status': 'error',
                    'message': result['error']
                }
            
            logger.info("Document créé avec succès")
            
            # 7. Sauvegarder le document
            if output_path:
                logger.info(f"Sauvegarde du document dans: {output_path}")
                try:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(result)
                    logger.info("Document sauvegardé avec succès")
                except Exception as e:
                    logger.error(f"Erreur lors de la sauvegarde: {str(e)}")
                    return {
                        'status': 'error',
                        'message': f"Erreur lors de la sauvegarde: {str(e)}"
                    }
            
            # 8. Mettre à jour les statistiques
            self.stats['created_docs'] += 1
            self.stats['successful_creations'] += 1
            creation_time = (datetime.now() - start_time).total_seconds()
            self.stats['avg_creation_time'] = (
                (self.stats['avg_creation_time'] * (self.stats['created_docs'] - 1) + creation_time)
                / self.stats['created_docs']
            )
            self.stats['last_creation_time'] = creation_time
            
            logger.info(f"Document créé en {creation_time:.2f} secondes")
            
            return {
                'status': 'success',
                'content': result,
                'output_path': output_path if output_path else None,
                'creation_time': creation_time
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du document: {e}")
            logger.debug(traceback.format_exc())
            self.stats['failed_creations'] += 1
            self.last_error = str(e)
            return {
                'status': 'error',
                'message': str(e)
            }

    def _preprocess_variables(self, variables: Dict[str, str]) -> Dict[str, str]:
        """
        Prétraite les variables avant la personnalisation pour assurer 
        la compatibilité et le bon formatage
        
        Args:
            variables: Dict des variables et leurs valeurs
            
        Returns:
            Dict des variables prétraitées
        """
        processed = {}
        
        # Obtenir les infos sur chaque variable si disponible
        var_infos = self.current_analysis.get('variables', {})
        
        for name, value in variables.items():
            # Si la valeur est None ou vide, la sauter
            if value is None or value == "":
                continue
                
            # Convertir en chaîne de caractères
            if not isinstance(value, str):
                value = str(value)
            
            # Appliquer des transformations en fonction du type de variable
            var_info = var_infos.get(name, {})
            var_type = var_info.get('type', 'text')
            
            if var_type == 'date':
                # Formater les dates selon le format attendu
                value = self._format_date(value, var_info.get('format', 'dd/mm/yyyy'))
            elif var_type == 'amount':
                # Formater les montants (ajouter symbole € si pas présent)
                if '€' not in value and 'EUR' not in value and 'euro' not in value.lower():
                    if ',' in value or '.' in value:
                        value = f"{value} €"
                    else:
                        # Si pas de décimale, ajouter ,00
                        value = f"{value},00 €"
            
            processed[name] = value
        
        return processed

    def _format_date(self, date_value: str, target_format: str) -> str:
        """Formate une date selon le format cible"""
        # Si la date est déjà dans le bon format, la retourner telle quelle
        if target_format == 'original':
            return date_value
            
        try:
            # Extraire les composants de la date
            day, month, year = None, None, None
            
            # Reconnaître le format d'entrée
            if re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_value):
                day, month, year = date_value.split('/')
            elif re.match(r'\d{1,2}/\d{1,2}/\d{2}', date_value):
                day, month, year = date_value.split('/')
                # Compléter l'année si nécessaire
                if len(year) == 2:
                    year = '20' + year
            elif re.match(r'\d{1,2}-\d{1,2}-\d{4}', date_value):
                day, month, year = date_value.split('-')
            elif re.match(r'\d{4}-\d{1,2}-\d{1,2}', date_value):
                year, month, day = date_value.split('-')
            
            if day and month and year:
                # Appliquer le format cible
                if target_format == 'dd/mm/yyyy':
                    return f"{int(day):02d}/{int(month):02d}/{year}"
                elif target_format == 'dd-mm-yyyy':
                    return f"{int(day):02d}-{int(month):02d}-{year}"
                elif target_format == 'yyyy-mm-dd':
                    return f"{year}-{int(month):02d}-{int(day):02d}"
                elif target_format == 'dd/mm/yy':
                    short_year = year[-2:]
                    return f"{int(day):02d}/{int(month):02d}/{short_year}"
            
            # Si le format n'est pas reconnu ou ne peut pas être traité, retourner la valeur originale
            return date_value
            
        except Exception as e:
            logger.warning(f"Erreur lors du formatage de la date {date_value}: {e}")
            return date_value

    def _apply_basic_replacements(self, content: str, variables: Dict[str, str]) -> str:
        """
        Applique des remplacements basiques pour les variables sans délimiteurs
        en cas d'échec de la personnalisation par IA
        
        Args:
            content: Contenu du template
            variables: Dict des variables et leurs valeurs
            
        Returns:
            str: Contenu personnalisé
        """
        personalized = content
        
        # Essayer d'abord le remplacement des modèles courants
        for var_name, var_value in variables.items():
            if not var_value:
                continue
                
            # Tenter le remplacement direct
            personalized = personalized.replace(f"{{{{{var_name}}}}}", var_value)
            
            # Essayer avec d'autres formats courants
            personalized = personalized.replace(f"<<{var_name}>>", var_value)
            personalized = personalized.replace(f"$${var_name}$$", var_value)
            personalized = personalized.replace(f"[{var_name}]", var_value)
            
            # Essayer avec différentes variations de casse
            personalized = personalized.replace(f"{{{{{var_name.upper()}}}}}", var_value)
            personalized = personalized.replace(f"{{{{{var_name.capitalize()}}}}}", var_value)
        
        # Si aucun changement, faire un remplacement direct des valeurs
        if personalized == content and variables:
            # Créer une liste triée des valeurs par longueur (décroissante) pour éviter les remplacements partiels
            values_to_replace = [(k, v) for k, v in variables.items() if v and len(v) > 3]
            values_to_replace.sort(key=lambda x: len(x[1]), reverse=True)
            
            # Rechercher et remplacer les occurrences exactes des valeurs
            for var_name, value in values_to_replace:
                personalized = personalized.replace(value, f"<<{var_name}>>")
            
            # Remplacer les marqueurs temporaires par les valeurs
            for var_name, value in variables.items():
                if value:
                    personalized = personalized.replace(f"<<{var_name}>>", value)
        
        return personalized

    def get_required_variables(self) -> Dict:
        """
        Retourne les variables requises pour le template courant
        
        Returns:
            Dict des variables requises et leur description
        """
        if not self.required_variables:
            return {}
        return self.required_variables
    
    def get_status(self) -> Dict:
        """
        Retourne l'état actuel du créateur de documents
        
        Returns:
            Dict contenant des informations sur l'état du créateur
        """
        status = {
            'status': self.processing_status,
            'has_template': self.current_template is not None,
            'has_analysis': self.current_analysis is not None,
            'variable_count': len(self.current_analysis.get('variables', {})) if self.current_analysis else 0,
            'required_variable_count': len(self.required_variables) if self.required_variables else 0,
            'last_error': self.last_error
        }
        
        return status
    
    def reset(self):
        """
        Réinitialise l'état du créateur de documents
        """
        self.current_template = None
        self.current_analysis = None
        self.required_variables = None
        self.last_error = None
        self.processing_status = "ready"
    
    def clear_cache(self):
        """
        Vide le cache d'analyses
        """
        self.cache = {}
        logger.info("Cache d'analyses vidé")