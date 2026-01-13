#!/usr/bin/env python3
"""
Fonctions utilitaires pour le serveur de mods
"""

import os
import json
import hashlib
from datetime import datetime

def calculate_sha256(filepath):
    """Calcule le checksum SHA256 d'un fichier"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Lire par chunks pour ne pas charger tout le fichier en mémoire
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_manifest(mods_folder):
    """Génère le fichier manifest.json avec la liste des mods"""
    mods = []

    for filename in os.listdir(mods_folder):
        if filename.endswith('.jar'):
            filepath = os.path.join(mods_folder, filename)
            stat = os.stat(filepath)

            # Calculer le checksum
            sha256 = calculate_sha256(filepath)

            mods.append({
                'filename': filename,
                'size': stat.st_size,
                'sha256': sha256,
                'url': f'/mods/{filename}'
            })

    # Créer le manifest
    manifest = {
        'version': '1.0.0',
        'minecraft_version': '1.20.1',
        'last_updated': datetime.now().isoformat(),
        'mods': mods
    }

    # Écrire le manifest.json
    manifest_path = os.path.join(mods_folder, 'manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Manifest généré avec {len(mods)} mod(s)")
    return manifest

def format_size(bytes):
    """Formate la taille en octets en format lisible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"
