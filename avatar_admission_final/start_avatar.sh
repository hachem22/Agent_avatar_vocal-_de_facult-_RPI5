#!/bin/bash
# start_avatar.sh
# ---------------------------------------------------------
# Script de demarrage AUTOMATIQUE complet, a lancer au boot :
#   1. Attend que le bureau / reseau / bluetooth soient prets
#   2. Connecte automatiquement le casque JBL (avec plusieurs
#      tentatives, au cas ou le Bluetooth ne soit pas encore pret)
#   3. Lance le pipeline principal (main.py), qui ouvrira la
#      fenetre avatar ET la fenetre de debug camera
#
# Ce script est concu pour etre appele automatiquement au
# demarrage via une entree d'autostart du bureau (voir le
# guide INSTALLATION_RASPBERRY_PI.md, partie "Lancement auto").
# ---------------------------------------------------------

# --- A ADAPTER si ton dossier projet a un autre chemin/nom ---
PROJET_DIR="/home/pi/avatar_admission_final"
LOG_FILE="$PROJET_DIR/avatar_boot.log"

cd "$PROJET_DIR" || { echo "Dossier projet introuvable : $PROJET_DIR"; exit 1; }

{
    echo "=========================================="
    echo "Demarrage avatar : $(date)"
    echo "=========================================="

    # Laisse le temps au bureau, au reseau et au service bluetooth
    # de bien demarrer avant de tenter quoi que ce soit
    echo "Attente du demarrage du systeme (15s)..."
    sleep 15

    # --- Connexion Bluetooth du casque JBL, avec plusieurs tentatives ---
    CONNECTE=0
    for i in 1 2 3; do
        echo "Tentative de connexion Bluetooth ($i/3)..."
        if bash connect_jbl.sh; then
            CONNECTE=1
            break
        fi
        echo "Echec, nouvelle tentative dans 5s..."
        sleep 5
    done

    if [ "$CONNECTE" -eq 0 ]; then
        echo "ATTENTION : le casque JBL n'a pas pu etre connecte automatiquement."
        echo "Le pipeline va quand meme demarrer (utilisera la sortie audio par defaut)."
    fi

    # --- Lancement du pipeline principal ---
    echo "Activation de l'environnement virtuel..."
    source venv/bin/activate

    echo "Lancement de main.py..."
    python main.py

    echo "main.py s'est arrete : $(date)"

} >> "$LOG_FILE" 2>&1
