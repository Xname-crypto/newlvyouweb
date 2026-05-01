/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx,vue}"],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        primary: "#0B1D26",
        secondary: "#1A3A4A",
        accent: "#FBD784",
        "text-main": "#FFFFFF",
        "text-muted": "#B8B8B8",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        serif: ["Playfair Display", "serif"],
      },
      backgroundImage: {
        "hero-gradient": "linear-gradient(to bottom, #0B1D26 0%, #1A3A4A 100%)",
      },
    },
  },
  plugins: [],
};
