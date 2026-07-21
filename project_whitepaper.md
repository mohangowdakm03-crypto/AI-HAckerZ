# PS 8 Submission: AI for Industrial Knowledge Intelligence (Unified Asset & Operations Brain)
**Project Name:** GraphRAG Brain  

---

## 1. Executive Summary & Value Proposition

**The Problem:** 
Modern industrial operations—such as power plants and manufacturing grids—generate massive amounts of fragmented data. Sensor telemetry logs, PDF maintenance manuals, and shift handover notes exist in isolated silos. When an equipment failure occurs, operators lose critical time trying to manually connect a warning from a sensor log to a mitigation procedure buried in a 500-page PDF. This lack of unified "tribal knowledge" leads to undetected cascading failures, compliance violations, and incredibly expensive unplanned downtime.

**The Solution:** 
**GraphRAG Brain** is a fully offline, air-gapped Industrial Intelligence platform. It autonomously reads multi-modal data (PDFs, TXTs, JSON telemetry) and uses a local Large Language Model to extract a structured **Knowledge Graph**. Instead of relying on keyword-based AI search, our system builds a physical and logical map of the facility, allowing the AI to traverse causal relationships (e.g., "Pump A is connected to Valve B, which causes Hazard C").

**The Impact:** 
- **Reduced Downtime:** By immediately highlighting the downstream effects of a failing component, operators can isolate issues before they trigger systemic shutdowns.
- **Automated Compliance:** Automatically flags "Hazard" nodes that lack connecting "Sensor" or "Procedure" nodes, instantly revealing unmitigated safety risks.
- **Zero Cloud Costs & Total Privacy:** Operating 100% locally on corporate hardware eliminates cloud API costs and prevents highly sensitive infrastructure data from leaking to third-party AI providers.

---

## 2. Solution Architecture & Technical Stack

**System Diagram:** 
*(Suggested Image: A clean architectural flowchart showing Unstructured Data converging into the Python Batch Extractor, splitting into ChromaDB and NetworkX, and being queried by the FastAPI backend to display on the Next.js Apple-glass frontend.)*
- **Data Ingestion:** `PyMuPDF` parses documents; text is chunked with overlap.
- **AI Extraction Pipeline:** `Ollama` running `Llama 3.1 (8B)` enforces a strict JSON schema contract to extract Entities and Relationships.
- **Dual-Storage Engine:** 
  - `NetworkX` (In-memory Graph) handles topological math (centrality, degree distribution).
  - `ChromaDB` (Vector Database) handles semantic embedding of the nodes.
- **Application Layer:** `FastAPI` (Backend) communicates with `Next.js` (Frontend).

**The AI Pipeline:** 
Standard RAG systems struggle with industrial data because they retrieve isolated text chunks based on keyword similarity, completely missing the physical connections between machines. We solved this by implementing **GraphRAG**. 
1. **Embedding:** We embed extracted nodes into ChromaDB.
2. **Retrieval:** When a user asks a question, we query ChromaDB for the closest semantic node.
3. **Graph Traversal:** Crucially, we don't just pass that node to the LLM. We use NetworkX to traverse 2-degrees of separation outwards from that node, pulling in all connected components, hazards, and sensors. 
4. **Generation:** This rich, interconnected subgraph is injected into Llama 3.1's prompt window, forcing it to generate a response based on the actual physical architecture of the plant.

**Handling Hallucinations:** 
In critical infrastructure, AI hallucinations are dangerous. We implemented strict guardrails:
1. **Schema Enforcement:** The LLM extraction is forced into a deterministic JSON contract. If it invents a relationship type outside our allowed set (`CONNECTED_TO`, `MONITORS`, `CAUSES`, `GOVERNED_BY`), the backend rejects it.
2. **Contextual Grounding:** The chat engine operates on a strict *Zero-Shot Context* prompt. The system prompt explicitly states: *"Answer ONLY using the provided subgraph relationships. If the graph does not state a connection, say you do not know."*

---

## 3. User Interface & Operator Experience

**UX/UI Showcase:**
*(Suggested Images: 1. The main dashboard showing the physics-based graph visualizer. 2. The dark-mode Chat panel with Liquid Glass elements. 3. The risk-alert sidebar showing flagged unmitigated hazards.)*

**Design Workflow:** 
Industrial tools often suffer from bloated, difficult-to-use interfaces. Our goal was to reduce operator cognitive load during high-stress emergencies. We implemented a photorealistic **Apple Liquid Glass** design language. Using advanced CSS (volumetric box-shadows, SVG fractal noise for frosted textures, and edge refraction), we created a highly premium, intuitive interface. Furthermore, the integration of a **D3.js Force-Directed Graph** allows operators to visually manipulate the plant's architecture, dynamically repelling nodes to prevent visual clutter, making the "Unified Brain" instantly readable on the factory floor.

---

## 4. Market Differentiation & Feasibility

**Competitive Edge:** 
- **Standard Enterprise Search:** Fails because it cannot understand causal relationships (e.g., it doesn't know that a cooling tower failure impacts the turbine).
- **Generic Cloud AI (ChatGPT/Claude):** Fails because industrial data is classified/ITAR restricted and cannot be sent to the public cloud.
- **GraphRAG Brain:** Succeeds by combining localized privacy, graph-based causal reasoning, and automated compliance auditing into a single offline box.

**Resource Requirements:** 
To scale this from prototype to enterprise deployment:
- **Compute:** Requires local edge servers equipped with NVIDIA RTX 4090s or A100s to run Llama 3.1 inference at acceptable latencies.
- **Integration:** Requires custom API connectors to ingest live SCADA data rather than static JSON/PDF logs, which is a standard IT integration challenge.

---

## 5. Known Limitations & Future Roadmap

**Current Gaps:**
1. **Entity Resolution (Deduplication):** Currently, if one manual calls it "Pump-1" and another calls it "Main Pump 01", the LLM might extract them as two separate nodes. Our deduplication logic is currently based on simple string matching rather than advanced semantic clustering.
2. **Synchronous Bottlenecks:** The current backend API processes extraction and LLM inference synchronously. Generating the graph from a massive PDF can block the server for minutes, causing UI timeouts.

**Next Steps (6-Month Roadmap):**
1. **Implement WebSockets/SSE:** Transition the FastAPI backend to Server-Sent Events to stream LLM tokens in real-time, drastically improving perceived performance.
2. **Graph-Native Database:** Migrate from in-memory NetworkX to a scalable, persistent graph database like Neo4j.
3. **Cross-Encoder Reranking:** Add a reranker (e.g., BGE-Reranker) before the LLM generation step to ensure only the most highly relevant sub-graphs are injected into the prompt, further reducing hallucination risk.
