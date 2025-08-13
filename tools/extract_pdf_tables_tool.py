from typing import Tuple
import io
import pdfplumber
import pandas as pd


def extract_pdf_tables(file) -> Tuple[str, bytes]:
    name = getattr(file, "name", "tables.pdf")
    output = io.BytesIO()
    all_tables = []

    with pdfplumber.open(file) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table in tables:
                df = pd.DataFrame(table)
                df.insert(0, "page", page_number)  # Add page number column
                all_tables.append(df)

    if not all_tables:
        raise ValueError("No tables found in the PDF.")

    # Merge all tables into one CSV
    result_df = pd.concat(all_tables, ignore_index=True)
    result_df.to_csv(output, index=False)
    output.seek(0)

    return f"{name.rsplit('.', 1)[0]}_tables.csv", output.read()
