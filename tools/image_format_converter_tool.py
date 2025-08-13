# image_format_converter_tool.py
import io
from typing import Tuple, Optional, Tuple as _Tuple
from PIL import Image, ImageOps
import pillow_heif

pillow_heif.register_heif_opener()

_WRITABLE = {"PNG", "JPEG", "JPG", "WEBP", "HEIF"}
_ALPHA_OK = {"PNG", "WEBP", "HEIF"}


def _normalize_format(fmt: str) -> str:
    if not fmt:
        raise ValueError("to_format must be a non-empty string.")
    f = fmt.strip().upper()
    if f == "JPG":
        f = "JPEG"
    if f not in _WRITABLE:
        raise ValueError(
            f"Unsupported output format '{fmt}'. Supported: {sorted(_WRITABLE)}"
        )
    return f


def _has_alpha(img: Image.Image) -> bool:
    if img.mode in ("RGBA", "LA", "PA"):
        return True
    return "transparency" in img.info


def _flatten_on_bg(img: Image.Image, bg: _Tuple[int, int, int]) -> Image.Image:
    """
    Flattens any transparency against a solid background color.
    Keeps orientation already applied.
    """
    if img.mode in ("LA", "L"):
        img = img.convert("RGBA")  # ensure alpha channel behaves consistently
    elif img.mode == "P":
        # paletted images may have transparency in info; RGBA normalizes it
        img = img.convert("RGBA")
    elif img.mode != "RGBA":
        # e.g. CMYK with alpha is rare; convert to RGBA to normalize
        try:
            img = img.convert("RGBA")
        except Exception:
            pass

    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, bg)
        # alpha_composite requires two RGBA images; compose then drop alpha
        bg_rgba = Image.new("RGBA", img.size, (*bg, 255))
        composed = Image.alpha_composite(bg_rgba, img)
        return composed.convert("RGB")
    # If we got here without RGBA, no alpha found; just ensure RGB
    return img.convert("RGB")


def image_format_converter(
    to_format: str = "png",
    raw_bytes: bytes = b"",
    max_width: int = 0,
    *,
    flatten_bg: _Tuple[int, int, int] = (
        255,
        255,
        255,
    ),  # background used only if needed
) -> Tuple[str, bytes, Image.Image]:
    """
    Convert input image bytes to the selected format.

    - Transparency is preserved for PNG/WEBP/HEIF.
    - For formats without alpha (e.g., JPEG), transparency is automatically flattened
      onto `flatten_bg` (default white) instead of raising an error.
    - If `max_width` > 0 and the image is wider than `max_width`, it is resized
      proportionally using bicubic resampling.
    - EXIF orientation is respected; EXIF and ICC are preserved when possible.

    Returns:
        (final_format: str, out_bytes: bytes, final_image: PIL.Image.Image)
    """
    if not isinstance(raw_bytes, (bytes, bytearray)) or len(raw_bytes) == 0:
        raise ValueError("raw_bytes must be non-empty bytes.")

    out_format = _normalize_format(to_format)

    # Open and auto-apply EXIF orientation
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img)

    # Optional resize (keep aspect ratio)
    if max_width and img.width > max_width:
        new_height = int(round(img.height * (max_width / img.width)))
        img = img.resize((max_width, new_height), Image.BICUBIC)

    # Prepare save parameters per format
    save_kwargs = {}
    if out_format == "PNG":
        save_kwargs.update(dict(format="PNG", optimize=True))

    elif out_format == "WEBP":
        save_kwargs.update(dict(format="WEBP", quality=95, method=6))

    elif out_format == "JPEG":
        # If image has alpha, flatten onto background; otherwise ensure RGB
        if _has_alpha(img):
            img = _flatten_on_bg(img, flatten_bg)
        elif img.mode != "RGB":
            img = img.convert("RGB")
        save_kwargs.update(
            dict(
                format="JPEG",
                quality=95,
                subsampling="4:4:4",
                progressive=True,
                optimize=True,
            )
        )

    elif out_format == "HEIF":
        save_kwargs.update(dict(format="HEIF", quality=90))

    # Try to preserve metadata where supported
    exif = img.info.get("exif")
    if exif:
        save_kwargs["exif"] = exif
    icc = img.info.get("icc_profile")
    if icc:
        save_kwargs["icc_profile"] = icc

    # Save to memory
    out_buf = io.BytesIO()
    img.save(out_buf, **save_kwargs)
    out_buf.seek(0)

    return out_format.lower(), out_buf.getvalue(), img
