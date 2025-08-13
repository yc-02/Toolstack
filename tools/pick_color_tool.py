import io
from PIL import Image, ImageCms

def to_srgb(img: Image.Image) -> Image.Image:
    try:
        icc = img.info.get("icc_profile")
        if icc:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            dst = ImageCms.createProfile("sRGB")
            return ImageCms.profileToProfile(img, src, dst, outputMode="RGBA")
    except Exception:
        pass
    return img.convert("RGBA")


def rgba_to_hex_over_bg(r, g, b, a, bg=(255, 255, 255)) -> str:
    if a == 255:
        return f"#{r:02X}{g:02X}{b:02X}"
    rb = int(round((r * a + bg[0] * (255 - a)) / 255))
    gb = int(round((g * a + bg[1] * (255 - a)) / 255))
    bb = int(round((b * a + bg[2] * (255 - a)) / 255))
    return f"#{rb:02X}{gb:02X}{bb:02X}"



