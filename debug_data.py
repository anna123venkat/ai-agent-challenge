"""
Debug script to analyze your PDF and CSV data
"""

import pandas as pd
import pdfplumber
from pathlib import Path

# Check CSV
csv_path = Path("data/icici/result.csv")
df = pd.read_csv(csv_path)

print("📊 Expected CSV Data:")
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"\nFirst 3 rows:")
print(df.head(3))
print(f"\nLast 3 rows:")
print(df.tail(3))
print(f"\nData types:")
print(df.dtypes)

# Check PDF
pdf_path = Path("data/icici/icici sample.pdf")
print(f"\n📄 PDF Analysis:")

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            lines = text.split('\n')
            
            # Count transaction lines
            transaction_count = 0
            for line in lines:
                if line and line[0:2].isdigit() and '-' in line[0:10]:
                    transaction_count += 1
            
            print(f"\nPage {i+1}:")
            print(f"  Total lines: {len(lines)}")
            print(f"  Transaction lines: {transaction_count}")
            print(f"  First line: {lines[0][:50] if lines else 'None'}")
            
            # Show a sample transaction
            for line in lines:
                if line and line[0:2].isdigit() and '-' in line[0:10]:
                    print(f"  Sample transaction: {line}")
                    break

# Test the parser
try:
    from custom_parsers.icici_parser import parse
    result_df = parse(str(pdf_path))
    
    print(f"\n✅ Parser Output:")
    print(f"Shape: {result_df.shape}")
    
    if result_df.shape[0] > 0:
        print(f"\nFirst transaction:")
        print(result_df.iloc[0])
        
        print(f"\nLast transaction:")
        print(result_df.iloc[-1])
    
    # Compare with expected
    if result_df.shape == df.shape:
        print("\n✅ Shape matches!")
        
        # Check for differences
        differences = []
        for col in df.columns:
            if col in result_df.columns:
                if col in ['Debit Amt', 'Credit Amt', 'Balance']:
                    # Numeric comparison
                    diff = (pd.to_numeric(result_df[col], errors='coerce').fillna(0.0) - 
                           pd.to_numeric(df[col], errors='coerce').fillna(0.0)).abs().sum()
                    if diff > 0.01:
                        differences.append(f"{col}: total difference = {diff}")
                else:
                    # String comparison
                    mismatches = (result_df[col] != df[col]).sum()
                    if mismatches > 0:
                        differences.append(f"{col}: {mismatches} mismatches")
        
        if differences:
            print("\n⚠️ Content differences found:")
            for diff in differences:
                print(f"  - {diff}")
        else:
            print("\n✅ Content matches perfectly!")
    else:
        print(f"\n❌ Shape mismatch: {result_df.shape} != {df.shape}")
        
except Exception as e:
    print(f"\n❌ Parser error: {e}")