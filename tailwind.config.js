/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c3d66',
        },
      },
      fontFamily: {
        sans: ['system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
  safelist: [
    'bg-green-100', 'text-green-800', 'bg-green-50',
    'bg-yellow-100', 'text-yellow-800', 'bg-yellow-50',
    'bg-red-100', 'text-red-800', 'bg-red-50',
    'bg-blue-100', 'text-blue-800', 'bg-blue-50',
  ],
}
