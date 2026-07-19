# Data Extraction Module (Person 1)

This module extracts entities and relationships from `inputs/` text and PDF files
and emits a single master JSON graph contract at `data/graph_input.json` for
consumption by the GraphRAG pipeline.

Prerequisites
- Python 3.10+ recommended
- Local Ollama runtime running with `llama3.2` model pulled

Quick start (PowerShell)

```powershell
# (1) Create and activate venv (if you use a venv)
python -m venv venv
.\venv\Scripts\Activate.ps1

# (2) Install required packages
python -m pip install -r requirements.txt

# (3) Ensure Ollama daemon is running locally and model is available
# (see your Ollama docs; e.g., `ollama pull llama3.2` and `ollama serve`)

# (4) Place your .txt or .pdf files into the inputs/ folder
# (create directory if missing)
New-Item -ItemType Directory -Path inputs -Force

# (5) Run the extractor
python .\batch_extractor.py

# Output: data/graph_input.json
Get-Content data\graph_input.json | python -m json.tool
```

Notes
- The extractor prefers `PyMuPDF` (package `pymupdf`) for PDF parsing and will
fall back to `PyPDF2` if PyMuPDF is not available. Installing both is recommended.
- The script chunk-splits large documents to avoid local LLM context overflow.
- If you see memory/file-lock issues when processing many PDFs concurrently,
ensure the environment has enough memory and that files are closed (the
extractor uses context managers where possible).

Contact
- For integration with the graph backend (Person 2) or UI (Person 3), share
`data/graph_input.json`.
