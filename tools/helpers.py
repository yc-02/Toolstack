# helpers.py
import os, subprocess, tempfile, shutil
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

_executor = ThreadPoolExecutor(max_workers=1)


def run_in_thread(fn, *args, **kwargs):
    """Run a blocking function in a background thread and return a Future."""
    return _executor.submit(fn, *args, **kwargs)


# ---------------- Node imagetracer bridge ----------------
def have_node() -> bool:
    return shutil.which("node") is not None


def bytesio_with_name(raw: bytes, name: str) -> BytesIO:
    bio = BytesIO(raw)
    bio.name = name
    bio.seek(0)
    return bio


def _repo_root_dir() -> str:
    """Return the absolute path to the repo root where package.json lives."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path_convert_mjs() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "png2svg_tool.mjs")


def trace_with_imagetracer_node(
    raw_bytes: bytes,
    *,
    mode: str = "fidelity",  # "fidelity" | "poster"
    layers: int = 8,
    upscale: int = 1,
    preblur: float = 0.0,
    median: int = 0,
    mergecolors: int = 0,  # ΔRGB 0–255
    dropwhite: bool = False,
    svgo: bool = True,
    palette_hex_csv: str | None = None,
) -> bytes:
    mjs = path_convert_mjs()
    if not os.path.exists(mjs):
        raise FileNotFoundError(f"png2svg_tool.mjs not found at {mjs}")
    with tempfile.TemporaryDirectory() as td:
        inp = os.path.join(td, "in.png")
        out = os.path.join(td, "out.svg")
        with open(inp, "wb") as f:
            f.write(raw_bytes)

        args = [
            "node",
            mjs,
            inp,
            out,
            f"--mode={mode}",
            f"--layers={int(max(2,layers))}",
        ]
        if upscale and int(upscale) > 1:
            args.append(f"--upscale={int(upscale)}")
        if preblur and float(preblur) > 0:
            args.append(f"--preblur={float(preblur)}")
        if median and int(median) > 0:
            args.append(f"--median={int(median)}")
        if mergecolors and int(mergecolors) > 0:
            args.append(f"--mergecolors={int(mergecolors)}")
        if dropwhite:
            args.append("--dropwhite")
        if svgo:
            args.append("--svgo")
        if palette_hex_csv:
            args.append(f"--palette={palette_hex_csv}")

        res = subprocess.run(args, cwd=_repo_root_dir(), capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"imagetracer failed:\n{res.stdout}\n{res.stderr}")

        return open(out, "rb").read()


def embed_svg(svg_bytes: bytes):
    import base64, streamlit as st

    b64 = base64.b64encode(svg_bytes).decode("utf-8")
    st.markdown(
        f"""
        <div style="width:100%;">
          <img src="data:image/svg+xml;base64,{b64}"
               style="width:100%; height:auto; display:block; margin:0; padding:0;" />
        </div>
        """,
        unsafe_allow_html=True,
    )
