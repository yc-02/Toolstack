# app.py
import os
import subprocess
import streamlit as st
from components.session import sessions
from components.sidebar import sidebar
from components.image_format_converter_section import image_format_converter_section
from components.bg_remover_section import bg_remover_section
from components.png2svg_section import png2svg_section
from components.pick_color_section import pick_color_section
from components.data_format_converter_section import data_format_converter_section
from components.extract_pdf_tables_section import extract_pdf_tables_section

NODE_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
node_modules_path = os.path.join(NODE_PROJECT_DIR, "node_modules")
if not os.path.exists(node_modules_path):
    st.write("Installing Node dependencies...")
    subprocess.run(["npm", "install"], cwd=NODE_PROJECT_DIR, check=True)

st.set_page_config(page_title="Toolstack", page_icon="favicon.ico", layout="wide")
sessions()
sidebar()

tool = st.session_state.tool
if tool == "intro":
    st.title("Toolstack")
    st.markdown(
        "### Welcome!\n"
        "Pick a tool from the **sidebar** on the left to get started.\n"
    )
    st.info("Use the left panel to explore available tools.")


elif tool == "Image Format Converter":
    image_format_converter_section()

elif tool == "Background Remover":
    bg_remover_section()

elif tool == "PNG to SVG":
    png2svg_section()

elif tool == "Click to Pick Color":
    pick_color_section()

elif tool == "Data Format Converter":
    data_format_converter_section()

elif tool == "Extract PDF Tables":
    extract_pdf_tables_section()
