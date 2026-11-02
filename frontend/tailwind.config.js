/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: '#1e3a5f',
        primary: '#2563eb',
        safe: '#22c55e',
        moderate: '#f59e0b',
        risky: '#ef4444',
      },
    },
  },
  plugins: [],
};
