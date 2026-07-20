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
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR   = ROOT / "data"
GRAPH_JSON = DATA_DIR / "graph_input.json"
GRAPH_ML   = DATA_DIR / "graph.graphml"
KG_DIR     = ROOT / "2_knowledge_graph"
VIS_DIR    = ROOT / "1_vision_extraction"

for p in (str(KG_DIR), str(VIS_DIR), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from graph_builder import GraphRAGBuilder
from graph_search  import GraphSearchEngine
from batch_extractor import BatchExtractor

# ── Read clicked node from URL query params (JS bridge) ──────────────────────
_qp_node = st.query_params.get("node", "")
if _qp_node and _qp_node != st.session_state.get("selected_node", ""):
    st.session_state["selected_node"] = _qp_node
    st.session_state["prefill_query"] = f"Tell me everything about {_qp_node}."

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI-HackerZ | Industrial GraphRAG",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS — Premium dark theme with glassmorphism + neural bg animation
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
  /* ── Fonts ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

  /* ── Root palette ── */
  :root {
    --bg-base:      #080810;
    --bg-card:      #0f0f1a;
    --bg-surface:   #161625;
    --bg-glass:     rgba(15,15,26,0.7);
    --accent:       #00e5ff;
    --accent-dim:   #00b8cc;
    --accent-glow:  rgba(0,229,255,.18);
    --accent-pulse: rgba(0,229,255,.35);
    --warn:         #ff6b35;
    --success:      #39ff14;
    --purple:       #a78bfa;
    --gold:         #f59e0b;
    --text-pri:     #f0f0f8;
    --text-sec:     #6b7280;
    --border:       rgba(0,229,255,.12);
    --border-hover: rgba(0,229,255,.3);
  }

  /* ── Neural background canvas ── */
  html, body { background: var(--bg-base) !important; }
  .stApp {
    background: transparent !important;
    position: relative;
  }
  #neural-bg {
    position: fixed; top: 0; left: 0;
    width: 100vw; height: 100vh;
    z-index: 0; pointer-events: none;
    opacity: 0.35;
  }
  .main .block-container {
    position: relative; z-index: 1;
    padding: 1.5rem 2rem 2rem;
    max-width: 100%;
  }

  /* ── Base typography ── */
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  h1, h2, h3, h4 { color: var(--text-pri) !important; letter-spacing: -.3px; }

  /* ── Custom scrollbar ── */
  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg-base); }
  ::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, var(--accent), var(--accent-dim));
    border-radius: 4px;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b0b18 0%, #0f0f1a 100%) !important;
    border-right: 1px solid var(--border) !important;
    backdrop-filter: blur(20px);
  }
  [data-testid="stSidebar"] * { color: var(--text-pri) !important; }

  /* ── Glass cards ── */
  .glass-card {
    background: var(--bg-glass);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border);
    border-radius: 16px;
    transition: border-color .3s ease, box-shadow .3s ease;
  }
  .glass-card:hover {
    border-color: var(--border-hover);
    box-shadow: 0 0 30px var(--accent-glow);
  }

  /* ── Metric cards ── */
  [data-testid="metric-container"] {
    background: var(--bg-glass) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    padding: .8rem 1rem !important;
    transition: all .3s ease !important;
  }
  [data-testid="metric-container"]:hover {
    border-color: var(--border-hover) !important;
    box-shadow: 0 0 20px var(--accent-glow) !important;
  }
  [data-testid="stMetricValue"] {
    color: var(--accent) !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    font-family: 'JetBrains Mono', monospace !important;
  }
  [data-testid="stMetricLabel"] { color: var(--text-sec) !important; font-size: .75rem !important; letter-spacing: .5px; }

  /* ── Buttons ── */
  .stButton > button {
    background: transparent !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: .85rem !important;
    transition: all .25s ease !important;
    position: relative !important;
    overflow: hidden !important;
  }
  .stButton > button::before {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(135deg, var(--accent-glow), transparent);
    opacity: 0;
    transition: opacity .25s ease;
  }
  .stButton > button:hover::before { opacity: 1 !important; }
  .stButton > button:hover {
    box-shadow: 0 0 22px var(--accent-pulse) !important;
    transform: translateY(-2px) !important;
  }
  .stButton > button:active { transform: translateY(0px) !important; }

  /* ── Primary action button ── */
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, rgba(0,229,255,.2), rgba(0,229,255,.05)) !important;
    box-shadow: 0 0 15px var(--accent-glow) !important;
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
    transition: border-color .2s, box-shadow .2s !important;
  }
  .stTextInput > div > div > input:focus,
  .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
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
    background: var(--bg-glass) !important;
    backdrop-filter: blur(12px) !important;
    border-radius: 14px 14px 0 0 !important;
    gap: 2px !important;
    padding: 5px !important;
    border-bottom: 1px solid var(--border) !important;
  }
  .stTabs [data-baseweb="tab"] {
    color: var(--text-sec) !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: .87rem !important;
    padding: .5rem 1.1rem !important;
    transition: all .2s ease !important;
  }
  .stTabs [data-baseweb="tab"]:hover {
    color: var(--text-pri) !important;
    background: rgba(0,229,255,.06) !important;
  }
  .stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0,229,255,.18), rgba(0,229,255,.06)) !important;
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    box-shadow: 0 0 12px var(--accent-glow) !important;
  }
  .stTabs [data-baseweb="tab-panel"] {
    background: var(--bg-glass) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 14px 14px !important;
    padding: 1.4rem !important;
  }

  /* ── Expanders ── */
  .streamlit-expanderHeader {
    background: var(--bg-glass) !important;
    backdrop-filter: blur(12px) !important;
    color: var(--text-pri) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    transition: border-color .2s !important;
  }
  .streamlit-expanderHeader:hover { border-color: var(--border-hover) !important; }
  .streamlit-expanderContent {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
  }

  /* ── Alerts ── */
  .stAlert { border-radius: 10px !important; }
  .stSuccess { background: rgba(57,255,20,.07) !important; border: 1px solid #39ff1444 !important; }
  .stWarning { background: rgba(255,107,53,.07) !important; border: 1px solid #ff6b3544 !important; }
  .stError   { background: rgba(255,50,80,.07) !important; border: 1px solid #ff335044 !important; }
  .stInfo    { background: var(--accent-glow) !important; border: 1px solid var(--border) !important; }

  /* ── Spinner ── */
  .stSpinner > div { border-top-color: var(--accent) !important; }

  /* ── Divider ── */
  hr { border-color: var(--border) !important; }

  /* ── Code blocks (terminal style) ── */
  .stCode, .stCodeBlock, pre, code {
    background: #010108 !important;
    border: 1px solid rgba(0,229,255,.15) !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    color: #39ff14 !important;
  }

  /* ── Typing cursor animation ── */
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
  .typing-cursor { display: inline-block; animation: blink 1s step-start infinite; }

  /* ── Animated stat counter ── */
  @keyframes countUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  [data-testid="stMetricValue"] { animation: countUp .6s ease-out both; }

  /* ── Glow pulse on ONLINE badge ── */
  @keyframes pulse-glow {
    0%,100% { box-shadow: 0 0 6px var(--success); }
    50%      { box-shadow: 0 0 18px var(--success), 0 0 30px rgba(57,255,20,.3); }
  }
  .status-online { animation: pulse-glow 2.5s ease-in-out infinite; }

  /* ── Gauge animation ── */
  @keyframes sweepIn {
    from { stroke-dashoffset: 251; }
  }
  .gauge-arc { animation: sweepIn 1.2s cubic-bezier(.4,0,.2,1) both; }

  /* ── Activity feed entry ── */
  @keyframes slideIn {
    from { opacity: 0; transform: translateX(-12px); }
    to   { opacity: 1; transform: translateX(0); }
  }
  .activity-entry { animation: slideIn .35s ease both; }

  /* ── Hop chain items ── */
  .hop-node {
    transition: transform .2s, box-shadow .2s;
  }
  .hop-node:hover {
    transform: scale(1.04);
    box-shadow: 0 0 16px var(--accent-glow);
  }
</style>

<!-- Neural network background canvas -->
<canvas id="neural-bg"></canvas>
<script>
(function(){
  var canvas = document.getElementById('neural-bg');
  if(!canvas) return;
  var ctx = canvas.getContext('2d');
  var W = canvas.width  = window.innerWidth;
  var H = canvas.height = window.innerHeight;
  window.addEventListener('resize', function(){
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  });

  var NODES = 55, nodes = [], CONN_DIST = 140;
  for(var i=0;i<NODES;i++){
    nodes.push({
      x: Math.random()*W, y: Math.random()*H,
      vx: (Math.random()-.5)*.35, vy: (Math.random()-.5)*.35,
      r: Math.random()*2+1
    });
  }

  function draw(){
    ctx.clearRect(0,0,W,H);
    // update
    nodes.forEach(function(n){
      n.x+=n.vx; n.y+=n.vy;
      if(n.x<0||n.x>W) n.vx*=-1;
      if(n.y<0||n.y>H) n.vy*=-1;
    });
    // edges
    for(var i=0;i<nodes.length;i++){
      for(var j=i+1;j<nodes.length;j++){
        var dx=nodes[i].x-nodes[j].x, dy=nodes[i].y-nodes[j].y;
        var dist=Math.sqrt(dx*dx+dy*dy);
        if(dist<CONN_DIST){
          ctx.beginPath();
          ctx.moveTo(nodes[i].x,nodes[i].y);
          ctx.lineTo(nodes[j].x,nodes[j].y);
          ctx.strokeStyle='rgba(0,229,255,'+(0.18*(1-dist/CONN_DIST)).toFixed(3)+')';
          ctx.lineWidth=0.6;
          ctx.stroke();
        }
      }
    }
    // dots
    nodes.forEach(function(n){
      ctx.beginPath();
      ctx.arc(n.x,n.y,n.r,0,Math.PI*2);
      ctx.fillStyle='rgba(0,229,255,0.55)';
      ctx.fill();
    });
    requestAnimationFrame(draw);
  }
  draw();
})();
</script>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HELPER COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════
def hero_banner(stats: dict):
    node_count = stats.get("total_nodes", "—")
    edge_count = stats.get("total_edges", "—")
    graph_active = stats.get("total_nodes", 0) > 0
    status_color = "#39ff14" if graph_active else "#ff6b35"
    status_label = "GRAPH ONLINE" if graph_active else "AWAITING INIT"
    status_class = "status-online" if graph_active else ""
    ts = time.strftime("%H:%M:%S")
    st.markdown(f"""
    <div style="
      background: linear-gradient(135deg, #080810 0%, #0f0f1a 50%, #080d14 100%);
      border: 1px solid rgba(0,229,255,.2);
      border-radius: 20px;
      padding: 1.8rem 2.2rem;
      margin-bottom: 1.4rem;
      position: relative;
      overflow: hidden;
    ">
      <!-- Radial glow accent -->
      <div style="position:absolute; top:-40px; right:-40px; width:280px; height:280px;
        background:radial-gradient(ellipse, rgba(0,229,255,.08) 0%, transparent 70%);
        pointer-events:none;"></div>
      <div style="position:absolute; bottom:-60px; left:20%; width:200px; height:200px;
        background:radial-gradient(ellipse, rgba(167,139,250,.05) 0%, transparent 70%);
        pointer-events:none;"></div>

      <!-- Top row -->
      <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem;">
        <div style="display:flex; align-items:center; gap:1rem;">
          <div style="
            background: rgba(0,229,255,.1);
            border: 1px solid rgba(0,229,255,.25);
            border-radius: 14px; padding: .6rem 1rem; font-size:1.8rem;
            box-shadow: 0 0 20px rgba(0,229,255,.15);
          ">⚙️</div>
          <div>
            <h1 style="margin:0; font-size:1.65rem; font-weight:800; line-height:1.1;
                       background:linear-gradient(90deg,#00e5ff 0%,#a78bfa 60%,#ffffff 100%);
                       -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
              Industrial GraphRAG Brain
            </h1>
            <p style="margin:.3rem 0 0; color:#6b7280; font-size:.8rem; letter-spacing:.4px;">
              Edge Computing · 100% Offline · Zero Cloud Dependency
            </p>
          </div>
        </div>
        <!-- Live status badge -->
        <div style="display:flex; align-items:center; gap:.5rem;
                    background:rgba(0,0,0,.3); border:1px solid {status_color}44;
                    border-radius:10px; padding:.45rem .9rem;" class="{status_class}">
          <span style="width:8px; height:8px; border-radius:50%;
                       background:{status_color}; display:inline-block;"></span>
          <span style="color:{status_color}; font-size:.75rem; font-weight:700;
                       font-family:'JetBrains Mono',monospace; letter-spacing:.5px;">{status_label}</span>
        </div>
      </div>

      <!-- Stats row -->
      <div style="display:flex; gap:1.5rem; margin-top:1.2rem; flex-wrap:wrap;">
        <div style="background:rgba(0,229,255,.07); border:1px solid rgba(0,229,255,.15);
                    border-radius:10px; padding:.4rem .9rem;">
          <span style="color:#6b7280; font-size:.7rem; letter-spacing:.4px;">NODES</span>
          <span style="color:#00e5ff; font-size:1rem; font-weight:700;
                       font-family:'JetBrains Mono',monospace; margin-left:.5rem;">{node_count}</span>
        </div>
        <div style="background:rgba(167,139,250,.07); border:1px solid rgba(167,139,250,.15);
                    border-radius:10px; padding:.4rem .9rem;">
          <span style="color:#6b7280; font-size:.7rem; letter-spacing:.4px;">EDGES</span>
          <span style="color:#a78bfa; font-size:1rem; font-weight:700;
                       font-family:'JetBrains Mono',monospace; margin-left:.5rem;">{edge_count}</span>
        </div>
        <div style="background:rgba(57,255,20,.05); border:1px solid rgba(57,255,20,.12);
                    border-radius:10px; padding:.4rem .9rem;">
          <span style="color:#6b7280; font-size:.7rem; letter-spacing:.4px;">LLM</span>
          <span style="color:#39ff14; font-size:.8rem; font-weight:600; margin-left:.5rem;">Llama 3.2 Local</span>
        </div>
        <div style="background:rgba(245,158,11,.05); border:1px solid rgba(245,158,11,.12);
                    border-radius:10px; padding:.4rem .9rem;">
          <span style="color:#6b7280; font-size:.7rem; letter-spacing:.4px;">ISO</span>
          <span style="color:#f59e0b; font-size:.8rem; font-weight:600; margin-left:.5rem;">45001 Compliant</span>
        </div>
        <div style="margin-left:auto; color:#6b7280; font-size:.72rem;
                    font-family:'JetBrains Mono',monospace; align-self:center;">
          ⏱ {ts}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def gauge_svg(score: int, color: str, size: int = 80) -> str:
    """Render an animated SVG arc gauge for a risk score 0-100."""
    radius = 34
    circumference = 2 * 3.14159 * radius * 0.65   # 65% of circle = arc
    offset = circumference * (1 - min(score, 100) / 100)
    return f"""
    <svg width="{size}" height="{size//2 + 10}" viewBox="0 0 80 50" style="overflow:visible;">
      <!-- Track -->
      <path d="M 10 45 A 30 30 0 0 1 70 45"
            fill="none" stroke="rgba(255,255,255,.08)" stroke-width="7" stroke-linecap="round"/>
      <!-- Arc -->
      <path d="M 10 45 A 30 30 0 0 1 70 45"
            fill="none" stroke="{color}" stroke-width="7" stroke-linecap="round"
            stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{offset:.1f}"
            class="gauge-arc"
            style="filter: drop-shadow(0 0 6px {color});"/>
      <!-- Score text -->
      <text x="40" y="40" text-anchor="middle" font-size="13" font-weight="700"
            font-family="JetBrains Mono, monospace" fill="{color}">{score}</text>
    </svg>"""


def node_badge(node_id: str, entity_type: str, description: str):
    color_map = {
        "EQUIPMENT":          ("#00e5ff", "rgba(0,229,255,.08)"),
        "SENSOR":             ("#a78bfa", "rgba(167,139,250,.08)"),
        "PROCEDURE":          ("#39ff14", "rgba(57,255,20,.08)"),
        "HAZARD":             ("#ff6b35", "rgba(255,107,53,.08)"),
        "COMPLIANCE_STANDARD":("#f59e0b", "rgba(245,158,11,.08)"),
    }
    color, bg = color_map.get(entity_type, ("#8888aa", "rgba(136,136,170,.08)"))
    st.markdown(f"""
    <div style="
      background:{bg};
      backdrop-filter:blur(8px);
      border:1px solid {color}30;
      border-left:3px solid {color};
      border-radius:12px; padding:.8rem 1.1rem; margin:.4rem 0;
      transition: border-color .2s, box-shadow .2s;
    " onmouseover="this.style.boxShadow='0 0 16px {color}44'"
       onmouseout="this.style.boxShadow='none'">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="color:{color}; font-weight:700; font-size:.93rem;
                     font-family:'JetBrains Mono',monospace;">{node_id}</span>
        <span style="color:{color}; font-size:.68rem; background:{color}18;
                     border:1px solid {color}33; border-radius:20px;
                     padding:.15rem .65rem; letter-spacing:.5px;">{entity_type}</span>
      </div>
      <p style="color:#9ca3af; font-size:.8rem; margin:.35rem 0 0; line-height:1.4;">{description}</p>
    </div>
    """, unsafe_allow_html=True)


def chat_bubble(role: str, content: str, timestamp: str = ""):
    if role == "user":
        st.markdown(f"""
        <div style="display:flex; justify-content:flex-end; margin:.8rem 0;">
          <div style="
            background: linear-gradient(135deg, rgba(0,229,255,.18), rgba(0,229,255,.06));
            border: 1px solid rgba(0,229,255,.25);
            border-radius: 18px 18px 4px 18px;
            padding: .85rem 1.15rem; max-width: 76%;
            backdrop-filter: blur(8px);
          ">
            <p style="color:#f0f0f8; margin:0; font-size:.9rem; line-height:1.55;">{content}</p>
            <span style="color:#6b7280; font-size:.7rem;">{timestamp}</span>
          </div>
          <div style="width:36px; height:36px; border-radius:50%; flex-shrink:0;
            background:rgba(0,229,255,.12); border:1px solid rgba(0,229,255,.25);
            display:flex; align-items:center; justify-content:center;
            margin-left:.7rem; font-size:1rem;">👤</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display:flex; justify-content:flex-start; margin:.8rem 0;">
          <div style="width:36px; height:36px; border-radius:50%; flex-shrink:0;
            background:rgba(57,255,20,.08); border:1px solid rgba(57,255,20,.25);
            display:flex; align-items:center; justify-content:center;
            margin-right:.7rem; font-size:1rem;
            box-shadow: 0 0 12px rgba(57,255,20,.2);">⚙️</div>
          <div style="
            background: rgba(22,22,37,0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,.07);
            border-radius: 18px 18px 18px 4px;
            padding: .85rem 1.15rem; max-width: 76%;
          ">
            <p style="color:#f0f0f8; margin:0; font-size:.9rem; line-height:1.65;
                      white-space:pre-wrap;">{content}</p>
            <span style="color:#6b7280; font-size:.7rem;">{timestamp}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)


def section_header(icon: str, title: str, subtitle: str = ""):
    sub = f'<p style="color:#6b7280; font-size:.8rem; margin:.1rem 0 0;">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:.75rem; margin-bottom:1.1rem;">
      <span style="font-size:1.25rem; filter:drop-shadow(0 0 6px rgba(0,229,255,.4));">{icon}</span>
      <div>
        <h3 style="margin:0; font-size:1.05rem; color:#f0f0f8; font-weight:600;">{title}</h3>
        {sub}
      </div>
    </div>
    """, unsafe_allow_html=True)


def activity_log(action: str, detail: str = "", icon: str = "◈"):
    """Append an entry to the in-memory activity feed."""
    if "activity_feed" not in st.session_state:
        st.session_state.activity_feed = []
    ts = time.strftime("%H:%M:%S")
    st.session_state.activity_feed.insert(0, {"ts": ts, "icon": icon, "action": action, "detail": detail})
    st.session_state.activity_feed = st.session_state.activity_feed[:12]  # keep last 12


# ── Session state ─────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "graph_loaded":  False,
        "builder":       None,
        "engine":        None,
        "chat_history":  [],
        "selected_node": None,
        "graph_stats":   {},
        "filter_type":   "ALL",
        "activity_feed": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ── Graph loader ──────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_graph_resources(json_path: str, graphml_path: str):
    builder = GraphRAGBuilder(data_contract_path=json_path)
    if not builder.load_data_contract():
        return None, None, "❌ Could not load data contract. Run batch_extractor.py first."
    if not builder.build_graph():
        return None, None, "❌ Failed to build graph."
    try:
        import networkx as nx
        nx.write_graphml(builder.graph, graphml_path)
    except Exception:
        pass
    engine = GraphSearchEngine(graph_path=graphml_path, data_contract_path=json_path)
    if not engine.load_graph():
        return builder, None, "⚠️ Search engine couldn't load saved graph."
    engine.load_data_contract()
    stats = builder.get_graph_stats()
    return builder, engine, None, stats


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1.4rem .5rem 1rem;">
      <div style="font-size:2.4rem; margin-bottom:.4rem;
                  filter:drop-shadow(0 0 12px rgba(0,229,255,.5));">⚙️</div>
      <h2 style="font-size:1.05rem; margin:0; color:#00e5ff; letter-spacing:.8px;
                 font-weight:700;">AI-HackerZ</h2>
      <p style="color:#6b7280; font-size:.72rem; margin:.3rem 0 0; letter-spacing:.3px;">
        GraphRAG Control Panel
      </p>
    </div>
    <hr style="border-color:rgba(0,229,255,.12); margin:.5rem 0 1rem;">
    """, unsafe_allow_html=True)

    # ── Load graph button ──
    if not st.session_state.graph_loaded:
        if st.button("⚡  Initialize Graph Engine", use_container_width=True):
            steps = [
                ("Parsing data contract…", .3),
                ("Building NetworkX graph…", .5),
                ("Calibrating search engine…", .9),
            ]
            prog_bar = st.progress(0, text="Starting…")
            for txt, pct in steps:
                prog_bar.progress(pct, text=txt)
                time.sleep(0.3)
            result = load_graph_resources(str(GRAPH_JSON), str(GRAPH_ML))
            prog_bar.empty()
            if len(result) == 4:
                builder, engine, err, stats = result
            else:
                builder, engine, err = result
                stats = {}
            if err and not builder:
                st.error(err)
            else:
                st.session_state.builder      = builder
                st.session_state.engine       = engine
                st.session_state.graph_loaded = True
                st.session_state.graph_stats  = stats or {}
                activity_log("Graph engine initialised", f"{stats.get('total_nodes',0)} nodes · {stats.get('total_edges',0)} edges", "⚡")
                if err:
                    st.warning(err)
                else:
                    st.success("Graph ready!")
                st.rerun()
    else:
        st.markdown('<p style="color:#39ff14; font-size:.82rem; text-align:center; letter-spacing:.3px;">✅ &nbsp;Graph Engine Active</p>', unsafe_allow_html=True)
        if st.button("🔄  Reload Graph", use_container_width=True):
            load_graph_resources.clear()
            for k in ["graph_loaded", "builder", "engine", "graph_stats", "selected_node"]:
                st.session_state[k] = None if k not in ["graph_loaded"] else False
            activity_log("Graph reloaded", "", "🔄")
            st.rerun()

    st.markdown("<hr style='border-color:rgba(0,229,255,.12);'>", unsafe_allow_html=True)

    # ── Live document upload ──
    with st.expander("📄 Live Document Upload"):
        st.markdown("<p style='font-size:.78rem; color:#6b7280;'>Upload a TXT or PDF — AI extracts entities and merges them live.</p>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload file", type=["txt", "pdf"], label_visibility="collapsed")
        if uploaded_file is not None:
            if st.button("🚀 Extract & Merge", use_container_width=True):
                raw_dir = DATA_DIR / "raw_documents"
                raw_dir.mkdir(exist_ok=True)
                tmp_path = raw_dir / uploaded_file.name
                with open(tmp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                with st.spinner(f"Extracting from {uploaded_file.name}… (~30-90s)"):
                    extractor = BatchExtractor(inputs_dir=str(raw_dir), output_dir=str(DATA_DIR))
                    success = extractor.process_single_file_and_merge(str(tmp_path), str(GRAPH_JSON))
                if success:
                    st.success("Merged into graph!")
                    activity_log(f"Doc uploaded: {uploaded_file.name}", "Knowledge merged into graph", "📄")
                    load_graph_resources.clear()
                    for k in ["graph_loaded", "builder", "engine", "graph_stats", "selected_node"]:
                        st.session_state[k] = None if k not in ["graph_loaded"] else False
                    st.rerun()
                else:
                    st.error("Extraction failed or no data found.")

    st.markdown("<hr style='border-color:rgba(0,229,255,.12);'>", unsafe_allow_html=True)

    # ── Graph stats ──
    stats = st.session_state.graph_stats or {}
    if stats:
        st.markdown('<p style="color:#6b7280; font-size:.7rem; letter-spacing:.6px; margin-bottom:.5rem;">GRAPH METRICS</p>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        col1.metric("Nodes", stats.get("total_nodes", 0))
        col2.metric("Edges", stats.get("total_edges", 0))
        st.markdown(f"""
        <div style="margin-top:.5rem; font-size:.76rem; color:#6b7280; line-height:2;">
          <div>Directed: <span style="color:#00e5ff;">{'Yes' if stats.get('is_directed') else 'No'}</span></div>
          <div>Connected: <span style="color:#{'39ff14' if stats.get('is_connected') else 'ff6b35'};">
            {'Yes' if stats.get('is_connected') else 'No'}</span></div>
          <div>Avg In-Degree: <span style="color:#a78bfa;">{stats.get('average_in_degree', 0):.2f}</span></div>
          <div>Avg Out-Degree: <span style="color:#a78bfa;">{stats.get('average_out_degree', 0):.2f}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(0,229,255,.12);'>", unsafe_allow_html=True)

    # ── Fault risk leaderboard ──
    if st.session_state.graph_loaded and st.session_state.builder:
        _b = st.session_state.builder
        _all = _b.get_all_node_ids()
        risk_scores = {}
        for _nid in _all:
            _info = _b.get_node_info(_nid)
            if _info and _info.get("entity_type") == "EQUIPMENT":
                _hazards = sum(1 for src, _, d in _b.graph.in_edges(_nid, data=True)
                               if _b.get_node_info(src) and _b.get_node_info(src).get("entity_type") == "HAZARD")
                _sensors = sum(1 for src, _, d in _b.graph.in_edges(_nid, data=True)
                               if _b.get_node_info(src) and _b.get_node_info(src).get("entity_type") == "SENSOR")
                _has_esd = any(d.get("relation_type") in ("INITIATES", "TRIGGERS")
                               for _, _, d in _b.graph.out_edges(_nid, data=True))
                risk_scores[_nid] = _hazards * 40 + _sensors * 15 + (20 if not _has_esd else 0)
        if risk_scores:
            st.markdown('<p style="color:#6b7280; font-size:.7rem; letter-spacing:.6px; margin-bottom:.5rem;">⚠️ FAULT RISK LEADERBOARD</p>', unsafe_allow_html=True)
            for _nid, _score in sorted(risk_scores.items(), key=lambda x: x[1], reverse=True):
                _color = "#ff6b35" if _score >= 50 else "#f59e0b" if _score >= 20 else "#39ff14"
                _label = "HIGH" if _score >= 50 else "MED" if _score >= 20 else "LOW"
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center;
                            background:rgba(0,0,0,.25); border-left:3px solid {_color};
                            border-radius:6px; padding:.35rem .65rem; margin:.2rem 0;
                            backdrop-filter:blur(4px);">
                  <span style="color:#e5e7eb; font-size:.75rem; font-family:'JetBrains Mono',monospace;">{_nid}</span>
                  <span style="color:{_color}; font-size:.68rem; font-weight:700;">{_label}</span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(0,229,255,.12);'>", unsafe_allow_html=True)

    # ── Activity feed ──
    feed = st.session_state.get("activity_feed", [])
    if feed:
        st.markdown('<p style="color:#6b7280; font-size:.7rem; letter-spacing:.6px; margin-bottom:.4rem;">◈ LIVE ACTIVITY</p>', unsafe_allow_html=True)
        for entry in feed[:5]:
            st.markdown(f"""
            <div class="activity-entry" style="
              display:flex; gap:.5rem; align-items:flex-start;
              padding:.3rem 0; border-bottom:1px solid rgba(0,229,255,.05);">
              <span style="color:#00e5ff; font-size:.8rem; flex-shrink:0;">{entry['icon']}</span>
              <div style="min-width:0;">
                <div style="color:#e5e7eb; font-size:.75rem; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{entry['action']}</div>
                <div style="color:#6b7280; font-size:.68rem;">{entry['ts']} · {entry.get('detail','')[:30]}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(0,229,255,.12);'>", unsafe_allow_html=True)

    # ── Filter ──
    st.markdown('<p style="color:#6b7280; font-size:.7rem; letter-spacing:.6px; margin-bottom:.4rem;">FILTER BY TYPE</p>', unsafe_allow_html=True)
    filter_type = st.selectbox("Filter by entity type", ["ALL", "EQUIPMENT", "SENSOR", "PROCEDURE", "HAZARD", "COMPLIANCE_STANDARD"], label_visibility="collapsed")
    st.session_state.filter_type = filter_type

    st.markdown("""
    <div style="font-size:.7rem; color:#6b7280; line-height:2; margin-top:.8rem;">
      <b style="color:#9ca3af;">HOW TO USE</b><br>
      1. Click <em>Initialize Graph Engine</em><br>
      2. Explore the <em>Knowledge Graph</em> tab<br>
      3. Click any node to inspect it<br>
      4. Ask questions in <em>AI Query</em> tab<br>
      5. Upload docs via <em>Live Document Upload</em>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════
hero_banner(st.session_state.graph_stats or {})

if not st.session_state.graph_loaded:
    st.markdown("""
    <div style="
      background: rgba(15,15,26,0.6);
      backdrop-filter: blur(20px);
      border: 1px dashed rgba(0,229,255,.2);
      border-radius: 20px;
      padding: 4rem 2rem;
      text-align: center;
      margin-top: 1rem;
    ">
      <div style="font-size:3.5rem; margin-bottom:1rem;
                  filter:drop-shadow(0 0 20px rgba(0,229,255,.4));">🔌</div>
      <h2 style="color:#f0f0f8; margin:0 0 .6rem; font-size:1.5rem;">Graph Engine Not Loaded</h2>
      <p style="color:#6b7280; font-size:.9rem; max-width:440px; margin:.3rem auto 0; line-height:1.6;">
        Click <strong style="color:#00e5ff;">⚡ Initialize Graph Engine</strong> in the
        sidebar to parse the data contract and build the knowledge graph.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Tabs ──────────────────────────────────────────────────────────────────────
builder: GraphRAGBuilder = st.session_state.builder
engine: GraphSearchEngine = st.session_state.engine

tab_graph, tab_query, tab_explorer, tab_risk, tab_contract = st.tabs([
    "📊  Knowledge Graph",
    "🤖  AI Query Interface",
    "🔍  Node Explorer",
    "⚠️  Risk Analysis",
    "📋  Data Contract",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Knowledge Graph
# ══════════════════════════════════════════════════════════════════════════════
with tab_graph:
    section_header("📊", "Live Knowledge Graph", "Interactive directed graph — click any node to inspect it")

    try:
        from pyvis.network import Network
        import streamlit.components.v1 as components

        ft = st.session_state.filter_type
        all_ids = builder.get_all_node_ids()

        net = Network(height="610px", width="100%", bgcolor="#080810", font_color="#e5e7eb", directed=True)
        net.set_options("""
        {
          "nodes": {
            "shape": "dot",
            "size": 22,
            "font": { "size": 13, "face": "JetBrains Mono", "color": "#e5e7eb" },
            "borderWidth": 2,
            "borderWidthSelected": 4,
            "shadow": { "enabled": true, "size": 16, "color": "rgba(0,229,255,.35)" }
          },
          "edges": {
            "arrows": { "to": { "enabled": true, "scaleFactor": 0.65 } },
            "color": { "color": "#00e5ff", "opacity": 0.45, "highlight": "#00e5ff" },
            "font": { "size": 10, "color": "#6b7280", "strokeWidth": 0, "face": "Inter" },
            "width": 1.4,
            "smooth": { "type": "curvedCW", "roundness": 0.22 },
            "shadow": { "enabled": true, "color": "rgba(0,229,255,.15)", "size": 8 }
          },
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -9000,
              "centralGravity": 0.3,
              "springLength": 170,
              "springConstant": 0.035,
              "damping": 0.09
            },
            "stabilization": { "iterations": 300 }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": false,
            "keyboard": true,
            "multiselect": false,
            "zoomView": true
          },
          "background": { "color": "#080810" }
        }
        """)

        COLOR_MAP = {
            "EQUIPMENT":           "#00e5ff",
            "SENSOR":              "#a78bfa",
            "PROCEDURE":           "#39ff14",
            "HAZARD":              "#ff6b35",
            "COMPLIANCE_STANDARD": "#f59e0b",
            "UNKNOWN":             "#6b7280",
        }

        for node_id in all_ids:
            info  = builder.get_node_info(node_id)
            etype = info.get("entity_type", "UNKNOWN") if info else "UNKNOWN"
            desc  = info.get("description", "") if info else ""
            if ft != "ALL" and etype != ft:
                continue
            color = COLOR_MAP.get(etype, "#6b7280")
            size  = 30 if etype == "EQUIPMENT" else 22 if etype == "SENSOR" else 20
            title = f"<b style='color:{color}'>{node_id}</b><br><em style='color:#6b7280'>{etype}</em><br><span style='color:#9ca3af;font-size:12px'>{desc}</span>"
            net.add_node(node_id, label=node_id, color={"background": color, "border": color, "highlight": {"background": color, "border": "#ffffff"}}, size=size, title=title)

        added_nodes = set(net.get_nodes())
        for u, v, data in builder.graph.edges(data=True):
            if u not in added_nodes or v not in added_nodes:
                continue
            rtype = data.get("relation_type", "")
            ctx   = data.get("context", "")
            net.add_edge(u, v, label=rtype, title=ctx)

        # Inject dark background + click bridge
        html_path = "/tmp/graph_viz.html"
        net.save_graph(html_path)
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Force dark bg + click bridge
        dark_and_click = """
<style>
  body, html { background: #080810 !important; margin: 0; padding: 0; }
  #mynetwork { background: #080810 !important; border: none !important; }
  canvas { background: #080810 !important; }
</style>
<script>
function attachClickBridge() {
  if (typeof network !== 'undefined') {
    network.on("click", function(params) {
      if (params.nodes.length > 0) {
        var nodeId = params.nodes[0];
        network.selectNodes([nodeId]);
        network.setSelection({nodes: [nodeId]}, {highlightEdges: true});
        try { window.parent.sessionStorage.setItem('__pyvis_clicked__', nodeId); } catch(e) {}
      }
    });
    network.on("hoverNode", function() { document.body.style.cursor = 'pointer'; });
    network.on("blurNode",  function() { document.body.style.cursor = 'default'; });
    // After stabilisation, disable physics for performance
    network.once("stabilizationIterationsDone", function() {
      network.setOptions({ physics: { enabled: false } });
    });
  } else {
    setTimeout(attachClickBridge, 200);
  }
}
attachClickBridge();
</script>
"""
        html_content = html_content.replace("</body>", dark_and_click + "</body>")
        components.html(html_content, height=620, scrolling=False)

        # Polling bridge (0-height, invisible)
        components.html("""
<script>
(function(){
  function poll(){
    try {
      var nodeId = window.parent.sessionStorage.getItem('__pyvis_clicked__');
      if (nodeId) {
        window.parent.sessionStorage.removeItem('__pyvis_clicked__');
        var url = new URL(window.parent.location.href);
        url.searchParams.set('node', nodeId);
        window.parent.location.href = url.toString();
      }
    } catch(e) {}
  }
  setInterval(poll, 250);
})();
</script>
""", height=0, scrolling=False)

        # Enhanced legend
        st.markdown("""
        <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-top:.7rem;
                    background:rgba(15,15,26,.7); backdrop-filter:blur(8px);
                    border:1px solid rgba(0,229,255,.08); border-radius:10px;
                    padding:.6rem 1rem;">
          <span style="font-size:.76rem; color:#00e5ff;">● EQUIPMENT</span>
          <span style="font-size:.76rem; color:#a78bfa;">● SENSOR</span>
          <span style="font-size:.76rem; color:#39ff14;">● PROCEDURE</span>
          <span style="font-size:.76rem; color:#ff6b35;">● HAZARD</span>
          <span style="font-size:.76rem; color:#f59e0b;">● COMPLIANCE</span>
          <span style="font-size:.73rem; color:#6b7280; margin-left:auto;">
            Drag · Scroll to zoom · Click to inspect
          </span>
        </div>
        """, unsafe_allow_html=True)

    except ImportError:
        st.warning("⚠️ `pyvis` not installed. Run: `pip install pyvis`")

    # ── Node Inspector ────────────────────────────────────────────────────────
    st.markdown("<hr style='border-color:rgba(0,229,255,.08); margin:1.4rem 0;'>", unsafe_allow_html=True)
    section_header("🔎", "Node Inspector", "Click any node in the graph above — or select below")

    all_ids = builder.get_all_node_ids()
    preselect  = st.session_state.get("selected_node", "")
    opts       = ["— choose a node —"] + all_ids
    default_idx = opts.index(preselect) if preselect in all_ids else 0

    selected = st.selectbox("Select node", opts, index=default_idx,
                            label_visibility="collapsed", key="node_inspector_select")
    if selected and selected != "— choose a node —":
        st.session_state["selected_node"] = selected
        activity_log(f"Node inspected: {selected}", "", "🔎")
        with st.spinner("Extracting local context…"):
            context = builder.extract_local_context(selected)
        if context:
            info  = builder.get_node_info(selected)
            etype = info.get("entity_type", "UNKNOWN") if info else "UNKNOWN"
            desc  = info.get("description", "") if info else ""
            in_d  = info.get("in_degree", 0) if info else 0
            out_d = info.get("out_degree", 0) if info else 0
            COLOR_MAP2 = {"EQUIPMENT":"#00e5ff","SENSOR":"#a78bfa","PROCEDURE":"#39ff14",
                          "HAZARD":"#ff6b35","COMPLIANCE_STANDARD":"#f59e0b"}
            nc = COLOR_MAP2.get(etype, "#6b7280")

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Entity Type", etype)
            col_b.metric("Incoming Links", in_d)
            col_c.metric("Outgoing Links", out_d)

            st.markdown(f"""
            <div style="background:rgba(15,15,26,.8); backdrop-filter:blur(16px);
                        border:1px solid {nc}28; border-left:3px solid {nc};
                        border-radius:14px; padding:1rem 1.3rem; margin-top:.9rem;">
              <p style="color:#6b7280; font-size:.72rem; margin:0 0 .4rem; letter-spacing:.4px;">DESCRIPTION</p>
              <p style="color:#f0f0f8; font-size:.92rem; margin:0; line-height:1.6;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📄 Raw Graph Context (sent to LLM)"):
                st.code(context, language="text")
        else:
            st.warning("No context found for this node.")

    # ── Path Finder ───────────────────────────────────────────────────────────
    st.markdown("<hr style='border-color:rgba(0,229,255,.08); margin:1.4rem 0;'>", unsafe_allow_html=True)
    section_header("🔗", "Relationship Path Finder", "Trace the shortest connection between any two nodes")

    if engine is not None:
        all_ids_pf = builder.get_all_node_ids()
        pf_col1, pf_col2 = st.columns(2)
        src_node = pf_col1.selectbox("From node", ["— select source —"] + all_ids_pf, key="pf_src")
        tgt_node = pf_col2.selectbox("To node",   ["— select target —"] + all_ids_pf, key="pf_tgt")

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
                    activity_log(f"Path found: {src_node} → {tgt_node}", f"{len(path)-1} hops", "🔗")
                    st.success(f"✅ Path found! {len(path)-1} hop(s)")
                    hop_html = ""
                    COLOR_MAP_PF = {"EQUIPMENT":"#00e5ff","SENSOR":"#a78bfa","PROCEDURE":"#39ff14",
                                    "HAZARD":"#ff6b35","COMPLIANCE_STANDARD":"#f59e0b"}
                    for i, nid in enumerate(path):
                        inf = builder.get_node_info(nid)
                        et  = inf.get("entity_type","UNKNOWN") if inf else "UNKNOWN"
                        c   = COLOR_MAP_PF.get(et, "#6b7280")
                        hop_html += f"""<span class='hop-node' style='
                          background:rgba(0,0,0,.35); backdrop-filter:blur(6px);
                          border:1px solid {c}55; border-radius:10px;
                          padding:.4rem .85rem; color:{c};
                          font-family:"JetBrains Mono",monospace; font-size:.85rem;
                          box-shadow:0 0 10px {c}22;'>{nid}</span>"""
                        if i < len(path)-1:
                            edge_d = builder.graph.get_edge_data(path[i], path[i+1]) or {}
                            rel    = edge_d.get("relation_type", "→")
                            hop_html += f"<span style='color:#6b7280; margin:0 .5rem; font-size:.78rem;'>──[{rel}]──▶</span>"
                    st.markdown(f"<div style='display:flex; flex-wrap:wrap; gap:.5rem; align-items:center; margin:.9rem 0;'>{hop_html}</div>", unsafe_allow_html=True)
                    with st.expander("📄 Full path context (sent to LLM)"):
                        st.code(path_ctx, language="text")
                else:
                    st.error(f"❌ No path found between **{src_node}** and **{tgt_node}**.")
    else:
        st.info("Load the graph engine first to use the path finder.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — AI Query Interface (streaming LLM response)
# ══════════════════════════════════════════════════════════════════════════════
with tab_query:
    section_header("🤖", "AI Query Interface", "Ask the knowledge graph anything in natural language")

    if engine is None:
        st.error("Search engine not available. Ensure graph is loaded.")
    else:
        # Dynamic quick queries
        st.markdown('<p style="color:#6b7280; font-size:.78rem; margin-bottom:.5rem; letter-spacing:.3px;">QUICK QUERIES</p>', unsafe_allow_html=True)
        all_equip   = [n for n in builder.get_all_node_ids() if builder.get_node_info(n) and builder.get_node_info(n).get("entity_type") == "EQUIPMENT"]
        all_hazards = [n for n in builder.get_all_node_ids() if builder.get_node_info(n) and builder.get_node_info(n).get("entity_type") == "HAZARD"]
        all_sensors = [n for n in builder.get_all_node_ids() if builder.get_node_info(n) and builder.get_node_info(n).get("entity_type") == "SENSOR"]
        sample_queries = []
        if all_equip:   sample_queries.append(f"What does {all_equip[0]} connect to?")
        if all_hazards: sample_queries.append(f"How do we mitigate {all_hazards[0]}?")
        if all_sensors: sample_queries.append(f"What does {all_sensors[0]} monitor?")
        general_qs = ["What hazards exist in the plant?", "What safety standards govern operations?", "Describe the emergency shutdown procedure."]
        sample_queries.extend(general_qs[:max(0, 5 - len(sample_queries))])

        cols = st.columns(len(sample_queries))
        for i, q in enumerate(sample_queries):
            label = f"💬 {q[:20]}…" if len(q) > 20 else f"💬 {q}"
            if cols[i].button(label, key=f"sample_{i}", use_container_width=True):
                st.session_state["prefill_query"] = q

        st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

        # Chat history
        if not st.session_state.chat_history:
            st.markdown("""
            <div style="text-align:center; padding:3rem 1rem;
                        background:rgba(15,15,26,.5); backdrop-filter:blur(12px);
                        border:1px solid rgba(0,229,255,.08); border-radius:16px;">
              <div style="font-size:3rem; margin-bottom:.7rem; opacity:.6;">💬</div>
              <p style="font-size:.9rem; color:#6b7280;">
                Ask your first question to begin exploring the knowledge graph.
              </p>
            </div>
            """, unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            chat_bubble(msg["role"], msg["content"], msg.get("time", ""))

        st.markdown("<hr style='border-color:rgba(0,229,255,.08);'>", unsafe_allow_html=True)

        # Query form
        prefill = st.session_state.pop("prefill_query", "")
        with st.form(key="query_form", clear_on_submit=True):
            user_input = st.text_input(
                "Your query", value=prefill,
                placeholder="e.g. What are the risk factors for PUMP-101A?",
                label_visibility="collapsed",
            )
            col_submit, col_clear, col_depth = st.columns([3, 1, 2])
            submit = col_submit.form_submit_button("⚡  Ask AI", use_container_width=True)
            clear  = col_clear.form_submit_button("🗑️",         use_container_width=True)
            depth  = col_depth.selectbox("Depth", [1, 2, 3], index=0, label_visibility="collapsed")

        if clear:
            st.session_state.chat_history = []
            st.rerun()

        if submit and user_input.strip():
            ts = time.strftime("%H:%M")
            st.session_state.chat_history.append({"role": "user", "content": user_input, "time": ts})
            activity_log(f"Query: {user_input[:40]}", "", "🤖")

            # Streaming response with typing effect
            with st.spinner("Searching graph + querying Llama 3.2…"):
                try:
                    ctx, answer = engine.query(user_input, top_k=5, context_depth=int(depth))
                    st.session_state.chat_history.append({
                        "role": "assistant", "content": answer,
                        "time": time.strftime("%H:%M"), "context": ctx,
                    })
                except Exception as e:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"⚠️ Error: {e}\n\nEnsure Ollama is running and `llama3.2` is pulled (`ollama pull llama3.2`).",
                        "time": time.strftime("%H:%M"),
                    })
            st.rerun()

        if st.session_state.chat_history:
            last = st.session_state.chat_history[-1]
            if last.get("role") == "assistant" and last.get("context"):
                with st.expander("🔎 View retrieved graph context"):
                    st.code(last["context"], language="text")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Node Explorer
# ══════════════════════════════════════════════════════════════════════════════
with tab_explorer:
    section_header("🔍", "Entity Explorer", "Browse and search all nodes in the knowledge graph")

    ft      = st.session_state.filter_type
    all_ids = builder.get_all_node_ids()
    search_term = st.text_input("Search nodes", placeholder="Type a keyword or node ID…", label_visibility="collapsed")

    filtered = []
    for node_id in all_ids:
        info  = builder.get_node_info(node_id)
        etype = info.get("entity_type", "UNKNOWN") if info else "UNKNOWN"
        desc  = info.get("description", "") if info else ""
        if ft != "ALL" and etype != ft: continue
        if search_term and search_term.lower() not in node_id.lower() and search_term.lower() not in desc.lower(): continue
        filtered.append((node_id, etype, desc, info))

    if not filtered:
        st.info("No nodes match your filter/search.")
    else:
        st.markdown(f'<p style="color:#6b7280; font-size:.78rem; margin-bottom:.6rem;"><b style="color:#f0f0f8;">{len(filtered)}</b> entity/entities found</p>', unsafe_allow_html=True)
        for node_id, etype, desc, info in filtered:
            node_badge(node_id, etype, desc)

        st.markdown("<hr style='border-color:rgba(0,229,255,.08); margin:1rem 0;'>", unsafe_allow_html=True)
        section_header("📌", "Relationship Map", "Outgoing and incoming edges for a selected node")
        pick = st.selectbox("Pick node for relationship map", ["— select —"] + [n for n, *_ in filtered], label_visibility="collapsed")
        if pick and pick != "— select —":
            context = builder.extract_local_context(pick)
            if context:
                st.code(context, language="text")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Risk Analysis (SVG Gauge Dials)
# ══════════════════════════════════════════════════════════════════════════════
with tab_risk:
    section_header("⚠️", "Fault Risk Analysis", "Automated risk scoring for all equipment nodes based on graph topology")

    all_ids_r = builder.get_all_node_ids()
    risk_data = []
    for nid in all_ids_r:
        info = builder.get_node_info(nid)
        if not info or info.get("entity_type") != "EQUIPMENT": continue
        hazards = [(src, d) for src, _, d in builder.graph.in_edges(nid, data=True)
                   if builder.get_node_info(src) and builder.get_node_info(src).get("entity_type") == "HAZARD"]
        sensors = [(src, d) for src, _, d in builder.graph.in_edges(nid, data=True)
                   if builder.get_node_info(src) and builder.get_node_info(src).get("entity_type") == "SENSOR"]
        procs   = [(tgt, d) for _, tgt, d in builder.graph.out_edges(nid, data=True)
                   if builder.get_node_info(tgt) and builder.get_node_info(tgt).get("entity_type") == "PROCEDURE"]
        has_redundancy = any(d.get("relation_type") == "HAS_REDUNDANCY" for _, _, d in builder.graph.out_edges(nid, data=True))
        score = len(hazards) * 40 + (max(0, 2 - len(sensors)) * 15) + (0 if procs else 25) + (0 if has_redundancy else 10)
        risk_data.append({
            "node_id": nid, "desc": info.get("description", ""),
            "hazards": len(hazards), "sensors": len(sensors),
            "procedures": len(procs), "redundancy": has_redundancy, "score": score,
        })
    risk_data.sort(key=lambda x: x["score"], reverse=True)

    if not risk_data:
        st.info("No EQUIPMENT nodes found in the graph.")
    else:
        st.markdown(f'<p style="color:#6b7280; font-size:.8rem;">Analysed <b style="color:#f0f0f8;">{len(risk_data)}</b> equipment nodes</p>', unsafe_allow_html=True)

        for rd in risk_data:
            score  = rd["score"]
            color  = "#ff6b35" if score >= 50 else "#f59e0b" if score >= 20 else "#39ff14"
            label  = "🔴 HIGH RISK" if score >= 50 else "🟠 MEDIUM RISK" if score >= 20 else "🟢 LOW RISK"
            gauge  = gauge_svg(min(score, 100), color, size=90)

            st.markdown(f"""
            <div style="
              background:rgba(15,15,26,.8); backdrop-filter:blur(16px);
              border:1px solid {color}22; border-left:4px solid {color};
              border-radius:16px; padding:1.1rem 1.3rem; margin:.6rem 0;
              transition: box-shadow .3s;
            " onmouseover="this.style.boxShadow='0 0 30px {color}22'"
               onmouseout="this.style.boxShadow='none'">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="flex:1;">
                  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:.5rem;">
                    <span style="color:{color}; font-family:'JetBrains Mono',monospace;
                                 font-weight:700; font-size:1rem;">{rd['node_id']}</span>
                    <span style="color:{color}; font-size:.78rem; font-weight:600;">{label}</span>
                  </div>
                  <p style="color:#9ca3af; font-size:.8rem; margin:0 0 .7rem; line-height:1.4;">{rd['desc']}</p>
                  <div style="display:flex; gap:1.5rem; font-size:.76rem; color:#6b7280; flex-wrap:wrap;">
                    <span>⚡ Hazards: <b style="color:{color};">{rd['hazards']}</b></span>
                    <span>📡 Sensors: <b style="color:#a78bfa;">{rd['sensors']}</b></span>
                    <span>📋 ESD Procs: <b style="color:#39ff14;">{rd['procedures']}</b></span>
                    <span>♻️ Redundancy: <b style="color:#{'39ff14' if rd['redundancy'] else 'ff6b35'};">{'Yes' if rd['redundancy'] else 'No'}</b></span>
                  </div>
                </div>
                <!-- SVG Gauge -->
                <div style="flex-shrink:0; margin-left:1.2rem;">{gauge}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color:rgba(0,229,255,.08); margin:1.2rem 0;'>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:rgba(15,15,26,.7); backdrop-filter:blur(12px);
                    border:1px solid rgba(0,229,255,.08); border-radius:14px; padding:1rem 1.3rem;">
          <p style="color:#6b7280; font-size:.72rem; margin:0 0 .4rem; letter-spacing:.4px;">SCORING FORMULA</p>
          <p style="color:#f0f0f8; font-size:.85rem; font-family:'JetBrains Mono',monospace; margin:0;">
            Score = (Hazards × 40) + (Missing sensors × 15) + (No ESD proc × 25) + (No redundancy × 10)
          </p>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Data Contract Viewer
# ══════════════════════════════════════════════════════════════════════════════
with tab_contract:
    section_header("📋", "Raw Data Contract", f"Source: {GRAPH_JSON}")
    try:
        with open(GRAPH_JSON, "r", encoding="utf-8") as f:
            raw = json.load(f)
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Document ID",   raw.get("document_id", "N/A"))
        col_b.metric("Entities",      len(raw.get("entities", [])))
        col_c.metric("Relationships", len(raw.get("relationships", [])))
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        st.json(raw)
    except FileNotFoundError:
        st.error(f"Data contract not found at `{GRAPH_JSON}`.")
    except Exception as e:
        st.error(f"Error reading contract: {e}")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
  text-align:center; padding:1.5rem .5rem .8rem;
  color:#4b5563; font-size:.72rem; letter-spacing:.4px;
  border-top:1px solid rgba(0,229,255,.06); margin-top:2.5rem;
">
  AI-HackerZ &nbsp;·&nbsp; ET AI Hackathon 2026 &nbsp;·&nbsp; Problem Statement 8 &nbsp;·&nbsp;
  <span style="color:#00e5ff;">100% Offline Edge-Computing GraphRAG</span>
</div>
""", unsafe_allow_html=True)
