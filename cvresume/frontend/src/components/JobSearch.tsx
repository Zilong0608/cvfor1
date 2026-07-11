import React, { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, ExternalLink, FileText, BarChart3, FileOutput, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { ScrollArea } from './ui/scroll-area';
import { motion } from 'motion/react';
import { downloadZip, streamJobSearch, streamZipGeneration } from '../lib/api';
import { CACHE_KEYS, readCache, writeCache } from '../lib/cache';
import type { GenerationBatch, JobResult, JobSearchParams, ResumeData } from '../lib/types';

interface JobSearchProps {
  onBack: () => void;
  onNext: () => void;
  initialSearchTerm?: string;
  language: 'zh' | 'en';
  theme: 'light' | 'dark';
}

export function JobSearch({ onBack, onNext, initialSearchTerm = '', language, theme }: JobSearchProps) {
  const t = {
    zh: {
      step2: "STEP 2",
      title: "精准职位检索",
      jobTitle: "职位标题",
      region: "地区",
      country: "国家",
      selectCountry: "选择国家",
      // linkedinCount: "LinkedIn 数量",
      // seekCount: "Seek 数量",
      searching: "搜索中...",
      startSearch: "开始搜索",
      // continueSearch: "继续搜索",
      stop: "停止",
      searchComplete: "搜索完成 ✓",
      // jobShown: "(已显示 2 个职位)",
      searchingPlatform: "正在各大平台检索职位...",
      searchLog: "\u641c\u7d22\u65e5\u5fd7",
      analysisReport: "市场分析报告",
      analysisContent: "根据您的搜索条件，我们在 LinkedIn 和 Seek 平台上分析了 150+ 个相关职位。 \n\n• 薪资范围：$120k - $160k (AUD)\n• 关键技能需求：React, TypeScript, Node.js, AWS\n• 热门地区：Sydney, Melbourne\n• 竞争程度：中等\n\n建议您针对 AWS 证书和 System Design 能力进行优化，以提高匹配度。",
      generationTitle: "\u7b80\u5386\u6279\u91cf\u751f\u6210",
      batchSize: "\u6bcf\u6279\u6570\u91cf",
      generateBatch: "\u5f00\u59cb\u751f\u6210",
      continueBatch: "\u7ee7\u7eed\u751f\u6210",
      generatingBatch: "\u751f\u6210\u4e2d...",
      batchReady: "\u672c\u6279\u5b8c\u6210\uff0c\u53ef\u4ee5\u7ee7\u7eed\u751f\u6210\u3002",
      generateFirstBatch: "\u5148\u751f\u6210\u4e00\u6279\u518d\u8fdb\u5165\u4e0b\u4e00\u6b65\u3002",
      noMoreJobs: "\u6ca1\u6709\u66f4\u591a\u804c\u4f4d\u4e86\u3002",
      openLink: "打开链接",
      analyzeJD: "分析 JD",
      matchScore: "匹配程度",
      generateResume: "生成简历"
    },
    en: {
      step2: "STEP 2",
      title: "Precision Job Search",
      jobTitle: "Job Title",
      region: "Region",
      country: "Country",
      selectCountry: "Select Country",
      // linkedinCount: "LinkedIn Count",
      // seekCount: "Seek Count",
      searching: "Searching...",
      startSearch: "Start Search",
      // continueSearch: "Continue Search",
      stop: "Stop",
      searchComplete: "Search Complete ✓",
      // jobShown: "(2 jobs shown)",
      searchingPlatform: "Searching jobs on major platforms...",
      searchLog: "Search Log",
      analysisReport: "Market Analysis Report",
      analysisContent: "Based on your search criteria, we analyzed 150+ relevant positions on LinkedIn and Seek. \n\n• Salary Range: $120k - $160k (AUD)\n• Key Skills: React, TypeScript, Node.js, AWS\n• Top Locations: Sydney, Melbourne\n• Competition: Moderate\n\nIt is recommended to optimize for AWS certifications and System Design skills to improve matching.",
      generationTitle: "Resume Batch Generation",
      batchSize: "Batch Size",
      generateBatch: "Generate Batch",
      continueBatch: "Continue Batch",
      generatingBatch: "Generating...",
      batchReady: "Batch ready. You can continue generating.",
      generateFirstBatch: "Generate the first batch before moving to Step 3.",
      noMoreJobs: "No more jobs to process.",
      openLink: "Open Link",
      analyzeJD: "Analyze JD",
      matchScore: "Match Score",
      generateResume: "Generate Resume"
    }
  };
  const [isSearching, setIsSearching] = useState(false);
  const [hasResults, setHasResults] = useState(false);
  const [jobTitle, setJobTitle] = useState(initialSearchTerm || '');
  const [region, setRegion] = useState('');
  const [country, setCountry] = useState('AU');
  const [jobs, setJobs] = useState<JobResult[]>([]);
  const [analysisText, setAnalysisText] = useState('');
  const [error, setError] = useState('');
  const [searchLogs, setSearchLogs] = useState<string[]>(
    readCache<string[]>(CACHE_KEYS.jobSearchLogs, [])
  );

  const [isGenerating, setIsGenerating] = useState(false);
  const [generationLogs, setGenerationLogs] = useState<string[]>(
    readCache<string[]>(CACHE_KEYS.generationLogs, [])
  );
  const [batchSize, setBatchSize] = useState<number>(
    readCache<number>(CACHE_KEYS.generationBatchSize, 100)
  );
  const [nextIndex, setNextIndex] = useState<number>(
    readCache<number>(CACHE_KEYS.generationNextIndex, 0)
  );
  const [totalJobs, setTotalJobs] = useState<number>(
    readCache<number>(CACHE_KEYS.generationTotal, 0)
  );
  const [hasGeneratedBatch, setHasGeneratedBatch] = useState<boolean>(
    readCache<boolean>(CACHE_KEYS.generationHasFirstBatch, false)
  );
  const [zipBatches, setZipBatches] = useState<GenerationBatch[]>(
    readCache<GenerationBatch[]>(CACHE_KEYS.generationBatches, [])
  );

  const searchAbortRef = useRef<AbortController | null>(null);
  const generateAbortRef = useRef<AbortController | null>(null);

  // Update local state if prop changes (e.g. if user goes back and re-selects)
  useEffect(() => {
    if (initialSearchTerm) {
      const englishPart = initialSearchTerm.replace(/[\u4e00-\u9fa5]/g, '').trim(); 
      setJobTitle(englishPart || initialSearchTerm);
    }
  }, [initialSearchTerm]);

  useEffect(() => {
    const cachedParams = readCache<JobSearchParams | null>(CACHE_KEYS.jobSearchParams, null);
    if (cachedParams) {
      setJobTitle(cachedParams.title || jobTitle);
      setRegion(cachedParams.region || '');
      setCountry(cachedParams.country || 'AU');
    }
    const cachedJobs = readCache<JobResult[]>(CACHE_KEYS.jobResults, []);
    if (cachedJobs.length) {
      setJobs(cachedJobs);
      setHasResults(true);
    }
    const cachedAnalysis = readCache<string>(CACHE_KEYS.jobAnalysis, '');
    if (cachedAnalysis) {
      setAnalysisText(cachedAnalysis);
    }
    const cachedTotal = readCache<number>(CACHE_KEYS.generationTotal, 0);
    if (cachedTotal) {
      setTotalJobs(cachedTotal);
    }
  }, []);

  useEffect(() => {
    if (jobs.length) {
      setTotalJobs(jobs.length);
      writeCache(CACHE_KEYS.generationTotal, jobs.length);
    }
  }, [jobs.length]);

  useEffect(() => {
    return () => {
      searchAbortRef.current?.abort();
      generateAbortRef.current?.abort();
    };
  }, []);

  const handleSearch = async () => {
    if (searchAbortRef.current) {
      searchAbortRef.current.abort();
    }
    const controller = new AbortController();
    searchAbortRef.current = controller;

    setIsSearching(true);
    setHasResults(false);
    setError('');
    setSearchLogs([]);
    writeCache(CACHE_KEYS.jobSearchLogs, []);
    setGenerationLogs([]);
    writeCache(CACHE_KEYS.generationLogs, []);
    setNextIndex(0);
    writeCache(CACHE_KEYS.generationNextIndex, 0);
    setHasGeneratedBatch(false);
    writeCache(CACHE_KEYS.generationHasFirstBatch, false);
    setZipBatches([]);
    writeCache(CACHE_KEYS.generationBatches, []);
    setTotalJobs(0);
    writeCache(CACHE_KEYS.generationTotal, 0);

    const params: JobSearchParams = {
      title: jobTitle,
      region,
      country,
    };
    writeCache(CACHE_KEYS.jobSearchParams, params);

    const appendLog = (message: string) => {
      setSearchLogs((prev) => {
        const next = [...prev, message];
        writeCache(CACHE_KEYS.jobSearchLogs, next);
        return next;
      });
    };

    try {
      await streamJobSearch(
        params,
        (payload) => {
          if (payload?.type === 'log' && payload.message) {
            appendLog(payload.message);
            return;
          }
          if (payload?.type === 'done') {
            const jobsResult = payload.jobs || [];
            setJobs(jobsResult);
            setAnalysisText(payload.analysis || '');
            setHasResults(true);
            writeCache(CACHE_KEYS.jobResults, jobsResult);
            writeCache(CACHE_KEYS.jobAnalysis, payload.analysis || '');
            if (typeof payload.total === 'number') {
              setTotalJobs(payload.total);
              writeCache(CACHE_KEYS.generationTotal, payload.total);
            }
            setIsSearching(false);
            return;
          }
          if (payload?.type === 'error') {
            setError(payload.message || 'Search failed.');
            setIsSearching(false);
          }
        },
        controller.signal
      );
    } catch (err: any) {
      if (err?.name !== 'AbortError') {
        setError(err?.message || 'Search failed.');
      }
    } finally {
      searchAbortRef.current = null;
      setIsSearching(false);
    }
  };

  const handleGenerateBatch = async () => {
    if (generateAbortRef.current) {
      generateAbortRef.current.abort();
    }
    const controller = new AbortController();
    generateAbortRef.current = controller;

    const resume = readCache<ResumeData | null>(CACHE_KEYS.resumeData, null);
    const cachedJobs = readCache<JobResult[]>(CACHE_KEYS.jobResults, []);
    if (!resume || cachedJobs.length === 0) {
      setError('Missing resume data or job results.');
      return;
    }
    if (nextIndex >= cachedJobs.length) {
      setGenerationLogs((prev) => {
        const next = [...prev, 'No more jobs to process.'];
        writeCache(CACHE_KEYS.generationLogs, next);
        return next;
      });
      return;
    }

    setError('');
    setIsGenerating(true);
    setGenerationLogs([]);
    writeCache(CACHE_KEYS.generationLogs, []);

    const appendGenLog = (message: string) => {
      setGenerationLogs((prev) => {
        const next = [...prev, message];
        writeCache(CACHE_KEYS.generationLogs, next);
        return next;
      });
    };

    try {
      await streamZipGeneration(
        {
          resume,
          jobs: cachedJobs,
          start: nextIndex,
          limit: batchSize,
        },
        async (payload) => {
          if (payload?.type === 'log' && payload.message) {
            appendGenLog(payload.message);
            return;
          }
          if (payload?.type === 'progress') {
            return;
          }
          if (payload?.type === 'done') {
            const start = typeof payload.start === 'number' ? payload.start : nextIndex;
            const end = typeof payload.end === 'number' ? payload.end : nextIndex;
            const total = typeof payload.total === 'number' ? payload.total : cachedJobs.length;
            const jobId = payload.job_id as string | undefined;
            const zipName = (payload.zip_name as string | undefined) || 'resumes.zip';

            if (typeof payload.end === 'number') {
              setNextIndex(payload.end);
              writeCache(CACHE_KEYS.generationNextIndex, payload.end);
            }
            setTotalJobs(total);
            writeCache(CACHE_KEYS.generationTotal, total);
            setHasGeneratedBatch(true);
            writeCache(CACHE_KEYS.generationHasFirstBatch, true);

            const createdAt = new Date().toISOString();
            if (jobId) {
              const batch: GenerationBatch = {
                jobId,
                zipName,
                start,
                end,
                total,
                createdAt,
              };
              setZipBatches((prev) => {
                const next = [...prev, batch];
                writeCache(CACHE_KEYS.generationBatches, next);
                return next;
              });
              try {
                const blob = await downloadZip(jobId);
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = zipName;
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(url);
              } catch (downloadErr: any) {
                setError(downloadErr?.message || 'Download failed.');
              }
            }
            setIsGenerating(false);
            return;
          }
          if (payload?.type === 'error') {
            setError(payload.message || 'Generation failed.');
            setIsGenerating(false);
          }
        },
        controller.signal
      );
    } catch (err: any) {
      if (err?.name !== 'AbortError') {
        setError(err?.message || 'Generation failed.');
      }
    } finally {
      generateAbortRef.current = null;
      setIsGenerating(false);
    }
  };

  const isDark = theme === 'dark';
  const hasMoreJobs = totalJobs > 0 && nextIndex < totalJobs;
  const nextBatchEnd = hasMoreJobs ? Math.min(nextIndex + Math.max(batchSize, 1), totalJobs) : 0;
  const nextRangeLabel = hasMoreJobs ? `${nextIndex + 1}-${nextBatchEnd}` : '';
  const batchActionLabel = hasGeneratedBatch ? t[language].continueBatch : t[language].generateBatch;
  const batchHint = !hasMoreJobs && totalJobs
    ? t[language].noMoreJobs
    : hasGeneratedBatch
    ? t[language].batchReady
    : t[language].generateFirstBatch;

  return (
    <div className={`flex flex-col items-center justify-center min-h-screen bg-transparent p-4 relative overflow-hidden font-sans perspective-1000 ${isDark ? 'text-gray-100' : 'text-[#1F1F1F]'}`}>
       
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
         {/* Ghost Card - Previous Step (Step 2) */}
         <div className={`absolute left-4 top-1/2 -translate-y-1/2 -translate-x-full w-full max-w-2xl h-[70vh] backdrop-blur-xl rounded-2xl shadow-xl border opacity-40 scale-90 hidden lg:block pointer-events-none -mr-32 transform -rotate-3 mix-blend-soft-light
             ${isDark ? 'bg-black/20 border-white/10' : 'bg-white/20 border-white/30'}
         `}>
           <div className="p-6 space-y-4 opacity-30">
             <div className="h-6 bg-gray-400/20 rounded w-1/3"></div>
             <div className="space-y-4">
               <div className="h-20 bg-gray-400/20 rounded w-full"></div>
               <div className="h-20 bg-gray-400/20 rounded w-full"></div>
             </div>
           </div>
        </div>
        
        {/* Ghost Card - Next Step (Step 4) */}
        <div className={`absolute right-4 top-1/2 -translate-y-1/2 translate-x-full w-full max-w-2xl h-[70vh] backdrop-blur-xl rounded-2xl shadow-xl border opacity-40 scale-90 hidden lg:block pointer-events-none -ml-32 transform rotate-3 mix-blend-soft-light
             ${isDark ? 'bg-black/20 border-white/10' : 'bg-white/20 border-white/30'}
        `}>
           <div className="p-6 space-y-4 opacity-30">
             <div className="h-6 bg-gray-400/20 rounded w-1/4"></div>
             <div className="space-y-2">
               <div className="h-full bg-gray-400/20 rounded w-full flex-1"></div>
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
            <span className={`text-xs font-bold tracking-wide uppercase drop-shadow-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{t[language].step2}</span>
            <CardTitle className={`text-lg font-bold drop-shadow-sm ${isDark ? 'text-white' : 'text-[#1F1F1F]'}`}>{t[language].title}</CardTitle>
          </div>
        </CardHeader>
        
        <CardContent className="p-5 md:p-8 pt-6 md:pt-8 flex-1 overflow-y-auto space-y-6 md:space-y-8 no-scrollbar z-10 relative">
          
          {/* Search Form */}
          <div className="space-y-6">
            <div className="space-y-4">
              {/* Job Title */}
              <div className="space-y-2">
                <label className={`text-xs font-semibold ml-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{t[language].jobTitle}</label>
                <div className="relative group/input">
                  <div className={`absolute -inset-0.5 rounded-lg blur opacity-30 group-hover/input:opacity-60 transition duration-500
                      ${isDark ? 'bg-white/20' : 'bg-gradient-to-r from-gray-200 to-gray-300'}
                  `}></div>
                  <Input 
                    value={jobTitle} 
                    onChange={(e) => setJobTitle(e.target.value)}
                    className={`relative border-0 focus:ring-0 shadow-[inset_2px_2px_4px_rgba(0,0,0,0.05)] h-10 transition-all
                        ${isDark 
                           ? 'bg-black/40 text-white placeholder:text-gray-500 focus:bg-black/60 rounded-none' 
                           : 'bg-white/80 focus:bg-white rounded-lg'
                        }
                    `} 
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Region */}
                <div className="space-y-2">
                  <label className={`text-xs font-semibold ml-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{t[language].region}</label>
                  <div className="relative group/input">
                    <div className={`absolute -inset-0.5 rounded-lg blur opacity-30 group-hover/input:opacity-60 transition duration-500
                        ${isDark ? 'bg-white/20' : 'bg-gradient-to-r from-gray-200 to-gray-300'}
                    `}></div>
                    <Input 
                      value={region} 
                      onChange={(e) => setRegion(e.target.value)}
                      placeholder={isDark ? "City or State..." : "City or State..."}
                      className={`relative border-0 focus:ring-0 shadow-[inset_2px_2px_4px_rgba(0,0,0,0.05)] h-10 transition-all
                          ${isDark 
                             ? 'bg-black/40 text-white placeholder:text-gray-500 focus:bg-black/60 rounded-none' 
                             : 'bg-white/80 focus:bg-white rounded-lg'
                          }
                      `} 
                    />
                  </div>
                </div>

                {/* Country */}
                <div className="space-y-2">
                  <label className={`text-xs font-semibold ml-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{t[language].country}</label>
                  <Select value={country} onValueChange={setCountry}>
                    <SelectTrigger className={`border-0 w-full focus:ring-0 shadow-[inset_2px_2px_4px_rgba(0,0,0,0.05)] h-10
                        ${isDark ? 'bg-black/40 text-white focus:bg-black/60 rounded-none' : 'bg-white/80 rounded-lg' }
                    `}>
                      <SelectValue placeholder={t[language].selectCountry} />
                    </SelectTrigger>
                    <SelectContent className={isDark ? 'bg-[#1A1A1A] border-white/10 text-white' : ''}>
                      <SelectItem value="AU">Australia</SelectItem>
                      <SelectItem value="US">United States</SelectItem>
                      <SelectItem value="UK">United Kingdom</SelectItem>
                      <SelectItem value="CA">Canada</SelectItem>
                      <SelectItem value="SG">Singapore</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-4">
              {/* MIRROR TECH HUD BUTTON */}
              <Button 
                onClick={handleSearch}
                className={`relative overflow-hidden text-white border px-8 h-11 text-sm font-medium transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0 group
                   ${isDark 
                      ? 'bg-white text-black border-white/20 hover:bg-gray-200 rounded-none' 
                      : 'bg-[#222224] border-white/10 rounded-lg'
                   }
                `}
                disabled={isSearching}
              >
                 {/* --- GEOMETRIC TECH OVERLAY --- */}
                      
                  {/* 1. Large Rotating Arc (Right side) */}
                  <div className={`absolute top-1/2 right-[-20%] w-[120%] h-[200%] -translate-y-1/2 rounded-full border border-dashed animate-[spin_10s_linear_infinite] pointer-events-none opacity-40
                      ${isDark ? 'border-black/20' : 'border-white/10'}
                  `}></div>
                  
                  {/* 2. Thin Crosshair Lines */}
                  <div className={`absolute top-0 bottom-0 left-6 w-[1px] pointer-events-none ${isDark ? 'bg-black/10' : 'bg-white/5'}`}></div>
                  <div className={`absolute left-0 right-0 top-1/2 h-[1px] pointer-events-none ${isDark ? 'bg-black/10' : 'bg-white/5'}`}></div>

                  {/* 3. Corner Markers */}
                  <div className={`absolute top-1 left-1 w-1.5 h-1.5 border-l border-t pointer-events-none ${isDark ? 'border-black/30' : 'border-white/30'}`}></div>
                  <div className={`absolute bottom-1 right-1 w-1.5 h-1.5 border-r border-b pointer-events-none ${isDark ? 'border-black/30' : 'border-white/30'}`}></div>

                  {/* 4. Scanning Line (Subtle) */}
                  <div className={`absolute top-0 bottom-0 left-0 w-[2px] blur-[1px] animate-[shimmer_3s_infinite] pointer-events-none ${isDark ? 'bg-black/20' : 'bg-white/20'}`}></div>

                {isSearching ? <Loader2 className={`w-4 h-4 animate-spin mr-2 relative z-10 ${isDark ? 'text-black' : 'text-white'}`} /> : null}
                <span className={`relative z-10 ${isDark ? 'text-black' : 'text-white'}`}>{isSearching ? t[language].searching : t[language].startSearch}</span>
              </Button>

              {/* Continue Search Button REMOVED as requested */}

              <Button
                variant="ghost"
                size="sm"
                className={`text-xs px-2 transition-colors ml-auto ${isDark ? 'text-gray-400 hover:text-red-400' : 'text-gray-400 hover:text-red-500'}`}
                onClick={() => {
                  if (isSearching) {
                    searchAbortRef.current?.abort();
                    setIsSearching(false);
                    setSearchLogs((prev) => {
                      const next = [...prev, 'Search stopped by user.'];
                      writeCache(CACHE_KEYS.jobSearchLogs, next);
                      return next;
                    });
                  }
                  if (isGenerating) {
                    generateAbortRef.current?.abort();
                    setIsGenerating(false);
                    setGenerationLogs((prev) => {
                      const next = [...prev, 'Generation stopped by user.'];
                      writeCache(CACHE_KEYS.generationLogs, next);
                      return next;
                    });
                  }
                }}
              >
                <span className={`text-[10px] px-3 py-1.5 border shadow-sm
                    ${isDark ? 'bg-white/5 border-white/10 text-gray-400 rounded-none' : 'bg-white/50 border-gray-200/50 rounded-full'}
                `}>{t[language].stop}</span>
              </Button>
            </div>
            
            {hasResults && (
               <div className={`text-xs mt-2 flex items-center gap-2 font-medium w-fit px-3 py-1 border 
                   ${isDark ? 'bg-white/5 border-white/10 text-gray-400 rounded-none' : 'bg-gray-100/50 border-gray-200/50 text-gray-500 rounded-full'}
               `}>
                 <span className={isDark ? 'text-gray-200' : 'text-gray-700'}>{t[language].searchComplete}</span>
               </div>
            )}
          </div>

          {/* Results Area */}
          <div className="min-h-[200px]">
            {error && (
              <div className={`text-xs font-medium mb-3 ${isDark ? 'text-red-300' : 'text-red-600'}`}>
                {error}
              </div>
            )}
            {isSearching && (
              <div className="flex flex-col items-center justify-center py-12 text-gray-400 space-y-3">
                <div className="relative">
                  <div className={`absolute inset-0 rounded-full blur animate-pulse ${isDark ? 'bg-white/20' : 'bg-gray-200'}`}></div>
                  <Loader2 className={`w-8 h-8 animate-spin relative z-10 ${isDark ? 'text-white' : 'text-gray-600'}`} />
                </div>
                <p className="text-xs font-medium tracking-wide">{t[language].searchingPlatform}</p>
              </div>
            )}

            {searchLogs.length > 0 && (
              <div
                className={`backdrop-blur-xl p-6 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.08)] border animate-in fade-in slide-in-from-bottom-4 duration-700 transition-all relative overflow-hidden mt-4
                   ${isDark ? 'bg-white/5 border-white/10 rounded-none' : 'bg-white/80 border-white/80 rounded-2xl'}
                `}
              >
                <h3
                  className={`text-sm font-bold uppercase tracking-widest mb-3 flex items-center gap-2
                      ${isDark ? 'text-gray-400' : 'text-gray-500'}
                  `}
                >
                  {t[language].searchLog}
                </h3>
                <ScrollArea className="h-40 pr-3">
                  <div className={`text-xs font-mono space-y-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                    {searchLogs.map((line, index) => (
                      <div key={`${line}-${index}`}>{line}</div>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            )}
            
            {hasResults && (
              <div className={`backdrop-blur-xl p-8 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.08)] border animate-in fade-in slide-in-from-bottom-4 duration-700 transition-all relative overflow-hidden
                   ${isDark 
                      ? 'bg-white/5 border-white/10 rounded-none' 
                      : 'bg-white/80 border-white/80 rounded-2xl'
                   }
              `}>
                  {/* Tech Decorations for Text Box */}
                  {isDark && (
                      <>
                          <div className="absolute top-0 left-0 w-4 h-4 border-l border-t border-white/30"></div>
                          <div className="absolute bottom-0 right-0 w-4 h-4 border-r border-b border-white/30"></div>
                      </>
                  )}

                  <h3 className={`text-sm font-bold uppercase tracking-widest mb-4 flex items-center gap-2
                      ${isDark ? 'text-gray-400' : 'text-gray-500'}
                  `}>
                      <BarChart3 className="w-4 h-4" />
                      {t[language].analysisReport}
                  </h3>

                  <div className={`whitespace-pre-wrap text-sm leading-relaxed font-mono
                      ${isDark ? 'text-gray-300' : 'text-gray-700'}
                  `}>
                      {analysisText || t[language].analysisContent}
                  </div>
              </div>
            )}
          </div>

          {/* Generation Area */}
          <div className="space-y-4">
            <div
              className={`backdrop-blur-xl p-6 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.08)] border transition-all relative overflow-hidden
                   ${isDark ? 'bg-white/5 border-white/10 rounded-none' : 'bg-white/80 border-white/80 rounded-2xl'}
              `}
            >
              <div className="flex items-center justify-between mb-4">
                <h3
                  className={`text-sm font-bold uppercase tracking-widest flex items-center gap-2
                      ${isDark ? 'text-gray-400' : 'text-gray-500'}
                  `}
                >
                  {t[language].generationTitle}
                </h3>
                <div className="flex items-center gap-2">
                  <div
                    className={`text-xs px-3 py-1 border
                        ${isDark ? 'bg-white/5 border-white/10 text-gray-400 rounded-none' : 'bg-gray-100/50 border-gray-200/50 text-gray-500 rounded-full'}
                    `}
                  >
                    {totalJobs ? `${nextIndex}/${totalJobs}` : '0/0'}
                  </div>
                  {zipBatches.length > 0 && (
                    <div
                      className={`text-xs px-3 py-1 border
                          ${isDark ? 'bg-white/5 border-white/10 text-gray-400 rounded-none' : 'bg-gray-100/50 border-gray-200/50 text-gray-500 rounded-full'}
                      `}
                    >
                      {zipBatches.length} batches
                    </div>
                  )}
                  {nextRangeLabel && (
                    <div
                      className={`text-xs px-3 py-1 border
                          ${isDark ? 'bg-white/5 border-white/10 text-gray-400 rounded-none' : 'bg-gray-100/50 border-gray-200/50 text-gray-500 rounded-full'}
                      `}
                    >
                      next {nextRangeLabel}
                    </div>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                <div className="space-y-2">
                  <label className={`text-xs font-semibold ml-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                    {t[language].batchSize}
                  </label>
                  <Input
                    value={batchSize}
                    onChange={(e) => {
                      const value = Number(e.target.value) || 0;
                      setBatchSize(value);
                      writeCache(CACHE_KEYS.generationBatchSize, value);
                    }}
                    className={`relative border-0 focus:ring-0 shadow-[inset_2px_2px_4px_rgba(0,0,0,0.05)] h-10 transition-all
                        ${isDark ? 'bg-black/40 text-white placeholder:text-gray-500 focus:bg-black/60 rounded-none' : 'bg-white/80 focus:bg-white rounded-lg'}
                    `}
                    type="number"
                    min={1}
                  />
                </div>

                <div className="md:col-span-2 flex items-center gap-3">
                  <Button
                    onClick={handleGenerateBatch}
                    disabled={isGenerating || isSearching || jobs.length === 0 || !hasMoreJobs}
                    className={`relative overflow-hidden text-white border px-6 h-10 text-xs font-medium transition-all shadow-lg hover:shadow-xl active:translate-y-0 group
                       ${isDark ? 'bg-white text-black border-white/20 hover:bg-gray-200 rounded-none' : 'bg-[#222224] border-white/10 rounded-lg'}
                    `}
                  >
                    {isGenerating ? <Loader2 className={`w-4 h-4 animate-spin mr-2 ${isDark ? 'text-black' : 'text-white'}`} /> : null}
                    <span className={`relative z-10 ${isDark ? 'text-black' : 'text-white'}`}>
                      {isGenerating ? t[language].generatingBatch : batchActionLabel}
                    </span>
                  </Button>

                  <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                    {batchHint}
                  </div>
                </div>
              </div>

              {generationLogs.length > 0 && (
                <div className="mt-4">
                  <ScrollArea className="h-40 pr-3">
                    <div className={`text-xs font-mono space-y-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      {generationLogs.map((line, index) => (
                        <div key={`${line}-${index}`}>{line}</div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}
            </div>
          </div>

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
          disabled={!hasGeneratedBatch || isGenerating || isSearching}
          title={
            !hasGeneratedBatch
              ? 'Generate at least one batch before moving on.'
              : isGenerating || isSearching
              ? 'Please wait for the current task to finish.'
              : undefined
          }
        >
          <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
        </Button>
      </div>
    </div>
  );
}
