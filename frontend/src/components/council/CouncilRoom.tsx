'use client';

import { useState, useRef, useEffect } from 'react';
import {
    Search, Shield, BarChart2, Brain, Users, ChevronRight,
} from 'lucide-react';
import { runCouncilAnalysis } from '@/lib/api';
import type { CouncilReport, CouncilProfile, PortfolioItem } from '@/lib/types';
import { formatPct } from '@/lib/utils';

// ─── Data ─────────────────────────────────────────────────────────────────────
const AGENTS = [
    { id: 'scout', name: 'Scout Agent', tag: '[SCOUT]', icon: Search, color: '#ea923e', bg: 'rgba(234,146,62,0.12)', status: 'Scanning Markets', activity: 'Analyzing volume patterns across NIFTY 100. Detecting breakout candidates in mid-cap space.' },
    { id: 'risk', name: 'Risk Auditor', tag: '[RISK]', icon: Shield, color: '#ef4444', bg: 'rgba(239,68,68,0.1)', status: 'Evaluating Risk', activity: 'Running VaR simulation on portfolio candidates. Cross-checking correlation matrix.' },
    { id: 'analyst', name: 'Analyst Agent', tag: '[ANALYST]', icon: BarChart2, color: '#6a9d9e', bg: 'rgba(106,157,158,0.1)', status: 'Processing Data', activity: 'Fetching macro indicators. Comparing P/E ratios against 5-year sector averages.' },
    { id: 'orchestrator', name: 'Orchestrator', tag: '[ORCHESTRATOR]', icon: Brain, color: '#e5e5e5', bg: 'rgba(229,229,229,0.08)', status: 'Awaiting Inputs', activity: 'Monitoring agent outputs. Will finalize verdict when consensus threshold is reached.' },
];

const BOOT_LINES = [
    '// COUNCIL PROTOCOL v4.2.1 INITIALIZED',
    '// CONNECTED TO NSE DATA STREAM [wss://feed.nse.india/v2]',
    '// LOADING AGENT WEIGHTS... DONE',
];

const MEMORY = [
    { date: '21 Feb 2026', verdict: 'COUNCIL APPROVED', top: 'HDFCBANK (12% alloc)' },
    { date: '15 Feb 2026', verdict: 'DEBATE — REVISED', top: 'RELIANCE (18% alloc)' },
    { date: '08 Feb 2026', verdict: 'COUNCIL APPROVED', top: 'TCS (15% alloc)' },
];

type Tab = 'convene' | 'logs' | 'debate' | 'memory';

interface LogLine {
    ts: string;
    tag: string;
    color: string;
    msg: string;
}

// ─── Conviction Gauge (SVG semicircle) ───────────────────────────────────────
function ConvictionGauge({ pct }: { pct: number }) {
    const r = 52, cx = 64, cy = 64;
    const circ = Math.PI * r;
    const fill = ((pct / 100) * circ);

    return (
        <div className="flex flex-col items-center py-4">
            <div className="text-[10px] uppercase tracking-widest font-mono mb-2" style={{ color: '#888' }}>
                Conviction
            </div>
            <svg width={128} height={72} viewBox="0 0 128 72">
                {/* track */}
                <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`} fill="none" stroke="#252525" strokeWidth="10" strokeLinecap="round" />
                {/* fill */}
                <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`} fill="none" stroke="#ea923e" strokeWidth="10" strokeLinecap="round"
                    strokeDasharray={`${fill} ${circ}`} />
                <text x={cx} y={cy - 6} textAnchor="middle" fill="#e5e5e5" fontSize="18" fontWeight="700" fontFamily="monospace">
                    {pct}%
                </text>
            </svg>
        </div>
    );
}

