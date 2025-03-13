#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module OCR pour Vynal Docs Automator
Fournit des fonctions pour l'extraction de texte à partir d'images et l'amélioration
des résultats OCR en utilisant diverses techniques de prétraitement.
"""

import os
import sys
import logging
import io
from typing import Dict, List, Optional, Tuple, Union, Any
import tempfile
import json
import re
from pathlib import Path

# Configuration du logger
logger = logging.getLogger("VynalDocsAutomator.Utils.OCR")

# Importation conditionnelle des dépendances
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV (cv2) n'est pas disponible. Les fonctionnalités d'amélioration d'image seront limitées.")

try:
    import pytesseract
    from pytesseract import Output
    TESSERACT_AVAILABLE = True
    
    # Vérification si Tesseract est correctement installé
    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        TESSERACT_AVAILABLE = False
        logger.warning("Tesseract n'est pas correctement installé ou n'est pas dans le PATH.")
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("PyTesseract n'est pas disponible. Les fonctionnalités OCR seront désactivées.")

try:
    from pdf2image import convert_from_path, convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logger.warning("pdf2image n'est pas disponible. La conversion de PDF en images sera désactivée.")

# Variables globales pour la configuration OCR
DEFAULT_LANGUAGE = "fra"  # Langue par défaut: français
AVAILABLE_LANGUAGES = ["fra", "eng", "ara", "deu", "spa", "ita", "por", "nld"]  # Langues supportées par défaut

# Configuration des chemins Tesseract (à ajuster selon l'environnement)
if sys.platform.startswith('win'):
    # Chemin Windows courant
    DEFAULT_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if TESSERACT_AVAILABLE and not os.path.exists(DEFAULT_TESSERACT_PATH):
        # Tenter de trouver le chemin automatiquement
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Tesseract-OCR")
            install_path = winreg.QueryValueEx(key, "InstallDir")[0]
            DEFAULT_TESSERACT_PATH = os.path.join(install_path, "tesseract.exe")
        except:
            # Laisser le chemin par défaut, pytesseract tentera de le trouver automatiquement
            pass
else:
    # Unix/Linux/Mac - généralement déjà dans le PATH
    DEFAULT_TESSERACT_PATH = "tesseract"

# Configuration de pytesseract si disponible
if TESSERACT_AVAILABLE and sys.platform.startswith('win'):
    pytesseract.pytesseract.tesseract_cmd = DEFAULT_TESSERACT_PATH


def enhance_image(image_path: str, output_path: Optional[str] = None, 
                 enhancement_level: str = "medium") -> str:
    """
    Améliore la qualité d'une image pour optimiser l'OCR.
    
    Args:
        image_path (str): Chemin vers l'image à améliorer
        output_path (str, optional): Chemin de sortie pour l'image améliorée. Si None, un fichier temporaire est créé.
        enhancement_level (str): Niveau d'amélioration (low, medium, high, extreme)
    
    Returns:
        str: Chemin vers l'image améliorée
    
    Raises:
        ValueError: Si le chemin d'image est invalide ou si OpenCV n'est pas disponible
    """
    if not CV2_AVAILABLE:
        raise ValueError("OpenCV (cv2) est nécessaire pour l'amélioration d'image")
    
    if not os.path.exists(image_path):
        raise ValueError(f"Le fichier image n'existe pas: {image_path}")
    
    # Charger l'image
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Impossible de charger l'image: {image_path}")
    except Exception as e:
        logger.error(f"Erreur lors du chargement de l'image: {e}")
        raise
    
    # Définir le fichier de sortie
    if output_path is None:
        temp_dir = tempfile.gettempdir()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', dir=temp_dir)
        output_path = temp_file.name
        temp_file.close()
    
    # Sélectionner les techniques de prétraitement selon le niveau d'amélioration
    enhanced_image = img.copy()
    
    if enhancement_level in ["low", "medium", "high", "extreme"]:
        # Convertir en niveaux de gris
        gray = cv2.cvtColor(enhanced_image, cv2.COLOR_BGR2GRAY)
        
        # Débruitage (pour tous les niveaux)
        if enhancement_level in ["medium", "high", "extreme"]:
            # Réduction du bruit avec préservation des bords
            gray = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # Correction de contraste (pour les niveaux medium et supérieurs)
        if enhancement_level in ["medium", "high", "extreme"]:
            # Égalisation d'histogramme adaptative (CLAHE)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
        
        # Binarisation (pour les niveaux high et extreme)
        if enhancement_level in ["high", "extreme"]:
            # Binarisation adaptative de Gauss
            gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY, 11, 2)
        
        # Techniques supplémentaires pour le niveau extreme
        if enhancement_level == "extreme":
            # Dilatation pour renforcer les contours
            kernel = np.ones((1, 1), np.uint8)
            gray = cv2.dilate(gray, kernel, iterations=1)
            # Érosion pour affiner les traits
            gray = cv2.erode(gray, kernel, iterations=1)
        
        enhanced_image = gray
    
    # Enregistrer l'image améliorée
    try:
        cv2.imwrite(output_path, enhanced_image)
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de l'image améliorée: {e}")
        raise
    
    return output_path


def extract_text_from_image(image_path: str, language: str = DEFAULT_LANGUAGE, 
                           preprocessing: str = "auto", config: str = "") -> str:
    """
    Extrait le texte d'une image en utilisant OCR.
    
    Args:
        image_path (str): Chemin vers l'image à analyser
        language (str): Code de langue pour l'OCR (fra, eng, ara, etc. ou combinaisons comme 'fra+eng')
        preprocessing (str): Méthode de prétraitement (none, auto, low, medium, high, extreme)
        config (str): Configuration supplémentaire pour Tesseract
    
    Returns:
        str: Texte extrait de l'image
    
    Raises:
        ValueError: Si Tesseract n'est pas disponible ou si le fichier image est invalide
    """
    if not TESSERACT_AVAILABLE:
        raise ValueError("PyTesseract est nécessaire pour l'extraction de texte")
    
    if not os.path.exists(image_path):
        raise ValueError(f"Le fichier image n'existe pas: {image_path}")
    
    # Prétraitement de l'image
    processed_image_path = image_path
    temp_file = None
    
    try:
        if preprocessing != "none" and CV2_AVAILABLE:
            # Détection automatique du niveau de prétraitement
            if preprocessing == "auto":
                # Lire l'image et évaluer sa qualité
                img = cv2.imread(image_path)
                if img is None:
                    raise ValueError(f"Impossible de charger l'image: {image_path}")
                
                # Calculer la netteté de l'image
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                
                # Calculer le contraste
                min_val, max_val, _, _ = cv2.minMaxLoc(gray)
                contrast = (max_val - min_val) / (max_val + min_val + 1e-10)
                
                # Calculer la luminosité moyenne
                brightness = np.mean(gray)
                
                # Déterminer le niveau de prétraitement en fonction des mesures
                if laplacian_var > 500 and contrast > 0.5:
                    # Image déjà nette avec bon contraste
                    preprocessing = "low"
                elif laplacian_var > 100 or (contrast > 0.3 and brightness > 100):
                    # Image de qualité moyenne
                    preprocessing = "medium"
                else:
                    # Image de faible qualité
                    preprocessing = "high"
            
            # Appliquer le prétraitement
            if preprocessing != "none":
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_file.close()
                processed_image_path = enhance_image(image_path, temp_file.name, preprocessing)
        
        # Configurer les options OCR
        custom_config = ""
        
        # Configuration par défaut: OEM 3 (default), PSM 3 (auto)
        if not config:
            custom_config = r'--oem 3 --psm 3'
        else:
            custom_config = config
        
        # Ajouter la spécification de langue
        if language:
            # Validation des langues
            langs = language.split('+')
            valid_langs = []
            
            for lang in langs:
                if lang in AVAILABLE_LANGUAGES:
                    valid_langs.append(lang)
                else:
                    logger.warning(f"Langue '{lang}' non reconnue, ignorée")
            
            if not valid_langs:
                valid_langs.append(DEFAULT_LANGUAGE)
            
            custom_config += f" -l {'+'.join(valid_langs)}"
        
        # Exécuter l'OCR
        extracted_text = pytesseract.image_to_string(processed_image_path, config=custom_config)
        
        return extracted_text
    
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de texte: {e}")
        raise
    
    finally:
        # Supprimer le fichier temporaire si créé
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.warning(f"Impossible de supprimer le fichier temporaire: {e}")


def extract_text_with_layout(image_path: str, language: str = DEFAULT_LANGUAGE, 
                            preprocessing: str = "auto") -> Dict[str, Any]:
    """
    Extrait le texte avec des informations de mise en page.
    
    Args:
        image_path (str): Chemin vers l'image à analyser
        language (str): Code de langue pour l'OCR
        preprocessing (str): Méthode de prétraitement
    
    Returns:
        dict: Dictionnaire contenant le texte et les informations de mise en page
        {
            'text': str,                # Texte complet
            'blocks': List[Dict],       # Blocs de texte avec leurs coordonnées
            'lines': List[Dict],        # Lignes de texte avec leurs coordonnées
            'words': List[Dict],        # Mots avec leurs coordonnées et confiance
            'page_dimensions': (w, h)   # Dimensions de l'image
        }
    
    Raises:
        ValueError: Si Tesseract n'est pas disponible ou si le fichier image est invalide
    """
    if not TESSERACT_AVAILABLE:
        raise ValueError("PyTesseract est nécessaire pour l'extraction de texte")
    
    if not os.path.exists(image_path):
        raise ValueError(f"Le fichier image n'existe pas: {image_path}")
    
    # Prétraitement de l'image
    processed_image_path = image_path
    temp_file = None
    
    try:
        if preprocessing != "none" and CV2_AVAILABLE:
            # Détection automatique du niveau de prétraitement (comme dans extract_text_from_image)
            if preprocessing == "auto":
                img = cv2.imread(image_path)
                if img is None:
                    raise ValueError(f"Impossible de charger l'image: {image_path}")
                
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                min_val, max_val, _, _ = cv2.minMaxLoc(gray)
                contrast = (max_val - min_val) / (max_val + min_val + 1e-10)
                brightness = np.mean(gray)
                
                if laplacian_var > 500 and contrast > 0.5:
                    preprocessing = "low"
                elif laplacian_var > 100 or (contrast > 0.3 and brightness > 100):
                    preprocessing = "medium"
                else:
                    preprocessing = "high"
            
            # Appliquer le prétraitement
            if preprocessing != "none":
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_file.close()
                processed_image_path = enhance_image(image_path, temp_file.name, preprocessing)
        
        # Configurer les options OCR
        custom_config = r'--oem 3 --psm 3'
        
        # Ajouter la spécification de langue
        if language:
            langs = language.split('+')
            valid_langs = []
            
            for lang in langs:
                if lang in AVAILABLE_LANGUAGES:
                    valid_langs.append(lang)
                else:
                    logger.warning(f"Langue '{lang}' non reconnue, ignorée")
            
            if not valid_langs:
                valid_langs.append(DEFAULT_LANGUAGE)
            
            custom_config += f" -l {'+'.join(valid_langs)}"
        
        # Obtenir le texte et les informations de mise en page
        img = cv2.imread(processed_image_path)
        h, w = img.shape[:2]  # Récupérer les dimensions de l'image
        
        # Extraire les données OCR
        ocr_data = pytesseract.image_to_data(processed_image_path, config=custom_config, output_type=Output.DICT)
        
        # Construire le résultat
        result = {
            'text': pytesseract.image_to_string(processed_image_path, config=custom_config),
            'blocks': [],
            'lines': [],
            'words': [],
            'page_dimensions': (w, h)
        }
        
        # Traiter les mots
        n_boxes = len(ocr_data['text'])
        current_block = -1
        current_line = -1
        
        for i in range(n_boxes):
            # Ignorer les textes vides
            if int(ocr_data['conf'][i]) < 0 or not ocr_data['text'][i].strip():
                continue
            
            word = {
                'text': ocr_data['text'][i],
                'confidence': int(ocr_data['conf'][i]),
                'x': ocr_data['left'][i],
                'y': ocr_data['top'][i],
                'width': ocr_data['width'][i],
                'height': ocr_data['height'][i],
                'block_num': ocr_data['block_num'][i],
                'line_num': ocr_data['line_num'][i],
                'word_num': ocr_data['word_num'][i]
            }
            
            result['words'].append(word)
            
            # Traiter les blocs de texte
            if ocr_data['block_num'][i] != current_block:
                current_block = ocr_data['block_num'][i]
                block_text = []
                block_indices = [j for j in range(n_boxes) if ocr_data['block_num'][j] == current_block and ocr_data['text'][j].strip()]
                
                if block_indices:
                    # Calculer la boîte englobante du bloc
                    block_left = min(ocr_data['left'][j] for j in block_indices)
                    block_top = min(ocr_data['top'][j] for j in block_indices)
                    block_right = max(ocr_data['left'][j] + ocr_data['width'][j] for j in block_indices)
                    block_bottom = max(ocr_data['top'][j] + ocr_data['height'][j] for j in block_indices)
                    
                    # Récupérer le texte du bloc
                    for j in sorted(block_indices, key=lambda x: (ocr_data['line_num'][x], ocr_data['word_num'][x])):
                        block_text.append(ocr_data['text'][j])
                    
                    result['blocks'].append({
                        'text': ' '.join(block_text),
                        'x': block_left,
                        'y': block_top,
                        'width': block_right - block_left,
                        'height': block_bottom - block_top,
                        'block_num': current_block
                    })
            
            # Traiter les lignes de texte
            if ocr_data['line_num'][i] != current_line or ocr_data['block_num'][i] != current_block:
                current_line = ocr_data['line_num'][i]
                line_text = []
                line_indices = [j for j in range(n_boxes) if ocr_data['block_num'][j] == current_block and 
                               ocr_data['line_num'][j] == current_line and ocr_data['text'][j].strip()]
                
                if line_indices:
                    # Calculer la boîte englobante de la ligne
                    line_left = min(ocr_data['left'][j] for j in line_indices)
                    line_top = min(ocr_data['top'][j] for j in line_indices)
                    line_right = max(ocr_data['left'][j] + ocr_data['width'][j] for j in line_indices)
                    line_bottom = max(ocr_data['top'][j] + ocr_data['height'][j] for j in line_indices)
                    
                    # Récupérer le texte de la ligne
                    for j in sorted(line_indices, key=lambda x: ocr_data['word_num'][x]):
                        line_text.append(ocr_data['text'][j])
                    
                    result['lines'].append({
                        'text': ' '.join(line_text),
                        'x': line_left,
                        'y': line_top,
                        'width': line_right - line_left,
                        'height': line_bottom - line_top,
                        'block_num': current_block,
                        'line_num': current_line
                    })
        
        return result
    
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de texte avec mise en page: {e}")
        raise
    
    finally:
        # Supprimer le fichier temporaire si créé
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.warning(f"Impossible de supprimer le fichier temporaire: {e}")


def pdf_to_text(pdf_path: str, language: str = DEFAULT_LANGUAGE, 
               preprocessing: str = "auto", page_range: Optional[Tuple[int, int]] = None) -> str:
    """
    Convertit un document PDF en texte en utilisant OCR.
    
    Args:
        pdf_path (str): Chemin vers le document PDF
        language (str): Code de langue pour l'OCR
        preprocessing (str): Méthode de prétraitement
        page_range (tuple, optional): Plage de pages à traiter (début, fin)
    
    Returns:
        str: Texte extrait du PDF
    
    Raises:
        ValueError: Si pdf2image n'est pas disponible ou si le fichier PDF est invalide
    """
    if not PDF2IMAGE_AVAILABLE:
        raise ValueError("pdf2image est nécessaire pour la conversion de PDF en texte")
    
    if not os.path.exists(pdf_path):
        raise ValueError(f"Le fichier PDF n'existe pas: {pdf_path}")
    
    try:
        # Définir la plage de pages
        if page_range:
            first_page, last_page = page_range
        else:
            # Toutes les pages
            first_page = 1
            last_page = None
        
        # Convertir les pages PDF en images
        images = convert_from_path(
            pdf_path,
            first_page=first_page,
            last_page=last_page,
            dpi=300,  # Résolution suffisante pour l'OCR
            fmt='png'
        )
        
        # Extraire le texte de chaque page
        all_text = []
        
        for i, image in enumerate(images):
            # Créer un fichier temporaire pour l'image
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_path = temp_file.name
            
            # Enregistrer l'image
            image.save(temp_path, 'PNG')
            
            # Extraire le texte
            page_text = extract_text_from_image(temp_path, language, preprocessing)
            all_text.append(page_text)
            
            # Supprimer le fichier temporaire
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Impossible de supprimer le fichier temporaire: {e}")
        
        # Joindre le texte de toutes les pages
        full_text = "\n\n".join(all_text)
        
        return full_text
    
    except Exception as e:
        logger.error(f"Erreur lors de la conversion du PDF en texte: {e}")
        raise


def optimize_image_for_ocr(image_path: str, output_path: Optional[str] = None) -> str:
    """
    Optimise une image spécifiquement pour l'OCR en appliquant plusieurs techniques.
    
    Args:
        image_path (str): Chemin vers l'image à optimiser
        output_path (str, optional): Chemin de sortie pour l'image optimisée
    
    Returns:
        str: Chemin vers l'image optimisée
    
    Raises:
        ValueError: Si OpenCV n'est pas disponible ou si le fichier image est invalide
    """
    if not CV2_AVAILABLE:
        raise ValueError("OpenCV (cv2) est nécessaire pour l'optimisation d'image")
    
    if not os.path.exists(image_path):
        raise ValueError(f"Le fichier image n'existe pas: {image_path}")
    
    # Définir le fichier de sortie
    if output_path is None:
        temp_dir = tempfile.gettempdir()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', dir=temp_dir)
        output_path = temp_file.name
        temp_file.close()
    
    try:
        # Charger l'image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Impossible de charger l'image: {image_path}")
        
        # Convertir en niveaux de gris
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Détecter automatiquement les caractéristiques de l'image pour déterminer le traitement
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        histogram = cv2.calcHist([gray], [0], None, [256], [0, 256])
        min_val, max_val, _, _ = cv2.minMaxLoc(gray)
        contrast = (max_val - min_val) / (max_val + min_val + 1e-10)
        mean_val = np.mean(gray)
        
        # Débruitage adaptatif
        if laplacian_var < 200:  # Image bruitée
            # Débruitage plus fort
            gray = cv2.fastNlMeansDenoising(gray, None, h=15, templateWindowSize=7, searchWindowSize=21)
        else:
            # Débruitage léger
            gray = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # Amélioration du contraste
        if contrast < 0.4:
            # Amélioration de contraste plus forte
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
        elif contrast < 0.6:
            # Amélioration de contraste standard
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
        
        # Binarisation adaptative
        # Déterminer le type de document pour choisir la méthode de binarisation
        is_document = mean_val > 200  # Les documents ont généralement un fond clair
        
        if is_document:
            # Méthode adaptative pour les documents textuels
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
        else:
            # Méthode Otsu pour les images générales
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphologie pour nettoyer le bruit et renforcer le texte
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        # Redimensionnement pour améliorer la netteté si nécessaire
        height, width = binary.shape
        min_dpi = 300  # DPI minimum pour un bon OCR
        
        # Si l'image est trop petite, redimensionner
        if width < 1000 or height < 1000:
            scale_factor = max(min_dpi / (width / 8.5), min_dpi / (height / 11))
            if scale_factor > 1:
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                binary = cv2.resize(binary, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Enregistrer l'image optimisée
        cv2.imwrite(output_path, binary)
        
        return output_path
    
    except Exception as e:
        logger.error(f"Erreur lors de l'optimisation de l'image: {e}")
        raise


def detect_document_orientation(image_path: str) -> int:
    """
    Détecte l'orientation d'un document et retourne l'angle de rotation.
    
    Args:
        image_path (str): Chemin vers l'image à analyser
    
    Returns:
        int: Angle de rotation (0, 90, 180, ou 270 degrés)
    
    Raises:
        ValueError: Si Tesseract n'est pas disponible ou si le fichier image est invalide
    """
    if not TESSERACT_AVAILABLE:
        raise ValueError("PyTesseract est nécessaire pour la détection d'orientation")
    
    if not os.path.exists(image_path):
        raise ValueError(f"Le fichier image n'existe pas: {image_path}")
    
    try:
        # Utilisez l'OSD (Orientation and Script Detection) de Tesseract
        osd_data = pytesseract.image_to_osd(image_path)
        
        # Extraire l'angle de rotation
        rotation_match = re.search(r'Rotate: (\d+)', osd_data)
        if rotation_match:
            rotation_angle = int(rotation_match.group(1))
            return rotation_angle
        
        return 0  # Par défaut: pas de rotation
    
    except Exception as e:
        logger.error(f"Erreur lors de la détection d'orientation: {e}")
        # En cas d'erreur, supposer qu'il n'y a pas de rotation
        return 0


def correct_image_orientation(image_path: str, output_path: Optional[str] = None) -> str:
    """
    Corrige l'orientation d'une image de document en la faisant pivoter si nécessaire.
    
    Args:
        image_path (str): Chemin vers l'image à corriger
        output_path (str, optional): Chemin de sortie pour l'image corrigée
    
    Returns:
        str: Chemin vers l'image corrigée
    
    Raises:
        ValueError: Si OpenCV n'est pas disponible ou si le fichier image est invalide
    """
    if not CV2_AVAILABLE:
        raise ValueError("OpenCV (cv2) est nécessaire pour la correction d'orientation")
    
    if not TESSERACT_AVAILABLE:
        raise ValueError("PyTesseract est nécessaire pour la détection d'orientation")
    
    if not os.path.exists(image_path):
        raise ValueError(f"Le fichier image n'existe pas: {image_path}")
    
    # Définir le fichier de sortie
    if output_path is None:
        temp_dir = tempfile.gettempdir()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', dir=temp_dir)
        output_path = temp_file.name
        temp_file.close()
    
    try:
        # Détecter l'orientation
        angle = detect_document_orientation(image_path)
        
        # Si l'orientation est correcte (0°), copier simplement l'image
        if angle == 0:
            img = cv2.imread(image_path)
            cv2.imwrite(output_path, img)
            return output_path
        
        # Charger l'image et la faire pivoter
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Impossible de charger l'image: {image_path}")
        
        # Rotation de l'image
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        
        # La rotation doit être dans le sens inverse pour corriger
        correction_angle = -angle
        rotation_matrix = cv2.getRotationMatrix2D(center, correction_angle, 1.0)
        
        # Calculer les nouvelles dimensions après rotation
        abs_cos = abs(rotation_matrix[0, 0])
        abs_sin = abs(rotation_matrix[0, 1])
        new_w = int(h * abs_sin + w * abs_cos)
        new_h = int(h * abs_cos + w * abs_sin)
        
        # Ajuster la matrice de rotation
        rotation_matrix[0, 2] += new_w / 2 - center[0]
        rotation_matrix[1, 2] += new_h / 2 - center[1]
        
        # Effectuer la rotation
        rotated_img = cv2.warpAffine(img, rotation_matrix, (new_w, new_h), flags=cv2.INTER_CUBIC)
        
        # Enregistrer l'image corrigée
        cv2.imwrite(output_path, rotated_img)
        
        return output_path
    
    except Exception as e:
        logger.error(f"Erreur lors de la correction d'orientation: {e}")
        raise


def detect_text_regions(image_path: str) -> List[Dict[str, Any]]:
    """
    Détecte les régions contenant du texte dans une image.
    
    Args:
        image_path (str): Chemin vers l'image à analyser
    
    Returns:
        list: Liste des régions détectées
        [
            {
                'x': x,          # Coordonnée X du coin supérieur gauche
                'y': y,          # Coordonnée Y du coin supérieur gauche
                'width': w,      # Largeur de la région
                'height': h,     # Hauteur de la région
                'confidence': c  # Score de confiance (0-100)
            },
            ...
        ]
    
    Raises:
        ValueError: Si OpenCV n'est pas disponible ou si le fichier image est invalide
    """
    if not CV2_AVAILABLE:
        raise ValueError("OpenCV (cv2) est nécessaire pour la détection de régions de texte")
    
    if not os.path.exists(image_path):
        raise ValueError(f"Le fichier image n'existe pas: {image_path}")
    
    try:
        # Charger l'image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Impossible de charger l'image: {image_path}")
        
        # Convertir en niveaux de gris
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Application d'un flou gaussien pour réduire le bruit
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Détection des bords
        edges = cv2.Canny(blurred, 50, 150)
        
        # Dilatation pour fermer les contours
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Trouver les contours
        contours, _ = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrer et regrouper les contours pour identifier les régions de texte
        text_regions = []
        min_area = 500  # Surface minimale pour éviter les petits bruits
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            
            # Ignorer les contours trop petits
            if area < min_area:
                continue
            
            # Ignorer les contours trop grands (probablement pas du texte)
            if area > img.shape[0] * img.shape[1] * 0.5:
                continue
            
            # Ignorer les régions trop larges ou trop hautes
            aspect_ratio = float(w) / h
            if aspect_ratio > 15 or aspect_ratio < 0.1:
                continue
            
            # Calculer un score de confiance basé sur la densité de bords dans la région
            roi = edges[y:y+h, x:x+w]
            edge_density = np.sum(roi > 0) / (w * h)
            confidence = min(100, int(edge_density * 200))  # Échelle de 0 à 100
            
            text_regions.append({
                'x': x,
                'y': y,
                'width': w,
                'height': h,
                'confidence': confidence
            })
        
        # Trier par position (haut vers bas, gauche vers droite)
        text_regions.sort(key=lambda r: (r['y'], r['x']))
        
        return text_regions
    
    except Exception as e:
        logger.error(f"Erreur lors de la détection des régions de texte: {e}")
        raise


def extract_text_from_regions(image_path: str, regions: List[Dict[str, Any]], 
                             language: str = DEFAULT_LANGUAGE) -> Dict[str, str]:
    """
    Extrait le texte de régions spécifiques d'une image.
    
    Args:
        image_path (str): Chemin vers l'image à analyser
        regions (list): Liste des régions à extraire
        language (str): Code de langue pour l'OCR
    
    Returns:
        dict: Dictionnaire associant chaque région à son texte extrait
        {
            'region_0': 'texte extrait de la région 0',
            'region_1': 'texte extrait de la région 1',
            ...
        }
    
    Raises:
        ValueError: Si Tesseract ou OpenCV n'est pas disponible
    """
    if not TESSERACT_AVAILABLE:
        raise ValueError("PyTesseract est nécessaire pour l'extraction de texte")
    
    if not CV2_AVAILABLE:
        raise ValueError("OpenCV (cv2) est nécessaire pour le traitement des régions")
    
    if not os.path.exists(image_path):
        raise ValueError(f"Le fichier image n'existe pas: {image_path}")
    
    try:
        # Charger l'image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Impossible de charger l'image: {image_path}")
        
        # Configurer les options OCR
        custom_config = r'--oem 3 --psm 6'  # PSM 6: Supposer un bloc de texte uniforme
        
        # Ajouter la spécification de langue
        if language:
            langs = language.split('+')
            valid_langs = []
            
            for lang in langs:
                if lang in AVAILABLE_LANGUAGES:
                    valid_langs.append(lang)
                else:
                    logger.warning(f"Langue '{lang}' non reconnue, ignorée")
            
            if not valid_langs:
                valid_langs.append(DEFAULT_LANGUAGE)
            
            custom_config += f" -l {'+'.join(valid_langs)}"
        
        # Extraire le texte de chaque région
        results = {}
        
        for i, region in enumerate(regions):
            x, y, w, h = region['x'], region['y'], region['width'], region['height']
            
            # Extraire la région
            roi = img[y:y+h, x:x+w]
            
            # Prétraiter la région pour améliorer l'OCR
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Amélioration de contraste adaptative
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced_roi = clahe.apply(gray_roi)
            
            # Créer un fichier temporaire pour la région
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_path = temp_file.name
            
            # Enregistrer la région
            cv2.imwrite(temp_path, enhanced_roi)
            
            # Extraire le texte
            region_text = pytesseract.image_to_string(temp_path, config=custom_config)
            results[f"region_{i}"] = region_text.strip()
            
            # Supprimer le fichier temporaire
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Impossible de supprimer le fichier temporaire: {e}")
        
        return results
    
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de texte des régions: {e}")
        raise


def get_available_languages() -> List[str]:
    """
    Récupère la liste des langues disponibles pour l'OCR.
    
    Returns:
        list: Liste des codes de langue disponibles
    """
    if not TESSERACT_AVAILABLE:
        logger.warning("PyTesseract n'est pas disponible")
        return []
    
    try:
        # Récupérer la liste des langues installées
        output = pytesseract.get_languages()
        return output
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des langues disponibles: {e}")
        return AVAILABLE_LANGUAGES  # Retourner la liste par défaut


def set_tesseract_path(path: str) -> bool:
    """
    Définit le chemin vers l'exécutable Tesseract.
    
    Args:
        path (str): Chemin vers l'exécutable Tesseract
        
    Returns:
        bool: True si le chemin est valide, False sinon
    """
    global TESSERACT_AVAILABLE
    
    if not os.path.exists(path):
        logger.error(f"Le chemin Tesseract spécifié n'existe pas: {path}")
        return False
    
    try:
        # Définir le chemin Tesseract
        pytesseract.pytesseract.tesseract_cmd = path
        
        # Vérifier que le chemin fonctionne
        pytesseract.get_tesseract_version()
        TESSERACT_AVAILABLE = True
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la configuration du chemin Tesseract: {e}")
        TESSERACT_AVAILABLE = False
        return False


def is_ocr_available() -> bool:
    """
    Vérifie si la fonctionnalité OCR est disponible.
    
    Returns:
        bool: True si OCR est disponible, False sinon
    """
    return TESSERACT_AVAILABLE


def install_language(language_code: str) -> bool:
    """
    Tente d'installer un pack de langue pour Tesseract.
    Note: Cette fonction nécessite généralement des privilèges administratifs.
    
    Args:
        language_code (str): Code de langue à installer
        
    Returns:
        bool: True si l'installation a réussi, False sinon
    """
    if not TESSERACT_AVAILABLE:
        logger.error("Tesseract n'est pas disponible, impossible d'installer des langues")
        return False
    
    if language_code in get_available_languages():
        logger.info(f"La langue {language_code} est déjà installée")
        return True
    
    # Déterminer le système d'exploitation
    if sys.platform.startswith('win'):
        logger.error("L'installation automatique de langues n'est pas supportée sous Windows")
        logger.info("Veuillez télécharger et installer manuellement le pack de langue depuis https://github.com/tesseract-ocr/tessdata")
        return False
    
    elif sys.platform.startswith('linux'):
        try:
            # Tenter d'installer via apt (distributions basées sur Debian/Ubuntu)
            import subprocess
            logger.info(f"Tentative d'installation du pack de langue {language_code}...")
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', f'tesseract-ocr-{language_code}', '-y'], check=True)
            return language_code in get_available_languages()
        except Exception as e:
            logger.error(f"Erreur lors de l'installation du pack de langue: {e}")
            return False
    
    elif sys.platform == 'darwin':  # macOS
        try:
            # Tenter d'installer via Homebrew
            import subprocess
            logger.info(f"Tentative d'installation du pack de langue {language_code}...")
            subprocess.run(['brew', 'install', f'tesseract-lang'], check=True)
            return language_code in get_available_languages()
        except Exception as e:
            logger.error(f"Erreur lors de l'installation du pack de langue: {e}")
            return False
    
    else:
        logger.error(f"Système d'exploitation non supporté pour l'installation automatique: {sys.platform}")
        return False


# Fonction principale pour extraire du texte à partir d'un fichier
def extract_text(file_path: str, language: str = DEFAULT_LANGUAGE, 
                preprocessing: str = "auto", page_range: Optional[Tuple[int, int]] = None) -> str:
    """
    Extrait le texte d'un fichier image ou PDF.
    
    Args:
        file_path (str): Chemin vers le fichier à analyser
        language (str): Code de langue pour l'OCR
        preprocessing (str): Méthode de prétraitement
        page_range (tuple, optional): Plage de pages à traiter pour les PDF
    
    Returns:
        str: Texte extrait du fichier
    
    Raises:
        ValueError: Si le format de fichier n'est pas supporté ou si les dépendances sont manquantes
    """
    if not os.path.exists(file_path):
        raise ValueError(f"Le fichier n'existe pas: {file_path}")
    
    # Déterminer le type de fichier
    file_extension = os.path.splitext(file_path)[1].lower()
    
    # Traitement selon le type de fichier
    if file_extension in ['.pdf']:
        # Vérifier que la conversion PDF est disponible
        if not PDF2IMAGE_AVAILABLE:
            raise ValueError("pdf2image est nécessaire pour la conversion de PDF en texte")
        
        return pdf_to_text(file_path, language, preprocessing, page_range)
    
    elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']:
        # Vérifier que l'OCR est disponible
        if not TESSERACT_AVAILABLE:
            raise ValueError("PyTesseract est nécessaire pour l'extraction de texte")
        
        return extract_text_from_image(file_path, language, preprocessing)
    
    else:
        raise ValueError(f"Format de fichier non supporté: {file_extension}")


if __name__ == "__main__":
    # Script de test et d'exemple
    import argparse
    
    parser = argparse.ArgumentParser(description="Module OCR pour extraction de texte")
    parser.add_argument("file", help="Chemin vers le fichier à analyser")
    parser.add_argument("--output", "-o", help="Chemin pour le fichier de sortie (texte extrait)")
    parser.add_argument("--language", "-l", default=DEFAULT_LANGUAGE, help="Code de langue pour l'OCR")
    parser.add_argument("--preprocessing", "-p", default="auto", choices=["none", "auto", "low", "medium", "high", "extreme"],
                      help="Méthode de prétraitement")
    parser.add_argument("--enhance", "-e", action="store_true", help="Optimiser l'image pour l'OCR")
    parser.add_argument("--orientation", "-r", action="store_true", help="Corriger l'orientation de l'image")
    parser.add_argument("--regions", "-g", action="store_true", help="Détecter et extraire par régions")
    
    args = parser.parse_args()
    
    # Configurer le logger
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Vérifier si l'OCR est disponible
    if not is_ocr_available():
        print("ERREUR: OCR non disponible. Vérifiez que Tesseract est installé et correctement configuré.")
        sys.exit(1)
    
    try:
        processed_file = args.file
        
        # Appliquer les prétraitements si demandé
        if args.enhance and (args.file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'))):
            print("Optimisation de l'image pour l'OCR...")
            enhanced_file = optimize_image_for_ocr(args.file)
            processed_file = enhanced_file
            print(f"Image optimisée enregistrée dans: {enhanced_file}")
        
        if args.orientation and (processed_file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'))):
            print("Correction de l'orientation...")
            corrected_file = correct_image_orientation(processed_file)
            processed_file = corrected_file
            print(f"Image avec orientation corrigée enregistrée dans: {corrected_file}")
        
        # Si extraction par régions demandée
        if args.regions and (processed_file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'))):
            print("Détection des régions de texte...")
            regions = detect_text_regions(processed_file)
            print(f"Nombre de régions détectées: {len(regions)}")
            
            print("Extraction du texte par région...")
            region_texts = extract_text_from_regions(processed_file, regions, args.language)
            
            # Afficher ou enregistrer les résultats
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    for region_id, text in region_texts.items():
                        f.write(f"=== {region_id} ===\n")
                        f.write(text)
                        f.write("\n\n")
                print(f"Texte par régions enregistré dans: {args.output}")
            else:
                for region_id, text in region_texts.items():
                    print(f"=== {region_id} ===")
                    print(text)
                    print()
        
        else:
            # Extraction de texte normale
            print(f"Extraction de texte du fichier: {processed_file}")
            print(f"Langue: {args.language}, Prétraitement: {args.preprocessing}")
            
            text = extract_text(processed_file, args.language, args.preprocessing)
            
            # Afficher ou enregistrer le résultat
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"Texte extrait enregistré dans: {args.output}")
            else:
                print("\n=== TEXTE EXTRAIT ===")
                print(text)
    
    except Exception as e:
        print(f"ERREUR: {e}")
        sys.exit(1)