export interface EducationItem {
  school: string;
  period: string;
  degree: string;
}

export interface ExperienceItem {
  company: string;
  period: string;
  role: string;
  details: string[];
}

export interface ResumeData {
  name: string;
  contact: string;
  intro: string;
  education: EducationItem[];
  experience: ExperienceItem[];
  skills: string[];
  phone?: string;
  email?: string;
  summary?: string;
  certifications?: string[];
  community?: string[];
  additional?: string[];
  languages?: string[];
}

export interface JobSearchParams {
  title: string;
  region?: string;
  country?: string;
}

export interface JobResult {
  title?: string;
  company?: string;
  location?: string;
  site?: string;
  description?: string;
  job_url?: string;
  job_url_direct?: string;
}

export interface JobSearchResponse {
  jobs: JobResult[];
  analysis?: string;
  total?: number;
}

export interface GenerationBatch {
  jobId: string;
  zipName: string;
  start: number;
  end: number;
  total: number;
  createdAt: string;
}
