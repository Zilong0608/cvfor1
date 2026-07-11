import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';

export const PopCat = ({ isDark }: { isDark: boolean }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number }>>([]);
  const [clickCount, setClickCount] = useState(0);

  const handleClick = () => {
    if (isOpen) return; // Prevent double trigger
    setIsOpen(true);
    setClickCount(prev => prev + 1);
    
    const newParticle = { 
        id: Date.now(), 
        x: Math.random() * 20 - 10, 
        y: 0 
    };
    setParticles(prev => [...prev, newParticle]);

    // Close mouth quickly
    setTimeout(() => {
        setIsOpen(false);
    }, 150);

    // Cleanup particle
    setTimeout(() => {
        setParticles(prev => prev.filter(p => p.id !== newParticle.id));
    }, 1000);
  };

  return (
    <div 
        className="relative w-20 h-20 -mb-2 -ml-2 flex items-end justify-center cursor-pointer pointer-events-auto select-none group"
        onMouseDown={handleClick}
        onTouchStart={(e) => { e.preventDefault(); handleClick(); }} 
    >
        {/* Click Counter/Particles */}
        <AnimatePresence>
            {particles.map((p) => (
                <motion.div
                    key={p.id}
                    initial={{ opacity: 1, y: -20, x: p.x, scale: 0.5 }}
                    animate={{ opacity: 0, y: -60, scale: 1.2 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className={`absolute -top-8 left-1/2 font-mono font-bold text-sm pointer-events-none ${isDark ? 'text-white' : 'text-black'}`}
                    style={{ marginLeft: '-0.5rem' }} // Center text
                >
                    +1
                </motion.div>
            ))}
        </AnimatePresence>

        {/* Tech PopCat SVG - Sitting, Looking Up, Side Face */}
        <svg 
            viewBox="0 0 100 110" 
            className={`w-full h-full transition-all duration-100 drop-shadow-sm group-hover:drop-shadow-md ${isDark ? 'stroke-white/90' : 'stroke-black/90'}`}
            style={{ strokeWidth: '2px', fill: 'transparent', strokeLinecap: 'round', strokeLinejoin: 'round' }}
        >
             {/* --- Tail (Side/Behind) --- */}
             <path d="M 78 90 Q 95 90 95 70 Q 92 60 88 65" className="opacity-60" />

             {/* --- Body (Sitting) --- */}
             <path d="M 32 75 Q 20 90 25 105 L 75 105 Q 80 90 70 75" />
             
             {/* Front Paws (Planted) */}
             <path d="M 40 105 L 40 85" />
             <path d="M 56 105 L 56 85" />
             <path d="M 36 105 L 44 105" />
             <path d="M 52 105 L 60 105" />

             {/* --- Head (Tilted UP & Turned Right) --- */}
             <g transform="rotate(-10, 50, 60) translate(0, -5)">
                {/* Head Contour */}
                <path d="M 25 65 Q 15 45 30 35 L 22 20 L 42 30 Q 55 25 65 30 L 85 20 L 78 35 Q 90 50 80 70 Q 55 80 25 65" />
                
                {/* Ear Details */}
                <path d="M 22 20 L 32 32" className="opacity-40" />
                <path d="M 85 20 L 75 32" className="opacity-40" />

                {/* Eyes (Looking Up/Forward relative to head tilt) */}
                <circle cx="40" cy="50" r="3.5" fill={isDark ? "white" : "currentColor"} stroke="none" />
                <circle cx="68" cy="50" r="3.5" fill={isDark ? "white" : "currentColor"} stroke="none" />

                {/* Nose (Higher) */}
                <path d="M 52 58 L 56 58 L 54 61 Z" fill="currentColor" stroke="none" opacity="0.6" />

                {/* Whiskers (Angled) */}
                <g className="opacity-60">
                    <path d="M 25 55 L 10 50" />
                    <path d="M 25 60 L 10 62" />
                    <path d="M 80 55 L 95 50" />
                    <path d="M 80 60 L 95 62" />
                </g>

                {/* Mouth Logic */}
                {isOpen ? (
                    <g>
                        {/* OPEN: Angled Big O */}
                        <ellipse cx="54" cy="72" rx="18" ry="16" transform="rotate(10, 54, 72)" className="fill-current opacity-10" />
                        <ellipse cx="54" cy="72" rx="18" ry="16" transform="rotate(10, 54, 72)" />
                        
                        {/* Dropped Chin Line for Open Mouth */}
                        <path d="M 35 75 Q 54 95 75 78" className="opacity-50" />
                    </g>
                ) : (
                    <g>
                        {/* CLOSED */}
                        <path d="M 46 65 Q 54 68 62 65" strokeWidth="2" />
                    </g>
                )}
             </g>

             {/* Neck Connection (Visual Fix) */}
             <path d="M 35 78 Q 50 85 65 78" className="opacity-0" /> {/* Spacer */}
        </svg>
        
        {/* Click Count Display */}
        {clickCount > 0 && (
            <div className={`absolute -right-2 top-0 text-[10px] font-mono opacity-40 ${isDark ? 'text-white' : 'text-black'}`}>
                {clickCount}
            </div>
        )}
    </div>
  );
};
