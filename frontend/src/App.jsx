import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import MemoryMatch from './MemoryMatch';
import MatrixBackground from './MatrixBackground';

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const runAgent = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/run-agent', {
        method: 'POST',
      });
      const data = await response.json();
      
      if (!response.ok || data.status === 'error') {
        throw new Error(data.error || data.message || 'An error occurred');
      }
      
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <MatrixBackground />
      <div className="min-h-screen p-8 max-w-4xl mx-auto flex flex-col items-center justify-center relative z-10">
        
        {/* Title Header matching the reference image typography */}
        <header className="mb-12 text-center w-full">
          <h1 className="text-5xl md:text-7xl font-black text-white tracking-tighter uppercase drop-shadow-[0_4px_4px_rgba(0,0,0,0.5)] leading-tight">
            The Daily<br/>AI Brief
          </h1>
          <p className="text-white/70 tracking-widest uppercase mt-4 text-sm font-semibold">AI News Agent</p>
        </header>

        {/* Main Glass Panel */}
        <div className="glass-panel rounded-2xl w-full p-8 mb-8 flex flex-col items-center">
          {!loading && !result && (
            <div className="text-center w-full max-w-lg">
              <p className="text-white/90 mb-8 font-light text-lg leading-relaxed">
                Welcome to your daily tech digest. We automatically read hundreds of articles every morning to find the single most exciting story you need to know today. 
              </p>
              <button 
                onClick={runAgent}
                className="glass-button px-10 py-4 rounded font-bold uppercase tracking-widest text-sm hover:scale-105"
              >
                Get Today's Story
              </button>
            </div>
          )}

          {loading && (
            <div className="w-full flex flex-col items-center">
              <MemoryMatch />
            </div>
          )}
        </div>

        {error && (
          <div className="glass-card text-red-400 p-4 rounded-xl mb-8 w-full">
            <strong>System Error:</strong> {error}
          </div>
        )}

        {result && result.post && (
          <div className="space-y-8 w-full animate-fade-in-up">
            
            {/* Dev.to Article Mockup */}
            <div className="bg-slate-900 border border-slate-700/50 rounded-lg shadow-2xl overflow-hidden relative">
              <div className="h-12 bg-slate-800/80 flex items-center px-4 border-b border-slate-700/50 space-x-2">
                <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
                <span className="ml-4 text-xs font-mono text-slate-400">dev.to/preview</span>
              </div>
              <div className="p-8">
                <div className="flex items-center space-x-4 mb-6">
                  <div className="w-12 h-12 rounded-full bg-emerald-500/20 border border-emerald-500/50 flex items-center justify-center text-xl font-bold text-emerald-400">AI</div>
                  <div>
                    <h3 className="text-white font-bold text-lg">Tech Taco Bot</h3>
                    <p className="text-slate-400 text-sm">Posted on {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</p>
                  </div>
                </div>
                <div className="prose prose-invert prose-emerald max-w-none text-slate-300 prose-headings:text-white prose-a:text-emerald-400">
                  <ReactMarkdown>{result.post.body_markdown}</ReactMarkdown>
                </div>
              </div>
            </div>

            {/* Mastodon Post Mockup */}
            <div className="bg-[#1e2028] border border-slate-700/50 rounded-xl max-w-2xl mx-auto shadow-xl p-6">
              <div className="flex space-x-4">
                <div className="w-12 h-12 rounded-lg bg-indigo-500/20 border border-indigo-500/50 flex-shrink-0 flex items-center justify-center text-xl font-bold text-indigo-400">TT</div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-white font-bold hover:underline cursor-pointer">Tech Taco 🌮</span>
                    <span className="text-slate-400 text-sm">@techtaco@mastodon.social</span>
                    <span className="text-slate-500 text-sm">· 1m</span>
                  </div>
                  <p className="text-white/90 font-medium whitespace-pre-wrap mt-2 text-[15px] leading-relaxed">
                    {result.post.mastodon_post}
                  </p>
                  <div className="flex items-center space-x-12 mt-6 text-slate-500 text-sm">
                    <span className="flex items-center space-x-2 hover:text-indigo-400 cursor-pointer transition-colors"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" /></svg> <span>0</span></span>
                    <span className="flex items-center space-x-2 hover:text-green-400 cursor-pointer transition-colors"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg> <span>0</span></span>
                    <span className="flex items-center space-x-2 hover:text-yellow-400 cursor-pointer transition-colors"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg> <span>0</span></span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-6 mt-12 pt-8 border-t border-slate-800">
              <a href={result.post.source_article_url} target="_blank" rel="noreferrer" className="text-emerald-400 hover:text-emerald-300 font-bold uppercase tracking-widest text-xs flex items-center space-x-2">
                <span>View Original Source</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
              </a>
              <button 
                onClick={() => setResult(null)}
                className="glass-button px-8 py-3 rounded font-bold uppercase tracking-widest text-xs"
              >
                Run Again
              </button>
            </div>
          </div>
        )}
        
        {result && !result.post && (
          <div className="glass-card text-white/80 p-6 rounded-xl mb-8 text-center w-full">
            {result.message}
            <div className="mt-6">
              <button 
                onClick={() => setResult(null)}
                className="glass-button px-8 py-3 rounded font-bold uppercase tracking-widest text-xs"
              >
                Acknowledge
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export default App;
