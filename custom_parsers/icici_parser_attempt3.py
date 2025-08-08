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
                parts = re.split(r'\s{2,}', line)
                if len(parts) < 4:
                    continue
                date = parts[0]
                desc = ' '.join(parts[1:-3])
                amounts = list(map(float, parts[-3:]))
                if amounts[0] > 0:
                    debit_amts.append(amounts[0])
                    credit_amts.append(0)
                else:
                    debit_amts.append(0)
                    credit_amts.append(-amounts[0])
                balances.append(amounts[1])
                dates.append(date)
                descriptions.append(desc)
    
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
