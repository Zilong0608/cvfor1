import React, { useEffect, useState } from 'react';
import { motion, useAnimation } from 'motion/react';

// --- SUB-COMPONENTS (LARGE SCALE PRECISION GEOMETRY) ---

// 1. Giant Precision Gear
const GiantGear = ({ 
    size = 600, 
    x = "-20%", 
    y = "20%", 
    duration = 60, 
    direction = 1,
    opacity = 0.2,
    theme = 'light'
}: any) => {
    return (
        <div 
            className="absolute flex items-center justify-center pointer-events-none z-0"
            style={{ 
                width: size, 
                height: size, 
                left: x, 
                top: y, 
                opacity: opacity 
            }}
        >
            <motion.div
                animate={{ rotate: 360 * direction }}
                transition={{ duration: duration, repeat: Infinity, ease: "linear" }}
                className={`absolute inset-0 border-[2px] border-dashed rounded-full ${theme === 'dark' ? 'border-white/70' : 'border-black/70'}`}
            />
            <motion.div
                animate={{ rotate: -360 * direction }}
                transition={{ duration: duration * 1.5, repeat: Infinity, ease: "linear" }}
                className={`absolute inset-8 border-[1px] rounded-full ${theme === 'dark' ? 'border-white/50' : 'border-black/50'}`}
            />
             <motion.div
                animate={{ rotate: 360 * direction }}
                transition={{ duration: duration * 0.5, repeat: Infinity, ease: "linear" }}
                className="absolute inset-[-20px] rounded-full"
            >
                <div className={`absolute top-0 left-1/2 w-full h-full -translate-x-1/2 border-t-[3px] rounded-full ${theme === 'dark' ? 'border-white/40' : 'border-black/40'}`} style={{ clipPath: 'polygon(0 0, 100% 0, 100% 30%, 0 30%)', transform: 'rotate(45deg)' }}></div>
                <div className={`absolute top-0 left-1/2 w-full h-full -translate-x-1/2 border-b-[3px] rounded-full ${theme === 'dark' ? 'border-white/40' : 'border-black/40'}`} style={{ clipPath: 'polygon(0 70%, 100% 70%, 100% 100%, 0 100%)', transform: 'rotate(45deg)' }}></div>
            </motion.div>
             <motion.div
                animate={{ rotate: 360 * direction }}
                transition={{ duration: duration, repeat: Infinity, ease: "linear" }}
                className="absolute inset-0 rounded-full"
            >
                {Array.from({ length: 24 }).map((_, i) => (
                    <div 
                        key={i} 
                        className={`absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 ${i % 3 === 0 ? 'w-[3px] h-6' : 'w-[1px] h-3'} ${theme === 'dark' ? 'bg-white/60' : 'bg-black/60'}`}
                        style={{ transform: `rotate(${i * 15}deg) translateY(-${size/2}px)` }} 
                    />
                ))}
            </motion.div>
        </div>
    );
};

// 2. Wireframe Sphere
const WireframeSphere = ({ size = 500, x = "80%", y = "60%", duration = 40, opacity = 0.25, theme = 'light' }: any) => (
     <div 
        className="absolute flex items-center justify-center pointer-events-none"
        style={{ width: size, height: size, left: x, top: y, opacity: opacity }}
     >
        <motion.div 
             animate={{ rotate: 360 }}
             transition={{ duration: duration, repeat: Infinity, ease: "linear" }}
             className={`absolute inset-0 rounded-full border-[2px] ${theme === 'dark' ? 'border-white/50' : 'border-black/50'}`}
        />
        <motion.div 
             animate={{ rotate: -360 }}
             transition={{ duration: duration * 0.8, repeat: Infinity, ease: "linear" }}
             className={`absolute inset-4 rounded-full border scale-x-[0.4] ${theme === 'dark' ? 'border-white/30' : 'border-black/30'}`}
        />
        <motion.div 
             animate={{ rotate: 360 }}
             transition={{ duration: duration * 1.2, repeat: Infinity, ease: "linear" }}
             className={`absolute inset-[-10%] rounded-full border-[1px] scale-y-[0.3] rotate-45 ${theme === 'dark' ? 'border-white/20' : 'border-black/20'}`}
        >
             <div className={`absolute top-0 left-1/2 w-3 h-3 rounded-full -translate-x-1/2 -translate-y-1/2 shadow-sm ${theme === 'dark' ? 'bg-white/60 shadow-white/20' : 'bg-black/60 shadow-black/20'}`}></div>
        </motion.div>
        <motion.div 
             animate={{ rotate: 360 }}
             transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
             className="absolute inset-0 rounded-full overflow-hidden opacity-30"
        >
            <div className={`w-1/2 h-full bg-gradient-to-r origin-right ml-[50%] ${theme === 'dark' ? 'from-transparent to-white/10' : 'from-transparent to-black/10'}`}></div>
        </motion.div>
     </div>
);

