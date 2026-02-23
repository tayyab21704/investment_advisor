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
        <div
            className="rounded-xl p-5 flex flex-col gap-3"
            style={{ background: '#0e0e0e', border: '1px solid #333' }}
        >
            <div className="skeleton h-3 w-24 rounded" />
            <div className="skeleton h-7 w-36 rounded" />
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
            className="group block rounded-xl p-5 transition-all duration-200 cursor-pointer"
            style={{
                background: '#0e0e0e',
                border: isSelected ? '1px solid rgba(234,146,62,0.6)' : '1px solid #333',
                boxShadow: isSelected ? '0 0 12px -3px rgba(234,146,62,0.2)' : 'none',
            }}
            onMouseEnter={(e) => {
                if (!isSelected) {
                    (e.currentTarget as HTMLElement).style.borderColor = 'rgba(234,146,62,0.35)';
                    (e.currentTarget as HTMLElement).style.boxShadow = '0 0 15px -3px rgba(234,146,62,0.1)';
                }
            }}
            onMouseLeave={(e) => {
                if (!isSelected) {
                    (e.currentTarget as HTMLElement).style.borderColor = '#333';
                    (e.currentTarget as HTMLElement).style.boxShadow = 'none';
                }
            }}
        >
            {/* Top row */}
            <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] tracking-widest uppercase font-mono" style={{ color: '#888' }}>
                    {name}
                </span>
                <span
                    className="text-[9px] px-1.5 py-0.5 rounded-full font-mono tracking-wider"
                    style={
                        exchange === 'NSE'
                            ? { color: '#ea923e', background: 'rgba(234,146,62,0.1)', border: '1px solid rgba(234,146,62,0.2)' }
                            : { color: '#6a9d9e', background: 'rgba(106,157,158,0.1)', border: '1px solid rgba(106,157,158,0.2)' }
                    }
                >
                    {exchange}
                </span>
            </div>

            {/* Price */}
            <div className="mono-num text-2xl font-bold mb-2" style={{ color: '#e5e5e5' }}>
                {idx.current_price?.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
            </div>

            {/* Bottom row */}
            <div className="flex items-end justify-between">
                <ChangeLabel value={idx.change_pct} absolute={idx.change} size="sm" />
                <div className="flex flex-col items-end gap-1">
                    <SparkLine data={idx.sparkline ?? []} color={isPos ? '#22c55e' : '#ef4444'} />
                    <RegimeBadge regime={idx.market_regime ?? 'NEUTRAL'} confidence={idx.regime_confidence} />
                </div>
            </div>
            {/* Subtle View Detail link */}
            <Link
                href={`/stock/${idx.symbol}`}
                className="block mt-4 text-center text-[9px] uppercase tracking-tighter text-[#555] hover:text-[#ea923e] transition-colors"
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
