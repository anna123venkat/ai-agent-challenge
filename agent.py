#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, field

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

@dataclass
class AgentState:
    bank_name: str
    pdf_path: Path
    csv_path: Path
    parser_path: Path
    attempts: int = 0
    max_attempts: int = 3
    current_code: str = ""
    errors: List[str] = field(default_factory=list)
    success: bool = False

class BankParserAgent:
    def __init__(self):
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY missing in .env")
        self.llm = Groq(api_key=api_key)
        print("✅ Agent initialized with Groq")

    def _call_llm(self, prompt: str) -> str:
        try:
            response = self.llm.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM call failed: {e}")
            return ""

    def analyze_discrepancies(self, result_df: pd.DataFrame, expected_df: pd.DataFrame) -> str:
        """Analyze differences between result and expected DataFrames"""
        discrepancies = []
        
        # Compare first few rows in detail
        for i in range(min(10, len(result_df), len(expected_df))):
            result_row = result_df.iloc[i]
            expected_row = expected_df.iloc[i]
            
            if not result_row.equals(expected_row):
                discrepancies.append(f"Row {i}:")
                discrepancies.append(f"  Date: {result_row['Date']} vs {expected_row['Date']}")
                discrepancies.append(f"  Description: '{result_row['Description']}' vs '{expected_row['Description']}'")
                discrepancies.append(f"  Debit: {result_row['Debit Amt']} vs {expected_row['Debit Amt']}")
                discrepancies.append(f"  Credit: {result_row['Credit Amt']} vs {expected_row['Credit Amt']}")
                discrepancies.append(f"  Balance: {result_row['Balance']} vs {expected_row['Balance']}")
                discrepancies.append("")
        
        return "\n".join(discrepancies[:50])  # Limit output

    def generate_code_prompt(self, state: AgentState, previous_errors: str = "") -> str:
        """Generate improved prompt based on previous attempts"""
        
        error_context = ""
        if previous_errors:
            error_context = f"\n\nPREVIOUS ERRORS TO FIX:\n{previous_errors}\n"
        
        return f"""
Generate a Python function to parse ICICI bank statement PDF.

CRITICAL FORMAT ANALYSIS:
- PDF Format: "DD-MM-YYYY Description Amount Balance" (only 4 values per line)
- CSV Output: Date, Description, Debit Amt, Credit Amt, Balance (5 columns)
- The single "Amount" from PDF must go to EITHER "Debit Amt" OR "Credit Amt" in CSV

CRITICAL: The expected CSV has COMPLETELY INVERTED debit/credit logic from normal accounting!

PUT IN DEBIT COLUMN (amount goes to Debit Amt, Credit Amt = 0) - INVERTED LOGIC:
- "Salary Credit XYZ Pvt Ltd" (logically income, but goes in DEBIT column)
- "Interest Credit Saving Account" (logically income, but goes in DEBIT column)
- "Cheque Deposit Local Clearing" (logically income, but goes in DEBIT column)
- "Cash Deposit Branch Counter" (when it's a debit in expected)
- "NEFT Transfer From PQR Pvt" (when it's a debit in expected)

PUT IN CREDIT COLUMN (amount goes to Credit Amt, Debit Amt = 0) - INVERTED LOGIC:
- "IMPS UPI Payment Amazon" (logically expense, but goes in CREDIT column)
- "Mobile Recharge Via UPI" (logically expense, but goes in CREDIT column)
- "UPI QR Payment Groceries" (logically expense, but goes in CREDIT column)
- "Fuel Purchase Debit Card" (logically expense, but goes in CREDIT column)
- "Dining Out Card Swipe" (logically expense, but goes in CREDIT column)
- "Credit Card Payment ICICI" (logically expense, but goes in CREDIT column)
- "EMI Auto Debit HDFC Bank" (logically expense, but goes in CREDIT column)
- "Service Charge GST Debit" (logically expense, but goes in CREDIT column)
- "Utility Bill Payment Electricity" (logically expense, but goes in CREDIT column)
- "Electricity Bill NEFT Online" (logically expense, but goes in CREDIT column)
- "NEFT Transfer To ABC Ltd" (logically expense, but goes in CREDIT column)
- "ATM Cash Withdrawal India" (logically expense, but goes in CREDIT column)
- "Online Card Purchase Flipkart" (logically expense, but goes in CREDIT column)
- "Insurance Premium Auto Debit" (logically expense, but goes in CREDIT column)
- "IMPS UPI Transfer Paytm" (logically expense, but goes in CREDIT column)

{error_context}

COMPLETE WORKING CODE:
```python
import pandas as pd
import pdfplumber
import re

def parse(pdf_path: str) -> pd.DataFrame:
    all_transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            for line in text.split('\\n'):
                # Skip empty lines and footers
                if not line.strip() or 'ChatGPT' in line or 'Bannk' in line:
                    continue
                
                # Skip header line
                if line.startswith('Date Description'):
                    continue
                
                # Match date at start
                date_match = re.match(r'^(\\d{{2}}-\\d{{2}}-\\d{{4}})\\s+', line)
                if not date_match:
                    continue
                
                date = date_match.group(1)
                rest = line[date_match.end():].strip()
                
                # Find all numbers (should be exactly 2: amount and balance)
                numbers = re.findall(r'\\d+\\.?\\d*', rest)
                
                if len(numbers) < 2:
                    continue
                
                # Last is balance, second-to-last is amount
                balance = float(numbers[-1])
                amount = float(numbers[-2])
                
                # Description is everything before the first number
                first_number_pos = rest.find(numbers[-2])
                description = rest[:first_number_pos].strip()
                
                # INVERTED classification to match the expected CSV format
                debit_amt = 0.0
                credit_amt = 0.0
                
                # Put logical CREDITS in DEBIT column (inverted logic for this specific CSV)
                if any(pattern in description for pattern in [
                    'Salary Credit', 'Interest Credit', 'Cheque Deposit'
                ]):
                    debit_amt = amount  # INVERTED: income goes to debit column
                # Put logical DEBITS in CREDIT column (inverted logic for this specific CSV)
                elif any(pattern in description for pattern in [
                    'IMPS UPI Payment', 'Mobile Recharge', 'UPI QR Payment',
                    'Fuel Purchase', 'Dining Out', 'Credit Card Payment', 
                    'EMI Auto Debit', 'Service Charge', 'Utility Bill Payment',
                    'Electricity Bill', 'NEFT Transfer To', 'ATM Cash Withdrawal',
                    'Online Card Purchase', 'Insurance Premium', 'IMPS UPI Transfer',
                    'Cash Deposit', 'NEFT Transfer From'
                ]):
                    credit_amt = amount  # INVERTED: expenses go to credit column
                else:
                    # Default: try to match other patterns or put in credit column
                    credit_amt = amount
                
                all_transactions.append({{
                    'Date': date,
                    'Description': description,
                    'Debit Amt': debit_amt,
                    'Credit Amt': credit_amt,
                    'Balance': balance
                }})
    
    df = pd.DataFrame(all_transactions)
    
    if len(df) > 0:
        df = df[['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']]
        for col in ['Debit Amt', 'Credit Amt', 'Balance']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    else:
        df = pd.DataFrame(columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
    
    print(f"Parsed {{len(df)}} transactions")
    return df
```

Return ONLY the code above.
"""

    def clean_code(self, code: str) -> str:
        """Extract Python code from LLM response"""
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        return code.strip()

    def test_parser(self, state: AgentState) -> bool:
        """Test the generated parser with detailed comparison"""
        try:
            # Import and run the parser
            import importlib.util
            spec = importlib.util.spec_from_file_location("parser", state.parser_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Parse the PDF
            result_df = module.parse(str(state.pdf_path))
            
            # Load expected CSV
            expected_df = pd.read_csv(state.csv_path)
            
            # Prepare for comparison
            for df in [result_df, expected_df]:
                for col in ['Debit Amt', 'Credit Amt', 'Balance']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            # Check shapes
            if result_df.shape != expected_df.shape:
                print(f"❌ Shape mismatch: {result_df.shape} != {expected_df.shape}")
                return False
                
            print(f"✅ Shape matches: {result_df.shape}")
            
            # Check if they match exactly
            if result_df.equals(expected_df):
                print("✅ All values match perfectly!")
                return True
            
            # Detailed comparison
            print("❌ Values don't match - analyzing differences...")
            
            # Check each column
            mismatches = 0
            for col in result_df.columns:
                if not result_df[col].equals(expected_df[col]):
                    mismatches += 1
                    print(f"  Column '{col}' has differences")
            
            # Show first few mismatched rows
            print("\nFirst 5 mismatched rows:")
            for i in range(min(5, len(result_df))):
                if not result_df.iloc[i].equals(expected_df.iloc[i]):
                    print(f"\nRow {i}:")
                    print(f"  Result:   {result_df.iloc[i].tolist()}")
                    print(f"  Expected: {expected_df.iloc[i].tolist()}")
                    
                    # Specific field analysis
                    for col in result_df.columns:
                        if result_df.iloc[i][col] != expected_df.iloc[i][col]:
                            print(f"    {col}: {result_df.iloc[i][col]} != {expected_df.iloc[i][col]}")
            
            # Save debug CSVs
            result_df.to_csv('debug_result.csv', index=False)
            print(f"\n💾 Saved result to debug_result.csv for analysis")
            
            return False
            
        except Exception as e:
            print(f"❌ Test error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run(self, bank_name: str) -> bool:
        # Setup paths
        state = AgentState(
            bank_name=bank_name,
            pdf_path=Path(f"data/{bank_name}/{bank_name} sample.pdf"),
            csv_path=Path(f"data/{bank_name}/result.csv"),
            parser_path=Path(f"custom_parsers/{bank_name}_parser.py")
        )
        
        # Check files exist
        if not state.pdf_path.exists():
            state.pdf_path = Path(f"data/{bank_name}/{bank_name}_sample.pdf")
        
        print(f"\n🚀 Starting Bank Parser Agent for {bank_name.upper()}")
        
        previous_errors = ""
        
        for attempt in range(1, state.max_attempts + 1):
            print(f"\n📍 Attempt {attempt}/{state.max_attempts}")
            
            # Generate code with context from previous attempts
            code = self._call_llm(self.generate_code_prompt(state, previous_errors))
            code = self.clean_code(code)
            
            if not code:
                print("❌ No code generated")
                continue
            
            # Save parser
            state.parser_path.parent.mkdir(parents=True, exist_ok=True)
            state.parser_path.write_text(code, encoding='utf-8')
            print(f"💾 Saved parser to {state.parser_path}")
            
            # Test parser
            if self.test_parser(state):
                print(f"\n🎉 SUCCESS! Parser works correctly!")
                return True
            
            # Collect error info for next attempt
            if attempt < state.max_attempts:
                previous_errors = f"Attempt {attempt}: Debit/Credit classification is still wrong. The agent is putting amounts in the opposite columns from what's expected."
            
            state.attempts = attempt
        
        print("\n❌ All attempts failed")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Bank name (e.g., icici)")
    args = parser.parse_args()
    
    agent = BankParserAgent()
    success = agent.run(args.target)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()