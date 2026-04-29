import asyncio
import glob
import os
import random
import subprocess
import tempfile
import textwrap

import httpx
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "")
ELEVENLABS_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
# Charlie — Deep, Confident, Energetic (eleven_multilingual_v2 parle français)
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "IKne3meq5aSn9XLyUdCD")
VOICE = os.environ.get("TTS_VOICE", "fr-FR-HenriNeural")  # fallback Edge TTS
MUSIC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media", "background_music.mp3")
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media", "logo.png")


def _generate_elevenlabs(text: str, output_path: str) -> bool:
    """Génère une voix via ElevenLabs. Retourne True si succès."""
    if not ELEVENLABS_KEY:
        return False
    try:
        r = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
            headers={"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.4},
            },
            timeout=30,
        )
        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)
            return True
        print(f"ElevenLabs error {r.status_code}: {r.text[:100]}")
        return False
    except Exception as e:
        print(f"ElevenLabs exception: {e}")
        return False


async def _generate_edge_tts(text: str, output_path: str) -> None:
    import edge_tts
    tts = edge_tts.Communicate(text, VOICE)
    await tts.save(output_path)


def generate_voiceover(text: str) -> str | None:
    """Génère voix off — ElevenLabs en priorité, Edge TTS en fallback."""
    audio_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
    # Essayer ElevenLabs d'abord
    if ELEVENLABS_KEY and _generate_elevenlabs(text, audio_path):
        print("Voix: ElevenLabs (Charlie multilingual)")
        return audio_path
    # Fallback Edge TTS
    try:
        asyncio.run(_generate_edge_tts(text, audio_path))
        print("Voix: Edge TTS (fallback)")
        return audio_path
    except Exception as e:
        print(f"TTS error: {e}")
        return None
MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
# Seul ce sous-dossier contient des vidéos/images de fond — évite d'utiliser avatar/logo
BG_DIR = os.path.join(MEDIA_DIR, "backgrounds")
# Noms à exclure explicitement
EXCLUDED_FILES = {"avatar.jpg", "avatar_round.png", "avatar_card.png",
                  "logo.png", "logo_alt.png", "background_music.mp3", "README.txt"}


def pick_local_media(keyword: str) -> str | None:
    """Cherche uniquement dans media/backgrounds/ des vidéos de fond."""
    search_dir = BG_DIR if os.path.isdir(BG_DIR) else MEDIA_DIR
    all_media = []
    for ext in ("*.mp4", "*.mov"):  # Vidéos uniquement — pas d'images statiques
        all_media.extend(glob.glob(os.path.join(search_dir, ext)))
    # Exclure les fichiers systèmes
    all_media = [f for f in all_media if os.path.basename(f) not in EXCLUDED_FILES]
    if not all_media:
        return None
    matches = [f for f in all_media if keyword.lower() in os.path.basename(f).lower()]
    return random.choice(matches) if matches else random.choice(all_media)


def is_image(path: str) -> bool:
    return path.lower().endswith((".jpg", ".jpeg", ".png"))


def search_video(query: str) -> str | None:
    """Télécharge une vidéo Pexels et retourne le chemin local."""
    r = httpx.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": PEXELS_KEY},
        params={"query": query, "per_page": 3, "orientation": "portrait", "size": "small"},
        timeout=15,
    )
    videos = r.json().get("videos", [])
    if not videos:
        return None

    # Prendre le premier fichier HD portrait
    for v in videos:
        for f in v.get("video_files", []):
            if f.get("height", 0) >= 720 and f.get("width", 0) <= 720:
                url = f["link"]
                tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
                data = httpx.get(url, timeout=60, follow_redirects=True).content
                tmp.write(data)
                tmp.close()
                return tmp.name
    return None


def wrap_text(text: str, max_chars: int = 30) -> str:
    """Coupe le texte pour l'affichage vidéo."""
    lines = []
    for line in text.split("\n"):
        if len(line) <= max_chars:
            lines.append(line)
        else:
            lines.extend(textwrap.wrap(line, max_chars))
    return "\n".join(lines[:6])  # Max 6 lignes


