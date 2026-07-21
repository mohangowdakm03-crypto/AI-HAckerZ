import sys
import os
import json
import re
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# ── Path bootstrap ────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parent.parent
DATA_DIR   = ROOT / "data"
KG_DIR     = ROOT / "2_knowledge_graph"
VIS_DIR    = ROOT / "1_vision_extraction"

for p in (str(KG_DIR), str(VIS_DIR), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from graph_builder  import GraphRAGBuilder
from graph_search   import GraphSearchEngine
from batch_extractor import BatchExtractor

app = FastAPI(title="AI-HackerZ Graph API")

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def sanitize_filename(name: str) -> str:
    """Strip out path traversal characters and keep only safe alphanumeric/dashes"""
    return re.sub(r'[^a-zA-Z0-9_\-\.]', '', name)

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".json"}
MAX_FILE_SIZE_MB = 50

# Global sessions (in-memory state)
sessions = {}

class ChatRequest(BaseModel):
    query: str
    depth: int = 2
    top_k: int = 5
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    context: str

def get_session(session_id: str):
    if not session_id:
        session_id = "default"
    
    session_id = sanitize_filename(session_id)
        
    if session_id not in sessions:
        print(f"[*] Initializing new session graph: {session_id}")
        json_path = DATA_DIR / f"graph_{session_id}.json"
        ml_path = DATA_DIR / f"graph_{session_id}.graphml"
        
        # If it doesn't exist, create an empty one
        if not json_path.exists():
            with open(json_path, "w") as f:
                json.dump({
                    "document_id": session_id,
                    "entities": [],
                    "relationships": []
                }, f)
                
        b = GraphRAGBuilder(data_contract_path=str(json_path))
        if not b.load_data_contract():
            print(f"[-] Failed to load data contract for {session_id}.")
        if not b.build_graph():
            print(f"[-] Failed to build graph for {session_id}.")
        
        try:
            import networkx as nx
            nx.write_graphml(b.graph, str(ml_path))
        except Exception as e:
            print(f"[-] Failed to write graphml for {session_id}: {e}")
            
        e = GraphSearchEngine(graph_path=str(ml_path), data_contract_path=str(json_path), session_id=session_id)
        if not e.load_graph():
            print(f"[-] Search engine couldn't load graph for {session_id}.")
        e.load_data_contract()
        
        sessions[session_id] = {"builder": b, "engine": e, "json_path": json_path}
        
    return sessions[session_id]

@app.on_event("startup")
async def startup_event():
    DATA_DIR.mkdir(exist_ok=True)
    get_session("default")

@app.get("/api/stats")
async def get_stats(session_id: Optional[str] = Query(None)):
    session = get_session(session_id)
    b = session["builder"]
    stats = b.get_graph_stats()
    return {"status": "online", "stats": stats}

@app.get("/api/graph-data")
async def get_graph_data(session_id: Optional[str] = Query(None)):
    session = get_session(session_id)
    b = session["builder"]
    if b.graph is None:
        return {"nodes": [], "links": []}
    
    import networkx as nx
    data = nx.node_link_data(b.graph)
    
    centrality = nx.degree_centrality(b.graph)
    
    nodes = []
    for n in data.get("nodes", []):
        risk = round(centrality.get(n.get("id"), 0) * 100, 1)
        n["risk_score"] = risk
        
        if "type" not in n:
            n["type"] = b.graph.nodes[n.get("id")].get("entity_type", "Unknown")
            
        nodes.append(n)
        
    return {"nodes": nodes, "links": data.get("links", [])}

@app.get("/api/explorer")
async def get_explorer_data(session_id: Optional[str] = Query(None)):
    session = get_session(session_id)
    b = session["builder"]
    if b.graph is None:
        return {"nodes": []}
    import networkx as nx
    nodes = []
    for node, data in b.graph.nodes(data=True):
        in_deg = b.graph.in_degree(node) if b.graph.is_directed() else b.graph.degree(node)
        out_deg = b.graph.out_degree(node) if b.graph.is_directed() else b.graph.degree(node)
        nodes.append({
            "id": node,
            "type": data.get("entity_type", "Unknown"),
            "attributes": {k: v for k, v in data.items() if k != "entity_type"},
            "connections": in_deg + out_deg
        })
    return {"nodes": nodes}

