#!/usr/bin/env python3
"""
Autonomous AI Agent for Bank Statement Parser Generation
This agent analyzes bank statement PDFs and generates custom parsers automatically.
"""

import os
import sys
import json
import argparse
import subprocess
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LLM Provider Configuration
class LLMProvider(Enum):
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"

@dataclass
class AgentState:
    """Tracks the agent's current state and history"""
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
    """Autonomous agent that generates bank statement parsers"""
    
    def __init__(self, provider: LLMProvider = LLMProvider.GROQ):
        """Initialize the agent with specified LLM provider"""
        self.provider = provider
        print(f"🤖 Initializing agent with {provider.value.upper()} provider...")
        self.llm = self._initialize_llm()
        print(f"✅ Agent ready with {provider.value.upper()}")
        
    def _initialize_llm(self):
        """Initialize the LLM based on provider"""
        if self.provider == LLMProvider.ANTHROPIC:
            try:
                import anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not found in environment. Please set it in .env file")
                return anthropic.Anthropic(api_key=api_key)
            except ImportError:
                print("Please install anthropic: pip install anthropic")
                sys.exit(1)
                
        elif self.provider == LLMProvider.GOOGLE:
            try:
                import google.generativeai as genai
                api_key = os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY"))
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not found in environment. Please set it in .env file")
                genai.configure(api_key=api_key)
                return genai.GenerativeModel('gemini-1.5-flash')
            except ImportError:
                print("Please install google-generativeai: pip install google-generativeai")
                sys.exit(1)
                
        elif self.provider == LLMProvider.GROQ:
            try:
                from groq import Groq
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise ValueError(
                        "GROQ_API_KEY not found in environment.\n"
                        "Please set it in .env file:\n"
                        "1. Create a .env file in the project root\n"
                        "2. Add: GROQ_API_KEY=your_api_key_here\n"
                        "3. Get your free API key from: https://console.groq.com/"
                    )
                return Groq(api_key=api_key)
            except ImportError:
                print("Please install groq: pip install groq")
                sys.exit(1)
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM with the given prompt"""
        try:
            if self.provider == LLMProvider.ANTHROPIC:
                response = self.llm.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
                
            elif self.provider == LLMProvider.GOOGLE:
                response = self.llm.generate_content(prompt)
                return response.text
                
            elif self.provider == LLMProvider.GROQ:
                response = self.llm.chat.completions.create(
                    model="llama3-70b-8192",  # Fast and capable model
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4000,
                    temperature=0.1  # Lower temperature for more consistent code generation
                )
                return response.choices[0].message.content
                
        except Exception as e:
            print(f"LLM call failed: {e}")
            return ""
    
    def analyze_data(self, state: AgentState) -> Dict:
        """Analyze the PDF structure and CSV schema"""
        print(f"📊 Analyzing {state.bank_name} bank statement structure...")
        
        # Read CSV to understand the expected schema
        try:
            df = pd.read_csv(state.csv_path)
            schema = {
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "sample_rows": df.head(3).to_dict('records'),
                "shape": df.shape
            }
        except Exception as e:
            print(f"Error reading CSV: {e}")
            schema = {}
        
        # Analyze PDF structure (basic analysis without parsing)
        pdf_info = {
            "path": str(state.pdf_path),
            "exists": state.pdf_path.exists(),
            "size": state.pdf_path.stat().st_size if state.pdf_path.exists() else 0
        }
        
        return {
            "csv_schema": schema,
            "pdf_info": pdf_info
        }
    
    def plan_approach(self, state: AgentState, analysis: Dict) -> str:
        """Plan the parsing approach based on analysis"""
        print("🎯 Planning parsing approach...")
        
        prompt = f"""
        You are an expert Python developer creating a bank statement PDF parser.
        
        Target Bank: {state.bank_name}
        
        Expected CSV Schema:
        {json.dumps(analysis['csv_schema'], indent=2)}
        
        Create a detailed plan for parsing the PDF that includes:
        1. Required libraries (pdfplumber, PyPDF2, etc.)
        2. Text extraction strategy
        3. Pattern matching approach for each column
        4. Data cleaning and validation steps
        5. Error handling strategy
        
        Previous errors to avoid: {state.errors[-3:] if state.errors else 'None'}
        
        Provide a concise, technical plan.
        """
        
        plan = self._call_llm(prompt)
        print(f"📝 Plan created: {len(plan)} characters")
        return plan
    
    def generate_parser_code(self, state: AgentState, analysis: Dict, plan: str) -> str:
        """Generate the parser code based on the plan"""
        print(f"💻 Generating parser code (Attempt {state.attempts + 1}/{state.max_attempts})...")
        
        prompt = f"""
        Generate a complete Python parser for {state.bank_name} bank statements.
        
        Requirements:
        - Function signature: def parse(pdf_path: str) -> pd.DataFrame
        - Must return a DataFrame with these exact columns: {analysis['csv_schema']['columns']}
        - Use appropriate PDF parsing library (pdfplumber recommended)
        - Handle errors gracefully
        - Include proper imports
        
        Plan to follow:
        {plan}
        
        Previous failed code (if any):
        {state.current_code if state.attempts > 0 else 'None'}
        
        Previous errors to fix:
        {state.errors[-1] if state.errors else 'None'}
        
        Generate ONLY the Python code, no explanations. The code should be complete and runnable.
        Start with imports and end with the parse function.
        """
        
        code = self._call_llm(prompt)
        
        # Clean the code (remove markdown formatting if present)
        code = self._clean_generated_code(code)
        
        return code
    
    def _clean_generated_code(self, code: str) -> str:
        """Clean generated code from markdown or other formatting"""
        # Remove markdown code blocks
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        # Ensure proper imports are at the top
        if "import pandas as pd" not in code:
            code = "import pandas as pd\n" + code
        
        return code.strip()
    
    def save_parser(self, state: AgentState, code: str) -> bool:
        """Save the generated parser code to file"""
        print(f"💾 Saving parser to {state.parser_path}...")
        
        try:
            # Ensure directory exists
            state.parser_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the code
            with open(state.parser_path, 'w') as f:
                f.write(code)
            
            print(f"✅ Parser saved successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error saving parser: {e}")
            state.errors.append(f"Save error: {e}")
            return False
    
    def test_parser(self, state: AgentState) -> Tuple[bool, str]:
        """Test the generated parser against expected output"""
        print("🧪 Testing generated parser...")
        
        try:
            # Create a test script
            test_code = f"""
