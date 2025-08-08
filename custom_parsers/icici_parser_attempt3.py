import pdfplumber
import pandas as pd

def parse_icici_bank_statement(pdf_file):
    dates = []
    descriptions = []
    debit_amts = []
    credit_amts = []
    balances = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')
            for line in lines:
                if 'Date' in line:
                    continue
                parts = line.split()
                if len(parts) < 5:
                    continue
                date = ' '.join(parts[:3])
                desc = ' '.join(parts[3:-3])
                amt = float(parts[-2].replace(',', ''))
                bal = float(parts[-1].replace(',', ''))
                if 'Dr' in parts[-3]:
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
This parser uses the `pdfplumber` library to extract text from the PDF file, and then processes the text to extract the relevant information. It assumes that the PDF file has a specific format, where each transaction is represented by a line with the following format:
```
Date Description ... Dr/Cr Amount Balance
```
The parser extracts the date, description, debit/credit amount, and balance from each line, and stores them in separate lists. It then trims the lists to the same minimum length, and creates a Pandas DataFrame from the lists.

Note that this parser assumes that the PDF file has a specific format, and may not work if the format is different. You may need to modify the parser to handle different formats.