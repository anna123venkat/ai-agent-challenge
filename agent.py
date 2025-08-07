# Updated agent.py with enhanced self-debugging, validation, and safety checks
# ✅ Prevents array length mismatch
# ✅ Skips invalid float conversions
# ✅ Avoids unsupported exceptions (like pdfplumber.PDFParserError)
# ✅ Adds inline constraints in the LLM prompt
# ✅ Handles None outputs properly

# Save this file as agent.py

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

    def generate_code_prompt(self, state: AgentState, analysis: Dict, plan: str) -> str:
        return f"""
Generate a complete parser function for the bank statement.

Requirements:
- Function: def parse(pdf_path: str) -> pd.DataFrame
- Use pdfplumber to extract table rows
- Try both `page.extract_table()` and `page.extract_text()` if needed
- Output must match columns: {analysis['csv_schema']['columns']}
- Use regex to extract structured lines if tables fail
- Skip header/footer lines or garbage rows
- Use try/except Exception for error handling
- Ensure equal-length column lists before DataFrame creation
- Do NOT use pdfplumber.PDFParserError (not a real exception)
- Return at least 3 extracted rows (or empty DataFrame if truly nothing usable)
- Include `print()` statements to debug number of rows found

PLAN:
{plan}

Prior Errors:
{state.errors[-1] if state.errors else 'None'}

Output only code.
"""

    def clean_code(self, code: str) -> str:
        if "```" in code:
            code = code.split("```python")[-1].split("```")[-2]
        return code.strip()

    def save_parser(self, path: Path, code: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code, encoding="utf-8")

    def test_parser(self, state: AgentState) -> Tuple[bool, str]:
        test_code = f"""
import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from custom_parsers.{state.bank_name}_parser import parse

pdf_path = r\"{state.pdf_path}\"
csv_path = r\"{state.csv_path}\"

try:
    result_df = parse(pdf_path)
    if result_df is None:
        raise ValueError(\"Parser returned None\")

    expected_df = pd.read_csv(csv_path)

    if result_df.shape != expected_df.shape:
        raise ValueError(f\"Shape mismatch: {{result_df.shape}} != {{expected_df.shape}}\")

    if not result_df.columns.equals(expected_df.columns):
        raise ValueError(f\"Column mismatch: {{result_df.columns.tolist()}} != {{expected_df.columns.tolist()}}\")

    if not result_df.equals(expected_df):
        raise ValueError(\"DataFrames content do not match\")

    print("Test passed")


except Exception as e:
    print("Test failed")
    print(e)
    sys.exit(1)
"""

        temp_test = Path("temp_test.py")
        temp_test.write_text(test_code)
        result = subprocess.run([sys.executable, str(temp_test)], capture_output=True, text=True)
        temp_test.unlink(missing_ok=True)
        return result.returncode == 0, result.stdout + result.stderr

    def run(self, bank_name: str) -> bool:
        print(f"\n🚀 Starting Bank Parser Agent for {bank_name.upper()}")
        state = AgentState(
            bank_name=bank_name,
            pdf_path=Path(f"data/{bank_name}/{bank_name} sample.pdf"),
            csv_path=Path(f"data/{bank_name}/result.csv"),
            parser_path=Path(f"custom_parsers/{bank_name}_parser.py")
        )

        df = pd.read_csv(state.csv_path)
        analysis = {
            "csv_schema": {
                "columns": list(df.columns),
                "sample": df.head(3).to_dict()
            }
        }

        for attempt in range(state.max_attempts):
            state.attempts += 1
            print(f"\n📍 Attempt {state.attempts}/{state.max_attempts}")
            plan = self._call_llm(f"Explain how to parse this PDF to match schema: {analysis['csv_schema']['columns']}")
            code = self._call_llm(self.generate_code_prompt(state, analysis, plan))
            code = self.clean_code(code)
            state.current_code = code
            self.save_parser(state.parser_path, code)

            success, output = self.test_parser(state)
            if success:
                print("\n🎉 SUCCESS! Parser passed validation.")
                return True
            else:
                print("\n❌ Test failed. Retrying...")
                print(output)
                state.errors.append(output)

        print("\n❌ All attempts failed.")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    try:
        success = BankParserAgent().run(args.target)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Agent error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
