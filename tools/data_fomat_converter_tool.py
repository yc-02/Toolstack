# data_format_converter_tool.py
from typing import Tuple
import pandas as pd
import io
import json

_WRITABLE = {"TXT", "CSV", "JSON", "XLSX"}


def data_format_converter(to_format: str = "CSV", file=None) -> Tuple[str, bytes]:
    if to_format.upper() not in _WRITABLE:
        raise ValueError(f"Unsupported format: {to_format}")

    name = getattr(file, "name", "converted")
    ext = name.split(".")[-1].lower()

    # --- Load file into DataFrame ---
    if ext == "csv":
        df = pd.read_csv(file)
    elif ext == "xlsx":
        df = pd.read_excel(file)
    elif ext == "json":
        df = pd.read_json(file)
    elif ext == "txt":
        df = pd.read_csv(file, delimiter="\t", header=None)
    else:
        raise ValueError(f"Unsupported input file type: {ext}")

    output = io.BytesIO()

    # --- Convert ---
    if to_format.upper() == "CSV":
        df.to_csv(output, index=False)
        ext_out = "csv"

    elif to_format.upper() == "XLSX":
        df.to_excel(output, index=False)
        ext_out = "xlsx"

    elif to_format.upper() == "JSON":
        json_str = df.to_json(orient="records")
        parsed = json.loads(json_str)
        pretty_json = json.dumps(parsed, indent=4, ensure_ascii=False)
        output.write(pretty_json.encode("utf-8"))
        ext_out = "json"

    elif to_format.upper() == "TXT":
        df.to_csv(output, sep="\t", index=False)
        ext_out = "txt"

    output.seek(0)
    return f"{name.rsplit('.', 1)[0]}.{ext_out}", output.read()
