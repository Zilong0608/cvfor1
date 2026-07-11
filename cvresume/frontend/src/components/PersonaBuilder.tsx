import React, { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, FileText, Check, Edit2, ChevronUp } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardHeader, CardTitle } from './ui/card';
import { Textarea } from './ui/textarea';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { motion, AnimatePresence } from 'motion/react';
import { parseResume } from '../lib/api';
import { CACHE_KEYS, readCache, writeCache } from '../lib/cache';
import type { ResumeData } from '../lib/types';

interface PersonaBuilderProps {
  onBack: () => void;
  onNext: () => void;
  language: 'zh' | 'en';
  theme: 'light' | 'dark';
}

export function PersonaBuilder({ onBack, onNext, language, theme }: PersonaBuilderProps) {
  const t = {
    zh: {
      step1: "STEP 1",
      title: "画像构建",
      done: "完成",
      edit: "编辑",
      collapse: "收起",
      clear: "清空",
      inputLabel: "自然语言输入",
      placeholder: "在此输入或粘贴你的经历描述，AI 将自动提取关键画像信息...",
      // or: "或者", // Removed
      fileParsing: "简历文件上传", // Updated
      fileSupport: "支持 PDF, DOCX, HTML",
      selectFile: "点击上传简历", // Updated
      dropFile: "或拖拽文件到此处", // Added
      noFile: "未选择任何文件",
      analyzing: "系统分析中...",
      complete: "分析完成",
      initiate: "开始分析",
      completeText: "分析完成 ✓",
      intro: "个人简介",
      education: "教育背景",
      experience: "工作经历"
    },
    en: {
      step1: "STEP 1",
      title: "Persona Building",
      done: "Done",
      edit: "Edit",
      collapse: "Collapse",
      clear: "Clear",
      inputLabel: "Natural Language Input",
      placeholder: "Enter or paste your experience description here, AI will automatically extract key persona information...",
      // or: "OR", // Removed
      fileParsing: "Resume Upload", // Updated
      fileSupport: "Supports PDF, DOCX, HTML",
      selectFile: "Click to Upload", // Updated
      dropFile: "Or Drag & Drop File Here", // Added
      noFile: "No file selected",
      analyzing: "SYSTEM ANALYZING...",
      complete: "ANALYSIS COMPLETE",
      initiate: "INITIATE ANALYSIS",
      completeText: "Analysis Complete ✓",
      intro: "Introduction",
      education: "Education",
      experience: "Work Experience"
    }
  };
  // const [text, setText] = useState(''); // Removed
  const defaultPersonaData: ResumeData = {
    name: "",
    contact: "",
    intro: "",
    education: [],
    experience: [],
    skills: [],
  };

  const cachedPersona = readCache<ResumeData | null>(CACHE_KEYS.resumeData, null);
  const cachedFileName = readCache<string>(CACHE_KEYS.resumeFileName, "");

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isComplete, setIsComplete] = useState(Boolean(cachedPersona));
  const [showDetails, setShowDetails] = useState(Boolean(cachedPersona));
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [fileName, setFileName] = useState(cachedFileName);

  const [personaData, setPersonaData] = useState<ResumeData>(
    cachedPersona || defaultPersonaData
  );

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isComplete) return;
    writeCache(CACHE_KEYS.resumeData, personaData);
  }, [personaData, isComplete]);

  const handleFileSelect = (file: File | null) => {
    if (!file) return;
    setResumeFile(file);
    setFileName(file.name);
    writeCache(CACHE_KEYS.resumeFileName, file.name);
  };

  const handleAnalyze = async () => {
    if (!resumeFile) {
      setError(t[language].noFile);
      return;
    }
    setError("");
    setIsAnalyzing(true);
    try {
      const parsed = await parseResume({ file: resumeFile });
      setPersonaData(parsed);
      writeCache(CACHE_KEYS.resumeData, parsed);
      setIsComplete(true);
      setShowDetails(true);
    } catch (err: any) {
      setError(err?.message || "Analyze failed.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCollapse = () => {
    setShowDetails(false);
    setIsEditing(false);
  };

  const isDark = theme === 'dark';

  return (
    <div className={`flex flex-col items-center justify-center min-h-screen bg-transparent p-4 overflow-hidden relative font-sans perspective-1000 ${isDark ? 'text-gray-100' : 'text-[#1F1F1F]'}`}>
       
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

      {/* Main Content - Center Card */}
      <div className="w-full max-w-4xl relative flex justify-center z-20 items-center md:items-end">
        
        {/* Ghost Card - Next Step */}
        <div className={`absolute right-4 top-1/2 -translate-y-1/2 translate-x-full w-full max-w-2xl h-[70vh] backdrop-blur-xl rounded-2xl shadow-xl border opacity-40 scale-90 hidden lg:block pointer-events-none -ml-32 transform rotate-3 mix-blend-soft-light
            ${isDark ? 'bg-black/20 border-white/10' : 'bg-white/20 border-white/30'}
        `}></div>

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
          <Card className={`w-full h-full backdrop-blur-2xl border-0 flex flex-col overflow-hidden relative group transition-colors duration-500
              ${isDark 
                 ? 'bg-black/40 shadow-[0_30px_60px_-10px_rgba(0,0,0,0.5),inset_0_0_0_1px_rgba(255,255,255,0.1)] rounded-none' // Tech style: No rounded corners in dark mode? Or maybe just tighter?
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
              <span className={`text-xs font-bold tracking-wide uppercase drop-shadow-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{t[language].step1}</span>
              <CardTitle className={`text-lg font-bold drop-shadow-sm ${isDark ? 'text-white' : 'text-[#1F1F1F]'}`}>{t[language].title}</CardTitle>
            </div>
          
            <AnimatePresence mode="wait">
              {showDetails ? (
                <motion.div 
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="flex gap-2"
                >
                  {isEditing ? (
                    <Button variant="outline" size="sm" className="text-xs rounded-full h-8 px-4 gap-1 bg-gray-600 text-white hover:bg-gray-700 border-0 shadow-lg" onClick={() => setIsEditing(false)}>
                      <Check className="w-3 h-3" /> {t[language].done}
                    </Button>
                  ) : (
                    <>
                      <Button variant="outline" size="sm" className={`text-xs h-8 px-4 gap-1 border hover:bg-opacity-80 backdrop-blur-sm shadow-[2px_2px_5px_rgba(0,0,0,0.05)]
                          ${isDark ? 'bg-white/10 border-white/20 text-gray-200 hover:bg-white/20 rounded-none' : 'bg-white/50 border-white/60 text-gray-700 hover:bg-white rounded-full'}
                      `} onClick={() => setIsEditing(true)}>
                        <Edit2 className="w-3 h-3" /> {t[language].edit}
                      </Button>
                      <Button variant="outline" size="sm" className={`text-xs h-8 px-4 gap-1 border hover:bg-opacity-80 backdrop-blur-sm shadow-[2px_2px_5px_rgba(0,0,0,0.05)]
                          ${isDark ? 'bg-white/10 border-white/20 text-gray-200 hover:bg-white/20 rounded-none' : 'bg-white/50 border-white/60 text-gray-700 hover:bg-white rounded-full'}
                      `} onClick={handleCollapse}>
                        {t[language].collapse} <ChevronUp className="w-3 h-3" />
                      </Button>
                    </>
                  )}
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                   {/* Clear button removed */}
                </motion.div>
              )}
            </AnimatePresence>
          </CardHeader>

          <div className="relative flex-1 overflow-hidden h-full z-10">
               {/* Form Content */}
              <ScrollArea className="h-full">
                <div className="p-5 md:p-8 pt-6 md:pt-8 space-y-6 md:space-y-8">
                  
                  {/* File Upload Section - Redesigned */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                       <label className={`text-sm font-semibold ml-1 drop-shadow-sm flex items-center gap-2 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${isDark ? 'bg-white' : 'bg-black'}`}></span>
                          {t[language].fileParsing}
                       </label>
                    </div>
                    
                    <div
                      className={`group relative border-2 border-dashed transition-all duration-500 p-8 flex flex-col items-center justify-center gap-4 cursor-pointer overflow-hidden
                        ${isDark 
                            ? 'border-white/10 hover:border-white/30 bg-black/20 hover:bg-black/40 rounded-none' 
                            : 'border-gray-300 hover:border-gray-400 bg-gray-50/50 hover:bg-gray-100/50 rounded-2xl'
                        }
                    `}
                      role="button"
                      tabIndex={0}
                      onClick={() => fileInputRef.current?.click()}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          fileInputRef.current?.click();
                        }
                      }}
                      onDragOver={(e) => {
                        e.preventDefault();
                      }}
                      onDrop={(e) => {
                        e.preventDefault();
                        const file = e.dataTransfer.files?.[0];
                        if (file) handleFileSelect(file);
                      }}
                    >
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,.docx,.txt,.html"
                        className="hidden"
                        onChange={(e) => handleFileSelect(e.target.files?.[0] || null)}
                      />
                      {/* Tech Grid Background (Dark Mode) */}
                      {isDark && (
                          <div className="absolute inset-0 pointer-events-none opacity-5 group-hover:opacity-10 transition-opacity" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
                      )}
                      
                      {/* Scanning Line Animation */}
                      <div className={`absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-current to-transparent opacity-0 group-hover:opacity-50 group-hover:animate-[shimmer_2s_infinite]
                          ${isDark ? 'text-white' : 'text-black'}
                      `}></div>

                      <div className={`p-4 rounded-full shadow-lg transition-transform group-hover:scale-110 duration-500 relative
                          ${isDark ? 'bg-white/5 text-gray-200 shadow-black/50' : 'bg-white text-gray-700 shadow-gray-200'}
                      `}>
                         <FileText className="w-8 h-8" />
                         {/* Pulse Ring */}
                         <div className={`absolute inset-0 rounded-full border animate-ping opacity-20 ${isDark ? 'border-white' : 'border-black'}`}></div>
                      </div>
                      
                      <div className="text-center space-y-1 z-10">
                        <div className={`font-bold text-base tracking-wide ${isDark ? 'text-white' : 'text-gray-900'}`}>
                           {t[language].selectFile}
                        </div>
                        <div className={`text-xs font-medium ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                           {t[language].dropFile}
                        </div>
                      </div>

                      <div className={`text-[10px] uppercase tracking-widest px-3 py-1 border mt-2
                          ${isDark ? 'text-gray-500 border-white/10 bg-white/5' : 'text-gray-400 border-gray-200 bg-white'}
                      `}>
                          {t[language].fileSupport}
                      </div>
                      <div className={`text-[10px] mt-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                        {fileName ? fileName : t[language].noFile}
                      </div>
                      
                      {/* Corner Accents */}
                      {isDark && (
                          <>
                              <div className="absolute top-0 left-0 w-3 h-3 border-l border-t border-white/30"></div>
                              <div className="absolute top-0 right-0 w-3 h-3 border-r border-t border-white/30"></div>
                              <div className="absolute bottom-0 left-0 w-3 h-3 border-l border-b border-white/30"></div>
                              <div className="absolute bottom-0 right-0 w-3 h-3 border-r border-b border-white/30"></div>
                          </>
                      )}
                    </div>
                  </div>

                  {/* Action Button - MIRROR TECH HUD BUTTON */}
                  <div className="pt-4 pb-2 flex items-center justify-center md:justify-start gap-4">
                    <Button 
                      className={`relative w-full md:w-auto overflow-hidden text-white border px-12 py-6 h-auto text-base font-medium tracking-wide transition-all shadow-lg hover:shadow-xl hover:scale-[1.01] active:scale-[0.99] group 
                        ${isDark
                           ? 'bg-white text-black border-white/20 hover:bg-gray-200 rounded-none'
                           : 'bg-[#222224] border-white/10 rounded-lg'
                        }
                        ${isComplete 
                            ? (isDark ? 'bg-white/90 border-black/10' : 'bg-[#1A1A1A] border-white/40 shadow-white/5') 
                            : ''
                        }
                      `}
                      onClick={handleAnalyze}
                      disabled={isAnalyzing}
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

                      {/* Content */}
                      {isAnalyzing ? (
                        <span className={`flex items-center gap-2 relative z-10 ${isDark ? 'text-black' : 'text-gray-200'}`}>
                          <span className={`w-2 h-2 rounded-full animate-pulse ${isDark ? 'bg-black/80' : 'bg-white/80'}`}></span>
                          {t[language].analyzing}
                        </span>
                      ) : isComplete ? (
                        <span className={`flex items-center gap-2 relative z-10 ${isDark ? 'text-black' : 'text-white'}`}><Check className={`w-5 h-5 ${isDark ? 'text-black' : 'text-white'}`} /> {t[language].complete}</span>
                      ) : (
                        <span className="flex items-center gap-3 relative z-10">
                           {t[language].initiate}
                           <ArrowRight className={`w-4 h-4 ${isDark ? 'text-black/70' : 'text-white/70'}`} />
                        </span>
                      )}
                    </Button>
                    {isComplete && <span className={`text-sm font-bold drop-shadow-sm animate-in fade-in zoom-in ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>{t[language].completeText}</span>}
                  </div>
                  {error && (
                    <div className={`text-xs font-medium ${isDark ? 'text-red-300' : 'text-red-600'}`}>
                      {error}
                    </div>
                  )}
                </div>
              </ScrollArea>

              {/* Details Overlay */}
              <AnimatePresence>
                {showDetails && (
                  <motion.div
                    initial={{ y: "100%" }}
                    animate={{ y: 0 }}
                    exit={{ y: "100%" }}
                    transition={{ type: "spring", damping: 25, stiffness: 200, mass: 0.8 }}
                    className={`absolute inset-x-0 bottom-0 top-0 backdrop-blur-xl z-30 flex flex-col shadow-[0_-10px_40px_rgba(0,0,0,0.15)] overflow-hidden
                        ${isDark 
                            ? 'bg-[#050505] border-t border-white/10 rounded-none' 
                            : 'bg-[#F7F8FA]/95 border-t border-white rounded-t-2xl'
                        }
                    `}
                  >
                    <div className="w-16 h-1.5 bg-gray-300/50 rounded-full mx-auto mt-4 mb-2 shrink-0" />
                    <ScrollArea className="flex-1 h-full w-full">
                      <div className="p-8 pb-24 space-y-8 max-w-xl mx-auto">
                         
                         {/* Header Info */}
                        <div>
                          {isEditing ? (
                            <div className="space-y-4 mb-6">
                              <Input 
                                value={personaData.name} 
                                onChange={(e) => setPersonaData({...personaData, name: e.target.value})}
                                className={`text-2xl font-bold h-12 shadow-sm ${isDark ? 'bg-black/40 border-white/10 text-white rounded-none' : 'bg-white border-gray-200 text-black'}`}
                              />
                              <Input 
                                value={personaData.contact} 
                                onChange={(e) => setPersonaData({...personaData, contact: e.target.value})}
                                className={`text-sm font-mono h-10 shadow-sm ${isDark ? 'bg-black/40 border-white/10 text-white rounded-none' : 'bg-white border-gray-200 text-black'}`}
                              />
                            </div>
                          ) : (
                            <>
                              <h1 className={`text-3xl font-black mb-2 tracking-tight ${isDark ? 'text-white' : 'text-[#1A1A1A]'}`}>{personaData.name}</h1>
                              <div className={`text-xs font-mono mb-6 flex items-center gap-2 px-3 py-1.5 w-fit
                                 ${isDark ? 'bg-white/10 text-gray-300 rounded-none' : 'bg-gray-100 text-gray-500 rounded-lg'}
                              `}>
                                <span className={`w-2 h-2 rounded-full inline-block animate-pulse shadow-[0_0_8px_rgba(0,0,0,0.2)] ${isDark ? 'bg-white/80' : 'bg-black/80'}`}></span>
                                {personaData.contact}
                              </div>
                            </>
                          )}
                        </div>

                        {/* Section: Intro */}
                        <div className="space-y-3">
                          <h3 className={`font-bold text-sm flex items-center gap-2 uppercase tracking-wider opacity-80 ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${isDark ? 'bg-white' : 'bg-black'}`}></span>
                            {t[language].intro}
                          </h3>
                          {isEditing ? (
                            <Textarea 
                              value={personaData.intro}
                              onChange={(e) => setPersonaData({...personaData, intro: e.target.value})}
                              className={`text-sm leading-relaxed min-h-[150px] shadow-sm ${isDark ? 'bg-black/40 border-white/10 text-gray-300 rounded-none' : 'bg-white border-gray-200'}`}
                            />
                          ) : (
                             <p className={`text-sm leading-relaxed p-4 border shadow-[2px_2px_10px_rgba(0,0,0,0.02)]
                                ${isDark ? 'text-gray-300 bg-white/5 border-white/10 rounded-none' : 'text-gray-600 bg-white border-gray-100 rounded-xl'}
                             `}>
                              {personaData.intro}
                            </p>
                          )}
                        </div>

                        {/* Section: Education */}
                        <div className="space-y-5">
                          <h3 className={`font-bold text-sm flex items-center gap-2 uppercase tracking-wider opacity-80 ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>
                             <span className={`w-1.5 h-1.5 rounded-full ${isDark ? 'bg-white' : 'bg-black'}`}></span>
                            {t[language].education}
                          </h3>
                          {personaData.education.map((edu, idx) => (
                            <div key={idx} className={`border-l-[3px] pl-5 py-1 relative ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
                               {isEditing ? (
                                 <div className={`space-y-3 mb-6 p-4 ${isDark ? 'bg-white/5 rounded-none' : 'bg-gray-50 rounded-lg'}`}>
                                    <Input 
                                      value={edu.school} 
                                      onChange={(e) => {
                                        const newEdu = [...personaData.education];
                                        newEdu[idx].school = e.target.value;
                                        setPersonaData({...personaData, education: newEdu});
                                      }}
                                      className={`font-bold text-sm h-9 ${isDark ? 'bg-black/40 border-white/10 text-white rounded-none' : 'bg-white'}`}
                                      placeholder="School"
                                    />
                                     <Input 
                                      value={edu.degree} 
                                      onChange={(e) => {
                                        const newEdu = [...personaData.education];
                                        newEdu[idx].degree = e.target.value;
                                        setPersonaData({...personaData, education: newEdu});
                                      }}
                                      className={`text-sm h-9 ${isDark ? 'bg-black/40 border-white/10 text-gray-300 rounded-none' : 'bg-white'}`}
                                      placeholder="Degree"
                                    />
                                     <Input 
                                      value={edu.period} 
                                      onChange={(e) => {
                                        const newEdu = [...personaData.education];
                                        newEdu[idx].period = e.target.value;
                                        setPersonaData({...personaData, education: newEdu});
                                      }}
                                      className={`text-xs h-8 ${isDark ? 'bg-black/40 border-white/10 text-gray-400 rounded-none' : 'bg-white'}`}
                                      placeholder="Period"
                                    />
                                 </div>
                               ) : (
                                 <>
                                  <div className={`font-bold text-base ${isDark ? 'text-gray-100' : 'text-gray-900'}`}>{edu.school}</div>
                                  <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider mt-1 mb-2">{edu.period}</div>
                                  <div className={`text-sm inline-block px-3 py-2 ${isDark ? 'text-gray-300 bg-white/10 rounded-none' : 'text-gray-700 bg-gray-50 rounded-lg'}`}>{edu.degree}</div>
                                 </>
                               )}
                            </div>
                          ))}
                        </div>

                        {/* Section: Experience */}
                        <div className="space-y-5">
                          <h3 className={`font-bold text-sm flex items-center gap-2 uppercase tracking-wider opacity-80 ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>
                             <span className={`w-1.5 h-1.5 rounded-full ${isDark ? 'bg-white' : 'bg-black'}`}></span>
                            {t[language].experience}
                          </h3>
                          {personaData.experience.map((exp, idx) => (
                             <div key={idx} className={`relative p-5 border shadow-[0_4px_20px_-10px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_25px_-10px_rgba(0,0,0,0.08)] transition-all
                                ${isDark ? 'bg-white/5 border-white/10 rounded-none' : 'bg-white border-gray-100 rounded-2xl'}
                             `}>
                              {isEditing ? (
                                <div className="space-y-3">
                                  <Input 
                                      value={exp.company} 
                                      onChange={(e) => {
                                        const newExp = [...personaData.experience];
                                        newExp[idx].company = e.target.value;
                                        setPersonaData({...personaData, experience: newExp});
                                      }}
                                      className={`font-bold text-sm h-9 ${isDark ? 'bg-black/40 border-white/10 text-white rounded-none' : 'bg-gray-50'}`}
                                      placeholder="Company"
                                  />
                                  <Input 
                                      value={exp.role} 
                                      onChange={(e) => {
                                        const newExp = [...personaData.experience];
                                        newExp[idx].role = e.target.value;
                                        setPersonaData({...personaData, experience: newExp});
                                      }}
                                      className={`text-sm font-medium h-9 ${isDark ? 'bg-black/40 border-white/10 text-gray-300 rounded-none' : 'bg-gray-50'}`}
                                      placeholder="Role"
                                  />
                                   <Input 
                                      value={exp.period} 
                                      onChange={(e) => {
                                        const newExp = [...personaData.experience];
                                        newExp[idx].period = e.target.value;
                                        setPersonaData({...personaData, experience: newExp});
                                      }}
                                      className={`text-xs text-gray-400 h-8 ${isDark ? 'bg-black/40 border-white/10 rounded-none' : 'bg-gray-50'}`}
                                      placeholder="Period"
                                  />
                                  <Textarea
                                     value={exp.details.join('\n')}
                                     onChange={(e) => {
                                        const newExp = [...personaData.experience];
                                        newExp[idx].details = e.target.value.split('\n');
                                        setPersonaData({...personaData, experience: newExp});
                                     }}
                                     className={`text-sm min-h-[100px] ${isDark ? 'bg-black/40 border-white/10 text-gray-400 rounded-none' : 'bg-gray-50 text-gray-600'}`}
                                     placeholder="Details (one per line)"
                                  />
                                </div>
                              ) : (
                                <>
                                  <div className="flex justify-between items-start mb-2">
                                    <div>
                                      <div className={`font-bold text-base ${isDark ? 'text-gray-100' : 'text-gray-900'}`}>{exp.company}</div>
                                      <div className={`text-sm font-semibold mt-0.5 ${isDark ? 'text-gray-400' : 'text-gray-700'}`}>{exp.role}</div>
                                    </div>
                                    <div className={`text-[10px] font-bold px-2 py-1 uppercase tracking-wider ${isDark ? 'text-gray-500 bg-white/10 rounded-none' : 'text-gray-400 bg-gray-50 rounded-md'}`}>{exp.period}</div>
                                  </div>
                                  
                                  <ul className={`list-disc list-inside text-sm space-y-2 ml-1 ${isDark ? 'text-gray-400 marker:text-gray-600' : 'text-gray-600 marker:text-gray-300'}`}>
                                    {exp.details.map((detail, dIdx) => (
                                      <li key={dIdx}>{detail}</li>
                                    ))}
                                  </ul>
                                </>
                              )}
                             </div>
                          ))}
                        </div>

                         {/* Action Area */}
                         <div className="pt-4 flex justify-end gap-3">
                            <Button 
                              variant="ghost" 
                              onClick={onBack}
                              className={isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-800'}
                            >
                               Cancel
                            </Button>
                            <Button 
                              onClick={onNext}
                              className={`bg-[#1A1A1A] text-white hover:bg-black px-8
                                 ${isDark ? 'bg-white text-black hover:bg-gray-200 rounded-none' : 'bg-[#1A1A1A] text-white hover:bg-black rounded-lg'}
                              `}
                            >
                               Confirm & Next <ArrowRight className="w-4 h-4 ml-2" />
                            </Button>
                         </div>
                      </div>
                    </ScrollArea>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </Card>
        </motion.div>

      </div>

    </div>
  );
}
