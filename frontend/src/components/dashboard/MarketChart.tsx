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
            className="rounded-lg px-3 py-2 text-[11px] font-mono"
            style={{ background: '#252525', border: '1px solid #333' }}
        >
            <div style={{ color: '#888' }}>{d.ts}</div>
            <div style={{ color: '#e5e5e5', fontSize: 13, fontWeight: 700 }}>
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
    const lineColor = isPos ? '#22c55e' : '#ef4444';
    const fillId = `area-fill-${isPos ? 'g' : 'r'}`;

    // SMA reference lines for M/Y/5Y
    const showSma = ['1M', '1Y', '5Y'].includes(tf) && detail;

    return (
        <div
            className="rounded-xl p-5 flex flex-col"
            style={{ background: '#0e0e0e', border: '1px solid #333', minHeight: 420 }}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <div className="text-sm font-bold uppercase tracking-tight" style={{ color: '#e5e5e5' }}>
                        {label} Trend
                    </div>
                    <div className="text-[10px] font-mono" style={{ color: '#888' }}>
                        Live Market Analysis
                    </div>
                </div>
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

            {/* Chart */}
            <div className="flex-1" style={{ minHeight: 280 }}>
                {loading ? (
                    <div className="skeleton h-full w-full rounded-lg" />
                ) : data.length === 0 ? (
                    <div className="flex items-center justify-center h-full" style={{ color: '#555' }}>
                        No data available
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor={lineColor} stopOpacity={0.18} />
                                    <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1f1f1f" vertical={false} />
                            <XAxis
                                dataKey="ts"
                                tick={{ fill: '#555', fontSize: 9, fontFamily: 'monospace' }}
                                axisLine={false}
                                tickLine={false}
                                interval="preserveStartEnd"
                            />
                            <YAxis
                                domain={[minY, maxY]}
                                tick={{ fill: '#555', fontSize: 9, fontFamily: 'monospace' }}
                                axisLine={false}
                                tickLine={false}
                                width={60}
                                tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}K`}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            {showSma && detail?.sma_20 && (
                                <ReferenceLine y={detail.sma_20} stroke="#555" strokeDasharray="4 3" strokeWidth={1} label={{ value: 'SMA20', fill: '#555', fontSize: 9 }} />
                            )}
                            {showSma && detail?.sma_50 && (
                                <ReferenceLine y={detail.sma_50} stroke="#ea923e" strokeDasharray="4 3" strokeWidth={1} label={{ value: 'SMA50', fill: '#ea923e', fontSize: 9 }} />
                            )}
                            {showSma && detail?.sma_200 && (
                                <ReferenceLine y={detail.sma_200} stroke="#6a9d9e" strokeDasharray="4 3" strokeWidth={1} label={{ value: 'SMA200', fill: '#6a9d9e', fontSize: 9 }} />
                            )}
                            <Area
                                type="monotone"
                                dataKey="close"
                                stroke={lineColor}
                                strokeWidth={1.5}
                                fill={`url(#${fillId})`}
                                dot={false}
                                activeDot={{ r: 4, fill: lineColor, stroke: '#0e0e0e', strokeWidth: 2 }}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </div>

            {/* Stat strip */}
            {detail && (
                <div
                    className="grid grid-cols-4 mt-4 pt-3 gap-2"
                    style={{ borderTop: '1px solid #2a2a2a' }}
                >
                    {[
                        { label: 'Day High', value: detail.day_high },
                        { label: 'Day Low', value: detail.day_low },
                        { label: '52W High', value: detail.year_high },
                        { label: '52W Low', value: detail.year_low },
                    ].map(({ label, value }) => (
                        <div key={label}>
                            <div className="text-[9px] uppercase tracking-wider font-mono mb-0.5" style={{ color: '#555' }}>
                                {label}
                            </div>
                            <div className="text-xs font-mono" style={{ color: '#e5e5e5' }}>
                                {value != null ? `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : '—'}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
