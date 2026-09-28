# Avatar d'Admission — Guide complet avec détection de présence (HC-SR04)

Ce guide part de zéro et intègre TOUT : Raspberry Pi 5, casque JBL Bluetooth,
capteur ultrason HC-SR04 pour détecter automatiquement les visiteurs, et le
pipeline vocal complet avec la machine à états **Attente → Écoute → Réflexion → Parole**.

---

## PARTIE 0 — Vue d'ensemble de la machine à états

```
                    ┌─────────────────────────┐
                    │        ATTENTE           │
                    │  (capteur ultrason actif)│
                    └────────────┬─────────────┘
                                 │ personne detectee
                                 ▼
                    ┌─────────────────────────┐
              ┌────►│  PAROLE : "Bonjour !"    │
              │     └────────────┬─────────────┘
              │                  ▼
              │     ┌─────────────────────────┐
              │     │   ECOUTE (micro JBL)     │◄──────┐
              │     └────────────┬─────────────┘       │
              │                  │ question captee      │
              │                  ▼                      │
              │     ┌─────────────────────────┐         │
              │     │  REFLEXION (Ollama LLM)  │         │
              │     └────────────┬─────────────┘         │
              │                  ▼                       │
              │     ┌─────────────────────────┐          │
              └─────┤   PAROLE (reponse)       ├──────────┘
   silence 15s       └─────────────────────────┘
   -> retour ATTENTE
```

**Point important** : tant qu'on est en conversation, le capteur est ignoré
(on ne relance pas "Bonjour" en boucle sur la même personne). On ne revient
en mode Attente qu'après un silence prolongé ou un mot d'arrêt ("au revoir").

---

## PARTIE 1 — Matériel nécessaire

- Raspberry Pi 5 (8GB) + carte SD 128GB + alimentation officielle 27W
- Écran HDMI + dissipateur/ventilateur
- Casque JBL Bluetooth
- **Capteur ultrason HC-SR04**
- **1 résistance de 1kΩ + 1 résistance de 2kΩ** (pont diviseur de tension, obligatoire)
- Breadboard + fils de connexion (jumper wires)

---

## PARTIE 2 — Câblage du capteur HC-SR04 (ÉTAPE CRITIQUE)

⚠️ **Le HC-SR04 envoie du 5V sur sa broche ECHO, mais les GPIO du Pi ne
supportent que 3.3V. Sans le pont diviseur de tension ci-dessous, tu risques
d'endommager définitivement ton Raspberry Pi.**

### Connexions :

| Broche HC-SR04 | Vers |
|---|---|
| VCC | Pin 2 du Pi (5V) |
| GND | Pin 6 du Pi (GND) |
| TRIG | Pin 16 du Pi (GPIO23) — direct, pas besoin de diviseur |
| ECHO | **Via le pont diviseur** (voir ci-dessous) vers Pin 18 du Pi (GPIO24) |

### Pont diviseur de tension pour ECHO (obligatoire) :

```
HC-SR04 ECHO ──────┬──── Resistance 1kΩ ────┬──── GPIO24 (Pin 18) du Pi
                    │                         │
                 (rien ici)              Resistance 2kΩ
                                               │
                                              GND
```

Concrètement sur une breadboard :
1. Relie la broche ECHO du capteur à une extrémité de la résistance 1kΩ
2. Relie l'autre extrémité de la résistance 1kΩ à un point de la breadboard
3. Depuis ce même point, relie une résistance 2kΩ vers le GND (masse)
4. Depuis ce même point également, tire un fil vers le GPIO24 (Pin 18) du Pi

Ce montage divise le 5V en sortie d'ECHO pour n'envoyer qu'environ 3.3V au GPIO.

---

## PARTIE 3 — Installer l'OS et les dépendances de base

(Identique aux guides précédents — voir `INTEGRATION_RASPBERRY_PI5.md` pour
le détail complet des parties 1 à 9 : flash de l'OS, Bluetooth JBL, Ollama,
transfert du projet, venv Python, Piper.)

Ajoute en plus les paquets pour le GPIO :
```bash
sudo apt install -y python3-gpiozero python3-lgpio
pip install gpiozero
```

