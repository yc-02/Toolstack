# image_format_converter_section.py
import time
import streamlit as st
from io import BytesIO
from tools.image_format_converter_tool import (
    image_format_converter,
)

try:
    from helpers import run_in_thread
except Exception:
    import concurrent.futures

    _EXEC = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def run_in_thread(fn, *args, **kwargs):
        return _EXEC.submit(fn, *args, **kwargs)



def image_format_converter_section():
    st.title("Image Format Converter")

    # --- Output format selection
    label_to_fmt = {"PNG": "png", "JPEG": "jpeg", "WEBP": "webp", "HEIF": "heif"}
    choice = st.selectbox("Convert to format", list(label_to_fmt.keys()), index=0)
    to_format = label_to_fmt[choice]

    # --- File upload (broaden types beyond HEIC)
    files = st.file_uploader(
        "Choose images",
        type=["png", "jpg", "jpeg", "webp", "heic", "HEIC", "heif", "HEIF"],
        accept_multiple_files=True,
        key=st.session_state.image_key,
    )

    # --- Optional resize
    resize_enabled = st.toggle("Enable resize", value=False)
    max_width = (
        st.number_input(
            "Max width (px)", min_value=0, value=300, help="0 = original size"
        )
        if resize_enabled
        else 0
    )

    has_files = bool(files)
    has_results = bool(st.session_state["image_results"])
    col1, col2, _ = st.columns([1, 2, 7])
    with col1:
        rerun_clicked = st.button(
            "Run Again", key="rerun-image", disabled=not (has_files)
        )
    with col2:
        clear_clicked = st.button(
            "Clear uploads/results",
            key="clear-image",
            disabled=not (has_files or has_results),
        )
    # helpers to map formats to extensions/mimes
    ext_map = {"png": "png", "jpeg": "jpg", "webp": "webp", "heif": "heic"}
    mime_map = {
        "png": "image/png",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "heif": "image/heif",
    }

    # clear
    def clear_images():
        st.session_state["image_results"] = []
        st.session_state["image_key"] = f"image-uploader-{time.time()}"
        st.rerun()

    # Run
    def run_images():
        if files:
            total = len(files)
        status_placeholder = st.empty()

        for idx, f in enumerate(files, start=1):
            raw = f.read()
            status_placeholder.markdown(f"**Converting {idx} / {total}:** {f.name}")

            progress = st.progress(0, text="Starting…")
            future = run_in_thread(image_format_converter, to_format, raw, max_width)

            pct = 10
            while not future.done():
                pct = min(pct + 2, 95)
                progress.progress(pct, text=f"Converting to {choice}…")
                time.sleep(0.05)

            try:
                final_fmt, out_bytes, final_img = future.result()
            except Exception as e:
                # e.g., trying to convert an alpha image to JPEG (your converter raises)
                progress.empty()
                st.error(f"Skipping **{f.name}**: {e}")
                continue

            progress.progress(100, text="Done")
            time.sleep(0.1)
            progress.empty()

            # Build preview 
            thumb = final_img.copy()
            thumb.thumbnail((900, 900))
            buf = BytesIO()
            thumb.save(buf, format="PNG")
            thumb_bytes = buf.getvalue()

            # File naming + mime
            base = f.name.rsplit(".", 1)[0]
            ext = ext_map.get(final_fmt, final_fmt)
            file_name = f"{base}.{ext}"
            mime = mime_map.get(final_fmt, "application/octet-stream")

            st.session_state.image_results.append(
                {
                    "name": file_name,
                    "bytes": out_bytes,
                    "preview": thumb_bytes,
                    "width": final_img.width,
                    "height": final_img.height,
                    "mime": mime,
                }
            )
        status_placeholder.empty()

    if files and not st.session_state.image_results:
        run_images()
    if files and rerun_clicked:
        st.session_state["image_results"] = []
        run_images()
    if clear_clicked:
        clear_images()
    if st.session_state.image_results:
        for i, r in enumerate(st.session_state.image_results, start=1):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{i}. {r['name']}")
                st.caption(f"{r['width']} × {r['height']} px")
            with col2:
                st.download_button(
                    "⬇ Download",
                    data=r["bytes"],
                    file_name=r["name"],
                    mime=r["mime"],
                    key=f"dl-image-{i}-{r['name']}",
                    use_container_width=True,
                )
            st.image(r["preview"], use_container_width=True)
