import React, { useEffect, useState, useRef } from 'react';
import { ArrowRight, Play, Sun, Moon } from 'lucide-react';
import { Button } from './ui/button';
import { motion, AnimatePresence } from 'motion/react';

interface LandingProps {
  onStart: () => void;
  language: 'zh' | 'en';
  onToggleLanguage: () => void;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
}

const FlipChar = ({ char }: { char: string }) => {
  return (
    <motion.span
      initial={{ rotateY: 90, opacity: 0, filter: "blur(4px)" }}
      animate={{ rotateY: 0, opacity: 1, filter: "blur(0px)" }}
      transition={{ 
        type: "spring", 
        stiffness: 600, 
        damping: 20,    
        mass: 0.5       
      }}
      className="inline-block origin-center backface-hidden whitespace-pre will-change-transform"
    >
      {char || '\u200B'}
    </motion.span>
  );
};

const OverwriteText = ({ text, className }: { text: string; className?: string }) => {
  const [items, setItems] = useState<Array<{ char: string; key: string; isVisible: boolean }>>([]);
  const previousText = useRef(text);
  
  useEffect(() => {
    if (previousText.current === text && items.length > 0) return;
    
    const oldTxt = previousText.current;
    const newTxt = text;
    const maxLength = Math.max(oldTxt.length, newTxt.length);
    let step = 0;
    
    const updateItems = (currentStep: number) => {
      const newItems = [];
      for (let i = 0; i < maxLength; i++) {
        let char = '';
        let isVisible = true;
        
        if (i < currentStep) {
          if (i < newTxt.length) {
            char = newTxt[i];
          } else {
            char = ''; 
            isVisible = false;
          }
        } else {
          if (i < oldTxt.length) {
            char = oldTxt[i];
          } else {
            char = '';
            isVisible = false;
          }
        }
        
        newItems.push({ 
          char, 
          key: `${i}-${char}`, 
          isVisible
        });
      }
      setItems(newItems);
    };

    if (items.length === 0) {
        updateItems(0);
    }
    
    const interval = setInterval(() => {
      if (step > maxLength) {
        clearInterval(interval);
        previousText.current = newTxt;
        const finalItems = newTxt.split('').map((c, i) => ({
             char: c,
             key: `${i}-${c}`,
             isVisible: true
        }));
        setItems(finalItems);
        return;
      }
      
      updateItems(step);
      step += 2; 
    }, 8); 

    return () => clearInterval(interval);
  }, [text]);

  return (
    <span className={`inline-block ${className}`}>
      {items.map((item) => (
        item.isVisible ? (
            <FlipChar key={item.key} char={item.char} />
        ) : null
      ))}
    </span>
  );
};

// --- PopCat moved to /components/PopCat.tsx ---

