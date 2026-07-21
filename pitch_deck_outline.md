# Pitch Deck Outline: PS 8 - AI for Industrial Knowledge Intelligence

## Slide 1: Title & The Hook
* **Project Name:** GraphRAG Brain
* **Team Name:** AI-HackerZ
* **The Hook:** Transforming siloed, fragmented machine manuals and telemetry logs into real-time, proactive operational intelligence.

## Slide 2: The Core Problem
* **The Cost of Fragmentation:** In modern industrial settings, critical data is scattered across isolated telemetry logs, compliance reports, and inaccessible OEM manuals.
* **Prolonged Downtime:** When a fault occurs, operators lose hours cross-referencing a 1,000-page PDF against a cryptic error code. 
* **The Brain Drain:** Retiring veteran operators are taking decades of undocumented "tribal knowledge" with them, leaving junior technicians vulnerable to making critical mistakes.

## Slide 3: The Solution: A Unified Brain
* **What it is:** A fully offline, air-gapped Industrial Intelligence platform that maps physical infrastructure into an interactive Knowledge Graph and queries it via conversational AI.
* **Who it is for:** Designed specifically for **Plant Managers** trying to prevent systemic failures, and **Floor Maintenance Technicians** who need instant, accurate diagnostic steps while standing in front of a broken machine.

## Slide 4: Key Capabilities & UX
* **Causal Reasoning Chat:** Queries are answered by tracing physical network connections, not just keyword matching.
* **Automated Hazard Detection:** Instantly flags unmitigated risks where a machine lacks required safety sensors.
* **Physics-Based Visualizer:** Operators can visually explore the entire plant architecture via a D3.js force-directed graph.
* **UX/UI Agility:** To ensure operators aren't overwhelmed by clunky enterprise software, we heavily prioritized UX. We utilized a rapid development workflow—exporting custom, photorealistic "Apple Liquid Glass" designs directly from Figma into deployable Next.js front-end code—allowing us to quickly iterate and ship an incredibly clean, stress-reducing interface.

## Slide 5: Technical Architecture (The Pipeline)
* **LLM Engine:** Local `Llama 3.1 (8B)` running via `Ollama`. Zero cloud dependency.
* **Vector Database:** `ChromaDB` for high-speed semantic search and document embeddings.
* **Graph Engine:** `NetworkX` for in-memory topological math, centrality calculations, and physical edge traversal.
* **The Pipeline:** We employ a custom **GraphRAG** pipeline. When a user queries a machine, we find the semantic match in ChromaDB, traverse its neighboring connections in NetworkX, and inject that rich, interconnected subgraph into Llama 3.1's prompt to generate a grounded response.
* **The Stack:** `Next.js` (Frontend) communicating asynchronously with a `FastAPI` (Python) backend.

## Slide 6: Data Ingestion & Processing
* **Multi-Modal Parsing:** The backend utilizes `PyMuPDF` to robustly extract unstructured text from massive OEM PDF manuals, alongside TXT logs and raw JSON telemetry files.
* **Intelligent Chunking:** Text is programmatically sliced into overlapping 800-word chunks. 
* **Automated Extraction:** The chunks are fed to the LLM via a strict zero-shot prompt. The AI automatically identifies Entities (Pumps, Sensors, Hazards) and maps their Relationships (Causes, Monitors, Connected To) to build the structured graph autonomously.

## Slide 7: Safety & Hallucination Mitigation
* **The Threat:** In industrial environments, an AI hallucination can lead to catastrophic machine failure or physical injury.
* **Strict Schema Guardrails:** The ingestion pipeline forces the LLM to output a rigid JSON contract. If it invents a relationship type that isn't physically possible in our schema, it is rejected.
* **Zero-Shot Restraints:** The chat engine is architecturally constrained by the prompt: *"Answer ONLY using the provided subgraph relationships. Under no circumstances should you guess. If the graph does not state a connection, you must explicitly state that you do not know."*

## Slide 8: The Business Impact (ROI)
* **Drastic MTTR Reduction:** (Mean Time to Repair). By instantly synthesizing a warning log with the correct mitigation procedure, we cut diagnostic time from hours to seconds.
* **Faster Technician Onboarding:** Junior technicians gain immediate access to an interactive "expert," accelerating their training and reducing costly rookie mistakes.
* **Increased OEE:** (Overall Equipment Effectiveness). By detecting cascading bottlenecks before they cause a shutdown, plant productivity rises significantly.

## Slide 9: Competitive Differentiation
* **Domain Specificity:** Standard enterprise search tools fail because they cannot understand that a "Valve" is physically connected to a "Turbine." We map the actual physics of the plant.
* **Total Data Privacy:** ChatGPT Enterprise requires sending highly classified, ITAR-restricted infrastructure data to the cloud. GraphRAG Brain runs 100% locally on internal company networks.
* **Workflow Integration:** It doesn't just answer questions; it calculates risk scores and compliance violations automatically.

## Slide 10: Execution Risks & Technical Limitations
* **Latency Constraints:** Generating subgraphs and running local Llama 3.1 inference synchronously can cause API delays on massive documents.
* **Entity Deduplication:** The prototype currently uses simplistic string-matching. If one log calls it "Pump-1" and another calls it "Main Pump 01", the graph may fragment.
* **Complex Diagrams:** The current pipeline reads unstructured text perfectly but struggles to interpret complex CAD drawings or P&ID schematics embedded inside the PDFs.

## Slide 11: Future Roadmap (Next 6 Months)
* **Semantic Clustering:** Integrating an embedding model (like `all-MiniLM-L6-v2`) to mathematically calculate similarity and automatically merge duplicate entities.
* **Live IoT Integration:** Connecting the GraphRAG backend to live SCADA systems via WebSockets to ingest real-time sensor temperatures rather than relying entirely on static logs.
* **Edge Deployment:** Containerizing the stack to run smoothly on localized rugged edge devices deployed directly on the factory floor.

## Slide 12: Conclusion & Team
* **The Future of Operations:** GraphRAG Brain is not just a search bar; it is a unified, proactive defense system for critical infrastructure.
* **Team:** AI-HackerZ
* **Contact & Demo:** Link to GitHub repository and live application demo.
