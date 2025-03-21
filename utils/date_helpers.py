import logging
from datetime import datetime

logger = logging.getLogger("VynalDocsAutomator.DateHelpers")

def parse_iso_datetime(date_str):
    """
    Parse une chaîne de date au format ISO 8601 avec gestion des exceptions
    Supporte les formats avec/sans timezone et le format 'Z'
    
    Args:
        date_str: Chaîne de date au format ISO
    
    Returns:
        datetime: Objet datetime
    """
    if not date_str:
        return datetime.now()  # Valeur par défaut
    
    try:
        # Format standard ISO
        return datetime.fromisoformat(date_str)
    except ValueError:
        # Format ISO avec Z (UTC)
        if date_str.endswith('Z'):
            # Remplacer Z par +00:00 qui est supporté par fromisoformat
            try:
                date_str = date_str[:-1] + '+00:00'
                return datetime.fromisoformat(date_str)
            except ValueError:
                pass
        
        # Essayer d'autres formats courants
        for fmt in [
            "%Y-%m-%dT%H:%M:%S.%f", 
            "%Y-%m-%dT%H:%M:%S", 
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d"
        ]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Si aucun format ne fonctionne, logger l'erreur et retourner l'heure actuelle
        logger.warning(f"Format de date non reconnu: {date_str}, utilisation de la date actuelle")
        return datetime.now()
    except Exception as e:
        logger.warning(f"Erreur de traitement de date '{date_str}': {e}")
        return datetime.now()

def format_datetime(dt, format_str="%d/%m/%Y %H:%M"):
    """
    Formate un objet datetime selon le format spécifié
    avec gestion des exceptions
    
    Args:
        dt: Objet datetime ou chaîne ISO
        format_str: Format de sortie
        
    Returns:
        str: Date formatée
    """
    # Si dt est une chaîne, la convertir en datetime
    if isinstance(dt, str):
        dt = parse_iso_datetime(dt)
    
    # Si dt n'est pas un datetime valide, utiliser la date actuelle
    if not isinstance(dt, datetime):
        dt = datetime.now()
    
    try:
        return dt.strftime(format_str)
    except Exception as e:
        logger.warning(f"Erreur de formatage de date: {e}")
        return datetime.now().strftime(format_str) 