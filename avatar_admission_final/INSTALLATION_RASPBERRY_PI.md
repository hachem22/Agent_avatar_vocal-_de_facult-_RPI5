# Installation complète — Avatar d'admission sur Raspberry Pi 5 (8GB) + casque JBL Bluetooth

Config : Raspberry Pi 5 8GB, carte SD 128GB, casque JBL sans fil (Bluetooth).

---

## PARTIE 1 — Préparer le système d'exploitation

### 1.1 Flasher Raspberry Pi OS
1. Télécharge **Raspberry Pi Imager** sur ton PC : https://www.raspberrypi.com/software/
2. Choisis **Raspberry Pi OS (64-bit)** — version complète avec bureau (plus simple pour débuter, tu pourras passer en "headless" plus tard)
3. Dans les options avancées (icône ⚙️) :
   - Active SSH (pratique pour travailler depuis ton PC)
   - Configure le Wi-Fi
   - Définis un nom d'utilisateur/mot de passe
4. Flashe sur la carte SD 128GB, insère-la dans le Pi 5, démarre

### 1.2 Mettre à jour le système
```bash
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

### 1.3 Installer les outils de base
```bash
sudo apt install -y git python3-venv python3-pip python3-dev \
    build-essential portaudio19-dev libasound2-dev pipewire pipewire-audio \
    wireplumber bluez bluez-tools
```

---

## PARTIE 2 — Connecter le casque JBL en Bluetooth

### 2.1 Appairage
```bash
bluetoothctl
power on
agent on
default-agent
scan on
```
Mets ton JBL en mode appairage (bouton Bluetooth du casque). Attends qu'il apparaisse dans la liste avec son adresse MAC (format `XX:XX:XX:XX:XX:XX`), puis :
```bash
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
scan off
exit
```

### 2.2 Vérifier que PipeWire gère bien le casque
```bash
wpctl status
```
Tu dois voir ton JBL apparaître dans la section "Sinks" (sortie) et "Sources" (entrée micro).

### 2.3 Définir le JBL comme périphérique par défaut
```bash
wpctl status   # note les numéros d'ID du JBL (sink et source)
wpctl set-default <ID_DU_SINK>
wpctl set-default <ID_DE_LA_SOURCE>
```
Ou plus simple en interface graphique : clique sur l'icône son en haut à droite du bureau → sélectionne le JBL en sortie ET en entrée.

### 2.4 Test rapide du son
```bash
speaker-test -t wav -c 2   # tu dois entendre du son dans le JBL, Ctrl+C pour arrêter
arecord -d 5 -f cd test.wav && aplay test.wav   # test micro : enregistre 5s puis rejoue
```
⚠️ Si le micro ne capte rien, vérifie que le profil Bluetooth est bien en mode "Head Unit / HFP" (pas juste A2DP) :
```bash
wpctl status   # regarde le profil actif du device Bluetooth
```

---

## PARTIE 3 — Installer Ollama (le LLM local)

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Télécharge un modèle **léger**, adapté au Pi 5 (8GB RAM, pas de GPU dédié) :
```bash
ollama pull llama3.2:3b
```
Si c'est trop lent au test (Partie 6), essaie un modèle encore plus petit :
```bash
ollama pull llama3.2:1b
# ou
ollama pull phi3:mini
```
Puis change `OLLAMA_MODEL` dans `config.py` en conséquence.

Teste qu'il répond :
```bash
ollama run llama3.2:3b
```
Tape une question, vérifie la réponse, `/bye` pour quitter.

---

## PARTIE 4 — Copier ton projet depuis le PC vers le Pi

Sur ton **PC**, dans le dossier du projet (`avatar_admission/`) :
```bash
scp -r avatar_admission pi@<IP_DU_RASPBERRY>:/home/pi/
```
(Remplace `pi` par ton nom d'utilisateur et `<IP_DU_RASPBERRY>` par l'IP du Pi, visible avec `hostname -I` sur le Pi)

Ou plus simple : copie via une clé USB, ou `git clone` si tu as mis le projet sur GitHub.

---

## PARTIE 5 — Installer l'environnement Python sur le Pi

```bash
cd /home/pi/avatar_admission
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

⚠️ Sur Pi, l'installation de `faster-whisper` peut prendre du temps (compilation de certaines dépendances). Sois patient, ça peut prendre 10-15 minutes.

---

## PARTIE 6 — Installer Piper (TTS) — version ARM64

```bash
cd /home/pi/avatar_admission
mkdir -p piper_bin && cd piper_bin
wget https://github.com/rhasspy/piper/releases/latest/download/piper_linux_aarch64.tar.gz
tar -xvzf piper_linux_aarch64.tar.gz
```
Ajoute Piper au PATH (ajoute cette ligne à la fin de `~/.bashrc`) :
```bash
export PATH=$PATH:/home/pi/avatar_admission/piper_bin/piper
```
```bash
source ~/.bashrc
```

