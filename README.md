# INKFORGE — AI-Powered Story Co-Writer

> *Built by Subasri B · Infosys Springboard Virtual Internship 6.0 · Batch 13*

---

## What is InkForge?

InkForge is a full-stack AI fiction writing studio that runs entirely on your local machine. It uses a locally hosted large language model (llama3 via Ollama) to co-write stories with you in real time — with no cloud dependency, no subscription fee, and complete content privacy.

This is not a chatbot wrapper. Every feature in InkForge was purpose-built for serious fiction writers — from the context-locked story engine to the six-tool Author's Workshop to the A5 print-ready PDF export.

---

## Project Structure

```
inkforge/
├── src/
│   ├── app.py               # Main application entry point
│   ├── story_engine.py      # AI prompt engine, guardrails, genre/tone logic
│   ├── ui_components.py     # All UI rendering components
│   └── auth.py              # SHA-256 authentication & story history
├── docs/
│   ├── Phase 1_Streamlit and UI.docx
│   ├── Phase 2_Ollama Integration.docx
│   └── Phase 3_The Guardrails.docx
├── Screenshots/
│   ├── THE FORGE.png
│   ├── THE WORKSHOP.png
│   ├── THE STORY COMPASS.png
│   ├── THE STORY VAULT.png
│   ├── THE USER'S DIRECTION.png
│   └── SIDE BAR CONTROLS.png
├── inkforge_paged.pdf       # Sample PDF export output
└── requirements.txt
```

---

## Features

### The Forge — Live AI Writing Engine
- 10 writing action directives: Continue, Plot Twist, Dialogue, Describe, Rewrite, Enhance, Foreshadow, Raise the Stakes, Flashback, End Chapter
- Live token-by-token streaming output via Ollama's local HTTP API
- Genre, tone, POV, scene mood, characters, and world context injected into every prompt

### Story Configuration
- 8 genres: Fantasy, Sci-Fi, Thriller, Romance, Horror, Mystery, Historical, Literary
- 6 narrative tones: Cinematic, Lyrical, Dark & Gritty, Whimsical, Epic, Intimate
- 8 scene moods: Neutral, Tense, Melancholic, Hopeful, Foreboding, Magical, Intense, Serene
- Point of view: First Person, Third Person Limited, Third Omniscient, Second Person

### Author's Workshop — 6 Professional Writing Tools
| Tool | Purpose |
|---|---|
| Character Forge | Full psychological character profiles |
| World Architect | Structured world-building bible |
| Plot Architect | 5 story frameworks (Three Act, Hero's Journey, Save the Cat, Five Act, Kishōtenketsu) |
| Dialogue Coach | Subtext-rich dialogue rewriting |
| Prose Doctor | Structural and stylistic prose diagnosis |
| Story Analyst | Full editorial narrative feedback |

### Book Viewer & PDF Export
- Dual-page manuscript spread with automatic pagination
- Bold / Italic / Underline formatting toolbar
- Serif / sans-serif reading font toggle
- A5 print-ready PDF via ReportLab — cover page, drop caps, chapter headers, page numbers

### Story Compass
- 8 quick-craft shortcuts: Overcome Block, Pacing Guide, Subtext, Show Don't Tell, Tension Building, Voice Consistency, World-Building, Dialogue Naturalness
- Free-form AI writing coach Q&A

### Story Vault (History)
- Per-user SHA-256 authenticated accounts
- Auto-save after every passage
- Search, pin, archive, rename, delete
- Full metadata: genre, word count, timestamp

### Responsible AI Guardrail
- Intent classifier built into `story_engine.py`
- Intercepts off-topic queries (coding, general knowledge, etc.)
- Returns an in-character refusal — the AI never breaks its co-author persona
- Tested across 50+ off-topic prompt categories — zero false positives on legitimate writing inputs

---

## Tech Stack

| Layer | Technology |
|---|---|
| User Interface | Streamlit + Custom CSS/JS |
| Application Logic | Python 3.10+ |
| AI Engine | story_engine.py (custom prompt builder) |
| LLM Runtime | Ollama — llama3 8B (local) |
| PDF Export | ReportLab |
| Authentication | SHA-256 + session tokens |
| Data Storage | Per-user JSON files (local) |

---

## Getting Started

### Prerequisites
- Python 3.10 or higher
- [Ollama](https://ollama.com) installed and running
- llama3 model pulled

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Subasri23Hub/inkforge.git
cd inkforge

# 2. Install dependencies
pip install -r requirements.txt

# 3. Pull the llama3 model (first time only)
ollama pull llama3

# 4. Start Ollama
ollama serve

# 5. Run the application
cd src
python -m streamlit run app.py
```

### Recommended First Run
Before launching the app, warm up the model so the first generation is instant:
```bash
ollama run llama3
# Type anything, wait for a response, then Ctrl+C
```

---

## Development Phases

| Phase | Focus | Status |
|---|---|---|
| Phase 1 | Streamlit UI, design system, Book Viewer, PDF export, authentication | ✅ Complete |
| Phase 2 | Ollama integration, live streaming, 10-action prompt engine, Author's Workshop | ✅ Complete |
| Phase 3 | Responsible AI guardrails, intent classification, off-topic interception | ✅ Complete |

---

## Screenshots

| The Forge | The Workshop |
|---|---|
| ![The Forge](Screenshots/THE%20FORGE.png) | ![The Workshop](Screenshots/THE%20WORKSHOP.png) |

| Story Compass | Story Vault |
|---|---|
| ![Story Compass](Screenshots/THE%20STORY%20COMPASS.png) | ![Story Vault](Screenshots/THE%20STORY%20VAULT.png) |

---

## Author

**Subasri B** — Team Lead  
Infosys Springboard Virtual Internship 6.0 · Batch 13 · 2026

---

## Acknowledgements

- [Meta AI](https://ai.meta.com) — llama3 model
- [Ollama](https://ollama.com) — local LLM runtime
- [Streamlit](https://streamlit.io) — application framework
- [ReportLab](https://www.reportlab.com) — PDF generation
- Infosys Springboard — for the programme and opportunity
