import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// Type assertion for the root element - we know it exists in public/index.html
const rootElement = document.getElementById('root') as HTMLElement;
const root = ReactDOM.createRoot(rootElement);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Performance monitoring
// Pass console.log to see metrics in development, or send to analytics in production
reportWebVitals(process.env['NODE_ENV'] === 'development' ? console.log : undefined);