Télécharge une voix française (dans le dossier `voices/` du projet) :
```bash
cd /home/pi/avatar_admission/voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json
```

Teste :
```bash
cd /home/pi/avatar_admission
source venv/bin/activate
python tts.py
```
Tu dois entendre la voix dans le casque JBL.

---

## PARTIE 7 — Personnaliser le projet

Édite `config.py` avec les vraies infos de ton école (nom, programmes, frais, dates, contacts) :
```bash
nano config.py
```
`Ctrl+O` pour sauvegarder, `Ctrl+X` pour quitter.

---

## PARTIE 8 — Tester chaque brique séparément sur le Pi

```bash
source venv/bin/activate

python tts.py      # 1. teste la voix (haut-parleur JBL)
python stt.py       # 2. teste le micro JBL + transcription
python llm.py        # 3. teste les réponses au clavier (sans micro)
```

Ajuste si besoin dans `stt.py` :
- `SILENCE_THRESHOLD` — le micro Bluetooth capte souvent moins bien qu'un micro USB filaire, tu devras peut-être baisser ce seuil

---

## PARTIE 9 — Lancer le pipeline complet

```bash
python main.py
```
Parle dans le JBL → transcription → réponse LLM → lecture vocale dans le JBL.
Dis "stop" ou "au revoir" pour arrêter.

---

## PARTIE 10 — Lancer automatiquement au démarrage du Pi (Bluetooth + pipeline)

Le script `start_avatar.sh` fait tout automatiquement dans l'ordre : il attend
que le système soit prêt, connecte le casque JBL (`connect_jbl.sh`, avec 3
tentatives), puis lance `main.py`.

⚠️ **Important : ce projet ouvre des fenêtres graphiques** (l'avatar avec
`pygame`, et la fenêtre de debug caméra avec `cv2.imshow`). Un service
systemd classique n'a **pas accès à l'affichage graphique** par défaut (il
tourne "derrière" la session utilisateur), donc la méthode recommandée ici
est **l'autostart du bureau**, pas systemd.

### 10.1 Adapter le chemin dans `start_avatar.sh`
Ouvre `start_avatar.sh` et vérifie que `PROJET_DIR` correspond bien à
l'emplacement réel du projet sur le Pi (par défaut `/home/pi/avatar_admission_final`) :
```bash
nano start_avatar.sh
chmod +x start_avatar.sh connect_jbl.sh
```

### 10.2 Activer la connexion automatique au bureau (autologin)
Pour que l'avatar démarre **dès que le Pi est alimenté**, sans avoir à taper
de mot de passe, active la connexion automatique :
```bash
sudo raspi-config
```
→ `System Options` → `Boot / Auto Login` → `Desktop Autologin`. Redémarre.

### 10.3 Installer l'entrée d'autostart
```bash
mkdir -p ~/.config/autostart
cp autostart/avatar.desktop ~/.config/autostart/
```
Vérifie que le chemin `Exec=` dans ce fichier pointe bien vers ton
`start_avatar.sh` (même chemin que `PROJET_DIR` ci-dessus) :
```bash
nano ~/.config/autostart/avatar.desktop
```

### 10.4 Tester
Redémarre le Pi :
```bash
sudo reboot
```
Après le démarrage du bureau (~15-20 secondes d'attente intégrée au script),
le casque doit se connecter automatiquement puis les fenêtres avatar +
caméra doivent s'ouvrir toutes seules.

Consulte les logs si quelque chose ne se lance pas :
```bash
cat /home/pi/avatar_admission_final/avatar_boot.log
```

⚠️ Le jour de l'événement, teste bien ce démarrage automatique **la veille**
avec le vrai casque JBL chargé et à portée. Garde `python main.py` en lancement
manuel comme solution de secours si l'autostart ne se déclenche pas.

---

## PARTIE 11 — Configurer la caméra (détection de présence par vision)

Le projet peut détecter la présence d'une personne par caméra (au lieu du, ou
en plus du, capteur ultrason), avec une fenêtre qui montre en direct le flux
vidéo, les visages détectés (rectangle vert) et le texte "Personne détectée :
OUI / NON".

### 11.1 Choisir le mode dans `config.py`
```python
DETECTION_MODE = "camera"    # ou "ultrason", ou "les_deux"
CAMERA_TYPE = "usb"          # ou "picamera2" si module officiel CSI
```

### 11.2 Cas 1 — Webcam USB
Branche-la puis vérifie qu'elle est détectée :
```bash
ls /dev/video*
```
Rien à installer de plus, `opencv-python` (déjà dans `requirements.txt`)
suffit. Si tu as plusieurs caméras/webcams, ajuste `CAMERA_INDEX` dans
`config.py` (0, 1, 2...) selon celle que tu veux utiliser.

