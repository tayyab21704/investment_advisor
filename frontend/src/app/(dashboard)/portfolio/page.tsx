'use client';

import { PieChart } from 'lucide-react';
import Link from 'next/link';

export default function PortfolioPage() {
    return (
        <div className="flex flex-col items-center justify-center h-[60vh] gap-5">
            <div
                className="w-20 h-20 rounded-3xl flex items-center justify-center bg-primary-dim border border-primary/20 shadow-lg"
            >
                <PieChart size={36} className="text-primary" />
            </div>
            <div className="text-xl tracking-tight font-bold text-text-primary">Portfolio Tracker</div>
            <div className="text-sm text-center max-w-sm text-text-secondary">
                Portfolio tracking is currently being built. Utilize the AI Council Room directly to process investments and track algorithmic actions.
            </div>
            <Link
                href="/council"
                className="mt-4 px-6 py-3 rounded-xl text-xs font-mono font-bold uppercase tracking-widest transition-all bg-primary text-text-inverse hover:opacity-90 shadow-[0_0_15px_rgba(var(--primary-rgb),0.3)]"
            >
                Open Council Room
            </Link>
        </div>
    );
}
