# AI-HackerZ: GraphRAG Brain

An elite, fully-offline, and air-gapped industrial GraphRAG dashboard. It leverages a Python FastAPI backend with a local Llama 3.1 LLM and ChromaDB vector store, paired with a modern Next.js Apple Liquid Glass interface.

## Prerequisites

Before running the application, ensure you have the following installed on your machine:

1.  **Node.js (v18+)** - For the frontend
2.  **Python (3.10+)** - For the backend
3.  **Ollama** - For local LLM inference

### Setup Ollama

You must have Ollama installed and the required models downloaded:

```bash
# Start the Ollama server in the background (if not already running)
ollama serve

# Download the required LLM model (Llama 3.1)
ollama run llama3.1

# Download the required embedding model
ollama pull nomic-embed-text
```

---

## 1. Starting the Backend (FastAPI)

The backend handles the graph generation, vector database (ChromaDB), and LLM queries.

1.  Open a terminal and navigate to the root directory.
2.  Create a virtual environment (optional but recommended):
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
    ```
3.  Install the required Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Navigate to the `backend/` directory and start the server:
    ```bash
    cd backend
    uvicorn main:app --port 8000 --reload
    ```
5.  The backend API is now running at `http://localhost:8000`.

---

## 2. Starting the Frontend (Next.js)

The frontend provides the interactive UI, built with Next.js and Tailwind CSS (or inline styles).

1.  Open a **new terminal** and navigate to the `frontend/` directory.
2.  Install the Node.js dependencies:
    ```bash
    npm install
    ```
3.  Start the Next.js development server:
    ```bash
    npm run dev
    ```
4.  Open your browser and navigate to `http://localhost:3000`.

---

## Usage Guide

1.  Click the **Upload** button (cloud icon) in the bottom left of the chat window.
2.  Select an industrial log or dataset (e.g., `industrial_plant_data.txt`).
3.  Wait for the ingestion process to complete. The system will build a Knowledge Graph and embed the entities into a local ChromaDB collection.
4.  Navigate to the **Graph** tab on the left sidebar to visualize the extracted network.
5.  Return to the **AI Chat** tab and ask complex, multi-hop questions about the data!
