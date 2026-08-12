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



\-----------------------------------------------------------------------------------



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



\------------------------------------------------------------------------------------



\## Building the eval set



\*\*What I did.\*\* Wrote \~14 questions with answers taken by reading the rendered

PDF myself, not extracted by code — so my ground truth doesn't share the same

extraction bugs as the app it's testing. Ground truth has to come from a

different source than the thing under test.



\*\*Categories, on purpose:\*\*

\- Simple lookups (revenue, cash, bitcoin holdings)

\- Table figures (segment revenue, TSR chart, equity) — where PDF extraction

&#x20; most often breaks

\- Text questions (dividends, production, capex guidance)

\- Unanswerable questions, which turned out to be three different tests:

&#x20; - Future date the report can't cover (R\&D % in 2027)

&#x20; - False premise stated as fact ("why is gross profit only $9bn") — tests

&#x20;   whether it challenges the question instead of inventing a justification

&#x20; - Absence of disclosure (a figure the company simply doesn't report)



\*\*Something I learned doing it.\*\* "Automotive revenue" exists at three scopes in

the report — sales only, sales plus regulatory credits, plus leasing. Same words,

different numbers. Retrieval could grab any of them. Precise questions need to

name the scope, and the app will eventually need to handle this ambiguity rather

than silently pick one.



\*\*Why this is the important part of the project.\*\* It turns "I think it works"

into "X out of N, and here's which categories it fails." Almost no student

project can state its own accuracy. This is the thing I'd lead with in an

interview when asked how I know it works.



\------------------------------------------------------------------------------------



\## First eval run — 5/10, and the failures point at one component



\*\*Result.\*\* Ran 10 questions through the pipeline. 5 clearly correct (revenue,

interest income, capex, and both refusals behaved sensibly). 5 failed — and all

5 failed identically: "the extracts do not contain this information."



\*\*The diagnosis.\*\* The failures were NOT the AI making things up. On the bitcoin

question I'd read the answer myself on page 73 — but the pages retrieval selected

didn't include 73. The model was handed extracts that genuinely didn't contain

the answer, and correctly said so. It behaved right on wrong input. Same for

equity (p52/55 not retrieved), dividends, and production numbers.



\*\*So the broken component is retrieval, not the model.\*\* I could only tell

because the app prints which pages it selected before the AI sees them. Without

that, "not in the extracts" looks like the AI failing. With it, I can point at

the exact failing step.



\*\*Why keyword retrieval fails here.\*\* My scorer ranks chunks by how many

question-words they contain. Questions that share wording with the document

("interest income") pass. Questions worded differently from the source fail —

"how many bitcoin units does Tesla hold" shares almost no words with a table

reading "Bitcoin / 11,509 / digital assets". Financial data lives in tables and

specific terms; natural questions rarely use those exact words. So the match

score is near zero and the right page never gets sent.



\*\*This is the failure I predicted when I chose keyword matching first.\*\* Now it's

measured, on a fixed question set, with a clear cause. That's the evidence I

needed to justify upgrading to embeddings (semantic search) — which match by

meaning rather than shared words, so "how many bitcoin" can find "digital assets

11,509" even with no words in common.



\*\*Interview version.\*\* I started with the simplest retrieval that could work,

built a test set, and measured it failing at 50% — specifically on questions

worded differently from the source. That told me exactly what embeddings buy me

and why, rather than reaching for them because they're fashionable.



\------------------------------------------------------------------------------------



\## Chunk size is a trade-off, and it has to be measured



\*\*The question.\*\* If 1-page chunks find the bitcoin table and 3-page chunks

don't, why not always use 1 page?



\*\*Why 3 was the original default.\*\* Not arbitrary, but not measured either — a

reasonable starting guess when building keyword retrieval. Semantic search later

exposed that it was too big for some questions.



\*\*Why smaller isn't simply better:\*\*

