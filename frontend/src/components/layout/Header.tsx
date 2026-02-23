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

    const navItems = [
        { label: 'Dashboard', href: '/' },
        { label: 'Council Room', href: '/council' },
        { label: 'Portfolio', href: '/portfolio' },
        { label: 'Settings', href: '/settings' },
    ];

    return (
        <header
            className="sticky top-0 z-50 h-14 flex items-center px-4 gap-4"
            style={{
                background: '#0e0e0e',
                borderBottom: '1px solid #333',
                backdropFilter: 'blur(12px)',
            }}
        >
            {/* ── Brand ─────────────────────────────────────────────── */}
            <div className="flex items-center gap-3 shrink-0">
                <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center"
                    style={{ background: '#ea923e' }}
                >
                    <BarChart2 size={16} color="#0e0e0e" strokeWidth={2.5} />
                </div>
                <div className="flex flex-col leading-none">
                    <span
                        className="text-xs font-bold tracking-widest uppercase"
                        style={{ color: '#e5e5e5', fontFamily: 'var(--font-display)' }}
                    >
                        Investment Council
                    </span>
                    <span
                        className="text-[10px] flex items-center gap-1.5 mt-0.5"
                        style={{ color: '#888' }}
                    >
                        <span
                            className="live-dot w-1.5 h-1.5 rounded-full"
                            style={{ background: '#22c55e', display: 'inline-block' }}
                        />
                        System Online
                    </span>
                </div>
                <span className="text-[#333] mx-1 select-none">|</span>
                <span className="font-mono text-xs" style={{ color: '#888' }}>{istTime} IST</span>
            </div>

            {/* ── Search ────────────────────────────────────────────── */}
            <div className="relative flex-1 max-w-sm mx-auto">
                <div
                    className="flex items-center gap-2 px-3 h-9 rounded-lg"
                    style={{ background: '#0e0e0e', border: '1px solid #333' }}
                >
                    <Search size={14} color="#888" />
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => handleSearch(e.target.value)}
                        onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
                        onFocus={() => results.length > 0 && setShowDropdown(true)}
                        onKeyDown={(e) => e.key === 'Escape' && setShowDropdown(false)}
                        placeholder="Search stocks, indices..."
                        className="flex-1 bg-transparent outline-none text-xs"
                        style={{ color: '#e5e5e5', fontFamily: 'var(--font-display)' }}
                    />
                    <span className="text-[10px] px-1 py-0.5 rounded" style={{ color: '#555', background: '#1a1a1a', border: '1px solid #333' }}>
                        ⌘K
                    </span>
                </div>

                {showDropdown && results.length > 0 && (
                    <div
                        className="absolute top-10 left-0 right-0 rounded-lg overflow-hidden shadow-xl z-50"
                        style={{ background: '#0e0e0e', border: '1px solid #333' }}
                    >
                        {results.map((r) => (
                            <button
                                key={r.symbol}
                                onMouseDown={() => {
                                    setShowDropdown(false);
                                    setQuery('');
                                    router.push(`/stock/${r.symbol}`);
                                }}
                                className="w-full flex items-center justify-between px-3 py-2 hover:bg-[#252525] transition-colors"
                            >
                                <div className="flex flex-col items-start">
                                    <span className="text-xs font-mono font-bold" style={{ color: '#e5e5e5' }}>
                                        {r.symbol}
                                    </span>
                                    <span className="text-[10px]" style={{ color: '#888' }}>{r.name}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    {r.sector && (
                                        <span
                                            className="text-[9px] px-1.5 py-0.5 rounded-full"
                                            style={{ color: '#6a9d9e', background: 'rgba(106,157,158,0.12)', border: '1px solid rgba(106,157,158,0.2)' }}
                                        >
                                            {r.sector}
                                        </span>
                                    )}
                                    {r.change_pct != null && (
                                        <span
                                            className="text-[10px] font-mono"
                                            style={{ color: r.change_pct >= 0 ? '#22c55e' : '#ef4444' }}
                                        >
                                            {r.change_pct >= 0 ? '+' : ''}{r.change_pct.toFixed(2)}%
                                        </span>
                                    )}
                                </div>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* ── Nav ───────────────────────────────────────────────── */}
            <nav className="hidden md:flex items-center gap-5 shrink-0">
                {navItems.map(({ label, href }) => (
                    <Link
                        key={href}
                        href={href}
                        className="text-xs transition-colors"
                        style={{ color: pathname === href ? '#e5e5e5' : '#888' }}
                    >
                        {label}
                    </Link>
                ))}
            </nav>

            {/* ── Right ─────────────────────────────────────────────── */}
            <div className="flex items-center gap-3 shrink-0 ml-auto md:ml-0">
                <button className="relative p-1.5 rounded-lg hover:bg-[#252525] transition-colors">
                    <Bell size={16} color="#888" />
                    <span
                        className="live-dot absolute top-1 right-1 w-1.5 h-1.5 rounded-full"
                        style={{ background: '#ea923e' }}
                    />
                </button>
                <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-bold"
                    style={{ background: '#252525', color: '#ea923e', border: '1px solid #333' }}
                >
                    IC
                </div>
            </div>
        </header>
    );
}
