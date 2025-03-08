#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contrôleur de gestion des documents pour l'application Vynal Docs Automator
"""

import os
import re
import shutil
import logging
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger("VynalDocsAutomator.DocumentController")

class DocumentController:
    """
    Contrôleur de gestion des documents
    Gère la logique métier liée aux documents
    """
    
    def __init__(self, app_model, document_view):
        """
        Initialise le contrôleur des documents
        
        Args:
            app_model: Modèle de l'application
            document_view: Vue de gestion des documents
        """
        self.model = app_model
        self.view = document_view
        
        # Connecter les événements de la vue aux méthodes du contrôleur
        self.connect_events()
        
        logger.info("DocumentController initialisé")
    
    def connect_events(self):
        """
        Connecte les événements de la vue aux méthodes du contrôleur
        """
        # Remplacer les méthodes de la vue par les méthodes du contrôleur
        self.view.new_document = self.new_document
        self.view.open_document = self.open_document
        self.view.download_document = self.download_document
        self.view.filter_documents = self.filter_documents
        
        logger.info("Événements de DocumentView connectés")
    
    def new_document(self):
        """
        Crée un nouveau document à partir d'un modèle
        """
        # Vérifier s'il y a des modèles disponibles
        if not self.model.templates:
            messagebox.showwarning("Attention", "Aucun modèle disponible. Veuillez d'abord créer un modèle.", parent=self.view.parent)
            return
        
        # Vérifier s'il y a des clients disponibles
        if not self.model.clients:
            messagebox.showwarning("Attention", "Aucun client disponible. Veuillez d'abord ajouter un client.", parent=self.view.parent)
            return
        
        # Créer une fenêtre de dialogue
        dialog = tk.Toplevel(self.view.parent)
        dialog.title("Nouveau document")
        dialog.geometry("550x600")
        dialog.resizable(False, False)
        dialog.grab_set()  # Modal
        dialog.focus_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Créer un cadre principal avec défilement
        main_frame = tk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 1. Sélection du modèle
        template_frame = tk.LabelFrame(main_frame, text="1. Sélectionner un modèle")
        template_frame.pack(fill=tk.X, pady=10)
        
        # Liste des modèles
        template_list_frame = tk.Frame(template_frame)
        template_list_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(template_list_frame, text="Modèle:").grid(row=0, column=0, sticky="w")
        template_var = tk.StringVar()
        template_options = [f"{t.get('name')} ({t.get('type', '')})" for t in self.model.templates]
        template_menu = tk.OptionMenu(template_list_frame, template_var, *template_options)
        template_menu.grid(row=0, column=1, sticky="ew", padx=5)
        template_list_frame.columnconfigure(1, weight=1)
        
        # Description du modèle sélectionné
        template_desc = tk.Label(template_frame, text="", justify=tk.LEFT, wraplength=500)
        template_desc.pack(fill=tk.X, padx=10, pady=5)
        
        # 2. Sélection du client
        client_frame = tk.LabelFrame(main_frame, text="2. Sélectionner un client")
        client_frame.pack(fill=tk.X, pady=10)
        
        # Liste des clients
        client_list_frame = tk.Frame(client_frame)
        client_list_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(client_list_frame, text="Client:").grid(row=0, column=0, sticky="w")
        client_var = tk.StringVar()
        client_options = [f"{c.get('name')} ({c.get('company', '')})" for c in self.model.clients]
        client_menu = tk.OptionMenu(client_list_frame, client_var, *client_options)
        client_menu.grid(row=0, column=1, sticky="ew", padx=5)
        client_list_frame.columnconfigure(1, weight=1)
        
        # Informations du client sélectionné
        client_info = tk.Label(client_frame, text="", justify=tk.LEFT, wraplength=500)
        client_info.pack(fill=tk.X, padx=10, pady=5)
        
        # 3. Informations du document
        info_frame = tk.LabelFrame(main_frame, text="3. Informations du document")
        info_frame.pack(fill=tk.X, pady=10)
        
        info_list_frame = tk.Frame(info_frame)
        info_list_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Titre
        tk.Label(info_list_frame, text="Titre:").grid(row=0, column=0, sticky="w", pady=5)
        title_var = tk.StringVar()
        title_entry = tk.Entry(info_list_frame, textvariable=title_var, width=40)
        title_entry.grid(row=0, column=1, sticky="ew", pady=5)
        
        # Date
        tk.Label(info_list_frame, text="Date:").grid(row=1, column=0, sticky="w", pady=5)
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = tk.Entry(info_list_frame, textvariable=date_var, width=40)
        date_entry.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Description
        tk.Label(info_list_frame, text="Description:").grid(row=2, column=0, sticky="w", pady=5)
        description_text = tk.Text(info_list_frame, width=40, height=3)
        description_text.grid(row=2, column=1, sticky="ew", pady=5)
        
        info_list_frame.columnconfigure(1, weight=1)
        
        # 4. Variables spécifiques du modèle
        variables_frame = tk.LabelFrame(main_frame, text="4. Variables spécifiques")
        variables_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Cadre défilable pour les variables
        canvas = tk.Canvas(variables_frame)
        scrollbar = tk.Scrollbar(variables_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Dictionnaire pour stocker les widgets des variables
        variable_widgets = {}
        
        # Fonction pour mettre à jour les informations du modèle et du client
        def update_template_info(*args):
            # Récupérer le modèle sélectionné
            selected_template = template_var.get()
            if not selected_template:
                return
            
            # Trouver le modèle correspondant
            template_index = template_options.index(selected_template)
            template = self.model.templates[template_index]
            
            # Mettre à jour la description
            template_desc.config(text=template.get('description', ''))
            
            # Générer un titre par défaut si le client est sélectionné
            if client_var.get():
                client_name = client_var.get().split(' (')[0]
                title_var.set(f"{template.get('type', 'Document')} - {client_name}")
            
            # Mettre à jour les variables
            # Supprimer les anciens widgets
            for widget in scrollable_frame.winfo_children():
                widget.destroy()
            
            # Créer les nouveaux widgets pour chaque variable
            variable_widgets.clear()
            variables = template.get('variables', [])
            
            if variables:
                tk.Label(scrollable_frame, text="Complétez les informations spécifiques à ce document:").pack(anchor="w", padx=10, pady=(10, 5))
                
                for i, var_name in enumerate(variables):
                    # Ignorer les variables standard qui seront remplies automatiquement
                    if var_name in ['client_name', 'client_company', 'client_email', 'client_phone', 'client_address']:
                        continue
                    
                    frame = tk.Frame(scrollable_frame)
                    frame.pack(fill=tk.X, padx=10, pady=2)
                    
                    tk.Label(frame, text=f"{var_name}:").pack(side=tk.LEFT)
                    
                    if "montant" in var_name.lower() or "prix" in var_name.lower() or "cout" in var_name.lower() or "coût" in var_name.lower():
                        # Champ monétaire
                        money_frame = tk.Frame(frame)
                        money_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                        
                        var = tk.StringVar()
                        entry = tk.Entry(money_frame, textvariable=var)
                        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                        
                        tk.Label(money_frame, text="€").pack(side=tk.LEFT)
                        
                        variable_widgets[var_name] = {"widget": entry, "var": var, "type": "money"}
                    elif "date" in var_name.lower():
                        # Champ date
                        var = tk.StringVar()
                        entry = tk.Entry(frame, textvariable=var, width=15)
                        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                        entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
                        
                        variable_widgets[var_name] = {"widget": entry, "var": var, "type": "date"}
                    else:
                        # Champ texte standard
                        var = tk.StringVar()
                        entry = tk.Entry(frame, textvariable=var)
                        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                        
                        variable_widgets[var_name] = {"widget": entry, "var": var, "type": "text"}
            else:
                tk.Label(scrollable_frame, text="Ce modèle ne contient pas de variables personnalisables.").pack(anchor="w", padx=10, pady=10)
        
        def update_client_info(*args):
            # Récupérer le client sélectionné
            selected_client = client_var.get()
            if not selected_client:
                return
            
            # Trouver le client correspondant
            client_index = client_options.index(selected_client)
            client = self.model.clients[client_index]
            
            # Mettre à jour les informations
            info_text = f"Email: {client.get('email', '')}\n"
            if client.get('phone'):
                info_text += f"Téléphone: {client.get('phone')}\n"
            if client.get('address'):
                info_text += f"Adresse: {client.get('address')}"
            
            client_info.config(text=info_text)
            
            # Mettre à jour le titre si un modèle est sélectionné
            if template_var.get():
                template_name = template_var.get().split(' (')[0]
                template_type = template_var.get().split(' (')[1].strip(')')
                client_name = selected_client.split(' (')[0]
                title_var.set(f"{template_type} - {client_name}")
        
        # Connecter les changements de sélection aux fonctions de mise à jour
        template_var.trace_add("write", update_template_info)
        client_var.trace_add("write", update_client_info)
        
        # Boutons
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Fonction pour générer le document
        def generate_document():
            # Vérifier si un modèle et un client sont sélectionnés
            if not template_var.get():
                messagebox.showwarning("Attention", "Veuillez sélectionner un modèle", parent=dialog)
                return
            
            if not client_var.get():
                messagebox.showwarning("Attention", "Veuillez sélectionner un client", parent=dialog)
                return
            
            # Récupérer le titre et la date
            title = title_var.get().strip()
            if not title:
                messagebox.showwarning("Attention", "Veuillez entrer un titre", parent=dialog)
                return
            
            date = date_var.get().strip()
            description = description_text.get("1.0", "end-1c").strip()
            
            # Récupérer le modèle et le client
            template_index = template_options.index(template_var.get())
            template = self.model.templates[template_index]
            
            client_index = client_options.index(client_var.get())
            client = self.model.clients[client_index]
            
            # Récupérer les valeurs des variables
            variables_values = {}
            for var_name, widget_info in variable_widgets.items():
                if widget_info["type"] in ["text", "money", "date"]:
                    variables_values[var_name] = widget_info["var"].get().strip()
            
            # Créer l'objet document
            document_id = f"doc_{len(self.model.documents) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            document_data = {
                "id": document_id,
                "title": title,
                "type": template.get("type", ""),
                "date": date,
                "description": description,
                "template_id": template.get("id"),
                "client_id": client.get("id"),
                "variables": variables_values,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Générer le contenu du document en remplaçant les variables
            content = self.generate_document_content(template, client, variables_values)
            
            # Générer le nom de fichier
            doc_filename = self.generate_filename(template.get("type", "document"), client.get('name', 'client'), date)
            
            # Chemin du fichier
            format_type = self.model.config.get("document.default_format", "pdf")
            doc_filepath = os.path.join(self.model.paths['documents'], f"{doc_filename}.{format_type}")
            
            # Générer le fichier selon le format
            try:
                if format_type == "pdf":
                    self.generate_pdf(doc_filepath, content, title, client, self.model.config.get("app.company_name", ""))
                else:
                    self.generate_docx(doc_filepath, content, title, client, self.model.config.get("app.company_name", ""))
                
                # Ajouter le chemin du fichier au document
                document_data["file_path"] = doc_filepath
                
                # Ajouter le document
                self.model.documents.append(document_data)
                self.model.save_documents()
                
                # Ajouter l'activité
                self.model.add_activity("document", f"Document créé: {title}")
                
                # Mettre à jour la vue
                self.view.update_view()
                
                # Fermer la fenêtre
                dialog.destroy()
                
                # Afficher un message de succès
                messagebox.showinfo("Succès", f"Document '{title}' créé avec succès")
                
                logger.info(f"Document créé: {document_id} - {title}")
                
            except Exception as e:
                logger.error(f"Erreur lors de la génération du document: {e}")
                messagebox.showerror("Erreur", f"Erreur lors de la génération du document: {str(e)}", parent=dialog)
        
        # Bouton Annuler
        cancel_btn = tk.Button(button_frame, text="Annuler", command=dialog.destroy, width=10)
        cancel_btn.pack(side=tk.RIGHT, padx=10)
        
        # Bouton Générer
        generate_btn = tk.Button(button_frame, text="Générer", command=generate_document, width=10)
        generate_btn.pack(side=tk.RIGHT, padx=10)
        
        logger.info("Formulaire de création de document affiché")
    
    def open_document(self, document_id):
        """
        Ouvre un document pour le visualiser
        
        Args:
            document_id: ID du document à ouvrir
        """
        # Récupérer le document
        document = next((d for d in self.model.documents if d.get('id') == document_id), None)
        
        if not document:
            messagebox.showerror("Erreur", "Document non trouvé")
            return
        
        # Vérifier si le fichier existe
        file_path = document.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Erreur", "Le fichier du document est introuvable")
            return
        
        # Ouvrir le fichier avec l'application par défaut du système
        try:
            import subprocess
            
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS ou Linux
                subprocess.call(('open' if os.uname().sysname == 'Darwin' else 'xdg-open', file_path))
            
            logger.info(f"Document ouvert: {document_id} - {file_path}")
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du document: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'ouverture du document: {str(e)}")
    
    def download_document(self, document_id):
        """
        Télécharge (copie) un document vers un emplacement choisi par l'utilisateur
        
        Args:
            document_id: ID du document à télécharger
        """
        # Récupérer le document
        document = next((d for d in self.model.documents if d.get('id') == document_id), None)
        
        if not document:
            messagebox.showerror("Erreur", "Document non trouvé")
            return
        
        # Vérifier si le fichier existe
        file_path = document.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Erreur", "Le fichier du document est introuvable")
            return
        
        # Déterminer l'extension du fichier
        _, ext = os.path.splitext(file_path)
        
        # Ouvrir une boîte de dialogue pour choisir l'emplacement de sauvegarde
        dest_path = filedialog.asksaveasfilename(
            title="Enregistrer le document",
            defaultextension=ext,
            initialfile=os.path.basename(file_path),
            filetypes=[(f"Fichiers {ext.upper()}", f"*{ext}"), ("Tous les fichiers", "*.*")]
        )
        
        if not dest_path:
            return
        
        try:
            # Copier le fichier
            shutil.copy2(file_path, dest_path)
            
            logger.info(f"Document téléchargé: {document_id} - {dest_path}")
            messagebox.showinfo("Succès", "Document téléchargé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du document: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du téléchargement du document: {str(e)}")
    
    def filter_documents(self, *args):
        """
        Filtre les documents selon les critères sélectionnés
        """
        # Cette méthode est déjà implémentée dans la vue
        # Nous nous assurons juste qu'elle est appelée au bon moment
        self.view.update_view()
        logger.debug("Documents filtrés")
    
    def generate_document_content(self, template, client, variables):
        """
        Génère le contenu d'un document en remplaçant les variables
        
        Args:
            template: Modèle de document
            client: Informations du client
            variables: Valeurs des variables spécifiques
            
        Returns:
            str: Contenu du document avec les variables remplacées
        """
        # Récupérer le contenu du modèle
        content = template.get('content', "")
        
        # Remplacer les variables client
        content = content.replace("{client_name}", client.get('name', ''))
        content = content.replace("{client_company}", client.get('company', ''))
        content = content.replace("{client_email}", client.get('email', ''))
        content = content.replace("{client_phone}", client.get('phone', ''))
        content = content.replace("{client_address}", client.get('address', ''))
        
        # Remplacer les variables de l'entreprise
        content = content.replace("{company_name}", self.model.config.get("app.company_name", ""))
        
        # Remplacer la date
        content = content.replace("{date}", datetime.now().strftime("%Y-%m-%d"))
        
        # Remplacer les variables spécifiques
        for var_name, var_value in variables.items():
            content = content.replace(f"{{{var_name}}}", var_value)
        
        # Calculer automatiquement les montants TTC et TVA si nécessaire
        if "{montant_ttc}" in content and "montant" in variables:
            try:
                montant_ht = float(variables.get("montant", "0").replace(",", "."))
                montant_tva = montant_ht * 0.2  # TVA à 20%
                montant_ttc = montant_ht + montant_tva
                
                content = content.replace("{montant_tva}", f"{montant_tva:.2f}")
                content = content.replace("{montant_ttc}", f"{montant_ttc:.2f}")
            except ValueError:
                pass
        
        return content
    
    def generate_filename(self, doc_type, client_name, date):
        """
        Génère un nom de fichier pour le document
        
        Args:
            doc_type: Type de document
            client_name: Nom du client
            date: Date du document
            
        Returns:
            str: Nom de fichier normalisé
        """
        # Nettoyer les noms
        doc_type = self.clean_filename(doc_type)
        client_name = self.clean_filename(client_name)
        
        # Formatter la date
        date_format = self.model.config.get("document.date_format", "%Y-%m-%d")
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime(date_format)
        except:
            formatted_date = datetime.now().strftime(date_format)
        
        # Construire le nom du fichier selon le pattern configuré
        pattern = self.model.config.get("document.filename_pattern", "{document_type}_{client_name}_{date}")
        
        filename = pattern.replace("{document_type}", doc_type)
        filename = filename.replace("{client_name}", client_name)
        filename = filename.replace("{date}", formatted_date)
        
        return filename
    
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
        
        return name
    
    def generate_pdf(self, file_path, content, title, client, company_name):
        """
        Génère un fichier PDF
        
        Args:
            file_path: Chemin du fichier à créer
            content: Contenu du document
            title: Titre du document
            client: Informations du client
            company_name: Nom de l'entreprise
        """
        try:
            # Créer un PDF
            c = canvas.Canvas(file_path, pagesize=A4)
            width, height = A4
            
            # En-tête
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, height - 50, company_name)
            
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 70, "Document généré par Vynal Docs Automator")
            c.drawString(50, height - 85, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # Ligne séparatrice
            c.line(50, height - 95, width - 50, height - 95)
            
            # Titre
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 130, title)
            
            # Client
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 160, f"Client: {client.get('name', '')}")
            if client.get('company'):
                c.drawString(50, height - 175, f"Entreprise: {client.get('company')}")
                y_offset = 190
            else:
                y_offset = 175
            
            c.drawString(50, height - y_offset, f"Email: {client.get('email', '')}")
            if client.get('phone'):
                y_offset += 15
                c.drawString(50, height - y_offset, f"Téléphone: {client.get('phone')}")
            
            # Ligne séparatrice
            y_offset += 15
            c.line(50, height - y_offset, width - 50, height - y_offset)
            
            # Contenu du document
            c.setFont("Helvetica", 10)
            y_position = height - y_offset - 25
            
            # Diviser le contenu en lignes
            lines = content.split('\n')
            
            for line in lines:
                if y_position < 50:
                    # Créer une nouvelle page
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y_position = height - 50
                
                # Écrire la ligne
                c.drawString(50, y_position, line)
                y_position -= 15
            
            # Finaliser le PDF
            c.showPage()
            c.save()
            
            logger.info(f"PDF généré: {file_path}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du PDF: {e}")
            raise
    
    def generate_docx(self, file_path, content, title, client, company_name):
        """
        Génère un fichier DOCX
        
        Args:
            file_path: Chemin du fichier à créer
            content: Contenu du document
            title: Titre du document
            client: Informations du client
            company_name: Nom de l'entreprise
        """
        try:
            # Créer un document Word
            doc = docx.Document()
            
            # En-tête
            header = doc.add_paragraph()
            header_run = header.add_run(company_name)
            header_run.bold = True
            header_run.font.size = Pt(14)
            
            doc.add_paragraph("Document généré par Vynal Docs Automator")
            doc.add_paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # Ligne séparatrice
            doc.add_paragraph("_______________________________________________________________")
            
            # Titre
            title_para = doc.add_paragraph()
            title_run = title_para.add_run(title)
            title_run.bold = True
            title_run.font.size = Pt(16)
            
            # Client
            doc.add_paragraph(f"Client: {client.get('name', '')}")
            if client.get('company'):
                doc.add_paragraph(f"Entreprise: {client.get('company')}")
            doc.add_paragraph(f"Email: {client.get('email', '')}")
            if client.get('phone'):
                doc.add_paragraph(f"Téléphone: {client.get('phone')}")
            
            # Ligne séparatrice
            doc.add_paragraph("_______________________________________________________________")
            
            # Contenu
            # Diviser le contenu en paragraphes
            paragraphs = content.split('\n')
            
            for paragraph in paragraphs:
                if paragraph.strip():
                    doc.add_paragraph(paragraph)
            
            # Pied de page
            footer = doc.sections[0].footer
            footer_para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            footer_run = footer_para.add_run(f"© {datetime.now().year} {company_name} - Confidentiel")
            footer_run.font.size = Pt(8)
            footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Enregistrer le document
            doc.save(file_path)
            
            logger.info(f"DOCX généré: {file_path}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du DOCX: {e}")
            raise
    
    def delete_document(self, document_id):
        """
        Supprime un document
        
        Args:
            document_id: ID du document à supprimer
        """
        # Récupérer le document
        document = next((d for d in self.model.documents if d.get('id') == document_id), None)
        
        if not document:
            messagebox.showerror("Erreur", "Document non trouvé")
            return
        
        # Confirmer la suppression
        response = messagebox.askyesno(
            "Confirmation", 
            f"Êtes-vous sûr de vouloir supprimer le document '{document.get('title')}'?\n\nCette action est irréversible.",
            icon='warning'
        )
        
        if not response:
            return
        
        try:
            # Supprimer le fichier s'il existe
            file_path = document.get('file_path')
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            
            # Supprimer le document de la liste
            self.model.documents = [d for d in self.model.documents if d.get('id') != document_id]
            
            # Sauvegarder les modifications
            self.model.save_documents()
            
            # Ajouter l'activité
            self.model.add_activity("document", f"Document supprimé: {document.get('title')}")
            
            # Mettre à jour la vue
            self.view.update_view()
            
            logger.info(f"Document supprimé: {document_id} - {document.get('title')}")
            
            # Afficher un message de succès
            messagebox.showinfo("Succès", "Document supprimé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du document: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la suppression du document: {str(e)}")
    
    def export_document(self, document_id, format_type=None):
        """
        Exporte un document dans un autre format
        
        Args:
            document_id: ID du document à exporter
            format_type: Format d'exportation (pdf ou docx)
        """
        # Récupérer le document
        document = next((d for d in self.model.documents if d.get('id') == document_id), None)
        
        if not document:
            messagebox.showerror("Erreur", "Document non trouvé")
            return
        
        # Vérifier si le fichier existe
        file_path = document.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Erreur", "Le fichier du document est introuvable")
            return
        
        # Déterminer le format actuel
        _, current_ext = os.path.splitext(file_path)
        current_ext = current_ext.lower().strip('.')
        
        # Si aucun format spécifié, demander à l'utilisateur
        if not format_type:
            if current_ext == 'pdf':
                format_type = 'docx'
            else:
                format_type = 'pdf'
        
        # Vérifier que le format est différent du format actuel
        if format_type == current_ext:
            messagebox.showinfo("Information", f"Le document est déjà au format {format_type.upper()}")
            return
        
        # Déterminer le chemin du nouveau fichier
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        new_file_path = os.path.join(os.path.dirname(file_path), f"{base_name}.{format_type}")
        
        try:
            # Récupérer les informations nécessaires
            title = document.get('title', '')
            
            # Récupérer le client
            client_id = document.get('client_id')
            client = next((c for c in self.model.clients if c.get('id') == client_id), {})
            
            # Récupérer le modèle
            template_id = document.get('template_id')
            template = next((t for t in self.model.templates if t.get('id') == template_id), {})
            
            # Récupérer le contenu
            content = self.generate_document_content(
                template, 
                client, 
                document.get('variables', {})
            )
            
            # Générer le fichier selon le format
            company_name = self.model.config.get("app.company_name", "")
            
            if format_type == "pdf":
                self.generate_pdf(new_file_path, content, title, client, company_name)
            else:
                self.generate_docx(new_file_path, content, title, client, company_name)
            
            logger.info(f"Document exporté: {document_id} - {new_file_path}")
            
            # Demander à l'utilisateur s'il veut ouvrir le fichier
            response = messagebox.askyesno(
                "Succès", 
                f"Document exporté avec succès en format {format_type.upper()}.\n\nVoulez-vous l'ouvrir maintenant?"
            )
            
            if response:
                # Ouvrir le fichier avec l'application par défaut du système
                if os.name == 'nt':  # Windows
                    os.startfile(new_file_path)
                elif os.name == 'posix':  # macOS ou Linux
                    import subprocess
                    subprocess.call(('open' if os.uname().sysname == 'Darwin' else 'xdg-open', new_file_path))
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation du document: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'exportation du document: {str(e)}")
    
    def update_document(self, document_id):
        """
        Met à jour un document existant
        
        Args:
            document_id: ID du document à mettre à jour
        """
        # Récupérer le document
        document = next((d for d in self.model.documents if d.get('id') == document_id), None)
        
        if not document:
            messagebox.showerror("Erreur", "Document non trouvé")
            return
        
        # Récupérer le client et le modèle associés
        client_id = document.get('client_id')
        client = next((c for c in self.model.clients if c.get('id') == client_id), None)
        
        template_id = document.get('template_id')
        template = next((t for t in self.model.templates if t.get('id') == template_id), None)
        
        if not client or not template:
            messagebox.showerror("Erreur", "Client ou modèle introuvable")
            return
        
        # Ouvrir une boîte de dialogue pour modifier les informations
        dialog = tk.Toplevel(self.view.parent)
        dialog.title("Mettre à jour le document")
        dialog.geometry("550x600")
        dialog.resizable(False, False)
        dialog.grab_set()  # Modal
        dialog.focus_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Créer un cadre principal avec défilement
        main_frame = tk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Informations du document
        info_frame = tk.LabelFrame(main_frame, text="Informations du document")
        info_frame.pack(fill=tk.X, pady=10)
        
        info_list_frame = tk.Frame(info_frame)
        info_list_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Titre
        tk.Label(info_list_frame, text="Titre:").grid(row=0, column=0, sticky="w", pady=5)
        title_var = tk.StringVar(value=document.get('title', ''))
        title_entry = tk.Entry(info_list_frame, textvariable=title_var, width=40)
        title_entry.grid(row=0, column=1, sticky="ew", pady=5)
        
        # Date
        tk.Label(info_list_frame, text="Date:").grid(row=1, column=0, sticky="w", pady=5)
        date_var = tk.StringVar(value=document.get('date', ''))
        date_entry = tk.Entry(info_list_frame, textvariable=date_var, width=40)
        date_entry.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Description
        tk.Label(info_list_frame, text="Description:").grid(row=2, column=0, sticky="w", pady=5)
        description_text = tk.Text(info_list_frame, width=40, height=3)
        description_text.grid(row=2, column=1, sticky="ew", pady=5)
        description_text.insert("1.0", document.get('description', ''))
        
        info_list_frame.columnconfigure(1, weight=1)
        
        # Variables spécifiques du modèle
        variables_frame = tk.LabelFrame(main_frame, text="Variables spécifiques")
        variables_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Cadre défilable pour les variables
        canvas = tk.Canvas(variables_frame)
        scrollbar = tk.Scrollbar(variables_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Dictionnaire pour stocker les widgets des variables
        variable_widgets = {}
        
        # Récupérer les variables existantes
        existing_variables = document.get('variables', {})
        
        # Créer les widgets pour chaque variable
        variables = template.get('variables', [])
        
        if variables:
            tk.Label(scrollable_frame, text="Complétez les informations spécifiques à ce document:").pack(anchor="w", padx=10, pady=(10, 5))
            
            for i, var_name in enumerate(variables):
                # Ignorer les variables standard qui sont remplies automatiquement
                if var_name in ['client_name', 'client_company', 'client_email', 'client_phone', 'client_address']:
                    continue
                
                frame = tk.Frame(scrollable_frame)
                frame.pack(fill=tk.X, padx=10, pady=2)
                
                tk.Label(frame, text=f"{var_name}:").pack(side=tk.LEFT)
                
                # Récupérer la valeur existante
                existing_value = existing_variables.get(var_name, '')
                
                if "montant" in var_name.lower() or "prix" in var_name.lower() or "cout" in var_name.lower() or "coût" in var_name.lower():
                    # Champ monétaire
                    money_frame = tk.Frame(frame)
                    money_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                    
                    var = tk.StringVar(value=existing_value)
                    entry = tk.Entry(money_frame, textvariable=var)
                    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                    
                    tk.Label(money_frame, text="€").pack(side=tk.LEFT)
                    
                    variable_widgets[var_name] = {"widget": entry, "var": var, "type": "money"}
                elif "date" in var_name.lower():
                    # Champ date
                    var = tk.StringVar(value=existing_value)
                    entry = tk.Entry(frame, textvariable=var, width=15)
                    entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                    
                    variable_widgets[var_name] = {"widget": entry, "var": var, "type": "date"}
                else:
                    # Champ texte standard
                    var = tk.StringVar(value=existing_value)
                    entry = tk.Entry(frame, textvariable=var)
                    entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
                    
                    variable_widgets[var_name] = {"widget": entry, "var": var, "type": "text"}
        else:
            tk.Label(scrollable_frame, text="Ce modèle ne contient pas de variables personnalisables.").pack(anchor="w", padx=10, pady=10)
        
        # Boutons
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Fonction pour mettre à jour le document
        def update_document_data():
            # Récupérer le titre et la date
            title = title_var.get().strip()
            if not title:
                messagebox.showwarning("Attention", "Veuillez entrer un titre", parent=dialog)
                return
            
            date = date_var.get().strip()
            description = description_text.get("1.0", "end-1c").strip()
            
            # Récupérer les valeurs des variables
            variables_values = {}
            for var_name, widget_info in variable_widgets.items():
                if widget_info["type"] in ["text", "money", "date"]:
                    variables_values[var_name] = widget_info["var"].get().strip()
            
            # Mettre à jour l'objet document
            document['title'] = title
            document['date'] = date
            document['description'] = description
            document['variables'] = variables_values
            document['updated_at'] = datetime.now().isoformat()
            
            # Générer le contenu du document en remplaçant les variables
            content = self.generate_document_content(template, client, variables_values)
            
            # Vérifier si le fichier existe
            file_path = document.get('file_path')
            
            if not file_path or not os.path.exists(file_path):
                # Générer un nouveau fichier
                doc_filename = self.generate_filename(template.get("type", "document"), client.get('name', 'client'), date)
                format_type = self.model.config.get("document.default_format", "pdf")
                doc_filepath = os.path.join(self.model.paths['documents'], f"{doc_filename}.{format_type}")
                document['file_path'] = doc_filepath
            else:
                doc_filepath = file_path
            
            # Déterminer le format
            _, ext = os.path.splitext(doc_filepath)
            format_type = ext.lower().strip('.')
            
            # Générer le fichier selon le format
            try:
                if format_type == "pdf":
                    self.generate_pdf(doc_filepath, content, title, client, self.model.config.get("app.company_name", ""))
                else:
                    self.generate_docx(doc_filepath, content, title, client, self.model.config.get("app.company_name", ""))
                
                # Sauvegarder les documents
                self.model.save_documents()
                
                # Ajouter l'activité
                self.model.add_activity("document", f"Document mis à jour: {title}")
                
                # Mettre à jour la vue
                self.view.update_view()
                
                # Fermer la fenêtre
                dialog.destroy()
                
                # Afficher un message de succès
                messagebox.showinfo("Succès", f"Document '{title}' mis à jour avec succès")
                
                logger.info(f"Document mis à jour: {document_id} - {title}")
                
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du document: {e}")
                messagebox.showerror("Erreur", f"Erreur lors de la mise à jour du document: {str(e)}", parent=dialog)
        
        # Bouton Annuler
        cancel_btn = tk.Button(button_frame, text="Annuler", command=dialog.destroy, width=10)
        cancel_btn.pack(side=tk.RIGHT, padx=10)
        
        # Bouton Mettre à jour
        update_btn = tk.Button(button_frame, text="Mettre à jour", command=update_document_data, width=10)
        update_btn.pack(side=tk.RIGHT, padx=10)
        
        logger.info("Formulaire de mise à jour de document affiché")