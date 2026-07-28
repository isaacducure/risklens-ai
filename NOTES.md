\# RiskLens AI — Build Notes



An AI tool that reads company annual reports and answers questions about them,

citing the page each answer came from. Built summer 2025.



Test document: Tesla 2025 annual report (139 pages).



\---



\## Setup (Week 1)



Built a command-line script that reads a PDF and prints a summary.



\*\*Tools:\*\* Python, `pypdf` to read PDFs, Git and GitHub to save versions.



\*\*Things worth knowing:\*\*

\- Virtual environment (`venv`) — keeps this project's libraries separate from

&#x20; everything else on the laptop, so upgrading something here can't break

&#x20; another project.

\- `.env` file — the OpenAI API key lives in a separate hidden file, listed in

&#x20; `.gitignore` so it never gets uploaded to GitHub. Anyone who gets the key can

&#x20; spend my money. Never write secrets inside the code itself.

\- Functions — each job (read the PDF, ask the AI) is its own block of code.

&#x20; Proved useful later: I completely rewrote the PDF reader and nothing else

&#x20; needed touching.



\---



\## Problem 1 — It was reading 5 pages out of 139



\*\*What happened.\*\* The first version had `max\\\_pages = 5`, which was meant to

make testing fast. I forgot it was there. The app was reading the cover,

contents and chairman's letter of a 139-page report — about 3% of it — and

still returning confident lists of "the company's principal risks."



\*\*Why it was wrong.\*\* Those answers weren't from the document. The AI knows

roughly what a car company's annual report says, so it produced plausible

generic risks and I had no way to tell. It looked like it was working.



\*\*How I found it.\*\* Checked an answer against the actual report instead of

just reading it and nodding.



\*\*The fix.\*\* Read every page, and store the text page by page instead of as

one big lump:



```python

def extract\\\_pages(pdf\\\_path):

\&#x20;   reader = PdfReader(pdf\\\_path)

\&#x20;   pages = \\\[]

\&#x20;   for i, page in enumerate(reader.pages, start=1):

\&#x20;       text = page.extract\\\_text()

\&#x20;       if text and text.strip():

\&#x20;           pages.append({"page": i, "text": text})

\&#x20;   return pages

```



\*\*The key decision.\*\* The page number is attached at the moment the text is

read. Once the text is combined into one string, there is no way to work out

which page a sentence came from. Provenance has to be recorded at the start or

it's gone for good.



\*\*Why this matters.\*\* The whole point of the product is that every answer is

traceable to a source. An AI that sounds right but can't be checked is worse

than useless in finance — it's confidently wrong, which is harder to catch than

obviously wrong.



\---



\## Problem 2 — Too much text to send at once



\*\*What happened.\*\* With all 139 pages being read, the OpenAI request failed:

147,433 tokens sent against a 128,000 limit.



\*\*Why it happens.\*\* An AI model can only consider a fixed amount of text in one

go. A full annual report doesn't fit. This is a hard limit, not a bug.



\*\*The idea that solves it.\*\* A question about revenue doesn't need the whole

report — it needs the pages with the revenue figures. So: split the document

into small chunks, find the chunks relevant to the question, send only those.

This approach is called RAG (retrieval-augmented generation).



\*\*The fix.\*\* Group pages into chunks of 3, then score each chunk by how many

words from the question appear in it, and send the top 5.



```python

def find\\\_relevant\\\_chunks(chunks, query, top\\\_n=5):

\&#x20;   query\\\_words = \\\[w.lower() for w in query.split() if len(w) > 3]

\&#x20;   scored = \\\[]

\&#x20;   for chunk in chunks:

\&#x20;       text\\\_lower = chunk\\\["text"].lower()

\&#x20;       score = sum(text\\\_lower.count(word) for word in query\\\_words)

\&#x20;       scored.append((score, chunk))

\&#x20;   scored.sort(key=lambda pair: pair\\\[0], reverse=True)

\&#x20;   return \\\[chunk for score, chunk in scored\\\[:top\\\_n] if score > 0]

```



\*\*A decision I made on purpose.\*\* Most people jump straight to a vector

database for this. I used simple word-matching first because I can explain

exactly how it works, I can see which pages it picked, and it gives me a

baseline to measure against when I do upgrade it. Financial documents use

specific language ("gross margin", "indebtedness"), so word matching works

better here than it would on ordinary writing. I'll switch to embeddings when I

can show word matching failing — not before.



\*\*Useful side effect.\*\* The app prints which pages it selected before the AI

sees anything. So when an answer is wrong I can tell whether it picked the

wrong pages, or picked the right pages and misread them. Two different

problems, two different fixes.



\---



\## Problem 3 — Citations pointed at the wrong pages



\*\*What happened.\*\* Revenue answer: "$94,827 million \[p.52]". The figure is real

and correctly quoted — but it's on page 53. Debt answer cited p.76 when the

