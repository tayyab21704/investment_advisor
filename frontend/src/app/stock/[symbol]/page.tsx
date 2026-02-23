'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { AlertCircle, TrendingUp, TrendingDown } from 'lucide-react';
import { fetchStockDetail } from '@/lib/api';
import type { StockDetail } from '@/lib/types';
import { formatVolume, clamp } from '@/lib/utils';
import PriceChart from '@/components/stock/PriceChart';
import FundamentalsGrid from '@/components/stock/FundamentalsGrid';
import TechnicalsPanel from '@/components/stock/TechnicalsPanel';
import RegimeBadge from '@/components/ui/RegimeBadge';

function Skeleton() {
    return (
        <div className="px-6 py-5 max-w-[1400px] mx-auto">
            <div className="grid gap-5" style={{ gridTemplateColumns: '1fr 360px' }}>
                <div className="space-y-4">
                    <div className="skeleton h-10 w-48 rounded" />
                    <div className="skeleton h-6 w-72 rounded" />
                    <div className="skeleton h-[380px] w-full rounded-xl" />
                </div>
                <div className="space-y-4">
                    <div className="skeleton h-[280px] rounded-xl" />
                    <div className="skeleton h-[320px] rounded-xl" />
                </div>
            </div>
        </div>
    );
}

export default function StockPage() {
    const params = useParams();
    const symbol = (params?.symbol as string ?? '').toUpperCase();
    const [detail, setDetail] = useState<StockDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!symbol) return;
        setLoading(true);
        setError(null);
        fetchStockDetail(symbol)
            .then((d) => { if (d) setDetail(d); else setError('Symbol not found'); })
            .catch(() => setError('Failed to load stock data'))
            .finally(() => setLoading(false));
    }, [symbol]);

    if (loading) return <Skeleton />;

    if (error || !detail) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-3">
                <AlertCircle size={28} color="#555" />
                <p className="text-sm font-mono" style={{ color: '#888' }}>{error ?? 'Unknown error'}</p>
            </div>
        );
    }

    const isPos = detail.change_pct >= 0;
    const ArrowIcon = isPos ? TrendingUp : TrendingDown;
    const arrowColor = isPos ? '#22c55e' : '#ef4444';

    // Day range bar position
    const dayLow = detail.day_low ?? detail.current_price;
    const dayHigh = detail.day_high ?? detail.current_price;
    const dayRangePct = clamp(
        ((detail.current_price - dayLow) / (dayHigh - dayLow || 1)) * 100,
        0, 100
    );

    const stats = [
        { label: 'Open', value: detail.open != null ? `₹${detail.open.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : '—' },
        { label: 'Prev Close', value: detail.prev_close != null ? `₹${detail.prev_close.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : '—' },
        { label: 'Day High', value: `₹${dayHigh.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` },
        { label: 'Day Low', value: `₹${dayLow.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` },
        { label: 'Volume', value: formatVolume(detail.volume) },
        { label: 'Avg Vol', value: formatVolume(detail.avg_volume) },
    ];

    return (
        <div className="px-6 py-5 max-w-[1400px] mx-auto animate-fade-up">
            <div className="grid gap-5" style={{ gridTemplateColumns: '1fr 360px' }}>
                {/* ── Left column ──────────────────────────────────────── */}
                <div className="space-y-5">
                    {/* Stock header */}
                    <div
                        className="rounded-xl p-5"
                        style={{ background: '#0e0e0e', border: '1px solid #333' }}
                    >
                        {/* Symbol + name */}
                        <div className="flex items-start justify-between mb-4">
                            <div>
                                <div className="text-3xl font-mono font-bold mb-1" style={{ color: '#e5e5e5' }}>
                                    {detail.symbol}
                                </div>
                                <div className="text-sm mb-2" style={{ color: '#888' }}>{detail.name}</div>
                                <div className="flex items-center gap-2 flex-wrap">
                                    {detail.sector && (
                                        <span className="text-[10px] px-2 py-0.5 rounded-full font-mono" style={{ color: '#6a9d9e', background: 'rgba(106,157,158,0.12)', border: '1px solid rgba(106,157,158,0.2)' }}>
                                            {detail.sector}
                                        </span>
                                    )}
                                    {detail.industry && (
                                        <span className="text-[10px] px-2 py-0.5 rounded-full font-mono" style={{ color: '#888', background: '#252525', border: '1px solid #333' }}>
                                            {detail.industry}
                                        </span>
                                    )}
                                </div>
                            </div>
                            <RegimeBadge regime={detail.regime ?? 'NEUTRAL'} confidence={detail.regime_confidence} size="sm" />
                        </div>

                        {/* Price */}
                        <div className="mb-3">
                            <div className="text-4xl font-mono font-bold mb-1" style={{ color: '#e5e5e5' }}>
                                ₹{detail.current_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                            </div>
                            <div className="flex items-center gap-2">
                                <ArrowIcon size={16} color={arrowColor} />
                                <span className="font-mono text-sm" style={{ color: arrowColor }}>
                                    {detail.change > 0 ? '+' : ''}{detail.change.toFixed(2)}
                                    {' '}({detail.change_pct > 0 ? '+' : ''}{detail.change_pct.toFixed(2)}%)
                                </span>
                            </div>
                        </div>

                        {/* Day range bar */}
                        <div className="mb-1">
                            <div className="flex justify-between text-[9px] font-mono mb-1" style={{ color: '#555' }}>
                                <span>Day Low ₹{dayLow.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                                <span>Day High ₹{dayHigh.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                            </div>
                            <div className="relative h-1 rounded-full" style={{ background: '#252525' }}>
                                <div
                                    className="absolute h-full rounded-full"
                                    style={{ width: `${dayRangePct}%`, background: isPos ? '#22c55e' : '#ef4444' }}
                                />
                                <div
                                    className="absolute w-2.5 h-2.5 rounded-full -top-[3px]"
                                    style={{ left: `calc(${dayRangePct}% - 5px)`, background: isPos ? '#22c55e' : '#ef4444', border: '2px solid #0e0e0e' }}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Chart */}
                    <PriceChart detail={detail} />

                    {/* Key stats strip */}
                    <div
                        className="rounded-xl px-5 py-3 grid grid-cols-6 divide-x"
                        style={{ background: '#0e0e0e', border: '1px solid #333' }}
                    >
                        {stats.map(({ label, value }) => (
                            <div key={label} className="px-3 first:pl-0 last:pr-0">
                                <div className="text-[9px] uppercase tracking-wider font-mono mb-0.5" style={{ color: '#555' }}>
                                    {label}
                                </div>
                                <div className="text-xs font-mono" style={{ color: '#e5e5e5' }}>
                                    {value}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* ── Right column ─────────────────────────────────────── */}
                <div className="space-y-4">
                    <FundamentalsGrid detail={detail} />
                    <TechnicalsPanel detail={detail} />
                </div>
            </div>
        </div>
    );
}
