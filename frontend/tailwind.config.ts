import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      boxShadow: {
        panel: "0 16px 40px -24px rgb(15 23 42 / 0.35)",
      },
    },
  },
  plugins: [],
};

export default config;
