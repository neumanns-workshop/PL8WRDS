// Loading screen component
import React from 'react';

const LoadingScreen: React.FC = () => {
  return (
    <div className="loading-screen">
      <div className="loading-content">
        <h1>PL8WRDS</h1>
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
        <p>Loading game data...</p>
        <div className="loading-details">
          <small>Decompressing 15,715 plates with 7M+ solutions...</small>
        </div>
      </div>
    </div>
  );
};

export default LoadingScreen;