sentence is on p.24.



\*\*Why it went wrong.\*\* I was labelling each chunk with a page \*range\*

("PAGES 52-54") in a header above the text. The model had no way to tell which

page within that range a given sentence came from, so it cited the first number

in the range. Roughly right, reliably wrong.



Two smaller issues found at the same time: I only stored pages containing text,

so 137 were kept out of 139 actual pages — meaning my printed count didn't match

the document. And the page number in a PDF viewer isn't the number printed on

the page, because annual reports have unnumbered covers. I need to state which

one I'm citing.



\*\*The fix.\*\* Put a `\[PAGE n]` marker inside the extract text at every page

boundary, not just in a header above the chunk, and instruct the model to cite

the marker immediately preceding the text it used.



```python

"text": "\\n".join(f"\[PAGE {p\['page']}]\\n{p\['text']}" for p in group)

```



\*\*Result.\*\* Revenue now cites p.53, debt cites p.24. Both verified correct

against the source document.



\*\*What I'm not claiming.\*\* Two correct answers isn't a working system — it's two

correct answers. The fix might be right, or it might happen to work on these two

questions. That's why the next step is a fixed set of questions with verified

answers, so I can measure accuracy rather than guess at it.



\*\*Why this mattered.\*\* The product's entire claim is that every answer is

traceable to a source. A citation that points at the wrong page disproves that

in ten seconds — and it does it while looking completely professional. This was

the second time the project demonstrated its own thesis against itself: the

dangerous failure isn't the one that crashes, it's the one that looks like

success.

\---



\## Things I got told that I later corrected



\*\*"Low temperature stops hallucination."\*\* Temperature controls how random the

model's word choices are. Setting it low (0.1) makes output consistent and

repeatable, which is right for financial work. But it does not stop the model

inventing facts — a model at zero temperature will state a made-up revenue

figure just as confidently. What actually prevents invention is \*\*grounding\*\*:

only giving it real extracted text, requiring a citation for every claim, and

telling it to say "not in the extracts" rather than fill the gap.



\---



\## What I'd say in an interview



\*\*"How do you know it works?"\*\*

I hand-checked answers against the source document rather than trusting the

output. That's how I found both the 5-page bug and the citation offset. I'm

building a fixed set of questions with verified answers so I can measure

accuracy properly instead of going on impressions.



\*\*"How do you stop it making things up?"\*\*

Three things. It only ever sees text pulled from the document. Every claim has

to carry a page citation, so it's checkable. And it's instructed to say when

the answer isn't in the extracts rather than fill the gap. The citation is the

important one — it makes wrong answers findable instead of just plausible.



\*\*"What went wrong?"\*\*

The app confidently analysed 3% of a document for three weeks and I didn't

notice, because the output looked exactly like real analysis. That taught me

more about AI risk than anything I've read: the dangerous failure isn't the one

that crashes, it's the one that looks like success.



\---



\## Next steps



\- \[ ] Fix citation page markers (in progress)

\- \[ ] Build 20-question test set with verified answers, measure accuracy

\- \[ ] Handle figures in tables that split across pages

\- \[ ] Streamlit web interface

\- \[ ] Deploy so it can be shared as a link



\## Decision — Keeping "from the report" and "outside knowledge" separate



\*\*The question.\*\* I wanted answers that go beyond the document — e.g. linking a

legal proceeding mentioned in the report to how the stock moved that week.

Useful, but it raised a design problem.



\*\*The problem.\*\* Those are two different kinds of claim. "The report discloses

an SEC proceeding" can be checked against a page. "The stock fell 4% that week"

is a claim about the world — it might be wrong, invented, or out of date. If I

merge them in one answer and cite the whole thing, the citation makes the

unverifiable half look verified. That's exactly the failure this whole project

is meant to prevent.



\*\*The decision.\*\* Keep two modes separate and always labelled:

1\. Grounded retrieval — answers only from the document, every claim cited to a

&#x20;  page. Testable and repeatable. This is the trustworthy core.

2\. Wider context — connects the report to outside information, clearly flagged

&#x20;  as external and possibly time-sensitive, never presented as document-sourced.



\*\*A hard limit I'm being honest about.\*\* The model's training has a cutoff and

no live prices. Asking it what a stock did on a given day invites a confident

made-up number. Doing the market/news feature properly needs a real price or

news feed, not the model's memory. So I'm parking it until I can build it on

live data — building it on the model's memory would plant a hallucination in the

one tool that's supposed to be hallucination-proof.



\*\*Why parking it is the right call.\*\* The outside-knowledge layer is my

differentiator, but it only works on top of a base people can trust. Measure and

solidify grounded retrieval first, then add the external layer on real data with

clear labelling.



\*\*Kept the eval strict.\*\* Ground-truth answers stay word-for-word from the

report on purpose — the eval tests faithful retrieval, so letting answers drift

into outside knowledge would destroy what it measures.

