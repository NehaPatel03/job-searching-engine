import React from 'react';
import { Building2, MapPin, Sparkles } from 'lucide-react';
import { JobResult } from '../types';

interface JobCardProps {
  job: JobResult;
  rank: number;
}

export const JobCard: React.FC<JobCardProps> = ({ job, rank }) => {
  // Compute percentage score for human readability (e.g. 0.724 -> 72.4%)
  const matchPercentage = Math.round(job.score * 100);

  return (
    <article className="bg-white rounded-2xl border border-gray-200/90 p-5 sm:p-6 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all duration-200">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        {/* Left: Title, Company, Location */}
        <div className="space-y-1.5 flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-gray-400 bg-gray-100 px-2 py-0.5 rounded-md">
              #{rank}
            </span>
            <h3 className="text-lg font-bold text-gray-900 truncate tracking-tight">
              {job.title}
            </h3>
          </div>

          <div className="flex items-center flex-wrap gap-y-1 gap-x-4 text-xs sm:text-sm text-gray-600">
            {job.company && (
              <div className="flex items-center space-x-1.5">
                <Building2 className="w-4 h-4 text-gray-400 shrink-0" />
                <span className="font-medium text-gray-700">{job.company}</span>
              </div>
            )}

            {job.location && (
              <div className="flex items-center space-x-1.5">
                <MapPin className="w-4 h-4 text-gray-400 shrink-0" />
                <span>{job.location}</span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Similarity Score Badge */}
        <div className="flex items-center sm:flex-col sm:items-end justify-between shrink-0">
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-100">
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
            <span>{matchPercentage}% Match</span>
          </div>
          <span className="text-[11px] text-gray-400 mt-1 hidden sm:block">
            Cosine sim: {job.score.toFixed(4)}
          </span>
        </div>
      </div>

      {/* Snippet */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <p className="text-sm text-gray-600 leading-relaxed line-clamp-3">
          {job.snippet}
        </p>
      </div>
    </article>
  );
};
