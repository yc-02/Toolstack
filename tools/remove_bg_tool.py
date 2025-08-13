# remove_bg_tool.py
import io
from typing import Tuple
from PIL import Image, ImageOps, ImageFilter
from rembg import remove as rembg_remove, new_session

# cache sessions per (model_name)
_sessions = {}

def get_session(model_name: str = "u2net"):  # default to faster model
    if model_name not in _sessions:
        _sessions[model_name] = new_session(model_name)
    return _sessions[model_name]


def _pre_downscale(raw_bytes: bytes, longest: int) -> bytes:
    """Downscale the image BEFORE rembg to limit pixels processed."""
    if longest <= 0:
        return raw_bytes
    im = Image.open(io.BytesIO(raw_bytes))
    im = ImageOps.exif_transpose(im)
    w, h = im.size
    scale_from = max(w, h)
    if scale_from <= longest:
        # already small enough
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        buf.seek(0)
        return buf.getvalue()
    s = float(longest) / float(scale_from)
    nw, nh = int(w * s), int(h * s)
    im = im.resize((nw, nh), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def remove_bg(
    raw_bytes: bytes,
    max_width: int = 0,  # output width cap; 0 keeps model-output size
    quality: str = "high",  # "fast" (no matting) | "high" (matting)
    model: str = "u2net",  # "u2netp" (fastest), "u2net" (fast), "isnet-general-use" (best)
    feather_px: float = 0.5,  # tiny edge soften; set 0 to disable
    longest_side_in: int = 1280,  # *** preprocess cap BEFORE rembg ***
    png_compress_level: int = 6,  # 0=fastest, 9=smallest
) -> Tuple[bytes, Image.Image]:
    """
    Speed-optimized background removal.
    - Pre-downscales input to reduce compute (longest_side_in).
    - Optional alpha-matting via `quality="high"`.
    - Caps output width with `max_width` (no upscaling).
    """
    # 1) Pre-downscale to cut inference time massively
    pre_bytes = _pre_downscale(raw_bytes, longest=longest_side_in)

    # 2) Session (cached)
    session = get_session(model)

    # 3) Rembg (bytes in → bytes out)
    use_matting = quality == "high"
    cut_bytes = rembg_remove(
        pre_bytes,
        session=session,
        alpha_matting=use_matting,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=10,
    )

    # 4) Open result for optional feather + resize
    out = Image.open(io.BytesIO(cut_bytes)).convert("RGBA")

    # tiny edge feather (after inference, before final save)
    if feather_px and feather_px > 0:
        out.putalpha(out.getchannel("A").filter(ImageFilter.GaussianBlur(feather_px)))

    # 5) Output size policy (width-capped, no upscaling)
    if max_width > 0 and out.width > max_width:
        nh = int(out.height * (max_width / out.width))
        out = out.resize((max_width, nh), Image.LANCZOS)

    # 6) Encode PNG (avoid heavy optimize)
    buf = io.BytesIO()
    out.save(buf, format="PNG", compress_level=png_compress_level)
    buf.seek(0)
    return buf.getvalue(), out
