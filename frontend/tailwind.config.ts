import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bloom: {
          50: "#fef7f2",
          100: "#fce8db",
          200: "#f9c9a8",
          300: "#f5a373",
          400: "#f08049",
          500: "#e8612b",
          600: "#cd4a1c",
          700: "#a73818",
        },
      },
    },
  },
  plugins: [],
};

export default config;
