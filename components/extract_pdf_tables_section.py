import time
import io
import pandas as pd
import streamlit as st
from tools.extract_pdf_tables_tool import extract_pdf_tables
from tools.helpers import bytesio_with_name


try:
    from tools.helpers import run_in_thread
except Exception:
    import concurrent.futures

    _EXEC = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def run_in_thread(fn, *args, **kwargs):
        return _EXEC.submit(fn, *args, **kwargs)


def extract_pdf_tables_section():
    st.title("Data Format Converter")

    # --- Upload
    files = st.file_uploader(
        "Upload files",
        type=["pdf"],
        accept_multiple_files=True,
        key=st.session_state.pdf_table_key,
    )

    has_files = bool(files)
    has_results = bool(st.session_state["pdf_table_results"])

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
        st.session_state["pdf_table_results"] = []
        st.session_state["pdf_table_key"] = f"pdf-table-uploader-{time.time()}"
        st.rerun()

    def run_pdfs():
        if not files:
            return
        total = len(files)
        status = st.empty()

        for idx, f in enumerate(files, start=1):
            raw = f.read()
            status.markdown(f"**Extracting {idx}/{total}:** {f.name}")
            progress = st.progress(0, text="Starting…")

            file_like = bytesio_with_name(raw, f.name)
            future = run_in_thread(extract_pdf_tables, file_like)

            pct = 10
            while not future.done():
                pct = min(pct + 2, 90)
                progress.progress(pct, text=f"Extracting tables…")
                time.sleep(0.05)

            try:
                result = future.result()
            except Exception as e:
                progress.empty()
                st.error(f"**{f.name}** failed: {e}")
                continue
            progress.progress(100, text="Done")
            time.sleep(0.05)
            progress.empty()

            if isinstance(result, list):
                for out_name, out_bytes in result:
                    st.session_state.pdf_table_results.append(
                        {"name": out_name, "bytes": out_bytes, "mime": "text/csv"}
                    )
            else:
                out_name, out_bytes = result  # for single-output
                st.session_state.pdf_table_results.append(
                    {"name": out_name, "bytes": out_bytes, "mime": "text/csv"}
                )

        status.empty()

    if files and not st.session_state.pdf_table_results:
        run_pdfs()

    if rerun_clicked:
        st.session_state.pdf_table_results = []
        run_pdfs()

    if clear_clicked:
        clear_files()

    if st.session_state.pdf_table_results:
        st.subheader("Results")
        for i, r in enumerate(st.session_state.pdf_table_results, start=1):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.write(f"{i}. {r['name']}")
                st.caption(f"Preview")
            with c2:
                st.download_button(
                    "⬇ Download",
                    data=r["bytes"],
                    file_name=r["name"],
                    mime=r["mime"],
                    key=f"dl-{i}-{r['name']}",
                    use_container_width=True,
                )
            # Preview first 3 rows
            try:
                preview_df = pd.read_csv(io.BytesIO(r["bytes"]))
                st.dataframe(preview_df.head(3))
            except Exception as e:
                st.error(f"Could not preview table: {e}")
