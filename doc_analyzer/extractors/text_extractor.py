import shutil
from PIL import Image
import pytesseract
from log import logger

def extract_text_from_image(image_path):
    """Extrait le texte d'une image"""
    try:
        # Vérifier si Tesseract est disponible
        if not shutil.which("tesseract"):
            return {
                "success": False,
                "error": "L'extraction de texte n'est pas disponible (Tesseract non installé)",
                "text": "",
                "requires_tesseract": True
            }
        
        # Charger l'image avec PIL
        image = Image.open(image_path)
        
        # Extraire le texte avec Tesseract
        text = pytesseract.image_to_string(image, lang='fra+eng')
        
        return {
            "success": True,
            "text": text,
            "error": None,
            "requires_tesseract": True
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte: {e}")
        return {
            "success": False,
            "error": str(e),
            "text": "",
            "requires_tesseract": True
        } 