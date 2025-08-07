import pdfplumber
import re
import pandas as pd

def parse(pdf_path: str) -> pd.DataFrame:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = [page.extract_text() for page in pdf.pages]
            text = '\n'.join(pages)

            date_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'
            description_pattern = r'([A-Za-z\s]+)'
            debit_pattern = r'(\d+(\.\d+)?)'
            credit_pattern = r'(\d+(\.\d+)?)'
            balance_pattern = r'(\d+(\.\d+)?)'

            dates = re.findall(date_pattern, text)
            descriptions = re.findall(description_pattern, text)
            debits = re.findall(debit_pattern, text)
            credits = re.findall(credit_pattern, text)
            balances = re.findall(balance_pattern, text)

            min_len = min(len(dates), len(descriptions), len(debits), len(credits), len(balances))

            dates = dates[:min_len]
            descriptions = descriptions[:min_len]
            debits = debits[:min_len]
            credits = credits[:min_len]
            balances = balances[:min_len]

            data = {'Date': dates, 'Description': descriptions, 'Debit Amt': debits, 'Credit Amt': credits, 'Balance': balances}
            df = pd.DataFrame(data)

            return df

    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return pd.DataFrame(columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])