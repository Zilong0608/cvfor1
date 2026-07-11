import React, { useState } from 'react';
import { motion } from 'motion/react';
import { ScanFace, FileBadge, BrainCircuit, Sparkles } from 'lucide-react';

export default function App() {
  const [hoveredSide, setHoveredSide] = useState<'left' | 'right' | null>(null);

  // Configuration for the diagonal split
  // [Top-X, Bottom-X] percentages relative to screen width
  const splitconfig = {
    default: { left: [55, 45], right: [55, 45] },
    hoverLeft: { left: [75, 65], right: [75, 65] },
    hoverRight: { left: [25, 15], right: [25, 15] },
  };

  const currentSplit = hoveredSide === 'left' 
    ? splitconfig.hoverLeft 
    : hoveredSide === 'right' 
      ? splitconfig.hoverRight 
      : splitconfig.default;

  const transition = { duration: 0.6, ease: [0.22, 1, 0.36, 1] };
  
  // FIXED: Calculate clip paths specifically for the text element.
  // The global split goes from Top% to Bottom% over 100vh.
  // The text element is only at the top (~10% of screen height).
  // So the "Bottom X" for the text clip path should be very close to the "Top X", not the screen bottom X.
  // We interpolate to find the correct X coordinate at the bottom of the text header.
  const textHeightFactor = 0.15; // Approximate height of header relative to screen
  
  const leftTextBottomX = currentSplit.left[0] + (currentSplit.left[1] - currentSplit.left[0]) * textHeightFactor;
  const rightTextBottomX = currentSplit.right[0] + (currentSplit.right[1] - currentSplit.right[0]) * textHeightFactor;

  const textLeftClipPath = `polygon(0% 0%, ${currentSplit.left[0]}% 0%, ${leftTextBottomX}% 100%, 0% 100%)`;
  const textRightClipPath = `polygon(${currentSplit.right[0]}% 0%, 100% 0%, 100% 100%, ${rightTextBottomX}% 100%)`;

  // Global background clip paths (full screen height)
  const bgLeftClipPath = `polygon(0% 0%, ${currentSplit.left[0]}% 0%, ${currentSplit.left[1]}% 100%, 0% 100%)`;
  const bgRightClipPath = `polygon(${currentSplit.right[0]}% 0%, 100% 0%, 100% 100%, ${currentSplit.right[1]}% 100%)`;
  const dividerClipPath = `polygon(${currentSplit.left[0]}% 0%, ${currentSplit.left[0] + 0.1}% 0%, ${currentSplit.left[1] + 0.1}% 100%, ${currentSplit.left[1]}% 100%)`;

  return (
    <div className="relative h-screen w-full overflow-hidden bg-black font-sans selection:bg-cyan-500 selection:text-white">
      
      {/* Header Container */}
      <div className="absolute top-0 left-0 z-50 w-full py-10 pointer-events-none">
        <div className="relative w-full text-center">
          
          {/* Right Side Text (Dark for Light Background) */}
          <motion.h1 
            className="text-3xl font-black tracking-[0.3em] text-slate-900 uppercase absolute left-0 right-0 mx-auto"
            animate={{ clipPath: textRightClipPath }}
            transition={transition}
          >
            MirrorCareer
          </motion.h1>

          {/* Left Side Text (White for Dark Background) */}
          <motion.h1 
             className="text-3xl font-black tracking-[0.3em] text-white uppercase absolute left-0 right-0 mx-auto drop-shadow-md"
             animate={{ clipPath: textLeftClipPath }}
             transition={transition}
          >
            MirrorCareer
          </motion.h1>

          {/* Spacer to maintain layout height */}
          <h1 className="text-3xl font-black tracking-[0.3em] text-transparent uppercase opacity-0">
            MirrorCareer
          </h1>
        </div>
      </div>

      {/* Mobile Layout */}
      <div className="flex h-full flex-col md:hidden">
        <MobileSection 
          type="interviewer"
          title="Interviewer"
          desc="Simulate Real-World Interviews"
          image="https://images.unsplash.com/photo-1764258559447-7f7b70e2580c?q=80&w=1080&auto=format&fit=crop"
        />
        <MobileSection 
          type="candidate"
          title="CvFor1"
          desc="Customize Your Resume"
          image="https://images.unsplash.com/photo-1708875832368-1f39a2dc6479?q=80&w=1080&auto=format&fit=crop"
        />
      </div>

      {/* Desktop Layout */}
      <div className="hidden h-full w-full md:block relative">
        
        {/* Left Side: Interviewer */}
        <motion.div
          className="absolute inset-0 z-10 overflow-hidden bg-slate-900"
          initial={false}
          animate={{
            clipPath: bgLeftClipPath
          }}
          transition={transition}
          onMouseEnter={() => setHoveredSide('left')}
          onMouseLeave={() => setHoveredSide(null)}
        >
          {/* Background */}
          <div className="absolute inset-0">
            <img
              src="https://images.unsplash.com/photo-1764258559447-7f7b70e2580c?q=80&w=1080&auto=format&fit=crop"
              alt="Interviewer Background"
              className="h-full w-full object-cover opacity-60 transition-transform duration-1000 scale-105"
            />
            <div className="absolute inset-0 bg-blue-950/90 mix-blend-multiply" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(6,182,212,0.15),transparent_60%)]" />
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />
          </div>

          {/* Content */}
          <div className="absolute inset-0 flex items-center">
            <motion.div 
              className="w-full flex justify-center"
              animate={{ x: hoveredSide === 'left' ? '12%' : hoveredSide === 'right' ? '-18%' : '-5%' }}
              transition={transition}
              style={{ width: '50vw' }}
            >
              <div className="flex flex-col items-center text-center max-w-lg px-8 pt-20">
                <motion.div 
                  className="mb-8 p-6 rounded-2xl bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-cyan-400/30 backdrop-blur-md shadow-[0_0_40px_rgba(6,182,212,0.2)] group"
                  whileHover={{ scale: 1.05 }}
                >
                  <ScanFace size={64} className="text-cyan-300 group-hover:animate-pulse" strokeWidth={1.5} />
                </motion.div>
                
                <h2 className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-b from-white to-cyan-200 tracking-tighter mb-4 drop-shadow-[0_0_25px_rgba(6,182,212,0.4)] font-mono">
                  INTERVIEWER
                </h2>
                
                <p className="text-cyan-100/80 text-xl font-light tracking-wide mb-10 h-8">
                  Simulate Real-World Interviews
                </p>

                <a
                  href="https://interviewer-2g2y.onrender.com"
                  className="group relative px-8 py-3 bg-transparent overflow-hidden border border-cyan-500/50 text-cyan-300 font-mono text-sm tracking-widest uppercase transition-all hover:bg-cyan-950/30 hover:border-cyan-400 hover:text-white hover:shadow-[0_0_20px_rgba(34,211,238,0.4)]"
                >
                  <span className="relative flex items-center gap-2">
                    Start Simulation
                    <BrainCircuit className="w-4 h-4" />
                  </span>
                </a>
              </div>
            </motion.div>
          </div>
        </motion.div>

        {/* Right Side: CvFor1 */}
        <motion.div
          className="absolute inset-0 z-10 overflow-hidden bg-white"
          initial={false}
          animate={{
            clipPath: bgRightClipPath
          }}
          transition={transition}
          onMouseEnter={() => setHoveredSide('right')}
          onMouseLeave={() => setHoveredSide(null)}
        >
          {/* Background */}
          <div className="absolute inset-0">
            <img
              src="https://images.unsplash.com/photo-1708875832368-1f39a2dc6479?q=80&w=1080&auto=format&fit=crop"
              alt="CvFor1 Background"
              className="h-full w-full object-cover opacity-20 grayscale transition-transform duration-1000 scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-white/90 via-white/50 to-white/80" />
            <div className="absolute inset-0 bg-[linear-gradient(rgba(0,0,0,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,0.03)_1px,transparent_1px)] bg-[size:40px_40px]" />
          </div>

          {/* Content */}
          <div className="absolute inset-0 flex items-center justify-end">
            <motion.div 
              className="w-full flex justify-center"
              animate={{ x: hoveredSide === 'right' ? '-12%' : hoveredSide === 'left' ? '18%' : '5%' }}
              transition={transition}
              style={{ width: '50vw' }}
            >
              <div className="flex flex-col items-center text-center max-w-lg px-8 pt-20">
                <motion.div 
                  className="mb-8 p-6 rounded-2xl bg-white border border-slate-200 shadow-[0_20px_40px_rgba(0,0,0,0.05)] relative z-20 group"
                  whileHover={{ scale: 1.05 }}
                >
                  <FileBadge size={64} className="text-slate-900 group-hover:text-cyan-600 transition-colors" strokeWidth={1.2} />
                </motion.div>
                
                <h2 className="text-6xl font-black text-slate-900 tracking-tight mb-4" style={{ fontFamily: '"Inter", sans-serif', letterSpacing: '-0.05em' }}>
                  CvFor1
                </h2>
                
                <p className="text-slate-600 text-xl font-medium tracking-wide mb-10 h-8">
                  Tailor Your Perfect Resume
                </p>

                <a
                  href="https://cvfor1-2.onrender.com"
                  className="group relative px-8 py-3 bg-slate-900 overflow-hidden text-white font-mono text-sm tracking-widest uppercase transition-all hover:bg-slate-800 hover:shadow-[0_10px_20px_rgba(0,0,0,0.1)]"
                >
                  <span className="relative flex items-center gap-2">
                    Optimize Now
                    <Sparkles className="w-4 h-4" />
                  </span>
                  <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500 transition-all duration-300 group-hover:h-full h-0" />
                </a>
              </div>
            </motion.div>
          </div>
        </motion.div>

        {/* Diagonal Divider Line */}
        <motion.div
           className="absolute inset-0 z-20 pointer-events-none"
           initial={false}
           animate={{
             clipPath: dividerClipPath
           }}
           transition={transition}
        >
          <div className="w-full h-full bg-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.6)]" />
        </motion.div>

      </div>
    </div>
  );
}

