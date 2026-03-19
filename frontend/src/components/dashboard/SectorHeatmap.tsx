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
        <div className="rounded-2xl p-6 h-full bg-bg-surface border border-border-subtle shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-5">
                <span className="text-xs tracking-widest uppercase font-semibold text-text-secondary">
                    Sector Performance
                </span>
                <div className="flex gap-1.5 bg-bg-elevated p-1 rounded-lg border border-border-subtle">
                    {TF_BTNS.map(({ label, key }) => (
                        <button
                            key={key}
                            onClick={() => setTf(key)}
                            className="text-[10px] px-3 py-1 rounded-md font-mono transition-colors"
                            style={
                                tf === key
                                    ? { background: 'var(--primary)', color: 'var(--color-text-inverse)', fontWeight: 700 }
                                    : { color: 'var(--color-text-secondary)' }
                            }
                        >
                            {label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Bars */}
            <div className="flex flex-col gap-3">
                {loading
                    ? [1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
                        <div key={n} className="flex items-center gap-3">
                            <div className="skeleton h-3 w-24 rounded" />
                            <div className="skeleton h-2 flex-1 rounded" />
                            <div className="skeleton h-3 w-12 rounded" />
                        </div>
                    ))
                    : sectors.map((s) => {
                        const perf = getPerf(s, tf);
                        const isPos = perf >= 0;
                        const fillPct = Math.abs(perf / absMax) * 100;
                        return (
                            <div
                                key={s.sector_name}
                                className="group relative flex items-center gap-3 cursor-default py-1"
                                onMouseEnter={() => setTooltip(s)}
                                onMouseLeave={() => setTooltip(null)}
                            >
                                <span
                                    className="text-[11px] font-mono w-28 shrink-0 truncate text-text-secondary group-hover:text-text-primary transition-colors"
                                    title={s.sector_name}
                                >
                                    {s.sector_name}
                                </span>
                                <div className="flex-1 h-2 rounded-full overflow-hidden bg-bg-elevated border border-border-subtle/50">
                                    <div
                                        className="h-full rounded-full transition-all duration-500 shadow-sm"
                                        style={{
                                            width: `${fillPct}%`,
                                            background: isPos ? 'var(--positive)' : 'var(--negative)',
                                            boxShadow: `0 0 10px ${isPos ? 'var(--color-green-glow)' : 'var(--color-red-glow)'}`
                                        }}
                                    />
                                </div>
                                <span
                                    className="text-[11px] font-mono w-14 text-right shrink-0"
                                    style={{ color: isPos ? 'var(--positive)' : 'var(--negative)' }}
                                >
                                    {isPos ? '+' : ''}{perf.toFixed(2)}%
                                </span>

                                {/* Hover tooltip */}
                                {tooltip?.sector_name === s.sector_name && (
                                    <div
                                        className="absolute left-[120px] top-6 z-20 rounded-xl p-3 text-xs font-mono shadow-2xl bg-bg-overlay border border-border-default backdrop-blur-md"
                                        style={{ minWidth: 180 }}
                                    >
                                        <div className="mb-1.5">
                                            <span className="text-text-muted">Best: </span>
                                            <span className="text-positive">{s.top_performer ?? '—'}</span>
                                        </div>
                                        <div className="mb-1.5">
                                            <span className="text-text-muted">Worst: </span>
                                            <span className="text-negative">{s.worst_performer ?? '—'}</span>
                                        </div>
                                        <div>
                                            <span className="text-text-muted">Mkt Cap: </span>
                                            <span className="text-text-primary font-bold">
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
