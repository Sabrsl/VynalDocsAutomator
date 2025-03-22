import customtkinter as ctk
from typing import Optional, Dict, List, Any, Callable
import logging
import os
import threading
import time
from datetime import datetime
from PIL import Image, ImageTk
from utils.ui_components import LoadingSpinner, ThemeManager

# Import des composants d'analyse
from doc_analyzer.extractors.personal_data import PersonalDataExtractor
from doc_analyzer.extractors.legal_docs import LegalDocsExtractor
from doc_analyzer.extractors.identity_docs import IdentityDocExtractor
from doc_analyzer.extractors.contracts import ContractExtractor
from doc_analyzer.extractors.business_docs import BusinessDocExtractor

from doc_analyzer.recognizers.phone_recognizer import PhoneRecognizer
from doc_analyzer.recognizers.name_recognizer import NameRecognizer
from doc_analyzer.recognizers.id_recognizer import IDRecognizer
from doc_analyzer.recognizers.address_recognizer import AddressRecognizer

from doc_analyzer.utils.text_processor import TextProcessor
from doc_analyzer.utils.validators import DataValidator
from doc_analyzer.utils.ocr import OCRProcessor

logger = logging.getLogger("VynalDocsAutomator.Views.Analysis")

class DocumentAnalyzer:
    """
    Classe principale pour l'analyse de documents
    """
    
    def __init__(self):
        """
        Initialise l'analyseur de documents avec initialisation paresseuse des composants
        """
        # Utilisation d'attributs privés pour l'initialisation paresseuse
        self._personal_data_extractor = None
        self._legal_docs_extractor = None
        self._identity_doc_extractor = None
        self._contract_extractor = None
        self._business_doc_extractor = None
        
        self._phone_recognizer = None
        self._name_recognizer = None
        self._id_recognizer = None
        self._address_recognizer = None
        
        self._text_processor = None
        self._data_validator = None
        self._ocr_processor = None
        
        logger.info("DocumentAnalyzer initialisé avec succès")
    
    # Propriétés pour l'initialisation paresseuse
    @property
    def personal_data_extractor(self):
        if self._personal_data_extractor is None:
            self._personal_data_extractor = PersonalDataExtractor()
            logger.info("Extracteur de données personnelles initialisé")
        return self._personal_data_extractor
    
    @property
    def legal_docs_extractor(self):
        if self._legal_docs_extractor is None:
            self._legal_docs_extractor = LegalDocsExtractor()
            logger.info("Extracteur de documents légaux initialisé")
        return self._legal_docs_extractor
    
    @property
    def identity_doc_extractor(self):
        if self._identity_doc_extractor is None:
            self._identity_doc_extractor = IdentityDocExtractor()
            logger.info("Extracteur de documents d'identité initialisé")
        return self._identity_doc_extractor
    
    @property
    def contract_extractor(self):
        if self._contract_extractor is None:
            self._contract_extractor = ContractExtractor()
            logger.info("Extracteur de contrats initialisé")
        return self._contract_extractor
    
    @property
    def business_doc_extractor(self):
        if self._business_doc_extractor is None:
            self._business_doc_extractor = BusinessDocExtractor()
            logger.info("BusinessDocExtractor initialized")
        return self._business_doc_extractor
    
    @property
    def phone_recognizer(self):
        if self._phone_recognizer is None:
            self._phone_recognizer = PhoneRecognizer()
            logger.info("Reconnaisseur de numéros de téléphone initialisé")
        return self._phone_recognizer
    
    @property
    def name_recognizer(self):
        if self._name_recognizer is None:
            self._name_recognizer = NameRecognizer()
            logger.info("Reconnaisseur de noms initialisé")
        return self._name_recognizer
    
    @property
    def id_recognizer(self):
        if self._id_recognizer is None:
            self._id_recognizer = IDRecognizer()
            logger.info("IDRecognizer initialisé")
        return self._id_recognizer
    
    @property
    def address_recognizer(self):
        if self._address_recognizer is None:
            self._address_recognizer = AddressRecognizer()
            logger.info("Reconnaisseur d'adresses initialisé")
        return self._address_recognizer
    
    @property
    def text_processor(self):
        if self._text_processor is None:
            self._text_processor = TextProcessor()
            logger.info("Initialisation du TextProcessor")
        return self._text_processor
    
    @property
    def data_validator(self):
        if self._data_validator is None:
            self._data_validator = DataValidator()
            logger.info("DataValidator initialisé")
        return self._data_validator
    
    @property
    def ocr_processor(self):
        if not hasattr(self, '_ocr_processor') or self._ocr_processor is None:
            try:
                self._ocr_processor = OCRProcessor()
            except Exception as e:
                logger.warning(f"OCR non disponible - fonctionnalités limitées: {e}")
                self._ocr_processor = None
        return self._ocr_processor
    
    def analyze_document(self, document_path: str) -> Dict[str, Any]:
        """
        Analyse un document et extrait toutes les informations pertinentes
        
        Args:
            document_path: Chemin vers le document à analyser
            
        Returns:
            dict: Résultats de l'analyse
        """
        try:
            # Vérifier si le fichier est un JSON (rejeter ces fichiers)
            if document_path.lower().endswith('.json'):
                logger.error(f"Les fichiers JSON ne sont pas supportés pour l'analyse: {document_path}")
                return {
                    'file_path': document_path,
                    'error': "Les fichiers JSON ne sont pas supportés pour l'analyse de document"
                }
                
            # Vérifier le contenu du fichier pour détecter les JSON non déclarés par l'extension
            try:
                with open(document_path, 'r', encoding='utf-8') as f:
                    first_chars = f.read(100).strip()
                    if first_chars.startswith('{') and ('"' in first_chars or "'" in first_chars):
                        # C'est probablement un JSON
                        logger.error(f"Le fichier semble être un JSON non déclaré: {document_path}")
                        return {
                            'file_path': document_path,
                            'error': "Ce fichier semble être au format JSON, qui n'est pas supporté pour l'analyse de document"
                        }
            except UnicodeDecodeError:
                # Ce n'est pas un fichier texte UTF-8, donc pas un JSON
                pass
            
            # Prétraitement du document
            text_result = self.text_processor.process_document(document_path)
            
            # Vérifier si une erreur s'est produite lors du prétraitement
            if isinstance(text_result, dict) and 'error' in text_result:
                logger.error(f"Erreur lors du prétraitement du document: {text_result['error']}")
                return {
                    'file_path': document_path,
                    'error': text_result['error']
                }
            
            # Extraire le texte du résultat
            if isinstance(text_result, dict):
                if 'text' in text_result:
                    text = text_result['text']
                else:
                    logger.warning("Aucun texte trouvé dans les résultats du prétraitement")
                    text = ""
            else:
                text = text_result
            
            # Initialiser les résultats avec le texte extrait
            results = {
                'file_path': document_path,
                'text': text,
                'variables': {}
            }
            
            # Analyse de la structure du document
            try:
                structure = self.text_processor.analyze_document_structure(text)
                if structure:
                    results['structure'] = structure
                    # Ajouter les variables de base
                    results['variables'].update({
                        'langue': structure.get('language', 'fr'),
                        'type_document': structure.get('document_type', 'autre'),
                        'titre': structure.get('title', ''),
                        'mots_cles': [kw[0] for kw in structure.get('keywords', [])]
                    })
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse de la structure: {e}")
            
            # Extraction des données personnelles
            try:
                personal_data = self.personal_data_extractor.extract(text)
                if personal_data:
                    results["personal_data"] = personal_data
                    # Ajouter les variables d'identité
                    if 'identity' in personal_data:
                        identity = personal_data['identity']
                        if identity.get('first_name') and identity.get('last_name'):
                            results['variables']['nom_complet'] = f"{identity['first_name']} {identity['last_name']}"
                        results['variables'].update({
                            'nom': identity.get('last_name', ''),
                            'prenom': identity.get('first_name', ''),
                            'date_naissance': identity.get('birth_date', ''),
                            'lieu_naissance': identity.get('birth_place', ''),
                            'nationalite': identity.get('nationality', ''),
                            'genre': identity.get('gender', ''),
                            'etat_civil': identity.get('civil_status', '')
                        })
                    # Ajouter les variables de contact
                    if 'contact' in personal_data:
                        contact = personal_data['contact']
                        if isinstance(contact.get('address'), dict):
                            address = contact['address']
                            results['variables'].update({
                                'adresse': address.get('full_address', ''),
                                'rue': address.get('street', ''),
                                'code_postal': address.get('postal_code', ''),
                                'ville': address.get('city', ''),
                                'pays': address.get('country', '')
                            })
                        if contact.get('phone_numbers'):
                            results['variables']['telephone'] = contact['phone_numbers'][0] if contact['phone_numbers'] else ''
                            results['variables']['telephones'] = contact['phone_numbers']
                        if contact.get('email'):
                            results['variables']['email'] = contact['email']
                    # Ajouter les variables professionnelles
                    if 'professional' in personal_data:
                        professional = personal_data['professional']
                        results['variables'].update({
                            'profession': professional.get('job_title', ''),
                            'entreprise': professional.get('company', ''),
                            'identifiant_professionnel': professional.get('professional_id', '')
                        })
                    # Ajouter les variables d'identifiants
                    if 'ids' in personal_data:
                        ids = personal_data['ids']
                        results['variables'].update({
                            'numero_securite_sociale': ids.get('ssn', ''),
                            'siret_personnel': ids.get('siret', ''),
                            'autres_identifiants': ids.get('other_ids', [])
                        })
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction des données personnelles: {e}")
            
            # Extraction des documents légaux
            try:
                legal_data = self.legal_docs_extractor.extract(text)
                if legal_data:
                    results["legal_data"] = legal_data
                    # Ajouter les variables de base
                    results['variables'].update({
                        'type_document': legal_data.get('doc_type', results['variables'].get('type_document', '')),
                        'titre_document': legal_data.get('title', ''),
                        'reference': legal_data.get('reference', ''),
                        'date_document': legal_data.get('creation_date', '')
                    })
                    # Ajouter les dates importantes
                    if 'important_dates' in legal_data:
                        dates = legal_data['important_dates']
                        results['variables'].update({
                            'date_signature': dates.get('signature', ''),
                            'date_effet': dates.get('effective', ''),
                            'date_expiration': dates.get('expiration', '')
                        })
                    # Ajouter les informations spécifiques au type de document
                    if 'content_fields' in legal_data:
                        content = legal_data['content_fields']
                        if legal_data.get('doc_type') == 'contrat_travail':
                            results['variables'].update({
                                'poste': content.get('poste', ''),
                                'salaire': content.get('salaire', ''),
                                'duree_travail': content.get('duree_travail', ''),
                                'lieu_travail': content.get('lieu_travail', ''),
                                'avantages': content.get('avantages', []),
                                'periode_essai': content.get('periode_essai', ''),
                                'convention_collective': content.get('convention_collective', '')
                            })
                        elif legal_data.get('doc_type') == 'contrat_prestation_service':
                            results['variables'].update({
                                'services': content.get('services', []),
                                'montant': content.get('montant', ''),
                                'duree_contrat': content.get('duree_contrat', ''),
                                'delais_execution': content.get('delais_execution', ''),
                                'livrables': content.get('livrables', [])
                            })
                        elif legal_data.get('doc_type') == 'contrat_vente':
                            results['variables'].update({
                                'biens': content.get('biens', []),
                                'prix_unitaires': content.get('prix_unitaires', {}),
                                'conditions_livraison': content.get('conditions_livraison', ''),
                                'garanties': content.get('garanties', '')
                            })
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction des données légales: {e}")
            
            # Extraction des documents d'identité
            try:
                identity_data = self.identity_doc_extractor.extract(text)
                if identity_data:
                    results["identity_data"] = identity_data
                    # Ajouter les variables d'identité
                    results['variables'].update({
                        'numero_identite': identity_data.get('document_number', ''),
                        'type_identite': identity_data.get('document_type', ''),
                        'date_emission': identity_data.get('document_info', {}).get('issue_date', ''),
                        'date_expiration': identity_data.get('document_info', {}).get('expiry_date', ''),
                        'autorite_emission': identity_data.get('document_info', {}).get('issuing_authority', ''),
                        'pays_emission': identity_data.get('country', '')
                    })
                    # Ajouter les informations personnelles si non déjà présentes
                    if 'personal_info' in identity_data:
                        personal = identity_data['personal_info']
                        if not results['variables'].get('nom_complet'):
                            if personal.get('last_name') and personal.get('first_name'):
                                results['variables']['nom_complet'] = f"{personal['first_name']} {personal['last_name']}"
                        for key, value in personal.items():
                            if not results['variables'].get(key) and value:
                                results['variables'][key] = value
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction des données d'identité: {e}")
            
            # Extraction des contrats
            try:
                contract_data = self.contract_extractor.extract(text)
                if contract_data:
                    results["contract_data"] = contract_data
                    # Ajouter les variables de contrat
                    results['variables'].update({
                        'type_contrat': contract_data.get('type', ''),
                        'montant_contrat': contract_data.get('amounts', {}).get('prix', ''),
                        'taux_horaire': contract_data.get('amounts', {}).get('taux_horaire', ''),
                        'devise': contract_data.get('amounts', {}).get('devise', 'EUR'),
                        'duree_contrat': contract_data.get('dates', {}).get('duree', ''),
                        'duree_unite': contract_data.get('dates', {}).get('duree_unite', ''),
                        'date_debut': contract_data.get('dates', {}).get('date_debut', ''),
                        'date_fin': contract_data.get('dates', {}).get('date_fin', ''),
                        'mode_paiement': contract_data.get('payment', {}).get('mode_paiement', ''),
                        'delai_paiement': contract_data.get('payment', {}).get('delai_paiement', ''),
                        'echeancier': contract_data.get('payment', {}).get('echeancier', ''),
                        'clause_confidentialite': contract_data.get('obligations', {}).get('confidentialite', ''),
                        'clause_non_concurrence': contract_data.get('obligations', {}).get('non_concurrence', ''),
                        'clause_resiliation': contract_data.get('obligations', {}).get('resiliation', '')
                    })
                    # Ajouter les parties du contrat
                    if 'parties' in contract_data:
                        parties = contract_data['parties']
                        results['variables'].update({
                            'client': parties.get('client', {}),
                            'prestataire': parties.get('prestataire', {}),
                            'signataires': parties.get('signataires', [])
                        })
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction des données de contrat: {e}")
            
            # Extraction des documents commerciaux
            try:
                business_data = self.business_doc_extractor.extract(text)
                if business_data:
                    results["business_data"] = business_data
                    # Ajouter les variables commerciales
                    results['variables'].update({
                        'societe': business_data.get('sender', {}).get('company_name', ''),
                        'siret_entreprise': business_data.get('sender', {}).get('siret', ''),
                        'montant_ht': business_data.get('amounts', {}).get('amount_excl_tax', ''),
                        'montant_ttc': business_data.get('amounts', {}).get('amount_incl_tax', ''),
                        'tva': business_data.get('amounts', {}).get('vat', ''),
                        'details_tva': business_data.get('amounts', {}).get('vat_details', []),
                        'reference_document': business_data.get('reference', ''),
                        'date_document': business_data.get('date', ''),
                        'conditions_paiement': business_data.get('conditions', {}).get('payment', ''),
                        'conditions_livraison': business_data.get('conditions', {}).get('delivery', '')
                    })
                    # Ajouter les produits/services si présents
                    if 'products' in business_data:
                        results['variables']['produits'] = business_data['products']
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction des données commerciales: {e}")
            
            # Ajouter des variables par défaut si aucune n'a été détectée
            if not results['variables']:
                filename = os.path.basename(document_path)
                name_parts = os.path.splitext(filename)[0].split('_')
                
                results['variables'] = {
                    "nom_document": filename,
                    "type_document": "autre",
                    "date": datetime.now().strftime("%d/%m/%Y"),
                    "nom_client": " ".join(name_parts) if name_parts else "Client"
                }
                logger.info("Aucune donnée extraite, ajout de variables par défaut")
            
            # S'assurer que les variables essentielles sont présentes
            if not results['variables'].get('type_document'):
                results['variables']['type_document'] = 'autre'
            
            if not results['variables'].get('langue'):
                results['variables']['langue'] = 'fr'  # Langue par défaut
            
            # Validation des données extraites
            try:
                validated_results = self.data_validator.validate(results)
            except Exception as e:
                logger.error(f"Erreur lors de la validation des données: {e}")
                validated_results = results
            
            logger.info(f"Analyse du document {document_path} terminée avec succès")
            return validated_results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du document {document_path}: {e}")
            return {
                'file_path': document_path,
                'error': str(e)
            }

