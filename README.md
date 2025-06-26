# 🤖 Robot Telemetry API – Flask Backend

Ce projet est une API Flask qui permet de :
- Recevoir des données de télémétrie envoyées par un robot
- Récupérer et mettre à jour des commandes
- Accuser réception des commandes
- Stocker toutes les données dans une base SQLite via SQLAlchemy
- Gérer les migrations avec Alembic

---

## 📦 Installation

### 1. Cloner le dépôt

**2. Installer les dépendances**
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
**3. Initialiser la base de données**
alembic upgrade head
**🚀 Lancer l’application**
python3 api_app.py
L'API sera accessible à : http://127.0.0.1:5000
