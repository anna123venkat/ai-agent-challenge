import os
import re
import pdfminer
from pdfminer.high_level import extract_text
import pandas as pd

def parse_icici_bank_statement(pdf_file_path):
    # Extract text from PDF file
    text = extract_text(pdf_file_path)

    # Regular expressions to extract relevant information
    date_pattern = r'\d{2}-\w{3}-\d{4}'
    desc_pattern = r'(?<=Description : ).*?(?=Amount)'
    debit_pattern = r'(?<=Debit : )\d+(\.\d+)?'
    credit_pattern = r'(?<=Credit : )\d+(\.\d+)?'
    balance_pattern = r'(?<=Balance : )\d+(\.\d+)?'

    # Initialize lists to store extracted information
    dates = []
    descriptions = []
    debit_amts = []
    credit_amts = []
    balances = []

    # Iterate through the text and extract information
    for line in text.split('\n'):
        date_match = re.search(date_pattern, line)
        if date_match:
            dates.append(date_match.group())
        desc_match = re.search(desc_pattern, line)
        if desc_match:
            descriptions.append(desc_match.group())
        debit_match = re.search(debit_pattern, line)
        if debit_match:
            debit_amts.append(float(debit_match.group()))
        credit_match = re.search(credit_pattern, line)
        if credit_match:
            credit_amts.append(float(credit_match.group()))
        balance_match = re.search(balance_pattern, line)
        if balance_match:
            balances.append(float(balance_match.group()))

    # Trim lists to same minimum length
    min_len = min(len(dates), len(descriptions), len(debit_amts), len(credit_amts), len(balances))
    dates = dates[:min_len]
    descriptions = descriptions[:min_len]
    debit_amts = debit_amts[:min_len]
    credit_amts = credit_amts[:min_len]
    balances = balances[:min_len]

    # Create DataFrame
    df = pd.DataFrame({
        'Date': dates,
        'Description': descriptions,
        'Debit Amt': debit_amts,
        'Credit Amt': credit_amts,
        'Balance': balances
    })

    return df

# Example usage
pdf_file_path = 'path/to/icici_bank_statement.pdf'
df = parse_icici_bank_statement(pdf_file_path)
print(df)
```
This parser uses regular expressions to extract the date, description, debit amount, credit amount, and balance from each transaction in the PDF file. It then creates a Pandas DataFrame from the extracted information.

Note that this parser assumes that the PDF file has a specific structure, with each transaction on a new line and the relevant information separated by spaces. You may need to modify the regular expressions or the parsing logic if your PDF files have a different structure."""