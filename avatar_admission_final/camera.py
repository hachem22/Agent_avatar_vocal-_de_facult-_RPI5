# camera.py
# ---------------------------------------------------------
# Detection de presence via camera (webcam USB ou module
# camera officiel Raspberry Pi via picamera2).
#
# - La CAPTURE et la DETECTION tournent dans un thread en
#   arriere-plan (ne bloquent jamais la boucle principale).
# - L'AFFICHAGE de la fenetre de debug (cv2.imshow/waitKey) doit
#   se faire depuis le THREAD PRINCIPAL uniquement : le backend
#   graphique d'OpenCV (Qt) ne garantit pas un affichage correct
#   si imshow() est appele depuis un thread secondaire. C'est
#   pour ca que la classe separe bien "detecter" (thread) et
#   "afficher" (methode a appeler depuis le programme principal).
# ---------------------------------------------------------

import os
import threading
import time

# IMPORTANT : sur Raspberry Pi OS recent (bureau Wayland/labwc), le backend
# graphique Qt d'OpenCV peut planter ou mal afficher ses fenetres sous
# Wayland natif. On force donc XWayland (couche de compatibilite X11),
# beaucoup plus fiable pour cv2.imshow(). Doit etre fait AVANT le "import
# cv2" pour avoir un effet.
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

import cv2

from config import (
    CAMERA_TYPE,
    CAMERA_INDEX,
    CAMERA_RESOLUTION,
    CAMERA_MIN_FACE_SIZE,
    CAMERA_FRAMES_SANS_VISAGE_AVANT_DEPART,
    CAMERA_SHOW_WINDOW,
    CAMERA_WINDOW_NAME,
)

# Classifieur Haar fourni avec OpenCV (aucun telechargement necessaire)
# NB : necessite opencv-python < 5 (voir requirements.txt), car OpenCV 5.0
# a deplace CascadeClassifier vers opencv_contrib.
_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


