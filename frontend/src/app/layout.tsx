import type { Metadata } from 'next';
import { Inter, Geist_Mono, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from '@/components/Providers';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const geistMono = Geist_Mono({
  subsets: ['latin'],
  variable: '--font-geist-mono',
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
});

const jbMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jb-mono',
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Investment Council | AI-Powered Advisory',
  description:
    'Autonomous multi-agent AI investment advisory system for Indian equity markets.',
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`dark ${inter.variable} ${geistMono.variable} ${jbMono.variable}`}
    >
      <body className="antialiased font-sans bg-bg-base text-text-primary">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
