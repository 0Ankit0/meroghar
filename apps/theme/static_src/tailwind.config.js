/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../../../**/*.{html,py,js}',
    '../../**/*.{html,py,js}',
    '../../../templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        /* Primary - Indigo (Trust, Professional) */
        primary: {
          50: 'oklch(96.5% 0.015 275)',
          100: 'oklch(93% 0.034 272.788)',
          200: 'oklch(86% 0.068 274)',
          300: 'oklch(78% 0.11 275)',
          400: 'oklch(68% 0.18 276)',
          500: 'oklch(58.5% 0.233 277.117)',
          600: 'oklch(51.1% 0.262 276.966)',
          DEFAULT: 'oklch(51.1% 0.262 276.966)', // 600
          700: 'oklch(45.7% 0.24 277.023)',
          800: 'oklch(40% 0.19 277)',
          900: 'oklch(35.9% 0.144 278.697)',
          950: 'oklch(28% 0.09 278)',
          foreground: 'oklch(100% 0 0)',
        },
        /* Secondary - Blue (Information, Calm) */
        secondary: {
          50: 'oklch(97% 0.014 254.604)',
          100: 'oklch(93.2% 0.032 255.585)',
          200: 'oklch(88.2% 0.059 254.128)',
          300: 'oklch(80.9% 0.105 251.813)',
          400: 'oklch(70% 0.17 255)',
          500: 'oklch(60% 0.22 258)',
          600: 'oklch(51% 0.24 260)',
          DEFAULT: 'oklch(51% 0.24 260)', // 600
          700: 'oklch(48.8% 0.243 264.376)',
          800: 'oklch(42.4% 0.199 265.638)',
          900: 'oklch(36% 0.15 266)',
          950: 'oklch(28% 0.1 266)',
          foreground: 'oklch(100% 0 0)',
        },
        /* Accent - Purple (Highlights, CTAs) */
        accent: {
          50: 'oklch(97% 0.02 295)',
          100: 'oklch(94% 0.04 295)',
          200: 'oklch(88% 0.08 295)',
          300: 'oklch(80% 0.14 295)',
          400: 'oklch(70% 0.2 295)',
          500: 'oklch(60% 0.24 295)',
          600: 'oklch(52% 0.26 295)',
          DEFAULT: 'oklch(52% 0.26 295)', // 600
          700: 'oklch(45% 0.23 295)',
          800: 'oklch(38% 0.18 295)',
          900: 'oklch(32% 0.13 295)',
          950: 'oklch(25% 0.08 295)',
          foreground: 'oklch(100% 0 0)',
        },
        /* Semantic Colors */
        success: {
          50: 'oklch(98.2% 0.018 155.826)',
          100: 'oklch(96.2% 0.044 156.743)',
          200: 'oklch(92.5% 0.084 155.995)',
          300: 'oklch(86% 0.14 155)',
          400: 'oklch(76% 0.19 152)',
          500: 'oklch(67% 0.21 150)',
          600: 'oklch(62.7% 0.194 149.214)',
          DEFAULT: 'oklch(62.7% 0.194 149.214)', // 600
          700: 'oklch(52.7% 0.154 150.069)',
          800: 'oklch(44.8% 0.119 151.328)',
          900: 'oklch(39.3% 0.095 152.535)',
          950: 'oklch(30% 0.06 152)',
        },
        warning: {
          50: 'oklch(98.7% 0.026 102.212)',
          100: 'oklch(97.3% 0.071 103.193)',
          200: 'oklch(94.5% 0.129 101.54)',
          300: 'oklch(90% 0.18 95)',
          400: 'oklch(82% 0.19 85)',
          500: 'oklch(75% 0.18 75)',
          600: 'oklch(68.1% 0.162 75.834)',
          DEFAULT: 'oklch(68.1% 0.162 75.834)', // 600
          700: 'oklch(55.4% 0.135 66.442)',
          800: 'oklch(47.6% 0.114 61.907)',
          900: 'oklch(40% 0.09 60)',
          950: 'oklch(30% 0.06 58)',
        },
        destructive: {
          50: 'oklch(97.1% 0.013 17.38)',
          100: 'oklch(93.6% 0.032 17.717)',
          200: 'oklch(88.5% 0.062 18.334)',
          300: 'oklch(82% 0.12 20)',
          400: 'oklch(72% 0.2 22)',
          500: 'oklch(63.7% 0.237 25.331)',
          600: 'oklch(57.7% 0.245 27.325)',
          DEFAULT: 'oklch(97.1% 0.013 17.38)', // 50 for bg
          700: 'oklch(50.5% 0.213 27.518)',
          800: 'oklch(44.4% 0.177 26.899)',
          900: 'oklch(39.6% 0.141 25.723)',
          950: 'oklch(30% 0.09 25)',
          foreground: 'oklch(50.5% 0.213 27.518)', // 700 matches theme.css .text-destructive-foreground
        },
        info: {
          50: 'oklch(97.5% 0.015 195)',
          100: 'oklch(94% 0.03 195)',
          200: 'oklch(88% 0.06 195)',
          300: 'oklch(80% 0.11 195)',
          400: 'oklch(70% 0.15 195)',
          500: 'oklch(62% 0.18 195)',
          600: 'oklch(54% 0.19 195)',
          DEFAULT: 'oklch(54% 0.19 195)', // 600
          700: 'oklch(46% 0.16 195)',
          800: 'oklch(38% 0.13 195)',
          900: 'oklch(32% 0.1 195)',
          950: 'oklch(25% 0.06 195)',
        },
        /* UI Colors */
        background: {
          DEFAULT: 'oklch(100% 0 0)',
          secondary: 'oklch(98.5% 0.002 247.839)',
          tertiary: 'oklch(96.7% 0.003 264.542)',
        },
        foreground: {
          DEFAULT: 'oklch(21% 0.034 264.665)',
          secondary: 'oklch(37.3% 0.034 259.733)',
          tertiary: 'oklch(55.1% 0.027 264.364)',
        },
        border: {
          DEFAULT: 'oklch(87.2% 0.01 258.338)',
          secondary: 'oklch(92.8% 0.006 264.531)',
        },
        muted: {
          DEFAULT: 'oklch(96.7% 0.003 264.542)',
          foreground: 'oklch(55.1% 0.027 264.364)',
        },
        card: {
          DEFAULT: 'oklch(100% 0 0)',
          foreground: 'oklch(21% 0.034 264.665)',
        },
        popover: {
          DEFAULT: 'oklch(100% 0 0)',
          foreground: 'oklch(21% 0.034 264.665)',
        },
        input: {
          DEFAULT: 'oklch(87.2% 0.01 258.338)',
          background: 'oklch(100% 0 0)',
        },
        ring: 'oklch(51.1% 0.262 276.966)',
      },
      textColor: theme => ({
        destructive: theme('colors.destructive.600'), // Override text-destructive to use 600
      }),
      backgroundColor: theme => ({
        destructive: theme('colors.destructive.50'),  // Override bg-destructive to use 50
      }),
      boxShadow: {
        sm: '0 1px 2px 0 oklch(0% 0 0 / 0.05)',
        DEFAULT: '0 1px 3px 0 oklch(0% 0 0 / 0.1), 0 1px 2px -1px oklch(0% 0 0 / 0.1)',
        md: '0 4px 6px -1px oklch(0% 0 0 / 0.1), 0 2px 4px -2px oklch(0% 0 0 / 0.1)',
        lg: '0 10px 15px -3px oklch(0% 0 0 / 0.1), 0 4px 6px -4px oklch(0% 0 0 / 0.1)',
        xl: '0 20px 25px -5px oklch(0% 0 0 / 0.1), 0 8px 10px -6px oklch(0% 0 0 / 0.1)',
        '2xl': '0 25px 50px -12px oklch(0% 0 0 / 0.25)',
      },
      borderRadius: {
        sm: '0.25rem',
        DEFAULT: '0.5rem',
        md: '0.5rem',
        lg: '0.75rem',
        xl: '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
        full: '9999px',
      },
    },
  },
  plugins: [],
}