// --- Reflective Title Component ---
const ReflectiveTitle = ({ isDark }: { isDark: boolean }) => {
  // Gradients - Pure Monochrome / Silver / Platinum
  // Dark: Dark Grey -> Bright White -> Dark Grey
  const darkGradient = "linear-gradient(to right, #4b5563 0%, #ffffff 45%, #e5e7eb 50%, #ffffff 55%, #4b5563 100%)"; 
  // Light: Black -> Silver -> Black
  const lightGradient = "linear-gradient(to right, #000000 0%, #4b5563 45%, #9ca3af 50%, #4b5563 55%, #000000 100%)";
  
  const bgSize = "200% auto";

  // Common font styles for reuse
  const cvStyle = "font-light tracking-[0.15em]"; // Airy, premium
  const foStyle = "font-serif italic opacity-60 text-[0.6em] mx-1 relative -top-1"; // Elegant connector
  const r1Style = "font-black tracking-tighter"; // Strong, impactful

  return (
    <div className="relative group flex flex-col items-center justify-center">
       {/* --- Main Text Layer (Z-10) --- */}
       <div className="relative z-10 flex flex-col md:flex-row items-center md:items-baseline justify-center gap-2 md:gap-8">
          
          {/* MirrorCareer */}
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ 
                opacity: 1, 
                y: 0,
                backgroundPosition: ["0% 50%", "-200% 50%"] 
            }}
            transition={{ 
                opacity: { duration: 1 },
                y: { duration: 1 },
                backgroundPosition: { duration: 6, repeat: Infinity, ease: "linear" } 
            }}
            style={{ 
                backgroundImage: isDark ? darkGradient : lightGradient,
                backgroundSize: bgSize,
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent"
            }}
            className="text-5xl md:text-8xl font-black tracking-tighter cursor-default"
          >
            MirrorCareer
          </motion.h1>

          <span className={`hidden md:inline-block text-4xl md:text-6xl font-light transition-colors duration-500 ${isDark ? 'text-white/20' : 'text-black/20'}`}>|</span>

          <motion.div
             initial={{ opacity: 0, x: 20 }}
             animate={{ opacity: 1, x: 0 }}
             transition={{ delay: 0.2, duration: 1 }}
             className={`flex items-baseline ${isDark ? 'text-white' : 'text-black'}`}
          >
             {/* CV: Ultra-light, wide tracking - Modern */}
             <span className="text-3xl md:text-7xl font-light tracking-[0.2em] opacity-90">
                CV
             </span>
             
             {/* foR: Calligraphic/Serif - The "Flower" touch - grouped as "for" */}
             <div className="flex items-baseline mx-1.5 opacity-70">
                 <span className="text-4xl md:text-8xl font-serif italic font-medium" style={{ fontFamily: 'Georgia, serif' }}>
                    f
                 </span>
                 <span className="text-2xl md:text-6xl font-serif italic font-light">
                    o
                 </span>
                 <span className="text-3xl md:text-7xl font-serif italic font-medium ml-0.5">
                    R
                 </span>
             </div>
             
             {/* 1: Heavy Industrial - The "Tech" touch with Delayed Light Flow */}
             <motion.span 
                animate={{ 
                    backgroundPosition: ["0% 50%", "-200% 50%"] 
                }}
                transition={{ 
                    duration: 6, 
                    repeat: Infinity, 
                    ease: "linear",
                    delay: 2.5 // Starts after MirrorCareer's main sweep
                }}
                style={{ 
                    backgroundImage: isDark ? darkGradient : lightGradient,
                    backgroundSize: "200% auto",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    display: "inline-block"
                }}
                className={`text-4xl md:text-8xl font-sans font-black tracking-tighter ml-1 pb-2 relative z-10 ${isDark ? 'drop-shadow-[0_0_15px_rgba(255,255,255,0.4)]' : ''}`}
             >
                1
             </motion.span>
          </motion.div>
       </div>

       {/* --- Tech Water Reflection Layer --- */}
       <div 
         className="absolute top-[60%] left-0 right-0 flex flex-col md:flex-row items-center md:items-baseline justify-center gap-2 md:gap-8 pointer-events-none select-none z-0"
         style={{ 
             opacity: 0.25,
             transform: "scaleY(-1)",
             filter: "url(#tech-water-reflection)", // SVG Filter for Liquid Metal effect
             maskImage: "linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 60%)",
             WebkitMaskImage: "linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 60%)" 
         }}
       >
           <h1 className={`text-5xl md:text-8xl font-black tracking-tighter ${isDark ? 'text-white' : 'text-black'}`}>
             MirrorCareer
           </h1>
           <span className={`hidden md:inline-block text-4xl md:text-6xl font-light ${isDark ? 'text-white/30' : 'text-black/30'}`}>|</span>
           <div className={`flex items-baseline ${isDark ? 'text-white' : 'text-black'}`}>
                <span className="text-3xl md:text-7xl font-light tracking-[0.2em] opacity-90">
                    CV
                </span>
                <div className="flex items-baseline mx-1.5 opacity-70">
                     <span className="text-4xl md:text-8xl font-serif italic font-medium" style={{ fontFamily: 'Georgia, serif' }}>
                        f
                     </span>
                     <span className="text-2xl md:text-6xl font-serif italic font-light">
                        o
                     </span>
                     <span className="text-3xl md:text-7xl font-serif italic font-medium ml-0.5">
                        R
                     </span>
                </div>
                <span className="text-4xl md:text-8xl font-sans font-black tracking-tighter ml-1 pb-2">
                    1
                </span>
           </div>
       </div>

       {/* --- SVG Filter Definition for Water Effect --- */}
       <svg className="absolute w-0 h-0 pointer-events-none" aria-hidden="true">
         <defs>
           <filter id="tech-water-reflection">
             {/* Turbulence creates the ripple noise */}
             <feTurbulence 
               type="fractalNoise" 
               baseFrequency="0.01 0.1" 
               numOctaves="2" 
               result="ripple" 
             >
               {/* Animate baseFrequency for flowing water effect */}
               <animate 
                  attributeName="baseFrequency" 
                  dur="10s" 
                  values="0.01 0.1; 0.01 0.15; 0.01 0.1" 
                  repeatCount="indefinite" 
               />
             </feTurbulence>
             {/* DisplacementMap applies the ripple to the source graphic */}
             <feDisplacementMap 
               in="SourceGraphic" 
               in2="ripple" 
               scale="8" 
               xChannelSelector="R" 
               yChannelSelector="G" 
             />
             {/* Optional: Add a subtle blur to soften the digital edge */}
             <feGaussianBlur stdDeviation="0.5" />
           </filter>
         </defs>
       </svg>
       
       {/* --- Ambient Light (Monochrome/Silver) --- */}
       {isDark && (
           <motion.div 
              animate={{ opacity: [0.05, 0.15, 0.05], scale: [0.9, 1.1, 0.9] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[150%] bg-gradient-radial from-white/10 to-transparent blur-3xl -z-10 pointer-events-none"
           />
       )}
    </div>
  );
};

