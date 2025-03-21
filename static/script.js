// Configuration
const API_URL = 'http://localhost:8000';
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const uploadProgress = document.getElementById('uploadProgress');
const uploadStatus = document.getElementById('uploadStatus');
const fileList = document.getElementById('fileList');
const fileDetailsModal = new bootstrap.Modal(document.getElementById('fileDetailsModal'));

// Gestion du drag & drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, unhighlight, false);
});

function highlight(e) {
    dropZone.classList.add('dragover');
}

function unhighlight(e) {
    dropZone.classList.remove('dragover');
}

dropZone.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

// Gestion de la sélection de fichier
fileInput.addEventListener('change', function(e) {
    handleFiles(this.files);
});

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
            uploadFile(file);
        } else {
            showStatus('Seuls les fichiers CSV sont acceptés', 'danger');
        }
    }
}

// Upload de fichier
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        showStatus('Upload en cours...', 'info');
        uploadProgress.classList.remove('d-none');
        uploadProgress.querySelector('.progress-bar').style.width = '0%';

        const response = await fetch(`${API_URL}/upload/`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showStatus('Fichier uploadé avec succès !', 'success');
            refreshFileList();
        } else {
            showStatus(data.detail || 'Erreur lors de l\'upload', 'danger');
        }
    } catch (error) {
        showStatus('Erreur de connexion au serveur', 'danger');
        console.error('Erreur:', error);
    } finally {
        uploadProgress.classList.add('d-none');
    }
}

// Affichage des messages de statut
function showStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = `alert alert-${type} mt-3 fade-in`;
    uploadStatus.classList.remove('d-none');
    setTimeout(() => {
        uploadStatus.classList.add('d-none');
    }, 5000);
}

// Liste des fichiers
async function refreshFileList() {
    try {
        const response = await fetch(`${API_URL}/files/`);
        const data = await response.json();

        fileList.innerHTML = '';
        data.files.forEach(file => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${file.filename}</td>
                <td>${formatFileSize(file.size)}</td>
                <td>${formatDate(file.upload_date)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary btn-action" onclick="showFileDetails('${file.filename}')">
                        <i class="bi bi-info-circle"></i>
                    </button>
                </td>
            `;
            fileList.appendChild(row);
        });
    } catch (error) {
        console.error('Erreur:', error);
        showStatus('Erreur lors de la récupération de la liste des fichiers', 'danger');
    }
}

// Détails du fichier
async function showFileDetails(filename) {
    try {
        const response = await fetch(`${API_URL}/files/${filename}`);
        const data = await response.json();

        const details = document.getElementById('fileDetails');
        details.innerHTML = `
            <div class="mb-3">
                <strong>Nom du fichier:</strong> ${data.filename}
            </div>
            <div class="mb-3">
                <strong>Taille:</strong> ${formatFileSize(data.size)}
            </div>
            <div class="mb-3">
                <strong>Date d'upload:</strong> ${formatDate(data.upload_date)}
            </div>
            <div class="mb-3">
                <strong>Chemin:</strong> ${data.path}
            </div>
        `;

        fileDetailsModal.show();
    } catch (error) {
        console.error('Erreur:', error);
        showStatus('Erreur lors de la récupération des détails du fichier', 'danger');
    }
}

// Utilitaires
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('fr-FR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    refreshFileList();
}); 