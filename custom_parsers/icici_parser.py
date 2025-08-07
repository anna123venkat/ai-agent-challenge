import pdfplumber
import re
import pandas as pd

def parse(pdf_path: str) -> pd.DataFrame:
    pdf = pdfplumber.open(pdf_path)
    data = []
    for page in pdf.pages:
        try:
            tables = page.extract_table()
            for table in tables:
                for row in table[1:]:  # skip header
                    data.append(row)
        except Exception:
            text = page.extract_text()
            lines = text.split('\n')
            for line in lines:
                match = re.match(r'(\d{1,2}/\d{1,2}/\d{4})\s+([\w\s]+)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)', line)
                if match:
                    data.append(list(match.groups()))
    if len(data) < 3:
        return pd.DataFrame()
    columns = ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']
    if len(set(len(row) for row in data)) != 1:
        raise ValueError("Inconsistent row lengths")
    df = pd.DataFrame(data, columns=columns)
    print(f"Found {len(df)} rows")
    return df