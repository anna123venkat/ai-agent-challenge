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
    desc_pattern = r'[^:]+(?=:)'
    debit_pattern = r'Debit\s+Rs.\s+(\d+(?:\.\d+)?)(?=\s+Cr.)'
    credit_pattern = r'Credit\s+Rs.\s+(\d+(?:\.\d+)?)(?=\s+Dr.)'
    balance_pattern = r'Balance\s+Rs.\s+(\d+(?:\.\d+)?)'

    # Extract dates
    dates = re.findall(date_pattern, text)

    # Extract descriptions
    descriptions = re.findall(desc_pattern, text)

    # Extract debit amounts
    debit_amts = re.findall(debit_pattern, text)

    # Extract credit amounts
    credit_amts = re.findall(credit_pattern, text)

    # Extract balances
    balances = re.findall(balance_pattern, text)

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
This parser extracts the following information from the PDF file:

* Dates
* Descriptions
* Debit amounts
* Credit amounts
* Balances

It uses regular expressions to extract the relevant information from the PDF text. The extracted lists are then trimmed to the same minimum length to ensure that each transaction has either a debit or credit amount, but not both. Finally, a Pandas DataFrame is created with the extracted information.

Note that this parser assumes that the PDF file has a specific structure and format, which may not be the case for all ICICI bank statements. You may need to modify the regular expressions or the parsing logic to accommodate variations in the PDF format.