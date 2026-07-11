import React from 'react';
import { motion } from 'motion/react';
import { Check, Loader2 } from 'lucide-react';

interface StepProgressProps {
    currentStep: number;
    theme: 'light' | 'dark';
}

export const StepProgress = ({ currentStep, theme }: StepProgressProps) => {
    const isDark = theme === 'dark';
    
    // Map step numbers to labels
    const steps = [
        { id: 1, label: "INIT", fullLabel: "PERSONA BUILDER" },
        { id: 2, label: "SEARCH", fullLabel: "MARKET SCAN" },
        { id: 3, label: "GENERATE", fullLabel: "RESUME COMPILE" },
    ];

    return (
        <div className="absolute bottom-6 md:bottom-8 left-1/2 -translate-x-1/2 z-50 flex flex-col items-center gap-1.5 pointer-events-none select-none">
            
            {/* Glass Container - Flatter & Compact */}
            <div className={`
                flex items-center gap-1 p-1 rounded-full border backdrop-blur-md shadow-lg transition-colors duration-500
                ${isDark 
                    ? 'bg-black/40 border-white/10 shadow-black/20' 
                    : 'bg-white/40 border-black/5 shadow-black/5'
                }
            `}>
                {steps.map((step) => {
                    const isActive = currentStep === step.id;
                    const isCompleted = currentStep > step.id;
                    
                    return (
                        <div key={step.id} className="relative group">
                            {/* Step Segment - Reduced Size */}
                            <div className={`
                                relative flex items-center justify-center w-6 h-6 md:w-8 md:h-8 rounded-full border transition-all duration-500
                                ${isActive 
                                    ? (isDark ? 'bg-white text-black border-white' : 'bg-[#1A1A1A] text-white border-black')
                                    : isCompleted
                                        ? (isDark ? 'bg-white/10 text-white border-transparent' : 'bg-black/5 text-black border-transparent')
                                        : (isDark ? 'bg-transparent text-white/20 border-white/10' : 'bg-transparent text-black/20 border-black/10')
                                }
                            `}>
                                {/* Icon / Number */}
                                {isCompleted ? (
                                    <Check className="w-2.5 h-2.5 md:w-3.5 md:h-3.5" />
                                ) : isActive ? (
                                    <motion.div
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                                    >
                                        <Loader2 className="w-2.5 h-2.5 md:w-3.5 md:h-3.5" />
                                    </motion.div>
                                ) : (
                                    <span className="text-[9px] md:text-[10px] font-mono font-bold">{step.id}</span>
                                )}
                                
                                {/* Active Pulse Ring */}
                                {isActive && (
                                    <motion.div
                                        initial={{ scale: 1, opacity: 0.5 }}
                                        animate={{ scale: 1.4, opacity: 0 }}
                                        transition={{ duration: 1.5, repeat: Infinity }}
                                        className={`absolute inset-0 rounded-full border ${isDark ? 'border-white' : 'border-black'}`}
                                    />
                                )}
                            </div>

                            {/* Connecting Line (except for last) */}
                            {step.id < steps.length && (
                                <div className={`
                                    absolute top-1/2 left-full -translate-y-1/2 w-3 md:w-6 h-[1px] -mx-0.5 z-[-1] transition-colors duration-500
                                    ${currentStep > step.id 
                                        ? (isDark ? 'bg-white/40' : 'bg-black/40') 
                                        : (isDark ? 'bg-white/10' : 'bg-black/10')
                                    }
                                `} />
                            )}
                            
                            {/* Hover Label (Tooltip style) - Closer positioning */}
                            {isActive && (
                                <motion.div 
                                    initial={{ opacity: 0, y: 3 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap text-[8px] md:text-[9px] font-mono tracking-widest px-1.5 py-0.5 rounded border backdrop-blur-sm
                                        ${isDark 
                                            ? 'bg-black/60 border-white/20 text-white' 
                                            : 'bg-white/60 border-black/10 text-black'
                                        }
                                    `}
                                >
                                    {step.label}
                                </motion.div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Total Progress Text - Smaller */}
            <div className={`text-[8px] tracking-[0.2em] font-mono opacity-40 uppercase ${isDark ? 'text-white' : 'text-black'}`}>
                System Status: Phase {currentStep}/3
            </div>
        </div>
    );
};
