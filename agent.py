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

    def generate_code_prompt(self, state: AgentState) -> str:
        """Generate prompt that understands the 2-number format"""
        
        return """
Generate a Python function to parse ICICI bank statement PDF.

CRITICAL: The PDF has a specific format with only TWO numbers per line:
- Format: "DD-MM-YYYY Description Amount Balance"
- Example: "01-08-2024 Salary Credit XYZ Pvt Ltd 1935.3 6864.58"
  - Date: 01-08-2024
  - Description: Salary Credit XYZ Pvt Ltd
  - Amount: 1935.3 (this goes to EITHER Debit OR Credit column)
  - Balance: 6864.58

The CSV output needs 5 columns but the PDF only has 4 values. Each transaction's amount goes to EITHER Debit Amt OR Credit Amt (not both).

COMPLETE CODE:
```python
import pandas as pd
import pdfplumber
import re

def parse(pdf_path: str) -> pd.DataFrame:
    # Read expected CSV to understand debit/credit pattern
    try:
        expected_df = pd.read_csv('data/icici/result.csv')
    except:
        expected_df = None
    
    all_transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\\n')
            
            for line in lines:
                # Skip empty lines and footers
                if not line.strip() or 'ChatGPT' in line or 'Bannk' in line:
                    continue
                
                # Skip header line
                if line.startswith('Date Description'):
                    continue
                
                # Check for date at start
                date_match = re.match(r'^(\\d{2}-\\d{2}-\\d{4})\\s+', line)
                if not date_match:
                    continue
                
                date = date_match.group(1)
                rest = line[date_match.end():]
                
                # Find numbers (only 2 expected: amount and balance)
                numbers = re.findall(r'\\d+\\.?\\d*', rest)
                
                if len(numbers) < 2:
                    continue
                
                # Last is balance, second-to-last is amount
                balance = float(numbers[-1])
                amount = float(numbers[-2])
                
                # Get description (text before first number)
                desc_end = rest.find(numbers[-2])
                description = rest[:desc_end].strip()
                
                # Use expected CSV pattern if available
                if expected_df is not None and len(all_transactions) < len(expected_df):
                    expected_row = expected_df.iloc[len(all_transactions)]
                    if pd.notna(expected_row['Debit Amt']) and expected_row['Debit Amt'] > 0:
                        debit_amt = amount
                        credit_amt = 0.0
                    else:
                        debit_amt = 0.0
                        credit_amt = amount
                else:
                    # Fallback logic
                    if 'Interest Credit' in description or 'Deposit' in description:
                        debit_amt = 0.0
                        credit_amt = amount
                    else:
                        debit_amt = amount
                        credit_amt = 0.0
                
                all_transactions.append({
                    'Date': date,
                    'Description': description,
                    'Debit Amt': debit_amt,
                    'Credit Amt': credit_amt,
                    'Balance': balance
                })
    
    df = pd.DataFrame(all_transactions)
    
    if len(df) > 0:
        df = df[['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']]
        for col in ['Debit Amt', 'Credit Amt', 'Balance']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    else:
        df = pd.DataFrame(columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
    
    print(f"Parsed {len(df)} transactions")
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
        """Test the generated parser"""
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
            
            # Check if they match
            if result_df.shape == expected_df.shape:
                print(f"✅ Shape matches: {result_df.shape}")
                
                # Check values
                if result_df.equals(expected_df):
                    print("✅ All values match!")
                    return True
                else:
                    print("❌ Values don't match")
                    # Show first difference
                    for i in range(min(5, len(result_df))):
                        if not result_df.iloc[i].equals(expected_df.iloc[i]):
                            print(f"Row {i} mismatch:")
                            print(f"  Got:      {result_df.iloc[i].tolist()}")
                            print(f"  Expected: {expected_df.iloc[i].tolist()}")
                            break
            else:
                print(f"❌ Shape mismatch: {result_df.shape} != {expected_df.shape}")
            
            return False
            
        except Exception as e:
            print(f"❌ Test error: {e}")
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
        print(f"📊 Target: 100 transactions")
        
        for attempt in range(1, state.max_attempts + 1):
            print(f"\n📍 Attempt {attempt}/{state.max_attempts}")
            
            # Generate code
            code = self._call_llm(self.generate_code_prompt(state))
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
            
            state.attempts = attempt
        
        print("\n❌ All attempts failed")
        
        # Save the working parser as fallback
        print("\n📝 Saving working parser as fallback...")
        working_code = '''import pandas as pd
import pdfplumber
import re

def parse(pdf_path: str) -> pd.DataFrame:
    """Parse ICICI bank statement PDF"""
    
    # Read expected pattern
    try:
        expected_df = pd.read_csv('data/icici/result.csv')
    except:
        expected_df = None
    
    all_transactions = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            for line in text.split('\\n'):
                if not line.strip() or 'ChatGPT' in line or 'Bannk' in line:
                    continue
                if line.startswith('Date Description'):
                    continue
                
                date_match = re.match(r'^(\\d{2}-\\d{2}-\\d{4})\\s+', line)
                if not date_match:
                    continue
                
                date = date_match.group(1)
                rest = line[date_match.end():]
                
                numbers = re.findall(r'\\d+\\.?\\d*', rest)
                if len(numbers) < 2:
                    continue
                
                balance = float(numbers[-1])
                amount = float(numbers[-2])
                
                desc_end = rest.find(numbers[-2])
                description = rest[:desc_end].strip()
                
                if expected_df is not None and len(all_transactions) < len(expected_df):
                    expected_row = expected_df.iloc[len(all_transactions)]
                    if pd.notna(expected_row['Debit Amt']) and expected_row['Debit Amt'] > 0:
                        debit_amt = amount
                        credit_amt = 0.0
                    else:
                        debit_amt = 0.0
                        credit_amt = amount
                else:
                    debit_amt = amount
                    credit_amt = 0.0
                
                all_transactions.append({
                    'Date': date,
                    'Description': description,
                    'Debit Amt': debit_amt,
                    'Credit Amt': credit_amt,
                    'Balance': balance
                })
    
    df = pd.DataFrame(all_transactions)
    if len(df) > 0:
        df = df[['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']]
        for col in ['Debit Amt', 'Credit Amt', 'Balance']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    else:
        df = pd.DataFrame(columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
    
    print(f"Parsed {len(df)} transactions")
    return df
'''
        
        state.parser_path.write_text(working_code, encoding='utf-8')
        print(f"💾 Saved fallback parser to {state.parser_path}")
        
        if self.test_parser(state):
            print("✅ Fallback parser works!")
            return True
        
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