# GUIDE MAÎTRE — Intégration complète de l'Avatar sur Raspberry Pi 5

Ce document est le guide UNIQUE à suivre du début à la fin. Suis les parties
dans l'ordre. Chaque partie se termine par un test — ne passe à la suivante
que si le test précédent fonctionne.

---

## PARTIE 1 — Flasher l'OS sur la carte SD

1. Sur ton PC, télécharge **Raspberry Pi Imager** : https://www.raspberrypi.com/software/
2. Choisis **Raspberry Pi OS (64-bit)** avec bureau
3. Options avancées (⚙️) : active SSH, configure le Wi-Fi, définis utilisateur `pi` / mot de passe
4. Flashe sur la carte SD 128GB, insère-la dans le Pi 5
5. Branche écran (HDMI), alimentation officielle 27W, dissipateur/ventilateur, démarre

**✅ Test** : le bureau Raspberry Pi OS s'affiche à l'écran.

```bash
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

---

## PARTIE 2 — Installer les dépendances système

```bash
sudo apt install -y git python3-venv python3-pip python3-dev \
    build-essential portaudio19-dev libasound2-dev pipewire pipewire-audio \
    wireplumber bluez bluez-tools python3-gpiozero python3-lgpio \
    libspa-0.2-bluetooth
```

**✅ Test** :
```bash
python3 --version   # doit afficher Python 3.11 ou plus
bluetoothctl --version
```

⚠️ **Piège fréquent** : `libspa-0.2-bluetooth` est INDISPENSABLE pour que
PipeWire puisse gérer l'audio Bluetooth. Sans ce paquet, tu peux appairer
le JBL avec succès, mais il n'apparaîtra jamais dans `wpctl status` comme
sortie/entrée audio utilisable (seul l'audio HDMI apparaîtra). Si tu as déjà
suivi ce guide sans ce paquet, installe-le maintenant puis redémarre :
```bash
sudo apt install -y libspa-0.2-bluetooth
sudo reboot
```

---

## PARTIE 3 — Connecter et tester le casque JBL

```bash
bluetoothctl
power on
agent on
default-agent
scan on
```
Mets le JBL en mode appairage (généralement : maintenir le bouton Bluetooth
3-5 secondes jusqu'au clignotement). Attends qu'il apparaisse dans la liste,
note son adresse MAC (`XX:XX:XX:XX:XX:XX`), puis :
```bash
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
scan off
exit
```

Définis-le comme périphérique par défaut :
```bash
wpctl status
```
Note les ID affichés pour le JBL (dans la section Sinks pour la sortie, et
Sources pour l'entrée micro), puis :
```bash
wpctl set-default <ID_SINK_JBL>
wpctl set-default <ID_SOURCE_JBL>
```

**✅ Test JBL #1 — Haut-parleur** :
```bash
speaker-test -t wav -c 2
```
Tu dois entendre du son dans le JBL. `Ctrl+C` pour arrêter.

**✅ Test JBL #2 — Micro** :
```bash
arecord -d 5 -f cd test.wav
```
Parle pendant les 5 secondes, puis :
```bash
aplay test.wav
```
Tu dois t'entendre parler, rejoué dans le JBL.

⚠️ Si le micro ne capte rien : vérifie que le profil Bluetooth actif est bien
`headset-head-unit` (HFP, avec micro) et pas juste `a2dp-sink` (musique
seule, sans micro) :
```bash
pactl list cards | grep -A 5 bluez
```

---

## PARTIE 4 — Installer Ollama et télécharger le modèle

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
```

**✅ Test** :
```bash
ollama run llama3.2:3b
```
Tape une question, vérifie qu'il répond. `/bye` pour quitter.

Si trop lent sur le Pi, utilise un modèle plus léger et change
`OLLAMA_MODEL` dans `config.py` :
```bash
ollama pull llama3.2:1b
```

---

## PARTIE 5 — Transférer le projet vers le Pi

