#!/usr/bin/env python3
"""
Los Nachos Minecraft Mods Server
Serveur Flask pour gérer les mods avec interface web
"""

import os
import json
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from werkzeug.utils import secure_filename
from functools import wraps
import utils

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'changeme-in-production')

# Configuration
MODS_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mods'))
MANIFEST_FILE = os.path.join(MODS_FOLDER, 'manifest.json')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
ALLOWED_EXTENSIONS = {'jar'}

# Créer le dossier mods s'il n'existe pas
os.makedirs(MODS_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Vérifie si le fichier est un .jar"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    """Décorateur pour protéger les routes admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Page d'accueil - Redirection vers l'admin"""
    return redirect(url_for('admin'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error='Mot de passe incorrect')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    """Interface web d'administration"""
    return render_template('index.html')

@app.route('/manifest.json')
def get_manifest():
    """API : Télécharger le manifest (pour le launcher)"""
    if os.path.exists(MANIFEST_FILE):
        return send_from_directory(MODS_FOLDER, 'manifest.json')
    else:
        # Générer le manifest s'il n'existe pas
        utils.generate_manifest(MODS_FOLDER)
        if os.path.exists(MANIFEST_FILE):
            return send_from_directory(MODS_FOLDER, 'manifest.json')
        else:
            return jsonify({'error': 'Manifest not found'}), 404

@app.route('/mods/<filename>')
def download_mod(filename):
    """API : Télécharger un mod spécifique"""
    return send_from_directory(MODS_FOLDER, filename)

@app.route('/api/mods', methods=['GET'])
@login_required
def list_mods():
    """API : Liste tous les mods avec leurs infos"""
    mods = []
    for filename in os.listdir(MODS_FOLDER):
        if filename.endswith('.jar'):
            filepath = os.path.join(MODS_FOLDER, filename)
            stat = os.stat(filepath)

            # Calculer le checksum
            sha256 = utils.calculate_sha256(filepath)

            mods.append({
                'filename': filename,
                'size': stat.st_size,
                'sha256': sha256,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

    return jsonify({'mods': mods})

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_mod():
    """API : Upload un mod"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    files = request.files.getlist('file')
    uploaded = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(MODS_FOLDER, filename)
            file.save(filepath)
            uploaded.append(filename)

    if uploaded:
        # Régénérer le manifest
        utils.generate_manifest(MODS_FOLDER)
        return jsonify({
            'success': True,
            'uploaded': uploaded,
            'message': f'{len(uploaded)} mod(s) uploadé(s) avec succès'
        })
    else:
        return jsonify({'error': 'No valid files uploaded'}), 400

@app.route('/api/mods/<filename>', methods=['DELETE'])
@login_required
def delete_mod(filename):
    """API : Supprimer un mod"""
    filepath = os.path.join(MODS_FOLDER, secure_filename(filename))

    if os.path.exists(filepath) and filename.endswith('.jar'):
        os.remove(filepath)
        # Régénérer le manifest
        utils.generate_manifest(MODS_FOLDER)
        return jsonify({
            'success': True,
            'message': f'{filename} supprimé avec succès'
        })
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/regenerate', methods=['POST'])
@login_required
def regenerate_manifest():
    """API : Régénérer le manifest.json"""
    utils.generate_manifest(MODS_FOLDER)
    return jsonify({
        'success': True,
        'message': 'Manifest régénéré avec succès'
    })

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """API : Statistiques sur les mods"""
    mods = []
    total_size = 0
    last_modified = None

    for filename in os.listdir(MODS_FOLDER):
        if filename.endswith('.jar'):
            filepath = os.path.join(MODS_FOLDER, filename)
            stat = os.stat(filepath)
            mods.append(filename)
            total_size += stat.st_size

            mod_time = datetime.fromtimestamp(stat.st_mtime)
            if last_modified is None or mod_time > last_modified:
                last_modified = mod_time

    return jsonify({
        'total_mods': len(mods),
        'total_size': total_size,
        'last_modified': last_modified.isoformat() if last_modified else None
    })

if __name__ == '__main__':
    # Générer le manifest au démarrage
    utils.generate_manifest(MODS_FOLDER)

    # Démarrer le serveur
    app.run(host='0.0.0.0', port=8080, debug=False)
