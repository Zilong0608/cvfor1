const PREFIX = 'resume-app';

export const CACHE_KEYS = {
  resumeRawText: `${PREFIX}:resume:raw_text`,
  resumeData: `${PREFIX}:resume:data`,
  resumeFileName: `${PREFIX}:resume:file_name`,
  jobSearchParams: `${PREFIX}:jobs:search_params`,
  jobResults: `${PREFIX}:jobs:results`,
  jobAnalysis: `${PREFIX}:jobs:analysis`,
  jobSearchLogs: `${PREFIX}:jobs:search_logs`,
  generationLogs: `${PREFIX}:generation:logs`,
  generationNextIndex: `${PREFIX}:generation:next_index`,
  generationTotal: `${PREFIX}:generation:total`,
  generationBatchSize: `${PREFIX}:generation:batch_size`,
  generationBatches: `${PREFIX}:generation:batches`,
  generationHasFirstBatch: `${PREFIX}:generation:has_first_batch`,
  zipName: `${PREFIX}:output:zip_name`,
} as const;

export function readCache<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function writeCache<T>(key: string, value: T): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Ignore write errors (storage quota, etc.)
  }
}

export function clearCache(keys: string[]): void {
  if (typeof window === 'undefined') return;
  keys.forEach((key) => {
    try {
      window.localStorage.removeItem(key);
    } catch {
      // Ignore remove errors
    }
  });
}
