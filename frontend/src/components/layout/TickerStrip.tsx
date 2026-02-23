'use client';

import { useEffect, useState } from 'react';
import { fetchMarketIndices, fetchMarketStatus } from '@/lib/api';
import type { IndexDetail, MarketStatus } from '@/lib/types';

export default function TickerStrip() {
    const [indices, setIndices] = useState<IndexDetail[]>([]);
    const [status, setStatus] = useState<MarketStatus | null>(null);

    useEffect(() => {
        fetchMarketIndices().then(setIndices);
        fetchMarketStatus().then(setStatus);
    }, []);

    // Build ticker items — duplicate for seamless loop
    const items = [...indices, ...indices];

    return (
        <div
            className="relative flex items-center h-9 overflow-hidden"
            style={{
                background: '#0e0e0e',
                borderBottom: '1px solid #333',
            }}
        >
            {/* ── Scrolling strip ───────────────────────────────────── */}
            <div className="flex-1 overflow-hidden">
                {items.length > 0 ? (
                    <div className="animate-marquee whitespace-nowrap">
                        {items.map((idx, i) => {
                            const isPos = idx.change_pct >= 0;
                            return (
                                <span
                                    key={`${idx.symbol}-${i}`}
                                    className="inline-flex items-center gap-2 px-6 text-[11px]"
                                >
                                    <span
                                        className="font-mono font-bold tracking-wide"
                                        style={{ color: '#e5e5e5' }}
                                    >
                                        {idx.name ?? idx.symbol}
                                    </span>
                                    <span className="font-mono" style={{ color: '#e5e5e5' }}>
                                        {idx.current_price?.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                                    </span>
                                    <span
                                        className="font-mono"
                                        style={{ color: isPos ? '#22c55e' : '#ef4444' }}
                                    >
                                        {isPos ? '+' : ''}{idx.change_pct?.toFixed(2)}%
                                    </span>
                                    <span style={{ color: '#333' }}>·</span>
                                </span>
                            );
                        })}
                    </div>
                ) : (
                    /* Loading skeleton - static names */
                    <div className="flex items-center gap-10 px-4 animate-pulse">
                        {['NIFTY 50', 'SENSEX', 'BANK NIFTY', 'NIFTY IT'].map(name => (
                            <span key={name} className="text-[#555] text-xs font-mono">{name} ---</span>
                        ))}
                    </div>
                )}
            </div>

            {/* ── Market status badge (fixed right) ─────────────────── */}
            <div className="shrink-0 px-4 border-l border-[#333]">
                {status ? (
                    <span
                        className="inline-flex items-center gap-1.5 text-[10px] font-mono font-semibold tracking-widest uppercase px-2.5 py-1 rounded-full"
                        style={
                            status.is_open
                                ? {
                                    background: 'rgba(34,197,94,0.1)',
                                    color: '#22c55e',
                                    border: '1px solid rgba(34,197,94,0.2)',
                                }
                                : {
                                    background: 'rgba(136,136,136,0.1)',
                                    color: '#888',
                                    border: '1px solid #333',
                                }
                        }
                    >
                        {status.is_open && (
                            <span className="live-dot w-1.5 h-1.5 rounded-full bg-[#22c55e] inline-block" />
                        )}
                        {status.is_open ? 'Market Open' : 'Market Closed'}
                    </span>
                ) : (
                    <div className="skeleton h-5 w-24 rounded-full" />
                )}
            </div>
        </div>
    );
}
