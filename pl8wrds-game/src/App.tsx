// Main App component for PL8WRDS game
import React, { useEffect, useState } from 'react';
import './styles/vintage.css';
import { ThemeProvider } from './theme';
import { useGame } from './hooks/useGame';
import PlateDisplay from './components/PlateDisplay';
import WordInput from './components/WordInput';
import LoadingScreen from './components/LoadingScreen';
import ErrorMessage from './components/ErrorMessage';
import InfoModal from './components/InfoModal';
import CollectionModal from './components/CollectionModal';
import { MapPin, Info, BookOpen } from 'lucide-react';

function App() {
  const { gameState, isLoading, error, actions } = useGame();
  const [showInfoModal, setShowInfoModal] = useState(false);
  const [showCollectionModal, setShowCollectionModal] = useState(false);

  // Auto-start first game when data is loaded
  useEffect(() => {
    if (!isLoading && !error && gameState.gameStatus === 'idle' && !gameState.currentPlate) {
      actions.startNewGame();
    }
  }, [isLoading, error, gameState.gameStatus, gameState.currentPlate, actions]);

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in input fields or when modals are open
      const activeElement = document.activeElement;
      const isTypingInInput = activeElement?.tagName === 'INPUT' || activeElement?.tagName === 'TEXTAREA';
      const isModalOpen = document.querySelector('.registration-overlay, .score-breakdown-overlay');
      
      if (isTypingInInput || isModalOpen) {
        return;
      }

      switch (event.code) {
        case 'Space':
          event.preventDefault(); // Prevent page scroll
          actions.startNewGame();
          break;
        case 'Enter':
          if (gameState.currentWord.trim() && gameState.gameStatus === 'playing') {
            actions.submitWord();
          }
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [actions, gameState.currentWord, gameState.gameStatus]);



  if (isLoading) {
    return <LoadingScreen />;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={() => window.location.reload()} />;
  }

  const foundWordsCount = gameState.foundWords.length;
  const totalSolutions = gameState.solutions.length;

  return (
    <ThemeProvider>
      <div className="App">
      <header className="App-header">
        <h1><MapPin className="inline-icon" size={32} />PL8WRDS</h1>
        <div className="header-actions">
          <button 
            className="info-button"
            onClick={() => setShowCollectionModal(true)}
            title="View Collection"
          >
            <BookOpen size={20} />
          </button>
          <button 
            className="info-button"
            onClick={() => setShowInfoModal(true)}
            title="How to Play"
          >
            <Info size={20} />
          </button>
        </div>
      </header>

      <main className="game-container">
        <PlateDisplay 
          plate={gameState.currentPlate}
          foundWordsCount={foundWordsCount}
          totalSolutions={totalSolutions}
          foundWords={gameState.foundWords}
          currentScore={gameState.score}
          gameData={gameState.gameData}
        />
        
        <WordInput
          currentWord={gameState.currentWord}
          onWordChange={actions.updateCurrentWord}
          onSubmit={actions.submitWord}
          onNewGame={actions.startNewGame}
          disabled={gameState.gameStatus !== 'playing'}
          placeholder="Enter a word..."
        />

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
      </main>

      {/* Info Modal */}
      <InfoModal 
        isOpen={showInfoModal}
        onClose={() => setShowInfoModal(false)}
        gameData={gameState.gameData}
      />

      {/* Collection Modal */}
      <CollectionModal 
        isOpen={showCollectionModal}
        onClose={() => setShowCollectionModal(false)}
        onSelectPlate={(plateId) => actions.loadCollectedPlate(plateId)}
      />

      </div>
    </ThemeProvider>
  );
}

export default App;
