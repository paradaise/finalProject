import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      keyframes: {
        shake: {
          '10%, 90%': {
            transform: 'translate3d(-1px, 0, 0)',
          },
          '20%, 80%': {
            transform: 'translate3d(2px, 0, 0)',
          },
          '30%, 50%, 70%': {
            transform: 'translate3d(-4px, 0, 0)',
          },
          '40%, 60%': {
            transform: 'translate3d(4px, 0, 0)',
          },
        },
        bell: {
          '0%, 100%': { transform: 'rotate(0)' },
          '10%, 30%, 50%, 70%, 90%': { transform: 'rotate(-10deg)' },
          '20%, 40%, 60%, 80%': { transform: 'rotate(10deg)' },
        }
      },
      animation: {
        shake: 'shake 0.82s cubic-bezier(.36,.07,.19,.97) both',
        bell: 'bell 1s ease-in-out',
      },
    },
  },
  plugins: [],
} satisfies Config;
