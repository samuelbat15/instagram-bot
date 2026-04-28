import os
import sys
import time
import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN_INSTA"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
offset = 0

SYSTEM_PROMPT = """Tu es un expert en marketing digital Instagram pour PME locales et coachs sportifs.

Quand l'utilisateur te donne un sujet ou une idée, génère EXACTEMENT ce format :

📸 CAPTION INSTAGRAM
[Une caption engageante de 3-5 lignes, avec emojis, ton humain et authentique]

📢 ACCROCHE (première ligne qui stoppe le scroll)
[Une accroche percutante de maximum 10 mots]

#️⃣ HASHTAGS (30 hashtags optimisés)
[30 hashtags mix : 10 populaires + 10 moyens + 10 niche]

💡 IDÉE VISUEL
[Description précise de la photo ou vidéo idéale pour ce post]

📅 MEILLEUR HORAIRE DE PUBLICATION
[Jour et heure optimaux pour ce type de contenu]

🔁 APPEL À L'ACTION
[Une CTA claire et naturelle]

Adapte toujours le contenu au secteur mentionné par l'utilisateur."""


def get_updates():
    global offset
    r = httpx.get(
        f"{TELEGRAM_API}/getUpdates",
        params={"offset": offset, "timeout": 30},
        timeout=35,
    )
    return r.json().get("result", [])


def send_message(chat_id, text):
    # Telegram limite à 4096 caractères par message
    if len(text) > 4000:
        for i in range(0, len(text), 4000):
            httpx.post(
                f"{TELEGRAM_API}/sendMessage",
                json={"chat_id": chat_id, "text": text[i:i+4000]},
            )
            time.sleep(0.5)
    else:
        httpx.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text},
        )


def generate_content(user_message):
    r = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "max_tokens": 1000,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        },
        timeout=20,
    )
    return r.json()["choices"][0]["message"]["content"]


def main():
    global offset
    print("Bot Instagram Marketing démarré...")
    while True:
        updates = get_updates()
        for update in updates:
            offset = update["update_id"] + 1
            msg = update.get("message", {})
            chat_id = msg.get("chat", {}).get("id")
            text = msg.get("text", "")
            if not chat_id or not text:
                continue

            if text == "/start":
                send_message(chat_id,
                    "🥊 Bot Marketing Instagram actif !\n\n"
                    "Envoie-moi un sujet ou une idée de post et je génère :\n"
                    "• Caption complète\n"
                    "• 30 hashtags optimisés\n"
                    "• Idée visuel\n"
                    "• Meilleur horaire\n\n"
                    "Exemple : \"Post sur les bienfaits de la boxe pour les femmes\""
                )
                continue

            print(f"Demande: {text[:60]}...")
            send_message(chat_id, "⏳ Génération en cours...")
            content = generate_content(text)
            send_message(chat_id, content)
            print("Contenu envoyé")

        time.sleep(1)


if __name__ == "__main__":
    main()
