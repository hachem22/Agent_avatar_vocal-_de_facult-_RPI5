# llm.py
# ---------------------------------------------------------
# Envoie la question au LLM local (Ollama) et récupère la réponse
# ---------------------------------------------------------

import requests
from config import OLLAMA_MODEL, OLLAMA_URL, SYSTEM_PROMPT

# On garde un petit historique pour garder le contexte de la conversation
_conversation_history = []
MAX_HISTORY_TURNS = 6  # nombre d'échanges gardés en mémoire (évite que le prompt devienne trop long)


def ask_llm(question: str) -> str:
    global _conversation_history

    _conversation_history.append(f"Utilisateur: {question}")
    history_text = "\n".join(_conversation_history[-MAX_HISTORY_TURNS:])

    full_prompt = f"{SYSTEM_PROMPT}\n\nConversation:\n{history_text}\nAvatar:"

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,   # réponses plus factuelles, moins "créatives"
                "num_predict": 200,   # limite la longueur de la réponse
            },
        },
        timeout=60,
    )
    response.raise_for_status()
    answer = response.json()["response"].strip()

    _conversation_history.append(f"Avatar: {answer}")
    print(f"🤖 Réponse : {answer}")
    return answer


def reset_conversation():
    global _conversation_history
    _conversation_history = []


if __name__ == "__main__":
    # Test rapide en mode texte (sans micro)
    print("Mode test texte. Tape 'stop' pour quitter.")
    while True:
        q = input("Question : ")
        if q.lower() == "stop":
            break
        ask_llm(q)
