import React, { useEffect, useState } from 'react';
import { ArrowLeft, ArrowRight, Edit2, Download, Search, Loader2 } from 'lucide-react';
import { motion } from 'motion/react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { downloadZip } from '../lib/api';
import { CACHE_KEYS, readCache, writeCache } from '../lib/cache';
import type { GenerationBatch, ResumeData } from '../lib/types';

interface ResumeGenerationProps {
  onBack: () => void;
  onNext: () => void;
  language: 'zh' | 'en';
  theme: 'light' | 'dark';
}

export function ResumeGeneration({ onBack, onNext, language, theme }: ResumeGenerationProps) {
  const t = {
    zh: {
      step3: "STEP 3",
      title: "简历匹配生成",
      edit: "编辑",
      matchScore: "匹配度",
      strengths: "优势",
      gaps: "差距",
      skillMatch: "技能匹配:",
      relevantExp: "相关经历:",
      expGap: "经验不足:",
      techStack: "技术栈:",
      missingExp: "缺少大型全栈项目经验 (AWS, Docker)",
      missingTech: "未提及 Java / Spring Boot",
      intro: "个人简介",
      workExp: "工作经历",
      education: "教育背景",
      downloadZip: "下载 ZIP",
      continueSearch: "继续搜索"
    },
    en: {
      step3: "STEP 3",
      title: "Resume Generation",
      edit: "Edit",
      matchScore: "Match Score",
      strengths: "Strengths",
      gaps: "Gaps",
      skillMatch: "Skill Match:",
      relevantExp: "Relevant Exp:",
      expGap: "Experience Gap:",
      techStack: "Tech Stack:",
      missingExp: "Missing large-scale full-stack project experience (AWS, Docker)",
      missingTech: "Java / Spring Boot not mentioned",
      intro: "Introduction",
      workExp: "Work Experience",
      education: "Education",
      downloadZip: "Download ZIP",
      continueSearch: "Continue Search"
    }
  };

  const isDark = theme === 'dark';
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState('');
  const resume = readCache<ResumeData | null>(CACHE_KEYS.resumeData, null);
  const [latestBatch, setLatestBatch] = useState<GenerationBatch | null>(null);

  useEffect(() => {
    const batches = readCache<GenerationBatch[]>(CACHE_KEYS.generationBatches, []);
    setLatestBatch(batches.length ? batches[batches.length - 1] : null);
  }, []);

  const handleDownloadZip = async () => {
    setError('');
    const batches = readCache<GenerationBatch[]>(CACHE_KEYS.generationBatches, []);
    if (!batches.length) {
      setError('No generated batches yet. Generate a batch on Step 2.');
      return;
    }
    setIsDownloading(true);
    try {
      const latest = batches[batches.length - 1];
      const blob = await downloadZip(latest.jobId);
      const zipName = latest.zipName || 'resumes.zip';
      writeCache(CACHE_KEYS.zipName, zipName);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = zipName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err?.message || 'Download failed.');
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className={`flex flex-col items-center justify-center min-h-screen bg-transparent p-4 overflow-hidden relative font-sans perspective-1000 ${isDark ? 'text-gray-100' : 'text-[#1F1F1F]'}`}>
       
       {/* --- GEOMETRIC LINES OVERLAY --- */}
       
       {/* ------------------------------------------ */}

       {/* Background Header */}
       <div className="absolute top-14 md:top-6 left-0 right-0 text-center z-10 pointer-events-none">
        <h2 className={`text-2xl font-serif italic drop-shadow-sm tracking-tight ${isDark ? 'text-gray-200' : 'text-[#1A1A1A]'}`}>MirrorCareer</h2>
        <p className={`text-[10px] tracking-[0.3em] uppercase font-semibold ${isDark ? 'text-gray-400 opacity-60' : 'text-[#444] opacity-70'}`}>CVfoR1</p>
      </div>

      {/* Navigation - Left */}
      <div className="absolute left-4 md:left-12 top-1/2 -translate-y-1/2 z-30">
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

      {/* Main Content */}
      <div className="w-full max-w-4xl relative flex justify-center z-20 items-center md:items-end">
         {/* Ghost Card - Previous Step (Step 3) */}
         <div className={`absolute left-4 top-1/2 -translate-y-1/2 -translate-x-full w-full max-w-2xl h-[70vh] backdrop-blur-xl rounded-2xl shadow-xl border opacity-40 scale-90 hidden lg:block pointer-events-none -mr-32 transform -rotate-3 mix-blend-soft-light
             ${isDark ? 'bg-black/20 border-white/10' : 'bg-white/20 border-white/30'}
         `}>
           <div className="p-6 space-y-4 opacity-30">
             <div className="h-6 bg-gray-400/20 rounded w-1/3"></div>
             <div className="grid grid-cols-2 gap-4">
               <div className="h-10 bg-gray-400/20 rounded"></div>
               <div className="h-10 bg-gray-400/20 rounded"></div>
             </div>
             <div className="h-32 bg-gray-400/20 rounded w-full"></div>
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
           className="w-full max-w-2xl z-20 mx-4 h-[65vh] md:h-[75vh] flex flex-col"
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
            <span className={`text-xs font-bold tracking-wide uppercase drop-shadow-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{t[language].step3}</span>
            <CardTitle className={`text-lg font-bold drop-shadow-sm ${isDark ? 'text-white' : 'text-[#1F1F1F]'}`}>{t[language].title}</CardTitle>
          </div>
        </CardHeader>
        
        <CardContent className="p-5 md:p-8 pt-6 md:pt-8 flex-1 overflow-hidden flex flex-col gap-6 md:gap-8 relative z-10">
          
          {error && (
            <div className={`text-xs font-medium ${isDark ? 'text-red-300' : 'text-red-600'}`}>
              {error}
            </div>
          )}
          
          <ScrollArea className="flex-1 h-full -mr-4 pr-4">
            <div className="pb-10">

              {/* Resume Preview */}
              <div className="relative group/paper">
                  {/* Paper Stack Effect - Less rotated/rigid in dark mode */}
                  <div className={`absolute top-2 left-2 right-2 h-full border shadow-sm z-0 transition-transform
                      ${isDark 
                          ? 'bg-[#1A1A1A] border-white/10 rounded-none rotate-0 group-hover/paper:translate-y-[-2px]' 
                          : 'bg-white border-gray-200 rounded-xl rotate-1 group-hover/paper:rotate-2'
                      }
                  `}></div>
                  <div className={`absolute top-1 left-1 right-1 h-full border shadow-sm z-0 transition-transform
                      ${isDark 
                          ? 'bg-[#1A1A1A] border-white/10 rounded-none rotate-0 group-hover/paper:translate-y-[-4px]' 
                          : 'bg-white border-gray-200 rounded-xl -rotate-1 group-hover/paper:-rotate-2'
                      }
                  `}></div>

                  <div className={`shadow-[0_10px_40px_-10px_rgba(0,0,0,0.1)] p-8 min-h-[800px] border relative transition-all z-10 transform
                      ${isDark 
                          ? 'bg-[#111] border-white/10 text-gray-200 rounded-none group-hover/paper:translate-y-[-6px]' 
                          : 'bg-white border-gray-100 text-[#1F1F1F] rounded-xl group-hover/paper:translate-y-[-4px]'
                      }
                  `}>
                      <div className="max-w-lg mx-auto space-y-8 font-serif">
                        <p className="text-xs font-sans">
                          {language === 'zh'
                            ? '\u5df2\u786e\u8ba4\u7684\u7b80\u5386\u8d44\u6599\u9884\u89c8\u3002\u5404\u804c\u4f4d\u7684\u5b9a\u5236\u7b80\u5386\u8bf7\u67e5\u770b ZIP \u4e2d\u7684 PDF\u3002'
                            : 'Confirmed resume details. See the PDFs in the ZIP for each job-specific summary.'}
                        </p>
                        {resume ? <>
                          <div>
                            <h1 className="text-3xl font-bold">{resume.name}</h1>
                            <p className="text-xs">{resume.contact}</p>
                          </div>
                          <section>
                            <h3 className="font-bold">{t[language].intro}</h3>
                            <p className="text-sm whitespace-pre-wrap">{resume.intro}</p>
                          </section>
                          {resume.skills.length > 0 && <section>
                            <h3 className="font-bold">{language === 'zh' ? '\u6280\u80fd' : 'Skills'}</h3>
                            <p className="text-sm">{resume.skills.join(' ? ')}</p>
                          </section>}
                          <section>
                            <h3 className="font-bold">{t[language].workExp}</h3>
                            {resume.experience.map((entry, index) => <div key={index} className="my-4 text-sm">
                              <strong>{entry.role} ? {entry.company}</strong>
                              <p>{entry.period}</p>
                              <ul className="list-disc pl-4">{entry.details.map((detail, i) => <li key={i}>{detail}</li>)}</ul>
                            </div>)}
                          </section>
                          <section>
                            <h3 className="font-bold">{t[language].education}</h3>
                            {resume.education.map((entry, index) => <div key={index} className="my-4 text-sm">
                              <strong>{entry.school}</strong><p>{entry.degree}</p><p>{entry.period}</p>
                            </div>)}
                          </section>
                          {(['certifications', 'community', 'additional', 'languages'] as const).map((field) =>
                            resume[field]?.length ? <section key={field}>
                              <h3 className="font-bold capitalize">{field}</h3>
                              <ul className="text-sm list-disc pl-4">{resume[field]!.map((value, index) => <li key={index}>{value}</li>)}</ul>
                            </section> : null)}
                        </> : <p>No resume data. Return to Step 1 to upload your resume.</p>}
                      </div>
                  </div>
              </div>
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
      </motion.div>
      </div>
      
       {/* Navigation - Right */}
       <div className="absolute right-4 md:right-12 z-30 flex flex-col gap-4">
         
         {/* Download ZIP Button */}
         <Button
          variant="default"
          size="icon"
          className={`rounded-full w-14 h-14 border transition-all duration-300 group shadow-lg
             ${isDark 
                ? 'bg-white text-black border-white/20 hover:bg-gray-200' 
                : 'bg-[#1A1A1A] text-white border-white/10 hover:bg-[#333]'
             }
          `}
          onClick={handleDownloadZip}
          disabled={isDownloading || !latestBatch}
          title={t[language].downloadZip}
        >
          {isDownloading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Download className="w-5 h-5 group-hover:scale-110 transition-transform" />
          )}
        </Button>

         {/* Continue Search Button */}
         <Button
          variant="outline"
          size="icon"
          className={`rounded-full w-14 h-14 border transition-all duration-300 group
             ${isDark 
                ? 'bg-[#1A1A1A] border-white/20 shadow-[6px_6px_12px_rgba(0,0,0,0.5),-6px_-6px_12px_rgba(255,255,255,0.05)] hover:bg-[#222] text-gray-300' 
                : 'bg-[#E0E5EC] border-white/50 shadow-[6px_6px_12px_#A3A7AE,-6px_-6px_12px_#FFFFFF] hover:shadow-[inset_6px_6px_12px_#A3A7AE,inset_-6px_-6px_12px_#FFFFFF] hover:scale-100 text-gray-600'
             }
          `}
          onClick={onBack} // Go back to Search
          title={t[language].continueSearch}
        >
          <Search className="w-5 h-5 group-hover:scale-110 transition-transform" />
        </Button>
      </div>

    </div>
  );
}
