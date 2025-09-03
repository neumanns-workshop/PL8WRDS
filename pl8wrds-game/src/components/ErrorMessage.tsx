// Error message component
import React from 'react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onRetry }) => {
  return (
    <div className="error-screen">
      <div className="error-content">
        <h1>PL8WRDS</h1>
        <div className="error-icon">⚠</div>
        <h2>Oops! Something went wrong</h2>
        <p className="error-message">{message}</p>
        {onRetry && (
          <button onClick={onRetry} className="retry-button">
            Try Again
          </button>
        )}
        <div className="error-help">
          <small>
            Make sure the game data file is available and your browser supports modern JavaScript features.
          </small>
        </div>
      </div>
    </div>
  );
};

export default ErrorMessage;
