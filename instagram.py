"""
Auto-post vers Instagram via instagrapi (sans Facebook Developer).
Usage : configure INSTAGRAM_USER et INSTAGRAM_PASS dans les variables d'env.
"""
import os
import time

INSTAGRAM_USER = os.environ.get("INSTAGRAM_USER", "")
INSTAGRAM_PASS = os.environ.get("INSTAGRAM_PASS", "")


def get_client():
    from instagrapi import Client
    cl = Client()
    cl.delay_range = [2, 5]  # délai humain entre les actions
    session_file = os.path.join(os.path.dirname(__file__), ".instagram_session.json")
    if os.path.exists(session_file):
        try:
            cl.load_settings(session_file)
            cl.login(INSTAGRAM_USER, INSTAGRAM_PASS)
            return cl
        except Exception:
            pass
    cl.login(INSTAGRAM_USER, INSTAGRAM_PASS)
    cl.dump_settings(session_file)
    return cl


def post_reel(video_path: str, caption: str, hashtags: str) -> str | None:
    """Publie un Reel sur Instagram. Retourne l'URL du post ou None si erreur."""
    if not INSTAGRAM_USER or not INSTAGRAM_PASS:
        return None
    try:
        cl = get_client()
        full_caption = f"{caption}\n\n{hashtags[:300]}"
        media = cl.clip_upload(video_path, full_caption)
        return f"https://www.instagram.com/reel/{media.code}/"
    except Exception as e:
        print(f"Instagram post error: {e}")
        return None


def post_story(video_path: str) -> bool:
    """Publie une Story sur Instagram."""
    if not INSTAGRAM_USER or not INSTAGRAM_PASS:
        return False
    try:
        cl = get_client()
        cl.video_upload_to_story(video_path)
        return True
    except Exception as e:
        print(f"Instagram story error: {e}")
        return False
