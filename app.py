# app.py
import os
import shutil
import subprocess
import streamlit as st

st.set_page_config(page_title="Toolstack", page_icon="favicon.ico", layout="wide")

NODE_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_JSON = os.path.join(NODE_PROJECT_DIR, "package.json")
PKG_LOCK = os.path.join(NODE_PROJECT_DIR, "package-lock.json")
NODE_MODULES = os.path.join(NODE_PROJECT_DIR, "node_modules")


def ensure_node_deps() -> bool:
    if shutil.which("node") is None or shutil.which("npm") is None:
        st.error(
            "Node.js/npm are not available."
        )
        return False

    if not os.path.exists(PKG_JSON):
        st.error(f"`package.json` not found at: {PKG_JSON}")
        return False


    need_install = (not os.path.isdir(NODE_MODULES)) or (not os.listdir(NODE_MODULES))
    if need_install:
        with st.status("Installing Node dependencies…", expanded=True) as status:
            try:
                if os.path.exists(PKG_LOCK):
                    cmd = ["npm", "ci", "--omit=dev"]
                else:
                    cmd = ["npm", "install", "--omit=dev"]
                st.write("Running:", " ".join(cmd))
                subprocess.run(cmd, cwd=NODE_PROJECT_DIR, check=True)
                status.update(label="Node dependencies installed", state="complete")
            except subprocess.CalledProcessError as e:
                st.error("Failed to install Node packages. Check app logs for details.")
                print("[npm-install ERROR]", e)
                return False
    return True


if not ensure_node_deps():
    st.stop()


from components.session import sessions
from components.sidebar import sidebar
from components.image_format_converter_section import image_format_converter_section
from components.bg_remover_section import bg_remover_section
from components.png2svg_section import png2svg_section
from components.pick_color_section import pick_color_section
from components.data_format_converter_section import data_format_converter_section
from components.extract_pdf_tables_section import extract_pdf_tables_section

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
