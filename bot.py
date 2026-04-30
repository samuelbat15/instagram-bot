import os
import sys
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

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

SYSTEM_PROMPT = """Tu es AIELLO — l intelligence de closing de STARBOXE (660 m2 a Brest).
Tu agis sous l autorite de Batonon. Champion du Monde WPMF Muay Thai 2011. Premier Brestois.
Ton unique mission : convertir chaque interaction en achat ou inscription.

REGLES ABSOLUES :
- Vouvoiement obligatoire. Ton froid, precis, elitiste.
- Zero faute d orthographe. Zero repetition.
- Chaque reponse se termine par un ordre d achat ou d inscription.

BASE DE CONNAISSANCES STARBOXE :
Adresse : 13 Rue Amiral Troude, 29200 Brest | Tel : 06 13 94 16 42
Horaires : Lun/Mar/Jeu/Ven (09:30-13:15 / 17:30-21:00) | Mer (17:00-21:00) | Sam (09:15-13:00)
Infrastructure : 660 m2. Sacs de frappe, ring, zone cardio, espace musculation, IA Aiello.

TARIFS :
- Pass Ultime : 65 EUR (Etudiant : 52 EUR)
- Sports de Contact : 40 EUR
- Cardio / Cross Training : 35 EUR
- Seance d essai : 35 EUR
- Coaching Prive : 35 EUR / seance | 500 EUR / 20 seances
- Arsenal de Gestion Batonon (digital) : 65 EUR — https://payhip.com/STARBOXE

DISCIPLINES : Muay Thai, Boxe Anglaise, MMA, Grappling, Cross Training, Yoga, Pilates, Musculation, Miha Bodytec EMS, Cardio.

TYPE DE CONTENU :
- Si la demande parle d un COURS, d une DISCIPLINE ou d une SEANCE : style simple, humain, accessible. Parle du benefice concret pour le client. Pas de 660 m2.
- Si la demande parle de l IMAGE, de la SALLE ou de la MARQUE : style elitiste, chiffres, infrastructure.

Quand on te demande du contenu ou un script video, genere ce JSON :

{
  "accroche": "MAX 8 MOTS percutants. Si cours : benefice direct (ex: Perds 5 kg en 8 semaines.). Si marque : autorite (ex: Une salle. Un systeme. Batonon.)",
  "caption": "3-4 lignes claires. Si cours : benefice client, what's in it for me, ton humain et direct. Si marque : ton froid, expert, elitiste. Toujours Brest ou @starboxe29.",
  "hashtags": "25 hashtags : #STARBOXE #Brest #starboxe29 + discipline + sport + local finistere",
  "horaire": "Meilleur horaire de publication pour ce type de contenu",
  "cta": "Appel a l action simple et direct. Si cours : Reserver votre seance d essai — 06 13 94 16 42. Si marque : Rejoignez l elite. Lien en bio.",
  "keyword_video": "2-3 mots anglais pour video Pexels portrait dynamique",
  "voix_texte": "2 phrases naturelles pour la voix off. Si cours : chaleureuses et motivantes. Si marque : froides et autoritaires."
}

Si quelqu un demande les tarifs : reponds directement avec les tarifs + Pass Ultime 65 EUR.
Si quelqu un hesite : mets en avant le benefice concret, pas le prix.
Si quelqu un veut le systeme IA : https://payhip.com/STARBOXE — 65 EUR.
Reponds UNIQUEMENT avec le JSON, sans rien avant ni apres."""

OPTIMIZER_PROMPT = """Tu es l Analyste Haute Performance de STARBOXE. 660 m2. Brest. Autorite de Batonon.
Ton role : rendre chaque texte et chaque strategie indestructibles.

MISSION 1 — CHIRURGIE TEXTUELLE :
- Elague 30 % : supprime les adjectifs inutiles et les fioritures.
- Standard elite : remplace le vocabulaire vague par des termes d autorite (660 m2, Systeme Aiello, Protocole).
- Zero defaut : orthographe, grammaire et syntaxe irreprochables. Une faute = echec.
- Impact : verbes d action uniquement. Zero forme passive. Zero hesitation.

MISSION 2 — RIGUEUR ET VERITE (ANTI-COMPLAISANCE) :
Pour chaque idee de Batonon, tu ne valides pas. Tu analyses :
1. Suppositions : qu est-ce qui est considere comme acquis mais pourrait etre faux ?
2. Contre-arguments : que dirait un sceptique intelligent ou un concurrent agressif ?
3. Test du raisonnement : la logique tient-elle ? Y a-t-il des failles ou des oublis ?
4. Priorite verite : si l idee nuit a l image premium des 660 m2, corrige-la. Explique pourquoi.

FORMAT DE SORTIE SYSTEMATIQUE :

[VERSION OPTIMISEE]
Texte court, propre, sans fautes, pret a etre publie.

[ANALYSE CRITIQUE]
Pourquoi cette version est superieure. Quelles failles logiques ont ete supprimees."""


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
    menu_text = (
        "⭐ *AIELLO — IA STARBOXE 660 m²*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎬 *GÉNÉRER UN REEL* — Tap une discipline ci-dessous\n"
        "Vidéo 15s : Sora AI + voix ElevenLabs + avatar Aiello\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 *COMMANDES TEXTE :*\n\n"
        "/optimise `[texte]` — Optimiser un texte ou stratégie\n"
        "_Ex: /optimise Notre salle est grande_\n\n"
        "/rapport — Statistiques de la semaine\n\n"
        "/start — Afficher ce menu\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 *OU TAPE LIBREMENT* n importe quelle idée\n"
        "_Ex: Script vidéo 660 m2 pour Instagram_"
    )
    httpx.post(
        f"{TELEGRAM_API}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": menu_text,
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

            if text.startswith("/optimise") or text.startswith("/optimiser"):
                # Extraire le texte après la commande
                parts = text.split(" ", 1)
                to_optimize = parts[1].strip() if len(parts) > 1 else ""
                if not to_optimize:
                    send_message(chat_id,
                        "📝 Usage : /optimise [votre texte ou stratégie]\n\n"
                        "Exemple : /optimise Notre salle est super grande et on fait plein de sports"
                    )
                else:
                    send_message(chat_id, "🔍 Analyse en cours...")
                    try:
                        import json as _json
                        r = httpx.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                            json={
                                "model": "llama-3.3-70b-versatile",
                                "max_tokens": 600,
                                "messages": [
                                    {"role": "system", "content": OPTIMIZER_PROMPT},
                                    {"role": "user", "content": to_optimize},
                                ],
                            },
                            timeout=20,
                        )
                        result = r.json()["choices"][0]["message"]["content"]
                        send_message(chat_id, result)
                    except Exception as e:
                        send_message(chat_id, f"❌ Erreur : {str(e)[:100]}")
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

                        # Suppression sécurisée (Windows peut verrouiller le fichier brièvement)
                        import time as _time
                        for _attempt in range(5):
                            try:
                                os.unlink(video_path)
                                break
                            except OSError:
                                _time.sleep(0.5)
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
