"use client";

import React, { useState, useRef, useEffect } from 'react';
import SiriOrb from '@/components/SiriOrb';
import { UploadCloud, Send, Loader2, Sparkles, Trash2, Activity, FileText, AlertTriangle, Database, Download, Paperclip, Mic, MicOff, ShieldAlert, Plus, Clock, Search, MessageSquare } from 'lucide-react';
import Link from 'next/link';
import ChatInput from '@/components/ChatInput';

type Message = {
  role: 'user' | 'assistant';
  content: string;
  context?: string;
};

type ChatThread = {
  id: string;
  title: string;
  date: string;
  messages: Message[];
};

const AILoadingState = ({ 
  steps = [
    "Analyzing graph topology...",
    "Extracting neighborhood context...",
    "Querying vector database...",
    "Synthesizing grounded response..."
  ],
  inline = false
}: { steps?: string[], inline?: boolean }) => {
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStepIndex((prev) => (prev + 1) % steps.length);
    }, 2500);
    return () => clearInterval(timer);
  }, []);

  if (inline) {
    return (
      <div className="fade-up" style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', color: 'var(--cyan)' }}>
        <div style={{ display: 'flex', gap: '4px' }}>
          <div style={{ width: '6px', height: '6px', background: 'var(--cyan)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both' }}></div>
          <div style={{ width: '6px', height: '6px', background: 'var(--cyan)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '0.2s' }}></div>
          <div style={{ width: '6px', height: '6px', background: 'var(--cyan)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '0.4s' }}></div>
        </div>
        <span style={{ fontSize: '0.95rem', fontWeight: 600, fontStyle: 'italic', transition: 'all 0.3s ease' }}>
          {steps[stepIndex]}
        </span>
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
          }
        `}} />
      </div>
    );
  }

  return (
    <div className="fade-up" style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1.5rem' }}>
      <div style={{
        width: '36px', height: '36px', borderRadius: '50%', flexShrink: 0,
        background: 'radial-gradient(circle at 30% 30%, #818cf8, #22d3ee, #fb7185)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: '0 0 15px rgba(34,211,238,.4)',
        animation: 'pulse-glow 2s infinite ease-in-out'
      }}>
        <Sparkles size={16} color="white" className="animate-pulse" />
      </div>
      
      <div style={{
        background: 'rgba(255,255,255,0.08)',
        color: 'var(--txt)',
        borderRadius: '4px 20px 20px 20px',
        padding: '1rem 1.2rem',
        boxShadow: 'var(--shadow-sm)',
        border: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.8rem',
        minWidth: '250px'
      }}>
        <div style={{ display: 'flex', gap: '4px' }}>
          <div style={{ width: '6px', height: '6px', background: 'var(--cyan)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both' }}></div>
          <div style={{ width: '6px', height: '6px', background: 'var(--cyan)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '0.2s' }}></div>
          <div style={{ width: '6px', height: '6px', background: 'var(--cyan)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '0.4s' }}></div>
        </div>
        <span style={{ fontSize: '0.9rem', color: 'var(--txt2)', fontWeight: 500, fontStyle: 'italic', transition: 'all 0.3s ease' }}>
          {steps[stepIndex]}
        </span>
      </div>
      
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes pulse-glow {
          0% { box-shadow: 0 0 0 0 rgba(34,211,238, 0.4); }
          70% { box-shadow: 0 0 0 10px rgba(34,211,238, 0); }
          100% { box-shadow: 0 0 0 0 rgba(34,211,238, 0); }
        }
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }
      `}} />
    </div>
  );
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);
  const currentThreadIdRef = useRef<string | null>(null);

  // Sync ref with state
  useEffect(() => {
    currentThreadIdRef.current = currentThreadId;
  }, [currentThreadId]);

  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  
  const [graphData, setGraphData] = useState<{nodes: any[], links: any[]}>({nodes: [], links: []});
  const [riskData, setRiskData] = useState<any[]>([]);
  const [isGeneratingQueries, setIsGeneratingQueries] = useState<boolean>(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // --- Local Storage Persistence ---
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedThreads = localStorage.getItem('graphrag_threads');
      const savedActive = localStorage.getItem('graphrag_active_thread');
      if (savedThreads) {
        try {
          const parsed = JSON.parse(savedThreads);
          setThreads(parsed);
          if (savedActive) {
            setCurrentThreadId(savedActive);
            const activeT = parsed.find((t: ChatThread) => t.id === savedActive);
            if (activeT) setMessages(activeT.messages);
          }
        } catch(e) {}
      }
    }
  }, []);

  useEffect(() => {
    if (typeof window !== 'undefined' && threads.length > 0) {
      localStorage.setItem('graphrag_threads', JSON.stringify(threads));
    }
  }, [threads]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      if (currentThreadId) {
        localStorage.setItem('graphrag_active_thread', currentThreadId);
      } else {
        localStorage.removeItem('graphrag_active_thread');
      }
    }
  }, [currentThreadId]);
  // --------------------------------

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadDashboardData = (sessionId: string) => {
    // Clear previous state to prevent cross-chat data bleeding
    setGraphData({nodes: [], links: []});
    setRiskData([]);
    
    fetch(`http://localhost:8000/api/graph-data?session_id=${sessionId}`)
      .then(r => {
        if (!r.ok) throw new Error("Graph data fetch failed");
        return r.json();
      })
      .then(data => {
        if(data.nodes) setGraphData(data);
      })
      .catch(e => console.error("Error loading graph data:", e));
    
    fetch(`http://localhost:8000/api/risk?session_id=${sessionId}`)
      .then(r => {
        if (!r.ok) throw new Error("Risk data fetch failed");
        return r.json();
      })
      .then(data => {
         if(data.hazards) {
            setRiskData(data.hazards.slice(0, 4));
         } else {
            setRiskData([]);
         }
      })
      .catch(e => console.error("Error loading risk data:", e));
  };

  useEffect(() => {
    if (currentThreadId === null) {
      setGraphData({nodes: [], links: []});
      setRiskData([]);
    } else {
      loadDashboardData(currentThreadId);
    }
  }, [currentThreadId]);

  // Quick queries are now generated instantly via getDynamicQueries() on render,
  // avoiding the 20-30s local GPU bottleneck.

  const handleExportReport = () => {
    window.open(`http://localhost:8000/api/export-report?session_id=${currentThreadId || 'default'}`, '_blank');
  };

  const handleSend = async (text: string) => {
    if (!text.trim() || isLoading) return;

    setIsLoading(true);

    let activeId = currentThreadId;
    let currentMessages = messages;
    
    if (!activeId) {
      activeId = Date.now().toString();
      setCurrentThreadId(activeId);
      currentMessages = [];
    }

    const newMessages: Message[] = [...currentMessages, { role: 'user', content: text }];
    setMessages(newMessages);

    // Update threads synchronously
    setThreads(prev => {
      const existing = prev.find(t => t.id === activeId);
      if (existing) {
        return prev.map(t => t.id === activeId ? { ...t, messages: newMessages } : t);
      } else {
        return [{ id: activeId as string, title: text.substring(0, 30) + (text.length > 30 ? '...' : ''), date: new Date().toLocaleDateString(), messages: newMessages }, ...prev];
      }
    });

    try {
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, depth: 2, top_k: 5, session_id: activeId }),
      });
      if (!res.ok) throw new Error('API Error');
      const data = await res.json();
      
      const updatedMessages: Message[] = [...newMessages, { role: 'assistant', content: data.answer, context: data.context }];
      
      if (currentThreadIdRef.current === activeId) {
        setMessages(updatedMessages);
      }
      
      setThreads(prev => prev.map(t => t.id === activeId ? { ...t, messages: updatedMessages } : t));
    } catch (err) {
      const errorMessages: Message[] = [...newMessages, { role: 'assistant', content: '⚠️ Failed to connect to engine.' }];
      if (currentThreadIdRef.current === activeId) {
        setMessages(errorMessages);
      }
      setThreads(prev => prev.map(t => t.id === activeId ? { ...t, messages: errorMessages } : t));
    } finally {
      setIsLoading(false);
    }
  };

  const startNewInvestigation = () => {
    setCurrentThreadId(null);
    setMessages([]);
  };

  const handleDeleteThread = (threadId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // prevent selecting the thread
    
    // Remove from state
    setThreads(prev => prev.filter(t => t.id !== threadId));
    
    // If it's the active one, clear dashboard
    if (currentThreadId === threadId) {
      setCurrentThreadId(null);
      setMessages([]);
    }
    
    // Update local storage immediately just in case
    const saved = localStorage.getItem('graphrag_threads');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        const filtered = parsed.filter((t: ChatThread) => t.id !== threadId);
        localStorage.setItem('graphrag_threads', JSON.stringify(filtered));
      } catch(e) {}
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadStatus(`Ingesting ${file.name}...`);
    
    let activeId = currentThreadId;
    if (!activeId) {
      activeId = Date.now().toString();
      setCurrentThreadId(activeId);
      // Initialize an empty thread so it shows up in the list
      setThreads(prev => [
        { id: activeId as string, title: `Dataset: ${file.name}`, date: new Date().toLocaleDateString(), messages: [] },
        ...prev
      ]);
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`http://localhost:8000/api/upload?session_id=${activeId}`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Upload Failed');
      setUploadStatus(`✓ ${file.name} ingested successfully`);
      setTimeout(() => setUploadStatus(null), 3000);
      
      // Refresh stats
      loadDashboardData(activeId);
    } catch (err) {
      setUploadStatus(`❌ Failed to ingest ${file.name}`);
      setTimeout(() => setUploadStatus(null), 3000);
    } finally {
      setIsUploading(false);
    }
  };

  const getDynamicQueries = () => {
     const nodes = graphData.nodes || [];
     if (nodes.length === 0) {
        return []; // No default queries if graph is empty
     }
     
     const eq = nodes.find(n => (n.entity_type || n.type || '').toUpperCase() === 'EQUIPMENT') || nodes[0];
     const haz = nodes.find(n => (n.entity_type || n.type || '').toUpperCase() === 'HAZARD');
     const sens = nodes.find(n => (n.entity_type || n.type || '').toUpperCase() === 'SENSOR');
     
     return [
        { 
          title: "Topology Query", 
          query: eq ? `What does ${eq.id} connect to?` : "What equipment is in the plant?", 
          icon: <Search size={16}/>, color: "var(--cyan)" 
        },
        { 
          title: "Mitigation Plan", 
          query: haz ? `How do we mitigate ${haz.id}?` : "Are there any unmitigated hazards?", 
          icon: <ShieldAlert size={16}/>, color: "var(--amber)" 
        },
        { 
          title: "Sensor Audit", 
          query: sens ? `What does ${sens.id} monitor?` : "Are all systems properly monitored?", 
          icon: <Activity size={16}/>, color: "var(--violet)" 
        },
        { 
          title: "Hazard Scan", 
          query: "Generate a full risk assessment report.", 
          icon: <AlertTriangle size={16}/>, color: "var(--rose)" 
        }
     ];
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      
      {/* Header */}
      <header style={{
        padding: '1.2rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface)',
        backdropFilter: 'blur(40px) saturate(150%)'
      }}>
        <div style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '-0.5px' }}>
          GraphRAG <span style={{ color: 'var(--cyan)' }}>Intelligence</span>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <Link href={`/compliance?session_id=${currentThreadId || 'default'}`} style={{ textDecoration: 'none' }}>
            <button 
              className="apple-glass-capsule"
              style={{
                padding: '0.6rem 1.2rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontSize: '0.9rem',
                fontWeight: 600
              }}
            >
              <ShieldAlert size={16} color="var(--rose)" />
              Compliance Auditor
            </button>
          </Link>
          <button 
            className="apple-glass-capsule"
            onClick={handleExportReport}
            style={{
              padding: '0.6rem 1.2rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.9rem',
              fontWeight: 600
            }}
          >
            <Download size={16} />
            Export Report
          </button>
        </div>
      </header>

      {/* Main Bento Grid */}
      <main style={{ 
        flex: 1, 
        padding: '1.5rem 2rem', 
        display: 'grid', 
        gridTemplateColumns: '1fr 2fr 1fr', 
        gap: '1.5rem', 
        overflow: 'hidden' 
      }}>
        
        {/* LEFT COLUMN */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', overflowY: 'auto', paddingRight: '0.5rem' }}>
          {/* System Health Widget */}
          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--txt)' }}>
              <Activity size={18} color="var(--emerald)" />
              <h3 style={{ fontSize: '1rem', margin: 0 }}>System Health</h3>
            </div>
            
            <div style={{ display: 'flex', gap: '1rem' }}>
              <div style={{ flex: 1, background: 'transparent', padding: '1rem', borderRadius: '12px', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--txt3)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.5rem' }}>Nodes</div>
                <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--txt)' }}>{(graphData.nodes || []).length}</div>
              </div>
              <div style={{ flex: 1, background: 'var(--glass)', padding: '1rem', borderRadius: '12px', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--txt3)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.5rem' }}>Edges</div>
                <div style={{ fontSize: '1.8rem', fontWeight: 700, color: 'var(--txt)' }}>{(graphData.links || []).length}</div>
              </div>
            </div>
            
            <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)', padding: '0.8rem', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--emerald)', fontSize: '0.85rem' }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--emerald)' }}></div>
              Graph Engine Online & Healthy
            </div>
          </div>

          {/* Active Investigations Widget */}
          <div className="glass-panel" style={{ padding: '1.5rem', flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <button
              onClick={startNewInvestigation}
              className="liquid-btn"
              style={{
                width: '100%',
                padding: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                fontWeight: 600,
                marginBottom: '1.5rem',
                color: 'var(--amber)'
              }}
            >
              <Plus size={16} /> New Investigation
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--txt)', marginBottom: '1rem' }}>
              <Clock size={18} color="var(--violet)" />
              <h3 style={{ fontSize: '1rem', margin: 0 }}>Investigation Logs</h3>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', overflowY: 'auto', flex: 1, paddingRight: '0.5rem' }}>
              {threads.length === 0 ? (
                <div style={{ fontSize: '0.85rem', color: 'var(--txt3)', textAlign: 'center', marginTop: '1rem' }}>No active cases.</div>
              ) : (
                threads.map(t => (
                  <button 
                    key={t.id}
                    className="apple-glass-panel"
                    onClick={() => { setCurrentThreadId(t.id); setMessages(t.messages); setIsLoading(false); }}
                    style={{
                      padding: '1rem',
                      color: 'var(--txt)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.4rem',
                      position: 'relative',
                      border: currentThreadId === t.id ? '1px solid var(--cyan)' : undefined,
                      boxShadow: currentThreadId === t.id ? 'inset 0 4px 10px rgba(255, 255, 255, 0.6), inset 0 -4px 10px rgba(0, 0, 0, 0.05), 0 20px 40px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(2, 132, 199, 0.5)' : undefined
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', paddingRight: '1.5rem' }}>{t.title}</div>
                      <div 
                        className="delete-chat-btn"
                        onClick={(e) => handleDeleteThread(t.id, e)}
                        title="Delete Chat"
                        aria-label={`Delete chat ${t.title}`}
                        style={{ position: 'absolute', right: '0.8rem', top: '0.8rem', color: 'var(--txt3)', cursor: 'pointer', transition: 'color 0.2s' }}
                        onMouseOver={e => e.currentTarget.style.color = 'var(--rose)'}
                        onMouseOut={e => e.currentTarget.style.color = 'var(--txt3)'}
                      >
                        <Trash2 size={14} />
                      </div>
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--txt3)' }}>{t.date} • {t.messages.length} messages</div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* CENTER COLUMN (CHAT) */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          
          {/* Chat Header inside card */}
          <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <SiriOrb state="online" size={32} />
              <span style={{ fontWeight: 600 }}>Graph Assistant</span>
            </div>
            {messages.length > 0 && (
              <button 
                onClick={startNewInvestigation}
                style={{ background: 'transparent', border: 'none', color: 'var(--txt3)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem' }}
              >
                <Plus size={14} /> New Chat
              </button>
            )}
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
            {messages.length === 0 ? (
              <div className="fade-up" style={{ margin: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'center', maxWidth: '600px', width: '100%' }}>
                <SiriOrb state="active" size={80} />
                <h2 style={{ fontSize: '1.5rem', marginTop: '1.5rem', marginBottom: '0.5rem' }}>Ready to Assist</h2>
                <p style={{ color: 'var(--txt3)', fontSize: '0.9rem', marginBottom: '2.5rem' }}>Select a diagnostic template or describe the issue below.</p>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', width: '100%' }}>
                  {isUploading ? (
                    <div style={{ gridColumn: 'span 2', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem', color: 'var(--cyan)' }}>
                      <Loader2 className="animate-spin" size={32} style={{ marginBottom: '1rem' }} />
                      <span style={{ fontSize: '1rem', fontWeight: 600 }}>Building Knowledge Graph...</span>
                      <span style={{ fontSize: '0.85rem', color: 'var(--txt3)', marginTop: '0.5rem', textAlign: 'center' }}>
                        The local LLM is reading your document and extracting entities.<br/>This may take 1-3 minutes depending on your computer's speed.
                      </span>
                    </div>
                  ) : isGeneratingQueries ? (
                    <div style={{ gridColumn: 'span 2', display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                      <AILoadingState 
                        inline={true} 
                        steps={[
                          "Scanning graph for topological anomalies...",
                          "Identifying critical risk vectors...",
                          "Formulating strategic AI queries..."
                        ]} 
                      />
                    </div>
                  ) : getDynamicQueries().length > 0 ? (
                    getDynamicQueries().map((q, idx) => (
                      <button 
                        key={idx}
                        className="liquid-btn"
                        onClick={() => handleSend(q.query)} 
                        style={{ padding: '1rem', textAlign: 'left', borderRadius: '16px' }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: q.color, marginBottom: '0.5rem' }}>
                          {q.icon} <b>{q.title}</b>
                        </div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--txt3)' }}>{q.query}</div>
                      </button>
                    ))
                  ) : (
                    <div style={{ gridColumn: 'span 2', textAlign: 'center', padding: '2rem', color: 'var(--txt3)', fontSize: '0.9rem' }}>
                      <FileText size={24} style={{ marginBottom: '0.5rem', opacity: 0.5 }} />
                      <div>No dataset detected. Please upload a document to begin.</div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div style={{ paddingBottom: '1rem' }}>
                {messages.map((m, i) => (
                  <div key={i} className="fade-up" style={{
                    display: 'flex',
                    justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
                    marginBottom: '1.5rem',
                    gap: '1rem'
                  }}>
                    {m.role === 'assistant' && (
                      <div style={{
                        width: '36px', height: '36px', borderRadius: '50%', flexShrink: 0,
                        background: 'radial-gradient(circle at 30% 30%, #818cf8, #22d3ee, #fb7185)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        boxShadow: '0 4px 10px rgba(34,211,238,.3)'
                      }}><Sparkles size={16} color="white" /></div>
                    )}
                    
                    <div style={{
                      maxWidth: '85%',
                      background: m.role === 'user' ? 'linear-gradient(135deg, var(--cyan), #0284c7)' : 'var(--surface)',
                      color: m.role === 'user' ? '#fff' : 'var(--txt)',
                      borderRadius: m.role === 'user' ? '20px 20px 4px 20px' : '4px 20px 20px 20px',
                      padding: '1rem 1.2rem',
                      boxShadow: 'var(--shadow-sm)',
                      border: m.role === 'user' ? 'none' : '1px solid var(--border)'
                    }}>
                      <p style={{ lineHeight: 1.5, fontSize: '0.95rem', whiteSpace: 'pre-wrap' }}>{m.content}</p>
                      
                      {m.context && (
                        <details style={{ marginTop: '0.8rem', fontSize: '0.8rem', color: 'var(--txt3)' }}>
                          <summary style={{ cursor: 'pointer', outline: 'none' }}>Source Context</summary>
                          <pre style={{ marginTop: '0.5rem', padding: '0.8rem', background: 'var(--surface2)', borderRadius: '8px', overflowX: 'auto', border: '1px solid var(--border)' }}>
                            {m.context}
                          </pre>
                        </details>
                      )}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <AILoadingState />
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Chat Input inside card */}
          <ChatInput 
            isLoading={isLoading}
            isUploading={isUploading}
            uploadStatus={uploadStatus}
            onSend={handleSend}
            onFileUpload={handleFileUpload}
          />
        </div>

        {/* RIGHT COLUMN */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', overflowY: 'auto', paddingLeft: '0.5rem' }}>
          
          {/* Risk Alerts Widget */}
          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--txt)' }}>
              <AlertTriangle size={18} color="var(--rose)" />
              <h3 style={{ fontSize: '1rem', margin: 0 }}>Critical Risk Alerts</h3>
            </div>
            
            {riskData.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                {riskData.map((hazard, idx) => (
                  <div key={idx} style={{ 
                    background: 'var(--glass)', 
                    border: '1px solid rgba(244, 63, 94, 0.2)', 
                    borderLeft: '4px solid var(--rose)',
                    padding: '0.8rem 1rem', 
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{hazard.component}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--txt3)' }}>{hazard.type}</div>
                    </div>
                    <div style={{ color: 'var(--rose)', fontWeight: 700, fontSize: '0.9rem' }}>
                      {hazard.risk_score}%
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: '0.85rem', color: 'var(--txt3)', textAlign: 'center', padding: '1rem' }}>
                No active hazards found.
              </div>
            )}
          </div>

          {/* Database Info Widget */}
          <div className="glass-panel" style={{ padding: '1.5rem', flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--txt)', marginBottom: '1rem' }}>
              <Database size={18} color="var(--amber)" />
              <h3 style={{ fontSize: '1rem', margin: 0 }}>Active Dataset</h3>
            </div>
            
            <div style={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              padding: '1rem',
              borderRadius: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.8rem'
            }}>
              {(graphData.nodes || []).length === 0 ? (
                <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--txt3)' }}>
                  <div style={{ marginBottom: '0.5rem' }}>No datasets uploaded.</div>
                  <div style={{ fontSize: '0.8rem' }}>Upload documents to populate the graph.</div>
                </div>
              ) : (
                <>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                    <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Database size={16} color="var(--amber)" />
                    </div>
                    <div>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Graph Database Active</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--txt3)' }}>Primary Knowledge Base</div>
                    </div>
                  </div>
                  <div style={{ height: '1px', background: 'var(--border)' }}></div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--txt3)' }}>
                    Contains topology data for {(graphData.nodes || []).length} ingested entities.
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </main>

      <style>{`
        .animate-spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .pulse { animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.7; transform: scale(1.1); } 100% { opacity: 1; transform: scale(1); } }
      `}</style>
    </div>
  );
}