function MobileSection({ type, title, desc, image }: { type: 'interviewer' | 'candidate', title: string, desc: string, image: string }) {
  const isInterviewer = type === 'interviewer';
  
  return (
    <div className={`relative flex flex-1 items-center justify-center overflow-hidden ${isInterviewer ? 'bg-slate-900 text-white' : 'bg-white text-slate-900'}`}>
      <div className="absolute inset-0 z-0">
         <img src={image} className="w-full h-full object-cover opacity-50" />
         {isInterviewer ? (
           <div className="absolute inset-0 bg-blue-900/80 mix-blend-multiply" />
         ) : (
           <div className="absolute inset-0 bg-white/80" />
         )}
      </div>
      
      <div className="relative z-10 flex flex-col items-center p-6 text-center">
        {isInterviewer ? <ScanFace size={48} className="mb-4 text-cyan-300" /> : <FileBadge size={48} className="mb-4 text-slate-800" />}
        <h2 className="text-4xl font-bold uppercase tracking-wider mb-2">{title}</h2>
        <p className={`mb-6 text-lg ${isInterviewer ? 'text-blue-200' : 'text-slate-600'}`}>{desc}</p>
        <a
          href={isInterviewer ? 'https://interviewer-2g2y.onrender.com' : 'https://cvfor1-2.onrender.com'}
          className={`px-8 py-3 font-medium uppercase tracking-widest text-sm border ${isInterviewer ? 'border-cyan-400 text-cyan-400' : 'border-slate-900 bg-slate-900 text-white'}`}
        >
          Enter
        </a>
      </div>
    </div>
  )
}
