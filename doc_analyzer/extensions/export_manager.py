"""
Gestionnaire d'export des résultats
"""

import os
import json
import csv
import xml.etree.ElementTree as ET
from typing import Dict, Any
from pathlib import Path

class ExportManager:
    """Gère l'export des résultats dans différents formats"""
    
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = export_dir
        Path(export_dir).mkdir(parents=True, exist_ok=True)
    
    def export_data(self, data: Dict[str, Any], format: str, filename: str = None, config: Dict = None) -> str:
        """
        Exporte les données dans le format spécifié
        
        Args:
            data: Données à exporter
            format: Format d'export (json, csv, xml)
            filename: Nom du fichier de sortie
            config: Configuration spécifique au format
            
        Returns:
            str: Chemin du fichier exporté
        """
        if not filename:
            filename = f"export.{format}"
        
        output_path = os.path.join(self.export_dir, filename)
        
        if format == "json":
            return self._export_json(data, output_path)
        elif format == "csv":
            return self._export_csv(data, output_path, config)
        elif format == "xml":
            return self._export_xml(data, output_path)
        else:
            raise ValueError(f"Format non supporté: {format}")
    
    def _export_json(self, data: Dict[str, Any], output_path: str) -> str:
        """Exporte en JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return output_path
    
    def _export_csv(self, data: Dict[str, Any], output_path: str, config: Dict = None) -> str:
        """Exporte en CSV"""
        config = config or {}
        delimiter = config.get('delimiter', ',')
        
        # Aplatir les données
        flat_data = self._flatten_dict(data)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(['Champ', 'Valeur'])
            for key, value in flat_data.items():
                writer.writerow([key, value])
        
        return output_path
    
    def _export_xml(self, data: Dict[str, Any], output_path: str) -> str:
        """Exporte en XML"""
        root = ET.Element('document')
        self._dict_to_xml(data, root)
        
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
        return output_path
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, str]:
        """Aplatit un dictionnaire imbriqué"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                    else:
                        items.append((f"{new_key}[{i}]", str(item)))
            else:
                items.append((new_key, str(v)))
        return dict(items)
    
    def _dict_to_xml(self, d: Dict[str, Any], parent: ET.Element):
        """Convertit un dictionnaire en éléments XML"""
        for key, value in d.items():
            child = ET.SubElement(parent, key)
            if isinstance(value, dict):
                self._dict_to_xml(value, child)
            elif isinstance(value, list):
                for item in value:
                    item_elem = ET.SubElement(child, 'item')
                    if isinstance(item, dict):
                        self._dict_to_xml(item, item_elem)
                    else:
                        item_elem.text = str(item)
            else:
                child.text = str(value) 