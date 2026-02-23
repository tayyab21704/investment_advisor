'use client';

import type { StockDetail } from '@/lib/types';
import { clamp } from '@/lib/utils';

function SmaRow({
    label, color, sma, price,
}: { label: string; color: string; sma: number | null; price: number }) {
    if (sma == null) return null;
    const above = price >= sma;
    return (
        <div className="flex items-center justify-between py-2" style={{ borderBottom: '1px solid #2a2a2a' }}>
            <span className="text-[10px] font-mono" style={{ color: '#888' }}>{label}</span>
            <div className="flex items-center gap-3">
                <span className="text-xs font-mono" style={{ color }}>
                    ₹{sma.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                </span>
                <span
                    className="text-[9px] px-1.5 py-0.5 rounded font-mono uppercase tracking-wider"
                    style={
                        above
                            ? { background: 'rgba(34,197,94,0.12)', color: '#22c55e' }
                            : { background: 'rgba(239,68,68,0.12)', color: '#ef4444' }
                    }
                >
                    {above ? 'Above' : 'Below'}
                </span>
            </div>
        </div>
    );
}

function RsiGauge({ rsi }: { rsi: number }) {
    const state =
        rsi <= 30 ? { label: 'Oversold', color: '#ef4444' }
            : rsi >= 70 ? { label: 'Overbought', color: '#22c55e' }
                : { label: 'Neutral', color: '#888' };

    const dotLeft = `${clamp(rsi, 0, 100)}%`;

    return (
        <div className="mt-3">
            <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] uppercase tracking-widest font-mono" style={{ color: '#888' }}>
                    RSI (14)
                </span>
                <span className="text-lg font-mono font-bold" style={{ color: state.color }}>
                    {rsi.toFixed(1)}
                </span>
            </div>
            <div className="relative h-2 rounded-full overflow-hidden" style={{ background: '#252525' }}>
                {/* zones */}
                <div className="absolute inset-y-0 left-0" style={{ width: '30%', background: 'rgba(239,68,68,0.4)' }} />
                <div className="absolute inset-y-0" style={{ left: '30%', right: '30%', background: 'rgba(136,136,136,0.25)' }} />
                <div className="absolute inset-y-0 right-0" style={{ width: '30%', background: 'rgba(34,197,94,0.4)' }} />
            </div>
            <div className="relative mt-1">
                <div
                    className="absolute w-3 h-3 rounded-full -translate-x-1/2 -translate-y-0.5"
                    style={{ left: dotLeft, background: state.color, border: '2px solid #0e0e0e', top: -4 }}
                />
            </div>
            <div className="flex justify-between mt-3 text-[9px] font-mono" style={{ color: '#555' }}>
                <span>Oversold</span><span>Neutral</span><span>Overbought</span>
            </div>
            <div className="text-center text-[10px] font-mono mt-1 font-semibold uppercase tracking-widest" style={{ color: state.color }}>
                {state.label}
            </div>
        </div>
    );
}

function WeekRange({ low, high, current }: { low: number; high: number; current: number }) {
    const pct = clamp(((current - low) / (high - low)) * 100, 0, 100);
    return (
        <div className="mt-4 pt-4" style={{ borderTop: '1px solid #2a2a2a' }}>
            <div className="text-[10px] uppercase tracking-widest font-mono mb-3" style={{ color: '#888' }}>
                52-Week Range
            </div>
            <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono shrink-0" style={{ color: '#ef4444' }}>
                    ₹{low.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </span>
                <div className="flex-1 relative h-1.5 rounded-full" style={{ background: '#252525' }}>
                    <div
                        className="absolute h-full rounded-full"
                        style={{
                            width: `${pct}%`,
                            background: 'linear-gradient(to right, #ef4444, #ea923e, #22c55e)',
                        }}
                    />
                    <div
                        className="absolute w-3 h-3 rounded-full -top-[3px]"
                        style={{
                            left: `calc(${pct}% - 6px)`,
                            background: '#ea923e',
                            border: '2px solid #0e0e0e',
                        }}
                    />
                </div>
                <span className="text-[10px] font-mono shrink-0" style={{ color: '#22c55e' }}>
                    ₹{high.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </span>
            </div>
            <div className="text-center text-[10px] font-mono mt-2" style={{ color: '#888' }}>
                Current: ₹{current.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
            </div>
        </div>
    );
}

export default function TechnicalsPanel({ detail }: { detail: StockDetail }) {
    const price = detail.current_price;

    return (
        <div
            className="rounded-xl p-5"
            style={{ background: '#0e0e0e', border: '1px solid #333' }}
        >
            <div className="text-[10px] tracking-widest uppercase font-mono mb-3" style={{ color: '#888' }}>
                Technicals
            </div>

            {/* SMA indicators */}
            <SmaRow label="SMA (20)" color="#888" sma={detail.sma_20} price={price} />
            <SmaRow label="SMA (50)" color="#ea923e" sma={detail.sma_50} price={price} />
            <SmaRow label="SMA (200)" color="#6a9d9e" sma={detail.sma_200} price={price} />

            {/* RSI gauge */}
            {detail.rsi_14 != null && <RsiGauge rsi={detail.rsi_14} />}

            {/* 52W range */}
            {detail.year_low != null && detail.year_high != null && (
                <WeekRange low={detail.year_low} high={detail.year_high} current={price} />
            )}
        </div>
    );
}
