from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pdfplumber


def extract_tables_from_pdf(pdf_path: str | Path) -> pd.DataFrame:
    """Extract all project-level tabular data from a PDF and concatenate only matching tables."""
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_file}")

    relevant_tables = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = (page.extract_text() or "").lower()
            if "state" not in page_text or "physical progress" not in page_text:
                continue
            table = page.extract_table()
            if not table or len(table) < 2:
                continue
            columns = [str(value).strip() if value is not None else "" for value in table[0]]
            normalized_columns = [str(value).lower() for value in columns]
            has_state = any("state" in value for value in normalized_columns)
            has_progress = any("physical progress" in value for value in normalized_columns)
            has_cost = any("cost" in value for value in normalized_columns)

            if has_state and has_progress and has_cost:
                df = pd.DataFrame(table[1:], columns=columns)
                relevant_tables.append(df)

    if not relevant_tables:
        raise ValueError(f"No project-level table found in {pdf_file}")

    return pd.concat(relevant_tables, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract table data from a PDF file.")
    parser.add_argument("--pdf", required=True, help="Path to the PDF file to parse.")
    parser.add_argument(
        "--output",
        default="data/extracted_project_data.csv",
        help="Path to save the extracted CSV output.",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        parser.error(f"PDF file not found: {pdf_path}. Place the actual PDF in the repo or pass the correct file path.")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    extracted = extract_tables_from_pdf(pdf_path)
    extracted.to_csv(output_path, index=False)
    print(f"Data extracted successfully and saved to {output_path}")
    print(extracted.head())


if __name__ == "__main__":
    main()
