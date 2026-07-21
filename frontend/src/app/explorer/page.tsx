"use client";

import React, { useEffect, useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

export default function ExplorerPage() {
  const [nodes, setNodes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const sessionId = localStorage.getItem('graphrag_active_thread') || 'default';
    fetch(`http://localhost:8000/api/explorer?session_id=${sessionId}`)
      .then(r => r.json())
      .then(d => {
        setNodes(d.nodes || []);
        setLoading(false);
      })
      .catch(e => {
        console.error(e);
        setLoading(false);
      });
  }, []);

  return (
    <div style={{ padding: '2rem', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', marginBottom: '2rem' }}>
        <Search size={24} color="var(--cyan)" />
        <h1 style={{ fontSize: '1.6rem', margin: 0 }}>Node Explorer</h1>
      </header>
      
      <div className="glass-panel" style={{ flex: 1, borderRadius: '24px', padding: '1.5rem', overflowY: 'auto' }}>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <Loader2 size={40} color="var(--cyan)" className="animate-spin" />
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-lit)' }}>
                <th style={{ padding: '1rem', color: 'var(--txt2)' }}>ID</th>
                <th style={{ padding: '1rem', color: 'var(--txt2)' }}>Type</th>
                <th style={{ padding: '1rem', color: 'var(--txt2)' }}>Connections</th>
                <th style={{ padding: '1rem', color: 'var(--txt2)' }}>Attributes</th>
              </tr>
            </thead>
            <tbody>
              {nodes.map((node, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--border)', background: i % 2 === 0 ? 'var(--glass)' : 'transparent' }}>
                  <td style={{ padding: '1rem', fontWeight: 'bold', color: 'var(--cyan)' }}>{node.id}</td>
                  <td style={{ padding: '1rem' }}>
                    <span style={{ background: 'var(--violet-glow)', color: 'var(--violet)', padding: '4px 8px', borderRadius: '4px', fontSize: '0.85rem' }}>
                      {node.type}
                    </span>
                  </td>
                  <td style={{ padding: '1rem', color: 'var(--txt)' }}>{node.connections}</td>
                  <td style={{ padding: '1rem', fontSize: '0.85rem', color: 'var(--txt2)' }}>
                    <pre style={{ margin: 0 }}>{JSON.stringify(node.attributes, null, 2)}</pre>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      <style>{`
        .animate-spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
