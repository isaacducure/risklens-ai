\# RiskLens



An AI tool that reads a company's annual report and answers questions about it — citing the exact page each answer comes from, so every claim is traceable to the source document.



Built as a personal learning project (2026) by a first-year Actuarial Mathematics student, to explore how retrieval-augmented AI can be applied to financial documents in a way that is \*\*measurable and honest\*\* rather than just plausible-sounding.



\---



\## What it does



Give it a company's annual report (a PDF) and ask a question in plain English — "what was total revenue?", "how much debt does the company have?", "what are the principal risks?" — and it returns an answer grounded in the document, with a page citation for every factual claim. If the answer isn't in the report, it says so rather than inventing one.



Example:



```

> python analyzer.py report.pdf "what was total revenue"

Total revenue in 2025 was $94,827 million, a decrease of $2,863 million vs 2024 \[p.40].

```



\## Why it's built this way



The core problem with using a language model on a long document is that the model can produce confident, fluent answers that aren't actually supported by the source. The whole design of this project is aimed at preventing that:



\- \*\*Every answer is traceable.\*\* Page numbers are attached to the text at the moment it's extracted, so any claim can be traced back to a specific page. Provenance is preserved from ingestion, not reconstructed later.

\- \*\*The model only sees real text.\*\* It answers using only extracts retrieved from the document, and is instructed to say when the answer isn't present rather than fill the gap.

\- \*\*It's measured, not guessed.\*\* A fixed evaluation set of questions with hand-verified answers is used to score accuracy, so improvements can be proven rather than assumed.



\## How it works



1\. \*\*Extract\*\* — read the PDF page by page, keeping each page's text tagged with its page number.

2\. \*\*Chunk\*\* — group the text into small chunks, each recording which pages it spans.

3\. \*\*Retrieve\*\* — given a question, find the most relevant chunks using semantic (embedding-based) search, which matches on \*meaning\* rather than shared keywords.

4\. \*\*Answer\*\* — send only those chunks to the language model, with instructions to cite the page behind every claim and to refuse when the answer isn't in the extracts.



Embeddings are computed once per document and reused across questions (cached), rather than recomputed each time.



\## Measured results



Accuracy is tracked with a 10-question evaluation set (`evaluate.py`) covering simple lookups, figures buried in tables, text-based questions, and deliberately unanswerable questions (to test whether the tool correctly refuses instead of inventing).



| Retrieval method | Score |

|---|---|

| Keyword matching (baseline) | 5 / 10 |

| Semantic search (embeddings) | \*\*9 / 10\*\* |



The improvement came from a single deliberate change — replacing keyword matching with embedding-based retrieval — and was verified by re-running the same evaluation set. The one remaining failure is understood and documented (see below).



\## Known limitations



Being explicit about what doesn't work yet, because a tool like this is only trustworthy if its limits are known:



\- \*\*One retrieval case still fails.\*\* A question about the company's bitcoin holdings isn't retrieved correctly, because the relevant page is dominated by unrelated accounting text (diluting its meaning), the question's wording differs from the document's, and other pages repeat the query words without holding the answer. The fix — hybrid keyword + semantic retrieval — is identified but not yet built; at 9/10 it was a deliberate choice to prioritise other work.

\- \*\*Citations use the PDF page position\*\*, which can differ from the printed page number (annual reports have unnumbered cover pages). This needs reconciling.

\- \*\*Single document at a time.\*\* No persistent store across many companies yet.

\- \*\*Impact/financial estimates are out of scope by design\*\* — the tool retrieves and explains what the document says; it does not produce its own financial projections.



\## Project notes



`NOTES.md` is a running log of the build — every problem hit, what caused it, how it was fixed, and why it mattered. It's the honest development history rather than a polished summary, and it's where the reasoning behind each decision lives.



\## Tech



Python · \[pypdf](https://pypdf.readthedocs.io/) for PDF extraction · OpenAI API (embeddings + chat) · NumPy for vector maths · Git/GitHub.



\## Running it



```bash

pip install -r requirements.txt          # pypdf, openai, numpy, python-dotenv

\# add your OpenAI key to a .env file as OPENAI\_API\_KEY=...   (never commit this)

python analyzer.py <report.pdf> "<your question>"

python evaluate.py                        # run the evaluation set

```



\---



\*This is a learning project and a demonstration of method — grounded retrieval, measured accuracy, and transparent reasoning — not a production financial tool.\*

