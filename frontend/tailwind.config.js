/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        devanagari: ["Noto Sans Devanagari", "sans-serif"],
        shrikhand: ["Shrikhand", "cursive"],
      },
    },
  },
  plugins: [],
};
