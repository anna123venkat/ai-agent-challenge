#!/usr/bin/env python3
"""
Quick test script to verify the agent is working
Run this to test your setup before the main challenge
"""

import os
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
import sys
from pathlib import Path

def check_setup():
    """Check if the environment is properly set up"""
    print("🔍 Checking AI Agent Setup...")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("⚠️  Warning: Python 3.8+ recommended")
    
    # Check required directories
    dirs_to_check = ['data/icici', 'custom_parsers', 'tests']
    for dir_path in dirs_to_check:
        if Path(dir_path).exists():
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Missing directory: {dir_path}")
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"   Created: {dir_path}")
    
    # Check for required files
    files_to_check = [
        'data/icici/icici sample.pdf',
        'data/icici/result.csv',
        'agent.py'
    ]
    
    missing_files = []
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"✅ File exists: {file_path}")
        else:
            print(f"⚠️  Missing file: {file_path}")
            missing_files.append(file_path)
    
    # Check Python packages
    print("\n📦 Checking Python packages...")
    required_packages = {
        'pandas': 'pandas',
        'groq': 'groq',
        'pdfplumber': 'pdfplumber',
        'PyPDF2': 'PyPDF2',
        'pytest': 'pytest'
    }
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name} installed")
        except ImportError:
            print(f"❌ {package_name} not installed - run: pip install {package_name}")
    
    # Check API configuration
    print("\n🔑 Checking API configuration...")
    if os.getenv('GROQ_API_KEY'):
        print("✅ GROQ_API_KEY found in environment")
    else:
        print("📌 GROQ_API_KEY not in env (will use embedded key)")
    
    # Test Groq connection
    try:
        from groq import Groq

        # Quick test call
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": "Say 'API working' in 3 words"}],
            max_tokens=10
        )
        print(f"✅ Groq API connection successful")
        print(f"   Response: {response.choices[0].message.content[:50]}")
    except Exception as e:
        print(f"❌ Groq API test failed: {e}")
    
    print("\n" + "=" * 50)
    if missing_files:
        print("⚠️  Setup incomplete - add missing files:")
        for f in missing_files:
            print(f"   - {f}")
        print("\n💡 Tip: Make sure you have the ICICI sample PDF and CSV")
    else:
        print("✅ Setup complete! Ready to run agent.py")
        print("\n🚀 Run the agent with:")
        print("   python agent.py --target icici")
    
    return len(missing_files) == 0

if __name__ == "__main__":
    print("🤖 AI Agent Challenge - Setup Test")
    print("===================================\n")
    
    success = check_setup()
    
    if success:
        print("\n🎯 Would you like to run the agent now? (y/n): ", end="")
        response = input().strip().lower()
        if response == 'y':
            print("\n🚀 Starting agent...\n")
            os.system("python agent.py --target icici")
    else:
        print("\n📋 Please complete the setup first")
        sys.exit(1)