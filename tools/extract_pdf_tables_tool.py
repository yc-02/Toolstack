from typing import List, Tuple, Union, Dict, Any
import io
import re
import pdfplumber
import pandas as pd


def _as_bio(
    file: Union[bytes, bytearray, io.BufferedIOBase, io.BytesIO, Any],
) -> io.BytesIO:
    """Normalize input to a fresh BytesIO at position 0 with a best-effort .name."""
    if isinstance(file, (bytes, bytearray)):
        bio = io.BytesIO(file)
        bio.name = getattr(file, "name", "input.pdf")
        bio.seek(0)
        return bio
    if hasattr(file, "read"):
        name = getattr(file, "name", "input.pdf")
        try:
            pos = file.tell()
        except Exception:
            pos = None
        try:
            file.seek(0)
            data = file.read()
        finally:
            try:
                if pos is not None:
                    file.seek(pos)
            except Exception:
                pass
        bio = io.BytesIO(data)
        bio.name = name
        bio.seek(0)
        return bio
    raise TypeError("Expected bytes or a binary file-like object for PDF input")


def _looks_like_pdf(bio: io.BytesIO) -> bool:
    cur = bio.tell()
    bio.seek(0)
    head = bio.read(1024)
    bio.seek(cur)
    return b"%PDF" in head


def _norm_header_cell(x: Any) -> str:
    if x is None:
        return ""
    s = str(x)
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s.lower()


def _signature(headers: list) -> Tuple[str, ...]:
    return tuple(_norm_header_cell(h) for h in headers)


def _slug(text: str, maxlen: int = 48) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    if not text:
        return "table"
    return (text[:maxlen]).strip("_")


def extract_pdf_tables(
    file: Union[bytes, io.BytesIO, io.BufferedIOBase],
    include_page_col: bool = True,
) -> List[Tuple[str, bytes]]:

    bio = _as_bio(file)
    if not _looks_like_pdf(bio):
        raise ValueError(
            "Input does not appear to be a valid PDF (missing %PDF header)."
        )

    stem = getattr(bio, "name", "tables").rsplit(".", 1)[0]

    groups: Dict[Tuple[str, ...], Dict[str, Any]] = {}

    bio.seek(0)
    with pdfplumber.open(bio) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables() or []
            for table in tables:
                if not table or len(table) == 0:
                    continue

                headers = list(table[0])  # first row as header
                body = table[1:]

                # drop repeated head rows
                body = [row for row in body if row != headers]

                sig = _signature(headers)

                if sig not in groups:
                    groups[sig] = {"headers": headers, "rows": []}

                # Append rows; keep page info
                if include_page_col:
                    for r in body:
                        groups[sig]["rows"].append([page_num] + list(r))
                else:
                    for r in body:
                        groups[sig]["rows"].append(list(r))


    if not groups:
        raise ValueError("No tables found in the PDF.")

    outputs: List[Tuple[str, bytes]] = []
    for idx, (sig, bundle) in enumerate(groups.items(), start=1):
        headers = bundle["headers"]
        rows = bundle["rows"]

        if include_page_col:
            cols = ["page"] + [str(h) if h is not None else "" for h in headers]
        else:
            cols = [str(h) if h is not None else "" for h in headers]

        # write CSV
        df = pd.DataFrame(rows, columns=cols)

        out = io.BytesIO()
        df.to_csv(out, index=False)
        out.seek(0)

        # using the first few header names as file name
        header_slug = _slug("_".join([str(h or "") for h in headers]) or f"group_{idx}")
        fname = f"{stem}_{header_slug}.csv"
        outputs.append((fname, out.read()))

    return outputs