Sur Raspberry Pi 5, le chip GPIO a changé (RP1) — `gpiozero` doit utiliser le
backend `lgpio` (installé ci-dessus). Si tu as une erreur de "pin factory" au
lancement, force le backend :
```bash
export GPIOZERO_PIN_FACTORY=lgpio
```
(ajoute cette ligne à ton `~/.bashrc` pour que ce soit permanent)

---

## PARTIE 4 — Tester le capteur seul

```bash
cd /home/pi/avatar_admission
source venv/bin/activate
python sensor.py
```
Tu dois voir la distance mesurée s'afficher en continu. Approche ta main et
vérifie que "Personne detectee" passe à OUI en dessous de 80cm (réglable dans
`config.py` via `DISTANCE_DETECTION_CM`).

⚠️ Si les mesures sont erratiques ou toujours à 0 : revérifie le câblage,
en particulier le pont diviseur sur ECHO.

---

## PARTIE 5 — Personnaliser les infos de ta faculté

Ouvre `config.py`, section `SYSTEM_PROMPT`. Remplace le contenu par toutes
les informations utiles sur TA faculté : programmes, admission, frais,
contacts, etc. (voir l'exemple déjà rempli pour ESPRIT dans le fichier — tu
peux garder cette structure et remplacer le contenu).

**Astuce pour rassembler l'info rapidement** : récupère le contenu des pages
"Admissions", "Programmes", "Frais de scolarité" et "Contact" du site web de
ta faculté, et colle-les de façon organisée dans `SYSTEM_PROMPT`. Plus c'est
structuré et précis, meilleures seront les réponses.

Si tu as énormément de contenu (plus de 2-3 pages), dis-le-moi : on peut
mettre en place un système de recherche qui ne charge que les infos
pertinentes à chaque question plutôt que tout injecter d'un coup.

---

## PARTIE 6 — Lancer le pipeline complet avec détection de présence

```bash
python main.py
```

Comportement attendu :
1. L'avatar reste au repos, silencieux, écran affichant le visage neutre
2. Tu t'approches à moins de 80cm du capteur → l'avatar dit "Bonjour !"
   et commence à écouter
3. Tu poses une question → il répond
4. S'il n'y a plus de question pendant 15 secondes → il repasse en mode
   attente automatiquement (le capteur redevient actif)
5. Si tu dis "au revoir" → il te salue et repasse en mode attente

---

## PARTIE 7 — Ajuster les réglages

Dans `config.py` :

| Réglage | Effet |
|---|---|
| `DISTANCE_DETECTION_CM` | Distance de déclenchement (par défaut 80cm). Réduis si le capteur se déclenche trop souvent avec du passage lointain |
| `TEMPS_INACTIVITE_FIN_CONVERSATION` | Secondes de silence avant retour en veille (par défaut 15s) |
| `ULTRASON_TRIG_PIN` / `ULTRASON_ECHO_PIN` | Numéros GPIO utilisés (change si tu câbles sur d'autres broches) |

---

## PARTIE 8 — Placer physiquement le capteur

Pour un stand d'admission, positionne le HC-SR04 :
- À hauteur de poitrine/visage (environ 1m20-1m40 du sol), orienté vers l'endroit
  où les visiteurs s'arrêteraient naturellement devant l'écran
- Évite de le pointer vers une zone de passage général (couloir), sinon
  l'avatar va se déclencher pour des gens qui ne font que passer
- Teste plusieurs fois en conditions réelles avant l'événement pour ajuster
  `DISTANCE_DETECTION_CM`

---

## Problèmes fréquents

| Problème | Solution |
|---|---|
| Le capteur ne détecte rien / valeurs à 0 | Revérifier le câblage, en particulier le pont diviseur sur ECHO |
| Erreur `PinFactoryFallback` au lancement | Installer `python3-lgpio` et définir `GPIOZERO_PIN_FACTORY=lgpio` |
| L'avatar se déclenche sans arrêt | Réduire `DISTANCE_DETECTION_CM`, ou repositionner/réorienter le capteur |
| L'avatar ne revient jamais en veille | Vérifier `TEMPS_INACTIVITE_FIN_CONVERSATION`, et que `listen_and_transcribe()` ne bloque pas indéfiniment |
| Le Pi a été endommagé après branchement du capteur | Le pont diviseur était probablement absent/mal câblé — vérifier avec un multimètre que le GPIO24 ne reçoit jamais plus de 3.3V avant de rebrancher |
