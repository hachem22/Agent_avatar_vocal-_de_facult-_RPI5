# avatar_visual.py
# ---------------------------------------------------------
# Avatar visuel base sur 3 VIDEOS courtes :
#   - AVATAR_VIDEO_WELCOME  : jouee au moment du "Bonjour"
#   - AVATAR_VIDEO_TALKING  : bouclee pendant que l'avatar repond
#   - AVATAR_VIDEO_GOODBYE  : jouee au moment de "au revoir"
#
# Les videos sont decodees avec OpenCV et affichees dans une
# fenetre Pygame, synchronisees avec l'audio genere par Piper.
# ---------------------------------------------------------

import os
import time
import threading

import cv2
import numpy as np
import pygame
import sounddevice as sd

from tts import SAMPLE_RATE

try:
    from config import (
        AVATAR_VIDEO_WELCOME,
        AVATAR_VIDEO_TALKING,
        AVATAR_VIDEO_GOODBYE,
        AVATAR_WINDOW_SIZE,
    )
except ImportError:
    AVATAR_VIDEO_WELCOME = None
    AVATAR_VIDEO_TALKING = None
    AVATAR_VIDEO_GOODBYE = None
    AVATAR_WINDOW_SIZE = (500, 500)

BG_COLOR = (20, 20, 30)


class Avatar:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(AVATAR_WINDOW_SIZE)
        pygame.display.set_caption("Avatar - Admission")
        self.clock = pygame.time.Clock()
        self.running = True

        self._videos_disponibles = all([
            AVATAR_VIDEO_WELCOME and os.path.exists(AVATAR_VIDEO_WELCOME),
            AVATAR_VIDEO_TALKING and os.path.exists(AVATAR_VIDEO_TALKING),
            AVATAR_VIDEO_GOODBYE and os.path.exists(AVATAR_VIDEO_GOODBYE),
        ])
        if not self._videos_disponibles:
            print("ATTENTION : une ou plusieurs videos introuvables, "
                  "l'avatar affichera un fond uni a la place.")

        # Derniere image affichee, gardee figee pendant les silences/veille
        self._derniere_image = None

    # -----------------------------------------------------------
    # Utilitaires internes
    # -----------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def _frame_vers_surface(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, AVATAR_WINDOW_SIZE)
        frame = np.transpose(frame, (1, 0, 2))
        return pygame.surfarray.make_surface(frame)

    def _afficher(self, surface=None):
        if surface is not None:
            self.screen.blit(surface, (0, 0))
        elif self._derniere_image is not None:
            self.screen.blit(self._derniere_image, (0, 0))
        else:
            self.screen.fill(BG_COLOR)
        pygame.display.flip()

    # -----------------------------------------------------------
    # Lecture d'une video synchronisee avec un audio (en boucle si besoin)
    # -----------------------------------------------------------
    def _jouer_video_avec_audio(self, chemin_video, audio_data, boucle=True):
        if audio_data.size == 0:
            return

        def _jouer_audio():
            sd.play(audio_data, samplerate=SAMPLE_RATE)

        thread_audio = threading.Thread(target=_jouer_audio)
        thread_audio.start()

        duree_totale = len(audio_data) / SAMPLE_RATE
        debut = time.time()

        cap = cv2.VideoCapture(chemin_video) if self._videos_disponibles else None
        fps = (cap.get(cv2.CAP_PROP_FPS) if cap else 0) or 25
        delai_frame = 1.0 / fps

        while time.time() - debut < duree_totale and self.running:
            self.handle_events()
            debut_frame = time.time()

            if cap is not None:
                ok, frame = cap.read()
                if not ok:
                    if boucle:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        break
                surface = self._frame_vers_surface(frame)
                self._derniere_image = surface
                self._afficher(surface)
            else:
                self._afficher()

            ecoule = time.time() - debut_frame
            time.sleep(max(0, delai_frame - ecoule))

        if cap is not None:
            cap.release()

        sd.wait()
        thread_audio.join()

    # -----------------------------------------------------------
    # API publique (utilisee par main.py)
    # -----------------------------------------------------------
    def speak_animated(self, audio_data, texte: str = None):
        """Reponse normale : boucle la video TALKING pendant l'audio."""
        self._jouer_video_avec_audio(AVATAR_VIDEO_TALKING, audio_data, boucle=True)

    def welcome_animated(self, audio_data, texte: str = None):
        """Message d'accueil : boucle la video WELCOME pendant l'audio."""
        self._jouer_video_avec_audio(AVATAR_VIDEO_WELCOME, audio_data, boucle=True)

    def goodbye_animated(self, audio_data, texte: str = None):
        """Message d'au revoir : boucle la video GOODBYE pendant l'audio."""
        self._jouer_video_avec_audio(AVATAR_VIDEO_GOODBYE, audio_data, boucle=True)

    def idle_tick(self):
        """A appeler en boucle pendant les phases d'attente/ecoute."""
        self.handle_events()
        self._afficher()
        self.clock.tick(30)

    def close(self):
        pygame.quit()


if __name__ == "__main__":
    # Test rapide : joue le message d'accueil puis d'au revoir
    from tts import synthesize

    avatar = Avatar()
    audio = synthesize("Bonjour, je suis l'avatar d'accueil de l'ecole.")
    avatar.welcome_animated(audio)

    audio2 = synthesize("Merci de votre visite, au revoir !")
    avatar.goodbye_animated(audio2)

    avatar.close()
