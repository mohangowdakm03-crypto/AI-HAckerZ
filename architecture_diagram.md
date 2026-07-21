# GraphRAG Brain: Architecture Diagram

This diagram outlines the complete end-to-end data flow and system architecture for GraphRAG Brain, from raw data ingestion to the final user interface.

```mermaid
graph TD
    %% Define Styles
    classDef frontend fill:#000000,stroke:#333,stroke-width:2px,color:#fff
    classDef backend fill:#1a365d,stroke:#2b6cb0,stroke-width:2px,color:#fff
    classDef ai fill:#276749,stroke:#48bb78,stroke-width:2px,color:#fff
    classDef db fill:#744210,stroke:#d69e2e,stroke-width:2px,color:#fff
    classDef data fill:#4a5568,stroke:#a0aec0,stroke-width:2px,color:#fff

    %% Data Sources Layer
    subgraph Data Sources ["Unstructured Industrial Data"]
        PDF[PDF Manuals & Audits]:::data
        TXT[Maintenance Logs]:::data
        JSON[Telemetry JSONs]:::data
    end

    %% Backend Ingestion Layer
    subgraph Backend Pipeline ["FastAPI Backend (Python)"]
        UploadAPI[POST /api/upload]:::backend
        BatchExtractor[Batch Extractor Pipeline]:::backend
        Parser[PyMuPDF & Text Chunking]:::backend
        
        UploadAPI --> BatchExtractor
        BatchExtractor --> Parser
    end

    %% AI Extraction Layer
    subgraph AI Engine ["Local AI (Air-Gapped)"]
        Ollama[Ollama Engine]:::ai
        Llama[Llama 3.1 LLM]:::ai
        Prompt[Strict JSON Guardrails]:::ai
        
        Ollama --> Llama
        Llama --> Prompt
    end

    %% Database Layer
    subgraph Databases ["Dual-Storage Engine"]
        NetworkX[(NetworkX<br>In-Memory Graph)]:::db
        ChromaDB[(ChromaDB<br>Vector Database)]:::db
    end

    %% Frontend Layer
    subgraph Frontend ["Next.js Frontend (React)"]
        UI[Apple Liquid Glass UI]:::frontend
        D3Graph[D3.js Force-Directed Visualizer]:::frontend
        Chat[Conversational Interface]:::frontend
    end

    %% Connections
    PDF --> UploadAPI
    TXT --> UploadAPI
    JSON --> UploadAPI

    Parser -->|Raw Text Chunks| Ollama
    Prompt -->|Structured Entities & Relationships| NetworkX
    Prompt -->|Semantic Embeddings| ChromaDB

    %% Query Flow
    Chat -->|User Query| QueryAPI[POST /api/chat]:::backend
    QueryAPI -->|Semantic Search| ChromaDB
    ChromaDB -->|Nearest Node Match| NetworkX
    NetworkX -->|Traverse Edges Depth=2| Subgraph[Connected Subgraph Context]:::backend
    
    Subgraph -->|Context + Query| Ollama
    Llama -->|Grounded Answer| Chat

    NetworkX -->|Graph Topology Data| D3Graph
```

### Flow Breakdown:
1. **Ingestion:** Raw files (PDFs, TXTs, JSONs) are uploaded via the Next.js frontend to the FastAPI backend.
2. **Extraction:** The `Batch Extractor` slices the text and passes it to the **Local AI Engine** (Llama 3.1 via Ollama).
3. **Structuring:** The LLM is forced by strict prompts to output a JSON contract of Entities and Relationships, which are then saved to **NetworkX** (for graph topology) and **ChromaDB** (for semantic vector search).
4. **Retrieval (RAG):** When a user asks a question, the backend queries ChromaDB for the closest node, then uses NetworkX to pull all connected neighboring nodes.
5. **Generation:** That specific sub-graph is passed back to Llama 3.1 to generate a highly accurate, hallucination-free answer, which is streamed back to the **Apple Liquid Glass UI**.
