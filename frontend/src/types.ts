export interface JobResult {
  job_id: number;
  title: string;
  company: string | null;
  location: string | null;
  score: number;
  snippet: string;
}

export type SearchMode = 'vector' | 'keyword' | 'hybrid';
