"use client";

import React, { useEffect, useState } from 'react';
import { FileText, Loader2 } from 'lucide-react';

export default function ContractPage() {
  const [contract, setContract] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // In a real scenario, this would fetch the actual semantic contract applied to the graph
    // We can fetch the raw graph data and show it as the contract
    const sessionId = localStorage.getItem('graphrag_active_thread') || 'default';
    fetch(`http://localhost:8000/api/graph-data?session_id=${sessionId}`)
      .then(r => r.json())
      .then(d => {
        setContract(d);
        setLoading(false);
      })
      .catch(e => {
        setError("Failed to load contract");
        setLoading(false);
      });
  }, []);

  return (
    <div style={{ padding: '2rem', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', marginBottom: '2rem' }}>
        <FileText size={24} color="var(--amber)" />
        <h1 style={{ fontSize: '1.6rem', margin: 0 }}>Data Contract</h1>
      </header>
      
      <div className="glass-panel" style={{ flex: 1, borderRadius: '16px', padding: '1rem', overflowY: 'auto' }}>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <Loader2 size={40} color="var(--amber)" className="animate-spin" />
          </div>
        ) : (
          <pre style={{ margin: 0, color: 'var(--amber)', fontSize: '0.85rem', fontFamily: "'JetBrains Mono', monospace" }}>
            {JSON.stringify(contract, null, 2)}
          </pre>
        )}
      </div>
      <style>{`
        .animate-spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
