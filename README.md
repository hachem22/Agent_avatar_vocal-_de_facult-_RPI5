# Avatar d'Admission ESPRIT — Projet complet (PC + Raspberry Pi 5)

Agent vocal 100% local (aucune API cloud) : un visiteur parle, l'IA (Ollama)
répond en se basant sur les infos d'ESPRIT, la réponse est lue à voix haute
(Piper) et un avatar vidéo anime l'écran pendant qu'il parle. Sur le Pi, une
caméra (et/ou un capteur ultrason) détecte automatiquement la présence d'un
visiteur, et tout démarre seul dès que le Pi est alimenté.

**⚠️ Lis `CORRECTIONS_CAMERA_AUTOSTART_BLUETOOTH.md` en premier** : il résume
les 3 corrections apportées à cette version (détection caméra, démarrage
automatique, Bluetooth automatique) et comment tester ces changements.

---

## Structure du projet

| Fichier | Rôle |
|---|---|
| `main.py` | Chef d'orchestre : machine à états ATTENTE → ÉCOUTE → RÉFLEXION → PAROLE |
| `config.py` | Toutes les infos ESPRIT + réglages (modèles, GPIO, capteur, caméra, vidéos) |
| `stt.py` | Reconnaissance vocale (faster-whisper) |
| `llm.py` | Interrogation du modèle IA local (Ollama) |
| `tts.py` | Synthèse vocale (Piper) |
| `avatar_visual.py` | Affichage vidéo de l'avatar (3 clips : accueil/parole/au revoir) |
| `presence.py` | Point d'entrée unique de détection (redirige vers caméra et/ou ultrason selon `config.py`) |
| `camera.py` | **Nouveau** — détection de présence par caméra (visage) + fenêtre de debug en direct |
| `sensor.py` | Détection de présence par capteur ultrason HC-SR04 (Pi uniquement) |
| `check_setup.py` | Vérifie que toute l'installation est correcte (y compris la caméra) |
| `connect_jbl.sh` | Connexion Bluetooth du casque JBL (appelé automatiquement par `start_avatar.sh`) |
| `start_avatar.sh` | **Nouveau** — script de démarrage tout-en-un : Bluetooth puis `main.py` |
| `autostart/avatar.desktop` | **Nouveau** — entrée d'autostart du bureau Pi OS (lance `start_avatar.sh` au boot) |
| `requirements.txt` | Dépendances Python |
| `assets/` | Place ici tes 3 vidéos : `welcome.mp4`, `talking.mp4`, `goodbye.mp4` |
| `voices/` | Modèle de voix Piper (`.onnx` + `.onnx.json`) |

---

## Deux façons d'utiliser ce projet

### 1. Sur PC (développement/test)
Guide détaillé : `INSTALLATION_PC_WINDOWS.md`
- Sert à développer et tester rapidement, sans dépendre du matériel du Pi
- Par défaut `DETECTION_MODE = "camera"` dans `config.py` : ça fonctionne
  aussi sur PC avec ta webcam intégrée/USB, pas besoin de GPIO
- Le capteur ultrason (`sensor.py`) ne fonctionne PAS sur PC (pas de GPIO) —
  reste sur `DETECTION_MODE = "camera"` pour tester sur PC

### 2. Sur Raspberry Pi 5 (déploiement final)
Guides détaillés : `CORRECTIONS_CAMERA_AUTOSTART_BLUETOOTH.md` (nouveautés) +
`INSTALLATION_RASPBERRY_PI.md` (installation complète, parties 10 et 11 mises
à jour) et `GUIDE_COMPLET_CAPTEUR_ULTRASON.md` (câblage du capteur, si utilisé)
- C'est la cible finale : caméra et/ou capteur + JBL + démarrage 100% automatique
- ⚠️ `GUIDE_MAITRE_INTEGRATION_COMPLETE.md` et `INTEGRATION_RASPBERRY_PI5.md`
  mentionnent encore l'ancienne méthode `avatar.service` (systemd) pour le
  démarrage automatique — **ne l'utilise plus**, elle ne donne pas accès à
  l'affichage graphique. Utilise `start_avatar.sh` + `autostart/avatar.desktop`
  comme décrit dans `INSTALLATION_RASPBERRY_PI.md` (partie 10)

---

## Ordre de lecture recommandé des guides

1. `CORRECTIONS_CAMERA_AUTOSTART_BLUETOOTH.md` — ce qui a changé dans cette version
2. `INSTALLATION_PC_WINDOWS.md` — pour tester d'abord sur PC
3. `INSTALLATION_RASPBERRY_PI.md` — installation complète sur le Pi (parties 10-11 à jour)
4. `GUIDE_COMPLET_CAPTEUR_ULTRASON.md` — câblage détaillé du capteur ultrason (si utilisé)
5. `GUIDE_MAITRE_INTEGRATION_COMPLETE.md` / `INTEGRATION_RASPBERRY_PI5.md` — références
   complémentaires (ignorer la partie `avatar.service`, remplacée)

---

## Avant l'événement — checklist rapide

- [ ] `python check_setup.py` passe sans erreur sur le Pi
- [ ] Les 3 vidéos sont dans `assets/` (welcome.mp4, talking.mp4, goodbye.mp4)
- [ ] `config.py` à jour avec les vraies infos ESPRIT
- [ ] `DETECTION_MODE` choisi et testé (`camera`, `ultrason` ou `les_deux`)
- [ ] `connect_jbl.sh` contient la bonne adresse MAC du JBL
- [ ] Autologin bureau activé + `avatar.desktop` copié dans `~/.config/autostart/`
- [ ] Testé avec une VRAIE coupure/remise de courant (pas juste `reboot`)
- [ ] JBL chargé à 100%
