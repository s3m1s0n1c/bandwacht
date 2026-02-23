/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        sdr: {
          bg: '#0a0e17',
          surface: '#111827',
          border: '#1f2937',
          text: '#e5e7eb',
          muted: '#9ca3af',
          green: '#00ff41',
          cyan: '#06b6d4',
          red: '#ef4444',
          amber: '#f59e0b',
        },
      },
    },
  },
  plugins: [],
}
