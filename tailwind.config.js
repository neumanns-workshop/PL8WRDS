/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      // Mobile-first responsive breakpoints
      screens: {
        'xs': '475px',
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
      },
      
      // Game-specific color palette
      colors: {
        // License plate colors
        'plate': {
          'background': '#f8f9fa',
          'border': '#343a40',
          'text': '#212529',
          'shadow': '#6c757d'
        },
        
        // Game state colors
        'game': {
          'correct': '#10b981',
          'incorrect': '#ef4444',
          'hint': '#f59e0b',
          'rare': '#8b5cf6',
          'common': '#6b7280'
        },
        
        // Dark theme
        'dark': {
          'bg': '#0f172a',
          'surface': '#1e293b',
          'border': '#334155',
          'text': '#f1f5f9'
        }
      },
      
      // Typography optimized for mobile reading
      fontFamily: {
        'game': ['Inter', 'system-ui', 'sans-serif'],
        'plate': ['JetBrains Mono', 'Monaco', 'monospace'],
        'display': ['Poppins', 'system-ui', 'sans-serif']
      },
      
      // Spacing for touch targets (44px minimum)
      spacing: {
        'touch': '2.75rem', // 44px
        'safe': 'env(safe-area-inset-bottom)'
      },
      
      // Animation curves for mobile
      animation: {
        'bounce-in': 'bounceIn 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'shake': 'shake 0.5s ease-in-out'
      },
      
      keyframes: {
        bounceIn: {
          '0%': { 
            transform: 'scale(0.3)', 
            opacity: '0' 
          },
          '50%': { 
            transform: 'scale(1.05)' 
          },
          '70%': { 
            transform: 'scale(0.9)' 
          },
          '100%': { 
            transform: 'scale(1)', 
            opacity: '1' 
          }
        },
        slideUp: {
          '0%': { 
            transform: 'translateY(100%)', 
            opacity: '0' 
          },
          '100%': { 
            transform: 'translateY(0)', 
            opacity: '1' 
          }
        },
        pulseGlow: {
          '0%, 100%': { 
            boxShadow: '0 0 20px rgba(59, 130, 246, 0.5)' 
          },
          '50%': { 
            boxShadow: '0 0 40px rgba(59, 130, 246, 0.8)' 
          }
        },
        shake: {
          '0%, 100%': { transform: 'translateX(0)' },
          '10%, 30%, 50%, 70%, 90%': { transform: 'translateX(-2px)' },
          '20%, 40%, 60%, 80%': { transform: 'translateX(2px)' }
        }
      },
      
      // Mobile-optimized shadows
      boxShadow: {
        'mobile': '0 2px 8px rgba(0, 0, 0, 0.1)',
        'mobile-lg': '0 4px 16px rgba(0, 0, 0, 0.15)',
        'mobile-pressed': 'inset 0 2px 4px rgba(0, 0, 0, 0.1)'
      }
    },
  },
  plugins: [
    // Add custom utilities for mobile gaming
    function({ addUtilities }) {
      addUtilities({
        '.touch-manipulation': {
          'touch-action': 'manipulation',
        },
        '.tap-highlight-none': {
          '-webkit-tap-highlight-color': 'transparent',
        },
        '.safe-area-inset': {
          'padding-bottom': 'env(safe-area-inset-bottom)',
          'padding-left': 'env(safe-area-inset-left)',
          'padding-right': 'env(safe-area-inset-right)',
        }
      })
    }
  ],
} 