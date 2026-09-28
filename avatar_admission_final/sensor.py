# sensor.py
# ---------------------------------------------------------
# Detection de presence via capteur ultrason HC-SR04.
# Utilise gpiozero, qui gere automatiquement le trig/echo.
# ---------------------------------------------------------

from gpiozero import DistanceSensor
from config import ULTRASON_TRIG_PIN, ULTRASON_ECHO_PIN, DISTANCE_DETECTION_CM

# max_distance en metres ; le HC-SR04 est fiable jusqu'a environ 4m
capteur = DistanceSensor(
    echo=ULTRASON_ECHO_PIN,
    trigger=ULTRASON_TRIG_PIN,
    max_distance=4.0,
    queue_len=5,  # lisse un peu les mesures pour eviter les faux positifs
)


def personne_detectee() -> bool:
    """Retourne True si un objet/personne est detecte sous le seuil configure."""
    distance_metres = capteur.distance
    distance_cm = distance_metres * 100
    return distance_cm < DISTANCE_DETECTION_CM


def distance_actuelle_cm() -> float:
    """Utile pour debug/calibration : renvoie la distance mesuree en cm."""
    return capteur.distance * 100


if __name__ == "__main__":
    # Test rapide : affiche la distance en continu, Ctrl+C pour arreter
    import time
    print("Test du capteur ultrason. Ctrl+C pour arreter.")
    try:
        while True:
            d = distance_actuelle_cm()
            detecte = "OUI" if personne_detectee() else "non"
            print(f"Distance : {d:.1f} cm | Personne detectee : {detecte}")
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\nArret du test.")
