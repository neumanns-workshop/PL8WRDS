// Theme Provider for PL8WRDS
// Clean theme context like Synapse but for vintage highway aesthetic

import React, { createContext, useContext } from 'react';
import { vintageTheme, VintageTheme } from './VintageTheme';

interface ThemeContextValue {
  theme: VintageTheme;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  return (
    <ThemeContext.Provider value={{ theme: vintageTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextValue => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
