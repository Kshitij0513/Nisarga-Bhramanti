/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#005B9A',
        'secondary': '#007CBA',
        'accent': '#F0A800',
        'background': '#F5F7FA',
        'surface': '#FFFFFF',
        'text-primary': '#333333',
        'text-secondary': '#666666',
        'border': '#E0E0E0',
      },
    },
  },
  plugins: [],
};