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

SYSTEM_PROMPT = """Tu es le community manager expert de STAR BOXE COACHING à Brest.

=== INFOS OFFICIELLES STAR BOXE ===
Adresse : 13 Rue Amiral Troude, 29200 Brest
Tél : 06 13 94 16 42 | Site : starboxe.com | Instagram : @starboxe29
Horaires : 10h-13h30 / 17h30-21h15
Note : 4.8/5 — plus de 1000 personnes coachées

=== COACH AIELLO BATONON ===
- Né au Gabon, grandit à Brest dès 12 ans
- Champion de France Muay Thai 2009
- Champion d'Europe WPMF -75kg 2010
- 🏆 Champion du Monde WPMF -75kg — 2 avril 2011
- Premier Brestois à décrocher un titre mondial de Boxe Thaï
- Diplôme d'État BPJEPS sports de contact
- Coaching personnalisé : 80€/heure
- Fondateur de Star Boxe

=== DISCIPLINES ===
Muay Thai • Boxe Anglaise • MMA • Grappling • Cross Training
Yoga • Pilates • Musculation • Miha Bodytec (EMS) • Cardio

=== OBJECTIF ===
Attirer maximum de clients à Brest et Finistère. Mettre en avant le Champion du Monde Aiello.
Ton : Dynamique, champion, authentique, motivant, local breton.

Quand l'utilisateur te donne un sujet ou une discipline, génère EXACTEMENT ce JSON :

{
  "accroche": "Accroche de MAX 8 MOTS qui arrête le scroll — percutante, action ou question",
  "caption": "Caption de 4-6 lignes avec emojis 🥊💪🔥 — storytelling, bénéfices concrets, ton champion",
  "hashtags": "30 hashtags mix local Brest + sport + motivation",
  "horaire": "Meilleur horaire de publication pour ce type de contenu",
  "cta": "Appel à l'action direct (ex: Envoie ESSAI en MP pour ton cours gratuit !)",
  "keyword_video": "2-3 mots anglais pour vidéo Pexels portrait (ex: boxing training)",
  "voix_texte": "Texte de 2-3 phrases pour la voix off — enthousiaste, comme un champion qui parle"
}

Intègre toujours le nom Star Boxe, Aiello Batonon ou Champion du Monde dans la caption.
Mentionne Brest ou Bretagne dans les hashtags.
Réponds UNIQUEMENT avec le JSON, sans rien avant ni après."""


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


def send_discipline_menu(chat_id):
    """Envoie le menu inline des 8 disciplines."""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🥊 Boxe Thaï", "callback_data": "disc:boxing"},
                {"text": "⚔️ MMA", "callback_data": "disc:mma"},
            ],
            [
                {"text": "💪 Musculation", "callback_data": "disc:musculation"},
                {"text": "🧘 Yoga", "callback_data": "disc:yoga"},
            ],
            [
                {"text": "🤸 Pilates", "callback_data": "disc:pilates"},
                {"text": "⚡ Miha Bodytec", "callback_data": "disc:miha_bodytec"},
            ],
            [
                {"text": "🏃 Cardio", "callback_data": "disc:cardio"},
                {"text": "🏆 Coaching perso", "callback_data": "disc:coaching"},
            ],
            [
                {"text": "📊 Rapport semaine", "callback_data": "cmd:report"},
                {"text": "⚙️ Statut bot", "callback_data": "cmd:status"},
            ],
        ]
    }
    httpx.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": "🥊 *Star Boxe Coaching — Bot Marketing*\n\nChoisis une discipline pour générer un Reel :",
            "parse_mode": "Markdown",
            "reply_markup": keyboard,
        },
        timeout=10,
    )


