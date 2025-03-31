# Backend Rugby Fauteuil – Projet de Coaching Stratégique

![Flask](https://img.shields.io/badge/built%20with-flask-red)
![Status](https://img.shields.io/badge/status-en%20cours-yellow)

Ce backend fait partie du projet de **coaching stratégique pour le rugby en fauteuil**, conçu dans une approche de design thinking durant l'année 2024. Il est destiné à collecter, stocker et restituer des données issues de capteurs embarqués sur les joueurs (accélération, fréquence cardiaque, température...) afin d'alimenter une interface de visualisation pour les coachs et analystes.

Projet présenté lors d'une **summer school** avec la participation de l'UPSSITECH, l'université d'Ostfalia, l'université de Wuerzburg et l'université technologique de Munster.
---

## 🚀 Objectif

- Offrir une API REST et WebSocket pour alimenter une interface de monitoring temps réel.
- Centraliser les données physiologiques et de collision.
- Préparer les données à des fins d'analyse sportive, statistique et stratégique (ex : heatmaps, suivi fatigue).

---

## 🔍 Fonctionnalités principales

- Réception de données capteurs via POST :
  - **Chocs** : accéléromètre
  - **Température & humidité** 
  - **Rythme cardiaque** 
- Stockage via SQLAlchemy dans une base SQLite
- Gestion des entités : Clubs, Joueurs, Championnats, Matchs, Statistiques
- Modes d’affichage configurables via WebSocket
- Streaming vidéo redirigé depuis l'ESP32-Cam

---

## ⚖️ Stack Technique

- **Langage** : Python 3
- **Framework** : Flask, Flask-SocketIO, Flask-CORS, SQLAlchemy
- **Librairies** :
  - `requests`, `logging`, `datetime`, `dateutil`
- **Base de données** : SQLite
- **Architecture** : REST API + Socket.IO + ORM

---

## 🌍 Lien vers l’interface associée

Frontend Angular : [interface_rugby_wheelchair_FE](https://github.com/GuyBorel/interface_rugby_wheelchair_FE)
---

## ✅ Statut

Ce projet est **fonctionnel** mais encore en cours de test. Il peut être déployé localement pour collecter les données via ESP32 et les consulter via l'interface frontend.

---

## 📂 Lancer le backend localement

```bash
# 1. Cloner le repo
$ git clone https://github.com/Bebel19/rugby_wheelchair_backend.git
$ cd rugby_wheelchair_backend

# 2. Installer les dépendances
$ pip install flask flask-socketio flask-cors flask-sqlalchemy requests python-dateutil

# 3. Lancer le serveur
$ python3 app.py

# Backend accessible sur http://localhost:5000
```

---

## 💡 Exemples de routes API

```http
POST /data                 # Données de choc
POST /temperature_data     # Données temp/humidité
POST /heartrate_data       # Données de BPM
GET  /shocks               # Tous les chocs
GET  /sensor_data/<id>     # Données mixtes pour un capteur
```

---

## 📄 Modèles de données (extraits)

- `ShockData(sensorID, accelX, accelY, accelZ, shockDetected)`
- `TemperatureHumidityData(sensorID, temperature, humidity)`
- `HeartRateData(sensorID, BPM)`
- `Player`, `Match`, `Championship`, `Club`...

---

**Projet universitaire collaboratif** — UPSSITECH 2024  
Initiative : Coaching stratégique via capteurs embarqués et IA
