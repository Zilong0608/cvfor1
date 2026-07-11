import React from 'react';
import { ArrowLeft, ArrowRight, Edit2, ChevronUp } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';

interface PersonaDetailsProps {
  onBack: () => void;
  onNext: () => void;
  theme: 'light' | 'dark';
}

export function PersonaDetails({ onBack, onNext, theme }: PersonaDetailsProps) {
  const isDark = theme === 'dark';

  return (
    <div className={`flex items-center justify-center min-h-screen bg-transparent p-4 overflow-hidden relative ${isDark ? 'text-gray-100' : 'text-[#1A1A1A]'}`}>
      {/* Background Header */}
      <div className="absolute top-8 left-0 right-0 text-center">
        <h2 className={`text-2xl font-serif italic ${isDark ? 'text-white' : 'text-black'}`}>MirrorCareer</h2>
        <p className={`text-xs tracking-widest uppercase ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>CV for R1</p>
      </div>

      {/* Navigation - Left */}
      <div className="absolute left-4 md:left-12 z-30">
        <Button
          variant="outline"
          size="icon"
          className={`rounded-full w-12 h-12 border-0 shadow-sm ${isDark ? 'bg-white/10 text-white hover:bg-white/20' : 'bg-white hover:bg-gray-50 text-gray-700'}`}
          onClick={onBack}
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
      </div>

      {/* Main Content - Center Card */}
      <Card className={`w-full max-w-2xl h-[80vh] border-0 shadow-xl z-20 mx-4 flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500
          ${isDark ? 'bg-[#111] text-gray-200' : 'bg-white text-[#1A1A1A]'}
      `}>
        <CardHeader className={`flex flex-row items-center justify-between border-b py-4 shrink-0 ${isDark ? 'border-white/10' : 'border-gray-100'}`}>
          <CardTitle className="text-lg font-bold">个人画像详情</CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className={`text-xs rounded-full h-8 px-3 gap-1 ${isDark ? 'bg-white/5 border-white/10 hover:bg-white/10' : ''}`}>
              <Edit2 className="w-3 h-3" /> 编辑
            </Button>
            <Button variant="outline" size="sm" className={`text-xs rounded-full h-8 px-3 gap-1 ${isDark ? 'bg-white/5 border-white/10 hover:bg-white/10' : ''}`}>
              收起 <ChevronUp className="w-3 h-3" />
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="p-0 flex-1 overflow-hidden">
          <ScrollArea className="h-full p-6">
            <div className="space-y-6 max-w-xl mx-auto pb-10">
              
              {/* Header Info */}
              <div>
                <h1 className={`text-2xl font-bold mb-1 ${isDark ? 'text-white' : 'text-black'}`}>Zilong Guo</h1>
                <div className={`text-xs font-mono mb-4 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                  0423 570 272 | excalibur8680608@gmail.com | 8680608
                </div>
              </div>

              {/* Section: Intro */}
              <div className="space-y-2">
                <h3 className={`font-bold text-sm ${isDark ? 'text-gray-200' : 'text-black'}`}>个人简介</h3>
                <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  Motivated and detail-oriented technology professional with a strong foundation in computer science, data science, and artificial intelligence. Experienced in software development, data processing, and the design of efficient technical solutions across both backend and frontend contexts. Demonstrates strong analytical ability, adaptability, and the capacity to take ownership of complex tasks from planning to execution. Skilled in applying automation, systematic problem-solving, and modern development practices to deliver reliable and scalable outcomes.
                </p>
              </div>

              {/* Section: Education */}
              <div className="space-y-4">
                <h3 className={`font-bold text-sm ${isDark ? 'text-gray-200' : 'text-black'}`}>教育背景</h3>
                
                <div className={`border-l-2 pl-4 space-y-1 ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
                  <div className="font-semibold text-sm">University of New South Wales</div>
                  <div className="text-xs text-gray-400">2023 - Present</div>
                  <div className="text-sm">Master of Information Technology · Artificial Intelligence Specialisation</div>
                </div>

                <div className={`border-l-2 pl-4 space-y-1 ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
                  <div className="font-semibold text-sm">The University of Auckland</div>
                  <div className="text-xs text-gray-400">2021 - 2023</div>
                  <div className="text-sm">Bachelor of Science · Computer Science & Statistics</div>
                </div>

                <div className={`border-l-2 pl-4 space-y-1 ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
                  <div className="font-semibold text-sm">UP Education</div>
                  <div className="text-xs text-gray-400">2018 - 2019</div>
                  <div className="text-sm">Foundation Programme · Academic English, Mathematics, Physics, Calculus, Accounting</div>
                </div>
              </div>

              {/* Section: Experience */}
              <div className="space-y-4">
                <h3 className={`font-bold text-sm ${isDark ? 'text-gray-200' : 'text-black'}`}>工作经历</h3>
                
                <div className={`border-l-2 pl-4 space-y-2 ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
                  <div>
                    <div className="font-semibold text-sm">WhiteMirror</div>
                    <div className="text-xs text-gray-400">2021 - 2022</div>
                    <div className="text-sm font-medium">AI Intern (2025 Apr)</div>
                  </div>
                  <ul className={`list-disc list-inside text-sm space-y-1 ml-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    <li>Assisted in testing, evaluating, and refining AI and language model behaviours.</li>
                    <li>Conducted prompt analysis, experiment design, and documentation preparation.</li>
                    <li>Supported development of lightweight applications and prototypes.</li>
                  </ul>
                </div>
              </div>

              {/* Tags/Skills */}
              <div className="pt-4 flex flex-wrap gap-2">
                <Badge variant="secondary" className={`font-normal ${isDark ? 'bg-white/10 text-gray-300 hover:bg-white/20' : 'bg-gray-100 text-gray-600'}`}>React</Badge>
                <Badge variant="secondary" className={`font-normal ${isDark ? 'bg-white/10 text-gray-300 hover:bg-white/20' : 'bg-gray-100 text-gray-600'}`}>TypeScript</Badge>
                <Badge variant="secondary" className={`font-normal ${isDark ? 'bg-white/10 text-gray-300 hover:bg-white/20' : 'bg-gray-100 text-gray-600'}`}>Python</Badge>
                <Badge variant="secondary" className={`font-normal ${isDark ? 'bg-white/10 text-gray-300 hover:bg-white/20' : 'bg-gray-100 text-gray-600'}`}>Machine Learning</Badge>
              </div>

            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Navigation - Right */}
      <div className="absolute right-4 md:right-12 z-30">
         <Button
          variant="outline"
          size="icon"
          className={`rounded-full w-12 h-12 border-0 shadow-sm ${isDark ? 'bg-white/10 text-white hover:bg-white/20' : 'bg-white hover:bg-gray-50 text-gray-700'}`}
          onClick={onNext}
        >
          <ArrowRight className="w-5 h-5" />
        </Button>
      </div>
    </div>
  );
}
