'use client';

import { useEffect, useState, useRef } from 'react';
import { fetchMarketIndices } from '@/lib/api';
import type { IndexDetail } from '@/lib/types';
import SparkLine from '@/components/ui/SparkLine';
import ChangeLabel from '@/components/ui/ChangeLabel';
import RegimeBadge from '@/components/ui/RegimeBadge';
import Link from 'next/link';

const SYMBOL_MAP: Record<string, string> = {
    '^NSEI': 'NIFTY 50',
    '^BSESN': 'SENSEX',
    '^NSEBANK': 'BANK NIFTY',
    '^CNXIT': 'NIFTY IT',
};

function Skeleton() {
    return (
        <div className="rounded-2xl p-6 flex flex-col gap-4 bg-bg-surface border border-border-subtle shadow-xl">
            <div className="skeleton h-3 w-24 rounded" />
            <div className="skeleton h-8 w-36 rounded" />
            <div className="skeleton h-3 w-20 rounded" />
        </div>
    );
}

function IndexCardItem({
    idx,
    isSelected,
    onSelect
}: {
    idx: IndexDetail;
    isSelected: boolean;
    onSelect: (symbol: string, name: string) => void;
}) {
    const isPos = idx.change_pct >= 0;
    const name = SYMBOL_MAP[idx.symbol] ?? idx.name ?? idx.symbol;
    const exchange = idx.symbol.startsWith('^BSE') ? 'BSE' : 'NSE';

    return (
        <div
            onClick={() => onSelect(idx.symbol, name)}
            className={`group block rounded-2xl p-6 transition-all duration-300 cursor-pointer shadow-xl ${
                isSelected 
                    ? 'bg-bg-elevated border-border-accent ring-1 ring-border-accent/50' 
                    : 'bg-bg-surface border-border-subtle hover:bg-bg-elevated hover:border-border-default'
            } border`}
        >
            {/* Top row */}
            <div className="flex items-center justify-between mb-4">
                <span className="text-[11px] tracking-widest uppercase font-mono text-text-secondary">
                    {name}
                </span>
                <span
                    className={`text-[9px] px-2 py-0.5 rounded-full font-mono tracking-wider border ${
                        exchange === 'NSE'
                            ? 'text-primary bg-primary-dim border-primary/20'
                            : 'text-blue bg-blue-dim border-blue/20'
                    }`}
                >
                    {exchange}
                </span>
            </div>

            {/* Price */}
            <div className="mono-num text-3xl font-semibold mb-3 text-text-primary tracking-tight">
                {idx.current_price?.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
            </div>

            {/* Bottom row */}
            <div className="flex items-end justify-between">
                <ChangeLabel value={idx.change_pct} absolute={idx.change} size="sm" />
                <div className="flex flex-col items-end gap-1.5">
                    <SparkLine data={idx.sparkline ?? []} color={isPos ? 'var(--positive)' : 'var(--negative)'} />
                    <RegimeBadge regime={idx.market_regime ?? 'NEUTRAL'} confidence={idx.regime_confidence} />
                </div>
            </div>
            {/* Subtle View Detail link */}
            <Link
                href={`/stock/${idx.symbol}`}
                className="block mt-5 text-center text-[10px] uppercase tracking-wider text-text-muted hover:text-primary transition-colors font-medium border-t border-border-subtle pt-3"
                onClick={(e) => e.stopPropagation()}
            >
                View detailed analysis →
            </Link>
        </div>
    );
}

export default function IndexCards({ activeSymbol, onSelect }: { activeSymbol?: string; onSelect?: (sym: string, name: string) => void }) {
    const [indices, setIndices] = useState<IndexDetail[]>([]);
    const [loading, setLoading] = useState(true);
    const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

    const load = async () => {
        const data = await fetchMarketIndices();
        if (data.length) { setIndices(data); setLoading(false); }
    };

    useEffect(() => {
        load();
        intervalRef.current = setInterval(load, 60000);
        return () => clearInterval(intervalRef.current);
    }, []);

    if (loading) {
        return (
            <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((n) => <Skeleton key={n} />)}
            </div>
        );
    }

    return (
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
            {indices.map((idx) => (
                <IndexCardItem
                    key={idx.symbol}
                    idx={idx}
                    isSelected={activeSymbol === idx.symbol}
                    onSelect={onSelect ?? (() => { })}
                />
            ))}
        </div>
    );
}
