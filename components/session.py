# session.py
import streamlit as st


def sessions():
    if "tool" not in st.session_state:
        st.session_state.tool = "intro"

    if "image_results" not in st.session_state:
        st.session_state.image_results = []
    if "bg_results" not in st.session_state:
        st.session_state.bg_results = []
    if "svg_results" not in st.session_state:
        st.session_state.svg_results = []
    if "pick_color_results" not in st.session_state:
        st.session_state.pick_color_results = []

    if "image_key" not in st.session_state:
        st.session_state.image_key = "image-uploader-0"
    if "bg_key" not in st.session_state:
        st.session_state.bg_key = "bg-uploader-0"
    if "svg_key" not in st.session_state:
        st.session_state.svg_key = "svg-uploader-0"
    if "pick_color_key" not in st.session_state:
        st.session_state.pick_color_key = "pick-color-uploader-0"
