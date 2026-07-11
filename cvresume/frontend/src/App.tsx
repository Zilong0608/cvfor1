import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Landing } from './components/Landing';
import { PersonaBuilder } from './components/PersonaBuilder';
import { PersonaDetails } from './components/PersonaDetails';
import { JobSearch } from './components/JobSearch';
import { ResumeGeneration } from './components/ResumeGeneration';
import { TechBackground } from './components/TechBackground';
import { PopCat } from './components/PopCat';
import { StepProgress } from './components/StepProgress';
import { CACHE_KEYS, clearCache } from './lib/cache';

// Define the steps of the application flow
type Step = 'landing' | 'builder' | 'details' | 'recommendations' | 'search' | 'generation';
type Theme = 'light' | 'dark';

export default function App() {
  const [step, setStep] = useState<Step>('landing');
  const [selectedJob, setSelectedJob] = useState<string>('');
  const [language, setLanguage] = useState<'zh' | 'en'>('en');
  const [theme, setTheme] = useState<Theme>('light');

  useEffect(() => {
    clearCache(Object.values(CACHE_KEYS));
  }, []);

  const toggleLanguage = () => {
    setLanguage(prev => prev === 'zh' ? 'en' : 'zh');
  };

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  // Step Calculation Logic
  const getStepNumber = (s: Step) => {
      switch(s) {
          case 'builder': return 1;
          case 'details': return 1; // Part of builder flow
          case 'search': return 2;
          case 'generation': return 3;
          default: return 0;
      }
  };

  const currentStepNumber = getStepNumber(step);
  const isDark = theme === 'dark';

  // Navigation handlers
  const handleStart = () => setStep('builder');
  
  const handleBuilderBack = () => setStep('landing');
  const handleBuilderNext = () => setStep('search'); // Go to Step 2

  // const handleDetailsBack = () => setStep('builder'); // Merged into builder
  // const handleDetailsNext = () => setStep('recommendations'); // Merged into builder
  
  const handleSearchBack = () => setStep('builder');
  const handleSearchNext = () => setStep('generation'); // Go to Step 3
  
  const handleGenerationBack = () => setStep('search');
  const handleGenerationNext = () => {
    // End of flow, maybe reset
    setStep('landing');
    setSelectedJob('');
  };

  // Enhanced transition config for "Silky Smooth" feel
  // Using custom bezier for "snappy start, slow settling" feel (Apple-like)
  const pageVariants = {
    initial: { 
      opacity: 0, 
      x: '30%', 
      scale: 0.95,
      filter: 'blur(8px)'
    },
    animate: { 
      opacity: 1, 
      x: '0%', 
      scale: 1,
      filter: 'blur(0px)'
    },
    exit: { 
      opacity: 0, 
      x: '-10%', // Parallax exit (slower)
      scale: 1.05,
      filter: 'blur(4px)'
    }
  };
  
  // Custom transition physics
  const pageTransition = { 
    duration: 0.65, 
    ease: [0.16, 1, 0.3, 1] // Custom cubic-bezier for "silky" feel
  };

  return (
    // Removed the global bg color transition since TechBackground handles it now.
    // The bg color here is just a fallback for the very bottom layer.
    <div className={`w-full h-screen overflow-hidden font-sans relative ${theme === 'dark' ? 'bg-[#0A0A0A]' : 'bg-[#EBEBF0]'}`}>
      {/* Persistent Background Layer - Stays static during transitions */}
      <TechBackground theme={theme} />
      
      {/* Content Layer - Transitions happen here */}
      <div className="absolute inset-0 z-10 pointer-events-none">
          {/* Note: We need pointer-events-none on the wrapper but pointer-events-auto on children to allow interaction */}
          <AnimatePresence mode="wait">
            {step === 'landing' && (
              <motion.div
                key="landing"
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={pageTransition}
                className="w-full h-full pointer-events-auto"
              >
                <Landing 
                    onStart={handleStart} 
                    language={language} 
                    onToggleLanguage={toggleLanguage} 
                    theme={theme}
                    onToggleTheme={toggleTheme}
                />
              </motion.div>
            )}

            {step === 'builder' && (
              <motion.div
                key="builder"
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={pageTransition}
                className="w-full h-full pointer-events-auto"
              >
                <PersonaBuilder 
                    onBack={handleBuilderBack} 
                    onNext={handleBuilderNext} 
                    language={language} 
                    theme={theme}
                />
              </motion.div>
            )}

            {step === 'details' && (
              <motion.div
                key="details"
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={pageTransition}
                className="w-full h-full pointer-events-auto"
              >
                <PersonaDetails onBack={() => {}} onNext={() => {}} theme={theme} />
              </motion.div>
            )}

            {step === 'search' && (
              <motion.div
                key="search"
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={pageTransition}
                className="w-full h-full pointer-events-auto"
              >
                <JobSearch 
                  onBack={handleSearchBack} 
                  onNext={handleSearchNext} 
                  initialSearchTerm={selectedJob}
                  language={language}
                  theme={theme}
                />
              </motion.div>
            )}

            {step === 'generation' && (
              <motion.div
                key="generation"
                variants={pageVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={pageTransition}
                className="w-full h-full pointer-events-auto"
              >
                <ResumeGeneration 
                    onBack={handleGenerationBack} 
                    onNext={handleGenerationNext} 
                    language={language} 
                    theme={theme}
                />
              </motion.div>
            )}
          </AnimatePresence>
      </div>

      {/* --- GLOBAL OVERLAYS --- */}
      
      {/* 1. PopCat - Persistent Bottom Left Accessory */}
      <div className="absolute bottom-0 left-6 md:left-12 z-50 pointer-events-none">
          {/* Wrapper for positioning, component handles pointer-events-auto */}
          <PopCat isDark={isDark} />
      </div>

      {/* 2. Step Progress - Only visible in Steps 1-4 */}
      <AnimatePresence>
        {currentStepNumber > 0 && (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="absolute bottom-0 left-0 right-0 z-40 flex justify-center pointer-events-none"
            >
                <StepProgress currentStep={currentStepNumber} theme={theme} />
            </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}
