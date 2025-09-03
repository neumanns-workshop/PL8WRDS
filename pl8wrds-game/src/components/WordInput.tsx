// WordInput component - Handles word input and validation
import React, { useRef, useEffect } from 'react';
import { Send, RotateCcw } from 'lucide-react';

interface WordInputProps {
  currentWord: string;
  onWordChange: (word: string) => void;
  onSubmit: () => void;
  onNewGame: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export const WordInput: React.FC<WordInputProps> = ({
  currentWord,
  onWordChange,
  onSubmit,
  onNewGame,
  disabled = false,
  placeholder = "Enter a word...",
}) => {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Focus the input when component mounts
    if (inputRef.current && !disabled) {
      inputRef.current.focus();
    }
  }, [disabled]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && currentWord.trim()) {
      onSubmit();
    }
  };



  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toLowerCase();
    // Only allow letters and remove any non-alphabetic characters
    const cleanValue = value.replace(/[^a-z]/g, '');
    onWordChange(cleanValue);
  };

  const canSubmit = currentWord.trim() && !disabled;

  return (
    <div className="word-input-container">
      <div className="input-field">
        <input
          ref={inputRef}
          type="text"
          value={currentWord}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          disabled={disabled}
          className={`word-input ${disabled ? 'disabled' : ''}`}
          maxLength={20} // Reasonable max length for words
        />
      </div>
      <div className="button-group">
        <button
          onClick={onNewGame}
          className="input-submit-button new-game-button"
          title="New Game (Spacebar)"
        >
          <RotateCcw size={16} />
        </button>
        <button
          onClick={onSubmit}
          disabled={!canSubmit}
          className={`input-submit-button ${!canSubmit ? 'disabled' : ''}`}
          title="Submit Word (Enter)"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
};

export default WordInput;
