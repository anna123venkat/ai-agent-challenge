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
                
                # Classify transaction based on description
                debit_amt = 0.0
                credit_amt = 0.0
                
                # Credit transactions (money coming in)
                if any(pattern in description for pattern in [
                    'Salary Credit', 'Interest Credit', 'Cheque Deposit', 
                    'Cash Deposit', 'NEFT Transfer From', 'Transfer From'
                ]):
                    credit_amt = amount
                # Debit transactions (money going out)  
                elif any(pattern in description for pattern in [
                    'UPI Payment', 'IMPS UPI Payment', 'UPI QR Payment',
                    'Card Swipe', 'Debit Card', 'Online Card Purchase', 
                    'Credit Card Payment', 'EMI Auto Debit', 'Insurance Premium Auto Debit',
                    'Service Charge', 'Bill Payment', 'NEFT Online',
                    'ATM Cash Withdrawal', 'Mobile Recharge', 'UPI Transfer',
                    'NEFT Transfer To', 'Fuel Purchase', 'Electricity', 'Utility'
                ]):
                    debit_amt = amount
                else:
                    # Default: assume debit if unclear
                    debit_amt = amount
                
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