// Crosshair Overlay
const CrosshairOverlay = ({ theme }: { theme: string }) => (
    <div className="absolute inset-0 pointer-events-none z-0">
        <div className={`absolute left-1/2 top-0 bottom-0 w-[1px] ${theme === 'dark' ? 'bg-white/10' : 'bg-black/10'}`}></div>
        <div className={`absolute top-1/2 left-0 right-0 h-[1px] ${theme === 'dark' ? 'bg-white/10' : 'bg-black/10'}`}></div>
        <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] border rounded-full ${theme === 'dark' ? 'border-white/5' : 'border-black/5'}`}></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4">
             <div className={`absolute top-0 left-1/2 -translate-x-1/2 w-[1px] h-full ${theme === 'dark' ? 'bg-white/40' : 'bg-black/40'}`}></div>
             <div className={`absolute top-1/2 left-0 -translate-y-1/2 w-full h-[1px] ${theme === 'dark' ? 'bg-white/40' : 'bg-black/40'}`}></div>
        </div>
    </div>
);

// Flowing Data Stream
const FlowingDataStream = ({ top = "50%", theme }: { top?: string, theme: string }) => (
    <div className={`absolute left-0 right-0 h-[1px] pointer-events-none overflow-hidden ${theme === 'dark' ? 'bg-white/10' : 'bg-black/10'}`} style={{ top }}>
        <motion.div 
            animate={{ x: ["-100%", "100%"] }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
            className={`absolute top-0 left-0 w-[20%] h-full bg-gradient-to-r from-transparent via-transparent to-transparent ${theme === 'dark' ? 'via-white/40' : 'via-black/40'}`}
        />
    </div>
);

// Gyro Scope
const GyroScope = ({ theme }: { theme: string }) => {
  return (
    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] pointer-events-none opacity-[0.08] select-none z-0">
      <motion.div 
        animate={{ rotate: -360 }}
        transition={{ duration: 120, repeat: Infinity, ease: "linear" }}
        className={`absolute inset-0 border rounded-full border-dashed ${theme === 'dark' ? 'border-white/20' : 'border-black/20'}`}
      />
      <motion.div 
        animate={{ rotate: 360, scale: [0.95, 1.05, 0.95] }}
        transition={{ 
            rotate: { duration: 60, repeat: Infinity, ease: "linear" },
            scale: { duration: 10, repeat: Infinity, ease: "easeInOut" }
        }}
        className={`absolute inset-[10%] border-[0.5px] rounded-full ${theme === 'dark' ? 'border-white/30' : 'border-black/30'}`}
      >
          <div className={`absolute top-0 left-1/2 w-2 h-2 rounded-full -translate-x-1/2 -translate-y-1/2 ${theme === 'dark' ? 'bg-white' : 'bg-black'}`}></div>
      </motion.div>
      <motion.div 
        animate={{ rotate: 360 }}
        transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
        className={`absolute inset-[25%] rounded-full border ${theme === 'dark' ? 'border-white/10' : 'border-black/10'}`}
      >
          <div className={`absolute inset-[-1px] border-t-[20px] border-transparent rounded-full rotate-45 ${theme === 'dark' ? 'border-t-white/5' : 'border-t-black/5'}`}></div>
          <div className={`absolute inset-[-1px] border-b-[20px] border-transparent rounded-full rotate-45 ${theme === 'dark' ? 'border-b-white/5' : 'border-b-black/5'}`}></div>
      </motion.div>
       <div className="absolute inset-0 flex items-center justify-center">
            <div className={`w-[1px] h-[100px] ${theme === 'dark' ? 'bg-white/20' : 'bg-black/20'}`}></div>
            <div className={`h-[1px] w-[100px] ${theme === 'dark' ? 'bg-white/20' : 'bg-black/20'}`}></div>
       </div>
    </div>
  );
};

// Silk Wave
const SilkWave = ({ delay, yOffset, opacity, theme }: { delay: number, yOffset: number, opacity: number, theme: string }) => (
    <motion.div
        initial={{ x: "-100%" }}
        animate={{ x: "100%" }}
        transition={{ duration: 15, repeat: Infinity, ease: "linear", delay: delay }}
        className="absolute left-0 w-[200%] h-[1px] pointer-events-none"
        style={{ 
            top: `${yOffset}%`,
            background: theme === 'dark' 
                ? 'linear-gradient(90deg, transparent, rgba(255,255,255,0.05), rgba(255,255,255,0.15), rgba(255,255,255,0.05), transparent)'
                : 'linear-gradient(90deg, transparent, rgba(0,0,0,0.05), rgba(0,0,0,0.15), rgba(0,0,0,0.05), transparent)',
            opacity: opacity
        }}
    />
);

// Floating Geo
const FloatingGeo = ({ delay, x, y, size, theme }: any) => (
    <motion.div 
        initial={{ y: y, opacity: 0 }}
        animate={{ 
            y: [y, y - 100, y - 200],
            opacity: [0, 0.4, 0],
            rotate: [0, 45, 90]
        }}
        transition={{ duration: 10 + Math.random() * 5, repeat: Infinity, delay: delay, ease: "linear" }}
        className={`absolute border backdrop-blur-sm ${theme === 'dark' ? 'border-white/10 bg-black/5' : 'border-black/10 bg-white/5'}`}
        style={{ left: x, width: size, height: size, borderRadius: Math.random() > 0.5 ? '50%' : '2px' }}
    />
);

// Scan Beam
const ScanBeam = ({ theme }: { theme: string }) => (
    <motion.div
        initial={{ top: "-10%" }}
        animate={{ top: "110%" }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", repeatDelay: 2 }}
        className={`absolute left-0 right-0 h-[100px] pointer-events-none z-0 rotate-[-5deg] scale-150 ${theme === 'dark' ? 'bg-gradient-to-b from-transparent via-white/[0.03] to-transparent' : 'bg-gradient-to-b from-transparent via-black/[0.03] to-transparent'}`}
    />
);

// Side Ruler
const SideRuler = ({ side = 'left', theme }: { side?: 'left' | 'right', theme: string }) => (
  <div className={`absolute top-0 bottom-0 ${side === 'left' ? 'left-8' : 'right-8'} w-2 flex flex-col justify-around py-20 opacity-[0.15] pointer-events-none z-10 hidden md:flex`}>
      {Array.from({ length: 30 }).map((_, i) => (
          <motion.div 
            key={i} 
            initial={{ opacity: 0.5, width: "30%" }}
            animate={{ opacity: [0.3, 0.8, 0.3], width: i % 5 === 0 ? ["100%", "80%", "100%"] : ["30%", "50%", "30%"] }}
            transition={{ duration: 2 + Math.random() * 2, repeat: Infinity, ease: "easeInOut", delay: Math.random() * 2 }}
            className={`h-[1px] ${side === 'left' ? 'self-start' : 'self-end'} ${theme === 'dark' ? 'bg-white' : 'bg-black'}`} 
          />
      ))}
  </div>
);

// Shooting Line
const ShootingLine = ({ x, delay, duration, theme }: any) => (
    <motion.div
        initial={{ y: "-100%", opacity: 0 }}
        animate={{ y: "200%", opacity: 1 }}
        transition={{ duration: duration, repeat: Infinity, ease: "linear", delay: delay }}
        className={`absolute top-0 w-[1px] h-[40vh] pointer-events-none z-0 ${theme === 'dark' ? 'bg-gradient-to-b from-transparent via-white/[0.07] to-transparent' : 'bg-gradient-to-b from-transparent via-black/[0.07] to-transparent'}`}
        style={{ left: x }}
    />
);

// Corner Artifact
const CornerArtifact = ({ theme }: { theme: string }) => (
    <div className="absolute top-[18%] left-[8%] w-64 h-64 pointer-events-none z-0">
        <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 80, repeat: Infinity, ease: "linear" }}
            className="absolute inset-0 flex items-center justify-center drop-shadow-md"
        >
            <div className={`w-full h-full border-[1.5px] opacity-80 ${theme === 'dark' ? 'border-white/30' : 'border-black/30'}`} style={{ clipPath: 'polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)' }}></div>
            <div className={`absolute w-[85%] h-[85%] border-[1px] ${theme === 'dark' ? 'border-white/20' : 'border-black/20'}`} style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }}></div>
        </motion.div>
        <div className={`absolute -right-12 -top-8 text-[9px] font-medium font-mono tracking-widest flex flex-col gap-1 backdrop-blur-[2px] ${theme === 'dark' ? 'text-white/50' : 'text-black/50'}`}>
             <span>XY-902</span>
             <span>STATE: ACTIVE</span>
        </div>
    </div>
);

// --- MAIN TECH LAYER COMPONENT ---
// This renders the actual graphics. We will use two of these overlapping.
const TechLayer = ({ theme }: { theme: string }) => {
    const [particles, setParticles] = useState<any[]>([]);
    const [shootingLines, setShootingLines] = useState<any[]>([]);

    useEffect(() => {
        setParticles(Array.from({ length: 20 }).map((_, i) => ({ id: i, x: `${Math.random() * 100}%`, y: Math.random() * 800 + 100, size: Math.random() * 15 + 5, delay: Math.random() * 10 })));
        setShootingLines([
            { x: "12%", delay: 0, duration: 15 },
            { x: "88%", delay: 5, duration: 18 },
            { x: "5%", delay: 2, duration: 20 },
            { x: "95%", delay: 8, duration: 12 },
            { x: "20%", delay: 10, duration: 25 },
            { x: "80%", delay: 3, duration: 22 }
        ]);
    }, []);

    return (
        <div className={`absolute inset-0 overflow-hidden ${theme === 'dark' ? 'bg-[#0A0A0A]' : 'bg-[#EBEBF0]'}`}>
            {/* Background Gradient */}
            <div className={`absolute inset-0 opacity-50 ${theme === 'dark' ? 'bg-[radial-gradient(circle_at_50%_50%,_rgba(20,20,20,0.8),_transparent_70%)]' : 'bg-[radial-gradient(circle_at_50%_50%,_rgba(255,255,255,0.8),_transparent_70%)]'}`}></div>
            
            <CrosshairOverlay theme={theme} />
            <FlowingDataStream top="30%" theme={theme} />
            <FlowingDataStream top="70%" theme={theme} />
            <CornerArtifact theme={theme} />
            <GiantGear size={900} x="-300px" y="-200px" duration={120} direction={1} opacity={0.15} theme={theme} />
            <GiantGear size={1000} x="calc(100% - 600px)" y="calc(100% - 400px)" duration={140} direction={-1} opacity={0.12} theme={theme} />
            <WireframeSphere size={700} x="calc(100% - 300px)" y="10%" duration={80} opacity={0.2} theme={theme} />
            <WireframeSphere size={600} x="-200px" y="calc(100% - 300px)" duration={90} opacity={0.18} theme={theme} />
            
            {/* Vertical Lines */}
            <div className="absolute inset-0 pointer-events-none">
                <div className={`absolute left-[12%] top-0 bottom-0 w-[1px] ${theme === 'dark' ? 'bg-white/[0.04]' : 'bg-black/[0.04]'}`}></div>
                <div className={`absolute right-[12%] top-0 bottom-0 w-[1px] ${theme === 'dark' ? 'bg-white/[0.04]' : 'bg-black/[0.04]'}`}></div>
            </div>

            <SilkWave delay={0} yOffset={15} opacity={0.3} theme={theme} />
            <SilkWave delay={5} yOffset={35} opacity={0.15} theme={theme} />
            
            {shootingLines.map((line, i) => <ShootingLine key={i} {...line} theme={theme} />)}
            
            <SideRuler side="left" theme={theme} />
            <SideRuler side="right" theme={theme} />
            <GyroScope theme={theme} />
            <ScanBeam theme={theme} />
            
            {particles.map(p => <FloatingGeo key={p.id} {...p} theme={theme} />)}
            
            {/* Noise & Vignette */}
            <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")` }}></div>
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_40%,rgba(0,0,0,0.03)_100%)]"></div>
        </div>
    );
}

