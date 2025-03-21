import customtkinter as ctk
from typing import Dict, Any
import json

class AnalysisResultWidget(ctk.CTkFrame):
    """Widget pour afficher les résultats d'une analyse"""
    
    def __init__(self, parent, analysis_type: str, result: Dict[str, Any], **kwargs):
        """
        Initialise le widget de résultat
        
        Args:
            parent: Widget parent
            analysis_type: Type d'analyse
            result: Résultats de l'analyse
            **kwargs: Arguments supplémentaires pour le frame
        """
        super().__init__(parent, **kwargs)
        
        self.analysis_type = analysis_type
        self.result = result
        
        # Configuration visuelle
        self.configure(
            fg_color=("#E5E5E5", "#333333"),
            corner_radius=10
        )
        
        # Créer les widgets
        self._create_widgets()
    
    def _create_widgets(self):
        """Crée les widgets du résultat"""
        # En-tête avec le type d'analyse
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill=ctk.X, padx=10, pady=5)
        
        # Icône selon le type d'analyse
        icon = self._get_analysis_icon()
        title = f"{icon} {self._get_analysis_title()}"
        
        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(side=ctk.LEFT)
        
        # Score de confiance si disponible
        if "confidence" in self.result:
            confidence = self.result["confidence"]
            confidence_color = self._get_confidence_color(confidence)
            
            confidence_label = ctk.CTkLabel(
                header,
                text=f"{confidence:.1f}%",
                font=ctk.CTkFont(size=12),
                text_color=confidence_color
            )
            confidence_label.pack(side=ctk.RIGHT)
        
        # Contenu principal
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        
        # Afficher les résultats selon le type
        self._display_results(content)
        
        # Boutons d'action
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill=ctk.X, padx=10, pady=5)
        
        # Bouton pour copier les résultats
        copy_btn = ctk.CTkButton(
            actions,
            text="📋 Copier",
            command=self._copy_results,
            width=80,
            height=25,
            font=ctk.CTkFont(size=12)
        )
        copy_btn.pack(side=ctk.RIGHT, padx=5)
        
        # Bouton pour exporter les résultats
        export_btn = ctk.CTkButton(
            actions,
            text="💾 Exporter",
            command=self._export_results,
            width=80,
            height=25,
            font=ctk.CTkFont(size=12)
        )
        export_btn.pack(side=ctk.RIGHT, padx=5)
    
    def _get_analysis_icon(self) -> str:
        """Retourne l'icône correspondant au type d'analyse"""
        icons = {
            "text": "📝",
            "entities": "🏷️",
            "sentiment": "😊",
            "keywords": "🔑",
            "summary": "📋",
            "topics": "📚",
            "language": "🌐",
            "structure": "📑"
        }
        return icons.get(self.analysis_type, "📊")
    
    def _get_analysis_title(self) -> str:
        """Retourne le titre formaté du type d'analyse"""
        titles = {
            "text": "Extraction de texte",
            "entities": "Entités détectées",
            "sentiment": "Analyse de sentiment",
            "keywords": "Mots-clés",
            "summary": "Résumé",
            "topics": "Thèmes",
            "language": "Langue détectée",
            "structure": "Structure du document"
        }
        return titles.get(self.analysis_type, self.analysis_type.title())
    
    def _get_confidence_color(self, confidence: float) -> str:
        """Retourne la couleur selon le score de confiance"""
        if confidence >= 90:
            return ("#27ae60", "#2ecc71")  # Vert clair/foncé
        elif confidence >= 70:
            return ("#f39c12", "#f1c40f")  # Jaune clair/foncé
        else:
            return ("#c0392b", "#e74c3c")  # Rouge clair/foncé
    
    def _display_results(self, parent: ctk.CTkFrame):
        """
        Affiche les résultats selon leur type
        
        Args:
            parent: Widget parent où afficher les résultats
        """
        if self.analysis_type == "text":
            self._display_text_results(parent)
        elif self.analysis_type == "entities":
            self._display_entities_results(parent)
        elif self.analysis_type == "sentiment":
            self._display_sentiment_results(parent)
        elif self.analysis_type == "keywords":
            self._display_keywords_results(parent)
        elif self.analysis_type == "summary":
            self._display_summary_results(parent)
        else:
            # Affichage générique pour les autres types
            self._display_generic_results(parent)
    
    def _display_text_results(self, parent: ctk.CTkFrame):
        """Affiche les résultats d'extraction de texte"""
        text = self.result.get("text", "")
        text_widget = ctk.CTkTextbox(
            parent,
            height=100,
            wrap="word"
        )
        text_widget.pack(fill=ctk.BOTH, expand=True)
        text_widget.insert("1.0", text)
        text_widget.configure(state="disabled")
    
    def _display_entities_results(self, parent: ctk.CTkFrame):
        """Affiche les entités détectées"""
        entities = self.result.get("entities", [])
        for entity in entities:
            entity_frame = ctk.CTkFrame(parent, fg_color="transparent")
            entity_frame.pack(fill=ctk.X, pady=2)
            
            ctk.CTkLabel(
                entity_frame,
                text=f"{entity['type']}:",
                font=ctk.CTkFont(size=12, weight="bold"),
                width=80
            ).pack(side=ctk.LEFT)
            
            ctk.CTkLabel(
                entity_frame,
                text=entity["text"],
                font=ctk.CTkFont(size=12)
            ).pack(side=ctk.LEFT, padx=5)
    
    def _display_sentiment_results(self, parent: ctk.CTkFrame):
        """Affiche les résultats d'analyse de sentiment"""
        sentiment = self.result.get("sentiment", {})
        
        # Score global
        score = sentiment.get("score", 0)
        label = sentiment.get("label", "Neutre")
        
        score_frame = ctk.CTkFrame(parent, fg_color="transparent")
        score_frame.pack(fill=ctk.X, pady=5)
        
        ctk.CTkLabel(
            score_frame,
            text=f"Score: {score:.2f}",
            font=ctk.CTkFont(size=12)
        ).pack(side=ctk.LEFT)
        
        ctk.CTkLabel(
            score_frame,
            text=f"({label})",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side=ctk.LEFT, padx=5)
    
    def _display_keywords_results(self, parent: ctk.CTkFrame):
        """Affiche les mots-clés extraits"""
        keywords = self.result.get("keywords", [])
        
        keywords_frame = ctk.CTkFrame(parent, fg_color="transparent")
        keywords_frame.pack(fill=ctk.BOTH, expand=True)
        
        for keyword in keywords:
            keyword_label = ctk.CTkLabel(
                keywords_frame,
                text=keyword,
                font=ctk.CTkFont(size=12),
                fg_color=("#E0E0E0", "#404040"),
                corner_radius=5
            )
            keyword_label.pack(side=ctk.LEFT, padx=2, pady=2)
    
    def _display_summary_results(self, parent: ctk.CTkFrame):
        """Affiche le résumé du document"""
        summary = self.result.get("summary", "")
        
        summary_widget = ctk.CTkTextbox(
            parent,
            height=80,
            wrap="word"
        )
        summary_widget.pack(fill=ctk.BOTH, expand=True)
        summary_widget.insert("1.0", summary)
        summary_widget.configure(state="disabled")
    
    def _display_generic_results(self, parent: ctk.CTkFrame):
        """Affiche les résultats de manière générique"""
        # Convertir les résultats en texte formaté
        text = json.dumps(self.result, indent=2, ensure_ascii=False)
        
        text_widget = ctk.CTkTextbox(
            parent,
            height=100,
            wrap="none"
        )
        text_widget.pack(fill=ctk.BOTH, expand=True)
        text_widget.insert("1.0", text)
        text_widget.configure(state="disabled")
    
    def _copy_results(self):
        """Copie les résultats dans le presse-papiers"""
        text = json.dumps(self.result, ensure_ascii=False)
        self.clipboard_clear()
        self.clipboard_append(text)
    
    def _export_results(self):
        """Exporte les résultats dans un fichier"""
        # TODO: Implémenter l'export des résultats
        pass 