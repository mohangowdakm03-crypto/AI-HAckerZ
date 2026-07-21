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
        background: "var(--ink)",
        foreground: "var(--txt)",
        ink: "var(--ink)",
        surface: "var(--surface)",
        surface2: "var(--surface2)",
        glass: "var(--glass)",
        cyan: { DEFAULT: "var(--cyan)", glow: "var(--cyan-glow)" },
        violet: { DEFAULT: "var(--violet)", glow: "var(--violet-glow)" },
        rose: "var(--rose)",
        emerald: "var(--emerald)",
        amber: "var(--amber)",
        txt: { DEFAULT: "var(--txt)", 2: "var(--txt2)", 3: "var(--txt3)" },
        border: { DEFAULT: "var(--border)", lit: "var(--border-lit)" }
      },
    },
  },
  plugins: [],
};
export default config;
