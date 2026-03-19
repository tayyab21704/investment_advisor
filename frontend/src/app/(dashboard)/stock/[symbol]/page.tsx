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
            <div className="flex flex-col items-center justify-center h-64 gap-4">
                <AlertCircle size={32} className="text-text-muted" />
                <p className="text-sm font-mono text-text-secondary">{error ?? 'Unknown error'}</p>
            </div>
        );
    }

    const isPos = detail.change_pct >= 0;
    const ArrowIcon = isPos ? TrendingUp : TrendingDown;
    const arrowColor = isPos ? 'var(--positive)' : 'var(--negative)';

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
            <div className="grid gap-6" style={{ gridTemplateColumns: '1fr 360px' }}>
                {/* ── Left column ──────────────────────────────────────── */}
                <div className="space-y-6">
                    {/* Stock header */}
                    <div
                        className="rounded-2xl p-6 bg-bg-surface border border-border-subtle shadow-xl"
                    >
                        {/* Symbol + name */}
                        <div className="flex items-start justify-between mb-5">
                            <div>
                                <div className="text-3xl font-mono font-bold mb-1 text-text-primary tracking-tight">
                                    {detail.symbol}
                                </div>
                                <div className="text-sm mb-3 text-text-secondary">{detail.name}</div>
                                <div className="flex items-center gap-2 flex-wrap">
                                    {detail.sector && (
                                        <span className="text-[10px] px-2 py-0.5 rounded-md font-mono font-semibold text-blue bg-blue-dim border border-blue/20">
                                            {detail.sector}
                                        </span>
                                    )}
                                    {detail.industry && (
                                        <span className="text-[10px] px-2 py-0.5 rounded-md font-mono font-semibold text-text-secondary bg-bg-elevated border border-border-default">
                                            {detail.industry}
                                        </span>
                                    )}
                                </div>
                            </div>
                            <RegimeBadge regime={detail.regime ?? 'NEUTRAL'} confidence={detail.regime_confidence} size="md" />
                        </div>

                        {/* Price */}
                        <div className="mb-4">
                            <div className="text-4xl font-mono font-bold mb-1.5 text-text-primary tracking-tight">
                                ₹{detail.current_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                            </div>
                            <div className="flex items-center gap-2">
                                <ArrowIcon size={20} color={arrowColor} />
                                <span className="font-mono text-[15px] font-bold" style={{ color: arrowColor }}>
                                    {detail.change > 0 ? '+' : ''}{detail.change.toFixed(2)}
                                    {' '}({detail.change_pct > 0 ? '+' : ''}{detail.change_pct.toFixed(2)}%)
                                </span>
                            </div>
                        </div>

                        {/* Day range bar */}
                        <div className="mb-1">
                            <div className="flex justify-between text-[10px] font-mono mb-1.5 font-bold text-text-muted">
                                <span>Day Low ₹{dayLow.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                                <span>Day High ₹{dayHigh.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                            </div>
                            <div className="relative h-1.5 rounded-full bg-bg-elevated">
                                <div
                                    className="absolute h-full rounded-full"
                                    style={{ width: `${dayRangePct}%`, background: arrowColor }}
                                />
                                <div
                                    className="absolute w-3 h-3 rounded-full -top-[3px]"
                                    style={{ left: `calc(${dayRangePct}% - 6px)`, background: arrowColor, border: '2px solid var(--color-bg-surface)' }}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Chart */}
                    <PriceChart detail={detail} />

                    {/* Key stats strip */}
                    <div
                        className="rounded-2xl px-6 py-4 grid grid-cols-6 divide-x divide-border-subtle bg-bg-surface border border-border-subtle shadow-xl"
                    >
                        {stats.map(({ label, value }) => (
                            <div key={label} className="px-4 first:pl-0 last:pr-0">
                                <div className="text-[10px] uppercase tracking-wider font-mono font-semibold mb-1 text-text-muted">
                                    {label}
                                </div>
                                <div className="text-[13px] font-mono font-bold text-text-primary">
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
