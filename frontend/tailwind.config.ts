import type { Config } from 'tailwindcss';

const config: Config = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                bg: {
                    base: '#0A0A0A',
                    surface: '#111111',
                    elevated: '#181818',
                    overlay: '#1F1F1F',
                },
                border: {
                    subtle: '#1E1E1E',
                    default: '#2A2A2A',
                    strong: '#3D3D3D',
                    accent: '#00C896',
                },
                text: {
                    primary: '#EFEFEF',
                    secondary: '#888888',
                    muted: '#4A4A4A',
                    inverse: '#0A0A0A',
                },
                green: {
                    DEFAULT: '#00C896',
                    dim: '#00C89618',
                    glow: '#00C89630',
                    bright: '#00DFA8',
                },
                red: {
                    DEFAULT: '#FF5252',
                    dim: '#FF525218',
                    glow: '#FF525230',
                },
                amber: {
                    DEFAULT: '#FFB347',
                    dim: '#FFB34718',
                },
                blue: {
                    DEFAULT: '#4D9EFF',
                    dim: '#4D9EFF18',
                },
                purple: {
                    DEFAULT: '#A78BFA',
                    dim: '#A78BFA15',
                    glow: '#A78BFA25',
                },
            },
            fontFamily: {
                display: ['var(--font-display)', 'Sora', 'sans-serif'],
                body: ['var(--font-body)', 'Geist', 'sans-serif'],
                mono: ['var(--font-mono)', 'DM Mono', 'monospace'],
            },
            fontSize: {
                'display-xl': ['3.5rem', { lineHeight: '1.1', letterSpacing: '-0.03em' }],
                'display-lg': ['2.5rem', { lineHeight: '1.15', letterSpacing: '-0.03em' }],
                'display-md': ['1.75rem', { lineHeight: '1.2', letterSpacing: '-0.02em' }],
                'display-sm': ['1.375rem', { lineHeight: '1.25', letterSpacing: '-0.01em' }],
                'h1': ['1.5rem', { lineHeight: '1.3', letterSpacing: '-0.01em' }],
                'h2': ['1.25rem', { lineHeight: '1.35', letterSpacing: '-0.005em' }],
                'h3': ['1rem', { lineHeight: '1.4', letterSpacing: '0' }],
                'label': ['0.75rem', { lineHeight: '1.5', letterSpacing: '0.08em' }],
            },
            borderRadius: {
                sm: '6px',
                md: '10px',
                lg: '14px',
                xl: '20px',
            },
            keyframes: {
                shimmer: {
                    '0%': { backgroundPosition: '-1000px 0' },
                    '100%': { backgroundPosition: '1000px 0' },
                },
                'fade-up': {
                    from: { opacity: '0', transform: 'translateY(12px)' },
                    to: { opacity: '1', transform: 'translateY(0)' },
                },
                'pulse-dot': {
                    '0%, 100%': { opacity: '1', transform: 'scale(1)' },
                    '50%': { opacity: '0.5', transform: 'scale(0.85)' },
                },
                'flash-green': {
                    '0%': { color: '#EFEFEF' },
                    '30%': { color: '#00C896' },
                    '100%': { color: '#EFEFEF' },
                },
                'flash-red': {
                    '0%': { color: '#EFEFEF' },
                    '30%': { color: '#FF5252' },
                    '100%': { color: '#EFEFEF' },
                },
            },
            animation: {
                shimmer: 'shimmer 1.6s infinite linear',
                'fade-up': 'fade-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) both',
                'pulse-dot': 'pulse-dot 2s ease-in-out infinite',
                'flash-green': 'flash-green 0.6s ease both',
                'flash-red': 'flash-red 0.6s ease both',
            },
            backgroundImage: {
                shimmer: 'linear-gradient(90deg, #181818 25%, #222222 50%, #181818 75%)',
            },
        },
    },
    plugins: [],
};

export default config;
