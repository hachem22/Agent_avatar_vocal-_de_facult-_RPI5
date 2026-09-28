# tts.py
# ---------------------------------------------------------
# Text-to-Speech local avec Piper
# synthesize() : genere l'audio (numpy array) sans le jouer
# speak()      : genere ET joue l'audio (usage simple, sans avatar)
# ---------------------------------------------------------

import os
import subprocess
import sounddevice as sd
import numpy as np
from config import PIPER_VOICE_MODEL, PIPER_EXECUTABLE

SAMPLE_RATE = 22050  # depend du modele de voix Piper utilise


def _resolve_piper_command():
    """Utilise le chemin complet vers piper.exe s'il existe, sinon retombe
    sur la commande 'piper' (au cas ou elle serait dans le PATH systeme)."""
    if os.path.exists(PIPER_EXECUTABLE):
        return PIPER_EXECUTABLE
    return "piper"


def synthesize(text: str) -> np.ndarray:
    """Genere l'audio avec Piper et retourne un tableau numpy (sans le jouer)."""
    if not text.strip():
        return np.array([], dtype=np.int16)

    piper_cmd = _resolve_piper_command()

    try:
        process = subprocess.run(
            [
                piper_cmd,
                "--model", PIPER_VOICE_MODEL,
                "--output_raw",
            ],
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        print(f"ERREUR : impossible de trouver Piper a l'emplacement '{piper_cmd}'.")
        print("Verifie le chemin PIPER_EXECUTABLE dans config.py.")
        return np.array([], dtype=np.int16)

    if process.returncode != 0:
        print("Erreur Piper :", process.stderr.decode(errors="ignore"))
        return np.array([], dtype=np.int16)

    return np.frombuffer(process.stdout, dtype=np.int16)


def play(audio_data: np.ndarray, blocking: bool = True):
    """Joue un tableau audio deja genere."""
    if audio_data.size == 0:
        return
    sd.play(audio_data, samplerate=SAMPLE_RATE)
    if blocking:
        sd.wait()


def speak(text: str):
    """Genere et joue directement le texte (usage simple, sans avatar visuel)."""
    print("Lecture de la reponse...")
    audio_data = synthesize(text)
    play(audio_data, blocking=True)


if __name__ == "__main__":
    speak("Bonjour, je suis l'avatar d'accueil de l'ecole. Comment puis-je vous aider ?")
