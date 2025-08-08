import pdfplumber
import pandas as pd

def parse(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        lines = text.split('\n')
        
        dates = []
        descriptions = []
        debit_amts = []
        credit_amts = []
        balances = []
        
        for line in lines:
            if 'Date' in line:
                continue
            parts = line.split()
            date = ' '.join(parts[:3])
            desc = ' '.join(parts[3:-3])
            amt = float(parts[-3].replace(',', ''))
            bal = float(parts[-1].replace(',', ''))
            if 'Dr' in parts[-2]:
                debit_amts.append(amt)
                credit_amts.append(0)
            else:
                debit_amts.append(0)
                credit_amts.append(amt)
            dates.append(date)
            descriptions.append(desc)
            balances.append(bal)
        
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
```