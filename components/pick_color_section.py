import time
import streamlit as st
from PIL import Image, ImageOps
from tools.pick_color_tool import rgba_to_hex_over_bg, to_srgb
try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except Exception:
    pass

from streamlit_image_coordinates import streamlit_image_coordinates


def pick_color_section():
    # session defaults
    st.session_state.setdefault("pick_color_key", f"pick-color-uploader-{time.time()}")
    st.session_state.setdefault("pick_color", None)  # will hold a single dict or None

    st.title("Click to pick a color")

    file = st.file_uploader(
        "Upload an image",
        type=["png", "jpg", "jpeg", "webp", "heic", "heif"],
        key=st.session_state.pick_color_key,
    )

    has_file = file is not None
    has_result = st.session_state["pick_color"] is not None

    if st.button("Clear uploads/result", disabled=not (has_file or has_result)):
        st.session_state["pick_color"] = None
        st.session_state["pick_color_key"] = f"pick-color-uploader-{time.time()}"
        st.rerun()

    if not has_file:
        return

    st.info("Click the image to pick a color")
    try:
        img = Image.open(file)
    except Exception as e:
        st.error(f"Could not open image: {e}")
        return

    img = ImageOps.exif_transpose(img)
    img = to_srgb(img)

    ow, oh = img.width, img.height

    # contain into a max box
    MAX_W, MAX_H = 900, 600
    scale = min(MAX_W / ow, MAX_H / oh)
    display_w = max(1, int(round(ow * scale)))
    display_h = max(1, int(round(oh * scale)))

    # mapping factors
    scale_x = ow / float(display_w)
    scale_y = oh / float(display_h)

    col1, col2 = st.columns([2, 1])
    with col1:
        coords = streamlit_image_coordinates(
            img,
            width=display_w,
            key="img-coords-contained",
        )

    with col2:
        # update single result on click
        if coords and "x" in coords and "y" in coords:
            disp_x, disp_y = coords["x"], coords["y"]
            px = max(0, min(ow - 1, int(round(disp_x * scale_x))))
            py = max(0, min(oh - 1, int(round(disp_y * scale_y))))
            r, g, b, a = img.getpixel((px, py))
            hex_over_white = rgba_to_hex_over_bg(r, g, b, a, bg=(255, 255, 255))

            st.session_state["pick_color"] = {
                "name": getattr(file, "name", "uploaded"),
                "x": px,
                "y": py,
                "hex_over_white": hex_over_white,
                "rgb": (r, g, b),
                "rgba": (r, g, b, a),
            }

        # display the single stored result
        result = st.session_state["pick_color"]
        if result:
            sw, vals = st.columns([1, 2])
            with sw:
                st.markdown(
                    f"""
                    <div style="
                        width: 100%;
                        height: 64px;
                        border-radius: 10px;
                        border: 1px solid #ddd;
                        background: {result['hex_over_white']};
                    "></div>
                    """,
                    unsafe_allow_html=True,
                )
            with vals:
                st.write(f"**Pixel:** ({result['x']}, {result['y']})")
                st.write(f"**HEX (over white):** `{result['hex_over_white']}`")
                st.write(f"**RGB (raw):** {result['rgb']}")
                st.write(f"**RGBA (raw):** {result['rgba']}")
