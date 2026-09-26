from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import pdfplumber


def clean_cell(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\xa0", " ")).strip()


def extract_numbers(value: object) -> list[float]:
    text = clean_cell(value)
    if not text:
        return []
    return [float(token) for token in re.findall(r"-?\d+(?:\.\d+)?", text)]


def parse_currency_pair(value: object) -> tuple[float, float]:
    nums = extract_numbers(value)
    if not nums:
        return 0.0, 0.0
    if len(nums) == 1:
        return nums[0], nums[0]
    return nums[0], nums[1]


def parse_date_value(value: object) -> pd.Timestamp | None:
    text = clean_cell(value)
    if not text or "-" in text or "na" in text.lower() or "(-)" in text:
        return None

    matches = re.findall(r"\d{2}/\d{4}", text)
    if not matches:
        return None

    try:
        date_str = f"01/{matches[0]}"
        return pd.to_datetime(date_str, format="%d/%m/%Y")
    except ValueError:
        return None


def months_between(start: pd.Timestamp | None, end: pd.Timestamp | None) -> float:
    if start is None or end is None:
        return 0.0
    delta_months = (end.year - start.year) * 12 + (end.month - start.month)
    return max(0.0, float(delta_months))


def infer_sector_from_project_name(project_name: object, state_name: object = "", sector_name: object = "") -> str:
    text = " ".join(part for part in [clean_cell(project_name), clean_cell(sector_name), clean_cell(state_name)] if part).lower()
    if not text:
        return "unknown"

    sector_rules = [
        ("railways", ["rail", "metro rail", "railway", "rail line"]),
        ("power", ["power", "solar", "thermal", "wind", "hydro"]),
        ("petroleum", ["petroleum", "lpg", "pol", "oil", "gas", "natural gas"]),
        ("road transport highways", ["highway", "national highway", "nh-", "road transport", "roads and services", "roads", "road", "expressway"]),
        ("telecommunication", ["telecom", "telecommunication", "mobile connectivity", "mobile services", "network"]),
        ("water resources", ["water", "irrigation", "storm water", "river", "drainage", "dam", "canal"]),
        ("urban development", ["urban", "housing", "airport", "building", "terminal", "infrastructure", "smart city", "civil aviation", "higher education"]),
    ]

    for sector_label, keywords in sector_rules:
        if any(keyword in text for keyword in keywords):
            return sector_label

    return clean_cell(sector_name).lower() or clean_cell(state_name).lower() or "unknown"


def normalize_project_table(table: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    current_state = ""
    current_sector = ""

    for row in table.itertuples(index=False, name=None):
        cells = [clean_cell(cell) for cell in row]
        if not any(cells):
            continue

        numeric_indexes = [idx for idx, value in enumerate(cells) if value.isdigit()]
        if not numeric_indexes:
            continue

        if cells[0].isdigit():
            if len(cells) < 8:
                continue
            project_id = cells[0]
            project_name = cells[1]
            state = cells[2] if len(cells) > 2 else current_state
            approval_cell = cells[3] if len(cells) > 3 else ""
            doc_cell = cells[4] if len(cells) > 4 else ""
            cost_cell = cells[5] if len(cells) > 5 else ""
            expenditure_cell = cells[6] if len(cells) > 6 else ""
            progress_cell = cells[7] if len(cells) > 7 else ""
            sector_value = current_sector
        else:
            if len(cells) < 9:
                continue
            project_id = cells[2] if len(cells) > 2 and cells[2].isdigit() else cells[0]
            state = cells[0] if cells[0] and not cells[0].isdigit() else current_state
            sector_value = cells[1] if len(cells) > 1 and cells[1] and not cells[1].isdigit() else current_sector
            project_name = cells[3] if len(cells) > 3 else ""
            approval_cell = cells[4] if len(cells) > 4 else ""
            doc_cell = cells[5] if len(cells) > 5 else ""
            cost_cell = cells[6] if len(cells) > 6 else ""
            expenditure_cell = cells[7] if len(cells) > 7 else ""
            progress_cell = cells[8] if len(cells) > 8 else ""

        if not project_name:
            continue

        if state:
            current_state = state
        if sector_value:
            current_sector = sector_value

        if not state:
            continue
        if project_id.lower() == "total":
            continue
        if any(token in project_name.lower() for token in ["total (", "summary", "overview"]):
            continue

        if not project_name:
            continue

        approval_dates = []
        for match in re.findall(r"\d{2}/\d{4}", approval_cell):
            try:
                approval_dates.append(pd.to_datetime(f"01/{match}", format="%d/%m/%Y"))
            except ValueError:
                pass

        doc_dates = []
        for match in re.findall(r"\d{2}/\d{4}", doc_cell):
            try:
                doc_dates.append(pd.to_datetime(f"01/{match}", format="%d/%m/%Y"))
            except ValueError:
                pass

        start_date = approval_dates[0] if approval_dates else None
        target_date = doc_dates[0] if doc_dates else None
        if len(doc_dates) > 1:
            target_date = doc_dates[1]

        original_cost, revised_cost = parse_currency_pair(cost_cell)
        physical_progress = extract_numbers(progress_cell)[0] if extract_numbers(progress_cell) else 0.0
        cumulative_expenditure = extract_numbers(expenditure_cell)[0] if extract_numbers(expenditure_cell) else 0.0
        time_delay_months = months_between(start_date, target_date)

        inferred_sector = infer_sector_from_project_name(project_name, state, sector_value)
        records.append(
            {
                "Project_ID": project_id,
                "Project_Name": project_name,
                "Sector": inferred_sector,
                "State": state,
                "Date_of_Approval": approval_cell,
                "Target_Doc": doc_cell,
                "Original_Cost": original_cost,
                "Revised_Cost": revised_cost,
                "Cumulative_Expenditure": cumulative_expenditure,
                "Physical_Progress": physical_progress,
                "Time_Delay_Months": time_delay_months,
                "Time_Overrun_Months": time_delay_months,
            }
        )

    if not records:
        raise ValueError("No usable project rows found in table")

    normalized = pd.DataFrame(records)
    normalized["Sector"] = normalized["Sector"].astype(str).str.strip().str.lower()
    normalized["Original_Cost"] = pd.to_numeric(normalized["Original_Cost"], errors="coerce")
    normalized["Revised_Cost"] = pd.to_numeric(normalized["Revised_Cost"], errors="coerce")
    normalized["Physical_Progress"] = pd.to_numeric(normalized["Physical_Progress"], errors="coerce")
    normalized["Time_Delay_Months"] = pd.to_numeric(normalized["Time_Delay_Months"], errors="coerce").fillna(0.0)
    normalized["Time_Overrun_Months"] = pd.to_numeric(normalized["Time_Overrun_Months"], errors="coerce").fillna(0.0)
    normalized = normalized.dropna(subset=["Sector", "Original_Cost", "Physical_Progress"]).copy()
    normalized = normalized[(normalized["Original_Cost"] > 0) & (normalized["Physical_Progress"] >= 0)].copy()
    return normalized


def extract_tables_from_pdf(pdf_path: str | Path) -> pd.DataFrame:
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_file}")

    relevant_tables: list[pd.DataFrame] = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = (page.extract_text() or "").lower()
            if "ongoing projects" not in page_text:
                continue
            table = page.extract_table()
            if not table:
                continue
            try:
                df = normalize_project_table(pd.DataFrame(table))
            except ValueError:
                continue
            relevant_tables.append(df)

    if not relevant_tables:
        raise ValueError(f"No usable project table found in {pdf_file}")

    return pd.concat(relevant_tables, ignore_index=True)


def build_dataset_from_pdfs(project_root: Path | str) -> pd.DataFrame:
    root = Path(project_root)
    extracted_frames: list[pd.DataFrame] = []

    for pdf_file in sorted(root.glob("*.pdf")):
        try:
            extracted_frames.append(extract_tables_from_pdf(pdf_file))
        except ValueError:
            continue

    if not extracted_frames:
        raise ValueError(f"No project tables could be extracted from PDFs in {root}")

    combined = pd.concat(extracted_frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["Project_ID", "Project_Name", "State"]).copy()
    combined["Original_Cost"] = pd.to_numeric(combined["Original_Cost"], errors="coerce")
    combined["Physical_Progress"] = pd.to_numeric(combined["Physical_Progress"], errors="coerce")
    combined["Time_Delay_Months"] = pd.to_numeric(combined["Time_Delay_Months"], errors="coerce").fillna(0.0)
    combined["Time_Overrun_Months"] = pd.to_numeric(combined["Time_Overrun_Months"], errors="coerce").fillna(0.0)
    return combined


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Extract project rows from one or more PDF reports.")
    parser.add_argument("--pdf", help="Optional single PDF file to process instead of all PDFs in the repo root.")
    parser.add_argument(
        "--output",
        default=str(project_root / "data" / "extracted_project_data.csv"),
        help="Path to save the extracted CSV output.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.pdf:
        extracted = extract_tables_from_pdf(args.pdf)
    else:
        extracted = build_dataset_from_pdfs(project_root)

    extracted.to_csv(output_path, index=False)
    print(f"Data extracted successfully and saved to {output_path}")
    print(extracted.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
