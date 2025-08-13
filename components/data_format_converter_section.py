# data_format_converter_section.py
import time
from io import BytesIO
import streamlit as st
from tools.data_fomat_converter_tool import data_format_converter

try:
    from tools.helpers import run_in_thread
except Exception:
    import concurrent.futures

    _EXEC = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def run_in_thread(fn, *args, **kwargs):
        return _EXEC.submit(fn, *args, **kwargs)



def _bytesio_with_name(raw: bytes, name: str) -> BytesIO:
    bio = BytesIO(raw)
    bio.name = name
    bio.seek(0)
    return bio


def data_format_converter_section():
    st.title("Data Format Converter")

    # --- Output format selection
    label_to_fmt = {"txt": "TXT", "csv": "CSV", "json": "JSON", "xlsx": "XLSX"}
    choice = st.selectbox("Convert to", list(label_to_fmt.keys()), index=0)
    to_format = label_to_fmt[choice]

    # --- Upload
    files = st.file_uploader(
        "Upload files",
        type=["txt", "csv", "json", "xlsx"],
        accept_multiple_files=True,
        key=st.session_state.file_key,
    )

    has_files = bool(files)
    has_results = bool(st.session_state["file_results"])

    b1, b2, _ = st.columns([1, 2, 6])
    with b1:
        rerun_clicked = st.button(
            "Run Again",
            key="rerun-files",
            disabled=not has_files,
            use_container_width=True,
        )
    with b2:
        clear_clicked = st.button(
            "Clear uploads/results",
            key="clear-files",
            disabled=not (has_files or has_results),
            use_container_width=True,
        )

    def clear_files():
        st.session_state["file_results"] = []
        st.session_state["file_key"] = f"file-uploader-{time.time()}"
        st.rerun()

    mime_map = {
        "TXT": "text/plain",
        "CSV": "text/csv",
        "JSON": "application/json",
        "XLSX": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    def run_files():
        if files:
            total = len(files)
            print(f"total files {total}")
            status = st.empty()

            for idx, f in enumerate(files, start=1):
                raw = f.read()

                status.markdown(f"**Converting {idx}/{total}:** {f.name}")
                progress = st.progress(0, text="Starting…")

                # Build a fresh file-like for the converter (with a name and pointer at 0)
                file_like = _bytesio_with_name(raw, f.name)

                future = run_in_thread(data_format_converter, to_format, file_like)
                pct = 10
                while not future.done():
                    pct = min(pct + 3, 95)
                    progress.progress(pct, text=f"Converting to {choice}…")
                    time.sleep(0.05)

                try:
                    out_name, out_bytes = future.result()
                except Exception as e:
                    progress.empty()
                    st.error(f"**{f.name}** failed: {e}")
                    continue

                progress.progress(100, text="Done")
                time.sleep(0.05)
                progress.empty()

                st.session_state.file_results.append(
                    {
                        "name": out_name,
                        "bytes": out_bytes,
                        "mime": mime_map.get(to_format, "application/octet-stream"),
                    }
                )

            status.empty()

    if files and not st.session_state.file_results:
        run_files()

    if rerun_clicked:
        st.session_state.file_results = []
        run_files()

    if clear_clicked:
        clear_files()

    if st.session_state.file_results:
        st.subheader("Results")
        for i, r in enumerate(st.session_state.file_results, start=1):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"{i}. **{r['name']}**")
            with c2:
                st.download_button(
                    "⬇ Download",
                    data=r["bytes"],
                    file_name=r["name"],
                    mime=r["mime"],
                    key=f"dl-{i}-{r['name']}",
                    use_container_width=True,
                )
