import React from 'react';
import { AlertCircle, SearchX, Briefcase, RefreshCw } from 'lucide-react';
import { JobResult } from '../types';
import { JobCard } from './JobCard';

interface JobListProps {
  jobs: JobResult[];
  isLoading: boolean;
  error: string | null;
  hasSearched: boolean;
  onRetry?: () => void;
}

export const JobList: React.FC<JobListProps> = ({
  jobs,
  isLoading,
  error,
  hasSearched,
  onRetry,
}) => {
  // 1. Loading Skeleton State
  if (isLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-6 w-48 bg-gray-200 rounded-md mb-6" />
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
            <div className="flex justify-between items-start">
              <div className="space-y-2 w-2/3">
                <div className="h-5 bg-gray-200 rounded w-3/4" />
                <div className="h-4 bg-gray-100 rounded w-1/2" />
              </div>
              <div className="h-7 w-24 bg-gray-100 rounded-full" />
            </div>
            <div className="h-12 bg-gray-50 rounded-lg w-full" />
          </div>
        ))}
      </div>
    );
  }

  // 2. Error State
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center space-y-3">
        <div className="w-12 h-12 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h3 className="text-base font-semibold text-red-900">Search Request Failed</h3>
        <p className="text-sm text-red-700 max-w-md mx-auto">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center space-x-2 px-4 py-2 mt-2 bg-red-600 text-white text-sm font-medium rounded-xl hover:bg-red-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Try Again</span>
          </button>
        )}
      </div>
    );
  }

  // 3. Initial Empty State (Before searching)
  if (!hasSearched) {
    return (
      <div className="text-center py-16 px-4 bg-white border border-gray-200/80 rounded-2xl">
        <div className="w-14 h-14 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Briefcase className="w-7 h-7" />
        </div>
        <h3 className="text-lg font-bold text-gray-900 mb-1">
          Explore 500+ Indexed Tech Opportunities
        </h3>
        <p className="text-sm text-gray-500 max-w-md mx-auto">
          Type any role, technology stack, or natural language query above to retrieve semantically matched jobs powered by pgvector embeddings.
        </p>
      </div>
    );
  }

  // 4. Zero Results Found State
  if (jobs.length === 0) {
    return (
      <div className="text-center py-16 px-4 bg-white border border-gray-200/80 rounded-2xl">
        <div className="w-12 h-12 bg-gray-100 text-gray-400 rounded-2xl flex items-center justify-center mx-auto mb-3">
          <SearchX className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-gray-900 mb-1">No Matching Jobs Found</h3>
        <p className="text-sm text-gray-500 max-w-sm mx-auto">
          Try broadening your search query or trying a different keyword variation.
        </p>
      </div>
    );
  }

  // 5. Results List
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-gray-200/60">
        <p className="text-sm font-medium text-gray-600">
          Showing <span className="font-bold text-gray-900">{jobs.length}</span> nearest matches
        </p>
        <span className="text-xs text-gray-400">Ordered by Cosine Similarity</span>
      </div>

      <div className="space-y-4">
        {jobs.map((job, index) => (
          <JobCard key={job.job_id} job={job} rank={index + 1} />
        ))}
      </div>
    </div>
  );
};
