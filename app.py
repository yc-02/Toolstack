# app.py
import streamlit as st
from components.session import sessions
from components.sidebar import sidebar
from components.image_format_converter_section import image_format_converter_section
from components.bg_remover_section import bg_remover_section
from components.png2svg_section import png2svg_section
from components.pick_color_section import pick_color_section

st.set_page_config(page_title="Toolstack", page_icon="", layout="wide")
sessions()
sidebar()

tool = st.session_state.tool
if tool == "intro":
    st.title("Select a tool")
    st.info("Select a tool you want to use from the left panel")

#  Image format converter
elif tool == "Image Format Converter":
    image_format_converter_section()

# Background Remover
elif tool == "Background Remover":
    bg_remover_section()

# PNG → SVG (Node imagetracer)
elif tool == "PNG → SVG":
    png2svg_section()

elif tool == "Click-to-pick color":
    pick_color_section()

elif tool == "File Converter":
    st.title("File Converter (coming soon)")
    st.info("Convert TXT ↔ CSV and more, right in the browser.")
