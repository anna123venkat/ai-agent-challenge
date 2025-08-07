import pdfplumber
import re
import pandas as pd
import logging
import numpy as np

logging.basicConfig(level=logging.ERROR)

class PDFParsingError(Exception):
    pass

def parse_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        logging.error(f"Error parsing PDF: {e}")
        raise PDFParsingError("Error parsing PDF")

def extract_columns(text):
    date_pattern = r'\d{2}-\d{2}-\d{4}'
    desc_pattern = r'[A-Za-z\s]+'
    debit_pattern = r'-\d+(\.\d+)?'
    credit_pattern = r'\+\d+(\.\d+)?'
    balance_pattern = r'\d+(\.\d+)?'
    
    dates = re.findall(date_pattern, text)
    descs = re.findall(desc_pattern, text)
    debits = re.findall(debit_pattern, text)
    credits = re.findall(credit_pattern, text)
    balances = re.findall(balance_pattern, text)
    
    return dates, descs, debits, credits, balances

def clean_and_validate(data):
    dates, descs, debits, credits, balances = data
    debits = [float(debit.lstrip('-')) for debit in debits]
    credits = [float(credit.lstrip('+')) for credit in credits]
    balances = [float(balance) for balance in balances]
    return list(zip(dates, descs, debits, credits, balances))

def parse(pdf_path: str) -> pd.DataFrame:
    try:
        text = parse_pdf(pdf_path)
        data = extract_columns(text)
        data = clean_and_validate(data)
        df = pd.DataFrame(data, columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
        df.replace('', np.nan, inplace=True)
        df.fillna(np.nan, inplace=True)
        return df
    except Exception as e:
        logging.error(f"Error parsing PDF: {e}")
        return pd.DataFrame(columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])