import React, { useState } from 'react';
import { Search, Loader2, X } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
  initialQuery?: string;
}

const SAMPLE_QUERIES = [
  "Python backend developer",
  "React TypeScript web engineer",
  "Machine Learning with PyTorch",
  "FastAPI and Docker microservices",
  "Kubernetes DevOps engineer",
];

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  isLoading,
  initialQuery = "",
}) => {
  const [query, setQuery] = useState(initialQuery);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  };

  const handlePresetClick = (sample: string) => {
    setQuery(sample);
    onSearch(sample);
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center shadow-sm rounded-2xl bg-white border border-gray-200 focus-within:border-indigo-500 focus-within:ring-4 focus-within:ring-indigo-100 transition-all">
          <div className="pl-5 text-gray-400">
            <Search className="w-5 h-5" />
          </div>

          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by role, skills, or natural language (e.g., 'building scalable Python APIs with PostgreSQL')..."
            className="w-full py-4 pl-3.5 pr-28 text-gray-900 placeholder-gray-400 bg-transparent text-sm sm:text-base focus:outline-none"
            disabled={isLoading}
          />

          {query && !isLoading && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="p-1.5 mr-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
              title="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <div className="pr-3">
            <button
              type="submit"
              disabled={!query.trim() || isLoading}
              className="inline-flex items-center justify-center px-5 py-2.5 rounded-xl font-medium text-sm text-white bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm shadow-indigo-200"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  <span>Searching...</span>
                </>
              ) : (
                <span>Search</span>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Suggested Search Query Pills */}
      <div className="mt-3 flex items-center flex-wrap gap-2 text-xs text-gray-500">
        <span className="font-medium text-gray-400">Try searching:</span>
        {SAMPLE_QUERIES.map((sample) => (
          <button
            key={sample}
            type="button"
            onClick={() => handlePresetClick(sample)}
            disabled={isLoading}
            className="px-2.5 py-1 rounded-lg bg-gray-100 hover:bg-indigo-50 hover:text-indigo-700 text-gray-600 transition-colors border border-transparent hover:border-indigo-200"
          >
            {sample}
          </button>
        ))}
      </div>
    </div>
  );
};
