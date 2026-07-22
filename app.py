import streamlit as st
from pypdf import PdfReader
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
client = OpenAI()

def extract_text(uploaded_file, max_pages=5):
    """Reads a PDF directly from Streamlit's file uploader."""
    try:
        # We pass the uploaded file directly to PyPDF
        reader = PdfReader(uploaded_file)
        extracted_text = ""
        
        pages_to_read = min(len(reader.pages), max_pages)
        for i in range(pages_to_read):
            page = reader.pages[i]
            if page.extract_text():
                extracted_text += page.extract_text() + "\n"
        return extracted_text
    except Exception as e:
        return f"Error reading PDF: {e}"

def analyze_with_ai(text):
    """Sends the extracted text to OpenAI."""
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
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI API Error: {e}"

# --- STREAMLIT WEB INTERFACE ---

# 1. Page Setup
st.set_page_config(page_title="RiskLens AI", page_icon="📊")
st.title("📊 RiskLens AI Platform")
st.write("Upload a corporate annual report to instantly extract and quantify key risk factors.")

# 2. File Uploader Widget
uploaded_file = st.file_uploader("Upload PDF Report", type="pdf")

# 3. Process the File
if uploaded_file is not None:
    st.success("File uploaded successfully!")
    
    # Create a button to start the analysis
    if st.button("Analyze Risks"):
        
        # Show a loading spinner while the AI thinks
        with st.spinner("Extracting data and running AI analysis..."):
            
            raw_text = extract_text(uploaded_file)
            
            if raw_text.startswith("Error"):
                st.error(raw_text)
            else:
                ai_results = analyze_with_ai(raw_text)
                
                # Display the results in a clean box
                st.subheader("⚠️ AI Risk Assessment")
                st.write(ai_results)