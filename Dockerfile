FROM python:3.11-slim

WORKDIR /app

# Copier les requirements et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY server/ ./server/

# Créer le dossier mods
RUN mkdir -p /app/mods

# Exposer le port
EXPOSE 8080

# Variables d'environnement par défaut
ENV ADMIN_PASSWORD=admin
ENV SECRET_KEY=changeme-in-production

# Lancer l'application
WORKDIR /app/server
CMD ["python", "app.py"]
