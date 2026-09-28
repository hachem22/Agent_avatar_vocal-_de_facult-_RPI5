# Installation complète — Avatar d'admission sur PC Windows (100% local)

---

## ÉTAPE 1 — Installer Python

1. Télécharge Python 3.11 (recommandé, bonne compatibilité avec faster-whisper) :
   https://www.python.org/downloads/
2. Lors de l'installation, **coche bien la case "Add python.exe to PATH"** en bas de la première fenêtre — c'est l'erreur la plus fréquente
3. Vérifie dans un terminal (PowerShell ou CMD) :
```powershell
python --version
pip --version
```

---

## ÉTAPE 2 — Installer Ollama (déjà fait chez toi, sinon)

Télécharge et installe : https://ollama.com/download/windows

Ollama tourne en service en fond sur Windows automatiquement après installation. Vérifie :
```powershell
ollama --version
ollama pull llama3.2:3b
ollama run llama3.2:3b
```
Tape une question test, vérifie la réponse, `/bye` pour quitter.

---

## ÉTAPE 3 — Récupérer le projet et créer l'environnement virtuel

Ouvre PowerShell dans le dossier `avatar_admission` :
```powershell
cd chemin\vers\avatar_admission
python -m venv venv
venv\Scripts\activate
```
Ton invite de commande doit maintenant afficher `(venv)` au début.

Installe les dépendances :
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

⚠️ Si `pyaudio`/`sounddevice` pose problème à l'installation sur Windows, installe d'abord les outils de compilation :
```powershell
pip install pipwin
pipwin install pyaudio
```
(Généralement pas nécessaire avec `sounddevice`, mais garde ça sous la main en cas d'erreur.)

---

## ÉTAPE 4 — Installer Piper (Text-to-Speech) pour Windows

1. Télécharge la version Windows de Piper :
   https://github.com/rhasspy/piper/releases → cherche `piper_windows_amd64.zip`
2. Dézippe dans le dossier du projet, par exemple : `avatar_admission\piper_bin\`
3. Ajoute ce dossier au PATH pour cette session PowerShell :
```powershell
$env:Path += ";$PWD\piper_bin"
```
   (Pour que ce soit permanent : Paramètres Windows → Variables d'environnement → ajouter le chemin complet à la variable `Path`)

4. Télécharge une voix française et place les 2 fichiers dans `avatar_admission\voices\` :
   - https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx
   - https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json

5. Teste :
```powershell
python tts.py
```
Tu dois entendre une voix française dans tes haut-parleurs/casque.

---

## ÉTAPE 5 — Connecter le casque JBL en Bluetooth (Windows)

1. **Paramètres Windows → Bluetooth et appareils → Ajouter un appareil**
2. Mets le JBL en mode appairage (bouton Bluetooth du casque, généralement maintenu 3-5 secondes jusqu'au clignotement)
3. Sélectionne-le dans la liste Windows, attends la connexion
4. **Paramètres → Son** :
   - Sortie : sélectionne le JBL
   - Entrée : sélectionne le JBL (Windows le liste souvent comme "JBL... (Hands-Free AG Audio)" pour le mode avec micro)

⚠️ Point important identique à ce qu'on a vu pour le Pi : Windows bascule automatiquement le JBL en mode "mains libres" (avec micro, qualité audio réduite) dès qu'une application utilise le micro. C'est normal, pas un bug.

Teste le micro Windows : **Paramètres → Son → Entrée → Tester le micro** (une barre de niveau doit bouger quand tu parles).

---

## ÉTAPE 6 — Personnaliser le projet

Ouvre `config.py` avec un éditeur de texte (VS Code recommandé) et remplis les vraies infos de ton école (programmes, frais, dates, contacts, etc.)

---

## ÉTAPE 7 — Tester chaque brique séparément

Dans PowerShell, avec le venv activé :
```powershell
python tts.py      # 1. Teste la voix
python stt.py       # 2. Teste le micro + transcription (parle, attends le silence)
python llm.py        # 3. Teste les réponses au clavier
```

Si le micro coupe trop vite ou pas assez, ajuste dans `config.py` ou en haut de `stt.py` :
- `SILENCE_THRESHOLD` (sensibilité)
- `SILENCE_DURATION` (temps de silence avant coupure)

---

## ÉTAPE 8 — Lancer le pipeline complet avec l'avatar visuel

```powershell
python main.py
```
Une fenêtre s'ouvre avec le visage de l'avatar, parle dans le JBL, la bouche s'anime pendant que l'avatar répond.

Dis "stop" ou "au revoir" pour arrêter, ou ferme simplement la fenêtre.

---

## Problèmes fréquents sur Windows

| Problème | Solution |
|---|---|
| `python` non reconnu | Réinstaller Python en cochant "Add to PATH", ou utiliser `py` à la place de `python` |
| Erreur d'installation `sounddevice`/`pyaudio` | Installer via `pipwin`, ou installer "Microsoft C++ Build Tools" |
| Le micro JBL ne capte rien | Vérifier dans Paramètres → Son → Entrée que le JBL est bien sélectionné, et que le profil est "Hands-Free" |
| Piper introuvable ("commande non reconnue") | Vérifier le PATH, ou utiliser le chemin complet vers `piper.exe` dans `tts.py` |
| Ollama très lent | Utiliser un modèle plus léger (`llama3.2:1b` ou `phi3:mini`) dans `config.py` |
| La fenêtre avatar ne s'affiche pas | Vérifier que `pygame` est bien installé (`pip show pygame`) |
