'use client';

import { useEffect, useState, useRef } from 'react';
import { fetchTopMovers } from '@/lib/api';
import type { MoverDetail } from '@/lib/types';
import SparkLine from '@/components/ui/SparkLine';
import Link from 'next/link';

type Tab = 'gainers' | 'losers';

function MoverRow({ m }: { m: MoverDetail }) {
    const isPos = m.change_pct >= 0;
    return (
        <Link
            href={`/stock/${m.symbol}`}
            className="flex items-center gap-4 py-3 px-2 border-b border-border-subtle last:border-b-0 hover:bg-bg-elevated rounded-lg transition-all hover:scale-[1.01]"
        >
            {/* Symbol + name */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[13px] font-mono font-bold text-text-primary">
                        {m.symbol}
                    </span>
                    {m.volume_surge && (
                        <span
                            className="text-[9px] px-1.5 py-0.5 rounded font-mono font-bold bg-primary-dim text-primary"
                        >
                            VOL
                        </span>
                    )}
                </div>
                <div className="text-[11px] truncate text-text-secondary">
                    {m.name ?? m.symbol}
                </div>
            </div>

            {/* Sparkline */}
            <SparkLine
                data={m.sparkline ?? []}
                color={isPos ? 'var(--positive)' : 'var(--negative)'}
                width={70}
                height={28}
            />

            {/* Change */}
            <span
                className="text-sm font-mono font-semibold shrink-0 w-16 text-right"
                style={{ color: isPos ? 'var(--positive)' : 'var(--negative)' }}
            >
                {isPos ? '+' : ''}{m.change_pct?.toFixed(2)}%
            </span>
        </Link>
    );
}

export default function TopMovers() {
    const [tab, setTab] = useState<Tab>('gainers');
    const [gainers, setGainers] = useState<MoverDetail[]>([]);
    const [losers, setLosers] = useState<MoverDetail[]>([]);
    const [loading, setLoading] = useState(true);
    const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

    const load = async () => {
        const data = await fetchTopMovers();
        setGainers(data.gainers);
        setLosers(data.losers);
        setLoading(false);
    };

    useEffect(() => {
        load();
        intervalRef.current = setInterval(load, 60000);
        return () => clearInterval(intervalRef.current);
    }, []);

    const items = tab === 'gainers' ? gainers : losers;

    return (
        <div className="rounded-2xl p-6 bg-bg-surface border border-border-subtle shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-5">
                <span className="text-xs tracking-widest uppercase font-semibold text-text-secondary">
                    Top Movers
                </span>
                <div className="flex gap-1.5 bg-bg-elevated p-1 rounded-lg border border-border-subtle">
                    {(['gainers', 'losers'] as Tab[]).map((t) => (
                        <button
                            key={t}
                            onClick={() => setTab(t)}
                            className={`text-[11px] px-3 py-1 rounded-md font-mono capitalize transition-colors font-medium ${
                                tab === t
                                    ? t === 'gainers'
                                        ? 'bg-green-500/10 text-positive'
                                        : 'bg-red/10 text-negative'
                                    : 'text-text-secondary hover:text-text-primary'
                            }`}
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            {/* Rows */}
            <div className="pr-1">
                {loading
                    ? [1, 2, 3, 4, 5].map((n) => (
                        <div key={n} className="flex items-center gap-4 py-3 border-b border-border-subtle last:border-b-0">
                            <div className="flex-1">
                                <div className="skeleton h-3 w-16 rounded mb-1.5" />
                                <div className="skeleton h-2 w-24 rounded" />
                            </div>
                            <div className="skeleton h-7 w-16 rounded" />
                            <div className="skeleton h-4 w-14 rounded" />
                        </div>
                    ))
                    : items.map((m) => <MoverRow key={m.symbol} m={m} />)}
            </div>
        </div>
    );
}
