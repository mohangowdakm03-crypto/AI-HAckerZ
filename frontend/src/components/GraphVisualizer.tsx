"use client";
import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

const GraphVisualizer = React.memo(({ data }: { data: any }) => {
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const containerRef = React.useRef<HTMLDivElement>(null);
  const fgRef = React.useRef<any>(null);
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [blastRadius, setBlastRadius] = useState<Set<string>>(new Set());

  const computeBlastRadius = (startNodeId: string) => {
    if (!data || !data.links) return;
    const visited = new Set<string>();
    const queue = [startNodeId];
    
    while (queue.length > 0) {
      const current = queue.shift()!;
      if (!visited.has(current)) {
        visited.add(current);
        const outgoing = data.links.filter((l: any) => {
          const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
          return sourceId === current;
        });
        
        outgoing.forEach((l: any) => {
          const targetId = typeof l.target === 'object' ? l.target.id : l.target;
          queue.push(targetId);
        });
      }
    }
    setBlastRadius(visited);
  };

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight
      });
      
      const handleResize = () => {
        if (containerRef.current) {
          setDimensions({
            width: containerRef.current.clientWidth,
            height: containerRef.current.clientHeight
          });
        }
      };
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
  }, []);

  useEffect(() => {
    if (fgRef.current) {
      // Increase repulsion between nodes to prevent text overlap
      fgRef.current.d3Force('charge').strength(-600);
      // Increase the ideal distance between connected nodes for better spacing
      fgRef.current.d3Force('link').distance(150);
    }
  }, [data]);

  // Map risk score to a color (blue -> amber -> rose) for light theme
  const getRiskColor = (riskScore: number = 0) => {
    if (riskScore > 30) return '#f43f5e'; // High risk (rose)
    if (riskScore > 15) return '#f59e0b'; // Medium risk (amber)
    return '#3b82f6'; // Low risk (blue)
  };

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%' }}>
      <ForceGraph2D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={data}
        nodeId="id"
        nodeLabel="id"
        onNodeClick={(node: any) => {
          if (activeNode === node.id) {
            setActiveNode(null);
            setBlastRadius(new Set());
          } else {
            setActiveNode(node.id);
            computeBlastRadius(node.id);
          }
        }}
        onBackgroundClick={() => {
          setActiveNode(null);
          setBlastRadius(new Set());
        }}
        linkColor={(link: any) => {
          if (!activeNode) return 'rgba(15, 23, 42, 0.15)';
          const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
          const targetId = typeof link.target === 'object' ? link.target.id : link.target;
          if (blastRadius.has(sourceId) && blastRadius.has(targetId)) {
            return 'rgba(244, 63, 94, 0.8)';
          }
          return 'rgba(15, 23, 42, 0.03)';
        }}
        linkWidth={(link: any) => {
          if (!activeNode) return 3;
          const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
          const targetId = typeof link.target === 'object' ? link.target.id : link.target;
          return (blastRadius.has(sourceId) && blastRadius.has(targetId)) ? 5 : 2;
        }}
        linkDirectionalParticles={(link: any) => {
          if (!activeNode) return 2;
          const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
          const targetId = typeof link.target === 'object' ? link.target.id : link.target;
          return (blastRadius.has(sourceId) && blastRadius.has(targetId)) ? 4 : 0;
        }}
        linkDirectionalParticleSpeed={0.005}
        linkDirectionalParticleColor={() => activeNode ? 'rgba(244, 63, 94, 1)' : 'rgba(15, 23, 42, 0.4)'}
        nodeCanvasObject={(node: any, ctx, globalScale) => {
          const label = node.id;
          const risk = node.risk_score || 0;
          
          // Determine size based on risk
          const baseSize = 5;
          const size = baseSize + (risk / 10);
          
          const isHighlighted = activeNode ? blastRadius.has(node.id) : false;
          const isDimmed = activeNode ? !blastRadius.has(node.id) : false;

          // Draw the Node Circle
          ctx.beginPath();
          ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);
          
          if (isDimmed) {
             ctx.fillStyle = 'rgba(15, 23, 42, 0.1)';
          } else if (isHighlighted) {
             ctx.fillStyle = '#f43f5e'; // Highlight path in red
          } else {
             ctx.fillStyle = getRiskColor(risk);
          }
          ctx.fill();
          
          // Add a glow/halo effect for high risk or highlight
          if (isHighlighted || (!activeNode && risk > 20)) {
            ctx.beginPath();
            ctx.arc(node.x, node.y, size + 3, 0, 2 * Math.PI, false);
            ctx.fillStyle = isHighlighted ? 'rgba(244, 63, 94, 0.3)' : getRiskColor(risk) + '40';
            ctx.fill();
          }

          // Draw the Label Text below the node
          const fontSize = 12 / globalScale;
          ctx.font = `500 ${fontSize}px Inter, sans-serif`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'top';
          
          // Background for text for better readability on light theme
          const textWidth = ctx.measureText(label).width;
          ctx.fillStyle = isDimmed ? 'rgba(255,255,255,0.2)' : 'rgba(255, 255, 255, 0.7)';
          
          // Use roundRect if available for softer look
          if (ctx.roundRect) {
             ctx.beginPath();
             ctx.roundRect(node.x - textWidth / 2 - 4, node.y + size + 2, textWidth + 8, fontSize + 4, 4);
             ctx.fill();
          } else {
             ctx.fillRect(node.x - textWidth / 2 - 4, node.y + size + 2, textWidth + 8, fontSize + 4);
          }
          
          ctx.fillStyle = isDimmed ? 'rgba(15, 23, 42, 0.2)' : (isHighlighted ? '#f43f5e' : 'rgba(15, 23, 42, 0.9)'); 
          ctx.fillText(label, node.x, node.y + size + 4);
        }}
        nodePointerAreaPaint={(node: any, color, ctx) => {
          const size = 5 + ((node.risk_score || 0) / 10);
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(node.x, node.y, size + 4, 0, 2 * Math.PI, false);
          ctx.fill();
        }}
      />
    </div>
  );
});

export default GraphVisualizer;
