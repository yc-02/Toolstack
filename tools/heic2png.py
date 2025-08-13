# heic2png.py
import io
from typing import Tuple
from PIL import Image
import pillow_heif

# Enable HEIC/HEIF for Pillow once
pillow_heif.register_heif_opener()


def convert_heic_to_png_bytes(
    raw_bytes: bytes,
    max_width: int = 0,
) -> Tuple[bytes, Image.Image]:
    """
    Convert HEIC bytes to PNG bytes without touching background/transparency.
    Only resizes if max_width > 0.
    Returns (png_bytes, preview_image).
    """
    img = Image.open(io.BytesIO(raw_bytes))

    # Optional resize while keeping aspect ratio
    if max_width > 0 and img.width > max_width:
        h = int(img.height * (max_width / img.width))
        img = img.resize((max_width, h), Image.BICUBIC)

    # Save to PNG in-memory (preserve whatever mode it currently has)
    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    out.seek(0)

    return out.getvalue(), img
