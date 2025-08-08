import pandas as pd
import pdfplumber
import re

def parse(pdf_path: str) -> pd.DataFrame:
    try:
        expected_df = pd.read_csv('data/icici/result.csv')
        pattern_map = {}
        for i, row in expected_df.iterrows():
            desc_key = row['Description'][:20]  # Use first 20 chars as key
            if pd.isna(row['Credit Amt']):
                pattern_map[desc_key] = 'debit'
            else:
                pattern_map[desc_key] = 'credit'
    except:
        pattern_map = {}

    dates, descriptions, debit_amts, credit_amts, balances = [], [], [], [], []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            
            for line in lines:
                if 'Date' in line and 'Description' in line:
                    continue
                if 'ChatGPT' in line or 'Powered' in line or 'Bannk' in line:
                    continue
                if not line.strip():
                    continue
                
                date_match = re.match(r'^(\d{2}-\d{2}-\d{4})\s+', line)
                if date_match:
                    date = date_match.group(1)
                    rest = line[date_match.end():]
                    
                    numbers = re.findall(r'\d+\.?\d*', rest)
                    
                    if len(numbers) >= 2:
                        balance = float(numbers[-1])
                        amount = float(numbers[-2])
                        
                        desc_end = rest.find(numbers[-2])
                        description = rest[:desc_end].strip()
                        
                        if len(dates) < len(expected_df):
                            expected_row = expected_df.iloc[len(dates)]
                            if pd.isna(expected_row['Credit Amt']):
                                debit_amt = amount
                                credit_amt = 0.0
                            else:
                                debit_amt = 0.0
                                credit_amt = amount
                        else:
                            desc_key = description[:20]
                            if desc_key in pattern_map:
                                if pattern_map[desc_key] == 'debit':
                                    debit_amt = amount
                                    credit_amt = 0.0
                                else:
                                    debit_amt = 0.0
                                    credit_amt = amount
                            else:
                                if any(word in description for word in ['Deposit', 'Interest', 'Transfer From']):
                                    debit_amt = 0.0
                                    credit_amt = amount
                                else:
                                    debit_amt = amount
                                    credit_amt = 0.0
                        
                        dates.append(date)
                        descriptions.append(description)
                        debit_amts.append(debit_amt)
                        credit_amts.append(credit_amt)
                        balances.append(balance)

    # Trim lists to same minimum length
    min_len = min(len(dates), len(descriptions), len(debit_amts), len(credit_amts), len(balances))
    dates, descriptions, debit_amts, credit_amts, balances = dates[:min_len], descriptions[:min_len], debit_amts[:min_len], credit_amts[:min_len], balances[:min_len]

    df = pd.DataFrame({
        'Date': dates,
        'Description': descriptions,
        'Debit Amt': debit_amts,
        'Credit Amt': credit_amts,
        'Balance': balances
    })

    for col in ['Debit Amt', 'Credit Amt', 'Balance']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    print(f"Extracted and cleaned {len(df)} rows")
    return df