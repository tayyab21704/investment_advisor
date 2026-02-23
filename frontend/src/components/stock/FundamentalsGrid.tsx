'use client';

import type { StockDetail } from '@/lib/types';
import { formatINR, formatCr, formatPct } from '@/lib/utils';

interface Cell {
    label: string;
    value: string;
}

export default function FundamentalsGrid({ detail }: { detail: StockDetail }) {
    const cells: Cell[] = [
        { label: 'Market Cap', value: detail.market_cap_cr != null ? formatCr(detail.market_cap_cr) : '—' },
        { label: 'P/E Ratio', value: detail.pe_ratio != null ? detail.pe_ratio.toFixed(2) : '—' },
        { label: 'P/B Ratio', value: detail.pb_ratio != null ? detail.pb_ratio.toFixed(2) : '—' },
        { label: 'EPS', value: detail.eps != null ? formatINR(detail.eps) : '—' },
        { label: 'ROE', value: detail.roe != null ? formatPct(detail.roe * 100) : '—' },
        { label: 'Div. Yield', value: detail.dividend_yield != null ? formatPct(detail.dividend_yield * 100) : '—' },
        { label: 'Debt / Equity', value: detail.debt_to_equity != null ? detail.debt_to_equity.toFixed(2) : '—' },
        { label: 'Revenue', value: detail.revenue_cr != null ? formatCr(detail.revenue_cr) : '—' },
        { label: 'Net Profit', value: detail.profit_cr != null ? formatCr(detail.profit_cr) : '—' },
    ];

    return (
        <div
            className="rounded-xl p-5"
            style={{ background: '#0e0e0e', border: '1px solid #333' }}
        >
            <div className="text-[10px] tracking-widest uppercase font-mono mb-4" style={{ color: '#888' }}>
                Fundamentals
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                {cells.map(({ label, value }) => (
                    <div key={label}>
                        <div className="text-[9px] uppercase tracking-wider font-mono mb-0.5" style={{ color: '#555' }}>
                            {label}
                        </div>
                        <div className="text-sm font-mono" style={{ color: '#e5e5e5' }}>
                            {value}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
