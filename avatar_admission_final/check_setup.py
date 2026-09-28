# check_setup.py
# ---------------------------------------------------------
# Verifie que tout est correctement installe AVANT de lancer
# le pipeline complet. Lance ce script en premier !
# ---------------------------------------------------------

import sys
import subprocess
import importlib
import importlib.util

def check(label, fn):
    print(f"Verification : {label} ... ", end="", flush=True)
    try:
        fn()
        print("OK")
        return True
    except Exception as e:
        print(f"ECHEC -> {e}")
        return False


def check_python_packages():
    required = ["faster_whisper", "sounddevice", "numpy", "requests", "pygame", "cv2"]
    missing = [p for p in required if importlib.util.find_spec(p) is None]
    if missing:
        raise RuntimeError(f"Packages manquants : {missing}. Lance 'pip install -r requirements.txt'")


def check_camera():
    from config import DETECTION_MODE, CAMERA_TYPE, CAMERA_INDEX
    if DETECTION_MODE not in ("camera", "les_deux"):
        print("(DETECTION_MODE n'utilise pas la camera, verification ignoree) ", end="")
        return

    import cv2
    if not hasattr(cv2, "CascadeClassifier"):
        raise RuntimeError(
            f"cv2 (version {cv2.__version__}) n'a pas CascadeClassifier. "
            "Depuis OpenCV 5.0, cette classe a ete deplacee vers opencv_contrib. "
            "Corrige avec : pip uninstall -y opencv-python opencv-python-headless "
            "opencv-contrib-python opencv-contrib-python-headless && "
            "pip install \"opencv-python<5\""
        )

    if CAMERA_TYPE == "picamera2":
        if importlib.util.find_spec("picamera2") is None:
            raise RuntimeError(
                "picamera2 introuvable. Installe-le avec : sudo apt install -y python3-picamera2 "
                "(et cree ton venv avec --system-site-packages)"
            )
    else:
        cap = cv2.VideoCapture(CAMERA_INDEX)
        ok = cap.isOpened()
        cap.release()
        if not ok:
            raise RuntimeError(
                f"Impossible d'ouvrir la camera USB (index={CAMERA_INDEX}). "
                "Verifie 'ls /dev/video*' et le branchement."
            )


def check_ollama():
    import requests
    r = requests.get("http://localhost:11434/api/tags", timeout=3)
    r.raise_for_status()
    models = [m["name"] for m in r.json().get("models", [])]
    if not models:
        raise RuntimeError("Ollama tourne mais aucun modele installe. Lance 'ollama pull llama3.2:3b'")
    print(f"(modeles disponibles : {models}) ", end="")


def check_piper():
    from config import PIPER_EXECUTABLE
    import os
    if not os.path.exists(PIPER_EXECUTABLE):
        raise RuntimeError(f"piper introuvable a l'emplacement configure : {PIPER_EXECUTABLE}")
    result = subprocess.run([PIPER_EXECUTABLE, "--help"], capture_output=True, text=True)
    if result.returncode != 0 and "piper" not in (result.stdout + result.stderr).lower():
        raise RuntimeError("Piper trouve mais ne repond pas correctement")


def check_voice_model():
    import os
    from config import PIPER_VOICE_MODEL
    if not os.path.exists(PIPER_VOICE_MODEL):
        raise RuntimeError(f"Modele de voix introuvable : {PIPER_VOICE_MODEL}. Verifie le dossier voices/")


def check_microphone():
    import sounddevice as sd
    devices = sd.query_devices()
    input_devices = [d for d in devices if d["max_input_channels"] > 0]
    if not input_devices:
        raise RuntimeError("Aucun peripherique d'entree audio (micro) detecte")
    default_input = sd.query_devices(kind="input")
    print(f"(micro par defaut : {default_input['name']}) ", end="")


def check_speaker():
    import sounddevice as sd
    devices = sd.query_devices()
    output_devices = [d for d in devices if d["max_output_channels"] > 0]
    if not output_devices:
        raise RuntimeError("Aucun peripherique de sortie audio (haut-parleur) detecte")
    default_output = sd.query_devices(kind="output")
    print(f"(sortie par defaut : {default_output['name']}) ", end="")


if __name__ == "__main__":
    print("=" * 55)
    print(" VERIFICATION DE L'INSTALLATION - Avatar Admission")
    print("=" * 55)

    results = []
    results.append(check("Packages Python (requirements.txt)", check_python_packages))
    results.append(check("Ollama en cours d'execution + modele", check_ollama))
    results.append(check("Piper installe et accessible", check_piper))
    results.append(check("Modele de voix Piper telecharge", check_voice_model))
    results.append(check("Microphone detecte", check_microphone))
    results.append(check("Haut-parleur detecte", check_speaker))
    results.append(check("Camera (si utilisee par DETECTION_MODE)", check_camera))

    print("=" * 55)
    if all(results):
        print("Tout est pret ! Tu peux lancer : python main.py")
    else:
        print("Certains elements manquent. Corrige les erreurs ci-dessus")
        print("avant de lancer main.py (voir INSTALLATION_PC_WINDOWS.md).")
    sys.exit(0 if all(results) else 1)
