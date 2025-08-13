# session.py
import streamlit as st


def sessions():

    if "tool" not in st.session_state:
        st.session_state.tool = "intro"

    if "file_results" not in st.session_state:
        st.file_results = []
    if "file_key" not in st.session_state:
        st.session_state.file_key = "file-uploader-0"

    if "image_results" not in st.session_state:
        st.session_state.image_results = []
    if "image_key" not in st.session_state:
        st.session_state.image_key = "image-uploader-0"

    if "bg_results" not in st.session_state:
        st.session_state.bg_results = []
    if "bg_key" not in st.session_state:
        st.session_state.bg_key = "bg-uploader-0"

    if "svg_results" not in st.session_state:
        st.session_state.svg_results = []
    if "svg_key" not in st.session_state:
        st.session_state.svg_key = "svg-uploader-0"

    if "pick_color" not in st.session_state:
        st.session_state.pick_color = None
    if "pick_color_key" not in st.session_state:
        st.session_state.pick_color_key = "pick-color-uploader-0"

    if "pdf_table_results" not in st.session_state:
        st.session_state.pdf_table_results = []
    if "pdf_table_key" not in st.session_state:
        st.session_state.pdf_table_key = "pdf-table-uploader-0"
