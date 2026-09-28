# presence.py
# ---------------------------------------------------------
# Point d'entree UNIQUE pour la detection de presence, utilise
# par main.py. Selon DETECTION_MODE dans config.py, redirige vers :
#   - sensor.py  (capteur ultrason HC-SR04)
#   - camera.py  (detection de visage par camera + fenetre de debug)
#   - les deux a la fois (OU logique : une seule detection suffit)
# ---------------------------------------------------------

from config import DETECTION_MODE

_MODES_VALIDES = ("ultrason", "camera", "les_deux")
if DETECTION_MODE not in _MODES_VALIDES:
    raise ValueError(
        f"DETECTION_MODE={DETECTION_MODE!r} invalide dans config.py. "
        f"Valeurs acceptees : {_MODES_VALIDES}"
    )

if DETECTION_MODE in ("ultrason", "les_deux"):
    from sensor import personne_detectee as _ultrason_detectee
else:
    _ultrason_detectee = None

if DETECTION_MODE in ("camera", "les_deux"):
    from camera import personne_detectee as _camera_detectee
    from camera import close as _camera_close
    from camera import update_window as _camera_update_window
else:
    _camera_detectee = None
    _camera_close = None
    _camera_update_window = None


def personne_detectee() -> bool:
    if DETECTION_MODE == "ultrason":
        return _ultrason_detectee()
    if DETECTION_MODE == "camera":
        return _camera_detectee()
    # "les_deux" : une seule des deux detections suffit
    return _ultrason_detectee() or _camera_detectee()


def update_window():
    """A appeler depuis le thread principal (main.py) pour rafraichir la
    fenetre de debug camera, si DETECTION_MODE l'utilise. Ne fait rien
    en mode 'ultrason' seul."""
    if _camera_update_window is not None:
        _camera_update_window()


def close():
    """A appeler a l'arret du programme pour bien liberer la camera."""
    if _camera_close is not None:
        _camera_close()


if __name__ == "__main__":
    import time
    print(f"Mode de detection actif : {DETECTION_MODE}")
    try:
        while True:
            update_window()  # doit tourner dans le thread principal
            print("Personne detectee :", "OUI" if personne_detectee() else "non")
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        close()
