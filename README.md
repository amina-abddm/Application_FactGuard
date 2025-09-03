# 🛡️ FactGuard

> Une application web intelligente de détection des fake news à partir de liens, textes ou images soumis par les utilisateurs.

## 📌 Description

FactGuard est une plateforme collaborative et intelligente permettant aux utilisateurs de soumettre des informations (textes, URL ou images) afin de vérifier leur fiabilité. En s'appuyant sur l’intelligence artificielle (LLM + ML), des APIs d'actualités et des services cognitifs (OCR, NLP), l’application attribue un **score de fiabilité** à chaque contenu, tout en expliquant son raisonnement de façon transparente.

---

## 🚀 Fonctionnalités principales

- ✅ Authentification (inscription, connexion sécurisée)
- ✅ Dashboard utilisateur avec :
  - 🔍 **Analyseur** (texte, URL, image)
  - 📊 **Statistiques personnalisées** selon les préférences
  - 📁 **Historique des analyses passées**
- ✅ Détection automatique de fake news avec scoring & explication
- ✅ Système de préférences d’actualité (sport, finance, politique…)
- ✅ Interface responsive & accessible

---

## 🛠️ Technologies utilisées

- **Backend** : Django (Python)
- **Frontend** : HTML / CSS / JavaScript
- **Base de données** : SQLite / PostgreSQL (dev/prod)
- **IA & API** :
  - Azure Cognitive Services (OCR / NLP)
  - OpenAI GPT (LLM pour analyse sémantique)
  - APIs d’actualités (NewsAPI, Bing News, etc.)
- **Machine Learning** : modèle supervisé de scoring de fiabilité
- **Pipeline data** : Azure Data Factory (ou scripts CRON)

---

## 🧪 Fonctionnalités IA

- 🔁 Classification binaire (fiable / non fiable)
- 🎯 Score de fiabilité (%) + justification
- 📖 Analyse linguistique (fake news markers, biais, sources)
- 📸 OCR pour traitement d’images
- 🔄 Apprentissage continu à partir de l’historique

---

## 📚 Structure du projet

---

## 🔐 Authentification

- Utilisateurs créés via un formulaire sécurisé
- Gestion des sessions Django
- Sécurité : hachage des mots de passe, validation email

---

## ⚙️ À venir (Roadmap)

- 📱 Application mobile (React Native ou Flutter)
- 🔄 Amélioration du moteur de recommandation
- 🌐 Extension navigateur (analyse automatique de page web)
- 💬 Ajout d’un chatbot pour analyse conversationnelle

---

## 💡 MVP du projet

- Authentification simple
- Analyse texte & lien avec scoring
- Historique des analyses
- Recommandation d’articles par préférence
-Interface fonctionnelle (responsive)

---

## 🤝 Équipe projet

👩‍💻 Membres :

- Amina [PO/UX]
- Bafodé [Développeur Front]
- Ryad [Développeur Back]

🧭 Méthodologie :

- Travail en sprints agiles (4 semaines)
- Collaboration via Notion, Jira, GitHub, Discord
- Design avec Figma et v0
- Organisation via CBL Organizer

---

## ✅ Lancer le projet en local

```bash
git clone https://github.com/ton-repo/factguard.git
cd factguard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```