export function Landing({ onStart, language, onToggleLanguage, theme, onToggleTheme }: LandingProps) {
  
  const isDark = theme === 'dark';
  
  // Text Colors (Directly transitionable)
  const textColor = isDark ? 'text-[#EDEDED]' : 'text-[#1A1A1A]';
  const subTextColor = isDark ? 'text-[#EDEDED]/60' : 'text-[#1A1A1A]/60';
  const borderColor = isDark ? 'border-[#EDEDED]' : 'border-[#1A1A1A]';
  const mutedText = isDark ? 'text-gray-400' : 'text-gray-500';
  
  const t = {
    zh: {
      logoSub: "AI 原生孵化器",
      description: "探索新的技术方向与工作范式",
      button: "开启探索之旅"
    },
    en: {
      logoSub: "AI NATIVE INCUBATOR",
      description: "EXPLORING NEW TECH DIRECTIONS & WORK PARADIGMS",
      button: "START EXPLORATION"
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-transparent p-4 relative overflow-hidden font-sans perspective-1000">
       
       {/* Removed the Grid Overlay from here as requested. The background transition is handled by TechBackground. */}

       {/* --- UI LAYER (z-10) --- */}
       
       {/* Theme Toggle Top Right */}
       <div className="absolute top-6 right-6 md:top-8 md:right-12 z-50 animate-in fade-in slide-in-from-top-4 duration-1000 delay-200">
            <Button
                onClick={onToggleTheme}
                variant="ghost"
                size="icon"
                className={`rounded-full border transition-all duration-300 hover:scale-110 ${
                    isDark 
                        ? 'border-white/20 hover:bg-white/10 text-white' 
                        : 'border-black/10 hover:bg-black/5 text-black'
                }`}
            >
                <AnimatePresence mode="wait">
                    {isDark ? (
                        <motion.div
                            key="moon"
                            initial={{ rotate: -90, opacity: 0 }}
                            animate={{ rotate: 0, opacity: 1 }}
                            exit={{ rotate: 90, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                        >
                            <Moon className="w-5 h-5" />
                        </motion.div>
                    ) : (
                        <motion.div
                            key="sun"
                            initial={{ rotate: -90, opacity: 0 }}
                            animate={{ rotate: 0, opacity: 1 }}
                            exit={{ rotate: 90, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                        >
                            <Sun className="w-5 h-5" />
                        </motion.div>
                    )}
                </AnimatePresence>
            </Button>
       </div>

       {/* Logo Top Left */}
       <div className="absolute top-6 left-6 md:top-8 md:left-12 z-50 animate-in fade-in slide-in-from-top-4 duration-1000">
         <div className="flex items-center gap-4 group cursor-pointer select-none" onClick={onToggleLanguage}>
            {/* Logo Icon */}
            <motion.div 
               animate={{ rotate: language === 'en' ? 0 : 180 }}
               transition={{ type: "spring", stiffness: 200, damping: 15 }}
               className={`relative w-12 h-12 flex items-center justify-center border-[2.5px] rounded-full transition-colors duration-500 ${borderColor}`}
            >
               <div className="flex flex-col gap-[5px] -rotate-45 items-center justify-center">
                 <div className={`w-5 h-[2.5px] rounded-full transition-colors duration-500 ${isDark ? 'bg-[#EDEDED]' : 'bg-[#1A1A1A]'}`}></div>
                 <div className={`w-5 h-[2.5px] rounded-full transition-colors duration-500 ${isDark ? 'bg-[#EDEDED]' : 'bg-[#1A1A1A]'}`}></div>
               </div>
            </motion.div>
            
            {/* Logo Text */}
            <div className="flex flex-col justify-center">
               <span className={`text-xl font-medium tracking-[0.15em] leading-none mb-1.5 font-sans transition-colors duration-500 ${textColor}`}>WHITE MIRROR</span>
               <span className={`text-[10px] font-medium tracking-[0.05em] leading-none h-3 block relative overflow-hidden transition-colors duration-500 ${subTextColor}`}>
                  <OverwriteText text={t[language].logoSub} />
               </span>
            </div>
         </div>
       </div>

       {/* Main Content Area */}
       <div className="w-full h-full flex flex-col items-center justify-center pointer-events-none z-10">
       
          {/* --- CONTENT Wrapper --- */}
          <div className="text-center space-y-12 max-w-5xl relative pointer-events-auto">
            
          {/* MAIN TITLE (Replaced with ReflectiveTitle) */}
            <div className="relative animate-in fade-in zoom-in duration-1000 z-20">
               <ReflectiveTitle isDark={isDark} />
            </div>
            
            {/* Mobile Geometric Decoration Middle - ENHANCED */}
            
            {/* Subtitle */}
            <div className="relative inline-flex justify-center mt-6 w-full min-h-[1.5rem] px-4 z-20">
                 {/* Animated Brackets */}
                 <motion.div 
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 1, duration: 1 }}
                    className={`absolute -left-4 md:-left-8 top-0 bottom-0 w-[1px] ${isDark ? 'bg-white/20' : 'bg-black/20'}`}
                 >
                    <div className={`absolute top-0 left-0 w-2 h-[1px] ${isDark ? 'bg-white/40' : 'bg-black/40'}`}></div>
                    <div className={`absolute bottom-0 left-0 w-2 h-[1px] ${isDark ? 'bg-white/40' : 'bg-black/40'}`}></div>
                 </motion.div>

                 <motion.div 
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 1, duration: 1 }}
                    className={`absolute -right-4 md:-right-8 top-0 bottom-0 w-[1px] ${isDark ? 'bg-white/20' : 'bg-black/20'}`}
                 >
                     <div className={`absolute top-0 right-0 w-2 h-[1px] ${isDark ? 'bg-white/40' : 'bg-black/40'}`}></div>
                     <div className={`absolute bottom-0 right-0 w-2 h-[1px] ${isDark ? 'bg-white/40' : 'bg-black/40'}`}></div>
                 </motion.div>

                 {/* Horizontal Lines */}
                 <div className={`absolute -left-8 top-1/2 w-6 h-[1px] hidden md:block transition-colors duration-500 ${isDark ? 'bg-white/10' : 'bg-black/10'}`}></div>
                 <div className={`absolute -right-8 top-1/2 w-6 h-[1px] hidden md:block transition-colors duration-500 ${isDark ? 'bg-white/10' : 'bg-black/10'}`}></div>
                 
                 <p className={`text-xs md:text-sm tracking-[0.2em] md:tracking-[0.5em] uppercase font-medium transition-colors duration-500 leading-relaxed ${mutedText}`}>
                   <OverwriteText text={t[language].description} />
                 </p>
            </div>

            {/* ACTION BUTTON */}
            <div className="pt-12 flex flex-col items-center justify-center relative z-20">
              <Button 
                onClick={onStart}
                className={`relative overflow-hidden border rounded-lg px-16 py-8 text-base font-bold tracking-widest transition-all hover:scale-105 shadow-xl group
                    ${isDark 
                        ? 'bg-white text-black border-white/20 hover:bg-[#F0F0F0] hover:border-white/40 shadow-white/5' 
                        : 'bg-[#222224] text-white border-black/5 hover:bg-[#111] hover:border-black/20 shadow-black/5'
                    }
                `}
              >
                 {/* Hover Grid */}
                 <div 
                    className="absolute inset-0 opacity-0 group-hover:opacity-10 transition-opacity duration-700 pointer-events-none"
                    style={{ 
                      backgroundImage: `linear-gradient(${isDark ? 'rgba(0,0,0,0.5)' : 'rgba(255,255,255,0.5)'} 1px, transparent 1px), linear-gradient(90deg, ${isDark ? 'rgba(0,0,0,0.5)' : 'rgba(255,255,255,0.5)'} 1px, transparent 1px)`, 
                      backgroundSize: '10px 10px',
                    }}
                  ></div>
                  
                  {/* Scanline */}
                  <div className={`absolute top-0 left-[-150%] w-[50%] h-full bg-gradient-to-r skew-x-[-20deg] group-hover:animate-[shimmer_1s_infinite]
                      ${isDark ? 'from-transparent via-black/10 to-transparent' : 'from-transparent via-white/10 to-transparent'}
                  `}></div>
                  
                  <span className="relative z-10 flex items-center gap-3">
                     <OverwriteText text={t[language].button} />
                     <Play className="w-3 h-3 fill-current" />
                  </span>
                  
                  {/* Button Corners */}
                  <div className={`absolute top-0 left-0 w-2 h-2 border-l border-t transition-colors duration-300 ${isDark ? 'border-black/20' : 'border-white/20'}`}></div>
                  <div className={`absolute bottom-0 right-0 w-2 h-2 border-r border-b transition-colors duration-300 ${isDark ? 'border-black/20' : 'border-white/20'}`}></div>
              </Button>

              {/* Bottom Decorative Line - ENHANCED with Footer Data */}
              <div className="relative mt-8 h-32 flex flex-col items-center overflow-hidden w-full max-w-xs">
                  {/* Central Line */}
                  <div className={`w-[1px] h-16 bg-gradient-to-b ${isDark ? 'from-white/50 to-transparent' : 'from-black/50 to-transparent'}`}></div>
                  <motion.div 
                    animate={{ y: [0, 64], opacity: [0, 1, 0] }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                    className={`absolute top-0 left-1/2 -translate-x-1/2 w-[1px] h-8 bg-gradient-to-b ${isDark ? 'from-transparent via-white to-transparent' : 'from-transparent via-black to-transparent'}`}
                  ></motion.div>
                  
                  {/* Horizontal Data Bar */}
                  <div className={`mt-2 flex items-center gap-4 text-[9px] tracking-[0.2em] font-mono opacity-40 uppercase ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                      <span>System.Init</span>
                      <div className={`w-1 h-1 rounded-full ${isDark ? 'bg-white' : 'bg-black'}`}></div>
                      <span>V.1.0.4</span>
                  </div>
                  
                  {/* Fading Grid Lines Below */}
                  <div className="mt-2 w-full flex justify-center gap-4 opacity-20">
                     <div className={`h-8 w-[1px] ${isDark ? 'bg-white' : 'bg-black'}`}></div>
                     <div className={`h-6 w-[1px] ${isDark ? 'bg-white' : 'bg-black'}`}></div>
                     <div className={`h-8 w-[1px] ${isDark ? 'bg-white' : 'bg-black'}`}></div>
                  </div>
              </div>
            </div>
          </div>
        
        </div>

        {/* Footer Tech Bar (Absolute Bottom) */}
        <div className={`absolute bottom-0 left-0 right-0 h-12 md:h-16 flex items-center px-6 md:px-12 text-[10px] tracking-widest select-none z-10 pointer-events-none border-t ${isDark ? 'border-white/5 text-gray-300' : 'border-black/5 text-gray-700'}`}>
           
           {/* Left Aligned Spacer (PopCat is now global) */}
           <div className="w-20 pointer-events-none" />

           {/* Center Aligned Ticker */}
           <div className="absolute left-1/2 -translate-x-1/2 flex items-center justify-center opacity-80">
               <div className="overflow-hidden w-48 md:w-64 relative h-4 [mask-image:linear-gradient(90deg,transparent,black_10%,black_90%,transparent)]">
                  <motion.div 
                    animate={{ x: ["100%", "-100%"] }}
                    transition={{ duration: 8, ease: "linear", repeat: Infinity }}
                    className="absolute whitespace-nowrap text-center w-full font-medium"
                  >
                    /// WAITING FOR START ///
                  </motion.div>
               </div>
           </div>
        
           {/* Right Aligned Copyright */}
           <div className="ml-auto">
              <span>COPYRIGHT © 2025</span>
           </div>
        </div>
    </div>
  );
}
