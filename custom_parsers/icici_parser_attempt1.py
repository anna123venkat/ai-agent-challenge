import pdfplumber
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
                if len(parts) >= 5 and parts[0].count('-') == 2:
                    date = parts[0]
                    description = ' '.join(parts[1:-3])
                    debit_amt = float(parts[-3])
                    credit_amt = float(parts[-2])
                    balance = float(parts[-1])
                    dates.append(date)
                    descriptions.append(description)
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
