/** Tailwind maps to CSS variables defined in src/index.css (single source of truth). */
const v = (name) => `rgb(var(--${name}) / <alpha-value>)`

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: v('ink'), soft: v('ink-soft'), raised: v('ink-raised') },
        cream: { DEFAULT: v('cream'), deep: v('cream-deep'), muted: v('cream-muted') },
        burgundy: { DEFAULT: v('burgundy'), light: v('burgundy-light'), dark: v('burgundy-dark') },
        sage: { DEFAULT: v('sage'), light: v('sage-light') },
        denim: { DEFAULT: v('denim'), light: v('denim-light') },
        rust: v('rust'),
        muted: v('muted'),
      },
      borderColor: { DEFAULT: 'var(--border)', strong: 'var(--border-strong)' },
      fontFamily: {
        display: ['"Space Grotesk"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        sans: ['Manrope', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      borderRadius: { xs: 'var(--radius-xs)', sm: 'var(--radius-sm)', md: 'var(--radius-md)' },
      boxShadow: {
        raised: 'var(--shadow-raised)',
        lift: 'var(--shadow-lift)',
      },
      transitionDuration: { fast: 'var(--dur-fast)', base: 'var(--dur-base)' },
      keyframes: {
        pulseDot: { '0%,100%': { opacity: '1' }, '50%': { opacity: '0.35' } },
      },
      animation: { 'pulse-dot': 'pulseDot 1.6s ease-in-out infinite' },
    },
  },
  plugins: [],
}
