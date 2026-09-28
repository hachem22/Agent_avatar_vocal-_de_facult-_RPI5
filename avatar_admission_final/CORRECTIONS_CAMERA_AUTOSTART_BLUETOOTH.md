# Corrections apportées à ce projet

Ce document résume les 3 corrections demandées et comment tester le projet
corrigé sur ton Raspberry Pi 5.

---

## 1. Détection de présence par caméra (au lieu de / en plus de l'ultrason)

**Nouveaux fichiers :**
- `camera.py` — ouvre la caméra (webcam USB ou module officiel Pi CSI),
  détecte les visages en continu dans un thread séparé, et affiche une
  **fenêtre de debug en direct** avec le flux vidéo, un rectangle vert autour
  de chaque visage détecté, et le texte **"Personne détectée : OUI / NON"**
  en haut de l'image.
- `presence.py` — point d'entrée unique utilisé par `main.py`. Choisit
  automatiquement entre caméra, ultrason, ou les deux, selon
  `DETECTION_MODE` dans `config.py`.

**Fichiers modifiés :**
- `main.py` — utilise maintenant `presence.py` au lieu d'appeler directement
  `sensor.py`, et libère proprement la caméra à la fermeture.
- `config.py` — nouveaux réglages : `DETECTION_MODE`, `CAMERA_TYPE`,
  `CAMERA_INDEX`, `CAMERA_RESOLUTION`, `CAMERA_MIN_FACE_SIZE`,
  `CAMERA_SHOW_WINDOW`, etc.
