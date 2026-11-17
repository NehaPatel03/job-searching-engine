import React from 'react';
import { Sparkles, Search, FileText } from 'lucide-react';

interface NavbarProps {
  activeTab: 'search' | 'resume';
  onTabChange: (tab: 'search' | 'resume') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, onTabChange }) => {
  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* App Title & Logo */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-sm shadow-indigo-200">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900 tracking-tight leading-none">
              Semantic Job Matching Engine
            </h1>
            <p className="text-xs text-gray-500 font-medium mt-0.5">
              Powered by pgvector & Google Gemini
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1 sm:space-x-2">
          <button
            onClick={() => onTabChange('search')}
            className={`inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'search'
                ? 'bg-indigo-50 text-indigo-700'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <Search className="w-4 h-4" />
            <span>Semantic Search</span>
          </button>

          <button
            onClick={() => onTabChange('resume')}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-gray-600 hover:bg-gray-50 cursor-pointer"
            title="Available in Step 3"
          >
            <FileText className="w-4 h-4" />
            <span>Resume Match</span>
            <span className="text-[10px] font-semibold uppercase tracking-wider bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
              Step 3
            </span>
          </button>
        </nav>
      </div>
    </header>
  );
};
