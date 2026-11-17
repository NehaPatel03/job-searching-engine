import { JobResult } from './types';

// Connect to FastAPI backend URL (default to localhost:8001 to avoid conflicting with other running projects)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';

/**
 * Executes semantic vector search against the FastAPI /search endpoint.
 */
export async function searchJobs(query: string, k: number = 10): Promise<JobResult[]> {
  const url = new URL(`${API_BASE_URL}/search`);
  url.searchParams.append('q', query);
  url.searchParams.append('k', k.toString());

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    let errorDetail = 'Failed to fetch search results.';
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = errorJson.detail;
      }
    } catch {
      errorDetail = response.statusText || errorDetail;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}