- `requirements.txt` — `opencv-python-headless` remplacé par
  `opencv-python` (la version "headless" ne peut PAS afficher de fenêtre,
  ce qui aurait empêché la fenêtre de debug de s'ouvrir).

⚠️ **Piège découvert en testant sur le vrai Pi** : `pip install opencv-python`
installe par défaut la version **5.x**, qui a **retiré `CascadeClassifier`**
du paquet principal (déplacé vers `opencv_contrib`, non inclus). Résultat :
`AttributeError: module 'cv2' has no attribute 'CascadeClassifier'` même
avec une installation propre. `requirements.txt` épingle donc maintenant
`opencv-python>=4.9.0,<5`. Si tu vois cette erreur, corrige avec :
```bash
pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python opencv-contrib-python-headless
pip install "opencv-python<5"
```

⚠️ **Deuxième piège découvert en testant** : sur Raspberry Pi OS récent
(bureau **Wayland**/`labwc`), la fenêtre de debug de `cv2.imshow()` peut
planter à la fermeture, ou s'ouvrir **cachée derrière d'autres fenêtres**
sans jamais passer au premier plan. `camera.py` force maintenant
automatiquement `QT_QPA_PLATFORM=xcb` (bascule vers XWayland, la couche de
compatibilité X11, beaucoup plus fiable pour OpenCV) directement dans le
code — pas besoin de le définir toi-même à chaque lancement. La fenêtre est
aussi maintenant créée explicitement à une position fixe (coin supérieur
gauche de l'écran) et forcée au premier plan à l'ouverture, pour ne plus
jamais rester invisible derrière un terminal en plein écran.

**Pour l'utiliser :** dans `config.py`, mets `DETECTION_MODE = "camera"`
(déjà fait par défaut). Voir `INSTALLATION_RASPBERRY_PI.md`, partie 11,
pour le câblage/branchement caméra USB ou module CSI.

---

## 2. Bluetooth connecté automatiquement

Le script `connect_jbl.sh` existait déjà mais n'était **appelé par rien** —
il fallait le lancer à la main. Ce n'est plus le cas :

- `start_avatar.sh` (nouveau) appelle maintenant `connect_jbl.sh`
  **automatiquement**, avec 3 tentatives en cas d'échec (utile si le
  Bluetooth du Pi met quelques secondes à être prêt au démarrage).

---

## 3. Lancement automatique dès que le Pi est alimenté

**Nouveaux fichiers :**
- `start_avatar.sh` — script tout-en-un : attend que le système soit prêt,
  connecte le Bluetooth, puis lance `main.py`. Écrit tout dans
  `avatar_boot.log` pour pouvoir déboguer facilement.
- `autostart/avatar.desktop` — fichier à copier dans
  `~/.config/autostart/` sur le Pi, qui fait lancer `start_avatar.sh`
  automatiquement dès l'ouverture du bureau.

**Pourquoi pas un service systemd (`avatar.service`) ?** Les anciens guides
(`GUIDE_MAITRE_INTEGRATION_COMPLETE.md`, `INTEGRATION_RASPBERRY_PI5.md`)
proposaient un service systemd. Le problème : ce projet ouvre des **fenêtres
graphiques** (avatar + fenêtre caméra), et un service systemd classique n'a
pas accès à l'affichage graphique de la session bureau. Résultat : les
fenêtres ne se seraient jamais affichées, même si le programme tournait "en
arrière-plan". La solution fiable pour une appli graphique qui doit démarrer
seule est l'**autostart du bureau**, combinée à l'**autologin** (connexion
automatique sans mot de passe), ce qui donne bien le comportement "je
branche l'alimentation → tout démarre tout seul, sans rien taper".

**Pour l'activer**, voir `INSTALLATION_RASPBERRY_PI.md`, partie 10
(3 étapes : adapter le chemin, activer l'autologin, copier le fichier
autostart).

---

## Comment envoyer le projet corrigé vers le Raspberry Pi

### Option A — via `scp` (le plus simple, depuis ton PC)

Assure-toi que le Pi et ton PC sont sur le **même réseau**, et récupère
l'IP du Pi (sur le Pi : `hostname -I`).

Depuis ton PC, dans le dossier qui contient `avatar_admission_final/` :

**Windows (PowerShell) :**
```powershell
scp -r avatar_admission_final pi@<IP_DU_PI>:/home/pi/
```

**Mac/Linux :**
```bash
scp -r avatar_admission_final pi@<IP_DU_PI>:/home/pi/
```

Remplace `pi` par ton nom d'utilisateur réel sur le Pi si différent, et
`<IP_DU_PI>` par l'adresse trouvée avec `hostname -I`.

⚠️ Si un dossier `avatar_admission_final` existe déjà sur le Pi (ancienne
version), supprime-le d'abord sur le Pi pour éviter de mélanger anciens et
nouveaux fichiers :
```bash
# Sur le Pi, en SSH
rm -rf /home/pi/avatar_admission_final
```
Puis relance la commande `scp` depuis ton PC.

### Option B — via `rsync` (plus rapide pour les mises à jour suivantes)

Ne retransfère que ce qui a changé, pratique une fois que le gros du projet
(vidéos, modèle de voix) est déjà sur le Pi :
```bash
rsync -avz --progress avatar_admission_final/ pi@<IP_DU_PI>:/home/pi/avatar_admission_final/
```

### Option C — via clé USB
Copie le dossier `avatar_admission_final` sur une clé USB, branche-la sur le
Pi, puis copie-la sur le bureau ou dans `/home/pi/`.

---

## Tester le projet corrigé sur le Pi, étape par étape

Connecte-toi en SSH au Pi (ou directement dessus) :

```bash
cd /home/pi/avatar_admission_final

# 1. (Re)créer l'environnement virtuel avec les nouvelles dépendances
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 2. Vérifier que tout est en place (inclut maintenant un check caméra)
python check_setup.py

# 3. Tester la caméra seule, avec sa fenêtre de debug
python camera.py
# → une fenêtre doit s'ouvrir, mets-toi devant : "Personne détectée : OUI"

# 4. Tester le Bluetooth seul
bash connect_jbl.sh

# 5. Tester le pipeline complet manuellement (avatar + caméra ensemble)
python main.py
# → 2 fenêtres doivent s'ouvrir : l'avatar ET le flux caméra de debug

# 6. Une fois que tout fonctionne, activer le démarrage automatique
#    (voir INSTALLATION_RASPBERRY_PI.md partie 10), puis tester avec un
#    vrai redémarrage :
sudo reboot
```

Après le redémarrage, attends ~20-30 secondes (le script attend que le
système soit prêt) : le casque doit se connecter seul, puis les 2 fenêtres
doivent s'ouvrir automatiquement, sans que tu aies rien tapé.

Si quelque chose ne se lance pas automatiquement, consulte le log :
```bash
cat /home/pi/avatar_admission_final/avatar_boot.log
```
