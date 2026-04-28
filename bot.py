import os
import sys
import time
import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN_INSTA"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
offset = 0

FFMPEG_AVAILABLE = False
try:
    import subprocess
    r = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    FFMPEG_AVAILABLE = r.returncode == 0
except Exception:
    pass

SYSTEM_PROMPT = """Tu es un expert en marketing digital Instagram pour PME locales et coachs sportifs.

Quand l'utilisateur te donne un sujet, génère EXACTEMENT ce format JSON :

{
  "accroche": "Une accroche de max 8 mots qui stoppe le scroll",
  "caption": "Caption complète 3-5 lignes avec emojis",
  "hashtags": "#hashtag1 #hashtag2 ... (30 hashtags)",
  "horaire": "Mardi 18h00",
  "cta": "Appel à l'action clair",
  "keyword_video": "mot-clé en anglais pour chercher une vidéo de fond (ex: boxing, fitness, workout)"
}

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après."""


def get_updates():
    global offset
    r = httpx.get(
        f"{TELEGRAM_API}/getUpdates",
        params={"offset": offset, "timeout": 30},
        timeout=35,
    )
    return r.json().get("result", [])


def send_message(chat_id, text):
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        httpx.post(f"{TELEGRAM_API}/sendMessage",
                   json={"chat_id": chat_id, "text": chunk})
        time.sleep(0.3)


def send_video(chat_id, video_path, caption=""):
    with open(video_path, "rb") as f:
        httpx.post(
            f"{TELEGRAM_API}/sendVideo",
            data={"chat_id": str(chat_id), "caption": caption[:1000]},
            files={"video": f},
            timeout=60,
        )


def generate_content(text):
    import json
    r = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "max_tokens": 600,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        },
        timeout=20,
    )
    content = r.json()["choices"][0]["message"]["content"]
    # Extraire le JSON
    start = content.find("{")
    end = content.rfind("}") + 1
    return json.loads(content[start:end])


def format_post(data):
    return (
        f"📢 ACCROCHE\n{data['accroche']}\n\n"
        f"📸 CAPTION\n{data['caption']}\n\n"
        f"#️⃣ HASHTAGS\n{data['hashtags']}\n\n"
        f"📅 HORAIRE : {data['horaire']}\n"
        f"🔁 CTA : {data['cta']}"
    )


def main():
    global offset
    print("Bot Instagram Marketing démarré...")
    print(f"FFmpeg disponible : {FFMPEG_AVAILABLE}")

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
                    "🥊 Bot Marketing Instagram\n\n"
                    "Envoie une idée de post et je génère :\n"
                    "• Caption + hashtags\n"
                    "• Vidéo Reel 15s prête à publier\n\n"
                    "Exemple : \"Reel pour promouvoir les cours du soir\""
                )
                continue

            print(f"Demande: {text[:60]}...")
            send_message(chat_id, "⏳ Génération du contenu...")

            try:
                data = generate_content(text)
                # Envoyer le texte
                send_message(chat_id, format_post(data))

                # Générer la vidéo si FFmpeg dispo
                if FFMPEG_AVAILABLE and os.environ.get("PEXELS_API_KEY"):
                    send_message(chat_id, "🎬 Création de la vidéo Reel...")
                    try:
                        from video import create_reel
                        video_path = create_reel(
                            data["caption"],
                            data["accroche"],
                            data["hashtags"],
                            data["keyword_video"],
                        )
                        send_video(chat_id, video_path,
                                   caption=f"{data['accroche']}\n\n{data['hashtags'][:200]}")
                        os.unlink(video_path)
                        print("Vidéo envoyée")
                    except Exception as e:
                        send_message(chat_id, f"⚠️ Vidéo indisponible : {str(e)[:100]}")
                elif not FFMPEG_AVAILABLE:
                    send_message(chat_id, "ℹ️ Vidéo désactivée — FFmpeg non installé")
                else:
                    send_message(chat_id, "ℹ️ Vidéo désactivée — clé Pexels manquante")

            except Exception as e:
                send_message(chat_id, f"❌ Erreur : {str(e)[:200]}")
                print(f"Erreur: {e}")

        time.sleep(1)


if __name__ == "__main__":
    main()
