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
VOICE = os.environ.get("TTS_VOICE", "fr-FR-DeniseNeural")


async def _generate_tts(text: str, output_path: str) -> None:
    import edge_tts
    tts = edge_tts.Communicate(text, VOICE)
    await tts.save(output_path)


def generate_voiceover(text: str) -> str | None:
    """Génère un fichier MP3 de voix off et retourne son chemin."""
    try:
        audio_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        asyncio.run(_generate_tts(text, audio_path))
        return audio_path
    except Exception as e:
        print(f"TTS error: {e}")
        return None
MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")


def pick_local_media(keyword: str) -> str | None:
    """Cherche dans media/ un fichier contenant le keyword, sinon prend un aléatoire."""
    if not os.path.isdir(MEDIA_DIR):
        return None
    all_media = []
    for ext in ("*.mp4", "*.mov", "*.jpg", "*.jpeg", "*.png"):
        all_media.extend(glob.glob(os.path.join(MEDIA_DIR, ext)))
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
    # Média local en priorité, Pexels en fallback
    local_path = pick_local_media(keyword)
    if local_path:
        bg_path = local_path
        source = "local"
        delete_bg = False
    elif PEXELS_KEY:
        bg_path = search_video(keyword)
        source = "pexels" if bg_path else "gradient"
        delete_bg = True
    else:
        bg_path = None
        source = "gradient"
        delete_bg = False

    output = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name

    def esc(s):
        return s.replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")

    main_esc = esc(wrap_text(accroche))
    sub_esc = esc(wrap_text(caption[:120]))

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
            f"crop=1080:1920,colorchannelmixer=aa=0.75,{text_filters}[v]"
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
            f"colorchannelmixer=aa=0.7,{text_filters}[v]"
        )
        cmd = [
            FFMPEG_EXE, "-y", "-i", bg_path,
            "-filter_complex", filters,
            "-map", "[v]", "-c:v", "libx264", "-t", "15",
            "-pix_fmt", "yuv420p", output,
        ]
    else:
        # Aucun média — fond dégradé noir/rouge
        filters = (
            f"color=c=0x1a0000:size=1080x1920:duration=15,"
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

    if delete_bg and bg_path and os.path.exists(bg_path):
        os.unlink(bg_path)

    # Générer et mixer la voix off
    voix_text = f"{accroche}. {caption[:100]}"
    audio_path = generate_voiceover(voix_text)
    if audio_path and os.path.exists(audio_path):
        final = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
        mix_cmd = [
            FFMPEG_EXE, "-y",
            "-i", output,
            "-i", audio_path,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            final,
        ]
        mix_result = subprocess.run(mix_cmd, capture_output=True, text=True)
        os.unlink(output)
        os.unlink(audio_path)
        if mix_result.returncode == 0:
            return final, source
        # Si merge échoue, retourner la vidéo sans son
        return final if os.path.exists(final) else output, source

    return output, source
