import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Deep navy / charcoal for serious intelligence aesthetic
        undertow: {
          50: "#f7f7f8",
          100: "#eeeef0",
          200: "#d9d9de",
          300: "#b8b9c1",
          400: "#91929f",
          500: "#737484",
          600: "#5d5e6c",
          700: "#4c4d58",
          800: "#41424b",
          900: "#393941",
          950: "#1a1a1f",
        },
        // Accent - muted gold for highlights
        accent: {
          50: "#fdf9ef",
          100: "#f9f0d5",
          200: "#f2dea9",
          300: "#eac873",
          400: "#e3ad45",
          500: "#d99429",
          600: "#c07720",
          700: "#a0591d",
          800: "#82471f",
          900: "#6b3b1d",
          950: "#3c1d0c",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        serif: ["var(--font-source-serif)", "Georgia", "serif"],
        mono: ["var(--font-jetbrains)", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;

