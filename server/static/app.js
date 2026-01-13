// Los Nachos Mods Manager - Frontend JavaScript

// État de l'application
let mods = [];

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadMods();
    setupEventListeners();
});

// Configuration des écouteurs d'événements
function setupEventListeners() {
    // Bouton de sélection de fichiers
    document.getElementById('selectFilesBtn').addEventListener('click', () => {
        document.getElementById('fileInput').click();
    });

    // Upload de fichiers
    document.getElementById('fileInput').addEventListener('change', handleFileSelect);

    // Drag and drop
    const dropZone = document.getElementById('dropZone');
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);

    // Bouton rafraîchir
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadStats();
        loadMods();
    });

    // Bouton régénérer manifest
    document.getElementById('regenerateBtn').addEventListener('click', regenerateManifest);

    // Bouton déconnexion
    document.getElementById('logoutBtn').addEventListener('click', () => {
        window.location.href = '/logout';
    });
}

// Charger les statistiques
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('totalMods').textContent = data.total_mods;
        document.getElementById('totalSize').textContent = formatSize(data.total_size);

        if (data.last_modified) {
            const lastUpdate = new Date(data.last_modified);
            document.getElementById('lastUpdate').textContent = formatTimeAgo(lastUpdate);
        } else {
            document.getElementById('lastUpdate').textContent = 'Jamais';
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Charger la liste des mods
async function loadMods() {
    try {
        const response = await fetch('/api/mods');
        const data = await response.json();
        mods = data.mods;
        renderMods();
    } catch (error) {
        console.error('Error loading mods:', error);
        showNotification('Erreur lors du chargement des mods', 'error');
    }
}

// Afficher les mods
function renderMods() {
    const modsList = document.getElementById('modsList');

    if (mods.length === 0) {
        modsList.innerHTML = `
            <div class="empty-state">
                <p>📦 Aucun mod installé</p>
                <p style="font-size: 14px;">Uploadez vos premiers mods pour commencer</p>
            </div>
        `;
        return;
    }

    modsList.innerHTML = mods.map(mod => `
        <div class="mod-item">
            <div class="mod-info">
                <div class="mod-name">🟢 ${mod.filename}</div>
                <div class="mod-details">${formatSize(mod.size)}</div>
                <div class="mod-sha">SHA256: ${mod.sha256.substring(0, 16)}...</div>
            </div>
            <div class="mod-actions">
                <button class="btn-secondary" onclick="downloadMod('${mod.filename}')">📥 Télécharger</button>
                <button class="btn-danger" onclick="deleteMod('${mod.filename}')">🗑️ Supprimer</button>
            </div>
        </div>
    `).join('');
}

// Gérer la sélection de fichiers
function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    uploadFiles(files);
}

// Gérer le drag over
function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.add('dragover');
}

// Gérer le drag leave
function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.remove('dragover');
}

// Gérer le drop
function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.remove('dragover');

    const files = Array.from(event.dataTransfer.files).filter(f => f.name.endsWith('.jar'));
    if (files.length > 0) {
        uploadFiles(files);
    } else {
        showNotification('Seuls les fichiers .jar sont acceptés', 'error');
    }
}

// Uploader des fichiers
async function uploadFiles(files) {
    const formData = new FormData();
    files.forEach(file => {
        formData.append('file', file);
    });

    // Afficher la progression
    const uploadProgress = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    uploadProgress.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = `Upload de ${files.length} fichier(s)...`;

    try {
        // Simuler la progression (Flask n'a pas de vraie progression)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                progressFill.style.width = progress + '%';
            }
        }, 100);

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        clearInterval(progressInterval);
        progressFill.style.width = '100%';

        const data = await response.json();

        if (response.ok) {
            showNotification(data.message, 'success');
            await loadStats();
            await loadMods();
        } else {
            showNotification(data.error || 'Erreur lors de l\'upload', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification('Erreur lors de l\'upload', 'error');
    } finally {
        setTimeout(() => {
            uploadProgress.style.display = 'none';
            // Réinitialiser le file input
            document.getElementById('fileInput').value = '';
        }, 1000);
    }
}

// Télécharger un mod
function downloadMod(filename) {
    window.open(`/mods/${filename}`, '_blank');
}

// Supprimer un mod
async function deleteMod(filename) {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer ${filename} ?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/mods/${filename}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            showNotification(data.message, 'success');
            await loadStats();
            await loadMods();
        } else {
            showNotification(data.error || 'Erreur lors de la suppression', 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('Erreur lors de la suppression', 'error');
    }
}

// Régénérer le manifest
async function regenerateManifest() {
    try {
        const response = await fetch('/api/regenerate', {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showNotification(data.message, 'success');
            await loadStats();
        } else {
            showNotification('Erreur lors de la régénération', 'error');
        }
    } catch (error) {
        console.error('Regenerate error:', error);
        showNotification('Erreur lors de la régénération', 'error');
    }
}

// Afficher une notification
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Formater la taille en octets
function formatSize(bytes) {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }

    return `${size.toFixed(2)} ${units[unitIndex]}`;
}

// Formater le temps relatif
function formatTimeAgo(date) {
    const now = new Date();
    const diff = now - date;

    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'À l\'instant';
    if (minutes < 60) return `Il y a ${minutes} minute${minutes > 1 ? 's' : ''}`;
    if (hours < 24) return `Il y a ${hours} heure${hours > 1 ? 's' : ''}`;
    return `Il y a ${days} jour${days > 1 ? 's' : ''}`;
}