// ─── Main Component ────────────────────────────────────────────────────────────
export default function CouncilRoom() {
    const [tab, setTab] = useState<Tab>('convene');
    const [running, setRunning] = useState(false);
    const [report, setReport] = useState<CouncilReport | null>(null);
    const [logs, setLogs] = useState<LogLine[]>([]);
    const logRef = useRef<HTMLDivElement>(null);

    // Form state
    const [riskAppetite, setRiskAppetite] = useState<'Conservative' | 'Moderate' | 'Aggressive'>('Moderate');
    const [surplus, setSurplus] = useState('25000');
    const [horizon, setHorizon] = useState('12');
    const [caps, setCaps] = useState({ large: true, mid: true, small: false });

    const addLog = (tag: string, color: string, msg: string) => {
        const ts = new Date().toLocaleTimeString('en-IN', { hour12: false, timeZone: 'Asia/Kolkata' });
        setLogs((prev) => [...prev, { ts, tag, color, msg }]);
        setTimeout(() => logRef.current?.scrollTo({ top: 99999, behavior: 'smooth' }), 50);
    };

    const handleConvene = async () => {
        setRunning(true);
        setTab('logs');
        setLogs([]);

        const profile: CouncilProfile = {
            risk_appetite: riskAppetite,
            actual_risk_capacity: riskAppetite === 'Conservative' ? 3 : riskAppetite === 'Moderate' ? 6 : 9,
            monthly_surplus: parseInt(surplus),
        };

        addLog('[ORCHESTRATOR]', '#e5e5e5', 'Council session initiated. Loading agent modules...');
        await new Promise(r => setTimeout(r, 800));
        addLog('[SCOUT]', '#ea923e', `Scanning markets for ${riskAppetite.toLowerCase()} portfolio opportunities...`);
        await new Promise(r => setTimeout(r, 600));
        addLog('[ANALYST]', '#6a9d9e', 'Fetching fundamental data. Computing relative strength...');
        await new Promise(r => setTimeout(r, 500));
        addLog('[RISK]', '#ef4444', 'Initializing VaR model. Checking correlation matrix...');

        const result = await runCouncilAnalysis(profile);

        if (result) {
            await new Promise(r => setTimeout(r, 400));
            addLog('[SCOUT]', '#ea923e', `Scout report ready. ${result.portfolio.length} candidates identified.`);
            addLog('[RISK]', '#ef4444', `Risk audit: Portfolio beta ${result.risk_metrics.portfolio_beta?.toFixed(2) ?? 'N/A'}. VaR${result.risk_metrics.var_95 != null ? ' ' + result.risk_metrics.var_95.toFixed(1) + '%' : ' N/A'}.`);
            addLog('[ORCHESTRATOR]', '#e5e5e5', `Debate rounds: ${result.debate_rounds}. Regime: ${result.regime} (${Math.round(result.regime_confidence * 100)}% confidence).`);
            addLog('[ORCHESTRATOR]', '#e5e5e5', `// CONSENSUS REACHED. VERDICT: ${result.decision.toUpperCase()}`);
            setReport(result);
        } else {
            addLog('[ORCHESTRATOR]', '#ef4444', '// ERROR: Could not reach consensus. Check backend connection.');
        }

        setRunning(false);
    };

    // Auto-scroll log
    useEffect(() => {
        logRef.current?.scrollTo({ top: 99999, behavior: 'smooth' });
    }, [logs]);

    const TABS: { key: Tab; label: string }[] = [
        { key: 'convene', label: 'CONVENE' },
        { key: 'logs', label: 'Live Logs' },
        { key: 'debate', label: 'Agent Debate' },
        { key: 'memory', label: 'Memory' },
    ];

    return (
        <div className="flex gap-4 px-6 py-5 max-w-[1600px] mx-auto h-[calc(100vh-108px)] overflow-hidden">
            {/* ── Left: Active Agents ──────────────────────────────── */}
            <div
                className="w-[240px] shrink-0 rounded-xl p-4 overflow-y-auto space-y-3"
                style={{ background: '#0e0e0e', border: '1px solid #333' }}
            >
                <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] uppercase tracking-widest font-mono" style={{ color: '#888' }}>
                        Active Agents
                    </span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded-full font-mono font-bold" style={{ background: 'rgba(234,146,62,0.15)', color: '#ea923e' }}>
                        4 ONLINE
                    </span>
                </div>
                {AGENTS.map((a) => (
                    <div
                        key={a.id}
                        className="rounded-lg p-3"
                        style={{ background: '#111', border: '1px solid #2a2a2a' }}
                    >
                        <div className="flex items-center gap-2 mb-2">
                            <div className="w-7 h-7 rounded-md flex items-center justify-center shrink-0" style={{ background: a.bg }}>
                                <a.icon size={13} color={a.color} />
                            </div>
                            <span className="text-[11px] font-bold" style={{ color: '#e5e5e5' }}>{a.name}</span>
                        </div>
                        <div className="flex items-center gap-1.5 mb-1.5">
                            <span
                                className="live-dot w-1.5 h-1.5 rounded-full shrink-0"
                                style={{ background: running ? a.color : '#555', display: 'inline-block' }}
                            />
                            <span className="text-[10px] font-mono" style={{ color: a.color }}>{a.status}</span>
                        </div>
                        <p className="text-[9px] leading-4" style={{ color: '#555' }}>{a.activity}</p>
                        <div className="flex justify-between mt-2">
                            <span className="text-[9px] font-mono" style={{ color: '#444' }}>LATENCY: 24MS</span>
                            <span className="text-[9px] font-mono" style={{ color: '#444' }}>ID: {a.id.slice(0, 3).toUpperCase()}-09</span>
                        </div>
                    </div>
                ))}
            </div>

            {/* ── Center: Terminal ─────────────────────────────────── */}
            <div
                className="flex-1 rounded-xl flex flex-col overflow-hidden"
                style={{ background: '#0e0e0e', border: '1px solid #333' }}
            >
                {/* Tab bar */}
                <div
                    className="flex items-center justify-between px-4 py-2 shrink-0"
                    style={{ borderBottom: '1px solid #2a2a2a' }}
                >
                    <div className="flex gap-1">
                        {TABS.map((t) => (
                            <button
                                key={t.key}
                                onClick={() => setTab(t.key)}
                                className="text-[10px] px-3 py-1 rounded font-mono transition-colors"
                                style={
                                    tab === t.key
                                        ? { background: '#252525', color: '#e5e5e5', fontWeight: 700 }
                                        : { color: '#555' }
                                }
                            >
                                {t.label}
                            </button>
                        ))}
                    </div>
                    {running && (
                        <div className="flex items-center gap-1.5">
                            <span className="live-dot w-1.5 h-1.5 rounded-full" style={{ background: '#ea923e', display: 'inline-block' }} />
                            <span className="text-[10px] font-mono" style={{ color: '#ea923e' }}>PROCESSING_STREAM</span>
                        </div>
                    )}
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto">
                    {/* CONVENE tab */}
                    {tab === 'convene' && (
                        <div className="flex flex-col items-center justify-center h-full gap-6 px-8">
                            <div className="w-14 h-14 rounded-full flex items-center justify-center" style={{ background: 'rgba(234,146,62,0.15)' }}>
                                <Users size={24} color="#ea923e" />
                            </div>
                            <div className="text-center">
                                <div className="text-xl font-bold mb-1" style={{ color: '#e5e5e5' }}>Investment Council</div>
                                <div className="text-sm" style={{ color: '#888' }}>
                                    Four AI agents — Scout, Risk, Analyst, and Orchestrator — will debate and reach consensus on your portfolio.
                                </div>
                            </div>

                            {/* Form */}
                            <div className="w-full max-w-sm space-y-4">
                                <div>
                                    <label className="text-[10px] uppercase tracking-wider font-mono block mb-1" style={{ color: '#888' }}>
                                        Risk Appetite
                                    </label>
                                    <select
                                        value={riskAppetite}
                                        onChange={(e) => setRiskAppetite(e.target.value as typeof riskAppetite)}
                                        className="w-full px-3 py-2 rounded-lg text-sm font-mono outline-none"
                                        style={{ background: '#252525', border: '1px solid #333', color: '#e5e5e5' }}
                                    >
                                        <option>Conservative</option>
                                        <option>Moderate</option>
                                        <option>Aggressive</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase tracking-wider font-mono block mb-1" style={{ color: '#888' }}>
                                        Monthly Surplus (₹)
                                    </label>
                                    <input
                                        type="number" value={surplus}
                                        onChange={(e) => setSurplus(e.target.value)}
                                        className="w-full px-3 py-2 rounded-lg text-sm font-mono outline-none"
                                        style={{ background: '#252525', border: '1px solid #333', color: '#e5e5e5' }}
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase tracking-wider font-mono block mb-1" style={{ color: '#888' }}>
                                        Investment Horizon (months)
                                    </label>
                                    <input
                                        type="number" value={horizon}
                                        onChange={(e) => setHorizon(e.target.value)}
                                        className="w-full px-3 py-2 rounded-lg text-sm font-mono outline-none"
                                        style={{ background: '#252525', border: '1px solid #333', color: '#e5e5e5' }}
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase tracking-wider font-mono block mb-2" style={{ color: '#888' }}>
                                        Cap Exposure
                                    </label>
                                    <div className="flex gap-4">
                                        {(['large', 'mid', 'small'] as const).map((cap) => (
                                            <label key={cap} className="flex items-center gap-1.5 cursor-pointer">
                                                <input
                                                    type="checkbox"
                                                    checked={caps[cap]}
                                                    onChange={(e) => setCaps((p) => ({ ...p, [cap]: e.target.checked }))}
                                                    className="accent-[#ea923e]"
                                                />
                                                <span className="text-[11px] font-mono capitalize" style={{ color: '#888' }}>
                                                    {cap}
                                                </span>
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                <button
                                    onClick={handleConvene}
                                    disabled={running}
                                    className="w-full py-3 rounded-lg text-xs font-mono font-bold uppercase tracking-widest transition-opacity"
                                    style={{
                                        background: running ? '#444' : '#ea923e',
                                        color: running ? '#888' : '#0e0e0e',
                                        cursor: running ? 'not-allowed' : 'pointer',
                                    }}
                                >
                                    {running ? 'Council in session...' : 'Convene the Council'}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* LOGS tab */}
                    {tab === 'logs' && (
                        <div
                            ref={logRef}
                            className="h-full overflow-y-auto p-4 space-y-1 font-mono text-[11px]"
                            style={{ background: '#080808' }}
                        >
                            {BOOT_LINES.map((l, i) => (
                                <div key={i} style={{ color: '#555' }}>{l}</div>
                            ))}
                            <div style={{ color: '#333' }}>{'─'.repeat(60)}</div>
                            {logs.map((l, i) => (
                                <div key={i} className="flex gap-3">
                                    <span style={{ color: '#444' }}>{l.ts}</span>
                                    <span style={{ color: l.color, fontWeight: 700 }}>{l.tag}</span>
                                    <span style={{ color: '#aaa' }}>{l.msg}</span>
                                </div>
                            ))}
                            {!running && logs.length === 0 && (
                                <div style={{ color: '#555' }}>Awaiting session start...</div>
                            )}
                            <span className="animate-blink font-mono" style={{ color: '#ea923e' }}>_</span>
                        </div>
                    )}

                    {/* DEBATE tab */}
                    {tab === 'debate' && (
                        <div className="p-4 space-y-3">
                            {report ? (
                                <>
                                    <div className="text-[10px] font-mono mb-4" style={{ color: '#555' }}>
                                        {report.debate_rounds} debate round(s) — {report.decision}
                                    </div>
                                    <div
                                        className="rounded-lg p-3 max-w-[75%]"
                                        style={{ background: 'rgba(234,146,62,0.08)', border: '1px solid rgba(234,146,62,0.2)' }}
                                    >
                                        <div className="text-[9px] font-mono mb-1" style={{ color: '#ea923e' }}>SCOUT AGENT</div>
                                        <div className="text-xs" style={{ color: '#e5e5e5' }}>
                                            Identified {report.portfolio.length} opportunities matching {report.regime} market regime. Recommending allocation based on momentum and fundamentals.
                                        </div>
                                    </div>
                                    <div
                                        className="rounded-lg p-3 max-w-[75%] ml-auto"
                                        style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.15)' }}
                                    >
                                        <div className="text-[9px] font-mono mb-1 text-right" style={{ color: '#ef4444' }}>RISK AUDITOR</div>
                                        <div className="text-xs" style={{ color: '#e5e5e5' }}>
                                            {report.reasoning}
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-48 gap-2" style={{ color: '#555' }}>
                                    <div className="text-xs font-mono">No debate data yet.</div>
                                    <div className="text-[10px] font-mono">Convene the council first.</div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* MEMORY tab */}
                    {tab === 'memory' && (
                        <div className="p-4 space-y-3">
                            <div className="text-[10px] uppercase tracking-widest font-mono mb-4" style={{ color: '#888' }}>
                                Past Council Sessions
                            </div>
                            {MEMORY.map((m, i) => (
                                <div
                                    key={i}
                                    className="flex items-center justify-between p-3 rounded-lg"
                                    style={{ background: '#111', border: '1px solid #2a2a2a' }}
                                >
                                    <div>
                                        <div className="text-[10px] font-mono" style={{ color: '#888' }}>{m.date}</div>
                                        <div className="text-xs font-mono" style={{ color: '#e5e5e5' }}>{m.top}</div>
                                    </div>
                                    <span
                                        className="text-[9px] font-mono px-2 py-0.5 rounded-full"
                                        style={{
                                            background: m.verdict.includes('APPROVED') ? 'rgba(34,197,94,0.1)' : 'rgba(234,146,62,0.1)',
                                            color: m.verdict.includes('APPROVED') ? '#22c55e' : '#ea923e',
                                        }}
                                    >
                                        {m.verdict}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Command bar */}
                <div
                    className="shrink-0 flex items-center gap-3 px-4 py-2"
                    style={{ borderTop: '1px solid #2a2a2a' }}
                >
                    <span className="font-mono text-xs" style={{ color: '#ea923e' }}>&gt;</span>
                    <input
                        type="text"
                        placeholder="Enter manual override command or query agent status..."
                        className="flex-1 bg-transparent outline-none text-xs font-mono"
                        style={{ color: '#888' }}
                    />
                    <span
                        className="text-[9px] px-1.5 py-0.5 rounded font-mono"
                        style={{ color: '#555', background: '#1a1a1a', border: '1px solid #333' }}
                    >
                        CMD + K
                    </span>
                </div>
            </div>

            {/* ── Right: Verdict ───────────────────────────────────── */}
            <div
                className="w-[280px] shrink-0 rounded-xl p-4 overflow-y-auto flex flex-col gap-4"
                style={{ background: '#0e0e0e', border: '1px solid #333' }}
            >
                <div className="text-[10px] uppercase tracking-widest font-mono" style={{ color: '#888' }}>
                    Council Verdict
                </div>

                {!report ? (
                    <div className="flex flex-col items-center justify-center flex-1 gap-2 text-center">
                        <div className="text-[10px] font-mono" style={{ color: '#555' }}>Awaiting Council Decision...</div>
                        <div className="text-[9px] font-mono" style={{ color: '#444' }}>Convene the council to see recommendations.</div>
                    </div>
                ) : (
                    <>
                        {/* Verdict */}
                        <div
                            className="rounded-xl p-4 text-center"
                            style={{ background: '#111', border: '1px solid #333' }}
                        >
                            <div className="text-[10px] font-mono mb-1" style={{ color: '#888' }}>Decision</div>
                            <div
                                className="text-3xl font-bold font-mono flex items-center justify-center gap-2"
                                style={{ color: '#ea923e' }}
                            >
                                {report.decision.toUpperCase()}
                                <ChevronRight size={24} />
                            </div>
                            <div className="text-[10px] font-mono mt-1" style={{ color: '#888' }}>
                                {report.regime} Market
                            </div>
                        </div>

                        {/* Conviction gauge */}
                        <ConvictionGauge pct={Math.round(report.regime_confidence * 100)} />

                        {/* Portfolio */}
                        <div>
                            <div className="text-[10px] uppercase tracking-widest font-mono mb-2" style={{ color: '#888' }}>
                                Portfolio Impact
                            </div>
                            <div className="space-y-2">
                                {report.portfolio.slice(0, 5).map((item: PortfolioItem) => (
                                    <div
                                        key={item.ticker}
                                        className="flex items-center justify-between p-2 rounded-lg"
                                        style={{ background: '#111', border: '1px solid #2a2a2a' }}
                                    >
                                        <div>
                                            <div className="text-xs font-mono font-bold" style={{ color: '#e5e5e5' }}>{item.ticker}</div>
                                            <div className="text-[9px]" style={{ color: '#555' }}>{item.type}</div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-[10px] font-mono" style={{ color: '#e5e5e5' }}>
                                                {item.allocation_pct.toFixed(1)}%
                                            </div>
                                            <div className="text-[9px] font-mono" style={{ color: '#22c55e' }}>
                                                ₹{item.monthly_investment.toLocaleString('en-IN')}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Risk metrics */}
                        {report.risk_metrics && (
                            <div>
                                <div className="text-[10px] uppercase tracking-widest font-mono mb-2" style={{ color: '#888' }}>
                                    Risk Metrics
                                </div>
                                <div className="space-y-1.5">
                                    {[
                                        { label: 'Portfolio Beta', value: report.risk_metrics.portfolio_beta?.toFixed(2) ?? '—' },
                                        { label: 'VaR (95%)', value: report.risk_metrics.var_95 != null ? formatPct(report.risk_metrics.var_95) : '—' },
                                        { label: 'Avg Correlation', value: report.risk_metrics.avg_correlation?.toFixed(2) ?? '—' },
                                    ].map(({ label, value }) => (
                                        <div key={label} className="flex justify-between">
                                            <span className="text-[10px] font-mono" style={{ color: '#555' }}>{label}</span>
                                            <span className="text-[10px] font-mono" style={{ color: '#e5e5e5' }}>{value}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