import sys
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the generated parser
from custom_parsers.{state.bank_name}_parser import parse

# Test the parser
pdf_path = r"{state.pdf_path.as_posix()}"
expected_csv_path = r"{state.csv_path.as_posix()}"

# Parse the PDF
result_df = parse(pdf_path)

# Load expected output
expected_df = pd.read_csv(expected_csv_path)

# Compare DataFrames
if result_df.shape != expected_df.shape:
    print(f"Shape mismatch: {{result_df.shape}} != {{expected_df.shape}}")
    sys.exit(1)

# Check columns
if list(result_df.columns) != list(expected_df.columns):
    print(f"Column mismatch: {{list(result_df.columns)}} != {{list(expected_df.columns)}}")
    sys.exit(1)

print("✅ Parser test passed!")
"""
            
            # Save test script temporarily
            test_file = Path("temp_test.py")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_code)

            
            # Run the test
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up
            test_file.unlink(missing_ok=True)
            
            if result.returncode == 0:
                print("✅ All tests passed!")
                return True, result.stdout
            else:
                error_msg = f"Test failed:\n{result.stderr}\n{result.stdout}"
                print(f"❌ {error_msg}")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "Test timeout (>30 seconds)"
            print(f"❌ {error_msg}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Test error: {e}\n{traceback.format_exc()}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def self_debug(self, state: AgentState, error: str) -> str:
        """Analyze errors and suggest fixes"""
        print("🔧 Self-debugging...")
        
        prompt = f"""
        The parser code failed with this error:
        {error}
        
        Current code:
        {state.current_code}
        
        Analyze the error and provide:
        1. Root cause of the failure
        2. Specific fixes needed
        3. Code sections that need modification
        
        Be concise and technical.
        """
        
        debug_analysis = self._call_llm(prompt)
        print("🔍 Debug analysis complete")
        return debug_analysis
    
    def run(self, bank_name: str) -> bool:
        """Main agent loop"""
        print(f"\n🚀 Starting Bank Parser Agent for {bank_name.upper()}")
        print("=" * 60)
        
        # Initialize state
        state = AgentState(
            bank_name=bank_name,
            pdf_path=Path(f"data/{bank_name}/{bank_name} sample.pdf"),
            csv_path=Path(f"data/{bank_name}/result.csv"),
            parser_path=Path(f"custom_parsers/{bank_name}_parser.py")
        )
        
        # Check if required files exist
        if not state.pdf_path.exists():
            print(f"❌ PDF not found: {state.pdf_path}")
            return False
        if not state.csv_path.exists():
            print(f"❌ CSV not found: {state.csv_path}")
            return False
        
        # Analyze data once
        analysis = self.analyze_data(state)
        
        # Main agent loop
        while state.attempts < state.max_attempts and not state.success:
            state.attempts += 1
            print(f"\n📍 Attempt {state.attempts}/{state.max_attempts}")
            print("-" * 40)
            
            # Plan approach
            plan = self.plan_approach(state, analysis)
            
            # Generate code
            code = self.generate_parser_code(state, analysis, plan)
            state.current_code = code
            
            # Save parser
            if not self.save_parser(state, code):
                continue
            
            # Test parser
            success, result = self.test_parser(state)
            
            if success:
                state.success = True
                print(f"\n🎉 SUCCESS! Parser generated and validated!")
                print(f"📄 Parser saved to: {state.parser_path}")
                break
            else:
                state.errors.append(result)
                state.test_results.append({"attempt": state.attempts, "error": result})
                
                if state.attempts < state.max_attempts:
                    # Self-debug and prepare for next attempt
                    debug_info = self.self_debug(state, result)
                    print(f"📝 Debug info: {debug_info[:200]}...")
                    print(f"🔄 Retrying with improvements...")
        
        # Final summary
        print("\n" + "=" * 60)
        if state.success:
            print("✅ AGENT COMPLETED SUCCESSFULLY")
            print(f"Parser location: {state.parser_path}")
            print(f"Total attempts: {state.attempts}")
        else:
            print("❌ AGENT FAILED TO GENERATE VALID PARSER")
            print(f"Attempts made: {state.attempts}")
            print("Recent errors:")
            for error in state.errors[-2:]:
                print(f"  - {error[:100]}...")
        
        return state.success

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AI Agent for Bank Statement Parser Generation"
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Target bank name (e.g., icici)"
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "google", "groq"],
        default="groq",
        help="LLM provider to use (default: groq)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with verbose output"
    )
    
    args = parser.parse_args()
    
    # Configure provider
    provider_map = {
        "anthropic": LLMProvider.ANTHROPIC,
        "google": LLMProvider.GOOGLE,
        "groq": LLMProvider.GROQ
    }
    
    try:
        # Initialize and run agent
        agent = BankParserAgent(provider=provider_map[args.provider])
        success = agent.run(args.target)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n📝 Setup Instructions:")
        print("1. Create a .env file in the project root")
        print("2. Add your API key:")
        print("   GROQ_API_KEY=your_api_key_here")
        print("3. Get a free API key from: https://console.groq.com/")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.debug:
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()