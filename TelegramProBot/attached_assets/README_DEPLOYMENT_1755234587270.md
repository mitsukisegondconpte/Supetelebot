# 🏆 Bot d'Échecs Telegram - Guide de Déploiement Gratuit

## 📋 Description
Bot d'échecs moderne avec interface à boutons, localisé en français. Permet de jouer contre le moteur Stockfish avec des fonctionnalités avancées d'export et de gestion des photos.

## 🎯 Fonctionnalités
- ✅ Interface entièrement en français avec boutons interactifs
- ♟️ Coups groupés par type de pièce (Pion, Tour, Cavalier, Fou, Reine, Roi)
- 🤖 Moteur Stockfish intégré (niveau configurable)
- 📸 Export PNG, FEN et PGN en fin de partie
- 🗑️ Gestion de l'espace de stockage (suppression des photos)
- 👥 Support multi-utilisateurs avec isolation des parties
- 🛡️ Fonctionnalités d'administration pour le propriétaire

## 🚀 Déploiement Gratuit sur Replit

### Étape 1 : Préparation
1. Téléchargez le fichier `chess_bot_deployment.zip`
2. Créez un compte gratuit sur [Replit.com](https://replit.com)
3. Connectez-vous à votre compte Replit

### Étape 2 : Import du projet
1. Cliquez sur "Create Repl" sur votre dashboard Replit
2. Sélectionnez "Import from GitHub" ou "Upload files"
3. Si upload : décompressez le ZIP et uploadez tous les fichiers
4. Nommez votre repl : `chess-bot-francais`
5. Cliquez sur "Create Repl"

### Étape 3 : Configuration du token Telegram
1. Contactez [@BotFather](https://t.me/BotFather) sur Telegram
2. Envoyez `/newbot`
3. Choisissez un nom pour votre bot (ex: "Mon Bot d'Échecs")
4. Choisissez un username (ex: `mon_echecs_bot`)
5. Copiez le token reçu (format: `123456789:ABCdef...`)

### Étape 4 : Mise à jour du code
1. Dans Replit, ouvrez le fichier `bot_modern.py`
2. Ligne 23, remplacez le token :
   ```python
   BOT_TOKEN = "VOTRE_TOKEN_ICI"
   ```
3. Ligne 24, remplacez par votre ID Telegram :
   ```python
   OWNER_ID = VOTRE_ID_TELEGRAM
   ```

**Pour trouver votre ID Telegram :**
- Envoyez un message à [@userinfobot](https://t.me/userinfobot)
- Copiez l'ID reçu

### Étape 5 : Installation des dépendances
Dans le terminal Replit (onglet Shell), exécutez :
```bash
pip install python-telegram-bot python-chess cairosvg
```

### Étape 6 : Configuration du fichier principal
1. Dans Replit, créez ou modifiez `.replit` :
```
run = "python bot_modern.py"
language = "python3"

[packager]
packages = ["python-chess", "python-telegram-bot", "cairosvg"]

[languages.python3]
pattern = "**/*.py"
syntax = "python"
```

### Étape 7 : Démarrage
1. Cliquez sur le bouton "Run" (▶️) dans Replit
2. Le bot va se lancer et afficher "Bot démarré !"
3. Testez en envoyant `/start` à votre bot sur Telegram

## 🛠️ Maintenance et Mise à Jour

### Garder le bot en ligne 24/7
**Option gratuite :**
- Replit : Le bot fonctionnera quand le navigateur est ouvert
- UptimeRobot : Service gratuit pour "ping" votre repl et le maintenir actif

**Option payante (Replit Hacker Plan - $7/mois) :**
- Always On : Bot en ligne 24/7 automatiquement

### Modifier les paramètres
Dans `bot_modern.py`, vous pouvez ajuster :
- `STOCKFISH_SKILL_LEVEL` : Niveau de difficulté (1-20)
- `STOCKFISH_TIME` : Temps de réflexion de l'IA (secondes)

### Sauvegarde
- Replit sauvegarde automatiquement votre code
- Téléchargez régulièrement vos fichiers via "Download as zip"

## 🔧 Résolution de Problèmes

### Erreur "Module not found"
```bash
pip install --upgrade python-telegram-bot python-chess cairosvg
```

### Erreur "Cairo library not found"
Dans le Shell de Replit :
```bash
apt update
apt install libcairo2-dev libpango1.0-dev
```

### Bot ne répond pas
1. Vérifiez que le token est correct dans `bot_modern.py`
2. Assurez-vous que le bot est démarré (console affiche "Bot démarré !")
3. Vérifiez que le bot n'est pas déjà en cours d'exécution ailleurs

### Performances lentes
- Le niveau gratuit de Replit peut être plus lent
- Réduisez `STOCKFISH_TIME` à 0.5 pour des réponses plus rapides

## 📊 Utilisation

### Commandes de base
- `/start` : Démarrer le bot et voir l'interface
- Interface à boutons pour toutes les interactions

### Fonctionnalités utilisateur
- **Nouvelle partie** : Commence une partie contre Stockfish
- **Coups par pièce** : Boutons organisés par type de pièce
- **Export** : PNG, FEN, PGN à la fin de la partie
- **Nettoyage** : Suppression des photos pour économiser l'espace

### Fonctionnalités admin (propriétaire uniquement)
- Statistiques globales du bot
- Liste des parties actives
- Export global des données

## 💡 Conseils d'Optimisation

### Réduire l'usage d'espace
- Encouragez les utilisateurs à supprimer leurs photos après export
- Les exports FEN et PGN sont des fichiers texte légers

### Améliorer les performances
- Ajustez `STOCKFISH_SKILL_LEVEL` selon vos besoins
- Réduisez `STOCKFISH_TIME` pour des réponses plus rapides

### Sécurité
- Ne partagez jamais votre token de bot
- Gardez votre ID Telegram privé
- Activez l'authentification 2FA sur Replit

## 🆘 Support

En cas de problème :
1. Vérifiez les logs dans la console Replit
2. Consultez la documentation Telegram Bot API
3. Redémarrez le repl en cas de blocage

## 📝 Licence
Projet open source - Utilisez et modifiez librement pour vos besoins personnels.

---
**Bon jeu d'échecs ! ♟️🏆**