'use client';

import type { StockDetail } from '@/lib/types';
import { clamp } from '@/lib/utils';

function SmaRow({
    label, color, sma, price,
}: { label: string; color: string; sma: number | null; price: number }) {
    if (sma == null) return null;
    const above = price >= sma;
    return (
        <div className="flex items-center justify-between py-2 border-b border-border-subtle">
            <span className="text-[10px] font-mono font-semibold text-text-secondary">{label}</span>
            <div className="flex items-center gap-3">
                <span className="text-[13px] font-mono font-bold" style={{ color }}>
                    ₹{sma.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                </span>
                <span
                    className={`text-[10px] px-2 py-0.5 rounded-md font-mono uppercase tracking-wider font-bold ${
                        above ? 'bg-positive-dim text-positive' : 'bg-negative-dim text-negative'
                    }`}
                >
                    {above ? 'Above' : 'Below'}
                </span>
            </div>
        </div>
    );
}

function RsiGauge({ rsi }: { rsi: number }) {
    const state =
        rsi <= 30 ? { label: 'Oversold', color: 'var(--negative)' }
            : rsi >= 70 ? { label: 'Overbought', color: 'var(--positive)' }
                : { label: 'Neutral', color: 'var(--color-text-muted)' };

    const dotLeft = `${clamp(rsi, 0, 100)}%`;

    return (
        <div className="mt-4">
            <div className="flex items-center justify-between mb-2.5">
                <span className="text-[10px] uppercase tracking-widest font-mono font-semibold text-text-secondary">
                    RSI (14)
                </span>
                <span className="text-xl font-mono font-bold" style={{ color: state.color }}>
                    {rsi.toFixed(1)}
                </span>
            </div>
            <div className="relative h-2.5 rounded-full overflow-hidden bg-bg-elevated">
                {/* zones */}
                <div className="absolute inset-y-0 left-0 w-[30%] bg-negative/40" />
                <div className="absolute inset-y-0 left-[30%] right-[30%] bg-text-muted/20" />
                <div className="absolute inset-y-0 right-0 w-[30%] bg-positive/40" />
            </div>
            <div className="relative mt-1">
                <div
                    className="absolute w-4 h-4 rounded-full -translate-x-1/2 -translate-y-0.5"
                    style={{ left: dotLeft, background: state.color, border: '3px solid var(--color-bg-surface)', top: -6 }}
                />
            </div>
            <div className="flex justify-between mt-3.5 text-[10px] font-mono font-bold text-text-muted">
                <span>Oversold</span><span>Neutral</span><span>Overbought</span>
            </div>
            <div className="text-center text-[11px] font-mono mt-2 font-bold uppercase tracking-widest" style={{ color: state.color }}>
                {state.label}
            </div>
        </div>
    );
}

function WeekRange({ low, high, current }: { low: number; high: number; current: number }) {
    const pct = clamp(((current - low) / (high - low)) * 100, 0, 100);
    return (
        <div className="mt-5 pt-5 border-t border-border-subtle">
            <div className="text-[10px] uppercase tracking-widest font-mono font-semibold mb-4 text-text-secondary">
                52-Week Range
            </div>
            <div className="flex items-center gap-3">
                <span className="text-[11px] font-mono font-bold shrink-0 text-negative">
                    ₹{low.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </span>
                <div className="flex-1 relative h-2 rounded-full bg-bg-elevated">
                    <div
                        className="absolute h-full rounded-full"
                        style={{
                            width: `${pct}%`,
                            background: 'linear-gradient(to right, var(--negative), var(--primary), var(--positive))',
                        }}
                    />
                    <div
                        className="absolute w-4 h-4 rounded-full -top-[4px]"
                        style={{
                            left: `calc(${pct}% - 8px)`,
                            background: 'var(--primary)',
                            border: '3px solid var(--color-bg-surface)',
                        }}
                    />
                </div>
                <span className="text-[11px] font-mono font-bold shrink-0 text-positive">
                    ₹{high.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </span>
            </div>
            <div className="text-center text-[11px] font-mono font-semibold mt-3 text-text-secondary">
                Current: ₹{current.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
            </div>
        </div>
    );
}

export default function TechnicalsPanel({ detail }: { detail: StockDetail }) {
    const price = detail.current_price;

    return (
        <div
            className="rounded-2xl p-6 bg-bg-surface border border-border-subtle shadow-xl"
        >
            <div className="text-[11px] font-semibold tracking-widest uppercase font-mono mb-4 text-text-secondary">
                Technicals
            </div>

            {/* SMA indicators */}
            <SmaRow label="SMA (20)" color="var(--color-text-muted)" sma={detail.sma_20} price={price} />
            <SmaRow label="SMA (50)" color="var(--primary)" sma={detail.sma_50} price={price} />
            <SmaRow label="SMA (200)" color="var(--blue)" sma={detail.sma_200} price={price} />

            {/* RSI gauge */}
            {detail.rsi_14 != null && <RsiGauge rsi={detail.rsi_14} />}

            {/* 52W range */}
            {detail.year_low != null && detail.year_high != null && (
                <WeekRange low={detail.year_low} high={detail.year_high} current={price} />
            )}
        </div>
    );
}
