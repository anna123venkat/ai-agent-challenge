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
    desc_pattern = r'[A-Za-z\s\.]+'
    amt_pattern = r'\d+(\.\d{2})?'

    # Initialize lists to store extracted information
    dates = []
    descriptions = []
    debit_amts = []
    credit_amts = []
    balances = []

    # Iterate through the extracted text
    for line in text.split('\n'):
        # Extract date
        date_match = re.search(date_pattern, line)
        if date_match:
            dates.append(date_match.group())

        # Extract description
        desc_match = re.search(desc_pattern, line)
        if desc_match:
            descriptions.append(desc_match.group())

        # Extract debit/credit amount
        amt_match = re.search(amt_pattern, line)
        if amt_match:
            amt = float(amt_match.group())
            if 'Dr' in line:
                debit_amts.append(amt)
                credit_amts.append(0.0)
            elif 'Cr' in line:
                debit_amts.append(0.0)
                credit_amts.append(amt)

        # Extract balance
        balance_match = re.search(r'Balance\s+(\d+(\.\d{2})?)', line)
        if balance_match:
            balances.append(float(balance_match.group(1)))

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
This parser extracts the date, description, debit/credit amount, and balance from the PDF file using regular expressions. It then creates a Pandas DataFrame with the extracted information.

Note that this parser assumes that the PDF file has a specific structure, with each transaction on a new line, and the date, description, debit/credit amount, and balance in a specific format. You may need to modify the regular expressions or the parsing logic if your PDF files have a different structure.