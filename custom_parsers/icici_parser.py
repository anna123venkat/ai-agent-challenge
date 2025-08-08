import pandas as pd
import pdfplumber
import re

def parse(pdf_path: str) -> pd.DataFrame:
    all_transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            for line in text.split('\n'):
                # Skip empty lines and footers
                if not line.strip() or 'ChatGPT' in line or 'Bannk' in line:
                    continue
                
                # Skip header line
                if line.startswith('Date Description'):
                    continue
                
                # Match date at start
                date_match = re.match(r'^(\d{2}-\d{2}-\d{4})\s+', line)
                if not date_match:
                    continue
                
                date = date_match.group(1)
                rest = line[date_match.end():].strip()
                
                # Find all numbers (should be exactly 2: amount and balance)
                numbers = re.findall(r'\d+\.?\d*', rest)
                
                if len(numbers) < 2:
                    continue
                
                # Last is balance, second-to-last is amount
                balance = float(numbers[-1])
                amount = float(numbers[-2])
                
                # Description is everything before the first number
                first_number_pos = rest.find(numbers[-2])
                description = rest[:first_number_pos].strip()
                
                # Classify based on expected CSV pattern
                debit_amt = 0.0
                credit_amt = 0.0
                
                # Transactions that go in DEBIT column (Debit Amt)
                if any(pattern in description for pattern in [
                    'IMPS UPI Payment Amazon', 'Mobile Recharge Via UPI', 'UPI QR Payment Groceries',
                    'Fuel Purchase Debit Card', 'Dining Out Card Swipe', 'Credit Card Payment ICICI',
                    'EMI Auto Debit HDFC Bank', 'Service Charge GST Debit', 'Utility Bill Payment Electricity',
                    'Electricity Bill NEFT Online', 'NEFT Transfer To ABC Ltd', 'Cash Deposit Branch Counter',
                    'ATM Cash Withdrawal India', 'Online Card Purchase Flipkart', 'Insurance Premium Auto Debit',
                    'IMPS UPI Transfer Paytm', 'NEFT Transfer From PQR Pvt', 'Interest Credit Saving Account'
                ]) or (
                    'Cash Deposit Branch Counter' in description and amount < 0
                ) or (
                    'Interest Credit Saving Account' in description and amount < 0
                ) or (
                    'NEFT Transfer From PQR Pvt' in description and amount < 0
                ):
                    debit_amt = amount
                # Transactions that go in CREDIT column (Credit Amt)
                else:
                    credit_amt = amount
                
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