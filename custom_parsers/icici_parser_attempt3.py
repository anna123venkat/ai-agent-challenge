#!/usr/bin/env python3
import os
import sys
import json
import argparse
import subprocess
import traceback
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

class LLMProvider(Enum):
    GROQ = "groq"

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
    test_results: List[Dict] = field(default_factory=list)
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

    def analyze_csv_pattern(self, csv_path: Path) -> str:
        df = pd.read_csv(csv_path)
        pattern_info = []
        for i in range(min(10, len(df))):
            row = df.iloc[i]
            desc = row['Description']
            debit = row['Debit Amt']
            credit = row['Credit Amt']
            if pd.isna(credit) and not pd.isna(debit):
                pattern_info.append(f"Row {i}: '{desc}' -> Debit only ({debit})")
            elif pd.isna(debit) and not pd.isna(credit):
                pattern_info.append(f"Row {i}: '{desc}' -> Credit only ({credit})")
            else:
                pattern_info.append(f"Row {i}: '{desc}' -> Both D:{debit} C:{credit}")
        return "\n".join(pattern_info)

    def generate_code_prompt(self, state: AgentState, analysis: Dict) -> str:
        csv_pattern = self.analyze_csv_pattern(state.csv_path)

        trim_instructions = """
IMPORTANT: Do NOT include any docstrings or comment blocks in the generated code.
Only extract lines that appear to represent valid transactions.
A valid transaction line MUST contain a date followed by text and at least 3 numeric values (amounts/balance).
Skip lines like 'Powered by', headers, footers, page numbers, or empty lines.

Before creating the DataFrame, ensure all extracted lists (dates, descriptions, debit_amts, credit_amts, balances) are trimmed to the same minimum length:

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
"""

        return f"""
Generate a minimal Python function named `parse` that parses an ICICI bank statement PDF using `pdfplumber`, as follows:

CRITICAL DISCOVERY from CSV analysis:
{csv_pattern}

{trim_instructions.strip()}
"""

    def run(self, bank_name: str):
        base_path = Path(f"data/{bank_name}")
        pdf_path = base_path / f"{bank_name}_sample.pdf"
        if not pdf_path.exists():
            alt_path = base_path / f"{bank_name} sample.pdf"
            if alt_path.exists():
                pdf_path = alt_path

        csv_path = base_path / "result.csv"
        parser_path = Path(f"custom_parsers/{bank_name}_parser.py")

        state = AgentState(
            bank_name=bank_name,
            pdf_path=pdf_path,
            csv_path=csv_path,
            parser_path=parser_path
        )

        print(f"\n🚀 Starting Bank Parser Agent for {bank_name.upper()}")
        print("📊 Expected: (100, 5) shape")

        for attempt in range(1, state.max_attempts + 1):
            print(f"\n📍 Attempt {attempt}/{state.max_attempts}")
            prompt = self.generate_code_prompt(state, analysis={})
            code = self._call_llm(prompt)

            if code.startswith("```"):
                code = code.strip()
                if code.startswith("```python"):
                    code = code[len("```python"):].strip()
                if code.endswith("```"):
                    code = code[:-3].strip()

            lines = code.splitlines()
            start, end = None, None
            for i, line in enumerate(lines):
                if start is None and line.strip().startswith(("import", "def")):
                    start = i
                if line.strip() != "":
                    end = i
            if start is not None and end is not None:
                code = "\n".join(lines[start:end+1])

            if not code.strip():
                print("Empty code generated. Skipping.")
                continue

            code = code.strip().replace('"""', '').replace("'''", '').replace('`', '')

            temp_path = parser_path.with_name(f"{bank_name}_parser_attempt{attempt}.py")
            try:
                parser_path.parent.mkdir(parents=True, exist_ok=True)
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                print(f"💾 Saved parser to {temp_path}")

                try:
                    compile(code, filename="<parser>", mode="exec")
                except SyntaxError as syn_err:
                    print("🔍 Generated Code with Syntax Error:")
                    print("="*60)
                    print(code)
                    print("="*60)
                    print(f"❌ Syntax error in generated code: {syn_err}")
                    continue
            except Exception as e:
                print(f"❌ Error saving or validating parser: {e}")
                continue

            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("icici_parser", str(temp_path))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                parse_fn = module.parse
                try:
                    df = parse_fn(str(pdf_path))
                except ValueError as ve:
                    print(f"Agent error (ValueError): {ve}")
                    continue
                except Exception as ex:
                    print(f"Agent error (Exception): {ex}")
                    continue

                expected_df = pd.read_csv(csv_path)
                common_cols = ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']

                df = df[common_cols].reset_index(drop=True)
                expected_df = expected_df[common_cols].reset_index(drop=True)

                for col in common_cols:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                    expected_df[col] = pd.to_numeric(expected_df[col], errors='ignore')

                if df.equals(expected_df):
                    print("✅ Parser output matches expected CSV")
                    return
                else:
                    print("❌ Test failed: Output mismatch")
                    try:
                        mismatched = df.compare(expected_df)
                        print(mismatched)
                    except Exception as e:
                        print(f"⚠️ Unable to compare: {e}")
                        print("Agent output columns:", df.columns.tolist())
                        print("Expected columns:", expected_df.columns.tolist())
            except Exception as e:
                print(f"Agent error: {e}")

        print("❌ All attempts failed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Bank name (e.g., icici)")
    args = parser.parse_args()

    agent = BankParserAgent()
    agent.run(args.target)
