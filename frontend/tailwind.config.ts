import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#f5f7fb",
        foreground: "#101828",
        card: "#ffffff",
        muted: "#667085",
        border: "#d9e0ea",
        accent: "#d5e5ff",
        primary: "#155eef",
      },
      boxShadow: {
        soft: "0 12px 40px rgba(16, 24, 40, 0.08)",
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.5rem",
      },
    },
  },
  plugins: [],
};

export default config;
