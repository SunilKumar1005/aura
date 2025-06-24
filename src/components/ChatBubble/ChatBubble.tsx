import React, { useEffect, useRef, useState } from 'react';
import './ChatBubble.css';
import botIcon from '../../assets/bot_icon.gif';

const BUBBLE_SIZE = 80;
const RING_SIZE = 240; // Large to avoid clipping
const PLASMA_BLOBS = 5;
const PLASMA_COLORS = [
  'rgba(0,255,255,0.25)',
  'rgba(162,89,255,0.22)',
  'rgba(255,0,255,0.18)',
  'rgba(0,255,247,0.18)',
  'rgba(255,97,246,0.15)'
];
const CYCLE_TEXTS = [
  { text: '5C', color: '#00fff7' },
  { text: 'Aura AI', color: '#00fff7' },
  { text: 'Chat Bot', color: '#00fff7' },
];

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

function lerpAngle(a: number, b: number, t: number) {
  let diff = b - a;
  while (diff > Math.PI) diff -= 2 * Math.PI;
  while (diff < -Math.PI) diff += 2 * Math.PI;
  return a + diff * t;
}

interface ChatBubbleProps {
  onClick?: () => void;
}

const ChatBubble: React.FC<ChatBubbleProps> = ({ onClick }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const neonRingRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [mouse, setMouse] = useState<{x: number, y: number}>({x: window.innerWidth/2, y: window.innerHeight/2});
  const [textIndex, setTextIndex] = useState(0);
  const [fade, setFade] = useState(true);

  // Persist pullAngle and bulgeLen across frames
  const pullAngleRef = useRef(0);
  const bulgeLenRef = useRef(0);

  // Cycle the center text with fade animation
  useEffect(() => {
    const interval = setInterval(() => {
      setFade(false);
      setTimeout(() => {
        setTextIndex((prev) => (prev + 1) % CYCLE_TEXTS.length);
        setFade(true);
      }, 350); // fade out duration
    }, 1800);
    return () => clearInterval(interval);
  }, []);

  // Animate floating plasma blobs (no pointer attraction)
  useEffect(() => {
    let animationId: number;
    let t = 0;
    const phases = Array.from({length: PLASMA_BLOBS}, (_, i) => Math.random() * 1000);
    const speeds = Array.from({length: PLASMA_BLOBS}, (_, i) => 0.7 + Math.random() * 0.7);
    const radii = Array.from({length: PLASMA_BLOBS}, (_, i) => 16 + Math.random() * 12);
    const draw = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (let i = 0; i < PLASMA_BLOBS; i++) {
        let cx = BUBBLE_SIZE/2 + Math.sin(t * speeds[i] + phases[i]) * 16 + Math.cos(t * 0.7 + i) * 8;
        let cy = BUBBLE_SIZE/2 + Math.cos(t * speeds[i] + phases[i]) * 16 + Math.sin(t * 0.9 + i) * 8;
        const r = radii[i] + Math.sin(t * 1.2 + i) * 4 + Math.cos(t * 0.7 + i) * 2;
        ctx.save();
        ctx.globalAlpha = 0.7;
        ctx.beginPath();
        for (let a = 0; a <= Math.PI * 2 + 0.1; a += Math.PI/24) {
          const edge = r + Math.sin(a * 3 + t * 1.5 + i) * 3 + Math.cos(a * 2.2 + t * 0.7 + i) * 2;
          const x = cx + Math.cos(a) * edge;
          const y = cy + Math.sin(a) * edge;
          if (a === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fillStyle = PLASMA_COLORS[i % PLASMA_COLORS.length];
        ctx.shadowColor = PLASMA_COLORS[i % PLASMA_COLORS.length];
        ctx.shadowBlur = 16;
        ctx.fill();
        ctx.restore();
      }
      t += 0.018;
      animationId = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(animationId);
  }, []);

  // Neon plasma ring animation with sharp bulge toward mouse, bulge reduces as mouse approaches bubble edge
  useEffect(() => {
    let animationId: number;
    let t = 0;
    let targetAngle = pullAngleRef.current;
    let targetBulgeLen = bulgeLenRef.current;
    const drawRing = () => {
      const canvas = neonRingRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.save();
      // Always center the ring on the bubble center
      const bubbleRect = containerRef.current?.getBoundingClientRect();
      let bubbleCenterX = 0;
      let bubbleCenterY = 0;
      if (bubbleRect) {
        bubbleCenterX = bubbleRect.left + BUBBLE_SIZE/2;
        bubbleCenterY = bubbleRect.top + BUBBLE_SIZE/2;
      }
      // Draw ring at center of canvas
      ctx.translate(RING_SIZE/2, RING_SIZE/2);
      const baseR = 85;
      // Calculate mouse distance/angle from bubble center
      let bulgeRatio = 0;
      let dx = mouse.x - bubbleCenterX;
      let dy = mouse.y - bubbleCenterY;
      let dist = Math.sqrt(dx*dx + dy*dy);
      targetAngle = Math.atan2(dy, dx);
      if (dist <= BUBBLE_SIZE/2) {
        bulgeRatio = Math.max(0, (dist - (BUBBLE_SIZE/2 - 16)) / 16);
      } else {
        bulgeRatio = Math.min(1, (dist - BUBBLE_SIZE/2) / 40 + 1);
      }
      targetBulgeLen = lerp(0, 36, bulgeRatio);
      // Smoothly interpolate pullAngle and bulgeLen
      pullAngleRef.current = lerpAngle(pullAngleRef.current, targetAngle, 0.18);
      bulgeLenRef.current = lerp(bulgeLenRef.current, targetBulgeLen, 0.18);
      // Create a gradient for the ring
      const grad = ctx.createConicGradient(0, 0, 0);
      grad.addColorStop(0, '#00fff7');
      grad.addColorStop(0.25, '#a259ff');
      grad.addColorStop(0.5, '#ff3cac');
      grad.addColorStop(0.75, '#00f0ff');
      grad.addColorStop(1, '#00fff7');
      ctx.strokeStyle = grad;
      ctx.shadowColor = '#00fff7';
      ctx.shadowBlur = 16;
      ctx.lineWidth = 4.5;
      ctx.globalAlpha = 0.85;
      ctx.beginPath();
      const spikeWidth = 0.18;
      for (let a = 0; a <= Math.PI * 2 + 0.01; a += Math.PI/96) {
        let r = baseR + Math.sin(a * 6 + t * 2) * 2 + Math.cos(a * 3 + t * 1.2) * 1.5;
        let diff = a - pullAngleRef.current;
        if (diff > Math.PI) diff -= 2 * Math.PI;
        if (diff < -Math.PI) diff += 2 * Math.PI;
        if (bulgeLenRef.current > 0 && Math.abs(diff) < spikeWidth) {
          r += (1 - Math.abs(diff)/spikeWidth) * bulgeLenRef.current;
        }
        const x = Math.cos(a) * r;
        const y = Math.sin(a) * r;
        if (a === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.stroke();
      ctx.restore();
      t += 0.018;
      animationId = requestAnimationFrame(drawRing);
    };
    drawRing();
    return () => cancelAnimationFrame(animationId);
  }, [mouse]);

  // Mouse move tracking (global)
  useEffect(() => {
    const handleMove = (e: MouseEvent) => {
      setMouse({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMove);
    return () => {
      window.removeEventListener('mousemove', handleMove);
    };
  }, []);

  return (
    <div
      className="chat-bubble-container"
      ref={containerRef}
      style={{ 
        position: 'fixed',
        bottom: '30px',
        right: '30px',
        width: '80px',
        height: '80px',
        zIndex: 3000, // Higher than backdrop
        overflow: 'visible',
        background: 'none',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        pointerEvents: 'auto' // Ensure container is interactive
      }}
    >
      {/* Neon plasma ring canvas (moved out of .chat-bubble) */}
      <canvas
        ref={neonRingRef}
        width={RING_SIZE}
        height={RING_SIZE}
        className="plasma-neon-ring-canvas"
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          pointerEvents: 'none',
          zIndex: 15
        }}
      />
      {/* Main interactive bubble */}
      <div 
        className="chat-bubble"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={onClick}
        style={{
          position: 'relative',
          width: '80px',
          height: '80px',
          borderRadius: '50%',
          cursor: 'pointer',
          zIndex: 3000, // Same as container
          background: 'transparent',
          pointerEvents: 'auto' // Ensure bubble is interactive
        }}
      >
        {/* Visual elements with pointer-events: none */}
        <div style={{ 
          position: 'absolute', 
          width: '100%', 
          height: '100%', 
          pointerEvents: 'none',
          zIndex: 1 // Lower than bubble
        }}>
          {/* Plasma orb */}
          <div className="plasma-orb" style={{ pointerEvents: 'none' }}>
            <div className="plasma-core"></div>
            <div className="plasma-glow"></div>
            <div className="plasma-trail"></div>
            <canvas
              ref={canvasRef}
              width={BUBBLE_SIZE}
              height={BUBBLE_SIZE}
              className="plasma-blobs-canvas"
              style={{ pointerEvents: 'none' }}
            />
          </div>
        </div>
        {/* Text and wrapper above GIF */}
        <div className="chat-bubble-wrapper" style={{ pointerEvents: 'none' }}>
          {isHovered && (
            <img 
              src={botIcon} 
              alt="AI Bot" 
              className="bot-gif-full"
              style={{ pointerEvents: 'none' }}
            />
          )}
          <div className={`bubble-center-text${fade ? ' fade-in' : ' fade-out'}`}
            style={{ 
              color: CYCLE_TEXTS[textIndex].color,
              pointerEvents: 'none'
            }}>
            {CYCLE_TEXTS[textIndex].text}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatBubble; 