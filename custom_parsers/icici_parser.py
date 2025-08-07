import pdfplumber
import re
import pandas as pd
import numpy as np
from datetime import datetime

def extract_text(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
        return text

def extract_columns(text):
    dates = re.findall(r'\b\d{1,2}-\d{1,2}-\d{4}\b', text)
    descriptions = re.findall(r'[A-Za-z\s]+', text)
    debit_amts = re.findall(r'\b\d+(\.\d+)?\b', text)
    credit_amts = re.findall(r'\b\d+(\.\d+)?\b', text)
    balances = re.findall(r'\b\d+(\.\d+)?\b', text)
    return dates, descriptions, debit_amts, credit_amts, balances

def clean_and_validate(data):
    dates, descriptions, debit_amts, credit_amts, balances = data
    dates = [datetime.strptime(date, '%d-%m-%Y').strftime('%Y-%m-%d') for date in dates]
    descriptions = [desc.strip() for desc in descriptions]
    debit_amts = [float(amt) if amt else np.nan for amt in debit_amts]
    credit_amts = [float(amt) if amt else np.nan for amt in credit_amts]
    balances = [float(bal) if bal else np.nan for bal in balances]
    max_len = max(len(dates), len(descriptions), len(debit_amts), len(credit_amts), len(balances))
    dates.extend([np.nan] * (max_len - len(dates)))
    descriptions.extend([np.nan] * (max_len - len(descriptions)))
    debit_amts.extend([np.nan] * (max_len - len(debit_amts)))
    credit_amts.extend([np.nan] * (max_len - len(credit_amts)))
    balances.extend([np.nan] * (max_len - len(balances)))
    return dates, descriptions, debit_amts, credit_amts, balances

def create_dataframe(data):
    dates, descriptions, debit_amts, credit_amts, balances = data
    df = pd.DataFrame({
        'Date': dates,
        'Description': descriptions,
        'Debit Amt': debit_amts,
        'Credit Amt': credit_amts,
        'Balance': balances
    })
    return df

def parse(pdf_path):
    try:
        text = extract_text(pdf_path)
        data = extract_columns(text)
        data = clean_and_validate(data)
        df = create_dataframe(data)
        return df
    except pdfplumber.PDFParserError as e:
        return f"Error parsing PDF file: {e}"
    except ValueError as e:
        return f"Error creating DataFrame: {e}"
    except AttributeError as e:
        return f"Error manipulating DataFrame: {e}"