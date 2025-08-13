import time
import streamlit as st
from io import BytesIO
from tools.remove_bg_tool import remove_bg, get_session

try:
    from helpers import run_in_thread
except Exception:
    import concurrent.futures

    _EXEC = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def run_in_thread(fn, *args, **kwargs):
        return _EXEC.submit(fn, *args, **kwargs)


def bg_remover_section():
    st.title("Background Remover")

    @st.cache_resource
    def warm_session():
        return get_session("isnet-general-use")

    warm_session()

    files = st.file_uploader(
        "Choose images",
        type=["png", "jpg", "jpeg", "webp", "heic", "HEIC", "heif", "HEIF"],
        accept_multiple_files=True,
        key=st.session_state.bg_key,
    )

    resize_enabled = st.toggle("Enable resize", value=False)
    max_width = (
        st.number_input(
            "Max width (px)", min_value=0, value=300, help="0 = original size"
        )
        if resize_enabled
        else 0
    )

    has_files = bool(files)
    has_results = bool(st.session_state["bg_results"])
    col1, col2, _ = st.columns([1, 2, 7])
    with col1:
        rerun_clicked = st.button("Run Again", key="rerun-bg", disabled=not (has_files))
    with col2:
        clear_clicked = st.button(
            "Clear uploads/results",
            key="clear-bg",
            disabled=not (has_files or has_results),
        )

    def clear_bg():
        st.session_state["bg_results"] = []
        st.session_state["bg_key"] = (
            f"bg-uploader-{time.time()}"  # reset uploader so files clear
        )
        st.rerun()

    def run_bg():
        if files:
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

    if files and not st.session_state.bg_results:
        run_bg()
    if files and rerun_clicked:
        st.session_state["bg_results"] = []
        run_bg()
    if clear_clicked:
        clear_bg()
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
