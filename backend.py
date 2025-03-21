from fastapi import FastAPI, File, UploadFile, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import pandas as pd
from io import BytesIO
import logging
from datetime import datetime
from typing import List, Optional
import json
import pytesseract
from PIL import Image
import docx
from docx import Document
import magic
import spacy
import nltk
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import uuid

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration de l'application
app = FastAPI(
    title="Vynal Docs Automator API",
    description="API pour l'automatisation de la gestion des documents",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration des dossiers
UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"
TEMP_DIR = "temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Montage des fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialisation des modèles NLP
try:
    nlp = spacy.load("fr_core_news_sm")
except:
    logger.warning("Modèle spaCy non trouvé, téléchargement en cours...")
    os.system("python -m spacy download fr_core_news_sm")
    nlp = spacy.load("fr_core_news_sm")

# Fonctions d'extraction de texte
def extract_text_from_docx(file_path):
    """Extrait le texte d'un document Word"""
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte DOCX: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'extraction du texte du document Word"
        )

def extract_text_from_csv(file_path):
    """Extrait le texte d'un fichier CSV"""
    try:
        df = pd.read_csv(file_path)
        return df.to_string()
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte CSV: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'extraction du texte du fichier CSV"
        )

def extract_text_from_image(file_path):
    """Extrait le texte d'une image avec OCR"""
    try:
        text = pytesseract.image_to_string(Image.open(file_path), lang='fra')
        return text
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte de l'image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'extraction du texte de l'image"
        )

# Gestion des erreurs globale
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erreur non gérée: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Une erreur interne s'est produite", "error": str(exc)}
    )

@app.get("/")
async def home():
    """Endpoint d'accueil de l'API"""
    return {
        "message": "Bienvenue sur l'API Vynal Docs Automator",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "upload": "/upload/",
            "files": "/files/",
            "process": "/process/{filename}",
            "analyze": "/analyze/{filename}"
        }
    }

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint pour l'upload de fichiers
    - Accepte les fichiers CSV, DOCX, PDF et images
    - Valide le contenu
    - Sauvegarde le fichier
    - Retourne les informations du fichier
    """
    try:
        # Lecture du contenu du fichier
        content = await file.read()
        
        # Détection du type de fichier
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(content)
        
        # Validation du type de fichier
        allowed_types = [
            'text/csv',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/tiff'
        ]
        
        if file_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Type de fichier non supporté: {file_type}"
            )

        # Sauvegarde du fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # Extraction du texte selon le type de fichier
        text = ""
        if file.filename.endswith(".docx"):
            text = extract_text_from_docx(file_path)
        elif file.filename.endswith(".csv"):
            text = extract_text_from_csv(file_path)
        elif file_type.startswith('image/'):
            text = extract_text_from_image(file_path)

        logger.info(f"Fichier {safe_filename} uploadé et traité avec succès")
        
        return {
            "message": "Fichier reçu et traité avec succès",
            "filename": safe_filename,
            "type": file_type,
            "timestamp": timestamp,
            "content": text if text else None
        }

    except Exception as e:
        logger.error(f"Erreur lors de l'upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement du fichier: {str(e)}"
        )

@app.post("/process/{filename}")
async def process_file(filename: str, background_tasks: BackgroundTasks):
    """
    Traite un fichier uploadé
    - Extraction de texte pour les images (OCR)
    - Conversion de format si nécessaire
    - Analyse du contenu
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Fichier non trouvé"
            )

        # Détection du type de fichier
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        
        # Traitement selon le type de fichier
        if file_type.startswith('image/'):
            # OCR pour les images
            text = extract_text_from_image(file_path)
            processed_path = os.path.join(PROCESSED_DIR, f"{filename}_text.txt")
            with open(processed_path, 'w', encoding='utf-8') as f:
                f.write(text)
                
        elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            # Traitement des documents Word
            text = extract_text_from_docx(file_path)
            processed_path = os.path.join(PROCESSED_DIR, f"{filename}_text.txt")
            with open(processed_path, 'w', encoding='utf-8') as f:
                f.write(text)
                
        else:
            # Copie simple pour les autres types
            processed_path = os.path.join(PROCESSED_DIR, filename)
            shutil.copy2(file_path, processed_path)

        return {
            "message": "Fichier traité avec succès",
            "processed_file": processed_path,
            "type": file_type
        }

    except Exception as e:
        logger.error(f"Erreur lors du traitement: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement du fichier: {str(e)}"
        )

@app.get("/analyze/{filename}")
async def analyze_file(filename: str):
    """
    Analyse le contenu d'un fichier
    - Extraction des entités nommées
    - Analyse des sentiments
    - Statistiques de base
    """
    try:
        file_path = os.path.join(PROCESSED_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Fichier non trouvé"
            )

        # Lecture du contenu
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Analyse avec spaCy
        doc = nlp(text)
        
        # Extraction des entités
        entities = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })

        # Statistiques de base
        words = text.split()
        sentences = nltk.sent_tokenize(text)
        
        stats = {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_word_length": sum(len(word) for word in words) / len(words) if words else 0,
            "unique_words": len(set(words))
        }

        return {
            "filename": filename,
            "entities": entities,
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse du fichier: {str(e)}"
        )

@app.get("/files/")
async def list_files():
    """Liste tous les fichiers uploadés"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            file_stat = os.stat(file_path)
            files.append({
                "filename": filename,
                "size": file_stat.st_size,
                "upload_date": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            })
        return {"files": files}
    except Exception as e:
        logger.error(f"Erreur lors de la liste des fichiers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération de la liste des fichiers"
        )

@app.get("/files/{filename}")
async def get_file_info(filename: str):
    """Récupère les informations d'un fichier spécifique"""
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Fichier non trouvé"
            )
        
        file_stat = os.stat(file_path)
        return {
            "filename": filename,
            "size": file_stat.st_size,
            "upload_date": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "path": file_path
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des infos du fichier: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des informations du fichier"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
