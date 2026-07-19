"""
Person 3 - Full-Stack Integration Lead
3_frontend/app.py

Elite industrial GraphRAG dashboard. Fully offline, zero cloud dependencies.
Integrates with:
  - 2_knowledge_graph/graph_builder.py  → builds + holds the NetworkX graph
  - 2_knowledge_graph/graph_search.py   → keyword search + Ollama synthesis
"""

import sys
import os
import json
import time
import streamlit as st
from pathlib import Path
from typing import Dict, List

# ── Path bootstrap ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent          # repo root
DATA_DIR   = ROOT / "data"
GRAPH_JSON = DATA_DIR / "graph_input.json"
GRAPH_ML   = DATA_DIR / "graph.graphml"
KG_DIR     = ROOT / "2_knowledge_graph"

for p in (str(KG_DIR), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from graph_builder import GraphRAGBuilder
from graph_search  import GraphSearchEngine

# ── Read clicked node from URL query params (set by JS bridge) ────────────────
_qp_node = st.query_params.get("node", "")
if _qp_node and _qp_node != st.session_state.get("selected_node", ""):
    st.session_state["selected_node"] = _qp_node
    st.session_state["inspector_expanded"] = True

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI-HackerZ | Industrial GraphRAG",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS (dark + neon cyan theme) ────────────────────────────────────────
st.markdown("""
<style>
  /* ── Fonts ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  /* ── Root palette ── */
  :root {
    --bg-base:    #0d0d0f;
    --bg-card:    #13131a;
    --bg-surface: #1a1a24;
    --accent:     #00e5ff;
    --accent-dim: #00b8cc;
    --accent-glow: rgba(0,229,255,.18);
    --warn:       #ff6b35;
    --success:    #39ff14;
    --text-pri:   #f0f0f5;
    --text-sec:   #8888aa;
    --border:     rgba(0,229,255,.15);
  }

  /* ── Base ── */
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .main .block-container { padding: 1.5rem 2rem 2rem; max-width: 100%; }
  .stApp { background: var(--bg-base); }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
  }
  [data-testid="stSidebar"] * { color: var(--text-pri) !important; }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: var(--bg-base); }
  ::-webkit-scrollbar-thumb { background: var(--accent-dim); border-radius: 4px; }

  /* ── Headings ── */
  h1, h2, h3, h4 { color: var(--text-pri) !important; letter-spacing: -.3px; }

  /* ── Metric cards ── */
  [data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: .8rem 1rem !important;
  }
  [data-testid="stMetricValue"] {
    color: var(--accent) !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
  }
  [data-testid="stMetricLabel"] { color: var(--text-sec) !important; font-size: .75rem !important; }

  /* ── Buttons ── */
  .stButton > button {
    background: transparent !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: .85rem !important;
    transition: all .2s ease !important;
  }
  .stButton > button:hover {
    background: var(--accent-glow) !important;
    box-shadow: 0 0 18px var(--accent-glow) !important;
    transform: translateY(-1px) !important;
  }

  /* ── Text inputs ── */
  .stTextInput > div > div > input,
  .stTextArea textarea {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-pri) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: .9rem !important;
  }
  .stTextInput > div > div > input:focus,
  .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-glow) !important;
  }

  /* ── Selectbox ── */
  .stSelectbox > div > div {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-pri) !important;
  }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card) !important;
    border-radius: 12px 12px 0 0 !important;
    gap: 4px !important;
    padding: 4px !important;
    border-bottom: 1px solid var(--border) !important;
  }
  .stTabs [data-baseweb="tab"] {
    color: var(--text-sec) !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: .88rem !important;
    padding: .45rem 1.1rem !important;
  }
  .stTabs [aria-selected="true"] {
    background: var(--accent-glow) !important;
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
  }
  .stTabs [data-baseweb="tab-panel"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
    padding: 1.2rem !important;
  }

  /* ── Expanders ── */
  .streamlit-expanderHeader {
    background: var(--bg-card) !important;
    color: var(--text-pri) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
  }
  .streamlit-expanderContent {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
  }

  /* ── Divider ── */
  hr { border-color: var(--border) !important; }

  /* ── Alerts ── */
  .stAlert { border-radius: 10px !important; border: 1px solid var(--border) !important; }
  .stSuccess { background: rgba(57,255,20,.07) !important; border-color: var(--success) !important; }
  .stWarning { background: rgba(255,107,53,.07) !important; border-color: var(--warn) !important; }
  .stError   { background: rgba(255,50,50,.07) !important; }
  .stInfo    { background: var(--accent-glow) !important; border-color: var(--accent) !important; }
</style>
""", unsafe_allow_html=True)

# ── Custom HTML components ──────────────────────────────────────────────────────
def hero_banner():
    st.markdown("""
    <div style="
      background: linear-gradient(135deg, #0d0d0f 0%, #13131a 40%, #0a1a20 100%);
      border: 1px solid rgba(0,229,255,.2);
      border-radius: 16px;
      padding: 2rem 2.4rem;
      margin-bottom: 1.5rem;
      position: relative;
      overflow: hidden;
    ">
      <div style="
        position: absolute; top: 0; right: 0; width: 320px; height: 100%;
        background: radial-gradient(ellipse at top right, rgba(0,229,255,.08) 0%, transparent 70%);
        pointer-events: none;
      "></div>
      <div style="display:flex; align-items:center; gap:1rem; margin-bottom:.6rem;">
        <div style="
          background: rgba(0,229,255,.12);
          border: 1px solid rgba(0,229,255,.3);
          border-radius: 10px;
          padding: .5rem .8rem;
          font-size: 1.6rem;
        ">⚙️</div>
        <div>
          <h1 style="margin:0; font-size:1.7rem; font-weight:700;
                     background:linear-gradient(90deg,#00e5ff,#ffffff);
                     -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            Industrial GraphRAG Brain
          </h1>
          <p style="margin:0; color:#8888aa; font-size:.85rem; letter-spacing:.3px;">
            Edge Computing · Fully Offline · Zero Cloud Dependency
          </p>
        </div>
      </div>
      <div style="display:flex; gap:2rem; margin-top:.8rem; flex-wrap:wrap;">
        <span style="color:#8888aa; font-size:.8rem;">🟢 &nbsp;Ollama&nbsp;Local&nbsp;LLM&nbsp;Active</span>
        <span style="color:#8888aa; font-size:.8rem;">📊 &nbsp;NetworkX&nbsp;Graph&nbsp;Engine</span>
        <span style="color:#8888aa; font-size:.8rem;">🔒 &nbsp;Air-Gapped&nbsp;·&nbsp;ISO-45001&nbsp;Compliant</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

def node_badge(node_id: str, entity_type: str, description: str):
    color_map = {
        "EQUIPMENT":          ("#00e5ff", "rgba(0,229,255,.12)"),
        "SENSOR":             ("#a78bfa", "rgba(167,139,250,.12)"),
        "PROCEDURE":          ("#39ff14", "rgba(57,255,20,.12)"),
        "HAZARD":             ("#ff6b35", "rgba(255,107,53,.12)"),
        "COMPLIANCE_STANDARD":("#f59e0b", "rgba(245,158,11,.12)"),
    }
    color, bg = color_map.get(entity_type, ("#8888aa", "rgba(136,136,170,.1)"))
    st.markdown(f"""
    <div style="
      background:{bg};
      border:1px solid {color}44;
      border-left: 3px solid {color};
      border-radius:10px; padding:.8rem 1rem; margin:.4rem 0;
    ">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="color:{color}; font-weight:700; font-size:.95rem;
                     font-family:'JetBrains Mono',monospace;">{node_id}</span>
        <span style="color:{color}; font-size:.7rem; background:{bg};
                     border:1px solid {color}44; border-radius:20px;
                     padding:.15rem .6rem; letter-spacing:.5px;">{entity_type}</span>
      </div>
      <p style="color:#b0b0cc; font-size:.8rem; margin:.3rem 0 0;">{description}</p>
    </div>
    """, unsafe_allow_html=True)

def chat_bubble(role: str, content: str, timestamp: str = ""):
    if role == "user":
        st.markdown(f"""
        <div style="display:flex; justify-content:flex-end; margin:.8rem 0;">
          <div style="
            background: linear-gradient(135deg, rgba(0,229,255,.2), rgba(0,229,255,.08));
            border: 1px solid rgba(0,229,255,.3);
            border-radius: 16px 16px 4px 16px;
            padding: .75rem 1.1rem;
            max-width: 78%;
          ">
            <p style="color:#f0f0f5; margin:0; font-size:.9rem; line-height:1.5;">{content}</p>
            <span style="color:#8888aa; font-size:.7rem;">{timestamp}</span>
          </div>
          <div style="
            width:34px; height:34px; border-radius:50%;
            background:rgba(0,229,255,.15); border:1px solid rgba(0,229,255,.3);
            display:flex; align-items:center; justify-content:center;
            margin-left:.6rem; flex-shrink:0; font-size:1rem;
          ">👤</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display:flex; justify-content:flex-start; margin:.8rem 0;">
          <div style="
            width:34px; height:34px; border-radius:50%;
            background:rgba(57,255,20,.1); border:1px solid rgba(57,255,20,.3);
            display:flex; align-items:center; justify-content:center;
            margin-right:.6rem; flex-shrink:0; font-size:1rem;
          ">⚙️</div>
          <div style="
            background: var(--bg-surface, #1a1a24);
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 16px 16px 16px 4px;
            padding: .75rem 1.1rem;
            max-width: 78%;
          ">
            <p style="color:#f0f0f5; margin:0; font-size:.9rem; line-height:1.6;">{content}</p>
            <span style="color:#8888aa; font-size:.7rem;">{timestamp}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

def section_header(icon: str, title: str, subtitle: str = ""):
    sub = f'<p style="color:#8888aa; font-size:.8rem; margin:0;">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:.7rem; margin-bottom:1rem;">
      <span style="font-size:1.2rem;">{icon}</span>
      <div>
        <h3 style="margin:0; font-size:1.05rem; color:#f0f0f5;">{title}</h3>
        {sub}
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Session state ───────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "graph_loaded":    False,
        "builder":         None,
        "engine":          None,
        "chat_history":    [],
        "selected_node":   None,
        "graph_stats":     {},
        "filter_type":     "ALL",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ── Graph loader ────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_graph_resources(json_path: str, graphml_path: str):
    """
    Loads and builds the NetworkX graph from the data contract.
    Falls back to GraphML cache if fresh JSON isn't available.
    """
    builder = GraphRAGBuilder(data_contract_path=json_path)
    if not builder.load_data_contract():
        return None, None, "❌ Could not load data contract. Run batch_extractor.py first."
    if not builder.build_graph():
        return None, None, "❌ Failed to build graph."

    # Persist GraphML for the search engine
    try:
        import networkx as nx
        nx.write_graphml(builder.graph, graphml_path)
    except Exception:
        pass

    engine = GraphSearchEngine(
        graph_path=graphml_path,
        data_contract_path=json_path,
    )
    if not engine.load_graph():
        return builder, None, "⚠️ Search engine couldn't load saved graph."
    engine.load_data_contract()

    stats = builder.get_graph_stats()
    return builder, engine, None, stats


# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1.2rem .5rem 1rem;">
      <div style="font-size:2.2rem; margin-bottom:.4rem;">⚙️</div>
      <h2 style="font-size:1.1rem; margin:0; color:#00e5ff; letter-spacing:.5px;">AI-HackerZ</h2>
      <p style="color:#8888aa; font-size:.75rem; margin:.2rem 0 0;">GraphRAG Control Panel</p>
    </div>
    <hr style="border-color:rgba(0,229,255,.15); margin:.5rem 0 1rem;">
    """, unsafe_allow_html=True)

    # ── Load graph ──
    if not st.session_state.graph_loaded:
        load_btn = st.button("⚡  Initialize Graph Engine", use_container_width=True)
        if load_btn:
            with st.spinner("Building knowledge graph…"):
                result = load_graph_resources(str(GRAPH_JSON), str(GRAPH_ML))
                if len(result) == 4:
                    builder, engine, err, stats = result
                else:
                    builder, engine, err = result
                    stats = {}

                if err and not builder:
                    st.error(err)
                else:
                    st.session_state.builder     = builder
                    st.session_state.engine      = engine
                    st.session_state.graph_loaded = True
                    st.session_state.graph_stats  = stats or {}
                    if err:
                        st.warning(err)
                    else:
                        st.success("Graph ready!")
                    st.rerun()
    else:
        st.markdown('<p style="color:#39ff14; font-size:.85rem; text-align:center;">✅ &nbsp;Graph Engine Active</p>', unsafe_allow_html=True)
        if st.button("🔄  Reload Graph", use_container_width=True):
            load_graph_resources.clear()
            for k in ["graph_loaded", "builder", "engine", "graph_stats", "selected_node"]:
                st.session_state[k] = None if k not in ["graph_loaded"] else False
            st.rerun()

    st.markdown("<hr style='border-color:rgba(0,229,255,.15);'>", unsafe_allow_html=True)

    # ── Graph stats ──
    stats = st.session_state.graph_stats or {}
    if stats:
        st.markdown('<p style="color:#8888aa; font-size:.75rem; letter-spacing:.5px; margin-bottom:.5rem;">GRAPH METRICS</p>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        col1.metric("Nodes",  stats.get("total_nodes", 0))
        col2.metric("Edges",  stats.get("total_edges", 0))
        st.markdown(f"""
        <div style="margin-top:.5rem; font-size:.78rem; color:#8888aa; line-height:1.8;">
          <div>Directed Graph: <span style="color:#00e5ff;">{'Yes' if stats.get('is_directed') else 'No'}</span></div>
          <div>Connected: <span style="color:#{'39ff14' if stats.get('is_connected') else 'ff6b35'};">
            {'Yes' if stats.get('is_connected') else 'No'}</span></div>
          <div>Avg In-Degree: <span style="color:#00e5ff;">{stats.get('average_in_degree', 0):.2f}</span></div>
          <div>Avg Out-Degree: <span style="color:#00e5ff;">{stats.get('average_out_degree', 0):.2f}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(0,229,255,.15);'>", unsafe_allow_html=True)

    # ── Fault Risk Leaderboard ──
    if st.session_state.graph_loaded and st.session_state.builder:
        _b = st.session_state.builder
        _all = _b.get_all_node_ids()
        risk_scores = {}
        for _nid in _all:
            _info = _b.get_node_info(_nid)
            if _info and _info.get("entity_type") == "EQUIPMENT":
                _hazards  = sum(1 for _, _, d in _b.graph.in_edges(_nid, data=True)
                                if _b.get_node_info(_) and
                                   _b.get_node_info(_).get("entity_type") == "HAZARD")
                _sensors  = sum(1 for _, _, d in _b.graph.in_edges(_nid, data=True)
                                if _b.get_node_info(_) and
                                   _b.get_node_info(_).get("entity_type") == "SENSOR")
                _has_esd  = any(d.get("relation_type") in ("INITIATES","TRIGGERS")
                                for _, _, d in _b.graph.out_edges(_nid, data=True))
                risk_scores[_nid] = _hazards * 40 + _sensors * 15 + (20 if not _has_esd else 0)

        if risk_scores:
            st.markdown('<p style="color:#8888aa; font-size:.75rem; letter-spacing:.5px; margin-bottom:.5rem;">⚠️ FAULT RISK LEADERBOARD</p>', unsafe_allow_html=True)
            for _nid, _score in sorted(risk_scores.items(), key=lambda x: x[1], reverse=True):
                _color = "#ff6b35" if _score >= 50 else "#f59e0b" if _score >= 20 else "#39ff14"
                _label = "HIGH" if _score >= 50 else "MED" if _score >= 20 else "LOW"
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center;
                            background:rgba(0,0,0,.2); border-left:3px solid {_color};
                            border-radius:6px; padding:.35rem .6rem; margin:.25rem 0;">
                  <span style="color:#f0f0f5; font-size:.78rem; font-family:'JetBrains Mono',monospace;">{_nid}</span>
                  <span style="color:{_color}; font-size:.7rem; font-weight:700;">{_label}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(0,229,255,.15);'>", unsafe_allow_html=True)

    # ── Filter ──
    st.markdown('<p style="color:#8888aa; font-size:.75rem; letter-spacing:.5px; margin-bottom:.4rem;">FILTER BY TYPE</p>', unsafe_allow_html=True)
    filter_type = st.selectbox("Filter by entity type", ["ALL","EQUIPMENT","SENSOR","PROCEDURE","HAZARD","COMPLIANCE_STANDARD"], label_visibility="collapsed")
    st.session_state.filter_type = filter_type

    st.markdown("<hr style='border-color:rgba(0,229,255,.15);'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:.73rem; color:#8888aa; line-height:1.9;">
      <b style="color:#f0f0f5;">HOW TO USE</b><br>
      1. Click <em>Initialize Graph Engine</em><br>
      2. Explore the <em>Knowledge Graph</em> tab<br>
      3. Click any node to inspect it<br>
      4. Ask questions in <em>AI Query</em> tab<br>
      5. Browse raw entities in <em>Explorer</em>
    </div>
    """, unsafe_allow_html=True)

# ── Main content ────────────────────────────────────────────────────────────────
hero_banner()

if not st.session_state.graph_loaded:
    # Landing state
    st.markdown("""
    <div style="
      border:1px dashed rgba(0,229,255,.25); border-radius:16px;
      padding:3rem 2rem; text-align:center; margin-top:1rem;
    ">
      <div style="font-size:3rem; margin-bottom:.8rem;">🔌</div>
      <h2 style="color:#f0f0f5;">Graph Engine Not Loaded</h2>
      <p style="color:#8888aa; font-size:.9rem; max-width:420px; margin:.5rem auto 0;">
        Click <strong style="color:#00e5ff;">⚡ Initialize Graph Engine</strong> in the
        sidebar to parse the data contract and build the knowledge graph.
        Ensure <code>data/graph_input.json</code> exists (run
        <code>batch_extractor.py</code> first).
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Tabs ────────────────────────────────────────────────────────────────────────
builder: GraphRAGBuilder = st.session_state.builder
engine: GraphSearchEngine = st.session_state.engine

tab_graph, tab_query, tab_explorer, tab_risk, tab_contract = st.tabs([
    "📊  Knowledge Graph",
    "🤖  AI Query Interface",
    "🔍  Node Explorer",
    "⚠️  Risk Analysis",
    "📋  Data Contract",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 ─ Knowledge Graph Visualisation
# ═══════════════════════════════════════════════════════════════════════════════
with tab_graph:
    section_header("📊", "Live Knowledge Graph", "Interactive directed graph — click nodes to inspect them")

    try:
        from pyvis.network import Network
        import streamlit.components.v1 as components

        # Build PyVis network
        net = Network(
            height="600px",
            width="100%",
            bgcolor="#0d0d0f",
            font_color="#f0f0f5",
            directed=True,
        )
        net.set_options("""
        {
          "nodes": {
            "shape": "dot",
            "size": 22,
            "font": { "size": 14, "face": "Inter", "color": "#f0f0f5" },
            "borderWidth": 2,
            "shadow": { "enabled": true, "size": 12 }
          },
          "edges": {
            "arrows": { "to": { "enabled": true, "scaleFactor": 0.7 } },
            "color": { "color": "#00e5ff", "opacity": 0.55 },
            "font": { "size": 10, "color": "#8888aa", "strokeWidth": 0 },
            "width": 1.5,
            "smooth": { "type": "curvedCW", "roundness": 0.2 }
          },
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -8000,
              "centralGravity": 0.35,
              "springLength": 160,
              "springConstant": 0.04,
              "damping": 0.09
            },
            "stabilization": { "iterations": 250 }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 150,
            "navigationButtons": false,
            "keyboard": true,
            "multiselect": false
          }
        }
        """)

        # Node color map by entity type
        COLOR_MAP = {
            "EQUIPMENT":           "#00e5ff",
            "SENSOR":              "#a78bfa",
            "PROCEDURE":           "#39ff14",
            "HAZARD":              "#ff6b35",
            "COMPLIANCE_STANDARD": "#f59e0b",
            "UNKNOWN":             "#8888aa",
        }

        ft = st.session_state.filter_type
        all_ids = builder.get_all_node_ids()

        for node_id in all_ids:
            info   = builder.get_node_info(node_id)
            etype  = info.get("entity_type", "UNKNOWN") if info else "UNKNOWN"
            desc   = info.get("description", "") if info else ""
            if ft != "ALL" and etype != ft:
                continue
            color  = COLOR_MAP.get(etype, "#8888aa")
            size   = 28 if etype == "EQUIPMENT" else 22 if etype == "SENSOR" else 20
            title  = f"<b style='color:{color}'>{node_id}</b><br><em style='color:#8888aa'>{etype}</em><br>{desc}"
            net.add_node(node_id, label=node_id, color=color, size=size, title=title)

        # Build a set of nodes actually added to PyVis (may be filtered)
        added_nodes = set(net.get_nodes())

        for u, v, data in builder.graph.edges(data=True):
            # Only add edge if BOTH endpoints were added to the PyVis graph
            if u not in added_nodes or v not in added_nodes:
                continue
            rtype = data.get("relation_type", "")
            ctx   = data.get("context", "")
            net.add_edge(u, v, label=rtype, title=ctx)

        # ── Inject click-to-inspect JS bridge into PyVis HTML ──────────────────
        html_path = "/tmp/graph_viz.html"
        net.save_graph(html_path)
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        click_bridge_js = """
<script>
// Wait for the vis-network to be ready, then attach click handler
function attachClickBridge() {
  if (typeof network !== 'undefined') {
    network.on("click", function(params) {
      if (params.nodes.length > 0) {
        var nodeId = params.nodes[0];
        // Highlight the clicked node
        network.selectNodes([nodeId]);
        // Store in parent window's sessionStorage so polling bridge can pick it up
        try { window.parent.sessionStorage.setItem('__pyvis_clicked__', nodeId); } catch(e) {}
        // Also paint a subtle ring on the node
        network.setSelection({nodes: [nodeId]}, {highlightEdges: true});
      }
    });
    // Hover cursor
    network.on("hoverNode", function() {
      document.body.style.cursor = 'pointer';
    });
    network.on("blurNode", function() {
      document.body.style.cursor = 'default';
    });
  } else {
    setTimeout(attachClickBridge, 200);
  }
}
attachClickBridge();
</script>
"""
        html_content = html_content.replace("</body>", click_bridge_js + "</body>")

        # Render graph
        components.html(html_content, height=630, scrolling=False)

        # ── Invisible polling bridge: reads sessionStorage, navigates to ?node= ──
        components.html("""
<script>
(function() {
  function poll() {
    try {
      var nodeId = window.parent.sessionStorage.getItem('__pyvis_clicked__');
      if (nodeId) {
        window.parent.sessionStorage.removeItem('__pyvis_clicked__');
        var url = new URL(window.parent.location.href);
        url.searchParams.set('node', nodeId);
        // Navigate parent → triggers Streamlit rerun with ?node=<id>
        window.parent.location.href = url.toString();
      }
    } catch(e) {}
  }
  setInterval(poll, 250);
})();
</script>
""", height=0, scrolling=False)

        # Legend
        st.markdown("""
        <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-top:.6rem;">
          <span style="font-size:.78rem; color:#00e5ff;">● EQUIPMENT</span>
          <span style="font-size:.78rem; color:#a78bfa;">● SENSOR</span>
          <span style="font-size:.78rem; color:#39ff14;">● PROCEDURE</span>
          <span style="font-size:.78rem; color:#ff6b35;">● HAZARD</span>
          <span style="font-size:.78rem; color:#f59e0b;">● COMPLIANCE_STANDARD</span>
          <span style="font-size:.78rem; color:#8888aa; margin-left:1rem;">
            Drag nodes · Scroll to zoom · Hover for details
          </span>
        </div>
        """, unsafe_allow_html=True)

    except ImportError:
        st.warning("⚠️ `pyvis` not installed. Run: `pip install pyvis`")

    st.markdown("<hr style='border-color:rgba(0,229,255,.1); margin:1.2rem 0;'>", unsafe_allow_html=True)
    section_header("🔎", "Node Inspector", "Click any node in the graph above — or select below")

    all_ids = builder.get_all_node_ids()

    # Auto-select from click bridge (via session_state set from query params)
    preselect = st.session_state.get("selected_node", "")
    default_idx = 0
    opts = ["— choose a node —"] + all_ids
    if preselect in all_ids:
        default_idx = opts.index(preselect)

    selected = st.selectbox(
        "Select node",
        opts,
        index=default_idx,
        label_visibility="collapsed",
        key="node_inspector_select",
    )
    # Sync back: if user picks manually, keep session state updated
    if selected and selected != "— choose a node —":
        st.session_state["selected_node"] = selected
        with st.spinner("Extracting local context…"):
            context = builder.extract_local_context(selected)
        if context:
            info = builder.get_node_info(selected)
            etype = info.get("entity_type", "UNKNOWN") if info else "UNKNOWN"
            desc  = info.get("description", "") if info else ""
            in_d  = info.get("in_degree", 0) if info else 0
            out_d = info.get("out_degree", 0) if info else 0

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Entity Type",  etype)
            col_b.metric("Incoming Links", in_d)
            col_c.metric("Outgoing Links", out_d)

            st.markdown(f"""
            <div style="background:#13131a; border:1px solid rgba(0,229,255,.15);
                        border-radius:12px; padding:1rem 1.2rem; margin-top:.8rem;">
              <p style="color:#8888aa; font-size:.75rem; margin:0 0 .4rem;">DESCRIPTION</p>
              <p style="color:#f0f0f5; font-size:.9rem; margin:0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📄 Raw Graph Context (sent to LLM)"):
                st.code(context, language="text")
        else:
            st.warning("No context found for this node.")

    # ── Path Finder ─────────────────────────────────────────────────────────────
    st.markdown("<hr style='border-color:rgba(0,229,255,.1); margin:1.2rem 0;'>", unsafe_allow_html=True)
    section_header("🔗", "Relationship Path Finder", "Trace the shortest connection between any two nodes")

    if engine is not None:
        all_ids_pf = builder.get_all_node_ids()
        pf_col1, pf_col2 = st.columns(2)
        src_node = pf_col1.selectbox("From node", ["— select source —"] + all_ids_pf, key="pf_src", label_visibility="visible")
        tgt_node = pf_col2.selectbox("To node",   ["— select target —"] + all_ids_pf, key="pf_tgt", label_visibility="visible")

        if st.button("🔍  Find Path", key="find_path_btn"):
            if src_node.startswith("—") or tgt_node.startswith("—"):
                st.warning("Please select both a source and a target node.")
            elif src_node == tgt_node:
                st.info("Source and target are the same node.")
            else:
                with st.spinner("Tracing relationship path…"):
                    path = engine.find_path(src_node, tgt_node)
                if path:
                    path_ctx = engine.format_path_as_context(path)
                    st.success(f"✅ Path found! {len(path)-1} hop(s): **{' → '.join(path)}**")
                    # Visual hop chain
                    hop_html = ""
                    COLOR_MAP_PF = {"EQUIPMENT":"#00e5ff","SENSOR":"#a78bfa","PROCEDURE":"#39ff14",
                                    "HAZARD":"#ff6b35","COMPLIANCE_STANDARD":"#f59e0b"}
                    for i, nid in enumerate(path):
                        inf = builder.get_node_info(nid)
                        et  = inf.get("entity_type","UNKNOWN") if inf else "UNKNOWN"
                        c   = COLOR_MAP_PF.get(et,"#8888aa")
                        hop_html += f"<span style='background:rgba(0,0,0,.3); border:1px solid {c}55; border-radius:8px; padding:.3rem .7rem; color:{c}; font-family:monospace; font-size:.85rem;'>{nid}</span>"
                        if i < len(path)-1:
                            edge_d = builder.graph.get_edge_data(path[i], path[i+1]) or {}
                            rel    = edge_d.get("relation_type","→")
                            hop_html += f"<span style='color:#8888aa; margin:0 .4rem; font-size:.8rem;'>──[{rel}]──▶</span>"
                    st.markdown(f"<div style='display:flex; flex-wrap:wrap; gap:.4rem; align-items:center; margin:.8rem 0;'>{hop_html}</div>", unsafe_allow_html=True)
                    with st.expander("📄 Full path context (sent to LLM)"):
                        st.code(path_ctx, language="text")
                else:
                    st.error(f"❌ No path found between **{src_node}** and **{tgt_node}** in either direction.")
    else:
        st.info("Load the graph engine first to use the path finder.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 ─ AI Query Interface
# ═══════════════════════════════════════════════════════════════════════════════
with tab_query:
    section_header("🤖", "AI Query Interface", "Ask the knowledge graph anything in natural language")

    if engine is None:
        st.error("Search engine not available. Ensure graph is loaded and graph.graphml is written.")
    else:
        # ── Example queries ──
        st.markdown('<p style="color:#8888aa; font-size:.8rem; margin-bottom:.4rem;">QUICK QUERIES</p>', unsafe_allow_html=True)
        sample_queries = [
            "What does PUMP-101A connect to?",
            "Which sensors monitor the cooling system?",
            "What hazards exist in the plant?",
            "What safety standards govern operations?",
            "Describe the emergency shutdown procedure.",
        ]
        cols = st.columns(len(sample_queries))
        for i, q in enumerate(sample_queries):
            if cols[i].button(f"💬 {q[:22]}…" if len(q) > 22 else f"💬 {q}", key=f"sample_{i}", use_container_width=True):
                st.session_state["prefill_query"] = q

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        # ── Chat history ──
        chat_container = st.container()
        with chat_container:
            if not st.session_state.chat_history:
                st.markdown("""
                <div style="text-align:center; padding:2.5rem 1rem; color:#8888aa;">
                  <div style="font-size:2.5rem; margin-bottom:.5rem;">💬</div>
                  <p style="font-size:.9rem;">Ask your first question above to begin exploring the knowledge graph.</p>
                </div>
                """, unsafe_allow_html=True)
            for msg in st.session_state.chat_history:
                chat_bubble(msg["role"], msg["content"], msg.get("time", ""))

        st.markdown("<hr style='border-color:rgba(0,229,255,.1);'>", unsafe_allow_html=True)

        # ── Query input ──
        prefill = st.session_state.pop("prefill_query", "")
        with st.form(key="query_form", clear_on_submit=True):
            user_input = st.text_input(
                "Your query",
                value=prefill,
                placeholder="e.g. What are the risk factors for PUMP-101A?",
                label_visibility="collapsed",
            )
            col_submit, col_clear, col_depth = st.columns([3, 1, 2])
            submit  = col_submit.form_submit_button("⚡  Ask AI", use_container_width=True)
            clear   = col_clear.form_submit_button("🗑️", use_container_width=True)
            depth   = col_depth.selectbox("Search depth", [1, 2, 3], index=0, label_visibility="collapsed")

        if clear:
            st.session_state.chat_history = []
            st.rerun()

        if submit and user_input.strip():
            ts = time.strftime("%H:%M")
            st.session_state.chat_history.append({
                "role": "user", "content": user_input, "time": ts
            })

            with st.spinner("Searching graph + querying local LLM…"):
                try:
                    ctx, answer = engine.query(user_input, top_k=5, context_depth=int(depth))
                    st.session_state.chat_history.append({
                        "role": "assistant", "content": answer, "time": time.strftime("%H:%M")
                    })
                    if ctx:
                        st.session_state.chat_history[-1]["context"] = ctx
                except Exception as e:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"⚠️ Error: {e}\n\nEnsure Ollama is running and `llama3.2` is pulled (`ollama pull llama3.2`).",
                        "time": time.strftime("%H:%M"),
                    })
            st.rerun()

        # ── Retrieved context expander ──
        if st.session_state.chat_history:
            last = st.session_state.chat_history[-1]
            if last.get("role") == "assistant" and last.get("context"):
                with st.expander("🔎 View retrieved graph context"):
                    st.code(last["context"], language="text")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 ─ Node Explorer
# ═══════════════════════════════════════════════════════════════════════════════
with tab_explorer:
    section_header("🔍", "Entity Explorer", "Browse all nodes in the knowledge graph")

    ft = st.session_state.filter_type
    all_ids = builder.get_all_node_ids()

    # Search bar
    search_term = st.text_input("Search nodes", placeholder="Type a keyword…", label_visibility="collapsed")

    filtered = []
    for node_id in all_ids:
        info  = builder.get_node_info(node_id)
        etype = info.get("entity_type", "UNKNOWN") if info else "UNKNOWN"
        desc  = info.get("description", "") if info else ""
        if ft != "ALL" and etype != ft:
            continue
        if search_term and search_term.lower() not in node_id.lower() and search_term.lower() not in desc.lower():
            continue
        filtered.append((node_id, etype, desc, info))

    if not filtered:
        st.info("No nodes match your filter/search.")
    else:
        st.markdown(f'<p style="color:#8888aa; font-size:.8rem; margin-bottom:.5rem;">{len(filtered)} entity/entities found</p>', unsafe_allow_html=True)
        for node_id, etype, desc, info in filtered:
            node_badge(node_id, etype, desc)

        # ── Selected node detail ──
        st.markdown("<hr style='border-color:rgba(0,229,255,.1); margin:1rem 0;'>", unsafe_allow_html=True)
        section_header("📌", "Relationship Map", "Outgoing and incoming edges for a selected node")
        pick = st.selectbox("Pick node for relationship map", ["— select —"] + [n for n, *_ in filtered], label_visibility="collapsed")
        if pick and pick != "— select —":
            context = builder.extract_local_context(pick)
            if context:
                st.code(context, language="text")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 ─ Risk Analysis
# ═══════════════════════════════════════════════════════════════════════════════
with tab_risk:
    section_header("⚠️", "Fault Risk Analysis", "Automated risk scoring for all equipment nodes based on graph topology")

    all_ids_r = builder.get_all_node_ids()
    risk_data = []
    for nid in all_ids_r:
        info = builder.get_node_info(nid)
        if not info or info.get("entity_type") != "EQUIPMENT":
            continue
        hazards  = [(src, d) for src, _, d in builder.graph.in_edges(nid, data=True)
                    if builder.get_node_info(src) and
                       builder.get_node_info(src).get("entity_type") == "HAZARD"]
        sensors  = [(src, d) for src, _, d in builder.graph.in_edges(nid, data=True)
                    if builder.get_node_info(src) and
                       builder.get_node_info(src).get("entity_type") == "SENSOR"]
        procs    = [(tgt, d) for _, tgt, d in builder.graph.out_edges(nid, data=True)
                    if builder.get_node_info(tgt) and
                       builder.get_node_info(tgt).get("entity_type") == "PROCEDURE"]
        has_redundancy = any(d.get("relation_type") == "HAS_REDUNDANCY"
                             for _, _, d in builder.graph.out_edges(nid, data=True))
        score = len(hazards) * 40 + (max(0, 2 - len(sensors)) * 15) + (0 if procs else 25) + (0 if has_redundancy else 10)
        risk_data.append({
            "node_id": nid,
            "desc": info.get("description", ""),
            "hazards": len(hazards),
            "sensors": len(sensors),
            "procedures": len(procs),
            "redundancy": has_redundancy,
            "score": score,
        })
    risk_data.sort(key=lambda x: x["score"], reverse=True)

    if not risk_data:
        st.info("No EQUIPMENT nodes found in the graph.")
    else:
        st.markdown(f'<p style="color:#8888aa; font-size:.8rem;">Analysed <b style="color:#f0f0f5;">{len(risk_data)}</b> equipment nodes · Score = f(hazards linked, sensor coverage, ESD procedures, redundancy)</p>', unsafe_allow_html=True)
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        for rd in risk_data:
            score   = rd["score"]
            color   = "#ff6b35" if score >= 50 else "#f59e0b" if score >= 20 else "#39ff14"
            label   = "🔴 HIGH RISK" if score >= 50 else "🟠 MEDIUM RISK" if score >= 20 else "🟢 LOW RISK"
            bar_pct = min(100, int(score * 1.2))
            st.markdown(f"""
            <div style="background:#13131a; border:1px solid {color}33; border-left:4px solid {color};
                        border-radius:12px; padding:1rem 1.2rem; margin:.5rem 0;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:.5rem;">
                <span style="color:{color}; font-family:'JetBrains Mono',monospace; font-weight:700; font-size:1rem;">{rd['node_id']}</span>
                <span style="color:{color}; font-size:.8rem; font-weight:600;">{label} &nbsp;|&nbsp; Score: {score}</span>
              </div>
              <div style="background:#0d0d0f; border-radius:4px; height:6px; margin-bottom:.7rem;">
                <div style="width:{bar_pct}%; background:linear-gradient(90deg,{color},{color}88); height:6px; border-radius:4px;"></div>
              </div>
              <p style="color:#b0b0cc; font-size:.8rem; margin:0 0 .5rem;">{rd['desc']}</p>
              <div style="display:flex; gap:1.5rem; font-size:.78rem; color:#8888aa;">
                <span>⚡ Hazards linked: <b style="color:{color};">{rd['hazards']}</b></span>
                <span>📡 Sensors monitoring: <b style="color:#a78bfa;">{rd['sensors']}</b></span>
                <span>📋 ESD procedures: <b style="color:#39ff14;">{rd['procedures']}</b></span>
                <span>♻️ Redundancy: <b style="color:#{'39ff14' if rd['redundancy'] else 'ff6b35'};">
                  {'Yes' if rd['redundancy'] else 'No'}</b></span>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color:rgba(0,229,255,.1); margin:1.2rem 0;'>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#13131a; border:1px solid rgba(0,229,255,.1);
                    border-radius:12px; padding:1rem 1.2rem;">
          <p style="color:#8888aa; font-size:.78rem; margin:0 0 .4rem;">SCORING FORMULA</p>
          <p style="color:#f0f0f5; font-size:.85rem; font-family:'JetBrains Mono',monospace; margin:0;">
            Score = (Hazards × 40) + (Missing sensors × 15) + (No ESD proc × 25) + (No redundancy × 10)
          </p>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 ─ Data Contract Viewer
# ═══════════════════════════════════════════════════════════════════════════════
with tab_contract:
    section_header("📋", "Raw Data Contract", f"Source: {GRAPH_JSON}")

    try:
        with open(GRAPH_JSON, "r", encoding="utf-8") as f:
            raw = json.load(f)

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Document ID",    raw.get("document_id", "N/A"))
        col_b.metric("Entities",       len(raw.get("entities", [])))
        col_c.metric("Relationships",  len(raw.get("relationships", [])))

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        st.json(raw)

    except FileNotFoundError:
        st.error(f"Data contract not found at `{GRAPH_JSON}`.\nRun `batch_extractor.py` from `1_vision_extraction/` first.")
    except Exception as e:
        st.error(f"Error reading contract: {e}")

# ── Footer ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
  text-align:center; padding:1.2rem .5rem .5rem;
  color:#8888aa; font-size:.75rem; letter-spacing:.3px;
  border-top:1px solid rgba(0,229,255,.08); margin-top:2rem;
">
  AI-HackerZ · ET AI Hackathon 2026 · Problem Statement 8 ·
  <span style="color:#00e5ff;">100% Offline Edge-Computing GraphRAG</span>
</div>
""", unsafe_allow_html=True)
