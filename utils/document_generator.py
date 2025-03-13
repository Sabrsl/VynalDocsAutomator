#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Générateur de documents pour l'application Vynal Docs Automator
Ce module contient des utilitaires pour générer des documents PDF et DOCX à partir de modèles
"""

import os
import re
import logging
from datetime import datetime
import io

# Pour les documents PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm, inch
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# Pour les documents Word
import docx
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn

logger = logging.getLogger("VynalDocsAutomator.DocumentGenerator")

class DocumentGenerator:
    """
    Générateur de documents pour l'application
    """
    
    def __init__(self, config_manager=None):
        """
        Initialise le générateur de documents
        
        Args:
            config_manager: Gestionnaire de configuration
        """
        self.config = config_manager
        logger.info("DocumentGenerator initialisé")
    
    def replace_variables(self, content, variables):
        """
        Remplace les variables dans un contenu
        
        Args:
            content: Contenu avec variables (format: {variable})
            variables: Dictionnaire des variables et leurs valeurs
            
        Returns:
            str: Contenu avec variables remplacées
        """
        # Si le contenu n'est pas une chaîne, le convertir
        if not isinstance(content, str):
            content = str(content)
        
        # Préparation des valeurs pour éviter les valeurs None
        safe_variables = {}
        for key, value in variables.items():
            if value is None:
                safe_variables[key] = ""
            else:
                safe_variables[key] = str(value)
        
        # Remplacer les variables
        for var_name, var_value in safe_variables.items():
            content = content.replace(f"{{{var_name}}}", var_value)
        
        # Rechercher les variables non remplacées
        remaining_vars = re.findall(r'{([^{}]*)}', content)
        if remaining_vars:
            logger.warning(f"Variables non remplacées: {remaining_vars}")
        
        return content
    
    def generate_filename(self, template_type, client_name, date=None, format_type="pdf"):
        """
        Génère un nom de fichier pour le document
        
        Args:
            template_type: Type de modèle (ex: contrat, facture)
            client_name: Nom du client
            date: Date du document (format: YYYY-MM-DD)
            format_type: Format du document (pdf ou docx)
            
        Returns:
            str: Nom de fichier normalisé
        """
        # Date par défaut
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Nettoyer les noms
        template_type = self.clean_filename(template_type)
        client_name = self.clean_filename(client_name)
        
        # Formater la date
        date_format = "%Y-%m-%d"
        if self.config:
            date_format = self.config.get("document.date_format", "%Y-%m-%d")
        
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime(date_format)
        except:
            formatted_date = datetime.now().strftime(date_format)
        
        # Construire le nom du fichier selon le pattern configuré
        pattern = "{document_type}_{client_name}_{date}"
        if self.config:
            pattern = self.config.get("document.filename_pattern", pattern)
        
        filename = pattern.replace("{document_type}", template_type)
        filename = filename.replace("{client_name}", client_name)
        filename = filename.replace("{date}", formatted_date)
        
        # Ajouter l'extension
        return f"{filename}.{format_type}"
    
    def clean_filename(self, name):
        """
        Nettoie un nom pour qu'il soit utilisable dans un nom de fichier
        
        Args:
            name: Nom à nettoyer
            
        Returns:
            str: Nom nettoyé
        """
        # Supprimer les caractères spéciaux et remplacer les espaces par des underscores
        name = re.sub(r'[\\/*?:"<>|]', '', name)
        name = name.replace(' ', '_')
        name = name.replace('/', '_')
        name = name.replace('\\', '_')
        name = name.strip('.')  # Supprime les points en début et fin
        
        return name
    
    def generate_pdf(self, file_path, content, title, client, company_info, logo_path=None):
        """
        Génère un fichier PDF
        
        Args:
            file_path: Chemin du fichier à créer
            content: Contenu du document
            title: Titre du document
            client: Informations du client (dict)
            company_info: Informations de l'entreprise (dict)
            logo_path: Chemin du logo de l'entreprise
            
        Returns:
            bool: True si le document a été généré avec succès, False sinon
        """
        try:
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Créer un PDF
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # Styles
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(
                name='Heading1',
                fontSize=16,
                fontName='Helvetica-Bold',
                spaceAfter=12
            ))
            styles.add(ParagraphStyle(
                name='Normal',
                fontSize=10,
                fontName='Helvetica',
                leading=12
            ))
            
            # En-tête avec logo si disponible
            y_position = height - 50
            if logo_path and os.path.exists(logo_path):
                try:
                    # Charger et redimensionner le logo
                    logo = Image(logo_path, width=150, height=50)
                    logo.drawOn(c, 50, height - 85)
                    y_position = height - 100
                except Exception as e:
                    logger.warning(f"Erreur lors du chargement du logo: {e}")
            
            # Informations de l'entreprise
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, y_position, company_info.get("name", ""))
            y_position -= 20
            
            c.setFont("Helvetica", 10)
            c.drawString(50, y_position, "Document généré par Vynal Docs Automator")
            y_position -= 15
            c.drawString(50, y_position, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            y_position -= 15
            
            # Ligne séparatrice
            c.line(50, y_position, width - 50, y_position)
            y_position -= 20
            
            # Titre du document
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, y_position, title)
            y_position -= 30
            
            # Informations du client
            c.setFont("Helvetica", 12)
            c.drawString(50, y_position, f"Client: {client.get('name', '')}")
            y_position -= 15
            
            if client.get('company'):
                c.drawString(50, y_position, f"Entreprise: {client.get('company')}")
                y_position -= 15
            
            c.drawString(50, y_position, f"Email: {client.get('email', '')}")
            y_position -= 15
            
            if client.get('phone'):
                c.drawString(50, y_position, f"Téléphone: {client.get('phone')}")
                y_position -= 15
            
            if client.get('address'):
                c.drawString(50, y_position, f"Adresse: {client.get('address')}")
                y_position -= 15
            
            # Ligne séparatrice
            c.line(50, y_position, width - 50, y_position)
            y_position -= 20
            
            # Fonction pour ajouter du texte multiligne
            def add_text_block(text_block, x, y, width):
                text_object = c.beginText(x, y)
                text_object.setFont("Helvetica", 10)
                
                # Diviser le texte en lignes
                words = text_block.split()
                current_line = ""
                
                for word in words:
                    # Tester si l'ajout du mot dépasse la largeur
                    test_line = current_line + " " + word if current_line else word
                    line_width = c.stringWidth(test_line, "Helvetica", 10)
                    
                    if line_width <= width:
                        current_line = test_line
                    else:
                        text_object.textLine(current_line)
                        current_line = word
                
                # Ajouter la dernière ligne
                if current_line:
                    text_object.textLine(current_line)
                
                c.drawText(text_object)
                
                # Calculer la hauteur totale du bloc
                line_count = len(text_object._code) - 1  # _code contient les commandes pour chaque ligne
                return line_count * 15  # 15 points par ligne
            
            # Contenu du document en gérant les sauts de page
            text_width = width - 100  # 50 de marge de chaque côté
            content_lines = content.split('\n')
            
            for line in content_lines:
                # Vérifier s'il reste assez d'espace sur la page
                if y_position < 100:  # Marge de bas de page de 100 points
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y_position = height - 50
                
                # Écrire la ligne
                line_height = add_text_block(line, 50, y_position, text_width)
                y_position -= (line_height + 5)  # 5 points d'espace entre paragraphes
            
            # Pied de page
            c.showPage()
            
            # Finir le document
            c.save()
            pdf_data = buffer.getvalue()
            
            # Écrire dans le fichier
            with open(file_path, 'wb') as f:
                f.write(pdf_data)
            
            logger.info(f"Document PDF généré: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération du PDF: {e}")
            return False
    
    def generate_docx(self, file_path, content, title, client, company_info, logo_path=None):
        """
        Génère un fichier DOCX
        
        Args:
            file_path: Chemin du fichier à créer
            content: Contenu du document
            title: Titre du document
            client: Informations du client (dict)
            company_info: Informations de l'entreprise (dict)
            logo_path: Chemin du logo de l'entreprise
            
        Returns:
            bool: True si le document a été généré avec succès, False sinon
        """
        try:
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Créer un document Word
            doc = docx.Document()
            
            # En-tête avec logo si disponible
            if logo_path and os.path.exists(logo_path):
                try:
                    # Ajouter une section pour l'en-tête
                    header_section = doc.sections[0]
                    header = header_section.header
                    header_para = header.paragraphs[0]
                    
                    # Ajouter le logo
                    run = header_para.add_run()
                    run.add_picture(logo_path, width=Cm(5))
                except Exception as e:
                    logger.warning(f"Erreur lors du chargement du logo: {e}")
            
            # Informations de l'entreprise
            company_para = doc.add_paragraph()
            company_run = company_para.add_run(company_info.get("name", ""))
            company_run.bold = True
            company_run.font.size = Pt(14)
            
            doc.add_paragraph("Document généré par Vynal Docs Automator")
            doc.add_paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # Ligne séparatrice
            doc.add_paragraph("_______________________________________________________________")
            
            # Titre du document
            title_para = doc.add_paragraph()
            title_run = title_para.add_run(title)
            title_run.bold = True
            title_run.font.size = Pt(16)
            
            # Informations du client
            doc.add_paragraph(f"Client: {client.get('name', '')}")
            
            if client.get('company'):
                doc.add_paragraph(f"Entreprise: {client.get('company')}")
            
            doc.add_paragraph(f"Email: {client.get('email', '')}")
            
            if client.get('phone'):
                doc.add_paragraph(f"Téléphone: {client.get('phone')}")
            
            if client.get('address'):
                doc.add_paragraph(f"Adresse: {client.get('address')}")
            
            # Ligne séparatrice
            doc.add_paragraph("_______________________________________________________________")
            
            # Contenu du document
            # Diviser le contenu en paragraphes
            paragraphs = content.split('\n')
            
            for paragraph in paragraphs:
                if paragraph.strip():
                    doc.add_paragraph(paragraph)
            
            # Pied de page
            footer = doc.sections[0].footer
            footer_para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            footer_run = footer_para.add_run(f"© {datetime.now().year} {company_info.get('name', '')} - Confidentiel")
            footer_run.font.size = Pt(8)
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Enregistrer le document
            doc.save(file_path)
            
            logger.info(f"Document DOCX généré: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération du DOCX: {e}")
            return False
    
    def generate_document(self, file_path, template, client, company_info, variables, format_type=None):
        """
        Génère un document à partir d'un modèle
        
        Args:
            file_path: Chemin du fichier à créer
            template: Modèle de document (dict)
            client: Informations du client (dict)
            company_info: Informations de l'entreprise (dict)
            variables: Variables spécifiques pour le document
            format_type: Format du document (pdf ou docx)
            
        Returns:
            bool: True si le document a été généré avec succès, False sinon
        """
        try:
            # Déterminer le format si non spécifié
            if format_type is None:
                format_type = "pdf"
                if self.config:
                    format_type = self.config.get("document.default_format", "pdf")
            
            # Vérifier que le format est valide
            format_type = format_type.lower()
            if format_type not in ["pdf", "docx"]:
                logger.error(f"Format de document non pris en charge: {format_type}")
                return False
            
            # Vérifier que l'extension correspond au format
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext and file_ext[1:] != format_type:
                file_path = os.path.splitext(file_path)[0] + f".{format_type}"
            
            # Préparer les variables
            all_variables = {}
            
            # Variables standard du client
            all_variables.update({
                "client_name": client.get("name", ""),
                "client_company": client.get("company", ""),
                "client_email": client.get("email", ""),
                "client_phone": client.get("phone", ""),
                "client_address": client.get("address", "")
            })
            
            # Variables de l'entreprise
            all_variables.update({
                "company_name": company_info.get("name", ""),
                "company_address": company_info.get("address", ""),
                "company_email": company_info.get("email", ""),
                "company_phone": company_info.get("phone", ""),
                "company_website": company_info.get("website", "")
            })
            
            # Variables spécifiques
            all_variables.update(variables)
            
            # Date actuelle
            all_variables["date"] = datetime.now().strftime("%Y-%m-%d")
            
            # Remplacer les variables dans le contenu
            content = self.replace_variables(template.get("content", ""), all_variables)
            
            # Titre du document
            title = template.get("name", "Document")
            if "title" in variables:
                title = variables["title"]
            
            # Obtenir le chemin du logo
            logo_path = None
            if self.config:
                logo_path = self.config.get("app.company_logo", "")
            
            # Générer le document selon le format
            if format_type == "pdf":
                return self.generate_pdf(file_path, content, title, client, company_info, logo_path)
            else:
                return self.generate_docx(file_path, content, title, client, company_info, logo_path)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du document: {e}")
            return False