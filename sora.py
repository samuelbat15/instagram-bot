"""
Génération vidéo via OpenAI Sora API.
Modèles disponibles : sora-2, sora-2-pro
"""
import os
import time
import tempfile
import httpx

OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
SORA_MODEL = os.environ.get("SORA_MODEL", "sora-2")
API_BASE = "https://api.openai.com/v1"


def generate_sora_video(prompt: str, duration: int = 15) -> str | None:
    """
    Génère une vidéo via Sora et retourne le chemin du fichier MP4.
    Format : 1080x1920 (portrait Instagram Reels).
    """
    if not OPENAI_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json",
    }

    # Lancer la génération
    try:
        resp = httpx.post(
            f"{API_BASE}/video/generations",
            headers=headers,
            json={
                "model": SORA_MODEL,
                "prompt": prompt,
                "n": 1,
                "size": "1080x1920",
                "duration": duration,
            },
            timeout=30,
        )
        data = resp.json()

        if "error" in data:
            print(f"Sora error: {data['error'].get('message', data['error'])}")
            return None

        # Récupérer l'ID de génération
        gen_id = data.get("id") or (data.get("data", [{}])[0].get("id"))
        if not gen_id:
            # Réponse synchrone directe
            return _extract_video(data)

        # Polling asynchrone
        return _poll_and_download(gen_id, headers)

    except Exception as e:
        print(f"Sora exception: {e}")
        return None


def _poll_and_download(gen_id: str, headers: dict, max_wait: int = 120) -> str | None:
    """Attend la fin de génération et télécharge la vidéo."""
    start = time.time()
    while time.time() - start < max_wait:
        try:
            r = httpx.get(f"{API_BASE}/video/generations/{gen_id}", headers=headers, timeout=15)
            data = r.json()
            status = data.get("status", "")

            if status == "succeeded":
                return _extract_video(data)
            elif status in ("failed", "cancelled"):
                print(f"Sora generation {status}: {data.get('error', '')}")
                return None

            time.sleep(5)
        except Exception as e:
            print(f"Sora poll error: {e}")
            time.sleep(5)

    print("Sora timeout")
    return None


def _extract_video(data: dict) -> str | None:
    """Extrait et télécharge la vidéo depuis la réponse."""
    # Chercher l'URL vidéo dans différents formats de réponse
    url = None
    if "data" in data and isinstance(data["data"], list):
        for item in data["data"]:
            url = item.get("url") or item.get("video_url")
            if url:
                break
    url = url or data.get("url") or data.get("video_url")

    if not url:
        print(f"Sora: pas d'URL vidéo dans la réponse: {list(data.keys())}")
        return None

    # Télécharger la vidéo
    try:
        r = httpx.get(url, timeout=120, follow_redirects=True)
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp.write(r.content)
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f"Sora download error: {e}")
        return None
