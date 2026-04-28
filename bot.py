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
FFMPEG_PATH = None
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
    FFMPEG_AVAILABLE = True
except Exception:
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


def send_photo(chat_id, photo_path, caption=""):
    with open(photo_path, "rb") as f:
        httpx.post(
            f"{TELEGRAM_API}/sendPhoto",
            data={"chat_id": str(chat_id), "caption": caption[:1024]},
            files={"photo": f},
            timeout=30,
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
                from video import MEDIA_DIR
                import glob, os as _os
                media_count = len(
                    glob.glob(_os.path.join(MEDIA_DIR, "*.mp4")) +
                    glob.glob(_os.path.join(MEDIA_DIR, "*.mov")) +
                    glob.glob(_os.path.join(MEDIA_DIR, "*.jpg")) +
                    glob.glob(_os.path.join(MEDIA_DIR, "*.jpeg")) +
                    glob.glob(_os.path.join(MEDIA_DIR, "*.png"))
                ) if _os.path.isdir(MEDIA_DIR) else 0
                media_status = f"📁 {media_count} médias locaux chargés" if media_count else "📁 Aucun média local (dossier media/ vide)"
                send_message(chat_id,
                    "🥊 Bot Marketing Instagram\n\n"
                    "Envoie une idée de post et je génère :\n"
                    "• Caption + hashtags\n"
                    "• Vidéo Reel 15s avec TES photos/vidéos\n\n"
                    f"{media_status}\n\n"
                    "Commandes :\n"
                    "/start — Afficher ce menu\n"
                    "/listmedia — Voir les médias disponibles\n\n"
                    "Exemple : \"Reel pour promouvoir les cours du soir\""
                )
                continue

            if text == "/listmedia":
                from video import MEDIA_DIR
                import glob, os as _os
                if not _os.path.isdir(MEDIA_DIR):
                    send_message(chat_id, "❌ Dossier media/ introuvable.")
                    continue
                files = []
                for ext in ("*.mp4", "*.mov", "*.jpg", "*.jpeg", "*.png"):
                    files.extend(glob.glob(_os.path.join(MEDIA_DIR, ext)))
                if not files:
                    send_message(chat_id, "📁 Dossier media/ vide.\n\nAjoute tes photos/vidéos dans :\n" + MEDIA_DIR)
                else:
                    names = "\n".join(f"• {_os.path.basename(f)}" for f in sorted(files))
                    send_message(chat_id, f"📁 {len(files)} médias disponibles :\n\n{names}")
                continue

            print(f"Demande: {text[:60]}...")
            send_message(chat_id, "⏳ Génération du contenu...")

            try:
                data = generate_content(text)
                # Envoyer le texte
                send_message(chat_id, format_post(data))

                # Générer la vidéo si FFmpeg dispo
                if FFMPEG_AVAILABLE:
                    send_message(chat_id, "🎬 Création du Reel...")
                    try:
                        from video import create_reel
                        video_path, source = create_reel(
                            data["caption"],
                            data["accroche"],
                            data["hashtags"],
                            data["keyword_video"],
                        )
                        source_label = {
                            "local": "📁 Média local utilisé",
                            "pexels": "🌐 Vidéo Pexels utilisée",
                            "gradient": "🎨 Fond généré (ajoutez des médias dans media/)",
                        }.get(source, "")
                        send_video(chat_id, video_path,
                                   caption=f"{data['accroche']}\n\n{data['hashtags'][:200]}")
                        send_message(chat_id, source_label)
                        os.unlink(video_path)
                        print(f"Vidéo envoyée — source: {source}")
                    except Exception as e:
                        send_message(chat_id, f"⚠️ Vidéo indisponible : {str(e)[:100]}")
                else:
                    send_message(chat_id, "ℹ️ Vidéo désactivée — FFmpeg non installé")

            except Exception as e:
                send_message(chat_id, f"❌ Erreur : {str(e)[:200]}")
                print(f"Erreur: {e}")

        time.sleep(1)


if __name__ == "__main__":
    main()
