import pdfplumber
import re
import pandas as pd

def is_float(s):
    try:
        float(s)
        return True
    except:
        return False

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
                tokens = line.split()
                if len(tokens) < 6:
                    print(f"Skipping line: too few tokens ({len(tokens)})")
                    continue
                if any(token in tokens for token in ['Date', 'Description', 'Credit', 'Debit']):
                    print(f"Skipping line: contains header-like words")
                    continue
                if not re.match(r'\d{2}-\d{2}-\d{4}', tokens[0]):
                    print(f"Skipping line: invalid date format ({tokens[0]})")
                    continue
                float_tokens = [token for token in tokens[::-1] if is_float(token)]
                if len(float_tokens) < 3:
                    print(f"Skipping line: fewer than 3 float-compatible tokens")
                    continue
                balance = float(float_tokens[0])
                credit_amt = float(float_tokens[1])
                debit_amt = float(float_tokens[2])
                description = ' '.join(tokens[1:-3])
                print(f"Parsed line: Date={tokens[0]}, Description={description}, Debit={debit_amt}, Credit={credit_amt}, Balance={balance}")
                dates.append(tokens[0])
                descriptions.append(description)
                debit_amts.append(debit_amt)
                credit_amts.append(credit_amt)
                balances.append(balance)

    min_len = min(len(dates), len(descriptions), len(debit_amts), len(credit_amts), len(balances))
    df = pd.DataFrame({
        'Date': dates[:min_len],
        'Description': descriptions[:min_len],
        'Debit Amt': debit_amts[:min_len],
        'Credit Amt': credit_amts[:min_len],
        'Balance': balances[:min_len]
    })
    print(f"✅ Parsed {len(df)} transactions")
    return df
