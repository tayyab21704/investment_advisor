'use client';

import { useEffect, useState } from 'react';
import { fetchSectors } from '@/lib/api';
import type { SectorData } from '@/lib/types';

type Timeframe = '1d' | '1w' | '1m';

function getPerf(s: SectorData, tf: Timeframe) {
    if (tf === '1w') return s.performance_1w;
    if (tf === '1m') return s.performance_1m;
    return s.change_pct;
}

export default function SectorHeatmap() {
    const [sectors, setSectors] = useState<SectorData[]>([]);
    const [loading, setLoading] = useState(true);
    const [tf, setTf] = useState<Timeframe>('1d');
    const [tooltip, setTooltip] = useState<SectorData | null>(null);

    useEffect(() => {
        fetchSectors().then((data) => { setSectors(data); setLoading(false); });
    }, []);

    const perfs = sectors.map((s) => getPerf(s, tf));
    const absMax = Math.max(...perfs.map(Math.abs), 0.01);

    const TF_BTNS: { label: string; key: Timeframe }[] = [
        { label: '1D', key: '1d' },
        { label: '1W', key: '1w' },
        { label: '1M', key: '1m' },
    ];

    return (
        <div
            className="rounded-xl p-5 h-full"
            style={{ background: '#0e0e0e', border: '1px solid #333' }}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <span className="text-[10px] tracking-widest uppercase font-mono" style={{ color: '#888' }}>
                    Sector Performance
                </span>
                <div className="flex gap-1">
                    {TF_BTNS.map(({ label, key }) => (
                        <button
                            key={key}
                            onClick={() => setTf(key)}
                            className="text-[10px] px-2 py-0.5 rounded font-mono transition-colors"
                            style={
                                tf === key
                                    ? { background: '#ea923e', color: '#0e0e0e', fontWeight: 700 }
                                    : { color: '#888' }
                            }
                        >
                            {label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Bars */}
            <div className="flex flex-col gap-2">
                {loading
                    ? [1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
                        <div key={n} className="flex items-center gap-2">
                            <div className="skeleton h-2.5 w-20 rounded" />
                            <div className="skeleton h-1.5 flex-1 rounded" />
                            <div className="skeleton h-2.5 w-10 rounded" />
                        </div>
                    ))
                    : sectors.map((s) => {
                        const perf = getPerf(s, tf);
                        const isPos = perf >= 0;
                        const fillPct = Math.abs(perf / absMax) * 100;
                        return (
                            <div
                                key={s.sector_name}
                                className="group relative flex items-center gap-2 cursor-default"
                                onMouseEnter={() => setTooltip(s)}
                                onMouseLeave={() => setTooltip(null)}
                            >
                                <span
                                    className="text-[10px] font-mono w-24 shrink-0 truncate"
                                    style={{ color: '#888' }}
                                    title={s.sector_name}
                                >
                                    {s.sector_name}
                                </span>
                                <div
                                    className="flex-1 h-1.5 rounded-full overflow-hidden"
                                    style={{ background: '#252525' }}
                                >
                                    <div
                                        className="h-full rounded-full transition-all duration-500"
                                        style={{
                                            width: `${fillPct}%`,
                                            background: isPos ? '#22c55e' : '#ef4444',
                                        }}
                                    />
                                </div>
                                <span
                                    className="text-[10px] font-mono w-12 text-right shrink-0"
                                    style={{ color: isPos ? '#22c55e' : '#ef4444' }}
                                >
                                    {isPos ? '+' : ''}{perf.toFixed(2)}%
                                </span>

                                {/* Hover tooltip */}
                                {tooltip?.sector_name === s.sector_name && (
                                    <div
                                        className="absolute left-28 top-5 z-10 rounded-lg px-3 py-2 text-[10px] font-mono shadow-xl"
                                        style={{ background: '#252525', border: '1px solid #333', minWidth: 160 }}
                                    >
                                        <div className="mb-1">
                                            <span style={{ color: '#888' }}>Best: </span>
                                            <span style={{ color: '#22c55e' }}>{s.top_performer ?? '—'}</span>
                                        </div>
                                        <div className="mb-1">
                                            <span style={{ color: '#888' }}>Worst: </span>
                                            <span style={{ color: '#ef4444' }}>{s.worst_performer ?? '—'}</span>
                                        </div>
                                        <div>
                                            <span style={{ color: '#888' }}>Mkt Cap: </span>
                                            <span style={{ color: '#e5e5e5' }}>
                                                ₹{(s.market_cap_cr / 100000).toFixed(1)}L Cr
                                            </span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
            </div>
        </div>
    );
}
