import os
import subprocess
import tempfile
import textwrap
import httpx


PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "")


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


def create_reel(caption: str, accroche: str, hashtags: str, keyword: str) -> str:
    """
    Crée un Reel Instagram MP4 de 15 secondes.
    Retourne le chemin du fichier généré.
    """
    # 1. Télécharger la vidéo de fond
    bg_path = search_video(keyword)

    output = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name

    # Texte principal à afficher
    main_text = wrap_text(accroche)
    sub_text = wrap_text(caption[:120])

    # Échapper les guillemets pour FFmpeg
    def esc(s):
        return s.replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")

    main_esc = esc(main_text)
    sub_esc = esc(sub_text)

    if bg_path:
        # Avec vidéo de fond
        filters = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,trim=duration=15,setpts=PTS-STARTPTS,"
            f"colorchannelmixer=aa=0.7,"
            f"drawtext=fontsize=60:fontcolor=white:x=(w-text_w)/2:y=h*0.35:"
            f"text='{main_esc}':line_spacing=10:shadowcolor=black:shadowx=3:shadowy=3,"
            f"drawtext=fontsize=38:fontcolor=white:x=(w-text_w)/2:y=h*0.62:"
            f"text='{sub_esc}':line_spacing=8:shadowcolor=black:shadowx=2:shadowy=2[v]"
        )
        cmd = [
            "ffmpeg", "-y", "-i", bg_path,
            "-filter_complex", filters,
            "-map", "[v]", "-c:v", "libx264", "-t", "15",
            "-vf", "scale=1080:1920",
            "-pix_fmt", "yuv420p", output
        ]
    else:
        # Sans vidéo — fond dégradé noir/rouge
        filters = (
            f"color=c=0x1a0000:size=1080x1920:duration=15,"
            f"drawtext=fontsize=65:fontcolor=white:x=(w-text_w)/2:y=h*0.35:"
            f"text='{main_esc}':line_spacing=10:shadowcolor=#ff3300:shadowx=4:shadowy=4,"
            f"drawtext=fontsize=40:fontcolor=#ffcccc:x=(w-text_w)/2:y=h*0.62:"
            f"text='{sub_esc}':line_spacing=8[v]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-filter_complex", filters,
            "-map", "[v]", "-c:v", "libx264",
            "-pix_fmt", "yuv420p", output
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr[-500:]}")

    if bg_path and os.path.exists(bg_path):
        os.unlink(bg_path)

    return output
