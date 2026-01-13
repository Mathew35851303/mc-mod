# API Documentation - Los Nachos Minecraft Mods Server

Documentation de l'API pour intégrer le serveur de mods avec un launcher Minecraft.

## URL de base

```
http://votre-serveur:8085
```

---

## Endpoints Publics (sans authentification)

Ces endpoints sont accessibles sans authentification et sont destinés au launcher.

### GET `/manifest.json`

Récupère la liste complète des mods avec leurs métadonnées.

**Requête :**
```http
GET /manifest.json
```

**Réponse :**
```json
{
  "version": "1.0.0",
  "minecraft_version": "1.20.1",
  "last_updated": "2024-01-13T14:30:00.000000",
  "mods": [
    {
      "filename": "sodium-fabric-0.5.3.jar",
      "size": 1234567,
      "sha256": "a1b2c3d4e5f6...",
      "url": "/mods/sodium-fabric-0.5.3.jar"
    },
    {
      "filename": "lithium-fabric-0.11.1.jar",
      "size": 987654,
      "sha256": "f6e5d4c3b2a1...",
      "url": "/mods/lithium-fabric-0.11.1.jar"
    }
  ]
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `version` | string | Version du manifest |
| `minecraft_version` | string | Version de Minecraft ciblée |
| `last_updated` | string | Date de dernière mise à jour (ISO 8601) |
| `mods` | array | Liste des mods disponibles |
| `mods[].filename` | string | Nom du fichier .jar |
| `mods[].size` | integer | Taille du fichier en octets |
| `mods[].sha256` | string | Hash SHA256 pour vérification d'intégrité |
| `mods[].url` | string | Chemin relatif pour télécharger le mod |

---

### GET `/mods/{filename}`

Télécharge un fichier mod spécifique.

**Requête :**
```http
GET /mods/sodium-fabric-0.5.3.jar
```

**Réponse :**
- **200 OK** : Le fichier .jar en téléchargement
- **404 Not Found** : Le mod n'existe pas

---

## Intégration Launcher

### Workflow recommandé

```
┌─────────────────────────────────────────────────────────────┐
│                      LAUNCHER                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  GET /manifest.json     │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Comparer avec mods     │
              │  locaux (via SHA256)    │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Télécharger les mods   │
              │  manquants/modifiés     │
              │  GET /mods/{filename}   │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Supprimer les mods     │
              │  non listés             │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │  Lancer Minecraft       │
              └─────────────────────────┘
```

### Exemple d'implémentation (Python)

```python
import requests
import hashlib
import os

SERVER_URL = "http://votre-serveur:8085"
MODS_DIR = "./mods"

def get_manifest():
    """Récupère le manifest depuis le serveur"""
    response = requests.get(f"{SERVER_URL}/manifest.json")
    response.raise_for_status()
    return response.json()

