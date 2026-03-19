'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Search, Bell, BarChart2 } from 'lucide-react';
import { searchStocks, fetchMarketStatus } from '@/lib/api';
import type { SearchResult, MarketStatus } from '@/lib/types';

let debounceTimer: ReturnType<typeof setTimeout>;

export default function Header() {
    const pathname = usePathname();
    const router = useRouter();
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<SearchResult[]>([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [istTime, setIstTime] = useState('');
    const [status, setStatus] = useState<MarketStatus | null>(null);

    /* ── IST clock ─────────────────────────────────────────────── */
    useEffect(() => {
        const tick = () => {
            const now = new Date();
            setIstTime(
                now.toLocaleTimeString('en-IN', {
                    hour: '2-digit', minute: '2-digit', second: '2-digit',
                    hour12: false, timeZone: 'Asia/Kolkata',
                })
            );
        };
        tick();
        const id = setInterval(tick, 1000);
        return () => clearInterval(id);
    }, []);

    /* ── Market status ─────────────────────────────────────────── */
    useEffect(() => {
        fetchMarketStatus().then(setStatus);
    }, []);

    /* ── Debounced search ─────────────────────────────────────── */
    const handleSearch = (val: string) => {
        setQuery(val);
        clearTimeout(debounceTimer);
        if (!val.trim()) { setResults([]); setShowDropdown(false); return; }
        debounceTimer = setTimeout(async () => {
            const res = await searchStocks(val);
            setResults(res.results);
            setShowDropdown(true);
        }, 300);
    };

    const pageTitle = pathname === '/' ? 'Dashboard' :
                      pathname.startsWith('/council') ? 'Council Room' :
                      pathname.startsWith('/portfolio') ? 'Portfolio' :
                      pathname.startsWith('/settings') ? 'Settings' : 'Detail';

    return (
        <header className="sticky top-0 z-40 h-16 flex items-center px-8 gap-6 bg-bg-base/80 backdrop-blur-md border-b border-border-subtle">
            {/* ── Page Title ─────────────────────────────────────────────── */}
            <div className="flex items-center gap-3 shrink-0">
                <span className="text-sm font-semibold text-text-primary tracking-wide">Investment Council</span>
                <span className="text-border-default">|</span>
                <span className="text-sm text-text-secondary">{pageTitle}</span>
            </div>

            <div className="flex-1 flex justify-end items-center gap-6">
                {/* ── Search ────────────────────────────────────────────── */}
                <div className="relative w-full max-w-sm">
                    <div className="flex items-center gap-2 px-4 h-10 rounded-xl bg-bg-surface border border-border-subtle focus-within:border-border-accent transition-colors">
                        <Search size={16} className="text-text-muted" />
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => handleSearch(e.target.value)}
                            onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
                            onFocus={() => results.length > 0 && setShowDropdown(true)}
                            onKeyDown={(e) => e.key === 'Escape' && setShowDropdown(false)}
                            placeholder="Search stocks, indices..."
                            className="flex-1 bg-transparent outline-none text-sm text-text-primary placeholder:text-text-muted font-body"
                        />
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-bg-elevated text-text-secondary border border-border-default font-mono">
                            ⌘K
                        </span>
                    </div>

                    {showDropdown && results.length > 0 && (
                        <div className="absolute top-12 left-0 right-0 rounded-xl overflow-hidden shadow-2xl z-50 bg-bg-elevated border border-border-subtle">
                            {results.map((r) => (
                                <button
                                    key={r.symbol}
                                    onMouseDown={() => {
                                        setShowDropdown(false);
                                        setQuery('');
                                        router.push(`/stock/${r.symbol}`);
                                    }}
                                    className="w-full flex items-center justify-between px-4 py-3 hover:bg-bg-overlay transition-colors border-b border-border-subtle last:border-0"
                                >
                                    <div className="flex flex-col items-start">
                                        <span className="text-sm font-mono font-bold text-text-primary">
                                            {r.symbol}
                                        </span>
                                        <span className="text-xs text-text-secondary">{r.name}</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {r.sector && (
                                            <span className="text-[10px] px-2 py-0.5 rounded-full text-blue bg-blue-dim border border-blue/20">
                                                {r.sector}
                                            </span>
                                        )}
                                        {r.change_pct != null && (
                                            <span className={`text-xs font-mono ${r.change_pct >= 0 ? 'text-positive' : 'text-negative'}`}>
                                                {r.change_pct >= 0 ? '+' : ''}{r.change_pct.toFixed(2)}%
                                            </span>
                                        )}
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* ── Right Actions ─────────────────────────────────────────────── */}
                <div className="flex items-center gap-4 shrink-0">
                    <div className="text-xs font-mono text-text-secondary flex items-center gap-2 hidden md:flex">
                        <span className="live-dot w-1.5 h-1.5 rounded-full bg-positive inline-block" />
                        {istTime} IST
                    </div>
                    <button className="relative p-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-bg-surface transition-colors">
                        <Bell size={20} />
                        <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-pink animate-pulse" />
                    </button>
                    <div className="w-9 h-9 rounded-full bg-bg-surface flex items-center justify-center text-xs font-bold text-primary border border-border-default md:hidden">
                        IC
                    </div>
                </div>
            </div>
        </header>
    );
}