class ModernAnalysisView:
    """
    Vue professionnelle pour l'analyse de documents
    Permet d'analyser les documents et d'afficher les résultats
    avec une interface utilisateur moderne et réactive
    """
    
    def __init__(self, parent: ctk.CTkFrame, app_model: Any):
        """
        Initialise la vue d'analyse avec des composants modernes
        
        Args:
            parent: Widget parent
            app_model: Modèle de l'application
        """
        self.parent = parent
        self.model = app_model
        self.theme = ThemeManager.get_theme() if hasattr(ThemeManager, 'get_theme') else "dark"
        
        # Couleurs selon le thème
        self.colors = {
            "primary": ("#2D7AF6", "#3B8ED0"),
            "success": ("#28a745", "#34c759"),
            "warning": ("#ffc107", "#ffcc00"),
            "danger": ("#dc3545", "#ff3b30"),
            "info": ("#17a2b8", "#5ac8fa"),
            "light_bg": ("#f8f9fa", "#2c2c2e"),
            "card_bg": ("#ffffff", "#1c1c1e"),
            "text": ("#212529", "#f8f9fa"),
            "subtle_text": ("#6c757d", "#aeaeb2")
        }
        
        # Créer le cadre principal avec un aspect moderne
        self.frame = ctk.CTkFrame(parent, fg_color=self.colors["light_bg"])
        
        # Initialiser l'analyseur de documents avec gestion d'erreur améliorée
        try:
            self.doc_analyzer = DocumentAnalyzer()
            self._analyzer_ready = True
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de l'analyseur: {e}")
            self.doc_analyzer = None
            self._analyzer_ready = False
        
        # Variables d'état
        self.current_document = None
        self.analysis_results = {}
        self.is_analyzing = False
        self.batch_results = []
        self.analysis_history = []
        
        # Créer les widgets avec une approche moderne
        self.create_widgets()
        
        # Configurer les accélérateurs clavier
        self.setup_keyboard_shortcuts()
        
        logger.info("Vue d'analyse moderne initialisée")
    
    def setup_keyboard_shortcuts(self):
        """Configure les raccourcis clavier pour une utilisation efficace"""
        if hasattr(self.parent, 'bind'):
            # Ctrl+O pour ouvrir un document
            self.parent.bind("<Control-o>", lambda event: self.analyze_document())
            # Ctrl+B pour l'analyse par lot
            self.parent.bind("<Control-b>", lambda event: self.batch_analyze())
        
    def show(self):
        """Affiche la vue avec une animation subtile"""
        if self.frame is not None:
            # Animation d'apparition
            self.frame.configure(fg_color="transparent")
            self.frame.pack(fill=ctk.BOTH, expand=True)
            
            def fade_in():
                self.frame.configure(fg_color=self.colors["light_bg"])
            
            # Délai court pour l'animation
            self.frame.after(100, fade_in)
            logger.debug("Vue d'analyse affichée")
    
    def hide(self):
        """Cache la vue"""
        if self.frame is not None:
            self.frame.pack_forget()
            logger.debug("Vue d'analyse masquée")
    
    def update_view(self):
        """Met à jour la vue dynamiquement"""
        # Vérifier l'état de l'analyseur
        if not self._analyzer_ready:
            self.retry_analyzer_initialization()
        
        # Actualiser l'état des boutons et composants
        self.toggle_buttons_state()
        
        # Vérifier les résultats récents
        self.check_for_pending_results()
    
    def retry_analyzer_initialization(self):
        """Tente de réinitialiser l'analyseur s'il n'est pas disponible"""
        try:
            logger.info("Tentative de réinitialisation de l'analyseur de documents...")
            self.doc_analyzer = DocumentAnalyzer()
            self._analyzer_ready = True
            self.update_status("Analyseur réinitialisé avec succès", "success")
            self.toggle_buttons_state()
        except Exception as e:
            logger.error(f"Échec de réinitialisation de l'analyseur: {e}")
            self._analyzer_ready = False
            self.update_status("Impossible d'initialiser l'analyseur", "error")
    
    def toggle_buttons_state(self):
        """Met à jour l'état des boutons selon les conditions actuelles"""
        if not self._analyzer_ready:
            self.analyze_btn.configure(state="disabled", fg_color=self.colors["subtle_text"])
            self.batch_analyze_btn.configure(state="disabled", fg_color=self.colors["subtle_text"])
            
            # Ajouter un bouton de réessai si l'analyseur n'est pas disponible
            if not hasattr(self, 'retry_btn'):
                self.retry_btn = ctk.CTkButton(
                    self.toolbar,
                    text="🔄 Réessayer",
                    command=self.retry_analyzer_initialization,
                    width=120,
                    height=32,
                    corner_radius=8,
                    border_width=0,
                    fg_color=self.colors["warning"],
                    text_color=self.colors["text"]
                )
                self.retry_btn.pack(side=ctk.LEFT, padx=10)
        else:
            self.analyze_btn.configure(
                state="normal" if not self.is_analyzing else "disabled",
                fg_color=self.colors["primary"] if not self.is_analyzing else self.colors["subtle_text"]
            )
            self.batch_analyze_btn.configure(
                state="normal" if not self.is_analyzing else "disabled",
                fg_color=self.colors["primary"] if not self.is_analyzing else self.colors["subtle_text"]
            )
            
            # Supprimer le bouton de réessai s'il existe
            if hasattr(self, 'retry_btn'):
                self.retry_btn.destroy()
                delattr(self, 'retry_btn')
    
    def check_for_pending_results(self):
        """Vérifie s'il y a des résultats en attente à afficher"""
        # Cette méthode pourrait être utilisée pour vérifier des traitements async
        pass
    
    def create_widgets(self):
        """
        Crée les widgets de la vue avec un design moderne et professionnel
        """
        # Barre d'outils élégante
        self.toolbar = ctk.CTkFrame(self.frame, fg_color=self.colors["card_bg"], corner_radius=10)
        self.toolbar.pack(fill=ctk.X, padx=15, pady=15)
        
        # Titre de la section
        title_label = ctk.CTkLabel(
            self.toolbar,
            text="Analyse de Documents",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text"]
        )
        title_label.pack(side=ctk.LEFT, padx=15, pady=10)
        
        # Séparateur vertical
        separator = ctk.CTkFrame(self.toolbar, width=1, height=36, fg_color=self.colors["subtle_text"])
        separator.pack(side=ctk.LEFT, padx=15, pady=10)
        
        # Bouton Analyser avec icône
        self.analyze_btn = ctk.CTkButton(
            self.toolbar,
            text="🔍 Analyser un document",
            command=self.analyze_document,
            width=200,
            height=36,
            corner_radius=8,
            border_width=0,
            fg_color=self.colors["primary"],
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=13)
        )
        self.analyze_btn.pack(side=ctk.LEFT, padx=10, pady=10)
        
        # Bouton Analyser en lot avec icône
        self.batch_analyze_btn = ctk.CTkButton(
            self.toolbar,
            text="📑 Analyse par lot",
            command=self.batch_analyze,
            width=200,
            height=36,
            corner_radius=8,
            border_width=0,
            fg_color=self.colors["primary"],
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=13)
        )
        self.batch_analyze_btn.pack(side=ctk.LEFT, padx=10, pady=10)
        
        # Indicateur de chargement modern avec animation
        self.loading_spinner = LoadingSpinner(self.toolbar, size=32, fg_color="transparent")
        self.loading_spinner.pack(side=ctk.LEFT, padx=10, pady=10)
        self.loading_spinner.hide()
        
        # Zone de filtres et recherche
        self.filter_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.filter_frame.pack(fill=ctk.X, padx=15, pady=(0, 10))
        
        # Champ de recherche
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)
        
        search_container = ctk.CTkFrame(self.filter_frame, fg_color=self.colors["card_bg"], corner_radius=8)
        search_container.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=(0, 10))
        
        search_icon = ctk.CTkLabel(
            search_container,
            text="🔍",
            width=30,
            font=ctk.CTkFont(size=14)
        )
        search_icon.pack(side=ctk.LEFT, padx=(10, 0))
        
        self.search_entry = ctk.CTkEntry(
            search_container,
            placeholder_text="Rechercher dans les résultats...",
            textvariable=self.search_var,
            border_width=0,
            fg_color="transparent",
            height=36
        )
        self.search_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5, pady=5)
        
        # Bouton de réinitialisation de recherche
        self.clear_search_btn = ctk.CTkButton(
            search_container,
            text="✕",
            width=30,
            height=30,
            corner_radius=15,
            fg_color=self.colors["subtle_text"],
            hover_color=self.colors["danger"],
            text_color=self.colors["text"],
            command=self._clear_search
        )
        self.clear_search_btn.pack(side=ctk.RIGHT, padx=5, pady=5)
        
        # Zone principale de contenu avec design moderne
        content_container = ctk.CTkFrame(self.frame, fg_color="transparent")
        content_container.pack(fill=ctk.BOTH, expand=True, padx=15, pady=5)
        
        # Panel latéral pour l'historique et la navigation
        self.sidebar = ctk.CTkFrame(content_container, width=250, fg_color=self.colors["card_bg"], corner_radius=10)
        self.sidebar.pack(side=ctk.LEFT, fill=ctk.Y, padx=(0, 15), pady=0)
        
        # En-tête du panel latéral
        sidebar_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        sidebar_header.pack(fill=ctk.X, padx=10, pady=10)
        
        sidebar_title = ctk.CTkLabel(
            sidebar_header,
            text="Historique des analyses",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors["text"]
        )
        sidebar_title.pack(side=ctk.LEFT)
        
        # Liste des documents analysés
        self.history_container = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            corner_radius=0
        )
        self.history_container.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        
        # Message initial pour l'historique
        self.no_history_label = ctk.CTkLabel(
            self.history_container,
            text="Aucun document analysé récemment.",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["subtle_text"],
            wraplength=220
        )
        self.no_history_label.pack(pady=20)
        
        # Frame principal de contenu
        self.content_frame = ctk.CTkScrollableFrame(
            content_container,
            fg_color=self.colors["card_bg"],
            corner_radius=10
        )
        self.content_frame.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True)
        
        # Message de bienvenue avec instructions
        self.welcome_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.welcome_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        welcome_icon = ctk.CTkLabel(
            self.welcome_frame,
            text="📄",
            font=ctk.CTkFont(size=48),
            text_color=self.colors["primary"]
        )
        welcome_icon.pack(pady=(40, 10))
        
        welcome_title = ctk.CTkLabel(
            self.welcome_frame,
            text="Bienvenue dans l'analyseur de documents",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text"]
        )
        welcome_title.pack(pady=(0, 20))
        
        welcome_text = ctk.CTkLabel(
            self.welcome_frame,
            text="Sélectionnez un document à analyser pour extraire automatiquement les informations pertinentes.",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text"],
            wraplength=400
        )
        welcome_text.pack(pady=(0, 10))
        
        # Options rapides
        quick_options = ctk.CTkFrame(self.welcome_frame, fg_color="transparent")
        quick_options.pack(pady=30)
        
        quick_analyze_btn = ctk.CTkButton(
            quick_options,
            text="Analyser un document",
            command=self.analyze_document,
            width=200,
            height=40,
            corner_radius=8,
            fg_color=self.colors["primary"],
            text_color=self.colors["text"]
        )
        quick_analyze_btn.pack(side=ctk.LEFT, padx=10)
        
        quick_batch_btn = ctk.CTkButton(
            quick_options,
            text="Analyse par lot",
            command=self.batch_analyze,
            width=200,
            height=40,
            corner_radius=8,
            fg_color=self.colors["info"],
            text_color=self.colors["text"]
        )
        quick_batch_btn.pack(side=ctk.LEFT, padx=10)
        
        # Zone des résultats (initialement cachée)
        self.results_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        # Barre d'état moderne
        self.status_bar = ctk.CTkFrame(
            self.frame,
            height=32,
            fg_color=self.colors["card_bg"],
            corner_radius=10
        )
        self.status_bar.pack(side=ctk.BOTTOM, fill=ctk.X, padx=15, pady=15)
        
        self.status_icon = ctk.CTkLabel(
            self.status_bar,
            text="✓",
            width=20,
            font=ctk.CTkFont(size=13),
            text_color=self.colors["success"]
        )
        self.status_icon.pack(side=ctk.LEFT, padx=(10, 0))
        
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Prêt",
            font=ctk.CTkFont(size=12),
            anchor="w",
            text_color=self.colors["text"]
        )
        self.status_label.pack(side=ctk.LEFT, padx=5, pady=5, fill=ctk.X, expand=True)
        
        # Compteur de documents
        self.doc_counter = ctk.CTkLabel(
            self.status_bar,
            text="0 documents analysés",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["subtle_text"]
        )
        self.doc_counter.pack(side=ctk.RIGHT, padx=10, pady=5)
    
    def _on_search_changed(self, *args):
        """Gère les changements dans le champ de recherche"""
        search_text = self.search_var.get().strip().lower()
        if hasattr(self, 'active_results_widgets'):
            for widget in self.active_results_widgets:
                if hasattr(widget, 'filter_by_text'):
                    widget.filter_by_text(search_text)
    
    def _clear_search(self):
        """Efface le champ de recherche"""
        self.search_var.set("")
        self.search_entry.focus_set()
    
    def analyze_document(self):
        """
        Lance l'analyse d'un document avec interface moderne
        et gestion avancée des erreurs
        """
        try:
            # Ouvrir la boîte de dialogue de sélection de fichier
            file_path = ctk.filedialog.askopenfilename(
                title="Sélectionner un document à analyser",
                filetypes=[
                    ("Documents", "*.pdf;*.doc;*.docx;*.txt"),
                    ("PDF", "*.pdf"),
                    ("Word", "*.doc;*.docx"),
                    ("Texte", "*.txt"),
                    ("Tous les fichiers", "*.*")
                ]
            )
            
            if not file_path:
                return  # L'utilisateur a annulé
            
            # Masquer le cadre de bienvenue
            self.welcome_frame.pack_forget()
            
            # Préparer la vue pour l'analyse
            self._prepare_analysis_view(file_path)
            
            # Lancer l'analyse dans un thread séparé
            self._run_analysis(file_path)
            
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du document: {e}")
            self.show_error(
                "Erreur",
                "Une erreur est survenue lors de la sélection du document.",
                str(e)
            )
            self.show_loading(False)
    
    def _prepare_analysis_view(self, file_path):
        """Prépare l'interface pour afficher l'analyse en cours"""
        # Effacer les résultats précédents
        for widget in self.content_frame.winfo_children():
            widget.pack_forget()
        
        # Créer un cadre pour l'analyse en cours
        analysis_progress_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent"
        )
        analysis_progress_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Nom du fichier
        filename = os.path.basename(file_path)
        file_label = ctk.CTkLabel(
            analysis_progress_frame,
            text=f"Analyse de document en cours",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text"]
        )
        file_label.pack(pady=(40, 5))
        
        filename_label = ctk.CTkLabel(
            analysis_progress_frame,
            text=filename,
            font=ctk.CTkFont(size=14),
            text_color=self.colors["primary"]
        )
        filename_label.pack(pady=(0, 20))
        
        # Indicateur de progression indéterminé
        progress_container = ctk.CTkFrame(analysis_progress_frame, fg_color="transparent")
        progress_container.pack(pady=10)
        
        progress_bar = ctk.CTkProgressBar(
            progress_container,
            width=300,
            height=15,
            corner_radius=7,
            fg_color=self.colors["subtle_text"],
            progress_color=self.colors["primary"]
        )
        progress_bar.pack(pady=10)
        progress_bar.start()  # Animation indéterminée
        
        # Message d'attente
        status_message = ctk.CTkLabel(
            analysis_progress_frame,
            text="Extraction et analyse des données du document...",
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text"]
        )
        status_message.pack(pady=5)
        
        # Stocker les références pour mise à jour
        self.current_progress_frame = analysis_progress_frame
        self.current_progress_bar = progress_bar
        self.current_status_message = status_message
        
        # Afficher le chargement dans la barre d'outils
        self.show_loading(True)
        
        # Mettre à jour le statut
        filename = os.path.basename(file_path)
        self.update_status(f"Analyse de {filename} en cours...", "info")
    
    def _run_analysis(self, file_path: str):
        """
        Exécute l'analyse du document dans un thread séparé
        en utilisant les différents extracteurs et reconnaisseurs
        """
        self.is_analyzing = True
        self.toggle_buttons_state()
        
        def analyze_task():
            start_time = time.time()
            try:
                # Initialiser les composants d'analyse
                ocr = OCRProcessor()
                text_processor = TextProcessor()
                validator = DataValidator()
                
                # Extracteurs spécialisés
                personal_extractor = PersonalDataExtractor()
                legal_extractor = LegalDocsExtractor()
                identity_extractor = IdentityDocExtractor()
                contract_extractor = ContractExtractor()
                business_extractor = BusinessDocExtractor()
                
                # Reconnaisseurs
                phone_recognizer = PhoneRecognizer()
                name_recognizer = NameRecognizer()
                id_recognizer = IDRecognizer()
                address_recognizer = AddressRecognizer()
                
                # Étapes d'analyse avec feedback
                steps = [
                    ("Lecture du document...", lambda: ocr.process_document(file_path)),
                    ("Extraction du contenu...", lambda: text_processor.process_text(ocr.get_text())),
                    ("Analyse de la structure...", lambda: text_processor.analyze_document_structure(ocr.get_text())),
                    ("Identification des métadonnées...", lambda: {
                        'metadata': {
                            'filename': os.path.basename(file_path),
                            'size': os.path.getsize(file_path),
                            'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        }
                    }),
                    ("Extraction des données personnelles...", lambda: personal_extractor.extract(ocr.get_text())),
                    ("Analyse des aspects légaux...", lambda: legal_extractor.extract(ocr.get_text())),
                    ("Vérification des documents d'identité...", lambda: identity_extractor.extract(ocr.get_text())),
                    ("Analyse des contrats...", lambda: contract_extractor.extract(ocr.get_text())),
                    ("Analyse des documents commerciaux...", lambda: business_extractor.extract(ocr.get_text())),
                    ("Reconnaissance des numéros...", lambda: phone_recognizer.recognize(ocr.get_text())),
                    ("Reconnaissance des noms...", lambda: name_recognizer.recognize(ocr.get_text())),
                    ("Reconnaissance des identifiants...", lambda: id_recognizer.recognize(ocr.get_text())),
                    ("Reconnaissance des adresses...", lambda: address_recognizer.recognize(ocr.get_text())),
                    ("Validation des données...", lambda: validator.validate_all_data({
                        'personal': personal_extractor.get_results(),
                        'legal': legal_extractor.get_results(),
                        'identity': identity_extractor.get_results(),
                        'contract': contract_extractor.get_results(),
                        'business': business_extractor.get_results(),
                        'phone': phone_recognizer.get_results(),
                        'name': name_recognizer.get_results(),
                        'id': id_recognizer.get_results(),
                        'address': address_recognizer.get_results()
                    }))
                ]
                
                results = {'file_path': file_path}
                
                for step_name, step_func in steps:
                    # Mise à jour du message dans le thread principal
                    self.frame.after(0, lambda s=step_name: self._update_analysis_status(s))
                    # Exécuter l'étape
                    step_result = step_func()
                    if step_result:
                        results.update(step_result)
                
                if results:
                    # Ajouter à l'historique
                    self._add_to_history(file_path, results)
                    
                    # Mettre à jour l'interface dans le thread principal
                    elapsed_time = time.time() - start_time
                    self.frame.after(0, lambda: self._complete_analysis(results, elapsed_time))
                else:
                    self.frame.after(0, lambda: self.show_error(
                        "Pas de résultats",
                        "Aucun résultat n'a été généré pour ce document.",
                        "Vérifiez que le document est dans un format supporté."
                    ))
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse de {file_path}: {e}")
                self.frame.after(0, lambda: self.show_error(
                    "Erreur d'analyse",
                    "Une erreur est survenue lors de l'analyse du document.",
                    str(e)
                ))
            finally:
                self.frame.after(0, lambda: self._finalize_analysis())
        
        # Lancer l'analyse dans un thread
        analysis_thread = threading.Thread(target=analyze_task)
        analysis_thread.daemon = True
        analysis_thread.start()
    
    def _update_analysis_status(self, message):
        """Met à jour le message de statut pendant l'analyse"""
        if hasattr(self, 'current_status_message'):
            self.current_status_message.configure(text=message)
            self.update_status(message, "info")
    
    def _complete_analysis(self, results, elapsed_time):
        """Affiche les résultats de l'analyse"""
        # Nettoyer la vue d'analyse en cours
        if hasattr(self, 'current_progress_frame'):
            self.current_progress_frame.destroy()
        
        # Afficher le formulaire de modèle
        self._show_template_form(results)
        
        # Mettre à jour le compteur
        self._update_document_counter()
    
    def _finalize_analysis(self):
        """Finalise le processus d'analyse"""
        self.is_analyzing = False
        self.show_loading(False)
        self.toggle_buttons_state()
    
    def _add_to_history(self, file_path, results):
        """Ajoute un document à l'historique des analyses"""
        # Supprimer le message "aucun historique" si présent
        if hasattr(self, 'no_history_label'):
            self.no_history_label.pack_forget()
        
        # Créer un élément d'historique
        history_item = self._create_history_item(file_path, results)
        
        # Ajouter aux résultats en mémoire
        self.analysis_history.insert(0, {
            "file_path": file_path,
            "results": results,
            "timestamp": datetime.now(),
            "widget": history_item
        })
        
        # Limiter l'historique à 10 éléments
        if len(self.analysis_history) > 10:
            old_item = self.analysis_history.pop()
            if 'widget' in old_item and old_item['widget']:
                old_item['widget'].destroy()
    
    def _create_history_item(self, file_path, results):
        """Crée un élément d'historique dans le sidebar"""
        filename = os.path.basename(file_path)
        
        # Container pour l'élément
        item_frame = ctk.CTkFrame(
            self.history_container,
            fg_color=self.colors["light_bg"],
            corner_radius=8
        )
        item_frame.pack(fill=ctk.X, pady=5, padx=5)
        
        # Icône selon le type de fichier
        icon = "📄"
        if file_path.lower().endswith('.pdf'):
            icon = "📕"
        elif file_path.lower().endswith(('.doc', '.docx')):
            icon = "📘"
        elif file_path.lower().endswith('.txt'):
            icon = "📝"
        
        icon_label = ctk.CTkLabel(
            item_frame,
            text=icon,
            font=ctk.CTkFont(size=16),
            width=25
        )
        icon_label.pack(side=ctk.LEFT, padx=5, pady=8)
        
        # Nom du fichier tronqué si trop long
        short_name = filename
        if len(filename) > 20:
            short_name = filename[:17] + "..."
        
        name_label = ctk.CTkLabel(
            item_frame,
            text=short_name,
            font=ctk.CTkFont(size=12),
            anchor="w",
            width=150
        )
        name_label.pack(side=ctk.LEFT, padx=5, pady=8, fill=ctk.X, expand=True)
        
        # Action au clic
        def on_click(event=None):
            self.display_results(results)
        
        # Rendre cliquable
        item_frame.bind("<Button-1>", on_click)
        icon_label.bind("<Button-1>", on_click)
        name_label.bind("<Button-1>", on_click)
        
        # Effet hover
        def on_enter(event=None):
            item_frame.configure(fg_color=self.colors["primary"])
            name_label.configure(text_color=self.colors["text"])
        
        def on_leave(event=None):
            item_frame.configure(fg_color=self.colors["light_bg"])
            name_label.configure(text_color=self.colors["text"])
        
        item_frame.bind("<Enter>", on_enter)
        item_frame.bind("<Leave>", on_leave)
        icon_label.bind("<Enter>", on_enter)
        icon_label.bind("<Leave>", on_leave)
        name_label.bind("<Enter>", on_enter)
        name_label.bind("<Leave>", on_leave)
        
        return item_frame    
    def batch_analyze(self):
        """
        Lance l'analyse par lot de documents avec une interface
        moderne et informative
        """
        if not self._analyzer_ready:
            self.show_error(
                "Analyseur non disponible",
                "L'analyseur de documents n'est pas initialisé correctement.",
                "Vérifiez que toutes les dépendances sont installées."
            )
            return
        
        try:
            # Ouvrir la boîte de dialogue de sélection de fichiers
            file_paths = ctk.filedialog.askopenfilenames(
                title="Sélectionner les documents à analyser",
                filetypes=[
                    ("Documents", "*.pdf;*.doc;*.docx;*.txt"),
                    ("PDF", "*.pdf"),
                    ("Word", "*.doc;*.docx"),
                    ("Texte", "*.txt"),
                    ("Tous les fichiers", "*.*")
                ]
            )
            
            if not file_paths or len(file_paths) == 0:
                return  # L'utilisateur a annulé
            
            # Masquer l'écran de bienvenue
            self.welcome_frame.pack_forget()
            
            # Préparer la vue par lot
            self._prepare_batch_view(file_paths)
            
            # Lancer l'analyse par lot
            self._run_batch_analysis(file_paths)
            
        except Exception as e:
            logger.error(f"Erreur lors de la sélection des documents: {e}")
            self.show_error(
                "Erreur",
                "Une erreur est survenue lors de la sélection des documents.",
                str(e)
            )
            self.show_loading(False)
    
    def _prepare_batch_view(self, file_paths):
        """
        Prépare l'interface pour l'analyse par lot
        """
        # Nettoyer la vue
        for widget in self.content_frame.winfo_children():
            widget.pack_forget()
        
        # Créer un cadre pour le traitement par lot
        batch_frame = ctk.CTkFrame(
            self.content_frame,
            fg_color="transparent"
        )
        batch_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # En-tête du traitement par lot
        header = ctk.CTkFrame(batch_frame, fg_color="transparent")
        header.pack(fill=ctk.X, pady=(0, 15))
        
        header_label = ctk.CTkLabel(
            header,
            text="Analyse par lot",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text"]
        )
        header_label.pack(side=ctk.LEFT)
        
        files_count = ctk.CTkLabel(
            header,
            text=f"{len(file_paths)} documents sélectionnés",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["subtle_text"]
        )
        files_count.pack(side=ctk.LEFT, padx=15)
        
        # Barre de progression globale
        progress_frame = ctk.CTkFrame(batch_frame, fg_color="transparent")
        progress_frame.pack(fill=ctk.X, pady=10)
        
        progress_label = ctk.CTkLabel(
            progress_frame,
            text="Progression totale:",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text"]
        )
        progress_label.pack(side=ctk.LEFT, padx=(0, 10))
        
        progress_bar = ctk.CTkProgressBar(
            progress_frame,
            width=400,
            height=15,
            corner_radius=7,
            fg_color=self.colors["subtle_text"],
            progress_color=self.colors["primary"]
        )
        progress_bar.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5)
        progress_bar.set(0)
        
        progress_percentage = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text"],
            width=40
        )
        progress_percentage.pack(side=ctk.LEFT, padx=5)
        
        # Statut actuel
        current_file_frame = ctk.CTkFrame(batch_frame, fg_color="transparent")
        current_file_frame.pack(fill=ctk.X, pady=5)
        
        current_label = ctk.CTkLabel(
            current_file_frame,
            text="Document en cours:",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text"]
        )
        current_label.pack(side=ctk.LEFT, padx=(0, 10))
        
        current_file = ctk.CTkLabel(
            current_file_frame,
            text="En attente...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["primary"]
        )
        current_file.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
        
        # Tableau des fichiers à traiter
        files_container_frame = ctk.CTkFrame(batch_frame, fg_color=self.colors["card_bg"], corner_radius=10)
        files_container_frame.pack(fill=ctk.BOTH, expand=True, pady=15)
        
        # En-tête du tableau
        table_header = ctk.CTkFrame(files_container_frame, fg_color=self.colors["light_bg"], corner_radius=0)
        table_header.pack(fill=ctk.X, padx=1, pady=1)
        
        ctk.CTkLabel(
            table_header,
            text="Document",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"],
            width=300
        ).pack(side=ctk.LEFT, padx=10, pady=8)
        
        ctk.CTkLabel(
            table_header,
            text="Statut",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"],
            width=100
        ).pack(side=ctk.LEFT, padx=10, pady=8)
        
        ctk.CTkLabel(
            table_header,
            text="Actions",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text"],
            width=100
        ).pack(side=ctk.LEFT, padx=10, pady=8)
        
        # Liste des fichiers
        files_list = ctk.CTkScrollableFrame(
            files_container_frame,
            fg_color="transparent",
            corner_radius=0
        )
        files_list.pack(fill=ctk.BOTH, expand=True)
        
        # Créer une entrée pour chaque fichier
        file_widgets = {}
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            
            file_row = ctk.CTkFrame(files_list, fg_color="transparent")
            file_row.pack(fill=ctk.X, pady=1)
            
            # Ajouter une ligne séparatrice
            separator = ctk.CTkFrame(files_list, height=1, fg_color=self.colors["light_bg"])
            separator.pack(fill=ctk.X)
            
            # Icône selon le type de fichier
            icon = "📄"
            if file_path.lower().endswith('.pdf'):
                icon = "📕"
            elif file_path.lower().endswith(('.doc', '.docx')):
                icon = "📘"
            elif file_path.lower().endswith('.txt'):
                icon = "📝"
            
            # Container pour le nom avec icône
            name_container = ctk.CTkFrame(file_row, fg_color="transparent", width=300)
            name_container.pack(side=ctk.LEFT, fill=ctk.Y, padx=10, pady=8)
            name_container.pack_propagate(False)
            
            icon_label = ctk.CTkLabel(
                name_container,
                text=icon,
                font=ctk.CTkFont(size=14),
                width=20
            )
            icon_label.pack(side=ctk.LEFT)
            
            name_label = ctk.CTkLabel(
                name_container,
                text=filename if len(filename) < 35 else filename[:32] + "...",
                font=ctk.CTkFont(size=12),
                anchor="w"
            )
            name_label.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
            
            # Statut
            status_container = ctk.CTkFrame(file_row, fg_color="transparent", width=100)
            status_container.pack(side=ctk.LEFT, fill=ctk.Y, padx=10, pady=8)
            status_container.pack_propagate(False)
            
            status_label = ctk.CTkLabel(
                status_container,
                text="En attente",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["subtle_text"]
            )
            status_label.pack(fill=ctk.BOTH, expand=True)
            
            # Actions
            actions_container = ctk.CTkFrame(file_row, fg_color="transparent", width=100)
            actions_container.pack(side=ctk.LEFT, fill=ctk.Y, padx=10, pady=5)
            actions_container.pack_propagate(False)
            
            # Le bouton sera ajouté dynamiquement quand les résultats seront disponibles
            
            # Stocker les widgets pour mise à jour
            file_widgets[file_path] = {
                "row": file_row,
                "status": status_label,
                "actions": actions_container
            }
        
        # Stocker les références pour mise à jour
        self.batch_frame = batch_frame
        self.batch_progress = {
            "bar": progress_bar,
            "percentage": progress_percentage,
            "current_file": current_file
        }
        self.batch_files = file_widgets
        
        # Afficher le chargement dans la barre d'outils
        self.show_loading(True)
        
        # Mettre à jour le statut
        self.update_status(f"Préparation de l'analyse de {len(file_paths)} documents...", "info")
    
    def _run_batch_analysis(self, file_paths):
        """
        Exécute l'analyse par lot dans un thread séparé
        et gère les mises à jour de l'interface
        """
        self.is_analyzing = True
        self.toggle_buttons_state()
        
        def batch_task():
            batch_results = []
            total_files = len(file_paths)
            processed = 0
            
            try:
                for idx, file_path in enumerate(file_paths):
                    filename = os.path.basename(file_path)
                    
                    # Mettre à jour l'interface dans le thread principal
                    self.frame.after(0, lambda f=filename, i=idx, t=total_files: self._update_batch_progress(f, i, t))
                    
                    # Analyser le document
                    try:
                        # Mettre à jour le statut du fichier
                        self.frame.after(0, lambda p=file_path: self._update_file_status(p, "En cours", "info"))
                        
                        # Exécuter l'analyse
                        results = self.doc_analyzer.analyze_document(file_path)
                        
                        if results:
                            # Stocker les résultats
                            batch_results.append(results)
                            
                            # Mettre à jour dans le thread principal
                            self.frame.after(0, lambda p=file_path, r=results: self._update_file_success(p, r))
                        else:
                            # Échec de l'analyse
                            self.frame.after(0, lambda p=file_path: self._update_file_status(p, "Aucun résultat", "warning"))
                    except Exception as e:
                        logger.error(f"Erreur lors de l'analyse de {file_path}: {e}")
                        # Mettre à jour le statut
                        self.frame.after(0, lambda p=file_path: self._update_file_status(p, "Erreur", "error"))
                    
                    processed += 1
                
                # Finaliser le traitement
                self.frame.after(0, lambda r=batch_results, t=total_files, p=processed: self._complete_batch_analysis(r, t, p))
                
            except Exception as e:
                logger.error(f"Erreur globale lors de l'analyse par lot: {e}")
                self.frame.after(0, lambda: self.show_error(
                    "Erreur d'analyse par lot",
                    "Une erreur est survenue lors de l'analyse par lot.",
                    str(e)
                ))
                self.frame.after(0, lambda: self._finalize_analysis())
        
        # Lancer l'analyse dans un thread
        batch_thread = threading.Thread(target=batch_task)
        batch_thread.daemon = True
        batch_thread.start()
    
    def _update_batch_progress(self, filename, index, total):
        """Met à jour la progression du traitement par lot"""
        progress = (index + 1) / total
        
        # Mettre à jour la barre de progression
        self.batch_progress["bar"].set(progress)
        self.batch_progress["percentage"].configure(text=f"{int(progress * 100)}%")
        self.batch_progress["current_file"].configure(text=filename)
        
        # Mettre à jour le statut
        self.update_status(f"Analyse de {filename} ({index + 1}/{total})", "info")
    
    def _update_file_status(self, file_path, status, status_type="info"):
        """Met à jour le statut d'un fichier dans la liste"""
        if file_path in self.batch_files:
            # Couleur selon le type de statut
            color = self.colors["subtle_text"]  # Défaut
            if status_type == "info":
                color = self.colors["info"]
            elif status_type == "success":
                color = self.colors["success"]
            elif status_type == "warning":
                color = self.colors["warning"]
            elif status_type == "error":
                color = self.colors["danger"]
            
            self.batch_files[file_path]["status"].configure(
                text=status,
                text_color=color
            )
    
    def _update_file_success(self, file_path, results):
        """Met à jour l'interface quand un fichier est analysé avec succès"""
        if file_path in self.batch_files:
            # Mettre à jour le statut
            self._update_file_status(file_path, "Succès", "success")
            
            # Ajouter à l'historique
            self._add_to_history(file_path, results)
            
            # Ajouter un bouton de détails
            view_btn = ctk.CTkButton(
                self.batch_files[file_path]["actions"],
                text="Détails",
                command=lambda r=results: self.display_results(r),
                width=80,
                height=24,
                corner_radius=6,
                font=ctk.CTkFont(size=11)
            )
            view_btn.pack(fill=ctk.X)
    
    def _complete_batch_analysis(self, results, total, processed):
        """Finalise l'analyse par lot"""
        # Mettre à jour l'en-tête du tableau
        if hasattr(self, 'batch_frame'):
            # Trouver l'en-tête et le mettre à jour
            for widget in self.batch_frame.winfo_children():
                if isinstance(widget, ctk.CTkFrame) and not hasattr(widget, 'children'):
                    # C'est probablement l'en-tête
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkLabel) and child.cget("text") == "Analyse par lot":
                            child.configure(text=f"Analyse par lot terminée")
                            break
        
        # Mettre à jour le statut
        success_count = len(results)
        self.update_status(
            f"Analyse par lot terminée: {success_count}/{total} documents traités avec succès",
            "success" if success_count == total else "warning"
        )
        
        # Mettre à jour le compteur
        self._update_document_counter(success_count)
        
        # Terminer l'analyse
        self._finalize_analysis()
    
    def display_results(self, results, elapsed_time=None):
        """
        Affiche les résultats d'analyse de manière professionnelle et moderne
        
        Args:
            results: Résultats de l'analyse
            elapsed_time: Temps écoulé pour l'analyse (optionnel)
        """
        from doc_analyzer.ui.analysis_widgets import AnalysisResultWidget
        
        # Nettoyer la vue actuelle
        for widget in self.content_frame.winfo_children():
            widget.pack_forget()
        
        # Créer un cadre pour les résultats
        results_main_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        results_main_frame.pack(fill=ctk.BOTH, expand=True)
        
        # En-tête des résultats
        header_frame = ctk.CTkFrame(results_main_frame, fg_color=self.colors["light_bg"], corner_radius=10)
        header_frame.pack(fill=ctk.X, padx=10, pady=(10, 15))
        
        # Titre avec nom du fichier
        filename = os.path.basename(results.get('file_path', 'Document'))
        header_title = ctk.CTkLabel(
            header_frame,
            text=f"Résultats d'analyse: {filename}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text"]
        )
        header_title.pack(side=ctk.LEFT, padx=15, pady=10)
        
        # Afficher le temps d'analyse si disponible
        if elapsed_time is not None:
            time_label = ctk.CTkLabel(
                header_frame,
                text=f"Temps d'analyse: {elapsed_time:.2f} secondes",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["subtle_text"]
            )
            time_label.pack(side=ctk.LEFT, padx=15, pady=10)
        
        # Bouton d'export
        export_btn = ctk.CTkButton(
            header_frame,
            text="📥 Exporter",
            command=lambda: self._export_results(results),
            width=120,
            height=28,
            corner_radius=6
        )
        export_btn.pack(side=ctk.RIGHT, padx=15, pady=10)
        
        # Onglets des résultats
        tabs_frame = ctk.CTkFrame(results_main_frame, fg_color="transparent")
        tabs_frame.pack(fill=ctk.X, padx=10, pady=(0, 10))
        
        # Conteneur pour le contenu des onglets
        tab_content = ctk.CTkFrame(results_main_frame, fg_color=self.colors["card_bg"], corner_radius=10)
        tab_content.pack(fill=ctk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Filtrer pour ne conserver que les résultats d'analyse
        analysis_results = {k: v for k, v in results.items() if k != 'file_path'}
        
        # Variables pour gérer les onglets
        self.active_tab = None
        self.tab_buttons = {}
        self.tab_frames = {}
        self.active_results_widgets = []
        
        # Vérifier s'il y a des résultats
        if not analysis_results:
            no_results = ctk.CTkLabel(
                tab_content,
                text="Aucun résultat d'analyse disponible pour ce document.",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["subtle_text"]
            )
            no_results.pack(pady=40)
        else:
            # Créer les onglets et leur contenu
            for i, (analysis_type, result) in enumerate(analysis_results.items()):
                # Créer un bouton d'onglet
                tab_btn = self._create_tab_button(tabs_frame, analysis_type, i == 0)
                tab_btn.pack(side=ctk.LEFT, padx=5, pady=5)
                
                # Créer le contenu de l'onglet
                tab_frame = ctk.CTkFrame(tab_content, fg_color=self.colors["card_bg"], corner_radius=10)
                tab_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
                
                # Créer le widget d'analyse
                analysis_widget = AnalysisResultWidget(tab_frame, result)
                analysis_widget.pack(fill=ctk.BOTH, expand=True)
                
                # Stocker les références
                self.tab_frames[analysis_type] = tab_frame
                self.active_results_widgets.append(analysis_widget)
                
                # Connecter le bouton d'onglet au contenu
                tab_btn.configure(command=lambda t=tab_frame: self._switch_tab(t))
        
        # Mettre à jour les onglets actifs
        self._update_active_tabs()
    
    def _create_tab_button(self, parent, text, is_active):
        """Crée un bouton d'onglet"""
        btn = ctk.CTkButton(
            parent,
            text=text,
            width=100,
            height=30,
            corner_radius=6,
            fg_color=self.colors["primary"] if is_active else self.colors["subtle_text"],
            text_color=self.colors["text"],
            command=lambda: self._switch_tab(self.tab_frames[text])
        )
        return btn
    
    def _switch_tab(self, tab_frame):
        """Basculer vers un onglet"""
        # Masquer tous les onglets
        for frame in self.tab_frames.values():
            frame.pack_forget()
        
        # Afficher le onglet sélectionné
        tab_frame.pack(fill=ctk.BOTH, expand=True)
        
        # Mettre à jour les onglets actifs
        self._update_active_tabs()
    
    def _update_active_tabs(self):
        """Met à jour les onglets actifs"""
        for tab_btn in self.tab_buttons.values():
            tab_btn.configure(fg_color=self.colors["primary"] if tab_btn.cget("command")() is self.tab_frames[tab_btn.cget("text")] else self.colors["subtle_text"])
    
    def _update_document_counter(self, count=1):
        """Met à jour le compteur de documents"""
        current_count = int(self.doc_counter.cget("text").split()[0])
        self.doc_counter.configure(text=f"{current_count + count} documents analysés")
    
    def _export_results(self, results):
        """Exporte les résultats d'analyse"""
        # Implémentation de l'exportation des résultats
        pass

    def _show_template_form(self, results):
        """
        Affiche le formulaire de modèle avec les résultats d'analyse
        
        Args:
            results: Résultats de l'analyse
        """
        try:
            # Créer les données pour le modèle
            filename = os.path.basename(results.get('file_path', 'Document'))
            template_data = {
                "name": os.path.splitext(filename)[0],
                "type": "document",
                "description": "Document analysé automatiquement",
                "content": results.get('text', ''),  # Contenu extrait du document
                "variables": []
            }
            
            # Extraire les variables des résultats
            for analysis_type, result in results.items():
                if isinstance(result, dict) and analysis_type != 'file_path':
                    for key, value in result.items():
                        if isinstance(value, str):
                            var_name = f"{analysis_type}_{key}".lower()
                            template_data["variables"].append(var_name)
                            # Remplacer la valeur dans le contenu par la variable
                            if value in template_data["content"]:
                                template_data["content"] = template_data["content"].replace(
                                    value,
                                    "{{" + var_name + "}}"  # Utiliser la concaténation au lieu de f-string
                                )
            
            # Créer le formulaire de modèle avec les résultats
            from views.template_view import TemplateFormView
            template_form = TemplateFormView(
                self.parent,
                self.model,
                template_data=template_data,
                update_view_callback=self.update_view
            )
            
            # Mettre à jour le statut
            self.update_status("Analyse terminée, vous pouvez maintenant éditer et sauvegarder le modèle", "success")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du formulaire de modèle: {e}")
            self.show_error(
                "Erreur",
                "Une erreur est survenue lors de l'affichage du formulaire de modèle.",
                str(e)
            )
