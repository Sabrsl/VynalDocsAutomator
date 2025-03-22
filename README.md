# VynalDocsAutomator

## Description
VynalDocsAutomator est une application Python conçue pour automatiser la création, la gestion et l'analyse de documents à l'aide de modèles personnalisables. Cette solution complète prend en charge l'extraction de texte à partir de différents formats, la génération de documents, et offre une interface conviviale pour la gestion de vos documents.

## Fonctionnalités principales

### Gestion des documents
- **Création de documents** à partir de modèles personnalisables
- **Génération automatique** de documents en formats PDF et DOCX
- **Conversion entre formats** (PDF, DOCX, TXT, etc.)
- **Analyse intelligente** du contenu des documents
- **Extraction de données structurées** à partir de documents non structurés
- **Application de watermarks** et signatures aux documents

### OCR et reconnaissance de texte
- **Reconnaissance optique de caractères (OCR)** avec Tesseract
- **Prise en charge multilingue** (français, anglais, etc.)
- **Traitement d'images** pour améliorer la qualité de reconnaissance
- **Extraction de texte** à partir d'images et de documents scannés

### Gestion des clients et données
- **Base de données clients** intégrée
- **Stockage des informations client** pour auto-complétion de documents
- **Remplacement automatique de variables** dans les modèles
- **Recherche intelligente** dans la base de données client
- **Import/export** des données clients (JSON, CSV)

### Intelligence artificielle et NLP
- **Analyse sémantique** des documents
- **Détection automatique** des entités (noms, dates, montants, etc.)
- **Classification de documents** par type et contenu
- **Suggestions intelligentes** basées sur le contenu
- **Analyse avancée par modèles de langage**:
  - Intégration avec **Ollama** pour traitement local
  - Support du modèle **Llama3** pour l'analyse en français
  - Utilisation de **Llama** pour l'extraction d'informations complexes
- **Extraction contextuelle** d'informations spécifiques au domaine
- **Résumé automatique** de documents longs
- **Détection d'incohérences** dans les contrats et documents légaux
- **Comparaison intelligente** entre plusieurs versions d'un document

### Interface utilisateur
- **Interface graphique moderne** avec customtkinter
- **Écran de démarrage** avec progression
- **Thème clair/sombre** adaptatif
- **Interface responsive** adaptée à différentes tailles d'écran
- **Notifications système** pour les opérations longues

### API et intégrations
- **API REST** avec FastAPI pour l'intégration avec d'autres systèmes
- **Mode serveur** pour traitement distribué
- **Endpoints pour** upload, traitement, et récupération de documents
- **Support CORS** pour intégration web

### Sécurité et monitoring
- **Journalisation complète** des opérations
- **Statistiques d'utilisation** et de performance
- **Surveillance des processus** en arrière-plan
- **Mécanismes de récupération** après erreur

### Optimisations
- **Système de cache** pour améliorer les performances
- **Traitement asynchrone** des tâches longues
- **Opérations en arrière-plan** pour une interface fluide
- **Gestion de la mémoire** pour les documents volumineux

## Prérequis

### Python et packages

- Python 3.8 ou supérieur
- Packages Python (installés automatiquement) :
  - pytesseract
  - pdf2image
  - Pillow
  - customtkinter
  - spacy
  - nltk
  - fastapi
  - uvicorn
  - docx
  - reportlab
  - ollama-python
  - langchain
  - transformers
  - autres dépendances...

### Tesseract OCR

Pour utiliser les fonctionnalités de reconnaissance de texte (OCR), vous devez installer Tesseract :

#### Windows
1. Téléchargez l'installateur depuis [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Exécutez l'installateur
3. Installez dans `C:\Program Files\Tesseract-OCR`
4. Sélectionnez au moins les langues French et English

#### Linux
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-fra
```

#### macOS
```bash
brew install tesseract tesseract-lang
```

## Installation
Pour installer et configurer le projet, suivez ces étapes :

1. Clonez le dépôt :
    ```bash
    git clone https://github.com/Sabrsl/VynalDocsAutomator.git
    cd VynalDocsAutomator
    ```

2. Créez un environnement virtuel :
    ```bash
    python -m venv venv
    source venv/bin/activate # Sur Windows, utilisez `venv\Scripts\activate`
    ```

3. Installez les dépendances requises :
    ```bash
    pip install -r requirements.txt
    ```

4. Installez Tesseract OCR comme indiqué ci-dessus

## Utilisation

### Interface graphique
1. Lancez l'application avec interface graphique :
    ```bash
    python run_with_splash.py
    ```
   ou simplement :
    ```bash
    python main.py
    ```

2. Suivez les instructions à l'écran pour gérer vos clients, modèles et générer des documents.

### API REST
1. Démarrez le serveur API :
    ```bash
    python backend.py
    ```

2. L'API est accessible à l'adresse `http://localhost:8000`
3. Documentation Swagger disponible à `http://localhost:8000/docs`

### Ligne de commande
Vous pouvez également utiliser l'application en ligne de commande :
```bash
python document_processor.py --client "Nom Client" --template "modele_facture.docx" --output "facture_finale.pdf"
```

## Exemples d'utilisation

### Traitement d'un document
```python
from document_processor import DocumentProcessor

processor = DocumentProcessor()
document_text = "Contrat pour {{CLIENT_NOM}}, datant du {{DATE}}..."
processed_text, variables = processor.process_document(document_text, "Entreprise XYZ")
```

### Analyse de document avec OCR
```python
from doc_analyzer.analyzer import DocumentAnalyzer

analyzer = DocumentAnalyzer()
results = analyzer.analyze_document("facture.pdf")
print(f"Type de document détecté : {results['document_type']}")
print(f"Montant total : {results['total_amount']}")
```

### Analyse de document avec IA
```python
from ai.document_analyzer import AIDocumentAnalyzer

# Initialisation avec un modèle Ollama local
analyzer = AIDocumentAnalyzer(model="llama3")

# Analyse d'un contrat
results = analyzer.analyze_contract("contrat_location.pdf")
print(f"Parties impliquées: {results['parties']}")
print(f"Obligations principales: {results['obligations']}")
print(f"Risques détectés: {results['risks']}")

# Génération de résumé
summary = analyzer.generate_summary("rapport_annuel.pdf")
print(f"Résumé du document: {summary}")
```

## Contribution
Les contributions sont les bienvenues ! Pour contribuer :

1. Forkez le dépôt.
2. Créez une nouvelle branche (`git checkout -b feature/VotreFeature`).
3. Commitez vos changements (`git commit -m 'Ajout d'une fonctionnalité'`).
4. Poussez vers la branche (`git push origin feature/VotreFeature`).
5. Ouvrez une Pull Request.

## Licence
Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Contact
Pour toute question, veuillez contacter le propriétaire du dépôt à [Sabrsl](https://github.com/Sabrsl).
