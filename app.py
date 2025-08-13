# app.py
import os, subprocess, tarfile, urllib.request, stat, streamlit as st

st.set_page_config(page_title="Toolstack", page_icon="favicon.ico", layout="wide")

NODE_VER = "v20.14.0"
NODE_DIST = f"node-{NODE_VER}-linux-x64"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "toolstack")
NODE_DIR = os.path.join(CACHE_DIR, NODE_DIST)
NODE_BIN = os.path.join(NODE_DIR, "bin", "node")
NPM_BIN = os.path.join(NODE_DIR, "bin", "npm")


def ensure_embedded_node():
    os.makedirs(CACHE_DIR, exist_ok=True)
    if not os.path.exists(NODE_BIN):
        url = f"https://nodejs.org/dist/{NODE_VER}/{NODE_DIST}.tar.xz"
        tar_path = os.path.join(CACHE_DIR, f"{NODE_DIST}.tar.xz")
        st.write(f"Downloading Node {NODE_VER}…")
        urllib.request.urlretrieve(url, tar_path)
        with tarfile.open(tar_path, "r:xz") as tf:
            tf.extractall(CACHE_DIR)
        # mark binaries executable
        os.chmod(NODE_BIN, os.stat(NODE_BIN).st_mode | stat.S_IXUSR)
        os.chmod(NPM_BIN, os.stat(NPM_BIN).st_mode | stat.S_IXUSR)


def ensure_node_deps():
    ensure_embedded_node()
    repo_root = os.path.dirname(os.path.abspath(__file__))
    pkg_json = os.path.join(repo_root, "package.json")
    node_modules = os.path.join(repo_root, "node_modules")
    if not os.path.exists(pkg_json):
        st.error(f"`package.json` not found at: {pkg_json}")
        st.stop()
    need_install = (not os.path.isdir(node_modules)) or (not os.listdir(node_modules))
    if need_install:
        with st.status("Installing Node dependencies…", expanded=True) as status:
            cmd = (
                [NPM_BIN, "ci", "--omit=dev"]
                if os.path.exists(os.path.join(repo_root, "package-lock.json"))
                else [NPM_BIN, "install", "--omit=dev"]
            )
            st.write("Running:", " ".join(cmd))
            subprocess.run(cmd, cwd=repo_root, check=True)
            status.update(label="Node dependencies installed", state="complete")


ensure_node_deps()

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
