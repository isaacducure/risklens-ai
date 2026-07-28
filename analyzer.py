import argparse
import os
from pypdf import PdfReader
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Initialize the OpenAI client (automatically finds your OPENAI_API_KEY)
client = OpenAI()

def extract_pages(pdf_path: str) -> list[dict]:
    """
    Reads a PDF and returns a list of pages.
    Each page is a dict: {"page": 1, "text": "..."}
    Keeping page numbers attached is what makes citations possible later.
    """
    try:
        reader = PdfReader(pdf_path)
        pages = []

        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                pages.append({"page": i, "text": text})

        return pages

    except Exception as e:
        print(f"Error reading PDF: {e}")
        return []


def pages_to_text(pages: list[dict]) -> str:
    """
    Joins pages into one string, with a page marker before each.
    The markers are what let the AI say 'this came from page 47'.
    """
    return "\n\n".join(f"[PAGE {p['page']}]\n{p['text']}" for p in pages)

def chunk_pages(pages: list[dict], pages_per_chunk: int = 3) -> list[dict]:
    """
    Groups pages into small chunks. Each chunk records which pages it spans,
    so a citation can point back to real page numbers.
    """
    chunks = []
    for i in range(0, len(pages), pages_per_chunk):
        group = pages[i:i + pages_per_chunk]
        chunks.append({
            "start_page": group[0]["page"],
            "end_page": group[-1]["page"],
            "text": "\n".join(f"[PAGE {p['page']}]\n{p['text']}" for p in group)
        })
    return chunks


def find_relevant_chunks(chunks: list[dict], query: str, top_n: int = 5) -> list[dict]:
    """
    Scores each chunk by how many query words it contains, returns the best ones.
    Crude, but transparent and fast.
    """
    query_words = [w.lower() for w in query.split() if len(w) > 3]

    scored = []
    for chunk in chunks:
        text_lower = chunk["text"].lower()
        score = sum(text_lower.count(word) for word in query_words)
        scored.append((score, chunk))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [chunk for score, chunk in scored[:top_n] if score > 0]

def analyze_with_ai(context: str, question: str) -> str:
    """
    Answers a question using ONLY the supplied context, with page citations.
    """
    print("Sending relevant sections to OpenAI...")

    system_prompt = (
        "You are a financial analyst. Answer using ONLY the provided extracts "
        "from a company's annual report. The extracts contain [PAGE n] markers. "
        "After every factual claim, cite the page marker that immediately "
        "precedes the text you used, e.g. [p.47]. Quote the exact figure as "
        "printed. If the extracts do not contain the answer, say so explicitly. "
        "Never guess or use outside knowledge."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"EXTRACTS:\n{context}\n\nQUESTION: {question}"}
            ],
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI API Error: {e}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RiskLens AI - Financial PDF Analyzer")
    parser.add_argument("file", help="Path to the annual report PDF")
    parser.add_argument("question", help="Question to ask about the report")

    args = parser.parse_args()

    print(f"Loading {args.file}...")
    pages = extract_pages(args.file)

    if not pages:
        print("No text could be extracted from this PDF.")
    else:
        print(f"Extracted {len(pages)} pages.")
        chunks = chunk_pages(pages)
        relevant = find_relevant_chunks(chunks, args.question)

        if not relevant:
            print("No relevant sections found for that question.")
        else:
            print(f"Selected {len(relevant)} sections: " +
                  ", ".join(f"p.{c['start_page']}-{c['end_page']}" for c in relevant))

            context = "\n\n".join(
                f"[PAGES {c['start_page']}-{c['end_page']}]\n{c['text']}" for c in relevant
            )

            answer = analyze_with_ai(context, args.question)
            print("\n--- ANSWER ---")
            print(answer)
            print("--------------")