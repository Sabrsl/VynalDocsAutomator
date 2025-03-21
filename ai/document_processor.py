#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de traitement des documents avec l'IA
Utilise Llama pour l'analyse et la personnalisation des documents
"""

import logging
import json
import os
import re
import chardet
import requests
import time
from typing import Dict, List, Optional, Tuple, Any

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger("VynalDocsAutomator.AIDocumentProcessor")

class AIDocumentProcessor:
    """
    Classe pour le traitement des documents avec l'IA
    Utilise Llama pour analyser et personnaliser les documents
    """
    
    def __init__(self):
        """
        Initialise le processeur de documents
        """
        self.config = self._load_config()
        self.cache = {}
        self.cache_size = 100  # Réduit de 1000 à 100
        self.fallback_mode = False  # Ajout de l'attribut fallback_mode initialisé à False
        
    def _load_config(self):
        """
        Charge la configuration depuis le fichier config.json
        Gère les différents encodages pour éviter les problèmes de décodage
        """
        try:
            # Utiliser le chemin absolu pour éviter les problèmes de chemin relatif
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "ai_config.json")
            logger.info(f"Tentative de chargement de la configuration depuis: {config_path}")
            
            if not os.path.exists(config_path):
                logger.warning(f"Le fichier de configuration n'existe pas: {config_path}")
                # Si le fichier n'existe pas, retourner une configuration par défaut
                return {
                    "api_url": "http://localhost:11434/api/generate",
                    "model": "mistral:latest",
                    "options": {
                        "temperature": 0.7,
                        "max_tokens": 512
                    }
                }
            
            # Essayer différents encodages
            encodings = ['utf-8', 'latin-1', 'cp1252', 'utf-16', 'utf-16-le', 'utf-16-be']
            
            for encoding in encodings:
                try:
                    with open(config_path, 'r', encoding=encoding) as f:
                        config = json.load(f)
                    logger.info(f"Configuration chargée avec l'encodage {encoding} depuis {config_path}")
                    return config
                except UnicodeDecodeError:
                    logger.debug(f"Échec du décodage avec l'encodage {encoding}")
                    continue  # Essayer le prochain encodage
                except json.JSONDecodeError:
                    # Si le fichier s'ouvre mais que le JSON est invalide
                    logger.warning(f"Format JSON invalide dans le fichier de configuration avec l'encodage {encoding}")
                    continue
            
            # Si on arrive ici, tous les encodages ont échoué
            # Essai en mode binaire avec détection d'encodage
            logger.warning("Tous les encodages standards ont échoué, tentative de détection automatique")
            import chardet
            try:
                with open(config_path, 'rb') as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    detected_encoding = result['encoding']
                    logger.info(f"Encodage détecté: {detected_encoding} (confiance: {result['confidence']})")
                    
                    if detected_encoding:
                        try:
                            config_str = raw_data.decode(detected_encoding)
                            config = json.loads(config_str)
                            logger.info(f"Configuration chargée avec l'encodage détecté {detected_encoding}")
                            return config
                        except Exception as e:
                            logger.warning(f"Échec avec l'encodage détecté {detected_encoding}: {e}")
            except Exception as e:
                logger.warning(f"Échec de la détection d'encodage: {e}")
                
            # Créer une nouvelle configuration par défaut
            logger.warning("Création d'une nouvelle configuration par défaut")
            config = {
                "api_url": "http://localhost:11434/api/generate",
                "model": "mistral:latest",
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 512
                }
            }
            
            # Essayer de sauvegarder cette configuration
            try:
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                logger.info("Nouvelle configuration par défaut créée")
            except Exception as e:
                logger.error(f"Impossible de créer la configuration par défaut: {e}")
                
            return config
            
        except Exception as e:
            logger.warning(f"Impossible de charger la configuration: {e}")
            # Configuration par défaut
            return {
                "api_url": "http://localhost:11434/api/generate",
                "model": "mistral:latest",
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 512
                }
            }
        
    def _read_file_safely(self, file_path: str) -> str:
        """
        Lit un fichier en détectant automatiquement l'encodage
        
        Args:
            file_path: Chemin vers le fichier à lire
            
        Returns:
            Contenu du fichier
        """
        try:
            # Détecter le type de fichier par l'extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # Fichiers PDF
            if ext == '.pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        return " ".join([page.extract_text() for page in reader.pages])
                except ImportError:
                    logger.warning("PyPDF2 non disponible, traitement du PDF en tant que fichier binaire")
                    return f"[PDF NON SUPPORTÉ: {os.path.basename(file_path)}]"
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture du PDF: {e}")
                    return f"[ERREUR PDF: {os.path.basename(file_path)}]"
            
            # Fichiers DOCX
            elif ext == '.docx':
                try:
                    import docx
                    doc = docx.Document(file_path)
                    return " ".join([para.text for para in doc.paragraphs])
                except ImportError:
                    logger.warning("python-docx non disponible, traitement du DOCX en tant que fichier binaire")
                    return f"[DOCX NON SUPPORTÉ: {os.path.basename(file_path)}]"
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture du DOCX: {e}")
                    return f"[ERREUR DOCX: {os.path.basename(file_path)}]"
            
            # Fichiers Excel
            elif ext in ['.xlsx', '.xls']:
                try:
                    import pandas as pd
                    df = pd.read_excel(file_path)
                    return df.to_string()
                except ImportError:
                    logger.warning("pandas non disponible, traitement du fichier Excel en tant que fichier binaire")
                    return f"[EXCEL NON SUPPORTÉ: {os.path.basename(file_path)}]"
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture du fichier Excel: {e}")
                    return f"[ERREUR EXCEL: {os.path.basename(file_path)}]"
            
            # Fichiers PowerPoint
            elif ext in ['.pptx', '.ppt']:
                try:
                    from pptx import Presentation
                    prs = Presentation(file_path)
                    text = []
                    for slide in prs.slides:
                        for shape in slide.shapes:
                            if hasattr(shape, "text"):
                                text.append(shape.text)
                    return "\n".join(text)
                except ImportError:
                    logger.warning("python-pptx non disponible, traitement du fichier PowerPoint en tant que fichier binaire")
                    return f"[POWERPOINT NON SUPPORTÉ: {os.path.basename(file_path)}]"
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture du fichier PowerPoint: {e}")
                    return f"[ERREUR POWERPOINT: {os.path.basename(file_path)}]"
            
            # Fichiers OpenDocument
            elif ext in ['.odt', '.ods', '.odp']:
                try:
                    import odf
                    if ext == '.odt':
                        doc = odf.text.TextDocument(file_path)
                        return " ".join([p.text for p in doc.getElementsByType(odf.text.P)])
                    elif ext == '.ods':
                        doc = odf.spreadsheet.SpreadsheetDocument(file_path)
                        return " ".join([cell.text for table in doc.getElementsByType(odf.table.Table) for cell in table.getElementsByType(odf.table.Cell)])
                    else:  # .odp
                        doc = odf.presentation.PresentationDocument(file_path)
                        return " ".join([shape.text for page in doc.getElementsByType(odf.presentation.Page) for shape in page.getElementsByType(odf.presentation.Text)])
                except ImportError:
                    logger.warning("odfpy non disponible, traitement du fichier OpenDocument en tant que fichier binaire")
                    return f"[OPENDOCUMENT NON SUPPORTÉ: {os.path.basename(file_path)}]"
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture du fichier OpenDocument: {e}")
                    return f"[ERREUR OPENDOCUMENT: {os.path.basename(file_path)}]"
            
            # Fichiers RTF
            elif ext == '.rtf':
                try:
                    import striprtf
                    with open(file_path, 'r', encoding='utf-8') as f:
                        rtf_content = f.read()
                    return striprtf.rtf_to_text(rtf_content)
                except ImportError:
                    logger.warning("striprtf non disponible, traitement du fichier RTF en tant que fichier binaire")
                    return f"[RTF NON SUPPORTÉ: {os.path.basename(file_path)}]"
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture du fichier RTF: {e}")
                    return f"[ERREUR RTF: {os.path.basename(file_path)}]"
            
            # Fichiers HTML
            elif ext in ['.html', '.htm']:
                try:
                    from bs4 import BeautifulSoup
                    with open(file_path, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                    return soup.get_text()
                except ImportError:
                    logger.warning("beautifulsoup4 non disponible, traitement du fichier HTML en tant que fichier binaire")
                    return f"[HTML NON SUPPORTÉ: {os.path.basename(file_path)}]"
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture du fichier HTML: {e}")
                    return f"[ERREUR HTML: {os.path.basename(file_path)}]"
            
            # Fichiers XML
            elif ext == '.xml':
                try:
                    import xml.etree.ElementTree as ET
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                    return ET.tostring(root, encoding='unicode', method='text')
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture du fichier XML: {e}")
                    return f"[ERREUR XML: {os.path.basename(file_path)}]"
            
            # Fichiers JSON
            elif ext == '.json':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return json.dumps(data, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture du fichier JSON: {e}")
                    return f"[ERREUR JSON: {os.path.basename(file_path)}]"
            
            # Fichiers CSV
            elif ext == '.csv':
                try:
                    import pandas as pd
                    df = pd.read_csv(file_path)
                    return df.to_string()
                except ImportError:
                    logger.warning("pandas non disponible, traitement du fichier CSV en tant que fichier binaire")
                    return f"[CSV NON SUPPORTÉ: {os.path.basename(file_path)}]"
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture du fichier CSV: {e}")
                    return f"[ERREUR CSV: {os.path.basename(file_path)}]"
            
            # Fichiers Markdown
            elif ext in ['.md', '.markdown']:
                try:
                    import markdown
                    with open(file_path, 'r', encoding='utf-8') as f:
                        md_content = f.read()
                    return markdown.markdown(md_content)
                except ImportError:
                    logger.warning("markdown non disponible, traitement du fichier Markdown en tant que fichier binaire")
                    return f"[MARKDOWN NON SUPPORTÉ: {os.path.basename(file_path)}]"
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture du fichier Markdown: {e}")
                    return f"[ERREUR MARKDOWN: {os.path.basename(file_path)}]"
            
            # Images
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                try:
                    import pytesseract
                    from PIL import Image
                    img = Image.open(file_path)
                    return pytesseract.image_to_string(img)
                except ImportError:
                    logger.warning("pytesseract non disponible, traitement de l'image en tant que fichier binaire")
                    return f"[IMAGE NON SUPPORTÉ: {os.path.basename(file_path)}]"
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture de l'image: {e}")
                    return f"[ERREUR IMAGE: {os.path.basename(file_path)}]"
            
            # Fichiers texte - détecter l'encodage automatiquement
            else:
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding'] if result['encoding'] else 'utf-8'
                    
                try:
                    return raw_data.decode(encoding)
                except UnicodeDecodeError:
                    # En cas d'échec, essayer latin-1 qui ne peut jamais échouer
                    return raw_data.decode('latin-1')
                    
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier: {e}")
            return f"[ERREUR DE LECTURE: {os.path.basename(file_path)}]"
            
    def analyze_document(self, file_path: str, file_type: str = None, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Analyse un document pour extraire des informations pertinentes
        
        Args:
            file_path: Chemin vers le document à analyser
            file_type: Type du fichier (extension sans le point)
            encoding: Encodage du fichier (par défaut utf-8)
            
        Returns:
            Dict contenant les informations extraites
        """
        if not os.path.exists(file_path):
            return {"error": f"Le fichier {file_path} n'existe pas"}
            
        if not file_type:
            # Extraire l'extension du fichier
            _, ext = os.path.splitext(file_path)
            file_type = ext.lower()[1:] if ext else ""
            
        # Convertir le document en texte
        try:
            content = self.convert_to_text(file_path, file_type, encoding)
        except Exception as e:
            logger.error(f"Erreur lors de la conversion du document en texte: {e}")
            return {"error": f"Impossible de lire le document: {str(e)}"}
            
        if not content or content.startswith("Erreur:"):
            return {"error": content if content else "Contenu vide ou non lisible"}
            
        # Utiliser directement le mode de secours si requis
        if self.fallback_mode:
            logger.info("Mode de secours activé, utilisation directe du mode de secours")
            return self._analyze_fallback(content)
            
        # Analyser le document
        try:
            # Analyse par sections pour les documents longs
            result = self._analyze_document_by_sections(content)
            
            # Si résultat vide ou erreur, utiliser le mode de secours
            if not result or "error" in result or not result.get("variables"):
                logger.warning("Analyse par sections a échoué ou n'a trouvé aucune variable, tentative avec le mode de secours")
                result = self._analyze_fallback(content)
            
            logger.info(f"Analyse terminée avec succès: {len(result['variables'])} variables trouvées")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du document: {e}")
            return self._analyze_fallback(content)
    
    def _smart_reduce_content(self, content: str, max_size: int) -> str:
        """
        Réduit intelligemment le contenu pour l'analyse en préservant les parties importantes
        
        Args:
            content: Contenu à réduire
            max_size: Taille maximale souhaitée
            
        Returns:
            Contenu réduit intelligemment
        """
        if len(content) <= max_size:
            return content
            
        # Zones prioritaires
        start_size = min(max_size // 3, 800)  # Début du document (en-têtes, intro)
        end_size = min(max_size // 3, 600)    # Fin du document (conclusion, signatures)
        
        # Extraire les sections importantes
        content_start = content[:start_size]
        content_end = content[-end_size:]
        
        # Espace restant pour les sections importantes
        remaining_size = max_size - (start_size + end_size + 100)  # 100 pour le texte de séparation
        
        # Mots-clés importants selon le type de document
        important_keywords = [
            # Identités
            "client", "nom", "prénom", "société", "entreprise", 
            # Coordonnées
            "adresse", "email", "téléphone", "portable", "contact",
            # Données financières 
            "montant", "prix", "total", "somme", "€", "euros", "eur",
            # Références et dates
            "référence", "facture", "commande", "date", "numéro",
            # Termes légaux
            "contrat", "signature", "légal", "obligation"
        ]
        
        # Découper en paragraphes et noter leur importance
        paragraphs = re.split(r'\n\s*\n', content)
        scored_paragraphs = []
        
        for para in paragraphs:
            # Ignorer les paragraphes vides ou trop courts
            if len(para.strip()) < 5:
                continue
                
            # Calculer un score d'importance
            score = 0
            para_lower = para.lower()
            
            # Points pour chaque mot-clé trouvé
            for keyword in important_keywords:
                if keyword in para_lower:
                    score += 2
                    
            # Points supplémentaires pour les formats spéciaux
            # Dates
            if re.search(r'\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b', para):
                score += 3
            # Montants
            if re.search(r'\b\d+(?:[,.]\d{1,2})?(?:\s?[€$]|EUR)?\b', para):
                score += 3
            # Emails
            if re.search(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b', para):
                score += 3
            # Téléphones
            if re.search(r'\b(?:0\d[\s.-]?){4,5}\d{2}\b', para):
                score += 3
            
            # Ajouter le paragraphe avec son score
            scored_paragraphs.append((para, score))
        
        # Trier les paragraphes par score d'importance décroissant
        scored_paragraphs.sort(key=lambda x: x[1], reverse=True)
        
        # Sélectionner les paragraphes les plus importants
        selected_paragraphs = []
        total_length = 0
        
        for para, score in scored_paragraphs:
            if total_length + len(para) <= remaining_size:
                selected_paragraphs.append(para)
                total_length += len(para) + 2  # +2 pour les sauts de ligne
            else:
                break
        
        # Construire le contenu final
        reduced_content = content_start + "\n\n"
        if selected_paragraphs:
            reduced_content += "--- INFORMATIONS IMPORTANTES ---\n\n" + "\n\n".join(selected_paragraphs) + "\n\n"
        reduced_content += "--- FIN DU DOCUMENT ---\n\n" + content_end
        
        logger.info(f"Contenu réduit de {len(content)} à {len(reduced_content)} caractères")
        return reduced_content

    def convert_to_text(self, file_path, file_type=None, encoding='utf-8'):
        """
        Convertit un document en texte brut, quel que soit son format
        
        Args:
            file_path: Chemin du fichier à convertir
            file_type: Type du fichier (extension)
            encoding: Encodage du fichier
            
        Returns:
            str: Contenu textuel du document
        """
        if not file_type:
            file_type = os.path.splitext(file_path)[1].lower()[1:]
            
        try:
            # Si le fichier est un .docx (Word)
            if file_type in ['docx', 'doc']:
                try:
                    import docx
                    doc = docx.Document(file_path)
                    full_text = []
                    # Extraire le texte de chaque paragraphe
                    for para in doc.paragraphs:
                        full_text.append(para.text)
                    # Extraire le texte des tableaux
                    for table in doc.tables:
                        for row in table.rows:
                            for cell in row.cells:
                                for para in cell.paragraphs:
                                    full_text.append(para.text)
                    return '\n'.join(full_text)
                except ImportError:
                    logger.warning("Module python-docx non disponible, tentative de fallback")
                    # Fallback à une lecture textuelle
                    try:
                        with open(file_path, 'rb') as f:
                            import chardet
                            result = chardet.detect(f.read())
                            detected_encoding = result['encoding']
                        with open(file_path, 'r', encoding=detected_encoding or 'utf-8', errors='replace') as f:
                            return f.read()
                    except Exception as e:
                        logger.error(f"Erreur lors de la lecture du fichier Word: {e}")
                        return f"Erreur: {str(e)}"
                except Exception as e:
                    logger.error(f"Erreur lors de l'extraction du texte du fichier Word: {e}")
                    return f"Erreur: {str(e)}"
                    
            # Si le fichier est un .pdf
            elif file_type == 'pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        text = ''
                        for page_num in range(len(pdf_reader.pages)):
                            page = pdf_reader.pages[page_num]
                            text += page.extract_text() + '\n'
                        return text
                except ImportError:
                    logger.warning("Module PyPDF2 non disponible, tentative de fallback")
                    # Fallback vers une lecture textuelle basique
                    try:
                        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                            return f.read()
                    except Exception as e:
                        logger.error(f"Erreur lors de la lecture du fichier PDF: {e}")
                        return f"Erreur: {str(e)}"
                except Exception as e:
                    logger.error(f"Erreur lors de l'extraction du texte du fichier PDF: {e}")
                    return f"Erreur: {str(e)}"
                    
            # Si le fichier est une image
            elif file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                try:
                    from PIL import Image
                    import pytesseract
                    image = Image.open(file_path)
                    text = pytesseract.image_to_string(image, lang='fra+eng')
                    return text
                except ImportError:
                    logger.warning("Module pytesseract non disponible")
                    return "Erreur: L'extraction de texte depuis des images nécessite le module pytesseract"
                except Exception as e:
                    logger.error(f"Erreur lors de l'OCR sur l'image: {e}")
                    return f"Erreur: {str(e)}"
                    
            # Pour les fichiers texte (.txt, .md, .html, etc.)
            else:
                # Essayer différents encodages pour gérer tous les cas de figure
                encodings = ['utf-8', 'latin-1', 'cp1252', 'utf-16', 'utf-16-le', 'utf-16-be']
                content = None
                last_error = None
                
                # Si un encodage spécifique est demandé, le tester en premier
                if encoding and encoding not in encodings:
                    encodings.insert(0, encoding)
                
                for enc in encodings:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            content = f.read()
                        logger.info(f"Fichier lu avec succès en utilisant l'encodage {enc}")
                        break
                    except UnicodeDecodeError as e:
                        logger.debug(f"Échec de lecture avec l'encodage {enc}: {e}")
                        last_error = e
                    except Exception as e:
                        logger.warning(f"Erreur lors de la lecture du fichier avec l'encodage {enc}: {e}")
                        last_error = e
                
                # Si tous les encodages ont échoué, tenter une détection automatique
                if content is None:
                    try:
                        import chardet
                        with open(file_path, 'rb') as f:
                            raw_data = f.read()
                            result = chardet.detect(raw_data)
                            detected_encoding = result['encoding']
                            
                            if detected_encoding:
                                logger.info(f"Encodage détecté: {detected_encoding}")
                                with open(file_path, 'r', encoding=detected_encoding, errors='replace') as f:
                                    content = f.read()
                            else:
                                # Dernier recours: lecture en mode binaire et conversion forcée
                                content = raw_data.decode('utf-8', errors='replace')
                    except Exception as e:
                        logger.error(f"Erreur lors de la détection de l'encodage: {e}")
                        if last_error:
                            raise last_error
                        else:
                            raise e
                
                return content
                
        except Exception as e:
            logger.error(f"Erreur lors de la conversion du document en texte: {e}")
            return f"Erreur lors de la lecture du document: {str(e)}"
            
    def fill_template(self, template_path: str, client_info: Dict, encoding: str = 'utf-8') -> Tuple[str, Dict]:
        """
        Remplit un modèle avec les informations client
        
        Args:
            template_path: Chemin vers le modèle
            client_info: Informations client
            encoding: Encodage du fichier
            
        Returns:
            Tuple[str, Dict]: (contenu rempli, variables manquantes)
        """
        try:
            logger.info(f"Début du remplissage du modèle: {template_path}")
            
            # 1. Validation initiale
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"Le modèle n'existe pas: {template_path}")
            
            if not client_info or not isinstance(client_info, dict):
                raise ValueError("Les informations client sont invalides")
            
            # 2. Lecture du modèle avec gestion d'encodage
            content = None
            encoding_errors = []
            
            for enc in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(template_path, 'r', encoding=enc) as f:
                        content = f.read()
                        logger.debug(f"Lecture réussie avec l'encodage: {enc}")
                        break
                except UnicodeDecodeError as e:
                    encoding_errors.append(f"Erreur avec {enc}: {str(e)}")
                    continue
                    
            if content is None:
                raise UnicodeError(f"Impossible de lire le fichier. Erreurs: {', '.join(encoding_errors)}")
            
            # 3. Analyse du modèle
            logger.debug("Analyse du modèle...")
            variables = self._analyze_template_content(content)
            
            # 4. Validation des variables requises
            missing_vars = {}
            invalid_vars = []
            
            for var_name, var_info in variables.items():
                if var_info.get('required', False):
                    if var_name not in client_info:
                        missing_vars[var_name] = var_info
                    else:
                        # Valider la valeur selon le type
                        value = client_info[var_name]
                        validation_rules = self._get_validation_rules(var_info.get('type', 'text'))
                        if not self._validate_variable(value, validation_rules):
                            invalid_vars.append(var_name)
            
            if invalid_vars:
                logger.warning(f"Variables invalides: {invalid_vars}")
                raise ValueError(f"Les variables suivantes sont invalides: {', '.join(invalid_vars)}")
            
            # 5. Remplissage du modèle
            if not self.fallback_mode and len(missing_vars) == 0:
                try:
                    logger.info("Utilisation de l'IA pour le remplissage...")
                    filled_content = self._fill_with_ai(content, client_info)
                except Exception as e:
                    logger.error(f"Erreur lors du remplissage IA: {e}")
                    filled_content = self._fill_template_basic(content, client_info)
                else:
                    logger.info("Utilisation du remplissage basique...")
                    filled_content = self._fill_template_basic(content, client_info)
            
            return filled_content, missing_vars
            
        except Exception as e:
            logger.error(f"Erreur lors du remplissage du modèle: {e}")
            return str(e), {
                    "error": {
                        "type": "text",
                    "description": "Erreur de traitement",
                        "required": True,
                    "current_value": str(e)
                }
            }
    
    def _validate_variable(self, value: Any, rules: Dict[str, Any]) -> bool:
        """
        Valide une variable selon les règles définies
        
        Args:
            value: Valeur à valider
            rules: Règles de validation
            
        Returns:
            bool: True si la valeur est valide
        """
        try:
            if 'regex' in rules:
                if not re.match(rules['regex'], str(value)):
                    return False
            
            if 'min_length' in rules and isinstance(value, (str, list)):
                if len(value) < rules['min_length']:
                    return False
            
            if 'max_length' in rules and isinstance(value, (str, list)):
                if len(value) > rules['max_length']:
                    return False
            
            if 'min_value' in rules and isinstance(value, (int, float)):
                if value < rules['min_value']:
                    return False
            
            if 'decimal_places' in rules and isinstance(value, (int, float)):
                str_value = str(value)
                if '.' in str_value:
                    if len(str_value.split('.')[1]) > rules['decimal_places']:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation: {e}")
            return False

    def generate_final_document(self, template_path: str, all_variables: Dict[str, str]) -> str:
        """
        Génère le document final avec toutes les variables
        
        Args:
            template_path: Chemin vers le modèle
            all_variables: Toutes les variables (client + complétées)
            
        Returns:
            Texte final du document
        """
        try:
            # Lire le contenu du modèle
            content = self._read_file_safely(template_path)
            original_content = content
            
            # Tentative initiale de remplacement simple des variables
            for var_name, value in all_variables.items():
                # S'assurer que la valeur est une chaîne non-vide
                value_str = str(value) if value is not None else ""
                
                # Différents formats de variables à remplacer
                patterns = [
                    f"{{{var_name}}}",     # {variable}
                    f"[{var_name}]",       # [variable]
                    f"<{var_name}>",       # <variable>
                    f"${var_name}$",       # $variable$
                    f"«{var_name}»"        # «variable»
                ]
                
                for pattern in patterns:
                    content = content.replace(pattern, value_str)
            
            # Vérifier si des variables n'ont pas été remplacées (motifs de variables restants)
            remaining_vars = []
            for pattern in [r'\{[a-zA-Z0-9_]+\}', r'\[[a-zA-Z0-9_]+\]', r'<[a-zA-Z0-9_]+>', r'\$[a-zA-Z0-9_]+\$', r'«[a-zA-Z0-9_]+»']:
                matches = re.findall(pattern, content)
                remaining_vars.extend(matches)
            
            # Si des variables n'ont pas été remplacées, utiliser l'IA pour un remplacement plus intelligent
            if remaining_vars and not self.fallback_mode:
                logger.info(f"{len(remaining_vars)} variables non remplacées détectées, utilisation de l'IA pour amélioration")
                
                # Utiliser l'IA pour générer un document complet
                final_content = self._complete_document_with_ai(content, all_variables, remaining_vars)
                
                # Vérification de qualité du document final
                if self._verify_document_quality(final_content, original_content, all_variables):
                    logger.info("Document final généré avec succès via IA")
                    return final_content
                else:
                    logger.warning("Document généré par IA de qualité insuffisante, fallback vers remplacement simple")
            
            # Si aucune variable non remplacée ou si en mode fallback, retourner le document modifié
            logger.info("Document final généré avec succès via remplacement simple")
            return content
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du document final: {e}")
            
            # Tentative de récupération en cas d'erreur
            try:
                # Lecture du template original et remplacement basique
                with open(template_path, 'r', encoding='utf-8', errors='replace') as f:
                    recovery_content = f.read()
                
                # Remplacement forcé avec toutes les variables
                for var_name, value in all_variables.items():
                    value_str = str(value) if value is not None else ""
                    for pattern in [f"{{{var_name}}}", f"[{var_name}]", f"<{var_name}>"]:
                        recovery_content = recovery_content.replace(pattern, value_str)
                
                logger.info("Document récupéré avec succès en mode de secours")
                return recovery_content
            except Exception as recovery_error:
                logger.error(f"Échec de la récupération: {recovery_error}")
                
                # En dernier recours, générer un document minimal mais complet
                minimal_doc = f"""
                # Document généré pour {all_variables.get('name', 'Client')}
                
                Date: {all_variables.get('date', '')}
                Référence: {all_variables.get('reference', '')}
                
                """
                
                # Ajouter toutes les variables disponibles
                for var_name, value in all_variables.items():
                    if var_name not in ['name', 'date', 'reference']:
                        minimal_doc += f"{var_name}: {value}\n"
                
                logger.warning("Document minimal généré suite à une erreur critique")
                return minimal_doc
    
    def _complete_document_with_ai(self, content: str, variables: Dict[str, str], remaining_vars: List[str]) -> str:
        """
        Utilise l'IA pour compléter intelligemment le document avec toutes les variables
        
        Args:
            content: Contenu du document partiellement rempli
            variables: Toutes les variables disponibles
            remaining_vars: Liste des variables non remplacées
            
        Returns:
            Document complété par l'IA
        """
        # Formater pour plus de lisibilité
        remaining_formatted = ', '.join(remaining_vars[:10])
        if len(remaining_vars) > 10:
            remaining_formatted += f" et {len(remaining_vars) - 10} autres"
        
        # Préparation du prompt
        prompt = f"""Vous êtes un expert en génération de documents juridiques et administratifs.

DOCUMENT ACTUEL:
```
{content}
```

VARIABLES DISPONIBLES:
```
{json.dumps(variables, indent=2, ensure_ascii=False)}
```

VARIABLES NON REMPLACÉES: {remaining_formatted}

TÂCHE:
1. Analysez le document et identifiez toutes les variables non remplacées
2. Remplacez chaque variable par sa valeur correspondante dans le dictionnaire
3. Si une variable n'a pas de valeur correspondante, utilisez une valeur standard appropriée
4. Assurez-vous que le texte final est cohérent et complet
5. Conservez EXACTEMENT la mise en forme du document (espaces, retours à la ligne, etc.)

IMPORTANT:
- Ne retournez que le document complété, sans explication
- Respectez la structure exacte du document original
- Utilisez toujours les informations fournies dans le dictionnaire quand elles existent

DOCUMENT COMPLÉTÉ:
"""
        
        try:
            # Appel à Ollama avec un timeout plus long pour garantir l'achèvement
            response = self._call_ollama(prompt, timeout=180)
            
            # Vérifier si la réponse contient du texte
            if not response or len(response) < 50:
                logger.warning("Réponse de l'IA trop courte ou vide")
                return content
                
            return response
            
        except Exception as e:
            logger.error(f"Échec de la complétion IA: {e}")
            return content
    
    def _verify_document_quality(self, final_doc: str, original_doc: str, variables: Dict[str, str]) -> bool:
        """
        Vérifie la qualité du document généré pour s'assurer qu'il est complet
        
        Args:
            final_doc: Document généré
            original_doc: Document original
            variables: Variables utilisées
            
        Returns:
            True si le document est de bonne qualité, False sinon
        """
        # 1. Vérifier que le document n'est pas vide
        if not final_doc or len(final_doc) < 50:
            logger.warning("Document final trop court")
            return False
            
        # 2. Vérifier que le document a une taille raisonnable par rapport à l'original
        if len(final_doc) < len(original_doc) * 0.7:
            logger.warning(f"Document final trop court: {len(final_doc)} vs {len(original_doc)} caractères")
            return False
            
        # 3. Vérifier que les variables importantes sont présentes dans le document final
        important_vars = ['name', 'date', 'montant', 'reference', 'adresse', 'telephone']
        for var in important_vars:
            if var in variables and variables[var]:
                if variables[var] not in final_doc:
                    logger.warning(f"Variable importante '{var}' absente du document final")
                    return False
        
        # 4. Vérifier qu'il ne reste pas de motifs de variables
        for pattern in [r'\{[a-zA-Z0-9_]+\}', r'\[[a-zA-Z0-9_]+\]', r'<[a-zA-Z0-9_]+>', r'\$[a-zA-Z0-9_]+\$', r'«[a-zA-Z0-9_]+»']:
            if re.search(pattern, final_doc):
                logger.warning(f"Variables non remplacées trouvées dans le document final")
                return False
                
        return True

    def personalize_document(self, content: str, variables: Dict[str, Any]) -> str:
        """
        Personnalise un document en remplaçant les variables par leurs valeurs
        
        Args:
            content: Contenu du document à personnaliser
            variables: Dictionnaire des variables à remplacer
            
        Returns:
            Document personnalisé
        """
        try:
            # Préparer les variables
            vars_list = []
            for var_name, var_info in variables.items():
                value = ""
                if isinstance(var_info, dict) and "current_value" in var_info:
                    value = var_info["current_value"]
                    description = var_info.get("description", var_name)
                    var_type = var_info.get("type", "text")
                    vars_list.append(f"{var_name} ({description}, {var_type}): {value}")
                else:
                    value = str(var_info)
                    vars_list.append(f"{var_name}: {value}")
                    
            vars_json = "\n".join(vars_list)
            
            # Créer le prompt pour personnaliser le document
            prompt = f"""
Personnalise ce document en remplaçant les variables par les valeurs données:

Document:
```
{content}
```

Variables:
{vars_json}

Retourne uniquement le document personnalisé."""

            # Si le document est petit, le traiter en une fois
            if len(content) < 4000:
                return self._call_ollama(prompt)

            # Pour les grands documents, découper en sections logiques
            sections = self._split_document_into_sections(content)
            
            # Traiter chaque section avec le contexte complet
            results = []
            for i, section in enumerate(sections, 1):
                logger.info(f"Traitement section {i}/{len(sections)}")
                
                section_prompt = f"""Personnalise cette section:

Section:
{section}

Variables:
{vars_json}

Conserve la mise en forme.
"""
                
                # Appeler l'API pour personnaliser la section
                section_result = self._call_ollama(section_prompt)
                
                # Si erreur, utiliser la section originale
                if section_result.startswith("Erreur:") or "Timeout" in section_result:
                    logger.warning(f"Échec de la personnalisation de la section {i}, utilisation de l'original")
                    results.append(section)
                else:
                    results.append(section_result)
            
            # Joindre les sections en préservant les sauts de ligne
            return "\n\n".join(results)
            
        except Exception as e:
            logger.error(f"Erreur lors de la personnalisation: {e}")
            return self._fallback_personalization(content, variables)

    def _call_ollama(self, prompt: str, timeout: int = 5) -> str:  # Timeout réduit à 5s
        try:
            # Limiter la taille du prompt
            if len(prompt) > 1000:  # Réduit de 2000 à 1000
                prompt = prompt[:1000]
            
            # Options simplifiées
            options = {
                "temperature": 0.1,  # Réduit pour plus de rapidité
                "num_predict": 50,   # Réduit de 100 à 50
                "stop": ["\n\n", "###"]
            }
            
            # Appel simplifié à Ollama avec le modèle Mistral
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "mistral", "prompt": prompt, **options},
                timeout=timeout
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            return ""
            
        except Exception as e:
            logger.error(f"Erreur Ollama: {str(e)}")
            return ""

    def _analyze_document_by_sections(self, content: str) -> Dict[str, Any]:
        # Analyse simplifiée
        try:
            sections = self._split_document_into_sections(content)
            results = []
            
            for section in sections[:5]:  # Limite à 5 sections
                if len(section) > 500:  # Réduit de 800 à 500
                    section = section[:500]
                result = self._analyze_section_simplified(section)
                if result:
                    results.append(result)
            
            return self._merge_results(results)
                    
        except Exception as e:
            logger.error(f"Erreur analyse: {str(e)}")
            return {}

    def _analyze_section_simplified(self, content: str) -> Dict[str, Any]:
        try:
            prompt = f"""
Extrais les variables clés de ce texte au format JSON. Exemples de variables à chercher:
- nom, prénom, société
- adresse, ville, code_postal, pays
- email, téléphone
- date, référence, montant
- objet, type_document

Analyse le texte suivant:
-----
{content}
-----

Réponds uniquement avec un objet JSON de la forme:
{{
  "variables": {{
    "nom": "Valeur",
    "email": "Valeur",
    ...
  }}
}}
"""
            response = self._call_ollama(prompt, timeout=10)
            
            if not response:
                return {}
                
            try:
                # Essayer d'extraire la partie JSON
                json_match = re.search(r'({.*})', response.replace('\n', ''), re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    try:
                        extracted_data = json.loads(json_str)
                        # Vérifier que c'est un dictionnaire et qu'il contient "variables"
                        if isinstance(extracted_data, dict):
                            if "variables" in extracted_data:
                                return extracted_data
                            return {"variables": extracted_data}
                    except:
                        pass
                
                # Si l'extraction a échoué, essayer de nettoyer la réponse entière
                try:
                    return json.loads(response)
                except:
                    pass
                    
                # En dernier recours, parser manuellement
                variable_pattern = r'"([^"]+)":\s*"([^"]+)"'
                matches = re.findall(variable_pattern, response)
                if matches:
                    variables = {}
                    for key, value in matches:
                        variables[key] = value
                    return {"variables": variables}
                    
                return {}
            except Exception as e:
                logger.error(f"Erreur lors du parsing de la réponse JSON: {e}")
                return {}
                        
        except Exception as e:
            logger.error(f"Erreur section: {str(e)}")
            return {}

    def _merge_results(self, results: List[Dict]) -> Dict[str, Any]:
        merged = {}
        for result in results:
            for key, value in result.items():
                if key not in merged:
                    merged[key] = value
        return merged

    def _analyze_fallback(self, content: str) -> Dict[str, Any]:
        """
        Méthode de secours pour l'analyse de document lorsque l'analyse principale échoue
        
        Args:
            content: Contenu textuel du document à analyser
            
        Returns:
            Dict contenant les informations extraites
        """
        logger.info("Utilisation de la méthode de secours pour l'analyse")
        try:
            # Extraire des informations basiques du texte
            variables = {}
            
            # Rechercher des dates (format JJ/MM/AAAA ou JJ-MM-AAAA)
            dates = re.findall(r'\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b', content)
            if dates:
                variables['date'] = dates[0]
            
            # Rechercher des montants
            amounts = re.findall(r'\b\d+(?:[,.]\d{1,2})?(?:\s?[€$]|EUR)?\b', content)
            if amounts:
                variables['montant'] = amounts[0]
            
            # Rechercher des emails
            emails = re.findall(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b', content)
            if emails:
                variables['email'] = emails[0]
            
            # Rechercher des numéros de téléphone
            phones = re.findall(r'\b(?:0\d[\s.-]?){4,5}\d{2}\b', content)
            if phones:
                variables['telephone'] = phones[0]
            
            # Essayer d'identifier le type de document
            doc_types = {
                'contrat': ['contrat', 'convention', 'accord', 'engagement'],
                'facture': ['facture', 'paiement', 'règlement', 'montant', 'total', 'tva'],
                'lettre': ['madame', 'monsieur', 'cordialement', 'sincères salutations'],
                'cv': ['expérience', 'compétences', 'formation', 'diplôme', 'curriculum vitae']
            }
            
            content_lower = content.lower()
            for doc_type, keywords in doc_types.items():
                if any(keyword in content_lower for keyword in keywords):
                    variables['type_document'] = doc_type
                    break
            else:
                variables['type_document'] = 'document'
            
            # Rechercher un nom ou une entité
            name_patterns = [
                r'M(?:\.|onsieur)\s+([A-Z][a-zA-Zéèêëàâäôöûüç\s-]+)',
                r'Mme(?:\.|adame)\s+([A-Z][a-zA-Zéèêëàâäôöûüç\s-]+)',
                r'Société\s+([A-Z][a-zA-Zéèêëàâäôöûüç\s-]+)'
            ]
            
            for pattern in name_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    variables['nom'] = matches[0].strip()
                    break
                    
            # Si pas de nom trouvé, essayer une approche simple
            if 'nom' not in variables:
                # Extraire des mots commençant par une majuscule et qui ne sont pas au début d'une phrase
                cap_words = re.findall(r'(?<=[^\.\?\!]\s)[A-Z][a-zA-Zéèêëàâäôöûüç]+', content)
                if cap_words:
                    # Prendre le mot qui apparaît le plus fréquemment
                    from collections import Counter
                    word_counts = Counter(cap_words)
                    most_common = word_counts.most_common(1)
                    if most_common:
                        variables['entite'] = most_common[0][0]
            
            # Créer le résultat final
            result = {
                'variables': variables,
                'detection_method': 'fallback',
                'confidence': 'low'
            }
            
            logger.info(f"Analyse de secours terminée, {len(variables)} variables extraites")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de secours: {e}")
            # Retourner un résultat minimal mais valide
            return {
                'variables': {
                    'type_document': 'document'
                },
                'detection_method': 'fallback_error',
                'error': str(e)
            }

    def diagnose_analysis_issues(self, file_path: str) -> Dict[str, Any]:
        """
        Diagnostique les problèmes potentiels dans l'analyse d'un document
        
        Args:
            file_path: Chemin vers le document à analyser
            
        Returns:
            Dict contenant les diagnostics et informations sur les problèmes
        """
        logger.info(f"Diagnostic de l'analyse pour le fichier: {file_path}")
        
        diagnostics = {
            "file_path": file_path,
            "file_exists": os.path.exists(file_path),
            "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            "file_extension": os.path.splitext(file_path)[1].lower() if os.path.exists(file_path) else "",
            "text_extraction": None,
            "text_length": 0,
            "mistral_connection": False,
            "mistral_response": None,
            "issues": [],
            "recommendations": []
        }
        
        # Vérification du fichier
        if not diagnostics["file_exists"]:
            diagnostics["issues"].append("Le fichier n'existe pas")
            diagnostics["recommendations"].append("Vérifiez le chemin du fichier")
            return diagnostics
            
        if diagnostics["file_size"] == 0:
            diagnostics["issues"].append("Le fichier est vide")
            diagnostics["recommendations"].append("Vérifiez que le fichier contient des données")
            return diagnostics
            
        # Extraction de texte
        try:
            content = self.convert_to_text(file_path)
            diagnostics["text_extraction"] = "success"
            diagnostics["text_length"] = len(content)
            
            # Échantillon du texte
            diagnostics["text_sample"] = content[:200] + "..." if len(content) > 200 else content
            
            if diagnostics["text_length"] == 0:
                diagnostics["issues"].append("Aucun texte n'a pu être extrait du document")
                diagnostics["recommendations"].append("Vérifiez que le document contient du texte et pas seulement des images")
                
            elif diagnostics["text_length"] < 50:
                diagnostics["issues"].append("Le texte extrait est très court")
                diagnostics["recommendations"].append("Vérifiez que le document contient suffisamment de texte pour l'analyse")
                
        except Exception as e:
            diagnostics["text_extraction"] = "failed"
            diagnostics["issues"].append(f"Erreur lors de l'extraction du texte: {str(e)}")
            diagnostics["recommendations"].append("Vérifiez le format du document et réessayez avec un autre format si possible")
            
        # Test de la connexion à Mistral
        try:
            test_prompt = "Renvoie simplement le mot 'OK'"
            response = self._call_ollama(test_prompt, timeout=3)
            
            diagnostics["mistral_connection"] = "OK" in response
            diagnostics["mistral_response"] = response[:50] if response else "Pas de réponse"
            
            if not diagnostics["mistral_connection"]:
                diagnostics["issues"].append("Problème de connexion avec le modèle Mistral")
                diagnostics["recommendations"].append("Vérifiez que le serveur Ollama est en cours d'exécution et que le modèle Mistral est installé")
                
        except Exception as e:
            diagnostics["issues"].append(f"Erreur lors du test de connexion à Mistral: {str(e)}")
            diagnostics["recommendations"].append("Vérifiez la configuration du serveur Ollama et assurez-vous qu'il fonctionne correctement")
            
        # Analyse conditionnelle du contenu
        if diagnostics["text_extraction"] == "success" and diagnostics["text_length"] > 0:
            # Vérification pour les formats structurés/semi-structurés
            if diagnostics["file_extension"] in [".pdf", ".docx", ".odt"]:
                if content.count("\n") < 5:
                    diagnostics["issues"].append("Le document semble manquer de structure (peu de sauts de ligne)")
                    diagnostics["recommendations"].append("Vérifiez que la mise en forme du document est préservée")
            
            # Vérification des caractères spéciaux/problèmes d'encodage
            strange_chars_count = len(re.findall(r'[^\x00-\x7F\u00C0-\u00FF]', content))
            if strange_chars_count > len(content) * 0.1:  # Plus de 10% de caractères étranges
                diagnostics["issues"].append("Le document contient beaucoup de caractères non standard")
                diagnostics["recommendations"].append("Vérifiez l'encodage du document")
            
        # Ajout d'un statut global
        if not diagnostics["issues"]:
            diagnostics["status"] = "ok"
            diagnostics["recommendations"].append("Aucun problème détecté, l'analyse devrait fonctionner correctement")
        else:
            diagnostics["status"] = "issues_detected"
            
        logger.info(f"Diagnostic terminé, statut: {diagnostics['status']}")
        return diagnostics
