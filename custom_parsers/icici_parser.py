import pdfplumber
import re
import pandas as pd

def parse(pdf_path: str) -> pd.DataFrame:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = [page.extract_text() for page in pdf.pages]
            text = '\n'.join(pages)
            
            # Remove header and footer
            text = re.sub(r'Page [0-9]+ of [0-9]+', '', text)
            text = re.sub(r'Statement [A-Za-z0-9\s]+', '', text)
            
            # Extract table using pdfplumber
            tables = []
            for page in pdf.pages:
                tables.extend(page.extract_table())
            
            # Fallback to regex if table extraction fails
            if not tables:
                rows = [row.split() for row in text.split('\n')]
                tables = [rows]
            
            # Clean and process table data
            data = []
            for table in tables:
                for row in table[1:]:  # skip header
                    if len(row) == 5:  # skip non-transaction rows
                        date = re.sub(r'[^\d-]', '', row[0])
                        desc = ' '.join(row[1:-2])
                        debit = float(re.sub(r'[^\d\.]', '', row[-2]).replace(',', ''))
                        credit = float(re.sub(r'[^\d\.]', '', row[-1]).replace(',', ''))
                        balance = float(re.sub(r'[^\d\.]', '', row[-1]).replace(',', ''))
                        data.append([date, desc, debit, credit, balance])
            
            # Create DataFrame and return
            if len(data) >= 3:
                df = pd.DataFrame(data, columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
                print(f"Parsed {len(df)} rows")
                return df
            else:
                return pd.DataFrame(columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
    
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return pd.DataFrame(columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])