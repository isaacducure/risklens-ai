"""
Runs a fixed set of questions through the pipeline and shows the answers
side by side, so accuracy can be judged consistently after any change.
Scoring is done by you reading each row — the model doesn't grade itself.
"""
from analyzer import extract_pages, chunk_pages, embed_chunks, find_relevant_chunks_semantic, analyze_with_ai

PDF = "treport25.pdf"

# category, question, what you expect (from reading the report yourself)
EVAL = [
    ("simple", "What was total revenue in 2025 and the change vs 2024?",
     "$94.83bn, down $2.86bn"),
    ("simple", "How much cash and investments did Tesla end 2025 with, and the change vs 2024?",
     "$44.06bn, up $7.50bn"),
    ("simple", "How many bitcoin units does Tesla hold and what was the 2025 fair value?",
     "11,509 units, fair value $1,007m"),
    ("table", "What was interest income in 2025?",
     "$1,680m"),
    ("table", "What was total stockholders' equity in 2025 and 2024?",
     "$82,137m and $72,913m"),
    ("text", "Has Tesla paid dividends, and does it plan to?",
     "Never paid, none anticipated"),
    ("text", "How many vehicles produced and delivered in 2025?",
     "~1.66m produced, ~1.64m delivered"),
    ("text", "Expected capital expenditure in 2026 and why?",
     ">$20bn, driven by AI/compute, manufacturing, fleet"),
    ("unanswerable-future", "What percentage of revenue went to R&D in 2027 vs 2023?",
     "SHOULD REFUSE — 2027 not in report"),
    ("unanswerable-premise", "Why is Tesla's 2025 gross profit only $9,000m?",
     "SHOULD CHALLENGE the premise, not justify it"),
]

def run():
    print(f"Loading {PDF}...")
    pages = extract_pages(PDF)
    chunks = chunk_pages(pages, pages_per_chunk=1)
    chunks = embed_chunks(chunks)
    print(f"{len(pages)} pages, {len(chunks)} chunks (embedded once)\n")

    for i, (cat, q, expected) in enumerate(EVAL, 1):
        relevant = find_relevant_chunks_semantic(chunks, q)
        if not relevant:
            answer = "(no relevant sections found)"
            pages_used = "-"
        else:
            pages_used = ", ".join(f"{c['start_page']}-{c['end_page']}" for c in relevant)
            context = "\n\n".join(c["text"] for c in relevant)
            answer = analyze_with_ai(context, q)

        print("=" * 70)
        print(f"Q{i} [{cat}]  {q}")
        print(f"EXPECTED : {expected}")
        print(f"PAGES    : {pages_used}")
        print(f"GOT      : {answer}")
        print()

if __name__ == "__main__":
    run()