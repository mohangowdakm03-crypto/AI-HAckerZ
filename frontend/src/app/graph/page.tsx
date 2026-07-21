"use client";

import React, { useEffect, useState } from 'react';
import { Network, Loader2 } from 'lucide-react';
import GraphVisualizer from '@/components/GraphVisualizer';

export default function GraphPage() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const sessionId = localStorage.getItem('graphrag_active_thread') || 'default';
    fetch(`http://localhost:8000/api/graph-data?session_id=${sessionId}`)
      .then(r => {
        if (!r.ok) throw new Error("Graph Engine Offline");
        return r.json();
      })
      .then(d => setData(d))
      .catch(e => setError(e.message));
  }, []);

  return (
    <div style={{ padding: '2rem', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', marginBottom: '2rem' }}>
        <Network size={24} color="var(--cyan)" />
        <h1 style={{ fontSize: '1.6rem', margin: 0 }}>Knowledge Graph</h1>
      </header>

      <div className="glass-panel" style={{
        flex: 1,
        borderRadius: '24px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}>
        {error ? (
          <div style={{ color: 'var(--rose)' }}>{error}</div>
        ) : !data ? (
          <Loader2 size={40} color="var(--cyan)" className="animate-spin" />
        ) : (
          <div className="fade-up" style={{ width: '100%', height: '100%' }}>
            <GraphVisualizer data={data} />
          </div>
        )}
      </div>
      
      <style>{`
        .animate-spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
