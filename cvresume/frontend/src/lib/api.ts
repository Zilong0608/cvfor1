import type { JobSearchParams, JobSearchResponse, ResumeData } from './types';

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || '/api';

function buildApiUrl(path: string): string {
  if (API_BASE.startsWith('http://') || API_BASE.startsWith('https://')) {
    return `${API_BASE}${path}`;
  }
  return `${window.location.origin}${API_BASE}${path}`;
}

async function readJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!text) {
    return {} as T;
  }
  return JSON.parse(text) as T;
}

export async function parseResume(input: { file?: File; text?: string }): Promise<ResumeData> {
  const form = new FormData();
  if (input.file) {
    form.append('file', input.file);
  }
  if (input.text) {
    form.append('text', input.text);
  }
  const res = await fetch(buildApiUrl('/resume/parse'), {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Parse failed (${res.status})`);
  }
  const data = await readJson<{ resume: ResumeData }>(res);
  if (!data.resume) {
    throw new Error('Invalid response: missing resume data.');
  }
  return data.resume;
}

export async function searchJobs(params: JobSearchParams): Promise<JobSearchResponse> {
  const res = await fetch(buildApiUrl('/jobs/search'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Search failed (${res.status})`);
  }
  return readJson<JobSearchResponse>(res);
}

export async function generateZip(payload: {
  resume: ResumeData;
  jobs: JobSearchResponse['jobs'];
}): Promise<Blob> {
  const res = await fetch(buildApiUrl('/resumes/zip'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `ZIP generation failed (${res.status})`);
  }
  return res.blob();
}

type StreamHandler = (payload: any) => void | Promise<void>;

async function streamNdjson(
  path: string,
  body: unknown,
  onMessage: StreamHandler,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(buildApiUrl(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Stream failed (${res.status})`);
  }
  if (!res.body) {
    throw new Error('Streaming not supported in this browser.');
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        const result = onMessage(JSON.parse(trimmed));
        if (result instanceof Promise) {
          await result;
        }
      } catch {
        // Ignore malformed lines.
      }
    }
  }
  if (buffer.trim()) {
    try {
      const result = onMessage(JSON.parse(buffer));
      if (result instanceof Promise) {
        await result;
      }
    } catch {
      // Ignore trailing malformed chunk.
    }
  }
}

export function streamJobSearch(
  params: JobSearchParams,
  onMessage: StreamHandler,
  signal?: AbortSignal
): Promise<void> {
  return streamNdjson('/jobs/search/stream', params, onMessage, signal);
}

export function streamZipGeneration(
  payload: {
    resume: ResumeData;
    jobs: JobSearchResponse['jobs'];
    start?: number;
    limit?: number;
  },
  onMessage: StreamHandler,
  signal?: AbortSignal
): Promise<void> {
  return streamNdjson('/resumes/zip/stream', payload, onMessage, signal);
}

export async function downloadZip(jobId: string): Promise<Blob> {
  const res = await fetch(buildApiUrl(`/resumes/zip/download/${jobId}`));
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Download failed (${res.status})`);
  }
  return res.blob();
}