def calculate_sha256(filepath):
    """Calcule le hash SHA256 d'un fichier local"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def download_mod(filename):
    """Télécharge un mod depuis le serveur"""
    response = requests.get(f"{SERVER_URL}/mods/{filename}", stream=True)
    response.raise_for_status()

    filepath = os.path.join(MODS_DIR, filename)
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Téléchargé: {filename}")

def sync_mods():
    """Synchronise les mods locaux avec le serveur"""
    os.makedirs(MODS_DIR, exist_ok=True)

    # Récupérer le manifest
    manifest = get_manifest()
    server_mods = {mod["filename"]: mod for mod in manifest["mods"]}

    # Lister les mods locaux
    local_mods = set()
    for filename in os.listdir(MODS_DIR):
        if filename.endswith(".jar"):
            local_mods.add(filename)

    # Télécharger les mods manquants ou modifiés
    for filename, mod_info in server_mods.items():
        filepath = os.path.join(MODS_DIR, filename)

        if filename not in local_mods:
            # Mod manquant
            print(f"Nouveau mod: {filename}")
            download_mod(filename)
        else:
            # Vérifier le hash
            local_hash = calculate_sha256(filepath)
            if local_hash != mod_info["sha256"]:
                print(f"Mod modifié: {filename}")
                download_mod(filename)
            else:
                print(f"Mod à jour: {filename}")

    # Supprimer les mods non présents sur le serveur
    for filename in local_mods:
        if filename not in server_mods:
            filepath = os.path.join(MODS_DIR, filename)
            os.remove(filepath)
            print(f"Supprimé: {filename}")

    print("Synchronisation terminée!")

if __name__ == "__main__":
    sync_mods()
```

### Exemple d'implémentation (JavaScript/Node.js)

```javascript
const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const SERVER_URL = 'http://votre-serveur:8085';
const MODS_DIR = './mods';

async function getManifest() {
    return new Promise((resolve, reject) => {
        http.get(`${SERVER_URL}/manifest.json`, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(JSON.parse(data)));
            res.on('error', reject);
        });
    });
}

function calculateSHA256(filepath) {
    return new Promise((resolve, reject) => {
        const hash = crypto.createHash('sha256');
        const stream = fs.createReadStream(filepath);
        stream.on('data', data => hash.update(data));
        stream.on('end', () => resolve(hash.digest('hex')));
        stream.on('error', reject);
    });
}

async function downloadMod(filename) {
    return new Promise((resolve, reject) => {
        const filepath = path.join(MODS_DIR, filename);
        const file = fs.createWriteStream(filepath);

        http.get(`${SERVER_URL}/mods/${filename}`, (res) => {
            res.pipe(file);
            file.on('finish', () => {
                file.close();
                console.log(`Téléchargé: ${filename}`);
                resolve();
            });
        }).on('error', reject);
    });
}

async function syncMods() {
    // Créer le dossier mods si nécessaire
    if (!fs.existsSync(MODS_DIR)) {
        fs.mkdirSync(MODS_DIR, { recursive: true });
    }

    // Récupérer le manifest
    const manifest = await getManifest();
    const serverMods = new Map(manifest.mods.map(m => [m.filename, m]));

    // Lister les mods locaux
    const localMods = new Set(
        fs.readdirSync(MODS_DIR).filter(f => f.endsWith('.jar'))
    );

    // Télécharger les mods manquants ou modifiés
    for (const [filename, modInfo] of serverMods) {
        const filepath = path.join(MODS_DIR, filename);

        if (!localMods.has(filename)) {
            console.log(`Nouveau mod: ${filename}`);
            await downloadMod(filename);
        } else {
            const localHash = await calculateSHA256(filepath);
            if (localHash !== modInfo.sha256) {
                console.log(`Mod modifié: ${filename}`);
                await downloadMod(filename);
            } else {
                console.log(`Mod à jour: ${filename}`);
            }
        }
    }

    // Supprimer les mods non présents sur le serveur
    for (const filename of localMods) {
        if (!serverMods.has(filename)) {
            fs.unlinkSync(path.join(MODS_DIR, filename));
            console.log(`Supprimé: ${filename}`);
        }
    }

    console.log('Synchronisation terminée!');
}

syncMods().catch(console.error);
```

---

## Endpoints Admin (authentification requise)

Ces endpoints nécessitent une session authentifiée (cookie de session Flask).

### POST `/login`

Authentification pour accéder à l'interface admin.

**Requête :**
```http
POST /login
Content-Type: application/x-www-form-urlencoded

password=votre_mot_de_passe
```

**Réponse :**
- **302 Redirect** vers `/admin` si succès
- **200 OK** avec message d'erreur si échec

---

### GET `/api/mods`

Liste tous les mods avec leurs informations détaillées.

**Requête :**
```http
GET /api/mods
Cookie: session=...
```

**Réponse :**
```json
{
  "mods": [
    {
      "filename": "sodium-fabric-0.5.3.jar",
      "size": 1234567,
      "sha256": "a1b2c3d4e5f6...",
      "modified": "2024-01-13T14:30:00"
    }
  ]
}
```

---

### POST `/api/upload`

Upload un ou plusieurs mods.

**Requête :**
```http
POST /api/upload
Cookie: session=...
Content-Type: multipart/form-data

file=@sodium-fabric-0.5.3.jar
```

**Réponse :**
```json
{
  "success": true,
  "uploaded": ["sodium-fabric-0.5.3.jar"],
  "message": "1 mod(s) uploadé(s) avec succès"
}
```

---

### DELETE `/api/mods/{filename}`

Supprime un mod.

**Requête :**
```http
DELETE /api/mods/sodium-fabric-0.5.3.jar
Cookie: session=...
```

**Réponse :**
```json
{
  "success": true,
  "message": "sodium-fabric-0.5.3.jar supprimé avec succès"
}
```

---

### POST `/api/regenerate`

Régénère le manifest.json manuellement.

**Requête :**
```http
POST /api/regenerate
Cookie: session=...
```

**Réponse :**
```json
{
  "success": true,
  "message": "Manifest régénéré avec succès"
}
```

---

### GET `/api/stats`

Statistiques sur les mods.

**Requête :**
```http
GET /api/stats
Cookie: session=...
```

**Réponse :**
```json
{
  "total_mods": 15,
  "total_size": 52428800,
  "last_modified": "2024-01-13T14:30:00"
}
```

---

## Codes d'erreur

| Code | Description |
|------|-------------|
| 200 | Succès |
| 302 | Redirection (login/logout) |
| 400 | Requête invalide (fichier manquant, format incorrect) |
| 401 | Non authentifié (redirection vers login) |
| 404 | Ressource non trouvée |

---

## Notes

- Les fichiers acceptés sont uniquement les `.jar`
- Le manifest est automatiquement régénéré après chaque upload/suppression
- Les hash SHA256 permettent de vérifier l'intégrité des fichiers téléchargés
- Pour le launcher, seuls `/manifest.json` et `/mods/{filename}` sont nécessaires