@app.get("/api/risk")
async def get_risk_data(session_id: Optional[str] = Query(None)):
    session = get_session(session_id)
    b = session["builder"]
    if b.graph is None or len(b.graph.nodes) == 0:
        return {"hazards": []}
    
    import networkx as nx
    centrality = nx.degree_centrality(b.graph)
    risks = []
    for node, score in centrality.items():
        if score > 0:
            risks.append({
                "component": node,
                "risk_score": round(score * 100, 1),
                "type": b.graph.nodes[node].get("entity_type", "Unknown")
            })
    risks.sort(key=lambda x: x["risk_score"], reverse=True)
    return {"hazards": risks[:10]}

@app.get("/api/compliance")
async def get_compliance_report(session_id: Optional[str] = Query(None)):
    session = get_session(session_id)
    b = session["builder"]
    if b.graph is None:
        return {"status": "success", "violations": []}
    
    violations = []
    
    for node, data in b.graph.nodes(data=True):
        ntype = data.get("entity_type", "").upper()
        
        if ntype == "EQUIPMENT":
            has_sensor = False
            for neighbor in b.graph.neighbors(node):
                if b.graph.nodes[neighbor].get("entity_type", "").upper() == "SENSOR":
                    has_sensor = True
                    break
            if hasattr(b.graph, "predecessors"):
                for pred in b.graph.predecessors(node):
                    if b.graph.nodes[pred].get("entity_type", "").upper() == "SENSOR":
                        has_sensor = True
                        break
            
            if not has_sensor:
                violations.append({
                    "component": node,
                    "type": "Missing Sensor",
                    "severity": "High",
                    "citation": "OSHA 1910.119 (Process Safety)",
                    "description": f"Equipment {node} is operating without any active sensor monitoring."
                })
                
        if ntype == "HAZARD":
            has_procedure = False
            for neighbor in b.graph.neighbors(node):
                if b.graph.nodes[neighbor].get("entity_type", "").upper() == "PROCEDURE":
                    has_procedure = True
                    break
            if hasattr(b.graph, "predecessors"):
                for pred in b.graph.predecessors(node):
                    if b.graph.nodes[pred].get("entity_type", "").upper() == "PROCEDURE":
                        has_procedure = True
                        break
                        
            if not has_procedure:
                violations.append({
                    "component": node,
                    "type": "Unmitigated Hazard",
                    "severity": "Critical",
                    "citation": "EPA 40 CFR Part 68 (RMP)",
                    "description": f"Hazard {node} has no associated safety procedure or mitigation protocol."
                })
                
    return {"status": "success", "violations": violations}