class CameraDetector:
    """Gere l'ouverture de la camera et la detection de visage en continu
    dans un thread d'arriere-plan. L'affichage de la fenetre de debug se
    fait via update_window(), a appeler depuis le thread principal."""

    def __init__(self):
        self._cap = None
        self._picam2 = None
        self._type = CAMERA_TYPE

        if self._type == "picamera2":
            self._init_picamera2()
        else:
            self._init_usb()

        if CAMERA_SHOW_WINDOW:
            self._creer_fenetre()
            self._fenetre_creee = True
        else:
            self._fenetre_creee = False

        self._detectee = False
        self._compteur_frames_sans_visage = 0
        self._lock = threading.Lock()
        self._frame_a_afficher = None   # prete pour cv2.imshow (thread principal)

        self._running = True
        self._thread = threading.Thread(target=self._boucle, daemon=True)
        self._thread.start()

    # -----------------------------------------------------------
    # Initialisation des deux types de camera possibles
    # -----------------------------------------------------------
    def _init_usb(self):
        self._cap = cv2.VideoCapture(CAMERA_INDEX)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_RESOLUTION[0])
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_RESOLUTION[1])
        if not self._cap.isOpened():
            raise RuntimeError(
                f"Impossible d'ouvrir la camera USB (index={CAMERA_INDEX}). "
                "Verifie qu'elle est bien branchee et visible avec 'ls /dev/video*'."
            )

    def _init_picamera2(self):
        try:
            from picamera2 import Picamera2
        except ImportError as e:
            raise RuntimeError(
                "picamera2 n'est pas installe. Sur Raspberry Pi OS, installe-le avec : "
                "sudo apt install -y python3-picamera2 "
                "(et cree ton venv avec --system-site-packages pour qu'il soit visible)."
            ) from e

        self._picam2 = Picamera2()
        config_cam = self._picam2.create_video_configuration(
            main={"size": CAMERA_RESOLUTION, "format": "RGB888"}
        )
        self._picam2.configure(config_cam)
        self._picam2.start()
        time.sleep(1)  # laisse le temps au capteur de s'initialiser

    def _creer_fenetre(self):
        """Cree la fenetre de debug explicitement, la place a un endroit
        fixe et visible (coin superieur gauche) et force son affichage au
        premier plan. Evite qu'elle s'ouvre "cachee" derriere une autre
        fenetre (terminal en plein ecran, par exemple)."""
        cv2.namedWindow(CAMERA_WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(CAMERA_WINDOW_NAME, CAMERA_RESOLUTION[0], CAMERA_RESOLUTION[1])
        cv2.moveWindow(CAMERA_WINDOW_NAME, 30, 30)
        try:
            # Force la fenetre au premier plan un court instant, le temps
            # qu'elle soit bien visible, puis on la laisse redevenir normale
            cv2.setWindowProperty(CAMERA_WINDOW_NAME, cv2.WND_PROP_TOPMOST, 1)
        except cv2.error:
            # Pas supporte par tous les backends : pas grave, la fenetre
            # reste quand meme creee et positionnee.
            pass

    def _lire_frame(self):
        if self._type == "picamera2":
            frame = self._picam2.capture_array()
            # picamera2 renvoie du RGB, OpenCV travaille en BGR
            return True, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        else:
            return self._cap.read()

    # -----------------------------------------------------------
    # Boucle de capture + detection (tourne dans son propre thread)
    # AUCUN appel cv2.imshow/waitKey/destroyWindow ici.
    # -----------------------------------------------------------
    def _boucle(self):
        while self._running:
            ok, frame = self._lire_frame()
            if not ok or frame is None:
                time.sleep(0.1)
                continue

            gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            visages = _face_cascade.detectMultiScale(
                gris,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=CAMERA_MIN_FACE_SIZE,
            )

            if len(visages) > 0:
                self._compteur_frames_sans_visage = 0
                nouvelle_detection = True
            else:
                self._compteur_frames_sans_visage += 1
                nouvelle_detection = (
                    self._compteur_frames_sans_visage
                    < CAMERA_FRAMES_SANS_VISAGE_AVANT_DEPART
                )

            if CAMERA_SHOW_WINDOW:
                frame_annotee = self._preparer_annotations(frame, visages, nouvelle_detection)
            else:
                frame_annotee = None

            with self._lock:
                self._detectee = nouvelle_detection
                self._frame_a_afficher = frame_annotee

            if not CAMERA_SHOW_WINDOW:
                time.sleep(0.03)  # laisse respirer le CPU

    def _preparer_annotations(self, frame, visages, detectee):
        """Dessine les rectangles/texte sur une copie de l'image.
        Ne fait AUCUN appel graphique (juste du dessin sur les pixels)."""
        frame = frame.copy()
        for (x, y, w, h) in visages:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 200, 0), 2)

        texte = "Personne detectee : OUI" if detectee else "Personne detectee : NON"
        couleur = (0, 200, 0) if detectee else (0, 0, 220)
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (30, 30, 30), -1)
        cv2.putText(
            frame, texte, (10, 27),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, couleur, 2,
        )
        return frame

    # -----------------------------------------------------------
    # API publique
    # -----------------------------------------------------------
    def personne_detectee(self) -> bool:
        with self._lock:
            return self._detectee

    def update_window(self):
        """A APPELER UNIQUEMENT DEPUIS LE THREAD PRINCIPAL, en boucle
        (ex: dans avatar.idle_tick() ou une boucle equivalente), pour
        afficher/rafraichir la fenetre de debug. Ne fait rien si
        CAMERA_SHOW_WINDOW = False."""
        if not CAMERA_SHOW_WINDOW:
            return
        with self._lock:
            frame = self._frame_a_afficher
        if frame is not None:
            cv2.imshow(CAMERA_WINDOW_NAME, frame)
            self._fenetre_creee = True
        # waitKey est indispensable pour que la fenetre se rafraichisse
        # et reste responsive (meme sans image encore prete)
        cv2.waitKey(1)

    def close(self):
        self._running = False
        self._thread.join(timeout=2)
        if self._cap is not None:
            self._cap.release()
        if self._picam2 is not None:
            self._picam2.stop()
            self._picam2.close()  # liberation complete du peripherique (evite
                                   # de bloquer la camera pour le prochain lancement)
        if CAMERA_SHOW_WINDOW and self._fenetre_creee:
            cv2.destroyWindow(CAMERA_WINDOW_NAME)
            cv2.waitKey(1)


# -----------------------------------------------------------
# Instance unique partagee (creee au premier appel)
# -----------------------------------------------------------
_instance = None


def _get_instance() -> CameraDetector:
    global _instance
    if _instance is None:
        _instance = CameraDetector()
    return _instance


def personne_detectee() -> bool:
    """Meme interface que sensor.personne_detectee() pour etre interchangeable."""
    return _get_instance().personne_detectee()


def update_window():
    """A appeler depuis le thread principal pour rafraichir la fenetre
    de debug camera (voir CameraDetector.update_window)."""
    if _instance is not None:
        _instance.update_window()


def close():
    global _instance
    if _instance is not None:
        _instance.close()
        _instance = None


if __name__ == "__main__":
    # Test rapide, execute entierement dans le thread principal :
    # ouvre la fenetre de debug et affiche OUI/NON en continu.
    # Ctrl+C dans le terminal pour arreter.
    print("Test de la camera. Ctrl+C dans le terminal pour arreter.")
    detecteur = _get_instance()
    dernier_affichage_texte = 0
    try:
        while True:
            detecteur.update_window()  # doit tourner dans le thread principal
            maintenant = time.time()
            if maintenant - dernier_affichage_texte > 0.5:
                print("Personne detectee :", "OUI" if detecteur.personne_detectee() else "non")
                dernier_affichage_texte = maintenant
            time.sleep(0.03)
    except KeyboardInterrupt:
        pass
    finally:
        close()
