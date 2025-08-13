# app.py
import streamlit as st
from components.session import sessions
from components.sidebar import sidebar
from components.image_format_converter_section import image_format_converter_section
from components.bg_remover_section import bg_remover_section
from components.png2svg_section import png2svg_section
from components.pick_color_section import pick_color_section
from components.data_format_converter_section import data_format_converter_section
st.set_page_config(page_title="Toolstack", page_icon="", layout="wide")
sessions()
sidebar()

tool = st.session_state.tool
if tool == "intro":
    st.title("Toolstack")
    st.markdown(
        "### Welcome!\n"
        "Pick a tool from the **sidebar** on the left to get started.\n"
    )
    st.info("➡️ Use the left panel to explore available tools.")


elif tool == "Image Format Converter":
    image_format_converter_section()


elif tool == "Background Remover":
    bg_remover_section()


elif tool == "PNG → SVG":
    png2svg_section()

elif tool == "Click-to-pick color":
    pick_color_section()

elif tool == "Data Format Converter":
    data_format_converter_section()

elif tool == "Extract PDF Tables":
    print("something")