Depuis ton PC (PowerShell), dans le dossier `avatar_admission` :
```powershell
scp -r avatar_admission pi@<IP_DU_PI>:/home/pi/
```
(trouve l'IP du Pi avec `hostname -I` exécuté directement sur le Pi)

**✅ Test** :
```bash
cd /home/pi/avatar_admission
ls
```
Tu dois voir tous les fichiers : `main.py`, `config.py`, `stt.py`, `llm.py`,
`tts.py`, `avatar_visual.py`, `lipsync.py`, `sensor.py`, `requirements.txt`,
`assets/`, `voices/`.

---

## PARTIE 6 — Installer l'environnement Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
⚠️ `faster-whisper` peut prendre 10-15 minutes à s'installer (patience).

**✅ Test** :
```bash
python -c "import faster_whisper, sounddevice, pygame, gpiozero; print('Tout est installe correctement')"
```

---

## PARTIE 7 — Installer Piper (voix) version ARM64

```bash
mkdir -p piper_bin && cd piper_bin
wget https://github.com/rhasspy/piper/releases/latest/download/piper_linux_aarch64.tar.gz
tar -xvzf piper_linux_aarch64.tar.gz
cd ..
find /home/pi/avatar_admission/piper_bin -name "piper"
```

Note le chemin exact affiché, puis ouvre `config.py` et corrige (sans `.exe`
sur Linux, contrairement à Windows) :
```python
PIPER_EXECUTABLE = "piper_bin/piper/piper"   # ajuste selon le chemin trouve
```

Télécharge la voix française :
```bash
cd voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json
cd ..
```

**✅ Test JBL #3 — Synthèse vocale complète** :
```bash
source venv/bin/activate
python tts.py
```
Tu dois entendre la voix française dans le JBL.

---

## PARTIE 8 — Câbler et tester le capteur ultrason (si déjà fait, passe à la Partie 9)

Voir `GUIDE_COMPLET_CAPTEUR_ULTRASON.md` pour le schéma détaillé du pont
diviseur de tension (⚠️ obligatoire, sinon risque d'endommager le Pi).

**✅ Test** :
```bash
python sensor.py
```
Approche ta main, vérifie que la distance affichée diminue et que
"Personne detectee" passe à OUI en dessous de 80cm.

---

## PARTIE 9 — Personnaliser les infos de la faculté

```bash
nano config.py
```
Vérifie/complète la section `SYSTEM_PROMPT` avec les vraies infos à jour.
`Ctrl+O` puis Entrée pour sauvegarder, `Ctrl+X` pour quitter.

---

## PARTIE 10 — Vérification automatique complète

```bash
python check_setup.py
```
Corrige tout ce qui est signalé en échec avant de continuer.

---

## PARTIE 11 — Tester chaque brique individuellement

```bash
python stt.py               # micro JBL + transcription
python llm.py                 # IA au clavier (sans micro)
python avatar_visual.py       # avatar visuel (tes photos)
```

Pour `stt.py` : parle une phrase, attends ~1 seconde de silence, vérifie que
le texte affiché correspond à ce que tu as dit. Ajuste `SILENCE_THRESHOLD`
dans `stt.py` si besoin (micro Bluetooth souvent moins sensible qu'un micro USB).

---

## PARTIE 12 — TEST FINAL : le pipeline complet avec JBL

```bash
python main.py
```

**Déroulé attendu du test** :
1. L'avatar reste silencieux, écran au repos (état ATTENTE)
2. Approche-toi du capteur (< 80cm) → l'avatar dit "Bonjour !" dans le JBL,
   la bouche s'anime à l'écran
3. Pose une question à voix haute dans le micro JBL
4. L'avatar réfléchit (Ollama) puis répond à voix haute dans le JBL
5. Reste silencieux 15 secondes → l'avatar repasse en mode ATTENTE
6. Dis "au revoir" → l'avatar te salue et repasse en ATTENTE

**Si tout ça fonctionne, l'intégration complète est réussie.**

---

## PARTIE 13 — Démarrage automatique (mode kiosque) — optionnel mais recommandé pour l'événement

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
```bash
sudo systemctl daemon-reload
sudo systemctl enable avatar.service
sudo systemctl start avatar.service
journalctl -u avatar.service -f    # voir les logs en direct
```

⚠️ Le JBL doit déjà être appairé et connecté avant que ce service démarre.
Garde un lancement manuel (`python main.py`) en secours pour le jour J.

---

## Checklist finale avant l'événement

- [ ] `check_setup.py` passe sans erreur
- [ ] Les 3 tests JBL (haut-parleur, micro, synthèse vocale) fonctionnent
- [ ] Capteur ultrason testé et calibré (`DISTANCE_DETECTION_CM` ajusté)
- [ ] `config.py` avec les vraies infos à jour de la faculté
- [ ] Test complet (`main.py`) réussi de bout en bout, plusieurs fois de suite
- [ ] JBL chargé à 100%, appairé la veille
- [ ] Testé en continu plusieurs heures (pas de plantage/surchauffe)
- [ ] Plan B (lancement manuel) prêt si le démarrage automatique a un souci

---

## Problèmes fréquents — récapitulatif

| Problème | Solution |
|---|---|
| Le micro JBL ne capte rien | Vérifier le profil Bluetooth (HFP/`headset-head-unit`, pas juste A2DP) via `pactl list cards` |
| `piper: command not found` | Vérifier `PIPER_EXECUTABLE` dans `config.py` (sans `.exe` sur Pi) |
| Ollama très lent | Modèle plus léger (`llama3.2:1b`) |
| Capteur toujours à 0 / erratique | Revérifier le pont diviseur de tension sur ECHO |
| Erreur `PinFactoryFallback` | `export GPIOZERO_PIN_FACTORY=lgpio` (ajouter à `~/.bashrc`) |
| Le Bluetooth ne se reconnecte pas après reboot | Vérifier que `trust` a bien été fait, pas juste `pair` |
| L'avatar ne revient jamais en veille | Vérifier `TEMPS_INACTIVITE_FIN_CONVERSATION` dans `config.py` |
