'use client';

import { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, CartesianGrid } from 'recharts';
import { fetchChartData, fetchStockDetail } from '@/lib/api';
import type { ChartCandle, StockDetail, ChartResponse } from '@/lib/types';
import { formatDate } from '@/lib/utils';

type Timeframe = '1D' | '1W' | '1M' | '1Y' | '5Y';
const TF_LIST: Timeframe[] = ['1D', '1W', '1M', '1Y', '5Y'];
// Mapping for detail access if available
const TF_MAP_DETAIL: Record<Timeframe, keyof Pick<StockDetail, 'chart_1d' | 'chart_1w' | 'chart_1m' | 'chart_1y' | 'chart_5y'>> = {
    '1D': 'chart_1d',
    '1W': 'chart_1w',
    '1M': 'chart_1m',
    '1Y': 'chart_1y',
    '5Y': 'chart_5y',
};

interface CustomTooltipProps {
    active?: boolean;
    payload?: Array<{ value: number; payload: { ts: string; close: number } }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
        <div
            className="rounded-xl px-4 py-3 text-xs font-mono bg-bg-overlay border border-border-default shadow-2xl backdrop-blur-md"
        >
            <div className="text-text-muted mb-1">{d.ts}</div>
            <div className="text-text-primary font-bold text-sm">
                ₹{d.close?.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
            </div>
        </div>
    );
}

export default function MarketChart({ symbol = '^NSEI', label = 'NIFTY 50' }: { symbol?: string; label?: string }) {
    const [candles, setCandles] = useState<ChartCandle[]>([]);
    const [detail, setDetail] = useState<StockDetail | null>(null);
    const [tf, setTf] = useState<Timeframe>('1M');
    const [loading, setLoading] = useState(true);

    // Fetch chart data - lazy-loaded by tf and symbol
    useEffect(() => {
        setLoading(true);
        fetchChartData(symbol, tf).then((res) => {
            if (res) setCandles(res.candles);
            setLoading(false);
        });
    }, [symbol, tf]);

    // Fetch detail in background for SMAs and footer stats
    useEffect(() => {
        fetchStockDetail(symbol).then(setDetail);
    }, [symbol]);

    const data = (candles || [])
        .filter((c) => c.close != null)
        .map((c) => ({
            ts: formatDate(c.timestamp, tf === '5Y'),
            close: c.close as number,
        }));

    const closes = data.map((d) => d.close);
    const minY = closes.length ? Math.min(...closes) * 0.998 : 0;
    const maxY = closes.length ? Math.max(...closes) * 1.002 : 1;
    const isPos = data.length >= 2 ? data[data.length - 1].close >= data[0].close : true;
    const lineColor = isPos ? 'var(--positive)' : 'var(--negative)';
    const fillId = `area-fill-${isPos ? 'g' : 'r'}`;

    // SMA reference lines for M/Y/5Y
    const showSma = ['1M', '1Y', '5Y'].includes(tf) && detail;

    return (
        <div
            className="rounded-2xl p-6 flex flex-col bg-bg-surface border border-border-subtle shadow-xl"
            style={{ minHeight: 420 }}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-5">
                <div>
                    <div className="text-sm font-bold uppercase tracking-tight text-text-primary">
                        {label} Trend
                    </div>
                    <div className="text-[11px] font-mono text-text-secondary mt-0.5">
                        Live Market Analysis
                    </div>
                </div>
                <div className="flex gap-1.5 bg-bg-elevated p-1 rounded-lg border border-border-subtle">
                    {TF_LIST.map((t) => (
                        <button
                            key={t}
                            onClick={() => setTf(t)}
                            className="text-[11px] px-3 py-1 rounded-md font-mono transition-colors"
                            style={
                                tf === t
                                    ? { background: 'var(--primary)', color: 'var(--color-text-inverse)', fontWeight: 700 }
                                    : { color: 'var(--color-text-secondary)' }
                            }
                        >
                            {t}
                        </button>
                    ))}
                </div>
            </div>

            {/* Chart */}
            <div className="flex-1" style={{ minHeight: 280 }}>
                {loading ? (
                    <div className="skeleton h-full w-full rounded-lg" />
                ) : data.length === 0 ? (
                    <div className="flex items-center justify-center h-full text-text-muted">
                        No data available
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
                            <XAxis
                                dataKey="ts"
                                tick={{ fill: 'var(--color-text-muted)', fontSize: 10, fontFamily: 'monospace' }}
                                axisLine={false}
                                tickLine={false}
                                interval="preserveStartEnd"
                            />
                            <YAxis
                                domain={[minY, maxY]}
                                tick={{ fill: 'var(--color-text-muted)', fontSize: 10, fontFamily: 'monospace' }}
                                axisLine={false}
                                tickLine={false}
                                width={60}
                                tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}K`}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            {showSma && detail?.sma_20 && (
                                <ReferenceLine y={detail.sma_20} stroke="var(--color-text-muted)" strokeDasharray="4 3" strokeWidth={1} label={{ value: 'SMA20', fill: 'var(--color-text-muted)', fontSize: 9 }} />
                            )}
                            {showSma && detail?.sma_50 && (
                                <ReferenceLine y={detail.sma_50} stroke="var(--primary)" strokeDasharray="4 3" strokeWidth={1} label={{ value: 'SMA50', fill: 'var(--primary)', fontSize: 9 }} />
                            )}
                            {showSma && detail?.sma_200 && (
                                <ReferenceLine y={detail.sma_200} stroke="var(--blue)" strokeDasharray="4 3" strokeWidth={1} label={{ value: 'SMA200', fill: 'var(--blue)', fontSize: 9 }} />
                            )}
                            <Area
                                type="monotone"
                                dataKey="close"
                                stroke={lineColor}
                                strokeWidth={2}
                                fill={`url(#${fillId})`}
                                dot={false}
                                activeDot={{ r: 5, fill: lineColor, stroke: 'var(--color-bg-surface)', strokeWidth: 2 }}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </div>

            {/* Stat strip */}
            {detail && (
                <div
                    className="grid grid-cols-4 mt-5 pt-4 gap-3 border-t border-border-default"
                >
                    {[
                        { label: 'Day High', value: detail.day_high },
                        { label: 'Day Low', value: detail.day_low },
                        { label: '52W High', value: detail.year_high },
                        { label: '52W Low', value: detail.year_low },
                    ].map(({ label, value }) => (
                        <div key={label} className="bg-bg-elevated p-2 rounded-lg border border-border-subtle hover:border-border-accent transition-colors">
                            <div className="text-[10px] uppercase tracking-wider font-semibold text-text-secondary mb-1">
                                {label}
                            </div>
                            <div className="text-sm font-bold text-text-primary">
                                {value != null ? `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : '—'}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