@app.get("/api/export-report")
async def export_report(session_id: Optional[str] = Query(None)):
    session = get_session(session_id)
    b = session["builder"]
    if b.graph is None:
        raise HTTPException(status_code=503, detail="Graph engine offline.")
    
    import networkx as nx
    from fpdf import FPDF
    
    stats = b.get_graph_stats()
    centrality = nx.degree_centrality(b.graph)
    risks = []
    for node, score in centrality.items():
        if score > 0:
            risks.append({
                "component": node,
                "risk_score": round(score * 100, 1),
                "type": b.graph.nodes[node].get("entity_type", "Unknown")
            })
    risks.sort(key=lambda x: x["risk_score"], reverse=True)
    top_hazards = risks[:5]
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=18)
    pdf.cell(0, 15, text=f"GraphRAG Intelligence - System Report", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", style="B", size=14)
    pdf.cell(0, 10, text="System Health & Stats", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=12)
    for k, v in stats.items():
        pdf.cell(0, 8, text=f"- {str(k).replace('_', ' ').title()}: {v}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", style="B", size=14)
    pdf.cell(0, 10, text="Top Critical Risk Hazards", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=12)
    for idx, hazard in enumerate(top_hazards, 1):
        pdf.cell(0, 8, text=f"{idx}. {hazard['component']} ({hazard['type']}) - Risk Score: {hazard['risk_score']}%", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", style="B", size=14)
    pdf.cell(0, 10, text="All Components", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=10)
    for node, data in b.graph.nodes(data=True):
        ntype = data.get("entity_type", "Unknown")
        pdf.cell(0, 6, text=f"- {node} [{ntype}]", new_x="LMARGIN", new_y="NEXT")
    
    pdf_bytes = pdf.output()
    return Response(content=bytes(pdf_bytes), media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=system_report_{session_id or 'default'}.pdf"
    })

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    session = get_session(request.session_id)
    e = session["engine"]
    if not e:
        raise HTTPException(status_code=503, detail="Graph engine is not initialized.")
    try:
        ctx, answer = e.query(request.query, top_k=request.top_k, context_depth=request.depth)
        return ChatResponse(answer=answer, context=ctx)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

@app.get("/api/suggested-queries")
def get_suggested_queries(session_id: Optional[str] = Query(None)):
    session = get_session(session_id)
    b = session["builder"]
    if not b.graph or len(b.graph.nodes) == 0:
        return {"queries": []}

    import networkx as nx
    import ollama
    
    # Get top 5 connected nodes to give the LLM some context
    centrality = nx.degree_centrality(b.graph)
    top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
    context_str = ", ".join([f"{n} ({b.graph.nodes[n].get('entity_type', 'Unknown')})" for n, _ in top_nodes])
    
    prompt = f"""You are an industrial AI assistant. Based on the following highly-connected nodes in the current graph dataset:
    {context_str}
    
    Generate exactly 4 insightful questions a user could ask to investigate this system. 
    Format your response STRICTLY as a JSON array of strings. Do not include any other text.
    Example: ["What is connected to X?", "How does Y affect Z?", "Are there hazards related to W?", "Explain the role of V."]"""
    
    try:
        response = ollama.chat(
            model='llama3.1',
            messages=[{'role': 'user', 'content': prompt}],
            format='json',
            options={'temperature': 0.7}
        )
        queries = json.loads(response['message']['content'])
        if isinstance(queries, dict):
             # sometimes it returns {"queries": [...]}
             queries = queries.get("queries", list(queries.values())[0])
        return {"queries": queries[:4]}
    except Exception as e:
        print(f"Error generating queries: {e}")
        return {"queries": []}

@app.post("/api/upload")
def upload_document(file: UploadFile = File(...), session_id: Optional[str] = Query(None)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
        
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    safe_filename = sanitize_filename(file.filename)
    if not safe_filename:
        safe_filename = "unnamed_upload.txt"

    session = get_session(session_id)
    json_path = session["json_path"]
        
    raw_dir = DATA_DIR / "raw_documents"
    raw_dir.mkdir(exist_ok=True)
    tmp_path = raw_dir / safe_filename
    
    # Stream file to disk to prevent DoS, enforcing max size
    bytes_written = 0
    with open(tmp_path, "wb") as f:
        while chunk := file.file.read(1024 * 1024): # 1MB chunks
            bytes_written += len(chunk)
            if bytes_written > MAX_FILE_SIZE_MB * 1024 * 1024:
                tmp_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail=f"File exceeds maximum size of {MAX_FILE_SIZE_MB}MB")
            f.write(chunk)
        
    extractor = BatchExtractor(inputs_dir=str(raw_dir), output_dir=str(DATA_DIR))
    # Pass the unique session json path
    success = extractor.process_single_file_and_merge(str(tmp_path), str(json_path))
    
    if success:
        # Re-initialize just this session's graph
        if session_id in sessions:
            del sessions[session_id]
        get_session(session_id)
        return {"status": "success", "message": f"{safe_filename} processed and graph updated."}
    else:
        raise HTTPException(status_code=500, detail="Failed to extract and merge document.")
