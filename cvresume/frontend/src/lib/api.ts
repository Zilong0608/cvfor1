import type { JobSearchParams, JobSearchResponse, ResumeData } from './types';

const API_BASE = ((import.meta as any).env?.VITE_API_BASE_URL || '/api').replace(/\/+$/, '');

function buildApiUrl(path: string): string {
  if (API_BASE.startsWith('http://') || API_BASE.startsWith('https://')) {
    return `${API_BASE}${path}`;
  }
  return `${window.location.origin}${API_BASE}${path}`;
}

// Start waking the backend as soon as the upload screen is opened.
export async function warmBackend(signal: AbortSignal): Promise<boolean> {
  try {
    const response = await fetch(buildApiUrl('/health'), { signal });
    return response.ok;
  } catch {
    return false;
  }
}

async function readJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!text) {
    return {} as T;
  }
  return JSON.parse(text) as T;
}

async function responseError(res: Response): Promise<Error> {
  const raw = await res.text();
  try {
    const payload = JSON.parse(raw);
    if (typeof payload.detail === 'string') return new Error(payload.detail);
  } catch { /* Gateway errors may not contain JSON. */ }
  return new Error(`Request failed (${res.status}). Please retry shortly.`);
}

export async function parseResume(input: { file?: File; text?: string }, signal?: AbortSignal): Promise<{ resume: ResumeData; warnings: string[] }> {
  const form = new FormData();
  if (input.file) {
    form.append('file', input.file);
  }
  if (input.text) {
    form.append('text', input.text);
  }
  const res = await fetch(buildApiUrl('/resume/parse'), {
    signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(120000)]) : AbortSignal.timeout(120000),
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    throw await responseError(res);
  }
  const data = await readJson<{ resume: ResumeData; warnings?: string[] }>(res);
  if (!data.resume) {
    throw new Error('Invalid response: missing resume data.');
  }
  return { resume: data.resume, warnings: data.warnings || [] };
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
  const controller = new AbortController();
  const abort = () => controller.abort();
  if (signal?.aborted) abort();
  signal?.addEventListener('abort', abort, { once: true });
  // Allow a free Render instance to wake up; reset on every received chunk.
  let timedOut = false;
  let timer: ReturnType<typeof setTimeout>;
  const resetTimer = () => {
    clearTimeout(timer);
    timer = setTimeout(() => { timedOut = true; controller.abort(); }, 120000);
  };
  resetTimer();
  let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
  let complete = false;
  const consume = async (line: string) => {
    if (!line.trim()) return;
    let payload: any;
    try { payload = JSON.parse(line); }
    catch { throw new Error('The server returned an invalid response. Please retry.'); }
    if (payload.type === 'error') throw new Error(payload.message || 'Request failed.');
    if (complete) return;
    if (payload.type === 'done') {
      complete = true;
      clearTimeout(timer);
    }
    // Completion handlers can download the ZIP; the stream idle timer must not
    // run during that separate request. Handler errors still reach the caller.
    await onMessage(payload);
  };
  try {
    const res = await fetch(buildApiUrl(path), {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body), signal: controller.signal,
    });
    if (!res.ok) throw await responseError(res);
    if (!res.body) throw new Error('Streaming is not supported in this browser.');
    reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (!complete) {
      const { value, done } = await reader.read();
      if (done) break;
      resetTimer();
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) await consume(line);
    }
    buffer += decoder.decode();
    if (!complete && buffer.trim()) await consume(buffer);
    if (!complete) throw new Error('Connection interrupted before completion. Results already shown are retained. Please retry.');
  } catch (err) {
    if (timedOut) throw new Error('The server took too long to respond. Please retry in a moment.');
    throw err;
  } finally {
    clearTimeout(timer!);
    signal?.removeEventListener('abort', abort);
    await reader?.cancel().catch(() => {});
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

export async function downloadZip(jobId: string, signal?: AbortSignal): Promise<Blob> {
  const timeout = AbortSignal.timeout(120000);
  const res = await fetch(buildApiUrl(`/resumes/zip/download/${encodeURIComponent(jobId)}`), {
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
  });
  if (!res.ok) {
    if (res.status === 404) throw new Error('This download has expired after a server restart. Please generate the batch again.');
    throw await responseError(res);
  }
  return res.blob();
}
