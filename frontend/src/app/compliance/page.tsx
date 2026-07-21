"use client";

import React, { useEffect, useState } from 'react';
import { ShieldAlert, Loader2, FileCheck2, AlertTriangle, ArrowLeft, Printer } from 'lucide-react';
import Link from 'next/link';

export default function CompliancePage() {
  const [violations, setViolations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const sessionId = localStorage.getItem('graphrag_active_thread') || 'default';

    fetch(`http://localhost:8000/api/compliance?session_id=${sessionId}`)
      .then(r => {
        if (!r.ok) throw new Error("Compliance Engine Offline");
        return r.json();
      })
      .then(d => {
        setViolations(d.violations || []);
        setLoading(false);
      })
      .catch(e => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* Header */}
      <header style={{
        padding: '1.2rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid var(--border)',
        background: 'rgba(255,255,255,0.4)',
        backdropFilter: 'blur(20px)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Link href="/" style={{ color: 'var(--txt3)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ArrowLeft size={18} /> Back to Dashboard
          </Link>
          <div style={{ width: '1px', height: '24px', background: 'var(--border)' }}></div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '-0.5px', display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
            <ShieldAlert color="var(--rose)" size={22} />
            Compliance <span style={{ color: 'var(--rose)' }}>Auto-Auditor</span>
          </div>
        </div>
        
        <button 
          className="glass-panel"
          onClick={() => window.print()}
          style={{
            padding: '0.6rem 1rem',
            color: 'var(--txt)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.85rem',
            transition: 'all 0.2s ease',
            borderRadius: '20px'
          }}
        >
          <Printer size={16} />
          Print OSHA Report
        </button>
      </header>

      <main style={{ flex: 1, padding: '2rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <div style={{ maxWidth: '900px', width: '100%', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          <div className="glass-panel" style={{ padding: '2rem', borderRadius: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.5rem', marginBottom: '0.5rem' }}>Automated Gap Analysis</h2>
              <p style={{ color: 'var(--txt3)', margin: 0 }}>Scanning Knowledge Graph for unmonitored equipment and unmitigated hazards.</p>
            </div>
            <div style={{ background: 'rgba(244, 63, 94, 0.1)', color: 'var(--rose)', padding: '1rem 1.5rem', borderRadius: '12px', textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 700, lineHeight: 1 }}>{loading ? '-' : violations.length}</div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, marginTop: '0.2rem', letterSpacing: '0.5px' }}>VIOLATIONS FOUND</div>
            </div>
          </div>

          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
              <Loader2 size={40} color="var(--rose)" className="animate-spin" />
            </div>
          ) : error ? (
            <div style={{ color: 'var(--rose)', textAlign: 'center', padding: '2rem' }}>{error}</div>
          ) : violations.length === 0 ? (
            <div className="glass-panel fade-up" style={{ padding: '4rem', textAlign: 'center', borderRadius: '16px' }}>
              <FileCheck2 size={60} color="var(--emerald)" style={{ margin: '0 auto 1rem' }} />
              <h3 style={{ fontSize: '1.4rem', color: 'var(--emerald)', marginBottom: '0.5rem' }}>100% Compliant</h3>
              <p style={{ color: 'var(--txt3)' }}>All equipment is monitored and all hazards are mitigated by active procedures.</p>
            </div>
          ) : (
            <div className="fade-up" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {violations.map((v, i) => (
                <div key={i} className="glass-panel" style={{ 
                  padding: '1.5rem', 
                  borderRadius: '12px',
                  borderLeft: v.severity === 'Critical' ? '4px solid var(--rose)' : '4px solid var(--amber)',
                  display: 'flex',
                  gap: '1.5rem'
                }}>
                  <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: v.severity === 'Critical' ? 'rgba(244,63,94,0.1)' : 'rgba(245,158,11,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <AlertTriangle size={24} color={v.severity === 'Critical' ? 'var(--rose)' : 'var(--amber)'} />
                  </div>
                  
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.8rem' }}>
                      <div>
                        <h4 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--txt)' }}>{v.component}</h4>
                        <div style={{ color: v.severity === 'Critical' ? 'var(--rose)' : 'var(--amber)', fontWeight: 600, fontSize: '0.85rem', marginTop: '0.2rem' }}>{v.type}</div>
                      </div>
                      <div style={{ background: 'var(--bg)', border: '1px solid var(--border)', padding: '0.4rem 0.8rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600, color: 'var(--txt3)' }}>
                        {v.citation}
                      </div>
                    </div>
                    <p style={{ margin: 0, color: 'var(--txt3)', fontSize: '0.95rem', lineHeight: 1.5 }}>
                      {v.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}

        </div>
      </main>
      
      <style>{`
        .animate-spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