### 11.3 Cas 2 — Module caméra officiel Raspberry Pi (CSI)
1. Branche le ruban CSI dans le connecteur caméra du Pi 5 (Pi éteint), puis démarre
2. Vérifie qu'il est détecté :
```bash
libcamera-hello --list-cameras
```
3. Installe `picamera2` via **apt** (pas pip, il a besoin de composants système) :
```bash
sudo apt install -y python3-picamera2
```
4. Recrée ton environnement virtuel avec accès aux paquets système, pour que
   `picamera2` soit visible dedans :
```bash
rm -rf venv
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
```
5. Mets `CAMERA_TYPE = "picamera2"` dans `config.py`

### 11.4 Tester la caméra seule
```bash
source venv/bin/activate
python camera.py
```
Une fenêtre doit s'ouvrir avec le flux vidéo en direct. Mets-toi devant :
le texte doit passer à "Personne détectée : OUI" avec un rectangle vert
autour de ton visage. Ctrl+C dans le terminal pour arrêter.

### 11.5 Ajuster la sensibilité
Dans `config.py` :
- `CAMERA_MIN_FACE_SIZE` : augmente si la caméra détecte des personnes trop
  loin (faux positifs), diminue si elle ne détecte pas assez tôt
- `CAMERA_FRAMES_SANS_VISAGE_AVANT_DEPART` : augmente si la conversation se
  coupe trop vite quand la personne bouge la tête ou cligne des yeux
- `CAMERA_SHOW_WINDOW = False` si tu veux désactiver la fenêtre de debug une
  fois que tout fonctionne bien (traitement en arrière-plan uniquement)

### 11.6 Combiner caméra + ultrason
Avec `DETECTION_MODE = "les_deux"`, une détection par l'un OU l'autre des
deux capteurs suffit à démarrer la conversation — utile si tu veux une
détection plus fiable (le capteur ultrason marche même dans le noir, la
caméra confirme qu'il s'agit bien d'une personne).

---

## Résumé — checklist avant le jour de l'événement

- [ ] JBL chargé à 100%, appairé et testé la veille
- [ ] `config.py` rempli avec les vraies infos à jour de l'école
- [ ] Modèle Ollama testé pour la vitesse de réponse (change pour un modèle plus léger si trop lent)
- [ ] Test complet du pipeline (`main.py`) dans un environnement bruyant pour ajuster `SILENCE_THRESHOLD`
- [ ] Caméra testée seule (`python camera.py`) et sensibilité ajustée (`CAMERA_MIN_FACE_SIZE`)
- [ ] Autologin bureau activé + `avatar.desktop` copié dans `~/.config/autostart/`
- [ ] Redémarrage complet testé (`sudo reboot`) : Bluetooth + fenêtres se lancent seuls
- [ ] Batterie/chargeur du Pi 5 et du JBL disponibles sur place
- [ ] Plan B : lancement manuel (`python main.py`) si l'autostart ne démarre pas correctement

---

## Problèmes fréquents

| Problème | Solution |
|---|---|
| Le micro JBL ne capte rien | Vérifier le profil Bluetooth (doit être HFP/Head Unit, pas juste A2DP) via `wpctl status` |
| Ollama très lent sur le Pi | Utiliser un modèle plus petit (`llama3.2:1b` ou `phi3:mini`) |
| Le Pi rame en général | Vérifier qu'aucune appli lourde ne tourne en fond, surveiller avec `htop` |
| Le Bluetooth se déconnecte | Rapprocher le Pi du JBL, éviter les interférences Wi-Fi 2.4GHz |
| Faster-whisper très lent | Utiliser un modèle plus petit (`WHISPER_MODEL_SIZE = "base"` ou `"tiny"` dans `config.py`) |
| La fenêtre caméra ne s'ouvre pas | Vérifier que `opencv-python` est installé (PAS `opencv-python-headless`) : `pip show opencv-python` |
| `cv2.VideoCapture` échoue / caméra non trouvée | Vérifier `ls /dev/video*`, essayer `CAMERA_INDEX = 1` ou `2`, vérifier le branchement USB |
| Module caméra CSI non détecté | `libcamera-hello --list-cameras`, vérifier le sens du ruban CSI, `sudo apt update && sudo apt full-upgrade` |
| L'avatar ne se lance pas seul au démarrage | Vérifier l'autologin (`sudo raspi-config`), vérifier `~/.config/autostart/avatar.desktop`, consulter `avatar_boot.log` |
| Le Bluetooth ne se connecte pas automatiquement | Vérifier l'adresse MAC dans `connect_jbl.sh`, augmenter le `sleep` initial dans `start_avatar.sh` si le Pi met du temps à démarrer le Bluetooth |
