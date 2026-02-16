# 📋 AI Policy Analyzer — NAU Edition

> Upload any AI policy document. Instantly know if your AI usage complies — and whether the policy itself is any good.

![NAU Edition](https://img.shields.io/badge/NAU-Edition-003f87?style=flat&labelColor=ffb511&color=003f87)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-black?style=flat&logo=flask)
![Gemini](https://img.shields.io/badge/Google-Gemini_API-4285F4?style=flat&logo=google)

---

## What It Does

Most AI policy tools just tell you *"yes/no"* on compliance. This one goes further:

1. **Reads your policy** (PDF, DOCX, TXT, or image)
2. **Analyzes your action** against the policy
3. **Gives a verdict** — ALLOWED / GRAY AREA / VIOLATION
4. **Scores the risk** (0–100) with explanation
5. **Shows 3 professor perspectives** — strict, moderate, lenient
6. **Critiques the policy itself** — because bad policies deserve to be called out
7. **Downloads a PDF report** with NAU branding

---

## Demo

| Input | Output |
|-------|--------|
| NAU Academic Integrity Policy + "I used ChatGPT to summarize a lecture" | ⚠️ GRAY AREA · Risk 45/100 · Policy Score 35/100 |
| NAU Policy + "I used AI to write my entire essay" | ❌ VIOLATION · Risk 95/100 · Policy Score 45/100 |
| NIST IR 8596 + "I used Gemini to clean up my work report" | ⚠️ GRAY AREA · Risk 72/100 · Policy Score 60/100 |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask |
| AI Engine | Google Gemini API (`gemini-3-flash-preview`) |
| PDF Parsing | PyMuPDF (fitz) |
| DOCX Parsing | python-docx |
| Frontend | Vanilla HTML/CSS/JS |
| PDF Export | jsPDF (client-side) |
| Deployment | GitHub Codespaces |

---

## Project Structure

```
ai-policy-analyzer/
├── app.py                  # Flask server + parsing logic
├── policy_analyzer.py      # Gemini API integration + prompt engineering
├── template.html           # Frontend UI (NAU theme)
├── uploads/                # Uploaded policy files (gitignored)
├── examples/
│   ├── nau_policy.pdf      # NAU Academic Integrity Policy
│   └── sample_policy.txt   # Simple test policy
└── README.md
```

---

## Getting Started

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/ai-policy-analyzer.git
cd ai-policy-analyzer
pip install -r requirements.txt
```

### 2. Set API Key

```bash
export GEMINI_API_KEY=your_api_key_here
```

Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey).

### 3. Run

```bash
python app.py
```

Open `http://localhost:5000`

---

## How It Works

### Parsing Pipeline

```
User uploads policy file
        ↓
PyMuPDF / python-docx / plain text extraction
        ↓
Gemini prompt: analyze compliance + critique policy
        ↓
Structured text output (sections delimited by ━━━)
        ↓
Python parser extracts: verdict / risk / recommendations / critique
        ↓
JSON → Flask → JavaScript renders cards
```

### Prompt Engineering

The analyzer uses a structured prompt that forces Gemini to output:

- **Binary verdict** with reasoning (ALLOWED / GRAY AREA / VIOLATION)
- **Risk score** 0–100 with specific policy clause references
- **3 professor interpretations** (strict → lenient spectrum)
- **Tiered recommendations** (safest / moderate risk / avoid)
- **Policy critique** in 4 bullet points with effectiveness score

Key insight: the prompt distinguishes between *"AI for learning"* (studying, note-taking, comprehension) vs *"AI for submission"* (generating graded work) — a distinction most policies fail to make.

---

## Key Features

### Policy Critique (What Makes This Different)

Most compliance tools just say *"violation"* and move on. This tool asks:
> **Is the policy itself actually good?**

For each analysis, Gemini evaluates:
- Does this policy punish learning behaviors?
- Does it create a "chilling effect" on students?
- What would a better policy say?
- Effectiveness score: 0–100

Example output on NAU's policy:
> *"KEY FLAW: Creates a 'guilty until proven innocent' environment by banning all AI use unless a teacher specifically opts-in."*
> **Policy Score: 35/100**

### Supported File Types

| Format | Parser |
|--------|--------|
| `.pdf` | PyMuPDF |
| `.docx` | python-docx |
| `.txt` | Built-in |
| `.png` `.jpg` `.jpeg` | Gemini Vision (multimodal) |

### PDF Report Export

Client-side PDF generation via jsPDF with:
- NAU blue header + gold accent bar
- Structured sections with visual hierarchy
- Page numbers + NAU footer
- Emoji-safe (all special characters stripped before PDF render)

---

## Error Handling

| Error | Response |
|-------|----------|
| Gemini 503 (overload) | "Please wait 10–30 seconds and try again" |
| Gemini 429 (rate limit) | "API rate limit reached" |
| No file uploaded | 400 with message |
| Invalid API key | Descriptive error message |

---

## Requirements

```
flask
google-generativeai
PyMuPDF
python-docx
```

---

## Notes

- **File size limit:** 16MB
- **Gemini model:** `gemini-3-flash-preview` (fast, cost-effective)
- **Not a lawyer:** This tool provides educational analysis only. Always consult your professor or academic advisor for official guidance.

---

## Author

Built by **[@LareineHan](https://github.com/LareineHan)** as a portfolio project demonstrating:
- Full-stack development (Python backend + modern frontend)
- Prompt engineering for structured AI output
- Real-world application (students checking AI policy compliance)
- Critical thinking: the tool doesn't just check compliance — it critiques bad policies

---

*"A student should not feel like a criminal for using a tool to help them learn."*