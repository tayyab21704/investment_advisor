import type { Metadata } from 'next';
import { Geist_Mono, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import Header from '@/components/layout/Header';
import TickerStrip from '@/components/layout/TickerStrip';

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
      className={`dark ${geistMono.variable} ${jbMono.variable}`}
    >
      <body className="antialiased bg-[#1a1a1a] text-[#e5e5e5]">
        <Header />
        <TickerStrip />
        <main>{children}</main>
      </body>
    </html>
  );
}
