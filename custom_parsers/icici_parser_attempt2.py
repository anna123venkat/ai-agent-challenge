import pdfplumber
import pandas as pd
import re

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
                line = line.strip()
                if not line or len(line) < 10:
                    continue
                match = re.search(r'(\d{1,2}\/\d{1,2}\/\d{4})\s*(.*)\s*(-?\d+(\.\d+)?)(\s*(-?\d+(\.\d+)?))(\s*(-?\d+(\.\d+)?))', line)
                if match:
                    date = match.group(1)
                    desc = match.group(2)
                    debit_amt = float(match.group(3)) if match.group(3) else 0
                    credit_amt = float(match.group(6)) if match.group(6) else 0
                    balance = float(match.group(9)) if match.group(9) else 0
                    dates.append(date)
                    descriptions.append(desc)
                    debit_amts.append(debit_amt)
                    credit_amts.append(credit_amt)
                    balances.append(balance)

    min_len = min(len(dates), len(descriptions), len(debit_amts), len(credit_amts), len(balances))
    dates = dates[:min_len]
    descriptions = descriptions[:min_len]
    debit_amts = debit_amts[:min_len]
    credit_amts = credit_amts[:min_len]
    balances = balances[:min_len]

    df = pd.DataFrame({
        'Date': dates,
        'Description': descriptions,
        'Debit Amt': debit_amts,
        'Credit Amt': credit_amts,
        'Balance': balances
    })
    return df
