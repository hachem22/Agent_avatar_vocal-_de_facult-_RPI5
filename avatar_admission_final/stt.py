# stt.py
# ---------------------------------------------------------
# Speech-to-Text local avec faster-whisper
# Enregistre le micro, détecte le silence, transcrit en texte
# ---------------------------------------------------------

import sounddevice as sd
import numpy as np
import queue
import time
from faster_whisper import WhisperModel
from config import WHISPER_MODEL_SIZE, WHISPER_LANGUAGE

SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.01      # seuil pour détecter le silence (à ajuster selon ton micro)
SILENCE_DURATION = 1.2        # secondes de silence avant d'arrêter l'enregistrement
MAX_DURATION = 15             # durée max d'une question (sécurité)

print("Chargement du modele Whisper (peut prendre un moment la 1ere fois)...")
_model = WhisperModel(
    WHISPER_MODEL_SIZE,
    device="cpu",
    compute_type="int8",
    cpu_threads=4,   # utilise les 4 coeurs du Raspberry Pi 5
)
print("Modele Whisper pret.")

_audio_queue = queue.Queue()


def _callback(indata, frames, time_info, status):
    _audio_queue.put(indata.copy())


def record_until_silence():
    """Enregistre depuis le micro jusqu'à détecter un silence, retourne l'audio en numpy array."""
    print("🎤 Écoute... (parlez maintenant)")
    frames = []
    silence_start = None
    start_time = time.time()

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=_callback):
        while True:
            chunk = _audio_queue.get()
            frames.append(chunk)
            volume = np.abs(chunk).mean()

            if volume < SILENCE_THRESHOLD:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > SILENCE_DURATION and len(frames) > 5:
                    break
            else:
                silence_start = None

            if time.time() - start_time > MAX_DURATION:
                break

    audio = np.concatenate(frames, axis=0).flatten()
    return audio


def transcribe(audio: np.ndarray) -> str:
    """Transcrit un tableau audio numpy en texte."""
    segments, _ = _model.transcribe(
        audio, language=WHISPER_LANGUAGE, beam_size=1, vad_filter=True
    )
    text = " ".join(seg.text.strip() for seg in segments)
    return text.strip()


def listen_and_transcribe() -> str:
    """Fonction principale : écoute puis renvoie le texte transcrit."""
    audio = record_until_silence()
    print("Transcription en cours...")
    text = transcribe(audio)
    print(f"👤 Question détectée : {text}")
    return text


if __name__ == "__main__":
    # Test rapide : lance ce fichier seul pour tester le micro
    while True:
        q = listen_and_transcribe()
        if q.lower() in ("stop", "quitter", "exit"):
            break
