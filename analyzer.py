import argparse
from pypdf import PdfReader

def extract_text(pdf_path: str, max_pages: int = 5) -> str:
    """
    Reads a PDF and extracts text from the specified number of pages.
    We limit to max_pages initially to keep processing fast while testing.
    """
    try:
        reader = PdfReader(pdf_path)
        extracted_text = ""
        
        # Determine how many pages to read
        pages_to_read = min(len(reader.pages), max_pages)
        
        for i in range(pages_to_read):
            page = reader.pages[i]
            extracted_text += page.extract_text() + "\n"
            
        return extracted_text
    
    except Exception as e:
        return f"Error reading PDF: {e}"

def generate_summary_stub(text: str) -> str:
    """
    Placeholder for Week 2. 
    Right now, it just returns word count and a snippet.
    Next week, we pass this text to an LLM API.
    """
    word_count = len(text.split())
    preview = text[:200].replace('\n', ' ')
    
    summary = (
        f"--- PDF EXTRACTION SUCCESS ---\n"
        f"Total words extracted (preview): {word_count}\n"
        f"Snippet: {preview}...\n"
        f"------------------------------"
    )
    return summary

if __name__ == "__main__":
    # Set up command-line arguments
    parser = argparse.ArgumentParser(description="RiskLens AI - Financial PDF Analyzer")
    parser.add_argument("file", help="Path to the annual report PDF")
    
    args = parser.parse_args()
    
    print(f"Loading {args.file}...")
    
    # 1. Extract data
    raw_text = extract_text(args.file)
    
    # 2. Process data
    result = generate_summary_stub(raw_text)
    
    # 3. Output
    print(result)
