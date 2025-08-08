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
                description = ' '.join(parts[3:-3])
                amount = float(parts[-2].replace(',', ''))
                balance = float(parts[-1].replace(',', ''))
                if amount > 0:
                    debit_amts.append(0)
                    credit_amts.append(amount)
                else:
                    debit_amts.append(-amount)
                    credit_amts.append(0)
                dates.append(date)
                descriptions.append(description)
                balances.append(balance)

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
This parser uses the `pdfplumber` library to extract text from the PDF file, and then processes the text to extract the relevant information. It assumes that the PDF file has a consistent format, with each transaction represented by a single line of text, with the date, description, amount, and balance separated by spaces.

The parser creates five lists to store the extracted information: `dates`, `descriptions`, `debit_amts`, `credit_amts`, and `balances`. It then trims these lists to the same minimum length using the `min_len` variable, to ensure that the resulting DataFrame has the correct shape.

Finally, the parser creates a Pandas DataFrame from the extracted information, with the specified column names.