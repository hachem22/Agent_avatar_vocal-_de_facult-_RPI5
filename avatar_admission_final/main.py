# main.py
# ---------------------------------------------------------
# Machine a etats : ATTENTE -> ECOUTE -> REFLEXION -> PAROLE
# Avatar visuel base sur 3 videos (accueil / parole / au revoir)
# ---------------------------------------------------------

import time
from stt import listen_and_transcribe
from llm import ask_llm, reset_conversation
from tts import synthesize
from avatar_visual import Avatar
from presence import personne_detectee
import presence
from config import TEMPS_INACTIVITE_FIN_CONVERSATION, DETECTION_MODE

MOTS_ARRET = ("stop", "quitte", "au revoir", "arrete-toi")

MESSAGE_ACCUEIL = "Bonjour ! Je suis l'avatar d'accueil. Posez-moi vos questions sur l'admission."
MESSAGE_AU_REVOIR = "Merci de votre visite, bonne journee !"


def main():
    print("=" * 50)
    print("  AVATAR D'ADMISSION - Demarrage")
    print(f"  Etat initial : ATTENTE (detection = {DETECTION_MODE})")
    print("=" * 50)

    avatar = Avatar()
    en_conversation = False
    dernier_echange = time.time()

    try:
        while avatar.running:

            # ------------------------------------------------------------
            # ETAT ATTENTE
            # ------------------------------------------------------------
            if not en_conversation:
                avatar.idle_tick()
                presence.update_window()

                if personne_detectee():
                    print("Personne detectee -> debut de conversation")
                    en_conversation = True
                    reset_conversation()
                    dernier_echange = time.time()

                    audio = synthesize(MESSAGE_ACCUEIL)
                    avatar.welcome_animated(audio, texte=MESSAGE_ACCUEIL)

                continue

            # ------------------------------------------------------------
            # ETAT ECOUTE
            # ------------------------------------------------------------
            question = listen_and_transcribe()

            if not avatar.running:
                break

            if not question:
                if time.time() - dernier_echange > TEMPS_INACTIVITE_FIN_CONVERSATION:
                    print("Inactivite prolongee -> retour en ATTENTE")
                    en_conversation = False
                avatar.idle_tick()
                presence.update_window()
                continue

            if any(mot in question.lower() for mot in MOTS_ARRET):
                audio = synthesize(MESSAGE_AU_REVOIR)
                avatar.goodbye_animated(audio, texte=MESSAGE_AU_REVOIR)
                en_conversation = False
                continue

            # ------------------------------------------------------------
            # ETAT REFLEXION
            # ------------------------------------------------------------
            reponse = ask_llm(question)
            dernier_echange = time.time()

            # ------------------------------------------------------------
            # ETAT PAROLE
            # ------------------------------------------------------------
            audio = synthesize(reponse)
            avatar.speak_animated(audio, texte=reponse)

    except KeyboardInterrupt:
        print("\nArret manuel.")
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        avatar.close()
        presence.close()


if __name__ == "__main__":
    main()
