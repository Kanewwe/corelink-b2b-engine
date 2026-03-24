/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-dark': '#0F1117',
        'bg-content': '#161B27',
        'glass-bg': 'rgba(30, 36, 53, 0.8)',
        'glass-border': 'rgba(42, 49, 71, 0.8)',
        'primary': '#4F8EF7',
        'primary-hover': '#3A7AE8',
        'accent': '#6EE7B7',
        'warning': '#F59E0B',
        'error': '#EF4444',
        'text-main': '#F1F5F9',
        'text-muted': '#94A3B8',
        'accent-cable': '#3B82F6',
        'accent-nameplate': '#EAB308',
        'accent-plastic': '#6EE7B7',
        'accent-auto': '#F97316',
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans TC', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
