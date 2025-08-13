import time
import streamlit as st
from io import BytesIO
from tools.heic2png import convert_heic_to_png_bytes

try:
    from helpers import run_in_thread
except Exception:
    import concurrent.futures

    _EXEC = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def run_in_thread(fn, *args, **kwargs):
        return _EXEC.submit(fn, *args, **kwargs)


def heic2png_section():
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

    has_files = bool(files)
    has_results = bool(st.session_state["heic_results"])
    clicked = st.button(
        "Clear uploads/results",
        key="clear-heic",  # keep this unique
        disabled=not (has_files or has_results),
    )

    if clicked:
        st.session_state["heic_results"] = []
        st.session_state["heic_key"] = (
            f"heic-uploader-{time.time()}"  # reset uploader so files clear
        )
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