def answer_callback(callback_id: str, text: str = ""):
    httpx.post(f"{TELEGRAM_API}/answerCallbackQuery",
               json={"callback_query_id": callback_id, "text": text}, timeout=5)


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

    # Démarrer le scheduler automatique
    try:
        from scheduler import start_scheduler
        _sched = start_scheduler()
    except Exception as e:
        print(f"Scheduler non démarré: {e}")

    while True:
        updates = get_updates()
        for update in updates:
            offset = update["update_id"] + 1

            # Gestion des callbacks (boutons inline)
            cb = update.get("callback_query")
            if cb:
                cb_id = cb["id"]
                cb_data = cb.get("data", "")
                cb_chat = cb["message"]["chat"]["id"]
                answer_callback(cb_id)
                if cb_data.startswith("disc:"):
                    discipline = cb_data[5:]
                    from sports_config import SPORTS_CATEGORIES
                    cat = SPORTS_CATEGORIES.get(discipline, {})
                    keyword = cat.get("pexels_keyword", discipline)
                    text = f"Reel {discipline} Star Boxe Brest Aiello champion du monde"
                    chat_id = cb_chat
                    # Traiter comme une demande normale
                elif cb_data == "cmd:report":
                    from analytics import weekly_report
                    send_message(cb_chat, weekly_report())
                    continue
                elif cb_data == "cmd:status":
                    from analytics import total_posts
                    insta = os.environ.get("INSTAGRAM_USER", "non configuré")
                    sora = "✅" if os.environ.get("OPENAI_API_KEY") else "❌"
                    send_message(cb_chat,
                        f"🤖 Statut bot\n\n"
                        f"FFmpeg: {'✅' if FFMPEG_AVAILABLE else '❌'}\n"
                        f"Sora AI: {sora}\n"
                        f"Instagram: {insta}\n"
                        f"Posts générés: {total_posts()} total"
                    )
                    continue
                else:
                    continue

            msg = update.get("message", {})
            if not cb:
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "")
            if not chat_id or not text:
                continue

            if text in ("/start", "/menu"):
                send_discipline_menu(chat_id)
                continue

            if text == "/rapport":
                from analytics import weekly_report
                send_message(chat_id, weekly_report())
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
                    send_message(chat_id, "🎬 Création du Reel avec voix off + musique...")
                    try:
                        from video import create_reel
                        video_path, source = create_reel(
                            data["caption"],
                            data["accroche"],
                            data["hashtags"],
                            data["keyword_video"],
                        )
                        source_label = {
                            "local": "📁 Média local",
                            "pexels": "🌐 Pexels",
                            "gradient": "🎨 Fond généré",
                        }.get(source, "")
                        send_video(chat_id, video_path,
                                   caption=f"{data['accroche']}\n\n{data['hashtags'][:200]}")

                        # Auto-post Instagram si configuré
                        from instagram import post_reel, INSTAGRAM_USER
                        if INSTAGRAM_USER:
                            send_message(chat_id, "📲 Publication sur Instagram en cours...")
                            url = post_reel(video_path, data["caption"], data["hashtags"])
                            if url:
                                send_message(chat_id, f"✅ Publié sur Instagram !\n{url}")
                            else:
                                send_message(chat_id, "⚠️ Publication Instagram échouée — vérifier les identifiants")
                        else:
                            send_message(chat_id, f"{source_label}\n💡 Configure INSTAGRAM_USER + INSTAGRAM_PASS pour auto-publier")

                        # Analytics
                        try:
                            from analytics import log_post
                            insta_url = url if (INSTAGRAM_USER and url) else ""
                            disc = data.get("keyword_video", "unknown")
                            log_post(disc, source, data.get("accroche", ""), insta_url)
                        except Exception:
                            pass

                        os.unlink(video_path)
                        print(f"Vidéo envoyée — source: {source}")
                    except Exception as e:
                        send_message(chat_id, f"⚠️ Erreur vidéo : {str(e)[:150]}")
                else:
                    send_message(chat_id, "ℹ️ Vidéo désactivée — FFmpeg non installé")

            except Exception as e:
                send_message(chat_id, f"❌ Erreur : {str(e)[:200]}")
                print(f"Erreur: {e}")

        time.sleep(1)


if __name__ == "__main__":
    main()
