import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { SearchBar } from './components/SearchBar';
import { JobList } from './components/JobList';
import { searchJobs } from './api';
import { JobResult } from './types';
import { Sparkles } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'search' | 'resume'>('search');
  const [query, setQuery] = useState<string>('Python backend developer');
  const [jobs, setJobs] = useState<JobResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState<boolean>(false);

  const handleSearch = async (searchQuery: string) => {
    setQuery(searchQuery);
    setIsLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const results = await searchJobs(searchQuery, 10);
      setJobs(results);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'An unexpected error occurred during search.';
      setError(msg);
      setJobs([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Perform initial search on mount to immediately show rich results
  useEffect(() => {
    handleSearch('Python backend developer');
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col antialiased text-gray-900">
      <Navbar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {activeTab === 'search' ? (
          <div className="space-y-8">
            {/* Header Hero */}
            <div className="text-center max-w-2xl mx-auto space-y-3">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-xs font-semibold text-indigo-700">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Vector Semantic Search Active</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">
                Find Opportunities by Meaning, <br className="hidden sm:inline" />
                Not Just Keywords.
              </h2>
              <p className="text-sm sm:text-base text-gray-600">
                Type what you love to build or the technical challenges you solve. Our vector engine maps your query directly to matching role responsibilities.
              </p>
            </div>

            {/* Search Bar Input */}
            <div className="max-w-3xl mx-auto">
              <SearchBar
                onSearch={handleSearch}
                isLoading={isLoading}
                initialQuery={query}
              />
            </div>

            {/* Job Results List */}
            <div className="max-w-3xl mx-auto pt-4">
              <JobList
                jobs={jobs}
                isLoading={isLoading}
                error={error}
                hasSearched={hasSearched}
                onRetry={() => handleSearch(query)}
              />
            </div>
          </div>
        ) : (
          /* Resume Match Tab Placeholder (Step 3) */
          <div className="text-center py-20 px-4 max-w-lg mx-auto bg-white border border-gray-200 rounded-3xl shadow-sm">
            <div className="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">
              Resume Parsing & Matching
            </h3>
            <p className="text-sm text-gray-600 mb-6">
              Step 3 will enable uploading PDF/text resumes to extract structured candidate profiles using Gemini and match directly against all indexed jobs.
            </p>
            <button
              onClick={() => setActiveTab('search')}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-medium transition-colors shadow-sm shadow-indigo-200"
            >
              Back to Semantic Search
            </button>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200/80 bg-white py-6 mt-12">
        <div className="max-w-5xl mx-auto px-4 text-center text-xs text-gray-500">
          Semantic Job Matching Engine &bull; Built with FastAPI, PostgreSQL, pgvector, and Google Gemini
        </div>
      </footer>
    </div>
  );
};
