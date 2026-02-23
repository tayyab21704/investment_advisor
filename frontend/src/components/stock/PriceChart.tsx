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
        <div className="rounded-lg px-3 py-2 text-[10px] font-mono" style={{ background: '#252525', border: '1px solid #333' }}>
            <div style={{ color: '#888', marginBottom: 4 }}>{d.ts}</div>
            {[
                ['O', d.open], ['H', d.high], ['L', d.low], ['C', d.close],
            ].map(([k, v]) => (
                <div key={String(k)} className="flex gap-2 justify-between">
                    <span style={{ color: '#555' }}>{k}</span>
                    <span style={{ color: '#e5e5e5' }}>₹{Number(v)?.toLocaleString('en-IN', { maximumFractionDigits: 2 }) ?? '—'}</span>
                </div>
            ))}
            <div className="flex gap-2 justify-between mt-1">
                <span style={{ color: '#555' }}>Vol</span>
                <span style={{ color: '#888' }}>{(d.volume / 1000).toFixed(0)}K</span>
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
    const lineColor = isPos ? '#22c55e' : '#ef4444';
    const fillId = `pf-${isPos ? 'g' : 'r'}`;

    const showSma = ['1M', '1Y', '5Y'].includes(tf);

    return (
        <div
            className="rounded-xl p-5"
            style={{ background: '#0e0e0e', border: '1px solid #333', minHeight: 380 }}
        >
            <div className="flex items-center justify-between mb-4">
                <span className="text-[10px] tracking-widest uppercase font-mono" style={{ color: '#888' }}>
                    Price Chart
                </span>
                <div className="flex gap-1">
                    {TF_LIST.map((t) => (
                        <button
                            key={t}
                            onClick={() => setTf(t)}
                            className="text-[10px] px-2.5 py-1 rounded font-mono transition-colors"
                            style={
                                tf === t
                                    ? { background: '#ea923e', color: '#0e0e0e', fontWeight: 700 }
                                    : { color: '#888' }
                            }
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            <div style={{ height: 310 }}>
                {data.length === 0 ? (
                    <div className="flex items-center justify-center h-full" style={{ color: '#555', fontSize: 12 }}>
                        No chart data
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor={lineColor} stopOpacity={0.15} />
                                    <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1f1f1f" vertical={false} />
                            <XAxis dataKey="ts" tick={{ fill: '#555', fontSize: 9, fontFamily: 'monospace' }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                            <YAxis
                                domain={[minY, maxY]}
                                tick={{ fill: '#555', fontSize: 9, fontFamily: 'monospace' }}
                                axisLine={false} tickLine={false} width={62}
                                tickFormatter={(v) => `₹${(v / 1000).toFixed(1)}K`}
                            />
                            <Tooltip content={<ChartTooltip />} />
                            {showSma && detail.sma_20 && <ReferenceLine y={detail.sma_20} stroke="#555" strokeDasharray="4 3" strokeWidth={1} label={{ value: 'SMA20', fill: '#555', fontSize: 8 }} />}
                            {showSma && detail.sma_50 && <ReferenceLine y={detail.sma_50} stroke="#ea923e" strokeDasharray="4 3" strokeWidth={1} label={{ value: 'SMA50', fill: '#ea923e', fontSize: 8 }} />}
                            {showSma && detail.sma_200 && <ReferenceLine y={detail.sma_200} stroke="#6a9d9e" strokeDasharray="4 3" strokeWidth={1} label={{ value: 'SMA200', fill: '#6a9d9e', fontSize: 8 }} />}
                            <Area type="monotone" dataKey="close" stroke={lineColor} strokeWidth={1.5} fill={`url(#${fillId})`} dot={false} activeDot={{ r: 4, fill: lineColor, stroke: '#0e0e0e', strokeWidth: 2 }} />
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
}
