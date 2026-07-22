import argparse
import os
from pypdf import PdfReader
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Initialize the OpenAI client (automatically finds your OPENAI_API_KEY)
client = OpenAI()

def extract_text(pdf_path: str, max_pages: int = 5) -> str:
    """
    Reads a PDF and extracts text from the specified number of pages.
    """
    try:
        reader = PdfReader(pdf_path)
        extracted_text = ""
        
        pages_to_read = min(len(reader.pages), max_pages)
        
        for i in range(pages_to_read):
            page = reader.pages[i]
            if page.extract_text():
                extracted_text += page.extract_text() + "\n"
            
        return extracted_text
    
    except Exception as e:
        return f"Error reading PDF: {e}"

def analyze_with_ai(text: str) -> str:
    """
    Sends the extracted text to OpenAI to perform basic risk analysis.
    """
    print("Sending text to OpenAI for analysis (this might take a few seconds)...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert financial risk analyst. Read the provided excerpts from a company's annual report. Identify the top 3 biggest risks mentioned, and output them as a clean, bulleted list. Keep it concise."
                },
                {
                    "role": "user", 
                    "content": text
                }
            ],
            temperature=0.3 # Lower temperature means more factual/less creative responses
        )
        return response.choices[0].message.content
    except Exception as e:
         return f"OpenAI API Error: {e}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RiskLens AI - Financial PDF Analyzer")
    parser.add_argument("file", help="Path to the annual report PDF")
    
    args = parser.parse_args()
    
    print(f"Loading {args.file}...")
    
    # 1. Extract data
    raw_text = extract_text(args.file)
    
    if raw_text.startswith("Error"):
        print(raw_text)
    elif len(raw_text.strip()) == 0:
        print("No text could be extracted from this PDF.")
    else:
        # 2. Process data with AI
        ai_analysis = analyze_with_ai(raw_text)
        
        # 3. Output
        print("\n--- AI RISK ANALYSIS ---")
        print(ai_analysis)
        print("------------------------")