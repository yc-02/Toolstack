# app.py
import os, shutil, subprocess, tempfile, time, base64
from io import BytesIO

import streamlit as st
from streamlit.components.v1 import html as html_comp

# Your existing helpers/modules
try:
    from helpers import run_in_thread
except Exception:
    # Fallback: tiny thread helper if your helpers.py isn't present
    import concurrent.futures

    _EXEC = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def run_in_thread(fn, *args, **kwargs):
        return _EXEC.submit(fn, *args, **kwargs)


from heic2png import convert_heic_to_png_bytes
from remove_bg import remove_bg, get_session  # requires rembg + onnxruntime

st.set_page_config(page_title="Toolstack", page_icon="🎨", layout="wide")

# ---------------- Session defaults ----------------
if "tool" not in st.session_state:
    st.session_state.tool = "HEIC → PNG"

if "heic_results" not in st.session_state:
    st.session_state.heic_results = []
if "bg_results" not in st.session_state:
    st.session_state.bg_results = []
if "svg_results" not in st.session_state:
    st.session_state.svg_results = []

if "heic_key" not in st.session_state:
    st.session_state.heic_key = "heic-uploader-0"
if "bg_key" not in st.session_state:
    st.session_state.bg_key = "bg-uploader-0"
if "svg_key" not in st.session_state:
    st.session_state.svg_key = "svg-uploader-0"

# ---------------- Sidebar ----------------
st.sidebar.title("Images")


def set_tool(name: str):
    st.session_state.tool = name


st.sidebar.button(
    "HEIC to PNG", use_container_width=True, on_click=set_tool, args=("HEIC → PNG",)
)
st.sidebar.button(
    "Background Remover",
    use_container_width=True,
    on_click=set_tool,
    args=("Background Remover",),
)
st.sidebar.button(
    "PNG → SVG", use_container_width=True, on_click=set_tool, args=("PNG → SVG",)
)

st.sidebar.title("Files")
st.sidebar.button(
    "File Converter",
    use_container_width=True,
    on_click=set_tool,
    args=("File Converter",),
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Active tool: **{st.session_state.tool}**")

tool = st.session_state.tool


# ---------------- Node imagetracer bridge ----------------
def have_node() -> bool:
    return shutil.which("node") is not None


def path_convert_mjs() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "convert.mjs")


def trace_with_imagetracer_node(
    raw_bytes: bytes,
    *,
    mode: str = "fidelity",  # "fidelity" | "poster"
    layers: int = 8,
    upscale: int = 1,
    preblur: float = 0.0,
    median: int = 0,
    mergecolors: int = 0,  # ΔRGB 0–255
    dropwhite: bool = False,
    svgo: bool = True,
    palette_hex_csv: str | None = None,
) -> bytes:
    mjs = path_convert_mjs()
    if not os.path.exists(mjs):
        raise FileNotFoundError(f"convert.mjs not found at {mjs}")
    with tempfile.TemporaryDirectory() as td:
        inp = os.path.join(td, "in.png")
        out = os.path.join(td, "out.svg")
        with open(inp, "wb") as f:
            f.write(raw_bytes)

        args = [
            "node",
            mjs,
            inp,
            out,
            f"--mode={mode}",
            f"--layers={int(max(2,layers))}",
        ]
        if upscale and int(upscale) > 1:
            args.append(f"--upscale={int(upscale)}")
        if preblur and float(preblur) > 0:
            args.append(f"--preblur={float(preblur)}")
        if median and int(median) > 0:
            args.append(f"--median={int(median)}")
        if mergecolors and int(mergecolors) > 0:
            args.append(f"--mergecolors={int(mergecolors)}")
        if dropwhite:
            args.append("--dropwhite")
        if svgo:
            args.append("--svgo")
        if palette_hex_csv:
            args.append(f"--palette={palette_hex_csv}")

        res = subprocess.run(args, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"imagetracer failed:\n{res.stdout}\n{res.stderr}")

        return open(out, "rb").read()


