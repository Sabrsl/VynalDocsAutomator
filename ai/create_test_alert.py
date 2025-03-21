import json
import os
from datetime import datetime

# Obtenir le chemin du répertoire de données de l'application
base_dir = os.path.join(os.path.expanduser("~"), ".vynal_docs_automator")
admin_dir = os.path.join(base_dir, "admin")
data_dir = os.path.join(admin_dir, "data")
security_alerts_file = os.path.join(data_dir, "security_alerts.json")

# Créer l'alerte de test
alert = {
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'type': 'suspicious_login',
    'details': 'Tentative de connexion suspecte détectée',
    'ip': '192.168.1.100',
    'device_info': {
        'os': 'Windows 10',
        'browser': 'Chrome',
        'device': 'Desktop'
    }
}

# S'assurer que le répertoire existe
os.makedirs(os.path.dirname(security_alerts_file), exist_ok=True)

# Lire les alertes existantes
alerts = []
try:
    with open(security_alerts_file, 'r') as f:
        alerts = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    alerts = []

# Ajouter la nouvelle alerte
alerts.append(alert)

# Sauvegarder les alertes
with open(security_alerts_file, 'w', encoding='utf-8') as f:
    json.dump(alerts, f, indent=4, ensure_ascii=False)

# Créer aussi un fichier de log pour test
logs_dir = os.path.join(admin_dir, "logs")
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, "system.log")

with open(log_file, 'a', encoding='utf-8') as f:
    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [INFO] Test log entry\n")

print(f"Alerte de sécurité créée avec succès dans {security_alerts_file}")
print(f"Fichier de log créé : {log_file}") 