"""
Création et intégration de l'avatar rond d'Aiello Batonon dans les vidéos.
Génère : avatar_round.png (cercle) + avatar_card.png (carte profil avec nom)
"""
import os
from PIL import Image, ImageDraw, ImageFont
import subprocess
import tempfile

MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
AVATAR_SRC = os.path.join(MEDIA_DIR, "avatar.jpg")
AVATAR_ROUND = os.path.join(MEDIA_DIR, "avatar_round.png")
AVATAR_CARD = os.path.join(MEDIA_DIR, "avatar_card.png")


def create_round_avatar(size: int = 300) -> str | None:
    """Crée un avatar circulaire depuis avatar.jpg."""
    if not os.path.exists(AVATAR_SRC):
        return None
    img = Image.open(AVATAR_SRC).convert("RGBA")
    # Crop carré centré
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 4  # Légèrement vers le haut pour centrer le visage
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((size, size), Image.LANCZOS)
    # Masque circulaire
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    # Bordure rouge Star Boxe
    border = Image.new("RGBA", (size + 12, size + 12), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)
    border_draw.ellipse((0, 0, size + 12, size + 12), fill=(220, 30, 30, 255))
    border.paste(img, (6, 6), mask)
    border.save(AVATAR_ROUND, "PNG")
    return AVATAR_ROUND


def create_avatar_card() -> str | None:
    """Crée une carte 'Coach Aiello — Champion du Monde' pour overlay vidéo."""
    if not os.path.exists(AVATAR_SRC):
        return None

    round_path = create_round_avatar(200)
    if not round_path:
        return None

    # Carte horizontale : avatar + texte
    card = Image.new("RGBA", (700, 240), (0, 0, 0, 180))
    avatar = Image.open(round_path).convert("RGBA").resize((200, 200))
    card.paste(avatar, (20, 20), avatar)

    draw = ImageDraw.Draw(card)
    # Nom
    draw.text((240, 50), "Aiello Batonon", fill=(255, 255, 255, 255),
              font=ImageFont.load_default())
    # Titre
    draw.text((240, 90), "🏆 Champion du Monde", fill=(220, 180, 30, 255),
              font=ImageFont.load_default())
    draw.text((240, 125), "Boxe Thaï WPMF -75kg", fill=(200, 200, 200, 255),
              font=ImageFont.load_default())
    # Logo texte
    draw.text((240, 165), "⭐ STAR BOXE COACHING", fill=(220, 30, 30, 255),
              font=ImageFont.load_default())
    draw.text((240, 195), "📍 Brest | @starboxe29", fill=(180, 220, 255, 255),
              font=ImageFont.load_default())

    card.save(AVATAR_CARD, "PNG")
    return AVATAR_CARD


def get_avatar_round() -> str | None:
    """Retourne l'avatar rond, le crée si nécessaire."""
    if not os.path.exists(AVATAR_ROUND):
        return create_round_avatar()
    return AVATAR_ROUND


def get_avatar_card() -> str | None:
    """Retourne la carte avatar, la crée si nécessaire."""
    if not os.path.exists(AVATAR_CARD):
        return create_avatar_card()
    return AVATAR_CARD


if __name__ == "__main__":
    r = create_round_avatar()
    c = create_avatar_card()
    print(f"Avatar rond : {r}")
    print(f"Avatar carte : {c}")
