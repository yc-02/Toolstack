# sidebar.py
import streamlit as st


def sidebar():
    def set_tool(name: str):
        st.session_state.tool = name

    # ---- data ----
    st.sidebar.title("Data")

    st.sidebar.button(
        "Data Format Converter",
        use_container_width=True,
        on_click=set_tool,
        args=("Data Format Converter",),
    )

    st.sidebar.button(
        "Extract PDF Tables",
        use_container_width=True,
        on_click=set_tool,
        args=("Extract PDF Tables",),
    )

    # ---- Images -----
    st.sidebar.title("Images")
    st.sidebar.button(
        "Image Format Converter",
        use_container_width=True,
        on_click=set_tool,
        args=("Image Format Converter",),
    )

    st.sidebar.button(
        "PNG to SVG", use_container_width=True, on_click=set_tool, args=("PNG to SVG",)
    )

    st.sidebar.button(
        "Click to Pick Color",
        use_container_width=True,
        on_click=set_tool,
        args=("Click to Pick Color",),
    )

    st.sidebar.button(
        "Background Remover",
        use_container_width=True,
        on_click=set_tool,
        args=("Background Remover",),
    )

    # -- caption --
    if st.session_state.tool != "intro":
        st.sidebar.markdown("---")
        st.sidebar.caption(f"Active tool: **{st.session_state.tool}**")
