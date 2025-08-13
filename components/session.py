import streamlit as st

def sessions():
    if "tool" not in st.session_state:
        st.session_state.tool = "intro"
    
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
