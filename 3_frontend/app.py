"""
Person 3 - Full-Stack Integration Lead
3_frontend/app.py

Elite industrial GraphRAG dashboard. Fully offline, zero cloud dependencies.
"""

import sys
import os
import json
import time
import streamlit as st
from pathlib import Path
from typing import Dict, List

# ── Path bootstrap ────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parent.parent
DATA_DIR   = ROOT / "data"
GRAPH_JSON = DATA_DIR / "graph_input.json"
GRAPH_ML   = DATA_DIR / "graph.graphml"
KG_DIR     = ROOT / "2_knowledge_graph"
VIS_DIR    = ROOT / "1_vision_extraction"

for p in (str(KG_DIR), str(VIS_DIR), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from graph_builder  import GraphRAGBuilder
from graph_search   import GraphSearchEngine
from batch_extractor import BatchExtractor

# ── JS bridge — clicked node from graph ──────────────────────────────────────
_qp_node = st.query_params.get("node", "")
if _qp_node and _qp_node != st.session_state.get("selected_node", ""):
    st.session_state["selected_node"] = _qp_node
    st.session_state["prefill_query"] = f"Tell me everything about {_qp_node}."

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI-HackerZ | GraphRAG Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS  — Siri-meets-ChatGPT premium dark UI
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ─── Variables ─────────────────────────────────── */
:root {
  --ink:        #050508;
  --surface:    rgba(255,255,255,.04);
  --surface2:   rgba(255,255,255,.07);
  --glass:      rgba(12,12,20,.75);
  --border:     rgba(255,255,255,.08);
  --border-lit: rgba(255,255,255,.18);
  --cyan:       #22d3ee;
  --cyan-glow:  rgba(34,211,238,.25);
  --violet:     #818cf8;
  --violet-glow:rgba(129,140,248,.2);
  --rose:       #fb7185;
  --emerald:    #34d399;
  --amber:      #fbbf24;
  --txt:        rgba(255,255,255,.92);
  --txt2:       rgba(255,255,255,.5);
  --txt3:       rgba(255,255,255,.28);
  --radius:     16px;
}

/* ─── Background ──────────────────────────────────── */
html, body { background: #050508 !important; }

.stApp {
  background:
    radial-gradient(ellipse 80% 60% at 10% 20%,  rgba(129,140,248,.09) 0%, transparent 60%),
    radial-gradient(ellipse 60% 80% at 90% 80%,  rgba(34,211,238,.07)  0%, transparent 55%),
    radial-gradient(ellipse 50% 50% at 50% 40%,  rgba(251,113,133,.05) 0%, transparent 50%),
    radial-gradient(ellipse 70% 40% at 70% 10%,  rgba(52,211,153,.06)  0%, transparent 55%),
    #050508 !important;
  background-attachment: fixed !important;
}

/* ─── Layout ────────────────────────────────────────── */
.main .block-container {
  padding: 1.2rem 1.8rem 3rem;
  max-width: 100%;
}

/* ─── Typography ─────────────────────────────────── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1,h2,h3,h4 { color: var(--txt) !important; letter-spacing: -.4px; }

/* ─── Scrollbar ──────────────────────────────────── */
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,.12); border-radius: 8px; }

/* ─── Sidebar ────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: rgba(8,8,14,.95) !important;
  border-right: 1px solid var(--border) !important;
  backdrop-filter: blur(40px) saturate(180%) !important;
}
[data-testid="stSidebar"] * { color: var(--txt) !important; }
[data-testid="stSidebar"] p { color: var(--txt2) !important; }

/* ─── Metric cards ───────────────────────────────── */
[data-testid="metric-container"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: .9rem 1rem !important;
  backdrop-filter: blur(20px) !important;
  transition: border-color .3s, box-shadow .3s !important;
}
[data-testid="metric-container"]:hover {
  border-color: var(--border-lit) !important;
}
[data-testid="stMetricValue"] {
  background: linear-gradient(135deg, var(--cyan), var(--violet)) !important;
  -webkit-background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  background-clip: text !important;
  font-size: 1.9rem !important; font-weight: 800 !important;
  font-family: 'JetBrains Mono', monospace !important;
}
[data-testid="stMetricLabel"] {
  color: var(--txt3) !important;
  font-size: .7rem !important;
  letter-spacing: .8px !important;
  text-transform: uppercase !important;
}

