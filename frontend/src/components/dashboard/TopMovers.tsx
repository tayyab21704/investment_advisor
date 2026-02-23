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
            className="flex items-center gap-3 py-2.5 px-1 border-b last:border-b-0 hover:bg-[#252525] rounded transition-colors"
            style={{ borderColor: '#2a2a2a' }}
        >
            {/* Symbol + name */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                    <span className="text-xs font-mono font-bold" style={{ color: '#e5e5e5' }}>
                        {m.symbol}
                    </span>
                    {m.volume_surge && (
                        <span
                            className="text-[8px] px-1 py-0.5 rounded font-mono font-bold"
                            style={{ background: 'rgba(234,146,62,0.15)', color: '#ea923e' }}
                        >
                            VOL
                        </span>
                    )}
                </div>
                <div className="text-[10px] truncate" style={{ color: '#888' }}>
                    {m.name ?? m.symbol}
                </div>
            </div>

            {/* Sparkline */}
            <SparkLine
                data={m.sparkline ?? []}
                color={isPos ? '#22c55e' : '#ef4444'}
                width={60}
                height={24}
            />

            {/* Change */}
            <span
                className="text-xs font-mono font-semibold shrink-0"
                style={{ color: isPos ? '#22c55e' : '#ef4444' }}
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
        <div
            className="rounded-xl p-5"
            style={{ background: '#0e0e0e', border: '1px solid #333' }}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <span className="text-[10px] tracking-widest uppercase font-mono" style={{ color: '#888' }}>
                    Top Movers
                </span>
                <div className="flex gap-1">
                    {(['gainers', 'losers'] as Tab[]).map((t) => (
                        <button
                            key={t}
                            onClick={() => setTab(t)}
                            className="text-[10px] px-2 py-0.5 rounded font-mono capitalize transition-colors"
                            style={
                                tab === t
                                    ? t === 'gainers'
                                        ? { background: 'rgba(34,197,94,0.15)', color: '#22c55e' }
                                        : { background: 'rgba(239,68,68,0.15)', color: '#ef4444' }
                                    : { color: '#888' }
                            }
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            {/* Rows */}
            <div>
                {loading
                    ? [1, 2, 3, 4, 5].map((n) => (
                        <div key={n} className="flex items-center gap-3 py-2.5 border-b last:border-b-0" style={{ borderColor: '#2a2a2a' }}>
                            <div className="flex-1">
                                <div className="skeleton h-3 w-16 rounded mb-1" />
                                <div className="skeleton h-2.5 w-24 rounded" />
                            </div>
                            <div className="skeleton h-6 w-14 rounded" />
                            <div className="skeleton h-3 w-12 rounded" />
                        </div>
                    ))
                    : items.map((m) => <MoverRow key={m.symbol} m={m} />)}
            </div>
        </div>
    );
}
