#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitaires de gestion des PDF pour l'application Vynal Docs Automator
Ce module fournit des fonctions pour créer, manipuler et extraire des informations des PDF
"""

import os
import io
import logging
import tempfile
from datetime import datetime

# Bibliothèques pour la manipulation des PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm, inch
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, Image, SimpleDocTemplate, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# Pour la fusion et manipulation de PDF existants
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logging.warning("PyPDF2 n'est pas installé. Certaines fonctionnalités PDF seront limitées.")

# Pour extraire du texte des PDF
try:
    import pdfminer
    from pdfminer.high_level import extract_text
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False
    logging.warning("pdfminer.six n'est pas installé. L'extraction de texte des PDF sera limitée.")

logger = logging.getLogger("VynalDocsAutomator.PDFUtils")

class PDFUtils:
    """
    Utilitaires pour la gestion des fichiers PDF
    """
    
    @staticmethod
    def create_simple_pdf(file_path, title, content, author=None, subject=None):
        """
        Crée un PDF simple avec un titre et du contenu texte
        
        Args:
            file_path: Chemin de sauvegarde du PDF
            title: Titre du document
            content: Contenu du document (texte simple)
            author: Auteur du document (métadonnée)
            subject: Sujet du document (métadonnée)
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Création du PDF
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # Métadonnées
            c.setTitle(title)
            if author:
                c.setAuthor(author)
            if subject:
                c.setSubject(subject)
            
            # Titre
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, title)
            
            # Contenu
            c.setFont("Helvetica", 12)
            y_position = height - 80
            
            # Traiter le contenu ligne par ligne
            for line in content.split('\n'):
                # Vérifier s'il reste assez d'espace sur la page
                if y_position < 50:  # Marge de bas de page
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y_position = height - 50
                
                c.drawString(50, y_position, line)
                y_position -= 15  # Espacement des lignes
            
            # Finalisation du document
            c.showPage()
            c.save()
            
            # Écriture du fichier
            with open(file_path, 'wb') as f:
                f.write(buffer.getvalue())
            
            logger.info(f"PDF simple créé : {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du PDF : {e}")
            return False
    
    @staticmethod
    def create_advanced_pdf(file_path, elements, metadata=None, page_size=A4, margins=(cm, cm, cm, cm)):
        """
        Crée un PDF avancé avec des éléments de mise en page complexes
        
        Args:
            file_path: Chemin de sauvegarde du PDF
            elements: Liste d'éléments Platypus (Paragraph, Table, Image, etc.)
            metadata: Dictionnaire de métadonnées (title, author, subject, etc.)
            page_size: Taille de page (A4, letter, etc.)
            margins: Marges (gauche, droite, haut, bas) en points
            
        Returns:
            bool: True si réussi, False sinon
        """
        try:
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Métadonnées par défaut
            if metadata is None:
                metadata = {}
            
            # Création du document
            doc = SimpleDocTemplate(
                file_path,
                pagesize=page_size,
                leftMargin=margins[0],
                rightMargin=margins[1],
                topMargin=margins[2],
                bottomMargin=margins[3],
                title=metadata.get('title', ''),
                author=metadata.get('author', ''),
                subject=metadata.get('subject', ''),
                creator=metadata.get('creator', 'Vynal Docs Automator')
            )
            
            # Construction du document
            doc.build(elements)
            
            logger.info(f"PDF avancé créé : {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du PDF avancé : {e}")
            return False
    
    @staticmethod
    def extract_text_from_pdf(file_path, page_numbers=None):
        """
        Extrait le texte d'un fichier PDF
        
        Args:
            file_path: Chemin du fichier PDF
            page_numbers: Liste des numéros de page à extraire (None = toutes les pages)
            
        Returns:
            str: Texte extrait du PDF ou None en cas d'erreur
        """
        if not PDFMINER_AVAILABLE:
            logger.error("Impossible d'extraire le texte : pdfminer.six n'est pas installé")
            return None
        
        try:
            # Vérifier que le fichier existe
            if not os.path.exists(file_path):
                logger.error(f"Le fichier PDF n'existe pas : {file_path}")
                return None
            
            # Extraire le texte
            if page_numbers is None:
                # Extraire toutes les pages
                text = extract_text(file_path)
            else:
                # Extraire les pages spécifiées
                text = ""
                for page_num in page_numbers:
                    page_text = extract_text(file_path, page_numbers=[page_num])
                    text += f"--- Page {page_num} ---\n{page_text}\n\n"
            
            return text
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du texte du PDF : {e}")
            return None
    
    @staticmethod
    def merge_pdfs(input_paths, output_path):
        """
        Fusionne plusieurs fichiers PDF en un seul
        
        Args:
            input_paths: Liste des chemins des fichiers PDF à fusionner
            output_path: Chemin du fichier PDF de sortie
            
        Returns:
            bool: True si réussi, False sinon
        """
        if not PYPDF2_AVAILABLE:
            logger.error("Impossible de fusionner des PDF : PyPDF2 n'est pas installé")
            return False
        
        try:
            # Vérifier que tous les fichiers existent
            for file_path in input_paths:
                if not os.path.exists(file_path):
                    logger.error(f"Le fichier PDF n'existe pas : {file_path}")
                    return False
            
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Fusionner les PDF
            pdf_merger = PyPDF2.PdfMerger()
            
            for file_path in input_paths:
                with open(file_path, 'rb') as f:
                    pdf_merger.append(f)
            
            # Écrire le fichier de sortie
            with open(output_path, 'wb') as f:
                pdf_merger.write(f)
            
            logger.info(f"Fusion de {len(input_paths)} PDF vers {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la fusion des PDF : {e}")
            return False
    
    @staticmethod
    def split_pdf(input_path, output_dir, prefix=None):
        """
        Divise un fichier PDF en plusieurs fichiers (un par page)
        
        Args:
            input_path: Chemin du fichier PDF à diviser
            output_dir: Répertoire de sortie pour les fichiers générés
            prefix: Préfixe pour les noms de fichiers (None = nom du fichier d'origine)
            
        Returns:
            list: Liste des chemins des fichiers générés ou None en cas d'erreur
        """
        if not PYPDF2_AVAILABLE:
            logger.error("Impossible de diviser un PDF : PyPDF2 n'est pas installé")
            return None
        
        try:
            # Vérifier que le fichier existe
            if not os.path.exists(input_path):
                logger.error(f"Le fichier PDF n'existe pas : {input_path}")
                return None
            
            # Créer le répertoire de sortie si nécessaire
            os.makedirs(output_dir, exist_ok=True)
            
            # Préfixe par défaut
            if prefix is None:
                prefix = os.path.splitext(os.path.basename(input_path))[0]
            
            # Ouvrir le PDF
            with open(input_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                total_pages = len(pdf_reader.pages)
                
                # Créer un fichier par page
                output_files = []
                for page_num in range(total_pages):
                    output_file = os.path.join(output_dir, f"{prefix}_page{page_num+1:03d}.pdf")
                    
                    pdf_writer = PyPDF2.PdfWriter()
                    pdf_writer.add_page(pdf_reader.pages[page_num])
                    
                    with open(output_file, 'wb') as out_f:
                        pdf_writer.write(out_f)
                    
                    output_files.append(output_file)
            
            logger.info(f"PDF divisé en {total_pages} fichiers dans {output_dir}")
            return output_files
            
        except Exception as e:
            logger.error(f"Erreur lors de la division du PDF : {e}")
            return None
    
    @staticmethod
    def add_watermark(input_path, output_path, watermark_text, font=None, size=60, color=colors.lightgrey, opacity=0.5, angle=45):
        """
        Ajoute un filigrane (watermark) à chaque page d'un PDF
        
        Args:
            input_path: Chemin du fichier PDF d'origine
            output_path: Chemin du fichier PDF de sortie
            watermark_text: Texte du filigrane
            font: Police (None = Helvetica)
            size: Taille de la police
            color: Couleur du filigrane
            opacity: Opacité du filigrane (0.0 à 1.0)
            angle: Angle de rotation du filigrane
            
        Returns:
            bool: True si réussi, False sinon
        """
        if not PYPDF2_AVAILABLE:
            logger.error("Impossible d'ajouter un filigrane : PyPDF2 n'est pas installé")
            return False
        
        try:
            # Vérifier que le fichier existe
            if not os.path.exists(input_path):
                logger.error(f"Le fichier PDF n'existe pas : {input_path}")
                return False
            
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Ouvrir le PDF
            with open(input_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                total_pages = len(pdf_reader.pages)
                
                # Créer un fichier temporaire pour le filigrane
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    watermark_path = tmp_file.name
                
                # Créer le filigrane
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                width, height = A4
                
                # Configuration de la police
                if font is None:
                    font = "Helvetica"
                
                c.setFont(font, size)
                c.setFillColor(color)
                c.setFillAlpha(opacity)
                
                # Placer le texte au centre, en rotation
                c.saveState()
                c.translate(width/2, height/2)
                c.rotate(angle)
                c.drawCentredString(0, 0, watermark_text)
                c.restoreState()
                
                c.showPage()
                c.save()
                
                # Écrire le filigrane dans le fichier temporaire
                with open(watermark_path, 'wb') as f:
                    f.write(buffer.getvalue())
                
                # Créer le PDF de sortie
                pdf_writer = PyPDF2.PdfWriter()
                
                # Ajouter chaque page avec le filigrane
                watermark_reader = PyPDF2.PdfReader(watermark_path)
                watermark_page = watermark_reader.pages[0]
                
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    page.merge_page(watermark_page)
                    pdf_writer.add_page(page)
                
                # Écrire le fichier de sortie
                with open(output_path, 'wb') as f:
                    pdf_writer.write(f)
                
                # Supprimer le fichier temporaire
                os.unlink(watermark_path)
            
            logger.info(f"Filigrane ajouté au PDF : {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du filigrane : {e}")
            return False
    
    @staticmethod
    def add_page_numbers(input_path, output_path, position='bottom', font=None, size=10, start_number=1):
        """
        Ajoute des numéros de page à un PDF
        
        Args:
            input_path: Chemin du fichier PDF d'origine
            output_path: Chemin du fichier PDF de sortie
            position: Position des numéros ('bottom', 'top', 'bottom-right', etc.)
            font: Police (None = Helvetica)
            size: Taille de la police
            start_number: Numéro de la première page
            
        Returns:
            bool: True si réussi, False sinon
        """
        if not PYPDF2_AVAILABLE:
            logger.error("Impossible d'ajouter des numéros de page : PyPDF2 n'est pas installé")
            return False
        
        try:
            # Vérifier que le fichier existe
            if not os.path.exists(input_path):
                logger.error(f"Le fichier PDF n'existe pas : {input_path}")
                return False
            
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Ouvrir le PDF
            with open(input_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                total_pages = len(pdf_reader.pages)
                
                # Créer le PDF de sortie
                pdf_writer = PyPDF2.PdfWriter()
                
                # Configuration de la police
                if font is None:
                    font = "Helvetica"
                
                # Pour chaque page
                for page_num in range(total_pages):
                    # Créer un fichier temporaire pour le numéro de page
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                        page_number_path = tmp_file.name
                    
                    # Créer le numéro de page
                    buffer = io.BytesIO()
                    c = canvas.Canvas(buffer, pagesize=A4)
                    width, height = A4
                    
                    c.setFont(font, size)
                    
                    # Position du numéro
                    page_text = f"Page {page_num+start_number}"
                    
                    if position == 'bottom':
                        c.drawCentredString(width/2, 20, page_text)
                    elif position == 'top':
                        c.drawCentredString(width/2, height-20, page_text)
                    elif position == 'bottom-right':
                        c.drawRightString(width-20, 20, page_text)
                    elif position == 'bottom-left':
                        c.drawString(20, 20, page_text)
                    elif position == 'top-right':
                        c.drawRightString(width-20, height-20, page_text)
                    elif position == 'top-left':
                        c.drawString(20, height-20, page_text)
                    else:
                        c.drawCentredString(width/2, 20, page_text)
                    
                    c.showPage()
                    c.save()
                    
                    # Écrire le numéro de page dans le fichier temporaire
                    with open(page_number_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    
                    # Fusionner la page avec le numéro de page
                    page = pdf_reader.pages[page_num]
                    
                    number_reader = PyPDF2.PdfReader(page_number_path)
                    number_page = number_reader.pages[0]
                    
                    page.merge_page(number_page)
                    pdf_writer.add_page(page)
                    
                    # Supprimer le fichier temporaire
                    os.unlink(page_number_path)
                
                # Écrire le fichier de sortie
                with open(output_path, 'wb') as f:
                    pdf_writer.write(f)
            
            logger.info(f"Numéros de page ajoutés au PDF : {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des numéros de page : {e}")
            return False
    
    @staticmethod
    def encrypt_pdf(input_path, output_path, user_password=None, owner_password=None, permissions=None):
        """
        Crypte un fichier PDF avec mot de passe
        
        Args:
            input_path: Chemin du fichier PDF d'origine
            output_path: Chemin du fichier PDF de sortie
            user_password: Mot de passe utilisateur (pour ouvrir le PDF)
            owner_password: Mot de passe propriétaire (pour les permissions)
            permissions: Dictionnaire de permissions (print, modify, copy, etc.)
            
        Returns:
            bool: True si réussi, False sinon
        """
        if not PYPDF2_AVAILABLE:
            logger.error("Impossible de crypter un PDF : PyPDF2 n'est pas installé")
            return False
        
        try:
            # Vérifier que le fichier existe
            if not os.path.exists(input_path):
                logger.error(f"Le fichier PDF n'existe pas : {input_path}")
                return False
            
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Permissions par défaut
            if permissions is None:
                permissions = {}
            
            # Ouvrir le PDF
            with open(input_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                # Créer le PDF de sortie
                pdf_writer = PyPDF2.PdfWriter()
                
                # Copier chaque page
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
                
                # Crypter le PDF
                pdf_writer.encrypt(
                    user_password=user_password,
                    owner_password=owner_password if owner_password else user_password,
                    use_128bit=True
                )
                
                # Écrire le fichier de sortie
                with open(output_path, 'wb') as f:
                    pdf_writer.write(f)
            
            logger.info(f"PDF crypté : {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du cryptage du PDF : {e}")
            return False
    
    @staticmethod
    def get_pdf_info(file_path):
        """
        Récupère les informations sur un fichier PDF
        
        Args:
            file_path: Chemin du fichier PDF
            
        Returns:
            dict: Dictionnaire d'informations sur le PDF ou None en cas d'erreur
        """
        if not PYPDF2_AVAILABLE:
            logger.error("Impossible de récupérer les informations : PyPDF2 n'est pas installé")
            return None
        
        try:
            # Vérifier que le fichier existe
            if not os.path.exists(file_path):
                logger.error(f"Le fichier PDF n'existe pas : {file_path}")
                return None
            
            # Ouvrir le PDF
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                # Récupérer les informations
                info = {}
                
                # Métadonnées
                metadata = pdf_reader.metadata
                if metadata:
                    for key, value in metadata.items():
                        # Nettoyer les clés (enlever le préfixe '/') et les valeurs
                        clean_key = key.lower().lstrip('/')
                        info[clean_key] = value
                
                # Nombre de pages
                info['pages'] = len(pdf_reader.pages)
                
                # Taille du fichier
                info['file_size'] = os.path.getsize(file_path)
                
                # Format file_size en texte lisible
                if info['file_size'] < 1024:
                    info['file_size_text'] = f"{info['file_size']} B"
                elif info['file_size'] < 1024 * 1024:
                    info['file_size_text'] = f"{info['file_size'] / 1024:.1f} KB"
                else:
                    info['file_size_text'] = f"{info['file_size'] / (1024 * 1024):.1f} MB"
                
                # Sécurité
                info['encrypted'] = pdf_reader.is_encrypted
                
                # Taille de la première page (en points)
                if len(pdf_reader.pages) > 0:
                    page = pdf_reader.pages[0]
                    if '/MediaBox' in page:
                        media_box = page['/MediaBox']
                        info['page_size'] = {
                            'width': float(media_box[2]),
                            'height': float(media_box[3])
                        }
                
                return info
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des informations du PDF : {e}")
            return None