/* ─── Buttons ────────────────────────────────────── */
.stButton > button {
  background: var(--surface) !important;
  color: var(--txt) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  font-weight: 500 !important;
  font-size: .85rem !important;
  backdrop-filter: blur(20px) !important;
  transition: all .2s cubic-bezier(.4,0,.2,1) !important;
}
.stButton > button:hover {
  background: var(--surface2) !important;
  border-color: var(--border-lit) !important;
  box-shadow: 0 0 0 1px rgba(255,255,255,.1), 0 8px 32px rgba(0,0,0,.4) !important;
  transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* Primary CTA — glowing cyan */
.stButton > button[kind="primary"],
.stButton > button:first-child {
  background: linear-gradient(135deg, rgba(34,211,238,.15), rgba(129,140,248,.1)) !important;
  border-color: rgba(34,211,238,.3) !important;
  box-shadow: 0 0 0 0 var(--cyan-glow), inset 0 1px 0 rgba(255,255,255,.08) !important;
}
.stButton > button:first-child:hover {
  box-shadow: 0 0 30px var(--cyan-glow), 0 0 60px rgba(34,211,238,.1) !important;
}

/* ─── Text inputs ────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea textarea {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  color: var(--txt) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: .9rem !important;
  backdrop-filter: blur(20px) !important;
  transition: border-color .2s, box-shadow .2s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
  border-color: rgba(34,211,238,.4) !important;
  box-shadow: 0 0 0 4px rgba(34,211,238,.08), 0 0 20px rgba(34,211,238,.1) !important;
  outline: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea textarea::placeholder { color: var(--txt3) !important; }

/* ─── Selectbox ──────────────────────────────────── */
.stSelectbox > div > div {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  color: var(--txt) !important;
  backdrop-filter: blur(20px) !important;
}
.stSelectbox > div > div:hover { border-color: var(--border-lit) !important; }

/* ─── Tabs ───────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background: transparent !important;
  gap: 2px !important;
  padding: 0 !important;
  border-bottom: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--txt3) !important;
  border-radius: 0 !important;
  font-weight: 500 !important;
  font-size: .88rem !important;
  padding: .7rem 1.2rem !important;
  border-bottom: 2px solid transparent !important;
  transition: color .2s, border-color .2s !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--txt2) !important; }
.stTabs [aria-selected="true"] {
  background: transparent !important;
  color: var(--txt) !important;
  border-bottom: 2px solid var(--cyan) !important;
  text-shadow: 0 0 20px var(--cyan-glow) !important;
}
.stTabs [data-baseweb="tab-panel"] {
  background: transparent !important;
  border: none !important;
  padding: 1.5rem 0 !important;
}

/* ─── Expanders ──────────────────────────────────── */
.streamlit-expanderHeader {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  color: var(--txt) !important;
  backdrop-filter: blur(20px) !important;
  transition: border-color .2s !important;
}
.streamlit-expanderHeader:hover { border-color: var(--border-lit) !important; }
.streamlit-expanderContent {
  background: rgba(8,8,14,.6) !important;
  border: 1px solid var(--border) !important;
  border-top: none !important;
  border-radius: 0 0 12px 12px !important;
  backdrop-filter: blur(20px) !important;
}

/* ─── Alerts ─────────────────────────────────────── */
.stAlert { border-radius: 12px !important; backdrop-filter: blur(20px) !important; }
.stSuccess { background: rgba(52,211,153,.07) !important; border: 1px solid rgba(52,211,153,.25) !important; }
.stWarning { background: rgba(251,191,36,.06) !important; border: 1px solid rgba(251,191,36,.22) !important; }
.stError   { background: rgba(251,113,133,.07) !important; border: 1px solid rgba(251,113,133,.25) !important; }
.stInfo    { background: rgba(34,211,238,.06) !important;  border: 1px solid rgba(34,211,238,.22) !important; }

/* ─── Code (terminal) ────────────────────────────── */
.stCode, pre, code {
  background: rgba(0,0,0,.6) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: .82rem !important;
  backdrop-filter: blur(20px) !important;
}

/* ─── Progress bar ───────────────────────────────── */
.stProgress > div > div > div {
  background: linear-gradient(90deg, var(--cyan), var(--violet)) !important;
  border-radius: 8px !important;
  box-shadow: 0 0 12px var(--cyan-glow) !important;
}

/* ─── Spinner ────────────────────────────────────── */
.stSpinner > div { border-top-color: var(--cyan) !important; }

/* ─── Siri orb animations ────────────────────────── */
@keyframes orb-float {
  0%, 100% { transform: translateY(0px) scale(1); }
  33%       { transform: translateY(-8px) scale(1.02); }
  66%       { transform: translateY(4px) scale(.98); }
}
@keyframes orb-pulse {
  0%, 100% { opacity: .6; transform: scale(1); }
  50%       { opacity: 1;  transform: scale(1.15); }
}
@keyframes orb-ring {
  0%   { transform: scale(.8); opacity: .8; }
  100% { transform: scale(1.8); opacity: 0; }
}
@keyframes orb-active {
  0%,100% { transform: translateY(0) scale(1); filter: brightness(1); }
  25%     { transform: translateY(-6px) scale(1.06); filter: brightness(1.3); }
  75%     { transform: translateY(6px) scale(.95); filter: brightness(.9); }
}
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position: 200% center; }
}
@keyframes fade-up {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes slide-in-left {
  from { opacity: 0; transform: translateX(-16px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes slide-in-right {
  from { opacity: 0; transform: translateX(16px); }
  to   { opacity: 1; transform: translateX(0); }
}
@keyframes typing-blink {
  0%,100% { opacity: 1; } 50% { opacity: 0; }
}
@keyframes gauge-fill {
  from { stroke-dashoffset: 220; }
}
@keyframes badge-pop {
  0%   { transform: scale(.85); opacity: 0; }
  70%  { transform: scale(1.05); }
  100% { transform: scale(1);   opacity: 1; }
}
@keyframes status-pulse {
  0%,100% { box-shadow: 0 0 0 0 rgba(52,211,153,.5); }
  50%     { box-shadow: 0 0 0 6px rgba(52,211,153,.0); }
}

.msg-user  { animation: slide-in-right .35s cubic-bezier(.4,0,.2,1) both; }
.msg-ai    { animation: slide-in-left  .35s cubic-bezier(.4,0,.2,1) both; }
.fade-up   { animation: fade-up .4s cubic-bezier(.4,0,.2,1) both; }
.badge-pop { animation: badge-pop .4s cubic-bezier(.4,0,.2,1) both; }

hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }

/* ─── Apple Intelligence Siri Chat Input ─────────── */
[data-testid="stChatInput"] {
  background: rgba(10,10,15,0.7) !important;
  border-radius: 30px !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  backdrop-filter: blur(40px) saturate(200%) !important;
  box-shadow: 0 0 0 1px rgba(255,255,255,0.05), 0 10px 40px rgba(0,0,0,0.5) !important;
  position: relative;
  overflow: visible !important;
}
[data-testid="stChatInput"]::before {
  content: '';
  position: absolute; inset: -2px; border-radius: 32px; z-index: -1;
  background: linear-gradient(90deg, #818cf8, #22d3ee, #fb7185, #34d399, #818cf8);
  background-size: 200% 100%;
  animation: shimmer 4s linear infinite;
  opacity: 0.4;
  filter: blur(4px);
  pointer-events: none;
}
[data-testid="stChatInput"] textarea {
  color: var(--txt) !important;
  font-size: 1rem !important;
}
[data-testid="stChatInputSubmitButton"] {
  background: rgba(34,211,238,0.1) !important;
  color: #22d3ee !important;
  border-radius: 50% !important;
}
[data-testid="stChatInputSubmitButton"]:hover {
  background: rgba(34,211,238,0.2) !important;
  box-shadow: 0 0 15px rgba(34,211,238,0.4) !important;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
def _init_state():
    defaults = {
        "graph_loaded":  False, "builder": None, "engine": None,
        "chat_history":  [], "selected_node": None,
        "graph_stats":   {}, "filter_type": "ALL",
        "activity_feed": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ── Helpers ───────────────────────────────────────────────────────────────────
def activity_log(action: str, detail: str = "", icon: str = "◈"):
    if "activity_feed" not in st.session_state:
        st.session_state.activity_feed = []
    st.session_state.activity_feed.insert(0, {
        "ts": time.strftime("%H:%M:%S"), "icon": icon, "action": action, "detail": detail
    })
    st.session_state.activity_feed = st.session_state.activity_feed[:10]


# ── Graph loader ──────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_graph_resources(json_path: str, graphml_path: str):
    builder = GraphRAGBuilder(data_contract_path=json_path)
    if not builder.load_data_contract(): return None, None, "❌ Could not load data contract."
    if not builder.build_graph():        return None, None, "❌ Failed to build graph."
    try:
        import networkx as nx
        nx.write_graphml(builder.graph, graphml_path)
    except Exception: pass
    engine = GraphSearchEngine(graph_path=graphml_path, data_contract_path=json_path)
    if not engine.load_graph(): return builder, None, "⚠️ Search engine couldn't load graph."
    engine.load_data_contract()
    stats = builder.get_graph_stats()
    return builder, engine, None, stats


# ══════════════════════════════════════════════════════════════════════════════
# SIRI ORB COMPONENT
# ══════════════════════════════════════════════════════════════════════════════
def siri_orb(state: str = "idle", size: int = 100):
    """
    state: 'idle' | 'active' | 'online'
    Renders a pure CSS Siri-style animated orb.
    """
    if state == "online":
        c1, c2, c3 = "#22d3ee", "#818cf8", "#34d399"
        anim = "orb-float 5s ease-in-out infinite"
    elif state == "active":
        c1, c2, c3 = "#818cf8", "#fb7185", "#22d3ee"
        anim = "orb-active 1.4s ease-in-out infinite"
    else:
        c1, c2, c3 = "#1e3a4a", "#2d1b69", "#0f3460"
        anim = "orb-float 7s ease-in-out infinite"

    return f"""
    <div style="position:relative; width:{size}px; height:{size}px; margin:0 auto;">
      <!-- Outer glow ring -->
      <div style="
        position:absolute; inset:-14px; border-radius:50%;
        background:conic-gradient(from 0deg, {c1}, {c2}, {c3}, {c1});
        animation: orb-ring 3s ease-out infinite;
        opacity:.4;
      "></div>
      <!-- Orb body -->
      <div style="
        position:absolute; inset:0; border-radius:50%;
        background: conic-gradient(from 0deg at 40% 40%, {c1}, {c2}, {c3}, {c1});
        animation: {anim};
        box-shadow: 0 0 {size//2}px rgba(34,211,238,.3), 0 0 {size}px rgba(129,140,248,.15), inset 0 2px 4px rgba(255,255,255,.25);
        filter: blur(.5px);
      "></div>
      <!-- Inner gloss -->
      <div style="
        position:absolute; top:10%; left:15%; width:38%; height:32%;
        background: radial-gradient(ellipse, rgba(255,255,255,.45) 0%, transparent 70%);
        border-radius:50%; pointer-events:none;
      "></div>
    </div>"""


# ══════════════════════════════════════════════════════════════════════════════
# HERO HEADER
# ══════════════════════════════════════════════════════════════════════════════
def render_hero(stats: dict):
    loaded = stats.get("total_nodes", 0) > 0
    orb_state = "online" if loaded else "idle"
    n = stats.get("total_nodes", "—")
    e = stats.get("total_edges", "—")
    orb_html = siri_orb(orb_state, size=72)
    status_dot = "#34d399" if loaded else "#6b7280"
    status_txt = "ONLINE" if loaded else "OFFLINE"

    st.markdown(f"""
    <div class="fade-up" style="
      display:flex; align-items:center; gap:1.5rem;
      padding:1.6rem 2rem; margin-bottom:1.2rem;
      background: rgba(255,255,255,.02);
      border: 1px solid var(--border);
      border-radius: 24px;
      backdrop-filter: blur(40px) saturate(150%);
      overflow:hidden; position:relative;
    ">
      <!-- Left orb -->
      <div style="flex-shrink:0;">{orb_html}</div>

      <!-- Text block -->
      <div style="flex:1; min-width:0;">
        <div style="display:flex; align-items:center; gap:.6rem; margin-bottom:.3rem;">
          <h1 style="margin:0; font-size:1.6rem; font-weight:800; letter-spacing:-.5px;
            background:linear-gradient(135deg,#ffffff 0%,rgba(255,255,255,.6) 100%);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;
            background-clip:text;">
            Industrial GraphRAG Brain
          </h1>
          <span class="badge-pop" style="
            background:rgba({('52,211,153' if loaded else '107,114,128')},.12);
            border:1px solid rgba({('52,211,153' if loaded else '107,114,128')},.3);
            border-radius:999px; padding:.2rem .7rem;
            font-size:.65rem; font-weight:700; letter-spacing:.8px;
            color:{'#34d399' if loaded else '#6b7280'};
            animation: status-pulse 2s infinite;
          ">
            <span style="display:inline-block; width:5px; height:5px; border-radius:50%;
              background:{status_dot}; margin-right:.35rem; vertical-align:middle;"></span>
            {status_txt}
          </span>
        </div>
        <p style="margin:0; font-size:.8rem; color:var(--txt3); letter-spacing:.2px;">
          Edge Computing &nbsp;·&nbsp; 100% Offline &nbsp;·&nbsp; Llama 3.2 Local &nbsp;·&nbsp; ISO-45001
        </p>
        <!-- Stat chips -->
        <div style="display:flex; gap:.6rem; margin-top:.8rem; flex-wrap:wrap;">
          <span style="background:rgba(34,211,238,.08); border:1px solid rgba(34,211,238,.2);
            border-radius:8px; padding:.3rem .75rem; font-size:.76rem; color:#22d3ee;
            font-family:'JetBrains Mono',monospace; font-weight:600;">
            {n} nodes
          </span>
          <span style="background:rgba(129,140,248,.08); border:1px solid rgba(129,140,248,.2);
            border-radius:8px; padding:.3rem .75rem; font-size:.76rem; color:#818cf8;
            font-family:'JetBrains Mono',monospace; font-weight:600;">
            {e} edges
          </span>
          <span style="background:rgba(52,211,153,.06); border:1px solid rgba(52,211,153,.15);
            border-radius:8px; padding:.3rem .75rem; font-size:.76rem; color:#34d399;">
            NetworkX + PyVis
          </span>
        </div>
      </div>

      <!-- Time -->
      <div style="flex-shrink:0; text-align:right; color:var(--txt3); font-size:.72rem;
        font-family:'JetBrains Mono',monospace; line-height:1.8;">
        {time.strftime("%H:%M")} <br>
        {time.strftime("%d %b %Y")}
      </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Brand
    st.markdown(f"""
    <div style="padding:1.5rem 1rem 1rem; text-align:center;">
      {siri_orb("idle" if not st.session_state.graph_loaded else "online", size=56)}
      <div style="margin-top:.8rem;">
        <div style="font-size:.95rem; font-weight:700; color:var(--txt); letter-spacing:.3px;">AI-HackerZ</div>
        <div style="font-size:.7rem; color:var(--txt3); margin-top:.15rem;">GraphRAG Control Panel</div>
      </div>
    </div>
    <div style="height:1px; background:var(--border); margin:0 .5rem .8rem;"></div>
    """, unsafe_allow_html=True)

    # Graph init
    if not st.session_state.graph_loaded:
        if st.button("⚡  Initialize Graph Engine", use_container_width=True):
            prog = st.progress(0, text="Parsing data contract…")
            time.sleep(.3); prog.progress(35, text="Building NetworkX graph…")
            time.sleep(.3); prog.progress(70, text="Calibrating search engine…")
            result = load_graph_resources(str(GRAPH_JSON), str(GRAPH_ML))
            prog.progress(100, text="Done!")
            time.sleep(.2); prog.empty()
            if len(result) == 4:
                builder, engine, err, stats = result
            else:
                builder, engine, err = result; stats = {}
            if err and not builder:
                st.error(err)
            else:
                st.session_state.update({
                    "builder": builder, "engine": engine,
                    "graph_loaded": True, "graph_stats": stats or {},
                })
                activity_log("Graph engine initialised",
                             f"{stats.get('total_nodes',0)} nodes", "⚡")
                if err: st.warning(err)
                st.rerun()
    else:
        st.markdown("""
        <div style="text-align:center; padding:.4rem;
          background:rgba(52,211,153,.07); border:1px solid rgba(52,211,153,.2);
          border-radius:10px; font-size:.8rem; color:#34d399; font-weight:600;
          margin-bottom:.4rem;">
          ✓ &nbsp;Graph Engine Active
        </div>
        """, unsafe_allow_html=True)
        if st.button("↺  Reload Graph", use_container_width=True):
            load_graph_resources.clear()
            for k in ["graph_loaded","builder","engine","graph_stats","selected_node"]:
                st.session_state[k] = False if k == "graph_loaded" else None
            st.rerun()

    st.markdown("<div style='height:1px;background:var(--border);margin:.8rem 0;'></div>", unsafe_allow_html=True)

    # Stats
    stats = st.session_state.graph_stats or {}
    if stats:
        c1, c2 = st.columns(2)
        c1.metric("Nodes", stats.get("total_nodes", 0))
        c2.metric("Edges", stats.get("total_edges", 0))
        st.markdown(f"""
        <div style="font-size:.74rem; color:var(--txt3); line-height:2.1; margin-top:.3rem; padding:0 .2rem;">
          <div>Directed &nbsp;<span style="color:var(--cyan);">{'Yes' if stats.get('is_directed') else 'No'}</span></div>
          <div>Connected &nbsp;<span style="color:{'#34d399' if stats.get('is_connected') else '#fb7185'};">{'Yes' if stats.get('is_connected') else 'No'}</span></div>
          <div>Avg degree &nbsp;<span style="color:var(--violet);">{stats.get('average_out_degree',0):.2f}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:1px;background:var(--border);margin:.8rem 0;'></div>", unsafe_allow_html=True)

    # Risk leaderboard
    if st.session_state.graph_loaded and st.session_state.builder:
        _b = st.session_state.builder
        risk_scores = {}
        for _nid in _b.get_all_node_ids():
            _info = _b.get_node_info(_nid)
            if _info and _info.get("entity_type") == "EQUIPMENT":
                _h = sum(1 for src,_,d in _b.graph.in_edges(_nid,data=True)
                         if _b.get_node_info(src) and _b.get_node_info(src).get("entity_type")=="HAZARD")
                _s = sum(1 for src,_,d in _b.graph.in_edges(_nid,data=True)
                         if _b.get_node_info(src) and _b.get_node_info(src).get("entity_type")=="SENSOR")
                risk_scores[_nid] = _h*40 + _s*15
        if risk_scores:
            st.markdown('<div style="font-size:.68rem; color:var(--txt3); letter-spacing:.7px; text-transform:uppercase; margin-bottom:.4rem;">⚠ Fault Risk</div>', unsafe_allow_html=True)
            for _nid, _score in sorted(risk_scores.items(), key=lambda x:x[1], reverse=True)[:5]:
                _color = "#fb7185" if _score>=50 else "#fbbf24" if _score>=20 else "#34d399"
                _pct = min(100, int(_score))
                st.markdown(f"""
                <div style="margin:.25rem 0;">
                  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:.2rem;">
                    <span style="font-size:.72rem; color:var(--txt2); font-family:'JetBrains Mono',monospace;">{_nid[:16]}</span>
                    <span style="font-size:.65rem; color:{_color}; font-weight:700;">{_score}</span>
                  </div>
                  <div style="height:2px; background:rgba(255,255,255,.06); border-radius:4px;">
                    <div style="width:{_pct}%; height:2px; background:{_color}; border-radius:4px;
                      box-shadow:0 0 6px {_color}88;"></div>
                  </div>
                </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1px;background:var(--border);margin:.8rem 0;'></div>", unsafe_allow_html=True)

    # Live upload
    with st.expander("📎 Live Document Ingest"):
        st.markdown("<p style='font-size:.76rem; color:var(--txt3);'>Drop a TXT/PDF — AI extracts & merges live.</p>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("File", type=["txt","pdf"], label_visibility="collapsed")
        if uploaded_file is not None:
            if st.button("🚀 Extract & Merge", use_container_width=True):
                raw_dir = DATA_DIR / "raw_documents"
                raw_dir.mkdir(exist_ok=True)
                tmp_path = raw_dir / uploaded_file.name
                with open(tmp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                with st.spinner(f"Extracting {uploaded_file.name}…"):
                    extractor = BatchExtractor(inputs_dir=str(raw_dir), output_dir=str(DATA_DIR))
                    success = extractor.process_single_file_and_merge(str(tmp_path), str(GRAPH_JSON))
                if success:
                    st.success("Merged into graph!")
                    activity_log(f"Doc ingested: {uploaded_file.name}", "", "📎")
                    load_graph_resources.clear()
                    for k in ["graph_loaded","builder","engine","graph_stats","selected_node"]:
                        st.session_state[k] = False if k=="graph_loaded" else None
                    st.rerun()
                else:
                    st.error("Extraction failed.")

    st.markdown("<div style='height:1px;background:var(--border);margin:.8rem 0;'></div>", unsafe_allow_html=True)

    # Activity feed
    feed = st.session_state.get("activity_feed", [])
    if feed:
        st.markdown('<div style="font-size:.68rem; color:var(--txt3); letter-spacing:.7px; text-transform:uppercase; margin-bottom:.4rem;">◈ Live Activity</div>', unsafe_allow_html=True)
        for entry in feed[:6]:
            st.markdown(f"""
            <div style="display:flex; gap:.5rem; padding:.35rem 0;
              border-bottom:1px solid rgba(255,255,255,.04);">
              <span style="font-size:.8rem; color:var(--cyan); flex-shrink:0;">{entry['icon']}</span>
              <div style="min-width:0;">
                <div style="font-size:.73rem; color:var(--txt2); white-space:nowrap;
                  overflow:hidden; text-overflow:ellipsis;">{entry['action']}</div>
                <div style="font-size:.65rem; color:var(--txt3);">{entry['ts']}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1px;background:var(--border);margin:.8rem 0;'></div>", unsafe_allow_html=True)

    # Filter
    st.markdown('<div style="font-size:.68rem; color:var(--txt3); letter-spacing:.7px; text-transform:uppercase; margin-bottom:.4rem;">Filter Nodes</div>', unsafe_allow_html=True)
    filter_type = st.selectbox("Filter", ["ALL","EQUIPMENT","SENSOR","PROCEDURE","HAZARD","COMPLIANCE_STANDARD"], label_visibility="collapsed")
    st.session_state.filter_type = filter_type


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════
render_hero(st.session_state.graph_stats or {})

if not st.session_state.graph_loaded:
    st.markdown("""
    <div class="fade-up" style="
      text-align:center; padding:5rem 2rem;
      background:rgba(255,255,255,.02); border:1px solid var(--border);
      border-radius:24px; margin-top:.5rem;
      backdrop-filter:blur(40px);
    ">
      <div style="font-size:4rem; margin-bottom:1rem; opacity:.6; filter:grayscale(1);">🧠</div>
      <h2 style="color:var(--txt); margin:0 0 .6rem; font-weight:600; font-size:1.4rem;">
        Graph Engine Not Loaded
      </h2>
      <p style="color:var(--txt3); font-size:.88rem; max-width:360px; margin:0 auto; line-height:1.6;">
        Hit <strong style="color:var(--cyan);">⚡ Initialize Graph Engine</strong> in the sidebar to
        build the knowledge graph from your data contract.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

builder: GraphRAGBuilder    = st.session_state.builder
engine:  GraphSearchEngine  = st.session_state.engine

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_graph, tab_query, tab_explorer, tab_risk, tab_contract = st.tabs([
    "  📊  Graph  ",
    "  🤖  AI Chat  ",
    "  🔍  Explorer  ",
    "  ⚠️  Risk  ",
    "  📋  Contract  ",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1  —  Knowledge Graph
# ══════════════════════════════════════════════════════════════════════════════
with tab_graph:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:.6rem; margin-bottom:1rem;">
      <span style="font-size:1.1rem;">📊</span>
      <div>
        <div style="font-size:1rem; font-weight:600; color:var(--txt);">Live Knowledge Graph</div>
        <div style="font-size:.76rem; color:var(--txt3);">Click any node to inspect · Drag to explore</div>
      </div>
    </div>""", unsafe_allow_html=True)

    try:
        from pyvis.network import Network
        import streamlit.components.v1 as components

        ft = st.session_state.filter_type
        all_ids = builder.get_all_node_ids()

        net = Network(height="600px", width="100%", bgcolor="#050508", font_color="#ffffff", directed=True)
        net.set_options("""{
          "nodes": {
            "shape": "dot", "size": 22,
            "font": { "size": 12, "face": "JetBrains Mono", "color": "rgba(255,255,255,.85)" },
            "borderWidth": 1.5, "borderWidthSelected": 3,
            "shadow": { "enabled": true, "size": 18 }
          },
          "edges": {
            "arrows": { "to": { "enabled": true, "scaleFactor": 0.6 } },
            "color": { "color": "rgba(255,255,255,.18)", "highlight": "#22d3ee", "opacity": 1 },
            "font": { "size": 9, "color": "rgba(255,255,255,.35)", "strokeWidth": 0, "face": "Inter" },
            "width": 1.2,
            "smooth": { "type": "curvedCW", "roundness": 0.2 },
            "shadow": { "enabled": true, "color": "rgba(34,211,238,.15)", "size": 6 }
          },
          "physics": {
            "enabled": true,
            "barnesHut": { "gravitationalConstant": -9500, "centralGravity": 0.28,
              "springLength": 175, "springConstant": 0.035, "damping": 0.09 },
            "stabilization": { "iterations": 300 }
          },
          "interaction": { "hover": true, "tooltipDelay": 80, "keyboard": true, "zoomView": true }
        }""")

        CMAP = { "EQUIPMENT":"#22d3ee","SENSOR":"#818cf8","PROCEDURE":"#34d399",
                 "HAZARD":"#fb7185","COMPLIANCE_STANDARD":"#fbbf24","UNKNOWN":"#6b7280" }

        for nid in all_ids:
            info  = builder.get_node_info(nid)
            etype = info.get("entity_type","UNKNOWN") if info else "UNKNOWN"
            desc  = info.get("description","") if info else ""
            if ft != "ALL" and etype != ft: continue
            c    = CMAP.get(etype,"#6b7280")
            size = 28 if etype=="EQUIPMENT" else 22 if etype in ("SENSOR","HAZARD") else 18
            net.add_node(nid, label=nid, size=size, title=f"<b style='color:{c}'>{nid}</b><br><em style='color:#8888aa'>{etype}</em><br>{desc}",
                         color={"background":c,"border":c,"highlight":{"background":c,"border":"#ffffff"}})

        added = set(net.get_nodes())
        for u,v,data in builder.graph.edges(data=True):
            if u not in added or v not in added: continue
            net.add_edge(u,v, label=data.get("relation_type",""), title=data.get("context",""))

        html_path = "/tmp/kg_viz.html"
        net.save_graph(html_path)
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Dark background + click bridge
        inject = """
<style>
  html,body{background:#050508!important;margin:0;padding:0;}
  #mynetwork{background:#050508!important;border:none!important;}
  canvas{background:#050508!important;}
</style>
<script>
function bridge(){
  if(typeof network!=='undefined'){
    network.on("click",function(p){
      if(p.nodes.length){
        var id=p.nodes[0];
        network.selectNodes([id]);
        try{window.parent.sessionStorage.setItem('__pyvis_clicked__',id);}catch(e){}
      }
    });
    network.on("hoverNode",function(){document.body.style.cursor='pointer';});
    network.on("blurNode",function(){document.body.style.cursor='default';});
    network.once("stabilizationIterationsDone",function(){network.setOptions({physics:{enabled:false}});});
  } else { setTimeout(bridge,200); }
}
bridge();
</script>"""
        html = html.replace("</body>", inject + "</body>")
        components.html(html, height=615, scrolling=False)

        # Polling bridge
        components.html("""<script>
(function(){
  function poll(){
    try{
      var id=window.parent.sessionStorage.getItem('__pyvis_clicked__');
      if(id){
        window.parent.sessionStorage.removeItem('__pyvis_clicked__');
        var url=new URL(window.parent.location.href);
        url.searchParams.set('node',id);
        window.parent.location.href=url.toString();
      }
    }catch(e){}
  }
  setInterval(poll,250);
})();
</script>""", height=0, scrolling=False)

        # Legend
        st.markdown("""
        <div style="display:flex; gap:.8rem; flex-wrap:wrap; margin-top:.6rem;
          padding:.6rem 1rem; background:rgba(255,255,255,.02);
          border:1px solid var(--border); border-radius:12px;">
          <span style="font-size:.74rem; color:#22d3ee;">● Equipment</span>
          <span style="font-size:.74rem; color:#818cf8;">● Sensor</span>
          <span style="font-size:.74rem; color:#34d399;">● Procedure</span>
          <span style="font-size:.74rem; color:#fb7185;">● Hazard</span>
          <span style="font-size:.74rem; color:#fbbf24;">● Compliance</span>
        </div>""", unsafe_allow_html=True)

    except ImportError:
        st.warning("⚠️ `pyvis` not installed. Run: `pip install pyvis`")

    # Node inspector
    st.markdown("<div style='height:1px;background:var(--border);margin:1.5rem 0;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex; align-items:center; gap:.6rem; margin-bottom:.8rem;">
      <span style="font-size:1rem;">🔎</span>
      <div style="font-size:.95rem; font-weight:600; color:var(--txt);">Node Inspector</div>
    </div>""", unsafe_allow_html=True)

    all_ids = builder.get_all_node_ids()
    preselect = st.session_state.get("selected_node","")
    opts = ["— choose a node —"] + all_ids
    default_idx = opts.index(preselect) if preselect in all_ids else 0
    selected = st.selectbox("", opts, index=default_idx, label_visibility="collapsed", key="node_inspector_select")

    if selected and selected != "— choose a node —":
        st.session_state["selected_node"] = selected
        activity_log(f"Inspected: {selected}", "", "🔎")
        with st.spinner("Fetching context…"):
            ctx = builder.extract_local_context(selected)
        if ctx:
            info  = builder.get_node_info(selected)
            etype = info.get("entity_type","UNKNOWN") if info else "UNKNOWN"
            desc  = info.get("description","") if info else ""
            in_d  = info.get("in_degree",0) if info else 0
            out_d = info.get("out_degree",0) if info else 0
            CMAP2 = {"EQUIPMENT":"#22d3ee","SENSOR":"#818cf8","PROCEDURE":"#34d399",
                     "HAZARD":"#fb7185","COMPLIANCE_STANDARD":"#fbbf24"}
            nc = CMAP2.get(etype,"#6b7280")
            c1,c2,c3 = st.columns(3)
            c1.metric("Type", etype); c2.metric("In-links",in_d); c3.metric("Out-links",out_d)
            st.markdown(f"""
            <div style="background:rgba(255,255,255,.02); border:1px solid {nc}28;
              border-left:3px solid {nc}; border-radius:14px; padding:1rem 1.3rem; margin:.8rem 0;">
              <div style="font-size:.68rem; color:var(--txt3); letter-spacing:.6px; margin-bottom:.4rem; text-transform:uppercase;">Description</div>
              <div style="color:var(--txt); font-size:.9rem; line-height:1.6;">{desc}</div>
            </div>""", unsafe_allow_html=True)
            with st.expander("View raw context →"):
                st.code(ctx, language="text")
        else:
            st.info("No context found for this node.")

    # Path finder
    st.markdown("<div style='height:1px;background:var(--border);margin:1.5rem 0;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex; align-items:center; gap:.6rem; margin-bottom:.8rem;">
      <span style="font-size:1rem;">🔗</span>
      <div style="font-size:.95rem; font-weight:600; color:var(--txt);">Relationship Path Finder</div>
    </div>""", unsafe_allow_html=True)

    if engine:
        pf1, pf2 = st.columns(2)
        src = pf1.selectbox("From", ["— source —"]+builder.get_all_node_ids(), key="pf_src")
        tgt = pf2.selectbox("To",   ["— target —"]+builder.get_all_node_ids(), key="pf_tgt")
        if st.button("Find Path →", key="find_path_btn"):
            if src.startswith("—") or tgt.startswith("—"): st.warning("Select both nodes.")
            elif src == tgt: st.info("Same node.")
            else:
                with st.spinner("Tracing path…"):
                    path = engine.find_path(src, tgt)
                if path:
                    activity_log(f"Path: {src}→{tgt}", f"{len(path)-1} hops","🔗")
                    st.success(f"✓ {len(path)-1} hop(s) found")
                    CMAP3 = {"EQUIPMENT":"#22d3ee","SENSOR":"#818cf8","PROCEDURE":"#34d399",
                             "HAZARD":"#fb7185","COMPLIANCE_STANDARD":"#fbbf24"}
                    hops = ""
                    for i, nid in enumerate(path):
                        inf = builder.get_node_info(nid)
                        c   = CMAP3.get(inf.get("entity_type","") if inf else "","#6b7280")
                        hops += f"""<span style="
                          background:rgba(255,255,255,.04); border:1px solid {c}44;
                          border-radius:10px; padding:.35rem .8rem;
                          color:{c}; font-family:'JetBrains Mono',monospace; font-size:.82rem;">
                          {nid}</span>"""
                        if i < len(path)-1:
                            rel = (builder.graph.get_edge_data(path[i],path[i+1]) or {}).get("relation_type","→")
                            hops += f"<span style='color:var(--txt3); margin:0 .4rem; font-size:.75rem;'>──[{rel}]──▶</span>"
                    st.markdown(f"<div style='display:flex;flex-wrap:wrap;gap:.4rem;align-items:center;margin:.8rem 0;'>{hops}</div>", unsafe_allow_html=True)
                    with st.expander("Full path context"):
                        st.code(engine.format_path_as_context(path), language="text")
                else:
                    st.error(f"No path found between {src} and {tgt}.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2  —  AI Chat  (ChatGPT-style)
# ══════════════════════════════════════════════════════════════════════════════
with tab_query:
    if engine is None:
        st.error("Search engine unavailable. Ensure graph is loaded.")
    else:
        # Dynamic quick queries
        all_equip   = [n for n in builder.get_all_node_ids() if builder.get_node_info(n) and builder.get_node_info(n).get("entity_type")=="EQUIPMENT"]
        all_hazards = [n for n in builder.get_all_node_ids() if builder.get_node_info(n) and builder.get_node_info(n).get("entity_type")=="HAZARD"]
        all_sensors = [n for n in builder.get_all_node_ids() if builder.get_node_info(n) and builder.get_node_info(n).get("entity_type")=="SENSOR"]
        qs = []
        if all_equip:   qs.append(f"What does {all_equip[0]} connect to?")
        if all_hazards: qs.append(f"How do we mitigate {all_hazards[0]}?")
        if all_sensors: qs.append(f"What does {all_sensors[0]} monitor?")
        qs += ["What hazards exist in the plant?","What safety standards govern operations?"]
        qs = qs[:4]

        # Handle prefilled query from JS bridge or quick queries
        prefill = st.session_state.pop("prefill_query", "")

        # Empty state
        if not st.session_state.chat_history:
            orb_html = siri_orb("idle", size=90)
            st.markdown(f"""
            <div class="fade-up" style="text-align:center; padding:4rem 1rem 2rem;">
              <div style="margin-bottom:1.5rem;">{orb_html}</div>
              <h2 style="color:var(--txt); font-weight:700; font-size:1.6rem; margin:0 0 .5rem; letter-spacing:-0.5px;">
                How can I help?
              </h2>
              <p style="color:var(--txt3); font-size:.9rem; max-width:380px; margin:0 auto 2rem; line-height:1.5;">
                Ask anything about your industrial knowledge graph. I'll search through entities and relationships instantly.
              </p>
            </div>""", unsafe_allow_html=True)

            # Sleek vertical list for quick queries
            st.markdown('<div class="fade-up" style="max-width:500px; margin:0 auto; display:flex; flex-direction:column; gap:0.6rem;">', unsafe_allow_html=True)
            for i, q in enumerate(qs):
                if st.button(f"✨ &nbsp; {q}", key=f"qs_{i}", use_container_width=True):
                    prefill = q
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # Show quick query row at top in a scrollable horizontal flexbox if needed, or just let them scroll away
            # Actually, if we are in chat history, we don't need to show them constantly, but we can put a "Clear Chat" button
            col1, col2 = st.columns([8,1])
            if col2.button("🗑️ Clear", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

            st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

            # Chat messages — Siri/ChatGPT translucent style
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="msg-user" style="
                      display:flex; justify-content:flex-end; margin:.8rem 0; gap:.8rem;
                    ">
                      <div style="
                        max-width:72%; background:rgba(255,255,255,.09);
                        border:1px solid rgba(255,255,255,.15);
                        border-radius:22px 22px 6px 22px;
                        padding:.9rem 1.2rem;
                        backdrop-filter:blur(30px);
                        box-shadow:0 8px 24px rgba(0,0,0,.2);
                      ">
                        <p style="margin:0; color:var(--txt); font-size:.95rem; line-height:1.55;">{msg['content']}</p>
                        <span style="font-size:.65rem; color:var(--txt3); margin-top:.4rem; display:block; text-align:right;">{msg.get('time','')}</span>
                      </div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="msg-ai" style="
                      display:flex; justify-content:flex-start; margin:.8rem 0; gap:.8rem;
                    ">
                      <div style="
                        width:38px; height:38px; border-radius:50%; flex-shrink:0;
                        background:radial-gradient(circle at 30% 30%, #818cf8, #22d3ee, #fb7185);
                        display:flex; align-items:center; justify-content:center; font-size:1.1rem;
                        box-shadow:0 0 16px rgba(34,211,238,.2);
                      ">✨</div>
                      <div style="
                        max-width:78%; background:rgba(255,255,255,.03);
                        border:1px solid rgba(255,255,255,.08);
                        border-radius:8px 22px 22px 22px;
                        padding:.9rem 1.2rem;
                        backdrop-filter:blur(30px);
                        box-shadow:0 8px 24px rgba(0,0,0,.2);
                      ">
                        <p style="margin:0; color:var(--txt); font-size:.95rem; line-height:1.7; white-space:pre-wrap;">{msg['content']}</p>
                        <span style="font-size:.65rem; color:var(--txt3); margin-top:.4rem; display:block;">{msg.get('time','')}</span>
                      </div>
                    </div>""", unsafe_allow_html=True)

            # Show context if present
            if st.session_state.chat_history:
                last = st.session_state.chat_history[-1]
                if last.get("role")=="assistant" and last.get("context"):
                    with st.expander("View retrieved graph context →"):
                        st.code(last["context"], language="text")

        st.markdown("<div style='height:8rem'></div>", unsafe_allow_html=True) # Spacer for bottom input

        # Apple Intelligence glowing chat input
        user_input = st.chat_input("Ask anything about your industrial graph…")
        
        # If prefill was triggered by a button or JS bridge, we execute it
        query_to_run = user_input or prefill

        if query_to_run:
            ts = time.strftime("%H:%M")
            st.session_state.chat_history.append({"role":"user","content":query_to_run,"time":ts})
            activity_log(f"Query: {query_to_run[:38]}","","💬")
            st.rerun() # Rerun immediately to show the user message

        # If the last message is from the user, we need to generate a response
        if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
            last_msg = st.session_state.chat_history[-1]["content"]
            with st.spinner("Thinking…"):
                try:
                    ctx, answer = engine.query(last_msg, top_k=5, context_depth=2)
                    st.session_state.chat_history.append({
                        "role":"assistant","content":answer,
                        "time":time.strftime("%H:%M"),"context":ctx
                    })
                except Exception as ex:
                    st.session_state.chat_history.append({
                        "role":"assistant",
                        "content":f"⚠️ {ex}\n\nEnsure Ollama is running: `ollama pull llama3.2`",
                        "time":time.strftime("%H:%M")
                    })
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3  —  Node Explorer
# ══════════════════════════════════════════════════════════════════════════════
with tab_explorer:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:.6rem; margin-bottom:.8rem;">
      <span>🔍</span>
      <div style="font-size:.95rem; font-weight:600; color:var(--txt);">Entity Explorer</div>
    </div>""", unsafe_allow_html=True)

    ft      = st.session_state.filter_type
    all_ids = builder.get_all_node_ids()
    search  = st.text_input("", placeholder="Search by node ID or keyword…", label_visibility="collapsed")

    CMAP_EX = {"EQUIPMENT":"#22d3ee","SENSOR":"#818cf8","PROCEDURE":"#34d399",
               "HAZARD":"#fb7185","COMPLIANCE_STANDARD":"#fbbf24"}

    filtered = []
    for nid in all_ids:
        info  = builder.get_node_info(nid)
        etype = info.get("entity_type","UNKNOWN") if info else "UNKNOWN"
        desc  = info.get("description","") if info else ""
        if ft!="ALL" and etype!=ft: continue
        if search and search.lower() not in nid.lower() and search.lower() not in desc.lower(): continue
        filtered.append((nid,etype,desc))

    if not filtered:
        st.info("No nodes match.")
    else:
        st.markdown(f'<p style="font-size:.76rem; color:var(--txt3); margin-bottom:.6rem;"><b style="color:var(--txt);">{len(filtered)}</b> entities found</p>', unsafe_allow_html=True)
        for nid,etype,desc in filtered:
            c = CMAP_EX.get(etype,"#6b7280")
            st.markdown(f"""
            <div style="
              background:rgba(255,255,255,.025);
              border:1px solid rgba(255,255,255,.06);
              border-left:3px solid {c};
              border-radius:12px; padding:.75rem 1rem; margin:.3rem 0;
              transition:border-color .2s;
            " onmouseover="this.style.borderColor='{c}66'"
               onmouseout="this.style.borderColor='rgba(255,255,255,.06)'">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="color:{c}; font-family:'JetBrains Mono',monospace; font-weight:600; font-size:.88rem;">{nid}</span>
                <span style="color:{c}; font-size:.66rem; background:{c}14; border:1px solid {c}28;
                  border-radius:999px; padding:.1rem .6rem; letter-spacing:.4px;">{etype}</span>
              </div>
              <p style="color:rgba(255,255,255,.45); font-size:.78rem; margin:.25rem 0 0; line-height:1.4;">{desc}</p>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:1px;background:var(--border);margin:1rem 0;'></div>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:.95rem; font-weight:600; color:var(--txt); margin-bottom:.6rem;">📌 Relationship Map</div>', unsafe_allow_html=True)
        pick = st.selectbox("", ["— pick a node —"]+[n for n,*_ in filtered], label_visibility="collapsed")
        if pick and not pick.startswith("—"):
            ctx = builder.extract_local_context(pick)
            if ctx: st.code(ctx, language="text")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4  —  Risk Analysis (with SVG gauge dials)
# ══════════════════════════════════════════════════════════════════════════════
with tab_risk:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:.6rem; margin-bottom:.8rem;">
      <span>⚠️</span>
      <div>
        <div style="font-size:.95rem; font-weight:600; color:var(--txt);">Fault Risk Analysis</div>
        <div style="font-size:.76rem; color:var(--txt3);">Automated scoring based on graph topology</div>
      </div>
    </div>""", unsafe_allow_html=True)

    risk_data = []
    for nid in builder.get_all_node_ids():
        info = builder.get_node_info(nid)
        if not info or info.get("entity_type")!="EQUIPMENT": continue
        hazards = [(s,d) for s,_,d in builder.graph.in_edges(nid,data=True)
                   if builder.get_node_info(s) and builder.get_node_info(s).get("entity_type")=="HAZARD"]
        sensors = [(s,d) for s,_,d in builder.graph.in_edges(nid,data=True)
                   if builder.get_node_info(s) and builder.get_node_info(s).get("entity_type")=="SENSOR"]
        procs   = [(t,d) for _,t,d in builder.graph.out_edges(nid,data=True)
                   if builder.get_node_info(t) and builder.get_node_info(t).get("entity_type")=="PROCEDURE"]
        redund  = any(d.get("relation_type")=="HAS_REDUNDANCY" for _,_,d in builder.graph.out_edges(nid,data=True))
        score   = len(hazards)*40 + (max(0,2-len(sensors))*15) + (0 if procs else 25) + (0 if redund else 10)
        risk_data.append({"id":nid,"desc":info.get("description",""),"hazards":len(hazards),
                          "sensors":len(sensors),"procs":len(procs),"redund":redund,"score":score})
    risk_data.sort(key=lambda x:x["score"],reverse=True)

    if not risk_data:
        st.info("No EQUIPMENT nodes in graph.")
    else:
        st.markdown(f'<p style="font-size:.78rem; color:var(--txt3); margin-bottom:.8rem;">Analysed <b style="color:var(--txt);">{len(risk_data)}</b> equipment nodes</p>', unsafe_allow_html=True)
        for rd in risk_data:
            sc    = rd["score"]
            color = "#fb7185" if sc>=50 else "#fbbf24" if sc>=20 else "#34d399"
            label = "HIGH" if sc>=50 else "MED" if sc>=20 else "LOW"
            bar   = min(100, sc)
            # SVG gauge
            r,circ = 32, 125
            off    = circ*(1-min(sc,100)/100)
            gauge  = f"""
            <svg width="80" height="50" viewBox="0 0 80 50" style="overflow:visible; flex-shrink:0;">
              <path d="M 10 45 A 30 30 0 0 1 70 45" fill="none"
                stroke="rgba(255,255,255,.06)" stroke-width="7" stroke-linecap="round"/>
              <path d="M 10 45 A 30 30 0 0 1 70 45" fill="none"
                stroke="{color}" stroke-width="7" stroke-linecap="round"
                stroke-dasharray="{circ}" stroke-dashoffset="{off:.1f}"
                style="animation:gauge-fill 1s cubic-bezier(.4,0,.2,1) both;
                       filter:drop-shadow(0 0 6px {color})"/>
              <text x="40" y="40" text-anchor="middle" font-size="12" font-weight="700"
                font-family="JetBrains Mono,monospace" fill="{color}">{sc}</text>
            </svg>"""

            st.markdown(f"""
            <div style="
              background:rgba(255,255,255,.02); border:1px solid rgba(255,255,255,.06);
              border-left:3px solid {color}; border-radius:16px;
              padding:1rem 1.2rem; margin:.5rem 0;
              display:flex; align-items:center; gap:1rem;
              transition:border-color .2s, box-shadow .2s;
            " onmouseover="this.style.boxShadow='0 0 30px {color}18'"
               onmouseout="this.style.boxShadow='none'">
              <div style="flex:1; min-width:0;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:.4rem;">
                  <span style="color:{color}; font-family:'JetBrains Mono',monospace; font-weight:700; font-size:.95rem;">{rd['id']}</span>
                  <span style="color:{color}; font-size:.72rem; font-weight:700; background:{color}14;
                    border:1px solid {color}28; border-radius:999px; padding:.15rem .65rem;">{label} RISK</span>
                </div>
                <div style="height:3px; background:rgba(255,255,255,.06); border-radius:4px; margin-bottom:.6rem;">
                  <div style="width:{bar}%; height:3px; background:linear-gradient(90deg,{color}88,{color});
                    border-radius:4px; box-shadow:0 0 8px {color}66;"></div>
                </div>
                <p style="color:rgba(255,255,255,.4); font-size:.78rem; margin:0 0 .5rem; line-height:1.4;">{rd['desc'][:120]}</p>
                <div style="display:flex; gap:1.2rem; font-size:.74rem; color:rgba(255,255,255,.35); flex-wrap:wrap;">
                  <span>⚡ Hazards <b style="color:{color};">{rd['hazards']}</b></span>
                  <span>📡 Sensors <b style="color:#818cf8;">{rd['sensors']}</b></span>
                  <span>📋 ESD <b style="color:#34d399;">{rd['procs']}</b></span>
                  <span>♻️ Redundancy <b style="color:{'#34d399' if rd['redund'] else '#fb7185'};">{'Yes' if rd['redund'] else 'No'}</b></span>
                </div>
              </div>
              {gauge}
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-top:1.2rem; background:rgba(255,255,255,.02); border:1px solid var(--border);
          border-radius:12px; padding:.8rem 1.1rem;">
          <div style="font-size:.68rem; color:var(--txt3); letter-spacing:.6px; text-transform:uppercase; margin-bottom:.3rem;">Scoring Formula</div>
          <code style="color:#22d3ee; font-size:.8rem;">Score = (Hazards×40) + (Missing sensors×15) + (No ESD×25) + (No redundancy×10)</code>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5  —  Data Contract
# ══════════════════════════════════════════════════════════════════════════════
with tab_contract:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:.6rem; margin-bottom:.8rem;">
      <span>📋</span>
      <div style="font-size:.95rem; font-weight:600; color:var(--txt);">Raw Data Contract</div>
    </div>""", unsafe_allow_html=True)
    try:
        with open(GRAPH_JSON,"r",encoding="utf-8") as f:
            raw = json.load(f)
        c1,c2,c3 = st.columns(3)
        c1.metric("Document ID",   raw.get("document_id","N/A"))
        c2.metric("Entities",      len(raw.get("entities",[])))
        c3.metric("Relationships", len(raw.get("relationships",[])))
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        st.json(raw)
    except FileNotFoundError:
        st.error(f"Contract not found at `{GRAPH_JSON}`.")
    except Exception as ex:
        st.error(f"Error: {ex}")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:1.5rem; margin-top:2rem;
  border-top:1px solid var(--border); font-size:.72rem; color:var(--txt3);">
  AI-HackerZ &nbsp;·&nbsp; ET AI Hackathon 2026 &nbsp;·&nbsp; Problem Statement 8 &nbsp;·&nbsp;
  <span style="color:var(--cyan);">100% Offline · Edge Computing · GraphRAG</span>
</div>
""", unsafe_allow_html=True)