\- Severed context. Reports refer across pages ("the increase described above",

&#x20; or a table whose units sit in a header on the previous page). Big chunks keep

&#x20; related text together; 1-page chunks cut it apart, so you can retrieve a number

&#x20; with no idea what it means.

\- Less context reaches the model. Top-5 of 3-page chunks = 15 pages sent; top-5

&#x20; of 1-page chunks = 5 pages. To compensate you'd retrieve more chunks, using

&#x20; more tokens — reintroducing the volume problem embeddings were meant to reduce.

\- More chunks = more embedding calls and comparisons. Negligible now, real at

&#x20; scale.



\*\*The real lesson.\*\* Too big dilutes meaning and retrieves the wrong thing (the

bitcoin failure). Too small severs context and costs more. The right size is in

the middle and is found by measuring against the eval set, not by guessing. And a

fix proven on ONE question (bitcoin) can't be trusted until the FULL eval

confirms it didn't break the questions that needed the larger context.



\------------------------------------------------------------------------------------



\## The bitcoin question: why BOTH search methods missed one page



\*\*Symptom.\*\* "How many bitcoin units does Tesla hold" failed under keyword search

AND under embeddings, even at 1 page per chunk. The answer is plainly on page 73:

"Digital assets held: Bitcoin 11,509".



\*\*Diagnosis — three problems stacked on one question:\*\*



1\. Wording mismatch. The question says "hold" and "Tesla". The page says "held"

&#x20;  and "our" — it never says "Tesla" or "hold". Keyword overlap is near zero.



2\. Topic dilution. Page 73 is only about one-third bitcoin; the rest is

&#x20;  fair-value-hierarchy methodology (Level I/II/III, commercial paper, government

&#x20;  securities). Averaged into one embedding, the page's dominant "meaning" is

&#x20;  accounting methodology, not crypto holdings — so a bitcoin question doesn't

&#x20;  rank it highly even as a standalone page.



3\. Decoys. The risk-factor pages (133-136) use the words "bitcoin", "hold" and

&#x20;  "Tesla" many times in prose, so keyword search ranks THEM top — pages that

&#x20;  discuss bitcoin risk but contain no holdings figure.



\*\*Proof.\*\* Re-scoring with document-style wording ("digital assets held bitcoin

units cost fair value") pulls page 73 straight to the top. Same page, same

system, different phrasing — retrieval flips completely.



\*\*The lesson.\*\* "Use embeddings" is not a magic fix. Retrieval quality depends on

chunk size, on how the source is worded versus how users ask, and on decoy pages

that repeat query words without holding the answer. Keyword search fails on

vocabulary mismatch; embeddings fail on topic dilution. Knowing WHICH failure

you're looking at is the actual skill.



\*\*Also spotted (parked).\*\* Page 73 in the PDF prints "70" at its foot — a 3-page

offset from unnumbered covers. My citations currently use the PDF position, not

the printed number. Need to decide which to show users and label it. Logged for

later.



\------------------------------------------------------------------------------------



\## Embeddings result: 5/10 → 9/10



\*\*The change.\*\* Replaced keyword retrieval (rank chunks by shared words) with

semantic retrieval (rank by meaning, using embeddings + cosine similarity).

1 page per chunk. Same ten eval questions, same everything else.



\*\*Result: 9/10, up from 5/10.\*\*



\- 4 of the 5 keyword failures recovered: cash (Q2), equity (Q5), dividends (Q6),

&#x20; production (Q7). All had failed purely on vocabulary mismatch — the question

&#x20; worded differently from the document. Matching on meaning fixed them.

\- Nothing that passed before regressed.

\- Q10 (false premise) actively improved. Keyword version just refused. Semantic

&#x20; version caught the false "$9,000m gross profit", corrected it with the real

&#x20; figure — $17,094m, verified on p.53 — and cited it. Ideal behaviour.



\*\*The one remaining failure: Q3 bitcoin.\*\* Still not retrieved, exactly as

predicted. Page 73 never enters the top 5 because (1) the page is mostly

fair-value methodology, diluting its meaning away from "bitcoin holdings",

(2) the question says "hold"/"Tesla" while the page says "held"/"our", and

(3) decoy pages repeat the query words without holding the figure. Both search

methods miss it for different reasons. This needs hybrid retrieval or a wider

net, not more chunk-size tuning.



\*\*Why this matters as evidence.\*\* I didn't guess that embeddings would help — I

measured a baseline, made one targeted change, and measured again. 5 to 9, with

the single miss explained rather than mysterious. That's the difference between

"I used embeddings" and "I can show what they fixed, what they didn't, and why."



\*\*Minor issues logged, not yet fixed:\*\*

\- Q2 cited p.34 (summary) rather than p.52 (detail) — right number, loosely

&#x20; placed citation.

\- Citations still use PDF page position, which is offset \~3 from the printed

&#x20; page number. Need to pick one and label it.

