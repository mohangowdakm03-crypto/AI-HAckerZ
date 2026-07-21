"use client";

import React, { useEffect, useState } from 'react';
import { AlertTriangle, Loader2 } from 'lucide-react';

export default function RiskPage() {
  const [hazards, setHazards] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const sessionId = localStorage.getItem('graphrag_active_thread') || 'default';
    fetch(`http://localhost:8000/api/risk?session_id=${sessionId}`)
      .then(r => r.json())
      .then(d => {
        setHazards(d.hazards || []);
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
        <AlertTriangle size={24} color="var(--rose)" />
        <h1 style={{ fontSize: '1.6rem', margin: 0 }}>Risk Dashboard</h1>
      </header>
      
      <div className="glass-panel" style={{ flex: 1, borderRadius: '24px', padding: '2rem', overflowY: 'auto' }}>
        <h2 style={{ color: 'var(--txt)', marginBottom: '1.5rem', fontSize: '1.2rem' }}>Critical Centrality Hazards</h2>
        <p style={{ color: 'var(--txt3)', marginBottom: '2rem' }}>Nodes with the highest degree centrality pose the greatest risk to systemic failure.</p>
        
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
            <Loader2 size={40} color="var(--rose)" className="animate-spin" />
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {hazards.map((hazard, i) => (
              <div key={i} style={{ 
                background: 'rgba(251,113,133,0.05)', 
                border: '1px solid rgba(251,113,133,0.2)', 
                padding: '1.5rem', 
                borderRadius: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '2rem'
              }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'rgba(251,113,133,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--rose)', fontWeight: 'bold' }}>
                  #{i + 1}
                </div>
                
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--txt)' }}>{hazard.component}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--rose)', marginTop: '0.3rem' }}>Type: {hazard.type}</div>
                </div>
                
                <div style={{ width: '200px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.85rem', color: 'var(--txt2)' }}>
                    <span>Risk Score</span>
                    <span style={{ color: 'var(--rose)', fontWeight: 'bold' }}>{hazard.risk_score}%</span>
                  </div>
                  <div style={{ width: '100%', height: '6px', background: 'var(--glass)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${hazard.risk_score}%`, height: '100%', background: 'var(--rose)', borderRadius: '3px' }}></div>
                  </div>
                </div>
              </div>
            ))}
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