// --- THE BIO-METALLIC SCALE GRID ---
const BioMetallicScales = ({ targetTheme, animationKey }: { targetTheme: string, animationKey: number }) => {
    // Mobile needs fewer columns to keep scales readable sized
    const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
    const GRID_COLS = isMobile ? 6 : 12;
    const GRID_ROWS = isMobile ? 8 : 10;
    
    const cells = [];
    
    for (let row = 0; row < GRID_ROWS; row++) {
        for (let col = 0; col < GRID_COLS; col++) {
            // Distance from Top-Right (TR): col is max, row is 0
            const dist = Math.abs((GRID_COLS - 1) - col) + row;
            cells.push({ row, col, dist, id: `${row}-${col}` });
        }
    }

    // Metallic Gradient Definitions
    const darkMetalGradient = "linear-gradient(135deg, #2b2b2b 0%, #1a1a1a 50%, #000000 100%)";
    const darkMetalBorder = "1px solid rgba(255,255,255,0.1)";
    
    const lightMetalGradient = "linear-gradient(135deg, #ffffff 0%, #e6e6e6 50%, #d4d4d4 100%)";
    const lightMetalBorder = "1px solid rgba(0,0,0,0.1)";

    return (
        <div className="absolute inset-0 pointer-events-none z-50 overflow-hidden" style={{ 
            display: 'grid',
            gridTemplateColumns: `repeat(${GRID_COLS}, 1fr)`,
            gridTemplateRows: `repeat(${GRID_ROWS}, 1fr)`,
            perspective: '1000px'
        }}>
            {cells.map((cell) => {
                // Each cell is a 3D flipper
                return (
                    <motion.div
                        key={`${cell.id}-${animationKey}`} // Force re-render/reset on each transition
                        className="relative w-full h-full"
                        style={{ transformStyle: 'preserve-3d' }}
                        initial={{ rotateX: 0 }}
                        animate={{ rotateX: [0, -180, -360] }}
                        transition={{
                            delay: cell.dist * 0.05, // Wave propagation
                            duration: 1.2, // Total flip cycle
                            ease: [0.45, 0, 0.55, 1], // Cubic bezier for mechanical snap
                            times: [0, 0.5, 1] 
                        }}
                    >
                        {/* FRONT FACE (Transparent/Invisible initially) */}
                        <div 
                            className="absolute inset-0 backface-hidden"
                            style={{ 
                                transform: "rotateX(0deg)",
                                border: '0.5px solid transparent' // Hidden normally
                            }}
                        />

                        {/* BACK FACE (The Armor) */}
                        <div 
                            className="absolute inset-[1px] backface-hidden shadow-xl" // inset-1px for gap
                            style={{ 
                                transform: "rotateX(-180deg)",
                                background: targetTheme === 'dark' ? darkMetalGradient : lightMetalGradient,
                                border: targetTheme === 'dark' ? darkMetalBorder : lightMetalBorder,
                                boxShadow: targetTheme === 'dark' 
                                    ? '0 4px 6px -1px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255,255,255,0.1)' 
                                    : '0 4px 6px -1px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255,255,255,0.8)',
                                borderRadius: '2px'
                            }}
                        >
                            {/* Inner Tech Detail on the Scale */}
                            <div className={`absolute top-1 right-1 w-1 h-1 rounded-full ${targetTheme === 'dark' ? 'bg-blue-500/50' : 'bg-blue-400/50'} shadow-[0_0_4px_currentColor]`}></div>
                            <div className={`absolute bottom-1 left-1 w-2 h-[1px] ${targetTheme === 'dark' ? 'bg-white/20' : 'bg-black/20'}`}></div>
                        </div>
                    </motion.div>
                );
            })}
        </div>
    );
};

