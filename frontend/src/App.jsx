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
          <div className="space-y-6 w-full animate-fade-in-up">
            <div className="glass-card rounded-2xl p-6">
              <h2 className="text-xs font-bold uppercase tracking-wider text-primary-300 mb-2">Curator Reasoning</h2>
              <p className="text-white/80 italic border-l-2 border-primary-500 pl-4 text-sm">{result.reason}</p>
            </div>
            
            <div className="glass-card rounded-2xl overflow-hidden">
              <div className="bg-white/5 border-b border-white/10 p-4 flex items-center justify-between">
                <h2 className="font-semibold tracking-wider uppercase text-sm text-white/90">Generated Output</h2>
                <a href={result.post.source_article_url} target="_blank" rel="noreferrer" className="text-xs text-primary-300 hover:text-white uppercase tracking-wider transition-colors">View Source</a>
              </div>
              <div className="p-6 prose prose-invert max-w-none text-white/90 prose-h1:text-white prose-a:text-primary-400">
                <ReactMarkdown>{result.post.body_markdown}</ReactMarkdown>
              </div>
            </div>

            <div className="bg-black/60 backdrop-blur-md rounded-2xl border border-accent-600/30 p-6">
              <h2 className="text-xs font-bold uppercase tracking-wider text-accent-500 mb-2">Mastodon Broadcast</h2>
              <p className="text-white/90 font-medium whitespace-pre-wrap">{result.post.mastodon_post}</p>
            </div>
            
            <div className="text-center mt-8">
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