def embed_svg(svg_bytes: bytes):
    import base64, streamlit as st

    b64 = base64.b64encode(svg_bytes).decode("utf-8")
    st.markdown(
        f"""
        <div style="width:100%;">
          <img src="data:image/svg+xml;base64,{b64}"
               style="width:100%; height:auto; display:block; margin:0; padding:0;" />
        </div>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================
# HEIC → PNG
# =====================================================================
if tool == "HEIC → PNG":
    st.title("HEIC → PNG Converter")

    resize_enabled = st.toggle("Enable resize", value=False)
    max_width = (
        st.number_input(
            "Max width (px)", min_value=0, value=300, help="0 = original size"
        )
        if resize_enabled
        else 0
    )

    files = st.file_uploader(
        "Choose HEIC/HEIF files",
        type=["heic", "HEIC", "heif", "HEIF"],
        accept_multiple_files=True,
        key=st.session_state.heic_key,
    )

    if files and st.button("Clear uploads & results  (Click for re-upload)"):
        st.session_state.heic_results = []
        st.session_state.heic_key = f"heic-uploader-{time.time()}"
        st.rerun()

    if files and not st.session_state.heic_results:
        total = len(files)
        status_placeholder = st.empty()

        for idx, f in enumerate(files, start=1):
            raw = f.read()
            status_placeholder.markdown(f"**Converting {idx} / {total}:** {f.name}")

            progress = st.progress(0, text="Starting…")
            future = run_in_thread(convert_heic_to_png_bytes, raw, max_width)
            pct = 10
            while not future.done():
                pct = min(pct + 2, 95)
                progress.progress(pct, text="Converting HEIC to PNG…")
                time.sleep(0.05)

            png_bytes, preview_img = future.result()
            progress.progress(100, text="Done")
            time.sleep(0.1)
            progress.empty()

            thumb = preview_img.copy()
            thumb.thumbnail((900, 900))
            buf = BytesIO()
            thumb.save(buf, format="PNG")
            thumb_bytes = buf.getvalue()

            st.session_state.heic_results.append(
                {
                    "name": f.name.rsplit(".", 1)[0] + ".png",
                    "bytes": png_bytes,
                    "preview": thumb_bytes,
                    "width": preview_img.width,
                    "height": preview_img.height,
                }
            )
        status_placeholder.empty()

    if st.session_state.heic_results:
        for i, r in enumerate(st.session_state.heic_results, start=1):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{i}. {r['name']}")
                st.caption(f"{r['width']} × {r['height']} px")
            with col2:
                st.download_button(
                    "⬇ Download",
                    data=r["bytes"],
                    file_name=r["name"],
                    mime="image/png",
                    key=f"dl-heic-{i}-{r['name']}",
                    use_container_width=True,
                )
            st.image(r["preview"], use_container_width=True)
            st.divider()


# =====================================================================
# Background Remover
# =====================================================================
elif tool == "Background Remover":
    st.title("Background Remover")

    @st.cache_resource
    def warm_session():
        return get_session("isnet-general-use")

    warm_session()

    resize_enabled = st.toggle("Enable resize", value=False)
    max_width = (
        st.number_input(
            "Max width (px)", min_value=0, value=300, help="0 = original size"
        )
        if resize_enabled
        else 0
    )

    files = st.file_uploader(
        "Choose images",
        type=["png", "jpg", "jpeg", "webp", "heic", "HEIC", "heif", "HEIF"],
        accept_multiple_files=True,
        key=st.session_state.bg_key,
    )
    
    if files and st.button("Clear uploads & results  (Click for re-upload)"):
        st.session_state.heic_results = []
        st.session_state.heic_key = f"heic-uploader-{time.time()}"
        st.rerun()

    if files and not st.session_state.bg_results:
        total = len(files)
        status_placeholder = st.empty()
        for idx, f in enumerate(files, start=1):
            raw = f.read()
            status_placeholder.markdown(
                f"**Removing background {idx} / {total}:** {f.name}"
            )

            progress = st.progress(0, text="Starting…")
            future = run_in_thread(remove_bg, raw, max_width)
            pct = 10
            while not future.done():
                pct = min(pct + 2, 98)
                progress.progress(pct, text="Running rembg…")
                time.sleep(0.05)

            png_bytes, preview_img = future.result()
            progress.progress(100, text="Done")
            time.sleep(0.1)
            progress.empty()

            thumb = preview_img.copy()
            thumb.thumbnail((900, 900))
            buf = BytesIO()
            thumb.save(buf, format="PNG")
            thumb_bytes = buf.getvalue()

            st.session_state.bg_results.append(
                {
                    "name": f.name.rsplit(".", 1)[0] + "_rmbg.png",
                    "bytes": png_bytes,
                    "preview": thumb_bytes,
                    "width": preview_img.width,
                    "height": preview_img.height,
                }
            )
        status_placeholder.empty()

    if st.session_state.bg_results:
        for i, r in enumerate(st.session_state.bg_results, start=1):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{i}. {r['name']}")
                st.caption(f"{r['width']} × {r['height']} px")
            with col2:
                st.download_button(
                    "⬇ Download",
                    data=r["bytes"],
                    file_name=r["name"],
                    mime="image/png",
                    key=f"dl-cut-{i}-{r['name']}",
                    use_container_width=True,
                )
            st.image(r["preview"], use_container_width=True)
            st.divider()

# =====================================================================
# PNG → SVG (Node imagetracer)
# =====================================================================
elif tool == "PNG → SVG":
    st.title("PNG → SVG")

    if not have_node():
        st.warning(
            "Node.js not found on PATH. Please install Node to use the ImageTracer engine.\n`brew install node` (macOS) or from nodejs.org."
        )

    # Options
    colA, colB, colC = st.columns(3)
    with colA:
        mode = st.selectbox("Style", ["fidelity", "poster"], index=0)
        layers = st.slider("Layers (colors)", 2, 20, 8)
        dropwhite = st.checkbox("Drop white layer", value=False)
    with colB:
        preblur = st.slider("Pre-blur (smooth regions)", 0.0, 1.5, 0.0, 0.1)
        median = st.slider("Median denoise", 0, 3, 0)
        mergecolors = st.slider(
            "Merge similar colors (ΔRGB)", 0, 48, 0, help="Reduce near-duplicate fills"
        )
    with colC:
        upscale = st.slider("Upscale before trace (×)", 1, 3, 1)
        svgo = st.checkbox("Optimize with SVGO", value=True)
        custom_palette = st.text_input(
            "Fixed palette (comma hex)", value=""
        )  # e.g. #000000,#7d7e80,#ffffff

    files = st.file_uploader(
        "Choose images (PNG/JPG/WebP/HEIC…)",
        type=["png"],
        accept_multiple_files=True,
        key=st.session_state.svg_key,
    )
    

    if files and not st.session_state.svg_results:
        total = len(files)
        status_placeholder = st.empty()

        for idx, f in enumerate(files, start=1):
            raw = f.read()
            status_placeholder.markdown(f"**Vectorizing {idx} / {total}:** {f.name}")

            progress = st.progress(0, text="Starting…")
            if have_node():
                future = run_in_thread(
                    trace_with_imagetracer_node,
                    raw,
                    mode=mode,
                    layers=layers,
                    upscale=upscale,
                    preblur=preblur,
                    median=median,
                    mergecolors=mergecolors,
                    dropwhite=dropwhite,
                    svgo=svgo,
                    palette_hex_csv=(custom_palette.strip() or None),
                )
            else:
                st.error("Node.js not available; cannot run ImageTracer engine.")
                break

            pct = 10
            while not future.done():
                pct = min(pct + 2, 96)
                progress.progress(pct, text="Tracing shapes…")
                time.sleep(0.05)

            svg_bytes = future.result()
            progress.progress(100, text="Done ✅")
            time.sleep(0.1)
            progress.empty()

            out_name = f.name.rsplit(".", 1)[0] + ".svg"
            st.session_state.svg_results.append({"name": out_name, "svg": svg_bytes})

        status_placeholder.empty()

    if st.session_state.svg_results:
        for i, r in enumerate(st.session_state.svg_results, start=1):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{i}. {r['name']}")
            with col2:
                st.download_button(
                    "⬇ Download SVG",
                    data=r["svg"],
                    file_name=r["name"],
                    mime="image/svg+xml",
                    key=f"dl-svg-{i}-{r['name']}",
                    use_container_width=True,
                )
            embed_svg(r["svg"])
            st.divider()

        if st.button("Clear uploads/results"):
            st.session_state.svg_results = []
            st.session_state.svg_key = f"svg-uploader-{time.time()}"
            st.rerun()

# =====================================================================
# Placeholders
# =====================================================================
elif tool == "File Converter":
    st.title("File Converter (coming soon)")
    st.info("Convert TXT ↔ CSV and more, right in the browser.")
