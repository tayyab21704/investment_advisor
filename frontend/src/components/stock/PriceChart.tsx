'use client';

import { useState } from 'react';
import {
    AreaChart, Area, XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid, ReferenceLine,
} from 'recharts';
import type { ChartCandle, StockDetail } from '@/lib/types';
import { formatDate } from '@/lib/utils';

type TF = '1D' | '1W' | '1M' | '1Y' | '5Y';
const TF_LIST: TF[] = ['1D', '1W', '1M', '1Y', '5Y'];
const TF_KEY: Record<TF, keyof Pick<StockDetail, 'chart_1d' | 'chart_1w' | 'chart_1m' | 'chart_1y' | 'chart_5y'>> = {
    '1D': 'chart_1d', '1W': 'chart_1w', '1M': 'chart_1m', '1Y': 'chart_1y', '5Y': 'chart_5y',
};

function ChartTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: { ts: string; open: number; high: number; low: number; close: number; volume: number } }> }) {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
        <div className="rounded-xl px-4 py-3 text-xs font-mono bg-bg-overlay border border-border-default shadow-2xl backdrop-blur-md">
            <div className="text-text-muted mb-2 font-semibold">{d.ts}</div>
            {[
                ['O', d.open], ['H', d.high], ['L', d.low], ['C', d.close],
            ].map(([k, v]) => (
                <div key={String(k)} className="flex gap-4 justify-between mb-0.5">
                    <span className="text-text-secondary font-semibold">{k}</span>
                    <span className="text-text-primary font-bold">₹{Number(v)?.toLocaleString('en-IN', { maximumFractionDigits: 2 }) ?? '—'}</span>
                </div>
            ))}
            <div className="flex gap-4 justify-between mt-2 pt-2 border-t border-border-subtle">
                <span className="text-text-secondary font-semibold">Vol</span>
                <span className="text-text-muted font-bold">{(d.volume / 1000).toFixed(0)}K</span>
            </div>
        </div>
    );
}

export default function PriceChart({ detail }: { detail: StockDetail }) {
    const [tf, setTf] = useState<TF>('1M');

    const raw: ChartCandle[] = detail[TF_KEY[tf]] ?? [];
    const data = raw.filter((c) => c.close != null).map((c) => ({
        ts: formatDate(c.timestamp, tf === '5Y'),
        open: c.open ?? 0,
        high: c.high ?? 0,
        low: c.low ?? 0,
        close: c.close as number,
        volume: c.volume,
    }));

    const closes = data.map((d) => d.close);
    const minY = closes.length ? Math.min(...closes) * 0.997 : 0;
    const maxY = closes.length ? Math.max(...closes) * 1.003 : 1;
    const isPos = data.length >= 2 ? data[data.length - 1].close >= data[0].close : detail.change_pct >= 0;
    const lineColor = isPos ? 'var(--positive)' : 'var(--negative)';
    const fillId = `pf-${isPos ? 'g' : 'r'}`;

    const showSma = ['1M', '1Y', '5Y'].includes(tf);

    return (
        <div
            className="rounded-2xl p-6 bg-bg-surface border border-border-subtle shadow-xl"
            style={{ minHeight: 380 }}
        >
            <div className="flex items-center justify-between mb-5">
                <span className="text-[11px] font-semibold tracking-widest uppercase font-mono text-text-secondary">
                    Price Chart
                </span>
                <div className="flex gap-1.5 bg-bg-elevated p-1 rounded-lg border border-border-subtle">
                    {TF_LIST.map((t) => (
                        <button
                            key={t}
                            onClick={() => setTf(t)}
                            className={`text-[11px] px-3 py-1.5 rounded-md font-mono transition-colors font-semibold ${
                                tf === t
                                    ? 'bg-bg-overlay text-text-primary shadow-sm border border-border-default'
                                    : 'text-text-muted hover:text-text-secondary hover:bg-bg-base'
                            }`}
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            <div style={{ height: 310 }}>
                {data.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-text-muted text-xs">
                        No chart data
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor={lineColor} stopOpacity={0.25} />
                                    <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" vertical={false} />
                            <XAxis dataKey="ts" tick={{ fill: 'var(--color-text-muted)', fontSize: 10, fontFamily: 'monospace' }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                            <YAxis
                                domain={[minY, maxY]}
                                tick={{ fill: 'var(--color-text-muted)', fontSize: 10, fontFamily: 'monospace' }}
                                axisLine={false} tickLine={false} width={62}
                                tickFormatter={(v) => `₹${(v / 1000).toFixed(1)}K`}
                            />
                            <Tooltip content={<ChartTooltip />} />
                            {showSma && detail.sma_20 && <ReferenceLine y={detail.sma_20} stroke="var(--color-text-muted)" strokeDasharray="4 3" strokeWidth={1} label={{ value: 'SMA20', fill: 'var(--color-text-muted)', fontSize: 9 }} />}
                            {showSma && detail.sma_50 && <ReferenceLine y={detail.sma_50} stroke="var(--primary)" strokeDasharray="4 3" strokeWidth={1} label={{ value: 'SMA50', fill: 'var(--primary)', fontSize: 9 }} />}
                            {showSma && detail.sma_200 && <ReferenceLine y={detail.sma_200} stroke="var(--blue)" strokeDasharray="4 3" strokeWidth={1} label={{ value: 'SMA200', fill: 'var(--blue)', fontSize: 9 }} />}
                            <Area type="monotone" dataKey="close" stroke={lineColor} strokeWidth={2} fill={`url(#${fillId})`} dot={false} activeDot={{ r: 5, fill: lineColor, stroke: 'var(--color-bg-surface)', strokeWidth: 2 }} />
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
}
