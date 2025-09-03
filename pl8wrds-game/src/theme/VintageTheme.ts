// Vintage Rand McNally Theme System
// Inspired by classic highway atlases and clean design principles

export interface VintageColors {
  // Base colors - like old paper maps
  background: string;
  surface: string;
  surfaceVariant: string;
  
  // Highway system colors - classic US routes
  primary: string;      // Interstate blue
  secondary: string;    // US Route red  
  accent: string;       // State route green
  
  // Text & content
  onBackground: string;
  onSurface: string;
  onPrimary: string;
  muted: string;
  
  // Interactive states
  success: string;      // Found words
  warning: string;      // Invalid words
  border: string;
  shadow: string;
  
  // License plate specific
  plateFrame: string;
  plateLetters: string;
  plateBorder: string;
}

export interface VintageTheme {
  colors: VintageColors;
  typography: {
    fonts: {
      heading: string;
      body: string;
      mono: string;
      plate: string;
    };
    sizes: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      '2xl': string;
      '3xl': string;
      '4xl': string;
    };
    weights: {
      normal: number;
      medium: number;
      semibold: number;
      bold: number;
    };
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    '2xl': string;
    '3xl': string;
  };
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}

// Vintage Highway Map Color Palette
export const vintageTheme: VintageTheme = {
  colors: {
    // Base - vintage paper and clean surfaces
    background: '#F5F1E8',     // Aged paper cream
    surface: '#FFFFFF',         // Clean white
    surfaceVariant: '#FAFAF9',  // Off-white
    
    // Highway system inspired
    primary: '#1B4F72',        // Interstate blue
    secondary: '#C0392B',       // US Route red
    accent: '#27AE60',          // State route green
    
    // Typography
    onBackground: '#2C3E50',    // Charcoal - easy to read
    onSurface: '#2C3E50',       
    onPrimary: '#FFFFFF',       
    muted: '#7F8C8D',           // Gray for secondary text
    
    // States
    success: '#F39C12',         // Gold for found words
    warning: '#E74C3C',         // Red for errors
    border: '#BDC3C7',          // Subtle borders
    shadow: 'rgba(44, 62, 80, 0.1)',
    
    // License plate styling
    plateFrame: '#FFFFFF',      // Classic white plate
    plateLetters: '#2C3E50',    // Dark letters
    plateBorder: '#BDC3C7',     // Metal border
  },
  
  typography: {
    fonts: {
      heading: '"Inter", system-ui, -apple-system, sans-serif',
      body: '"Inter", system-ui, -apple-system, sans-serif', 
      mono: '"Fira Code", "Monaco", "Consolas", monospace',
      plate: '"Arial Black", "Arial", sans-serif', // Bold for plates
    },
    sizes: {
      xs: '0.75rem',    // 12px
      sm: '0.875rem',   // 14px  
      base: '1rem',     // 16px
      lg: '1.125rem',   // 18px
      xl: '1.25rem',    // 20px
      '2xl': '1.5rem',  // 24px
      '3xl': '2rem',    // 32px
      '4xl': '3rem',    // 48px
    },
    weights: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },
  
  spacing: {
    xs: '0.25rem',   // 4px
    sm: '0.5rem',    // 8px
    md: '1rem',      // 16px
    lg: '1.5rem',    // 24px
    xl: '2rem',      // 32px
    '2xl': '3rem',   // 48px
    '3xl': '4rem',   // 64px
  },
  
  borderRadius: {
    sm: '0.25rem',   // 4px
    md: '0.5rem',    // 8px  
    lg: '0.75rem',   // 12px
    xl: '1rem',      // 16px
  },
  
  shadows: {
    sm: '0 1px 2px 0 rgba(44, 62, 80, 0.05)',
    md: '0 4px 6px -1px rgba(44, 62, 80, 0.1), 0 2px 4px -1px rgba(44, 62, 80, 0.06)',
    lg: '0 10px 15px -3px rgba(44, 62, 80, 0.1), 0 4px 6px -2px rgba(44, 62, 80, 0.05)',
  },
};

export default vintageTheme;
