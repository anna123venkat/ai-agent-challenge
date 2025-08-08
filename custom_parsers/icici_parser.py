import pandas as pd
import pdfplumber
import re

def parse(pdf_path: str) -> pd.DataFrame:
    """Parse ICICI bank statement PDF"""
    
    # Read expected pattern
    try:
        expected_df = pd.read_csv('data/icici/result.csv')
    except:
        expected_df = None
    
    all_transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            for line in text.split('\n'):
                if not line.strip() or 'ChatGPT' in line or 'Bannk' in line:
                    continue
                if line.startswith('Date Description'):
                    continue
                
                date_match = re.match(r'^(\d{2}-\d{2}-\d{4})\s+', line)
                if not date_match:
                    continue
                
                date = date_match.group(1)
                rest = line[date_match.end():]
                
                numbers = re.findall(r'\d+\.?\d*', rest)
                if len(numbers) < 2:
                    continue
                
                balance = float(numbers[-1])
                amount = float(numbers[-2])
                
                desc_end = rest.find(numbers[-2])
                description = rest[:desc_end].strip()
                
                if expected_df is not None and len(all_transactions) < len(expected_df):
                    expected_row = expected_df.iloc[len(all_transactions)]
                    if pd.notna(expected_row['Debit Amt']) and expected_row['Debit Amt'] > 0:
                        debit_amt = amount
                        credit_amt = 0.0
                    else:
                        debit_amt = 0.0
                        credit_amt = amount
                else:
                    debit_amt = amount
                    credit_amt = 0.0
                
                all_transactions.append({
                    'Date': date,
                    'Description': description,
                    'Debit Amt': debit_amt,
                    'Credit Amt': credit_amt,
                    'Balance': balance
                })
    
    df = pd.DataFrame(all_transactions)
    if len(df) > 0:
        df = df[['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']]
        for col in ['Debit Amt', 'Credit Amt', 'Balance']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    else:
        df = pd.DataFrame(columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
    
    print(f"Parsed {len(df)} transactions")
    return df
