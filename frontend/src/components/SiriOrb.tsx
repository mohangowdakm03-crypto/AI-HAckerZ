import React from 'react';

interface SiriOrbProps {
  state?: 'idle' | 'active' | 'online';
  size?: number;
}

export default function SiriOrb({ state = 'idle', size = 100 }: SiriOrbProps) {
  let innerColors, outerColors, animationSpeed;
  
  if (state === 'online') {
    innerColors = ['#0ea5e9', '#6366f1', '#10b981']; // Cyan, Violet, Emerald
    outerColors = ['rgba(14,165,233,0.6)', 'rgba(99,102,241,0.6)'];
    animationSpeed = '3s';
  } else if (state === 'active') {
    innerColors = ['#6366f1', '#f43f5e', '#0ea5e9']; // Violet, Rose, Cyan
    outerColors = ['rgba(99,102,241,0.6)', 'rgba(244,63,94,0.6)'];
    animationSpeed = '1.5s';
  } else {
    // Idle state: Deep cosmic blue/violet
    innerColors = ['#1e3a8a', '#312e81', '#0f172a'];
    outerColors = ['rgba(30,58,138,0.6)', 'rgba(49,46,129,0.6)'];
    animationSpeed = '6s';
  }

  // The base container gives the physical shape and shadow
  const containerStyle = {
    position: 'relative' as const,
    width: size,
    height: size,
    margin: '0 auto',
    borderRadius: '50%',
    background: 'rgba(255,255,255,0.1)',
    boxShadow: `
      0 10px 30px rgba(0,0,0,0.1),
      inset 0 0 20px rgba(255,255,255,0.8),
      inset 0 -10px 20px rgba(0,0,0,0.05)
    `,
    backdropFilter: 'blur(10px)',
    transformStyle: 'preserve-3d' as const,
    animation: `orb-float ${animationSpeed} ease-in-out infinite alternate`
  };

  // Fluid inner plasma layers using rotating gradients
  const fluidLayer1 = {
    position: 'absolute' as const,
    inset: '2px',
    borderRadius: '50%',
    background: `linear-gradient(45deg, ${innerColors[0]}, ${innerColors[1]})`,
    filter: 'blur(4px)',
    animation: `spin-slow ${animationSpeed} linear infinite`,
    opacity: 0.9,
    mixBlendMode: 'normal' as const
  };

  const fluidLayer2 = {
    position: 'absolute' as const,
    inset: '2px',
    borderRadius: '50%',
    background: `linear-gradient(-45deg, ${innerColors[1]}, ${innerColors[2]})`,
    filter: 'blur(6px)',
    animation: `spin-reverse ${animationSpeed} linear infinite`,
    opacity: 0.8,
    mixBlendMode: 'overlay' as const
  };
  
  // A moving inner core to give the illusion of 3D depth
  const coreStyle = {
    position: 'absolute' as const,
    inset: '15%',
    borderRadius: '50%',
    background: `radial-gradient(circle at 30% 30%, #fff, ${innerColors[0]})`,
    animation: `core-wobble ${animationSpeed} ease-in-out infinite alternate`,
    boxShadow: `0 0 ${size/3}px ${outerColors[0]}`,
    opacity: 0.9
  };

  // The sharp glass reflection on top
  const glassReflection = {
    position: 'absolute' as const,
    top: '5%',
    left: '10%',
    width: '45%',
    height: '35%',
    background: 'radial-gradient(ellipse at top left, rgba(255,255,255,0.9), rgba(255,255,255,0) 70%)',
    borderRadius: '50%',
    transform: 'rotate(-40deg)',
    zIndex: 10,
    pointerEvents: 'none' as const
  };

  // Subtle bottom ambient reflection
  const ambientReflection = {
    position: 'absolute' as const,
    bottom: '-10%',
    left: '15%',
    width: '70%',
    height: '20%',
    background: `radial-gradient(ellipse at center, ${outerColors[0]}, transparent 70%)`,
    filter: 'blur(8px)',
    opacity: 0.6,
    zIndex: -1
  };

  return (
    <>
      <style>{`
        @keyframes orb-float {
          0% { transform: translateY(0px) scale(1); }
          100% { transform: translateY(-${size * 0.08}px) scale(1.02); }
        }
        @keyframes spin-slow {
          100% { transform: rotate(360deg); }
        }
        @keyframes spin-reverse {
          100% { transform: rotate(-360deg); }
        }
        @keyframes core-wobble {
          0% { transform: translate(-4%, -4%) scale(0.95); }
          100% { transform: translate(4%, 4%) scale(1.05); }
        }
      `}</style>
      <div style={{ position: 'relative', width: size, height: size, margin: '0 auto' }}>
        <div style={containerStyle}>
          <div style={fluidLayer1}></div>
          <div style={fluidLayer2}></div>
          <div style={coreStyle}></div>
          <div style={glassReflection}></div>
        </div>
        <div style={ambientReflection}></div>
      </div>
    </>
  );
}
