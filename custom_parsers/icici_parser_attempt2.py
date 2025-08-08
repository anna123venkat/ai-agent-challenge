import pdfplumber
import pandas as pd
import re

def parse(pdf_file):
    dates = []
    descriptions = []
    debit_amts = []
    credit_amts = []
    balances = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line or len(line) < 10:
                    continue
                parts = re.split(r'\s{2,}', line)
                if len(parts) < 4:
                    continue
                date = parts[0]
                desc = ' '.join(parts[1:-3])
                amounts = [float(x) for x in parts[-3:]]
                if len(amounts) != 3:
                    continue
                debit, credit, balance = amounts
                dates.append(date)
                descriptions.append(desc)
                debit_amts.append(debit)
                credit_amts.append(credit)
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
