#!/bin/bash
# connect_jbl.sh
# ---------------------------------------------------------
# Tente de reconnecter automatiquement le casque JBL au
# demarrage, avant de lancer le pipeline principal.
# ---------------------------------------------------------

# Remplace par l'adresse MAC exacte de TON casque JBL
ADRESSE_JBL="B8:17:43:0F:94:6B"

echo "Tentative de connexion au JBL ($ADRESSE_JBL)..."

# Laisse le temps au service bluetooth de bien demarrer
sleep 5

bluetoothctl connect "$ADRESSE_JBL"

# Petite pause pour laisser PipeWire detecter le nouveau peripherique
sleep 3

# Force le profil "mains-libres" (avec micro) plutot que musique seule
CARTE=$(pactl list cards short | grep bluez_card | awk '{print $2}')
if [ -n "$CARTE" ]; then
    pactl set-card-profile "$CARTE" headset-head-unit
    echo "Profil Bluetooth force en headset-head-unit sur $CARTE"
fi

echo "Etape Bluetooth terminee."
