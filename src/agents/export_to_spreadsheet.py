import json
import pandas as pd
from pathlib import Path


def json_to_excel(json_path: str, output_path: str):
    json_path = Path(json_path)
    output_path = Path(output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Optional: reorder columns
    preferred_order = [
        "business_name",
        "website_status",
        "lead_score",
        "priority",
        "outreach_message"
    ]
    df = df[[c for c in preferred_order if c in df.columns]]

    # Save Excel
    df.to_excel(output_path, index=False)

    # Save CSV in same folder
    csv_path = output_path.with_suffix(".csv")
    df.to_csv(csv_path, index=False)

    print(f"Excel created: {output_path}")
    print(f"CSV created: {csv_path}")


if __name__ == "__main__":
    json_to_excel(
        json_path="output/test_results.json",
        output_path="output/leads_outreach.xlsx"
    )
