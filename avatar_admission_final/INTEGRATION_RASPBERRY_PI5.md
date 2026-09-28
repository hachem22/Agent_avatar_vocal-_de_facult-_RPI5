# Intégration complète du projet Avatar sur Raspberry Pi 5

Ce guide part de zéro et couvre TOUT : OS, dépendances, transfert du projet,
Bluetooth JBL, et démarrage automatique en plein écran (mode kiosque).

Matériel nécessaire : Raspberry Pi 5 (8GB), carte SD 128GB, écran (HDMI),
casque JBL Bluetooth, alimentation officielle USB-C 27W, dissipateur/ventilateur.

---

## PARTIE 1 — Installer l'OS

1. Télécharge **Raspberry Pi Imager** sur ton PC : https://www.raspberrypi.com/software/
2. Choisis **Raspberry Pi OS (64-bit)** — version avec bureau
3. Dans les options avancées (⚙️) : active SSH, configure le Wi-Fi, définis utilisateur/mot de passe
4. Flashe sur la carte SD, insère-la dans le Pi 5, branche écran + alimentation, démarre

Mets à jour :
```bash
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

Installe les outils de base :
```bash
sudo apt install -y git python3-venv python3-pip python3-dev \
    build-essential portaudio19-dev libasound2-dev pipewire pipewire-audio \
    wireplumber bluez bluez-tools
```

---

## PARTIE 2 — Connecter le casque JBL

```bash
bluetoothctl
power on
agent on
default-agent
scan on
```
Mets le JBL en mode appairage, note son adresse MAC affichée, puis :
```bash
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
scan off
exit
```

Définis-le comme entrée/sortie par défaut :
```bash
wpctl status              # note les ID du JBL (sink et source)
wpctl set-default <ID_SINK>
wpctl set-default <ID_SOURCE>
```

Teste :
```bash
speaker-test -t wav -c 2      # Ctrl+C pour arreter
arecord -d 5 -f cd test.wav && aplay test.wav
```

---

## PARTIE 3 — Installer Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
```
Si trop lent sur le Pi, essaie un modèle plus léger :
```bash
ollama pull llama3.2:1b
```
(puis change `OLLAMA_MODEL` dans `config.py` en conséquence)

---

## PARTIE 4 — Transférer le projet vers le Pi

Depuis ton PC, dans le dossier `avatar_admission` :
```bash
scp -r avatar_admission pi@<IP_DU_PI>:/home/pi/
```
(trouve l'IP du Pi avec `hostname -I` exécuté sur le Pi lui-même)

---

## PARTIE 5 — Installer l'environnement Python

```bash
cd /home/pi/avatar_admission
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
⚠️ `faster-whisper` peut prendre 10-15 minutes à s'installer sur le Pi (patience).

---

## PARTIE 6 — Installer Piper (voix) — version ARM64

```bash
cd /home/pi/avatar_admission
mkdir -p piper_bin && cd piper_bin
wget https://github.com/rhasspy/piper/releases/latest/download/piper_linux_aarch64.tar.gz
tar -xvzf piper_linux_aarch64.tar.gz
```

Télécharge la voix française :
```bash
cd /home/pi/avatar_admission/voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json
```

**Important** : sur le Pi (Linux), l'exécutable n'a pas d'extension `.exe`. Ouvre `config.py` et corrige :
```python
PIPER_EXECUTABLE = "piper_bin/piper/piper"   # sans .exe, contrairement a Windows
```

Vérifie le chemin exact :
```bash
find /home/pi/avatar_admission/piper_bin -name "piper"
```

Teste :
```bash
source venv/bin/activate
python tts.py
```
Tu dois entendre la voix française dans le JBL.

---

## PARTIE 7 — Vérification complète

```bash
python check_setup.py
```
Corrige tout ce qui est signalé en échec avant de continuer.

---

## PARTIE 8 — Tester chaque brique

```bash
python stt.py       # micro
python llm.py        # IA (au clavier)
python avatar_visual.py   # avatar visuel avec tes photos
```

---

## PARTIE 9 — Lancer le pipeline complet

```bash
python main.py
```

---

## PARTIE 10 — Démarrage automatique en mode kiosque (plein écran, sans bureau)

C'est l'étape qui rend le système "présentable" pour l'événement : le Pi démarre
directement sur l'avatar en plein écran, sans montrer le bureau Linux.

### 10.1 — Configurer l'affichage plein écran dans le code

Dans `avatar_visual.py`, la fenêtre pygame doit s'ouvrir en plein écran. Ajoute
le flag `pygame.FULLSCREEN` lors de la création de la fenêtre (déjà présent dans
le code, adapte si besoin selon la résolution exacte de ton écran final).

### 10.2 — Créer le service systemd

```bash
sudo nano /etc/systemd/system/avatar.service
```
Contenu :
```ini
[Unit]
Description=Avatar Admission
After=bluetooth.target network.target graphical.target

[Service]
Environment=DISPLAY=:0
ExecStart=/home/pi/avatar_admission/venv/bin/python /home/pi/avatar_admission/main.py
WorkingDirectory=/home/pi/avatar_admission
Restart=on-failure
User=pi

[Install]
WantedBy=graphical.target
```

Active-le :
```bash
sudo systemctl daemon-reload
sudo systemctl enable avatar.service
sudo systemctl start avatar.service
```

Voir les logs en direct :
```bash
journalctl -u avatar.service -f
```

### 10.3 — Cacher le bureau au démarrage (mode kiosque complet, optionnel)

Pour que le Pi démarre directement sur l'app sans jamais montrer le bureau :
```bash
sudo raspi-config
```
→ System Options → Boot / Auto Login → **Desktop Autologin**

Puis désactive les éléments visuels inutiles (barre des tâches, écran de veille)
via les paramètres du bureau Raspberry Pi OS.

⚠️ **Recommandation** : garde aussi un moyen simple de lancer `python main.py`
manuellement (raccourci sur le bureau ou accès SSH) en secours pour le jour J,
au cas où le service automatique aurait un souci de timing avec le Bluetooth.

---

## Checklist finale avant l'événement

- [ ] `check_setup.py` passe sans erreur
- [ ] JBL appairé et testé la veille, chargé à 100%
- [ ] `config.py` avec les vraies infos à jour de l'école
- [ ] Le service `avatar.service` démarre bien tout seul après un redémarrage complet du Pi
- [ ] Testé en continu plusieurs heures sans plantage ni surchauffe
- [ ] Plan B (lancement manuel) prêt si besoin

---

## Problèmes fréquents

| Problème | Solution |
|---|---|
| Le micro JBL ne capte rien | Vérifier le profil Bluetooth (HFP/Head Unit) via `wpctl status` |
| Ollama très lent | Modèle plus léger (`llama3.2:1b` ou `phi3:mini`) |
| Piper "command not found" | Vérifier `PIPER_EXECUTABLE` dans `config.py` (sans `.exe` sur Pi) |
| Le service ne montre rien à l'écran | Vérifier `Environment=DISPLAY=:0` et que `graphical.target` est bien atteint avant le service |
| Le Bluetooth ne se reconnecte pas après redémarrage | Vérifier `trust` a bien été fait (pas juste `pair`), teste un redémarrage complet |
