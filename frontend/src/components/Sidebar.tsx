"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MessageSquare, Network, Search, AlertTriangle, FileText } from 'lucide-react';
import SiriOrb from './SiriOrb';

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { name: 'AI Chat', path: '/', icon: <MessageSquare size={18} /> },
    { name: 'Graph', path: '/graph', icon: <Network size={18} /> },
    { name: 'Explorer', path: '/explorer', icon: <Search size={18} /> },
    { name: 'Risk', path: '/risk', icon: <AlertTriangle size={18} /> },
    { name: 'Contract', path: '/contract', icon: <FileText size={18} /> },
  ];

  return (
    <div className="apple-glass-panel" style={{
      width: '260px',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      padding: '2rem 1rem',
      flexShrink: 0,
      borderRadius: '0',
      borderTop: 'none',
      borderBottom: 'none',
      borderLeft: 'none'
    }}>
      <div style={{ marginBottom: '2.5rem', textAlign: 'center' }}>
        <SiriOrb state="idle" size={56} />
        <div style={{ marginTop: '1rem', fontWeight: 600, color: 'var(--txt)', fontSize: '0.95rem' }}>AI-HackerZ</div>
        <div style={{ fontSize: '0.7rem', color: 'var(--txt3)', marginTop: '0.2rem' }}>GraphRAG Control Panel</div>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {links.map((link) => {
          const isActive = pathname === link.path;
          return (
            <Link key={link.path} href={link.path} 
              className={isActive ? 'apple-glass-capsule' : ''}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.8rem',
                padding: '0.7rem 1rem',
                borderRadius: '100px',
                color: isActive ? 'var(--txt)' : 'var(--txt2)',
                background: isActive ? undefined : 'transparent',
                textDecoration: 'none',
                fontSize: '0.9rem',
                fontWeight: isActive ? 600 : 500,
                transition: 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
              }}
              onMouseOver={!isActive ? (e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
                e.currentTarget.style.transform = 'translateY(-1px) scale(1.01)';
              } : undefined}
              onMouseOut={!isActive ? (e) => {
                e.currentTarget.style.background = 'transparent';
                e.currentTarget.style.transform = 'translateY(0) scale(1)';
              } : undefined}
            >
              {link.icon}
              {link.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
