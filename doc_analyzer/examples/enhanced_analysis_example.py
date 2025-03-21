"""
Exemple d'utilisation de l'analyseur amélioré avec les extensions
"""

import logging
from pathlib import Path
from doc_analyzer.extractors.legal_docs import LegalDocsExtractor
from doc_analyzer.extensions.document_format_handler import DocumentFormatHandler
from doc_analyzer.extensions.data_validator import AdvancedDataValidator
from doc_analyzer.extensions.export_manager import ExportManager
from doc_analyzer.extensions.plugin_manager import PluginManager, PluginInterface
from doc_analyzer.extensions.error_manager import ErrorManager, DocumentError

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VynalDocsAutomator.Examples")

class CustomPlugin(PluginInterface):
    """Plugin personnalisé pour le traitement des factures"""
    
    VERSION = "1.0.0"
    AUTHOR = "VynalDocsAutomator"
    DEPENDENCIES = []
    
    def __init__(self):
        self._config = None
    
    def initialize(self, config: dict = None) -> bool:
        """Initialise le plugin avec la configuration"""
        self._config = config or {}
        return True
    
    def process_invoice(self, data: dict) -> dict:
        """Traite les données de facture"""
        # Exemple de traitement personnalisé
        if 'montant_ht' in data and 'tva' in data:
            data['montant_ttc'] = float(data['montant_ht']) * (1 + float(data['tva']) / 100)
        return data
    
    def cleanup(self) -> bool:
        """Nettoie les ressources du plugin"""
        return True

def main():
    """Exemple principal d'utilisation"""
    try:
        # 1. Initialisation des composants
        legal_extractor = LegalDocsExtractor()
        format_handler = DocumentFormatHandler()
        validator = AdvancedDataValidator()
        export_manager = ExportManager(export_dir="exports")
        plugin_manager = PluginManager(plugins_dir="plugins")
        error_manager = ErrorManager(error_log_dir="error_logs")
        
        # 2. Configuration du gestionnaire de plugins
        plugin_manager.create_plugin_template(
            "invoice_processor",
            author="VynalDocsAutomator",
            description="Plugin de traitement des factures"
        )
        
        # Enregistrer notre plugin personnalisé
        plugin_manager.load_plugin(
            "custom_plugin",
            "CustomPlugin",
            config={"validate_amounts": True}
        )
        
        # 3. Configurer les règles de validation pour la France
        validator.add_country_rule(
            "FR",
            "siret",
            r"^\d{14}$"
        )
        validator.add_country_rule(
            "FR",
            "tva",
            r"^FR\d{2}\d{9}$"
        )
        
        # 4. Analyser un document
        document_path = "examples/facture_exemple.txt"
        country_code = "FR"
        
        try:
            # Lire le contenu du document
            with open(document_path, 'r', encoding='utf-8') as f:
                document_content = f.read()
            
            # Analyse de base avec l'extracteur de documents légaux
            base_results = legal_extractor.extract(document_content)
            
            # Validation du format
            format_valid = format_handler.validate_document_format(
                country_code,
                base_results.get('document_type')
            )
            
            if not format_valid:
                raise DocumentError(
                    "Format de document invalide",
                    {"country": country_code}
                )
            
            # Validation des données
            is_valid, validation_errors = validator.validate_data(
                base_results,
                country_code
            )
            
            if not is_valid:
                raise DocumentError(
                    "Validation échouée",
                    {"errors": validation_errors}
                )
            
            # Enrichissement par les plugins
            plugin_results = plugin_manager.call_hook(
                "process_document",
                document=base_results,
                country=country_code
            )
            
            # Fusion des résultats
            enhanced_results = {
                **base_results,
                "validation": {
                    "is_valid": is_valid,
                    "format_valid": format_valid,
                    "errors": validation_errors
                },
                "plugin_results": plugin_results
            }
            
            # 5. Exporter les résultats dans différents formats
            # JSON
            json_path = export_manager.export_data(
                enhanced_results,
                "json",
                filename="resultats_analyse.json"
            )
            logger.info(f"Résultats exportés en JSON: {json_path}")
            
            # CSV
            csv_path = export_manager.export_data(
                enhanced_results,
                "csv",
                filename="resultats_analyse.csv",
                config={"delimiter": ";"}
            )
            logger.info(f"Résultats exportés en CSV: {csv_path}")
            
            # XML
            xml_path = export_manager.export_data(
                enhanced_results,
                "xml",
                filename="resultats_analyse.xml"
            )
            logger.info(f"Résultats exportés en XML: {xml_path}")
            
            logger.info("Analyse terminée avec succès")
            
        except DocumentError as e:
            # Gestion spécifique des erreurs de document
            error_manager.handle_error(e, {
                "document": document_path,
                "country": country_code
            })
            logger.error(f"Erreur de document: {e}")
            
        except Exception as e:
            # Gestion générale des erreurs
            error_manager.handle_error(e, {
                "document": document_path
            })
            logger.error(f"Erreur inattendue: {e}")
        
        # 6. Analyser les erreurs sur les dernières 24h
        error_stats = error_manager.analyze_errors(time_period="24h")
        logger.info("Statistiques d'erreurs:")
        logger.info(f"- Total: {error_stats['total_errors']}")
        logger.info(f"- Types: {error_stats['error_types']}")
        
        # 7. Nettoyer les ressources
        plugin_manager.unload_plugin("custom_plugin.CustomPlugin")
        
    except Exception as e:
        logger.error(f"Erreur critique: {e}")
        raise

if __name__ == "__main__":
    main() 