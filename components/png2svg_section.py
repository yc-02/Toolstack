import time
import streamlit as st

try:
    from helpers import run_in_thread, embed_svg, trace_with_imagetracer_node, have_node
except Exception:
    import concurrent.futures

    _EXEC = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def run_in_thread(fn, *args, **kwargs):
        return _EXEC.submit(fn, *args, **kwargs)


def png2svg_section():

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
        custom_palette = st.text_input("Fixed palette (comma hex)", value="")

    files = st.file_uploader(
        "Choose images",
        type=["png"],
        accept_multiple_files=True,
        key=st.session_state.svg_key,
    )

    has_files = bool(files)  # list of UploadedFile when accept_multiple_files=True
    has_results = bool(st.session_state["svg_results"])
    clicked = st.button(
        "Clear uploads/results",
        key="clear-svg",
        disabled=not (has_files or has_results),
    )

    if clicked:
        st.session_state["svg_results"] = []
        st.session_state["svg_key"] = (
            f"sbg-uploader-{time.time()}"  # reset uploader so files clear
        )
        st.rerun()
        
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
