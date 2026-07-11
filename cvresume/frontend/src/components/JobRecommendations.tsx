import React, { useState } from 'react';
import { ArrowLeft, ArrowRight, Check, Briefcase } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { motion } from 'motion/react';

interface JobRecommendationsProps {
  onBack: () => void;
  onNext: () => void;
  onSelectJob?: (jobTitle: string) => void;
  language: 'zh' | 'en';
  theme: 'light' | 'dark';
}

export function JobRecommendations({ onBack, onNext, onSelectJob, language, theme }: JobRecommendationsProps) {
  const t = {
    zh: {
      step2: "STEP 2",
      title: "智能岗位推荐",
      analyzing: "分析中...",
      aiRecommend: "AI 推荐",
      description: "基于您的画像，AI 将推荐最匹配的职位方向",
      startRecommend: "开始推荐",
      recommendAgain: "重新推荐",
      done: "完成",
      keywords: "关键词"
    },
    en: {
      step2: "STEP 2",
      title: "AI Job Recommendations",
      analyzing: "Analyzing...",
      aiRecommend: "AI Recommend",
      description: "Based on your persona, AI will recommend the most matching job directions",
      startRecommend: "Start Recommendation",
      recommendAgain: "Recommend Again",
      done: "Done",
      keywords: "KEYWORDS"
    }
  };
  const [isRecommending, setIsRecommending] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const handleStart = () => {
    setIsRecommending(true);
    setTimeout(() => {
      setIsRecommending(false);
      setShowResults(true);
    }, 1500);
  };

  const jobs = [
    { title: "全栈工程师 Full Stack Engineer", tags: "React, Fastapi, Flask" },
    { title: "Software Engineer", tags: "Fastapi, Flask" },
    { title: "Backend Engineer", tags: "Fastapi, Flask" },
    { title: "前端工程师 Frontend Engineer", tags: "Javascript, React" },
    { title: "数据科学家 Data Scientist", tags: "statistics, model" },
  ];

  const handleJobClick = (title: string) => {
    if (onSelectJob) {
      onSelectJob(title);
    } else {
      onNext();
    }
  };

  const isDark = theme === 'dark';

  return (
    <div className={`flex flex-col items-center justify-center min-h-screen bg-transparent p-4 relative overflow-hidden font-sans perspective-1000 ${isDark ? 'text-gray-100' : 'text-[#1F1F1F]'}`}>
       
       {/* --- GEOMETRIC LINES OVERLAY --- */}
       
       {/* ------------------------------------------ */}

       {/* Background Header */}
       <div className="absolute top-14 md:top-6 left-0 right-0 text-center z-10 pointer-events-none">
        <h2 className={`text-2xl font-serif italic drop-shadow-sm tracking-tight ${isDark ? 'text-gray-200' : 'text-[#1A1A1A]'}`}>MirrorCareer</h2>
        <p className={`text-[10px] tracking-[0.3em] uppercase font-semibold ${isDark ? 'text-gray-400 opacity-60' : 'text-[#444] opacity-70'}`}>CVfoR1</p>
      </div>

      {/* Navigation - Left (Desktop) */}
      <div className="hidden md:block absolute left-12 top-1/2 -translate-y-1/2 z-30">
        <Button
          variant="outline"
          size="icon"
          className={`rounded-full w-14 h-14 border transition-all duration-300 group
             ${isDark 
                ? 'bg-[#1A1A1A] border-white/20 shadow-[6px_6px_12px_rgba(0,0,0,0.5),-6px_-6px_12px_rgba(255,255,255,0.05)] hover:bg-[#222] text-gray-300' 
                : 'bg-[#E0E5EC] border-white/50 shadow-[6px_6px_12px_#A3A7AE,-6px_-6px_12px_#FFFFFF] hover:shadow-[inset_6px_6px_12px_#A3A7AE,inset_-6px_-6px_12px_#FFFFFF] hover:scale-100 text-gray-600'
             }
          `}
          onClick={onBack}
        >
          <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
        </Button>
      </div>

       {/* Navigation - Mobile (Top Left) */}
       <div className="md:hidden absolute left-4 top-12 z-30">
        <Button
          variant="ghost"
          size="icon"
          className={`rounded-full w-10 h-10 border transition-all duration-300 backdrop-blur-md
             ${isDark 
                ? 'bg-black/20 border-white/10 text-gray-300 hover:bg-white/10' 
                : 'bg-white/40 border-white/40 text-gray-700 hover:bg-white/60'
             }
          `}
          onClick={onBack}
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
      </div>

      {/* Main Content */}
      <div className="w-full max-w-4xl relative flex justify-center z-20 items-center md:items-end">
         {/* Ghost Card - Previous Step (Step 1) */}
         <div className={`absolute left-4 top-1/2 -translate-y-1/2 -translate-x-full w-full max-w-2xl h-[70vh] backdrop-blur-xl rounded-2xl shadow-xl border opacity-40 scale-90 hidden lg:block pointer-events-none -mr-32 transform -rotate-3 mix-blend-soft-light
             ${isDark ? 'bg-black/20 border-white/10' : 'bg-white/20 border-white/30'}
         `}>
           <div className="p-6 space-y-4 opacity-30">
             <div className="h-6 bg-gray-400/20 rounded w-1/4"></div>
             <div className="space-y-2">
               <div className="h-32 bg-gray-400/20 rounded w-full"></div>
             </div>
           </div>
        </div>
        
        {/* Ghost Card - Next Step (Step 3) */}
        <div className={`absolute right-4 top-1/2 -translate-y-1/2 translate-x-full w-full max-w-2xl h-[70vh] backdrop-blur-xl rounded-2xl shadow-xl border opacity-40 scale-90 hidden lg:block pointer-events-none -ml-32 transform rotate-3 mix-blend-soft-light
             ${isDark ? 'bg-black/20 border-white/10' : 'bg-white/20 border-white/30'}
        `}>
           <div className="p-6 space-y-4 opacity-30">
             <div className="h-6 bg-gray-400/20 rounded w-1/3"></div>
             <div className="grid grid-cols-2 gap-4">
               <div className="h-10 bg-gray-400/20 rounded"></div>
               <div className="h-10 bg-gray-400/20 rounded"></div>
             </div>
           </div>
        </div>

        {/* REFLECTION UNDER THE CARD */}
        <div className={`absolute bottom-[-40px] left-4 right-4 h-16 blur-2xl rounded-[50%] scale-x-90 z-0 ${isDark ? 'bg-white/5' : 'bg-black/20'}`}></div>

        {/* MAIN CARD CONTAINER - Spring Animation */}
        <motion.div
           initial={{ opacity: 0, y: 40, scale: 0.95 }}
           animate={{ opacity: 1, y: 0, scale: 1 }}
           exit={{ opacity: 0, y: -40, scale: 0.95 }}
           transition={{ type: "spring", damping: 25, stiffness: 300 }}
           className="w-full max-w-2xl z-20 mx-4 h-[75vh] flex flex-col"
        >
          <Card className={`w-full h-full backdrop-blur-2xl border-0 flex flex-col relative overflow-hidden group transition-colors duration-500
              ${isDark 
                 ? 'bg-black/40 shadow-[0_30px_60px_-10px_rgba(0,0,0,0.5),inset_0_0_0_1px_rgba(255,255,255,0.1)] rounded-none' 
                 : 'bg-white/60 shadow-[0_30px_60px_-10px_rgba(30,30,35,0.15),inset_0_0_0_1px_rgba(255,255,255,0.4)] rounded-3xl'
              }
          `}>
          
          {/* Tech Line Corners for Dark Mode */}
          {isDark && (
              <>
                  <div className="absolute top-0 left-0 w-8 h-8 border-l-2 border-t-2 border-white/30 z-50"></div>
                  <div className="absolute top-0 right-0 w-8 h-8 border-r-2 border-t-2 border-white/30 z-50"></div>
                  <div className="absolute bottom-0 left-0 w-8 h-8 border-l-2 border-b-2 border-white/30 z-50"></div>
                  <div className="absolute bottom-0 right-0 w-8 h-8 border-r-2 border-b-2 border-white/30 z-50"></div>
                  
                  {/* Tech Grid Background for Card */}
                  <div className="absolute inset-0 pointer-events-none opacity-10" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
              </>
          )}

          {/* 1. Glossy Edge Highlight (Top) */}
          <div className="absolute inset-x-0 top-0 h-[1px] bg-gradient-to-r from-transparent via-white/80 to-transparent z-50 opacity-80"></div>
          
          {/* 2. Glass Shine (Diagonal) */}
          <div className={`absolute inset-0 bg-gradient-to-tr pointer-events-none z-10 opacity-30 group-hover:opacity-40 transition-opacity duration-1000
             ${isDark ? 'from-white/5 via-white/10 to-transparent' : 'from-white/5 via-white/20 to-transparent'}
          `}></div>

          <CardHeader className={`flex flex-row items-center justify-between border-b pb-4 shrink-0 z-20 relative backdrop-blur-sm
               ${isDark ? 'bg-black/20 border-white/10' : 'bg-white/30 border-gray-200/40'}
          `}>
            <div className="flex items-center gap-4">
              <span className={`text-xs font-bold tracking-wide uppercase drop-shadow-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{t[language].step2}</span>
              <CardTitle className={`text-lg font-bold drop-shadow-sm ${isDark ? 'text-white' : 'text-[#1F1F1F]'}`}>{t[language].title}</CardTitle>
            </div>
            {!showResults && (
              <Button 
                onClick={handleStart} 
                disabled={isRecommending} 
                size="sm" 
                className={`border px-4 text-xs shadow-[2px_2px_5px_rgba(0,0,0,0.05)] backdrop-blur-sm transition-all
                   ${isDark 
                      ? 'bg-white/10 border-white/20 text-white hover:bg-white/20 rounded-none' 
                      : 'bg-white/50 border-white/60 text-[#2D2D2D] hover:bg-white rounded-full'
                   }
                `}
              >
                {isRecommending ? <Briefcase className="w-3 h-3 animate-bounce mr-2" /> : <Briefcase className="w-3 h-3 mr-2" />}
                {isRecommending ? t[language].analyzing : t[language].aiRecommend}
              </Button>
            )}
          </CardHeader>
        
        <CardContent className="pt-8 flex-1 overflow-y-auto z-10 relative">
          {!showResults ? (
            <div className="h-full flex flex-col items-center justify-center space-y-6 animate-in fade-in duration-500">
               <div className="relative w-24 h-24 flex items-center justify-center">
                  <div className="absolute inset-0 bg-blue-100 rounded-full blur-xl opacity-50 animate-pulse"></div>
                  <Briefcase className={`w-12 h-12 relative z-10 opacity-80 ${isDark ? 'text-gray-300' : 'text-gray-400'}`} />
               </div>
               <p className={`font-medium tracking-wide drop-shadow-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{t[language].description}</p>
               
               {/* MIRROR TECH HUD BUTTON */}
               <Button 
                onClick={handleStart}
                className={`relative overflow-hidden text-white border px-12 py-6 text-sm font-bold tracking-wide transition-all shadow-lg hover:shadow-xl hover:scale-[1.01] active:scale-[0.99] group
                   ${isDark 
                      ? 'bg-white text-black border-white/20 hover:bg-gray-200 rounded-none' 
                      : 'bg-[#222224] border-white/10 rounded-lg'
                   }
                `}
                disabled={isRecommending}
              >
                 {/* --- GEOMETRIC TECH OVERLAY --- */}
                      
                {/* 1. Large Rotating Arc (Right side) */}
                <div className={`absolute top-1/2 right-[-20%] w-[120%] h-[200%] -translate-y-1/2 rounded-full border border-dashed animate-[spin_10s_linear_infinite] pointer-events-none opacity-40
                     ${isDark ? 'border-black/20' : 'border-white/10'}
                `}></div>
                
                {/* 2. Thin Crosshair Lines */}
                <div className={`absolute top-0 bottom-0 left-8 w-[1px] pointer-events-none ${isDark ? 'bg-black/10' : 'bg-white/5'}`}></div>
                <div className={`absolute left-0 right-0 top-1/2 h-[1px] pointer-events-none ${isDark ? 'bg-black/10' : 'bg-white/5'}`}></div>

                {/* 3. Corner Markers */}
                <div className={`absolute top-1.5 left-1.5 w-2 h-2 border-l border-t pointer-events-none ${isDark ? 'border-black/30' : 'border-white/30'}`}></div>
                <div className={`absolute bottom-1.5 right-1.5 w-2 h-2 border-r border-b pointer-events-none ${isDark ? 'border-black/30' : 'border-white/30'}`}></div>

                {/* 4. Scanning Line (Subtle) */}
                <div className={`absolute top-0 bottom-0 left-0 w-[2px] blur-[1px] animate-[shimmer_3s_infinite] pointer-events-none ${isDark ? 'bg-black/20' : 'bg-white/20'}`}></div>


                <span className={`relative z-10 flex items-center gap-2 ${isDark ? 'text-black' : 'text-white'}`}>
                   {isRecommending ? t[language].analyzing : t[language].startRecommend}
                   {!isRecommending && <ArrowRight className={`w-4 h-4 ${isDark ? 'text-black/70' : 'text-white/70'}`} />}
                </span>
              </Button>
            </div>
          ) : (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
              <div className="flex items-center gap-3 mb-6">
                 <Button className={`border h-8 text-xs shadow-sm ${isDark ? 'bg-white/10 border-white/10 text-white hover:bg-white/20 rounded-none' : 'bg-white border-gray-200 hover:bg-gray-50 text-gray-700 rounded-full'}`} onClick={() => setShowResults(false)}>
                   {t[language].recommendAgain}
                 </Button>
                 <span className={`text-sm flex items-center gap-1 font-medium px-3 py-1 border ${isDark ? 'bg-white/5 border-white/10 text-gray-300 rounded-none' : 'bg-gray-100 border-gray-200 text-gray-800 rounded-full'}`}>
                    {t[language].done} <Check className="w-3 h-3" />
                 </span>
              </div>

              <div className="space-y-4">
                {jobs.map((job, index) => (
                  <motion.div 
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1, type: "spring", stiffness: 100 }}
                    className={`group relative p-5 border shadow-[0_4px_10px_rgba(0,0,0,0.02)] hover:shadow-[0_10px_25px_-5px_rgba(0,0,0,0.1)] transition-all duration-300 cursor-pointer backdrop-blur-md
                        ${isDark 
                           ? 'bg-white/5 hover:bg-white/10 border-white/10 hover:border-white/30 rounded-none' 
                           : 'bg-white/40 hover:bg-white/80 border-white/60 hover:border-white rounded-xl'
                        }
                    `}
                    onClick={() => handleJobClick(job.title)}
                  >
                    {/* Hover Glow */}
                    <div className={`absolute inset-0 bg-gradient-to-r from-blue-50/0 via-blue-50/30 to-purple-50/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none ${isDark ? 'rounded-none' : 'rounded-xl'}`}></div>

                    <div className="flex items-start gap-4 relative z-10">
                      <div className={`mt-1 w-6 h-6 flex items-center justify-center font-mono text-xs font-bold transition-colors duration-300
                          ${isDark 
                             ? 'bg-white/10 text-gray-400 group-hover:bg-white group-hover:text-black rounded-none' 
                             : 'bg-gray-200/50 text-gray-500 group-hover:bg-[#2D2D2D] group-hover:text-white rounded-full'
                          }
                      `}>{(index + 1).toString()}</div>
                      <div>
                        <div className={`font-bold text-lg transition-colors ${isDark ? 'text-gray-200 group-hover:text-white' : 'text-[#1F1F1F] group-hover:text-black'}`}>{job.title}</div>
                        <div className="text-xs text-gray-500 mt-2 flex items-center gap-2">
                          <span className="font-semibold text-gray-400 uppercase tracking-wider text-[10px]">{t[language].keywords}</span> 
                          <span className={`h-1 w-1 rounded-full bg-gray-300`}></span>
                          {job.tags}
                        </div>
                      </div>
                      <div className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity -translate-x-2 group-hover:translate-x-0 duration-300">
                        <ArrowRight className="w-5 h-5 text-gray-400" />
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      </motion.div>
      </div>

      {/* Navigation - Right */}
      <div className="absolute right-4 md:right-12 z-30">
         <Button
          variant="outline"
          size="icon"
          className={`rounded-full w-14 h-14 border transition-all duration-300 group
             ${isDark 
                ? 'bg-[#1A1A1A] border-white/20 shadow-[6px_6px_12px_rgba(0,0,0,0.5),-6px_-6px_12px_rgba(255,255,255,0.05)] hover:bg-[#222] text-gray-300' 
                : 'bg-[#E0E5EC] border-white/50 shadow-[6px_6px_12px_#A3A7AE,-6px_-6px_12px_#FFFFFF] hover:shadow-[inset_6px_6px_12px_#A3A7AE,inset_-6px_-6px_12px_#FFFFFF] hover:scale-100 text-gray-600'
             }
          `}
          onClick={onNext}
        >
          <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
        </Button>
      </div>
    </div>
  );
}
