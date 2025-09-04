// WordInput component - Handles word input and validation
import React, { useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

interface WordInputProps {
  currentWord: string;
  onWordChange: (word: string) => void;
  onSubmit: () => void;
  onNewGame: () => void;
  onTriggerPlatePress?: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export const WordInput: React.FC<WordInputProps> = ({
  currentWord,
  onWordChange,
  onSubmit,
  onNewGame,
  onTriggerPlatePress,
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
    } else if (e.key === ' ') {
      e.preventDefault(); // Prevent space from being added to input
      onTriggerPlatePress?.(); // Trigger visual press effect
      onNewGame();
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
      <div className="input-field-with-icon">
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
        <button
          onClick={onSubmit}
          disabled={!canSubmit}
          className={`input-submit-icon ${!canSubmit ? 'disabled' : ''}`}
          title="Submit Word (Enter)"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
};

export default WordInput;
