import React, { useState, useEffect } from 'react';

// Using Emojis to avoid npm dependencies and ENOSPC errors
const EMOJIS = ['🤖', '🧠', '🚀', '⭐', '⚡', '💻', '🛸', '✨'];

const generateCards = () => {
  const deck = [...EMOJIS, ...EMOJIS]
    .map((emoji, i) => ({ id: i, emoji, isFlipped: false, isMatched: false }))
    .sort(() => Math.random() - 0.5);
  return deck;
};

const MemoryMatch = () => {
  const [cards, setCards] = useState([]);
  const [flippedIndices, setFlippedIndices] = useState([]);
  const [matches, setMatches] = useState(0);
  const [moves, setMoves] = useState(0);

  useEffect(() => {
    setCards(generateCards());
  }, []);

  useEffect(() => {
    if (flippedIndices.length === 2) {
      const [idx1, idx2] = flippedIndices;
      if (cards[idx1].emoji === cards[idx2].emoji) {
        setCards(prev => prev.map((card, i) => 
          i === idx1 || i === idx2 ? { ...card, isMatched: true } : card
        ));
        setMatches(m => m + 1);
        setFlippedIndices([]);
      } else {
        const timer = setTimeout(() => {
          setCards(prev => prev.map((card, i) => 
            i === idx1 || i === idx2 ? { ...card, isFlipped: false } : card
          ));
          setFlippedIndices([]);
        }, 1000);
        return () => clearTimeout(timer);
      }
    }
  }, [flippedIndices, cards]);

  const handleCardClick = (idx) => {
    if (flippedIndices.length === 2 || cards[idx].isFlipped || cards[idx].isMatched) return;

    if (flippedIndices.length === 0) {
      setMoves(m => m + 1);
    }

    setCards(prev => prev.map((card, i) => 
      i === idx ? { ...card, isFlipped: true } : card
    ));
    setFlippedIndices(prev => [...prev, idx]);
  };

  if (cards.length === 0) return null;

  return (
    <div className="flex flex-col items-center justify-center p-6 w-full animate-fade-in-up">
      <div className="flex justify-between items-center w-full max-w-sm mb-6 px-4">
        <div className="text-white/80 font-mono text-sm tracking-wider uppercase drop-shadow-md">
          Moves: {moves}
        </div>
        <div className="text-white/80 font-mono text-sm tracking-wider uppercase drop-shadow-md">
          Pairs: {matches}/8
        </div>
      </div>
      
      <div className="grid grid-cols-4 gap-3 sm:gap-4 perspective-1000">
        {cards.map((card, idx) => (
          <div 
            key={card.id}
            onClick={() => handleCardClick(idx)}
            className="w-14 h-14 sm:w-16 sm:h-16 cursor-pointer relative transform-style-3d transition-transform duration-500"
            style={{ transform: card.isFlipped || card.isMatched ? 'rotateY(180deg)' : '' }}
          >
            {/* Front (Hidden state) - Deep dark glass panel */}
            <div className="absolute inset-0 backface-hidden bg-black/40 backdrop-blur-md border border-white/20 rounded-xl flex items-center justify-center shadow-lg hover:bg-black/20 hover:border-white/40 transition-colors">
              <span className="text-2xl opacity-50 text-white">?</span>
            </div>
            {/* Back (Revealed state) - Glowing glass panel */}
            <div className="absolute inset-0 backface-hidden rotate-y-180 bg-black/60 backdrop-blur-xl border border-white/50 rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(255,255,255,0.2)]">
              <span className="text-3xl filter drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]">{card.emoji}</span>
            </div>
          </div>
        ))}
      </div>
      
      {matches === 8 ? (
        <div className="mt-8 text-center animate-bounce">
          <p className="text-white font-bold text-lg drop-shadow-lg">You Won in {moves} moves!</p>
          <p className="text-white/70 text-sm mt-1">Waiting for AI to finish writing...</p>
        </div>
      ) : (
        <div className="mt-8 text-center">
          <p className="text-white/70 text-sm animate-pulse tracking-widest uppercase">AI is analyzing...</p>
        </div>
      )}
    </div>
  );
};

export default MemoryMatch;