def create_reel(caption: str, accroche: str, hashtags: str, keyword: str) -> tuple[str, str]:
    """
    Crée un Reel Instagram MP4 de 15 secondes.
    Retourne (chemin_fichier, source) — source = "local" | "pexels" | "gradient".
    """
    # Priorité : Sora AI → Pexels → gradient
    OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
    if OPENAI_KEY:
        try:
            from sora import generate_sora_video
            sora_prompt = (
                f"Cinematic vertical boxing gym video, 9:16 format. "
                f"{keyword} training session, dynamic movement, professional athlete, "
                f"Brest France boxing club atmosphere, motivational energy. "
                f"No text overlay. High quality."
            )
            sora_path = generate_sora_video(sora_prompt, duration=15)
            if sora_path:
                bg_path = sora_path
                source = "sora"
                delete_bg = True
            else:
                raise Exception("Sora returned None")
        except Exception as e:
            print(f"Sora fallback to Pexels: {e}")
            bg_path = search_video(keyword) if PEXELS_KEY else None
            source = "pexels" if bg_path else "gradient"
            delete_bg = bool(bg_path)
    elif PEXELS_KEY:
        bg_path = search_video(keyword)
        source = "pexels" if bg_path else "gradient"
        delete_bg = True
    else:
        bg_path = None
        source = "gradient"
        delete_bg = False

    output = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name

    def clean(s):
        """Supprime emojis, retours à la ligne et caractères spéciaux pour FFmpeg drawtext."""
        import re
        # Supprimer emojis et caractères non-ASCII
        s = s.encode("ascii", errors="ignore").decode("ascii")
        # Remplacer retours à la ligne par espace
        s = s.replace("\n", " ").replace("\r", " ")
        # Échapper pour FFmpeg
        s = s.replace("'", "\\'").replace(":", "\\:").replace("%", "\\%").replace("\\n", " ")
        # Limiter la longueur
        return s[:80]

    main_esc = clean(wrap_text(accroche))
    sub_esc = clean(caption[:100])

    text_filters = (
        f"drawtext=fontsize=60:fontcolor=white:x=(w-text_w)/2:y=h*0.35:"
        f"text='{main_esc}':line_spacing=10:shadowcolor=black:shadowx=3:shadowy=3,"
        f"drawtext=fontsize=38:fontcolor=white:x=(w-text_w)/2:y=h*0.62:"
        f"text='{sub_esc}':line_spacing=8:shadowcolor=black:shadowx=2:shadowy=2"
    )

    if bg_path and is_image(bg_path):
        # Photo locale → image fixe pendant 15s
        filters = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,eq=brightness=-0.2:contrast=1.1,{text_filters}[v]"
        )
        cmd = [
            FFMPEG_EXE, "-y", "-loop", "1", "-i", bg_path,
            "-filter_complex", filters,
            "-map", "[v]", "-c:v", "libx264", "-t", "15",
            "-pix_fmt", "yuv420p", output,
        ]
    elif bg_path:
        # Vidéo locale ou Pexels
        filters = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,trim=duration=15,setpts=PTS-STARTPTS,"
            f"eq=brightness=-0.25:contrast=1.1,{text_filters}[v]"
        )
        cmd = [
            FFMPEG_EXE, "-y", "-i", bg_path,
            "-filter_complex", filters,
            "-map", "[v]", "-c:v", "libx264", "-t", "15",
            "-pix_fmt", "yuv420p", output,
        ]
    else:
        # Aucun média — fond animé avec effet de pulsation (cercles qui s'expandent)
        filters = (
            f"color=c=0x0a0a0a:size=1080x1920:duration=15,format=yuv420p,"
            f"geq=r='if(lt(mod(hypot(X-W/2\\,Y-H/2)-t*60\\,120)\\,20)\\,200\\,10)':"
            f"g='10':b='if(lt(mod(hypot(X-W/2\\,Y-H/2)-t*60\\,120)\\,20)\\,10\\,10)',"
            f"drawtext=fontsize=65:fontcolor=white:x=(w-text_w)/2:y=h*0.35:"
            f"text='{main_esc}':line_spacing=10:shadowcolor=#ff3300:shadowx=4:shadowy=4,"
            f"drawtext=fontsize=40:fontcolor=#ffcccc:x=(w-text_w)/2:y=h*0.62:"
            f"text='{sub_esc}':line_spacing=8[v]"
        )
        cmd = [
            FFMPEG_EXE, "-y",
            "-filter_complex", filters,
            "-map", "[v]", "-c:v", "libx264",
            "-pix_fmt", "yuv420p", output,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr[-500:]}")

    # Avatar Aiello en bas à gauche
    try:
        from avatar import get_avatar_round
        avatar_path = get_avatar_round()
        if avatar_path and os.path.exists(avatar_path):
            avatar_out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
            av_cmd = [
                FFMPEG_EXE, "-y",
                "-i", output, "-i", avatar_path,
                "-filter_complex",
                "[1:v]scale=180:-1[av];"
                "[0:v][av]overlay=30:H-h-30[v]",
                "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", avatar_out,
            ]
            av_r = subprocess.run(av_cmd, capture_output=True, text=True)
            if av_r.returncode == 0:
                os.unlink(output)
                output = avatar_out
    except Exception:
        pass


    if delete_bg and bg_path and os.path.exists(bg_path):
        os.unlink(bg_path)

    # 1. Voix off (Henri Neural — voix masculine dynamique)
    voix_text = f"{accroche}. {caption[:120]}"
    audio_path = generate_voiceover(voix_text)

    # 2. Mixer voix + musique de fond avec ducking automatique
    final = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
    has_voice = audio_path and os.path.exists(audio_path)
    has_music = os.path.exists(MUSIC_PATH)

    if has_voice and has_music:
        # Voix en premier plan + musique à -18dB en fond (ducking)
        audio_cmd = [
            FFMPEG_EXE, "-y",
            "-i", output,
            "-i", audio_path,
            "-i", MUSIC_PATH,
            "-filter_complex",
            "[2:a]volume=0.12,atrim=duration=15[music];"
            "[1:a][music]amix=inputs=2:duration=first:weights=1 0.15[audio]",
            "-map", "0:v", "-map", "[audio]",
            "-c:v", "copy", "-c:a", "aac", "-shortest", final,
        ]
    elif has_voice:
        audio_cmd = [
            FFMPEG_EXE, "-y",
            "-i", output, "-i", audio_path,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-shortest", final,
        ]
    elif has_music:
        audio_cmd = [
            FFMPEG_EXE, "-y",
            "-i", output, "-i", MUSIC_PATH,
            "-filter_complex", "[1:a]volume=0.18,atrim=duration=15[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-shortest", final,
        ]
    else:
        audio_cmd = None

    if audio_cmd:
        r = subprocess.run(audio_cmd, capture_output=True, text=True)
        if r.returncode != 0:
            final = output  # fallback silencieux
    else:
        final = output

    # 3. Watermark logo si disponible
    if os.path.exists(LOGO_PATH) and final != output:
        watermarked = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
        wm_cmd = [
            FFMPEG_EXE, "-y",
            "-i", final, "-i", LOGO_PATH,
            "-filter_complex",
            "[1:v]scale=200:-1,format=rgba,colorchannelmixer=aa=0.7[logo];"
            "[0:v][logo]overlay=W-w-30:H-h-80[v]",
            "-map", "[v]", "-map", "0:a?",
            "-c:v", "libx264", "-c:a", "copy", "-pix_fmt", "yuv420p", watermarked,
        ]
        wr = subprocess.run(wm_cmd, capture_output=True, text=True)
        if wr.returncode == 0:
            if final != output:
                os.unlink(final)
            final = watermarked

    # Nettoyage
    if audio_path and os.path.exists(audio_path):
        os.unlink(audio_path)
    if delete_bg and bg_path and os.path.exists(bg_path):
        os.unlink(bg_path)

    return final, source
