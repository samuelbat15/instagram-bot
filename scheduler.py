"""
Scheduling automatique des posts — lundi, mercredi, vendredi a 18h.
Lance en thread daemon depuis bot.py.
"""
import os
import random
import threading
import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN_INSTA", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Disciplines en rotation automatique
AUTO_DISCIPLINES = [
    ("boxing muay thai", "Reel cours de boxe thaï avec Aiello champion du monde"),
    ("MMA fighter training", "Reel MMA entrainement intensif Star Boxe"),
    ("fitness workout gym", "Reel cours de musculation et cardio Star Boxe"),
    ("yoga meditation", "Reel yoga et bien-etre Star Boxe Brest"),
    ("pilates workout", "Reel pilates renforcement musculaire"),
    ("EMS electrostimulation", "Reel Miha Bodytec electrostimulation 20 minutes"),
    ("personal trainer coaching", "Reel coaching personnalise Aiello champion"),
    ("cardio fitness intense", "Reel cardio haute intensite Star Boxe"),
]


def _notify(msg: str):
    if ADMIN_CHAT_ID and BOT_TOKEN:
        try:
            httpx.post(f"{TELEGRAM_API}/sendMessage",
                       json={"chat_id": ADMIN_CHAT_ID, "text": msg}, timeout=10)
        except Exception:
            pass


def auto_post():
    """Genere et publie un Reel automatiquement."""
    keyword, prompt = random.choice(AUTO_DISCIPLINES)
    print(f"[Scheduler] Auto-post: {prompt}")
    _notify(f"🤖 Scheduling: génération automatique en cours...\n{prompt}")

    try:
        import json
        import bot
        data = bot.generate_content(prompt)

        if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("PEXELS_API_KEY"):
            _notify("⚠️ Scheduler: pas de clé Sora/Pexels — post textuel uniquement")
        else:
            from video import create_reel
            FFMPEG_OK = False
            try:
                import imageio_ffmpeg; imageio_ffmpeg.get_ffmpeg_exe(); FFMPEG_OK = True
            except Exception:
                pass

            if FFMPEG_OK:
                video_path, source = create_reel(
                    data["caption"], data["accroche"], data["hashtags"], keyword
                )
                # Auto-post Instagram
                insta_url = ""
                instagram_user = os.environ.get("INSTAGRAM_USER", "")
                if instagram_user:
                    from instagram import post_reel
                    insta_url = post_reel(video_path, data["caption"], data["hashtags"]) or ""

                # Analytics
                from analytics import log_post
                log_post(keyword, source, data.get("accroche", ""), insta_url, "scheduled")

                msg = f"✅ Post automatique publié !\nSource: {source}"
                if insta_url:
                    msg += f"\nInstagram: {insta_url}"
                _notify(msg)
                os.unlink(video_path)

    except Exception as e:
        print(f"[Scheduler] Erreur: {e}")
        _notify(f"❌ Erreur scheduling: {str(e)[:150]}")


def start_scheduler():
    """Demarre le scheduler en background thread."""
    scheduler = BackgroundScheduler(timezone="Europe/Paris")
    # Lundi, Mercredi, Vendredi a 18h00 — misfire_grace_time=600s pour rattraper si PC dormait
    scheduler.add_job(
        auto_post,
        CronTrigger(day_of_week="mon,wed,fri", hour=18, minute=0),
        misfire_grace_time=600,
        max_instances=1,
        id="auto_post_18h",
        replace_existing=True,
    )
    scheduler.start()
    print("[Scheduler] Actif — posts automatiques lun/mer/ven 18h00 (heure Paris)")
    return scheduler
