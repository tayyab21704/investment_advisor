'use client';

import { PieChart } from 'lucide-react';
import Link from 'next/link';

export default function PortfolioPage() {
    return (
        <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
            <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center"
                style={{ background: 'rgba(234,146,62,0.1)', border: '1px solid rgba(234,146,62,0.2)' }}
            >
                <PieChart size={28} color="#ea923e" />
            </div>
            <div className="text-base font-bold" style={{ color: '#e5e5e5' }}>Portfolio Tracker</div>
            <div className="text-sm text-center max-w-xs" style={{ color: '#888' }}>
                Portfolio tracking is being built. Use the Council Room to generate AI recommendations.
            </div>
            <Link
                href="/council"
                className="mt-2 px-5 py-2 rounded-lg text-xs font-mono font-bold uppercase tracking-widest transition-colors"
                style={{ background: '#ea923e', color: '#0e0e0e' }}
            >
                Open Council Room
            </Link>
        </div>
    );
}