export function TechBackground({ theme = 'light' }: { theme?: 'light' | 'dark' }) {
  const [animationKey, setAnimationKey] = useState(0); 
  const lightControls = useAnimation();
  const darkControls = useAnimation();

  // Handle Animation Sequencing Manually for Absolute Control
  useEffect(() => {
      // 1. Increment key to trigger Scale Wave (this is "fire and forget")
      setAnimationKey(prev => prev + 1);

      // 2. Control Background Layers
      if (theme === 'light') {
         // --- Switching to LIGHT ---
         
         // LIGHT LAYER (Becoming Active):
         // - Reset to 0 immediately (instant invisible)
         // - Then animate to 150 (Reveal)
         lightControls.set({ clipPath: "circle(0% at 100% 0)", zIndex: 20 });
         lightControls.start({
             clipPath: "circle(150% at 100% 0)",
             transition: { duration: 1.6, delay: 0.3, ease: "easeInOut" }
         });

         // DARK LAYER (Becoming Inactive):
         // - Must stay visible (Full Screen) to be the "background" that gets covered
         // - Drop Z-Index to 10
         darkControls.set({ zIndex: 10, clipPath: "circle(150% at 100% 0)" });

      } else {
         // --- Switching to DARK ---

         // DARK LAYER (Becoming Active):
         // - Reset to 0 immediately (instant invisible)
         // - Then animate to 150 (Reveal)
         darkControls.set({ clipPath: "circle(0% at 100% 0)", zIndex: 20 });
         darkControls.start({
             clipPath: "circle(150% at 100% 0)",
             transition: { duration: 1.6, delay: 0.3, ease: "easeInOut" }
         });

         // LIGHT LAYER (Becoming Inactive):
         // - Must stay visible (Full Screen)
         // - Drop Z-Index to 10
         lightControls.set({ zIndex: 10, clipPath: "circle(150% at 100% 0)" });
      }

  }, [theme, lightControls, darkControls]);

  return (
    <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none select-none bg-[#111]">
       
       {/* DARK LAYER */}
       <motion.div
         className="absolute inset-0"
         animate={darkControls}
         initial={{ clipPath: "circle(150% at 100% 0)", zIndex: 10 }} 
       >
         <TechLayer theme="dark" />
       </motion.div>

       {/* LIGHT LAYER */}
       <motion.div
         className="absolute inset-0"
         animate={lightControls}
         initial={{ clipPath: "circle(150% at 100% 0)", zIndex: 20 }} // Start full if initial theme is light
       >
         <TechLayer theme="light" />
       </motion.div>

       {/* BIO-METALLIC SCALES OVERLAY */}
       <BioMetallicScales targetTheme={theme} animationKey={animationKey} />

    </div>
  );
}
