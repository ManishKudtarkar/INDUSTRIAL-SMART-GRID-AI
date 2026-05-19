/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        grid: {
          bg:       '#0a0e1a',
          card:     '#0f1629',
          border:   '#1e2d4a',
          accent:   '#00d4ff',
          green:    '#00ff88',
          yellow:   '#ffb800',
          red:      '#ff3b5c',
          purple:   '#a855f7',
          muted:    '#4a5568',
        }
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'blink':      'blink 1.2s step-end infinite',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0' },
        }
      }
    },
  },
  plugins: [],
}
