# sidebar.py
import streamlit as st


def sidebar():
    st.sidebar.title("Images")

    def set_tool(name: str):
        st.session_state.tool = name

    # Image Format Converter
    st.sidebar.button(
        "Image Format Converter",
        use_container_width=True,
        on_click=set_tool,
        args=("Image Format Converter",),
    )

    st.sidebar.button(
        "PNG → SVG", use_container_width=True, on_click=set_tool, args=("PNG → SVG",)
    )

    st.sidebar.button(
        "Click-to-pick color",
        use_container_width=True,
        on_click=set_tool,
        args=("Click-to-pick color",),
    )

    st.sidebar.button(
        "Background Remover",
        use_container_width=True,
        on_click=set_tool,
        args=("Background Remover",),
    )

    st.sidebar.title("Files")
    # txt to csv
    # txt to excel
    # txt to pdf
    # csv to excel
    # csv to pdf
    # csv to json
    # txt, csv, pdf, excel, json

    st.sidebar.button(
        "Data Format Converter",
        use_container_width=True,
        on_click=set_tool,
        args=("Data Format Converter",),
    )

    st.sidebar.button(
        "File Size Reducer",
        use_container_width=True,
        on_click=set_tool,
        args=("File Size Reducer",),
    )

    if st.session_state.tool != "intro":
        st.sidebar.markdown("---")
        st.sidebar.caption(f"Active tool: **{st.session_state.tool}**")
