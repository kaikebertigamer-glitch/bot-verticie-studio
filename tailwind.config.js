/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Space Grotesk', 'sans-serif'],
      },
      colors: {
        navy: {
          950: '#060a14',
          900: '#0a0f1e',
          800: '#0e1428',
          700: '#141c35',
          600: '#1a2444',
        },
        silver: {
          100: '#f0f4f8',
          200: '#dce5ed',
          300: '#c4d0db',
          400: '#a8b8c8',
          500: '#8a9bb0',
        },
        gold: {
          300: '#e8c97a',
          400: '#d4a853',
          500: '#c09642',
          600: '#a07830',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-glow': 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(180,160,100,0.12), transparent)',
        'card-glow': 'linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-gold': 'pulseGold 2s ease-in-out infinite',
        'shimmer': 'shimmer 2.5s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        pulseGold: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(192, 150, 66, 0.4)' },
          '50%': { boxShadow: '0 0 0 12px rgba(192, 150, 66, 0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
}
