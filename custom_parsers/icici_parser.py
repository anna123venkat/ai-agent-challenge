import pdfplumber
import pandas as pd

def parse(pdf_path: str) -> pd.DataFrame:
    with pdfplumber.open(pdf_path) as pdf:
        pages = [page.extract_table() for page in pdf.pages]
        tables = [table for page in pages for table in page]

    data = []
    for table in tables:
        for row in table[1:]:  # skip header
            row = [cell.strip().replace('₹', '').replace(',', '') for cell in row]
            try:
                row[1] = float(row[1].replace(',', ''))  # Debit Amt
                row[2] = float(row[2].replace(',', ''))  # Credit Amt
                row[3] = float(row[3].replace(',', ''))  # Balance
            except ValueError:
                row[1] = 0.0
                row[2] = 0.0
                row[3] = 0.0
            if any(cell in ['', 'Debit Amt', 'Credit Amt', 'Balance'] for cell in row):
                continue
            if len(row) != 5:
                continue
            data.append(row)

    max_len = max(len(row) for row in data)
    data = [row[:max_len] for row in data]

    df = pd.DataFrame(data, columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
    print(f"Extracted and cleaned {len(df)} rows")
    return df