import pdfplumber
import re
import pandas as pd

def parse(pdf_path):
    dates = []
    descriptions = []
    debit_amts = []
    credit_amts = []
    balances = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')
            for line in lines:
                parts = line.split()
                if len(parts) < 6 or any(word in parts for word in ['Date', 'Description', 'Credit', 'Balance']):
                    continue
                if not re.match(r'^\d{2}-\d{2}-\d{4}$', parts[0]):
                    continue
                try:
                    debit_amt = float(parts[-3])
                    credit_amt = float(parts[-2])
                    balance = float(parts[-1])
                    description = ' '.join(parts[1:-3])
                    dates.append(parts[0])
                    descriptions.append(description)
                    debit_amts.append(debit_amt)
                    credit_amts.append(credit_amt)
                    balances.append(balance)
                except ValueError:
                    continue

    min_len = min(len(dates), len(descriptions), len(debit_amts), len(credit_amts), len(balances))
    df = pd.DataFrame({
        'Date': dates[:min_len],
        'Description': descriptions[:min_len],
        'Debit Amt': debit_amts[:min_len],
        'Credit Amt': credit_amts[:min_len],
        'Balance': balances[:min_len]
    })
    return df
