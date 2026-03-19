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
    { id: 'scout', name: 'Scout Agent', tag: '[SCOUT]', icon: Search, color: 'var(--primary)', bg: 'var(--primary-dim)', status: 'Scanning Markets', activity: 'Analyzing volume patterns across NIFTY 100. Detecting breakout candidates in mid-cap space.' },
    { id: 'risk', name: 'Risk Auditor', tag: '[RISK]', icon: Shield, color: 'var(--negative)', bg: 'var(--negative-dim)', status: 'Evaluating Risk', activity: 'Running VaR simulation on portfolio candidates. Cross-checking correlation matrix.' },
    { id: 'analyst', name: 'Analyst Agent', tag: '[ANALYST]', icon: BarChart2, color: 'var(--blue)', bg: 'var(--blue-dim)', status: 'Processing Data', activity: 'Fetching macro indicators. Comparing P/E ratios against 5-year sector averages.' },
    { id: 'orchestrator', name: 'Orchestrator', tag: '[ORCHESTRATOR]', icon: Brain, color: 'var(--color-text-primary)', bg: 'var(--color-bg-elevated)', status: 'Awaiting Inputs', activity: 'Monitoring agent outputs. Will finalize verdict when consensus threshold is reached.' },
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
            <div className="text-[10px] uppercase tracking-widest font-mono mb-2 text-text-secondary">
                Conviction
            </div>
            <svg width={128} height={72} viewBox="0 0 128 72">
                {/* track */}
                <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`} fill="none" stroke="var(--color-border-subtle)" strokeWidth="10" strokeLinecap="round" />
                {/* fill */}
                <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`} fill="none" stroke="var(--primary)" strokeWidth="10" strokeLinecap="round"
                    strokeDasharray={`${fill} ${circ}`} />
                <text x={cx} y={cy - 6} textAnchor="middle" fill="var(--color-text-primary)" fontSize="18" fontWeight="700" fontFamily="monospace">
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
            addLog('[SCOUT]', 'var(--primary)', `Scout report ready. ${result.portfolio.length} candidates identified.`);
            addLog('[RISK]', 'var(--negative)', `Risk audit: Portfolio beta ${result.risk_metrics.portfolio_beta?.toFixed(2) ?? 'N/A'}. VaR${result.risk_metrics.var_95 != null ? ' ' + result.risk_metrics.var_95.toFixed(1) + '%' : ' N/A'}.`);
            addLog('[ORCHESTRATOR]', 'var(--color-text-primary)', `Debate rounds: ${result.debate_rounds}. Regime: ${result.regime} (${Math.round(result.regime_confidence * 100)}% confidence).`);
            addLog('[ORCHESTRATOR]', 'var(--color-text-primary)', `// CONSENSUS REACHED. VERDICT: ${result.decision.toUpperCase()}`);
            setReport(result);
        } else {
            addLog('[ORCHESTRATOR]', 'var(--negative)', '// ERROR: Could not reach consensus. Check backend connection.');
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
                className="w-[240px] shrink-0 rounded-2xl p-5 overflow-y-auto space-y-4 bg-bg-surface border border-border-subtle shadow-xl"
            >
                <div className="flex items-center justify-between mb-3">
                    <span className="text-[11px] uppercase tracking-widest font-mono text-text-secondary">
                        Active Agents
                    </span>
                    <span className="text-[9px] px-2 py-0.5 rounded-md font-mono font-bold bg-primary-dim text-primary border border-primary/20">
                        4 ONLINE
                    </span>
                </div>
                <div className="space-y-3">
                {AGENTS.map((a) => (
                    <div
                        key={a.id}
                        className="rounded-xl p-3 bg-bg-elevated border border-border-default hover:border-border-accent transition-colors shadow-sm"
                    >
                        <div className="flex items-center gap-2.5 mb-2.5">
                            <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border border-border-subtle" style={{ background: a.bg }}>
                                <a.icon size={15} color={a.color} />
                            </div>
                            <span className="text-xs font-bold text-text-primary tracking-tight">{a.name}</span>
                        </div>
                        <div className="flex items-center gap-2 mb-2">
                            <span
                                className="live-dot w-2 h-2 rounded-full shrink-0"
                                style={{ background: running ? a.color : 'var(--color-text-muted)', display: 'inline-block' }}
                            />
                            <span className="text-[10px] font-mono font-semibold" style={{ color: a.color }}>{a.status}</span>
                        </div>
                        <p className="text-[10px] leading-relaxed text-text-secondary">{a.activity}</p>
                        <div className="flex justify-between mt-3 pt-2 border-t border-border-default">
                            <span className="text-[9px] font-mono text-text-muted">LATENCY: 24MS</span>
                            <span className="text-[9px] font-mono text-text-muted">ID: {a.id.slice(0, 3).toUpperCase()}-09</span>
                        </div>
                    </div>
                ))}
                </div>
            </div>

            {/* ── Center: Terminal ─────────────────────────────────── */}
            <div
                className="flex-1 rounded-2xl flex flex-col overflow-hidden bg-bg-surface border border-border-subtle shadow-xl"
            >
                {/* Tab bar */}
                <div
                    className="flex items-center justify-between px-5 py-3 shrink-0 border-b border-border-subtle bg-bg-elevated"
                >
                    <div className="flex gap-2">
                        {TABS.map((t) => (
                            <button
                                key={t.key}
                                onClick={() => setTab(t.key)}
                                className={`text-[11px] px-3 py-1.5 rounded-md font-mono transition-colors font-semibold ${
                                    tab === t.key
                                        ? 'bg-bg-overlay text-text-primary shadow-sm border border-border-default'
                                        : 'text-text-muted hover:text-text-secondary hover:bg-bg-base'
                                }`}
                            >
                                {t.label}
                            </button>
                        ))}
                    </div>
                    {running && (
                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-primary-dim border border-primary/20">
                            <span className="live-dot w-2 h-2 rounded-full bg-primary" />
                            <span className="text-[10px] font-mono font-bold text-primary">PROCESSING_STREAM</span>
                        </div>
                    )}
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto">
                    {/* CONVENE tab */}
                    {tab === 'convene' && (
                        <div className="flex flex-col items-center justify-center h-full gap-6 px-8">
                            <div className="w-16 h-16 rounded-full flex items-center justify-center bg-primary-dim shadow-[0_0_30px_rgba(var(--primary-rgb),0.2)]">
                                <Users size={28} className="text-primary" />
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold tracking-tight mb-2 text-text-primary">Investment Council</div>
                                <div className="text-sm max-w-md mx-auto text-text-secondary">
                                    Four AI agents — Scout, Risk, Analyst, and Orchestrator — will debate and reach consensus on your portfolio.
                                </div>
                            </div>

                            {/* Form */}
                            <div className="w-full max-w-sm space-y-5 bg-bg-elevated p-6 rounded-2xl border border-border-subtle shadow-sm mt-2">
                                <div>
                                    <label className="text-[10px] uppercase tracking-wider font-mono font-bold block mb-2 text-text-secondary">
                                        Risk Appetite
                                    </label>
                                    <select
                                        value={riskAppetite}
                                        onChange={(e) => setRiskAppetite(e.target.value as typeof riskAppetite)}
                                        className="w-full px-4 py-2.5 rounded-xl text-sm font-mono outline-none bg-bg-base border border-border-default text-text-primary focus:border-border-accent focus:ring-1 focus:ring-border-accent transition-all"
                                    >
                                        <option>Conservative</option>
                                        <option>Moderate</option>
                                        <option>Aggressive</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase tracking-wider font-mono font-bold block mb-2 text-text-secondary">
                                        Monthly Surplus (₹)
                                    </label>
                                    <input
                                        type="number" value={surplus}
                                        onChange={(e) => setSurplus(e.target.value)}
                                        className="w-full px-4 py-2.5 rounded-xl text-sm font-mono outline-none bg-bg-base border border-border-default text-text-primary focus:border-border-accent focus:ring-1 focus:ring-border-accent transition-all"
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase tracking-wider font-mono font-bold block mb-2 text-text-secondary">
                                        Investment Horizon (months)
                                    </label>
                                    <input
                                        type="number" value={horizon}
                                        onChange={(e) => setHorizon(e.target.value)}
                                        className="w-full px-4 py-2.5 rounded-xl text-sm font-mono outline-none bg-bg-base border border-border-default text-text-primary focus:border-border-accent focus:ring-1 focus:ring-border-accent transition-all"
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase tracking-wider font-mono font-bold block mb-3 text-text-secondary">
                                        Cap Exposure
                                    </label>
                                    <div className="flex gap-4">
                                        {(['large', 'mid', 'small'] as const).map((cap) => (
                                            <label key={cap} className="flex items-center gap-2 cursor-pointer group">
                                                <input
                                                    type="checkbox"
                                                    checked={caps[cap]}
                                                    onChange={(e) => setCaps((p) => ({ ...p, [cap]: e.target.checked }))}
                                                    className="accent-primary w-4 h-4 cursor-pointer"
                                                />
                                                <span className="text-[11px] font-mono capitalize text-text-secondary group-hover:text-text-primary transition-colors">
                                                    {cap}
                                                </span>
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                <button
                                    onClick={handleConvene}
                                    disabled={running}
                                    className={`w-full py-3.5 mt-2 rounded-xl text-xs font-mono font-bold uppercase tracking-widest transition-all ${
                                        running
                                            ? 'bg-bg-base border border-border-default text-text-muted cursor-not-allowed'
                                            : 'bg-primary text-text-inverse hover:opacity-90 shadow-[0_0_15px_rgba(var(--primary-rgb),0.3)] cursor-pointer'
                                    }`}
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
                            className="h-full overflow-y-auto p-5 space-y-1.5 font-mono text-[11px] bg-bg-base"
                        >
                            {BOOT_LINES.map((l, i) => (
                                <div key={i} className="text-text-secondary">{l}</div>
                            ))}
                            <div className="text-border-default">{'─'.repeat(60)}</div>
                            {logs.map((l, i) => (
                                <div key={i} className="flex gap-3">
                                    <span className="text-text-muted">{l.ts}</span>
                                    <span style={{ color: l.color, fontWeight: 700 }}>{l.tag}</span>
                                    <span className="text-text-secondary">{l.msg}</span>
                                </div>
                            ))}
                            {!running && logs.length === 0 && (
                                <div className="text-text-muted">Awaiting session start...</div>
                            )}
                            <span className="animate-blink font-mono text-primary">_</span>
                        </div>
                    )}

                    {/* DEBATE tab */}
                    {tab === 'debate' && (
                        <div className="p-6 space-y-4">
                            {report ? (
                                <>
                                    <div className="text-[11px] font-mono mb-5 text-text-muted text-center">
                                        {report.debate_rounds} debate round(s) — {report.decision}
                                    </div>
                                    <div
                                        className="rounded-xl p-4 max-w-[80%] bg-primary-dim border border-primary/20 shadow-sm"
                                    >
                                        <div className="text-[10px] font-mono mb-1.5 font-bold text-primary">SCOUT AGENT</div>
                                        <div className="text-xs leading-5 text-text-primary">
                                            Identified {report.portfolio.length} opportunities matching {report.regime} market regime. Recommending allocation based on momentum and fundamentals.
                                        </div>
                                    </div>
                                    <div
                                        className="rounded-xl p-4 max-w-[80%] ml-auto bg-negative-dim border border-negative/20 shadow-sm"
                                    >
                                        <div className="text-[10px] font-mono mb-1.5 text-right font-bold text-negative">RISK AUDITOR</div>
                                        <div className="text-xs leading-5 text-text-primary">
                                            {report.reasoning}
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-48 gap-3 text-text-muted">
                                    <div className="text-sm font-mono font-semibold text-text-secondary">No debate data yet.</div>
                                    <div className="text-[11px] font-mono">Convene the council first.</div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* MEMORY tab */}
                    {tab === 'memory' && (
                        <div className="p-6 space-y-4">
                            <div className="text-[11px] font-semibold uppercase tracking-widest font-mono mb-5 text-text-secondary">
                                Past Council Sessions
                            </div>
                            {MEMORY.map((m, i) => (
                                <div
                                    key={i}
                                    className="flex items-center justify-between p-4 rounded-xl bg-bg-elevated border border-border-default hover:border-border-accent transition-colors shadow-sm"
                                >
                                    <div>
                                        <div className="text-[11px] font-mono text-text-secondary mb-0.5">{m.date}</div>
                                        <div className="text-sm font-mono font-bold text-text-primary">{m.top}</div>
                                    </div>
                                    <span
                                        className="text-[10px] font-mono px-2.5 py-1 rounded-md font-bold"
                                        style={{
                                            background: m.verdict.includes('APPROVED') ? 'var(--positive-dim)' : 'var(--primary-dim)',
                                            color: m.verdict.includes('APPROVED') ? 'var(--positive)' : 'var(--primary)',
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
                    className="shrink-0 flex items-center gap-3 px-5 py-3 border-t border-border-subtle bg-bg-elevated"
                >
                    <span className="font-mono text-xs font-bold text-primary">&gt;</span>
                    <input
                        type="text"
                        placeholder="Enter manual override command or query agent status..."
                        className="flex-1 bg-transparent outline-none text-[13px] font-mono text-text-primary placeholder:text-text-muted"
                    />
                    <span
                        className="text-[10px] px-2 py-1 rounded animate-pulse font-mono text-text-muted bg-bg-base border border-border-default"
                    >
                        CMD + K
                    </span>
                </div>
            </div>

            {/* ── Right: Verdict ───────────────────────────────────── */}
            <div
                className="w-[280px] shrink-0 rounded-2xl p-5 overflow-y-auto flex flex-col gap-5 bg-bg-surface border border-border-subtle shadow-xl"
            >
                <div className="text-[11px] font-semibold uppercase tracking-widest font-mono text-text-secondary">
                    Council Verdict
                </div>

                {!report ? (
                    <div className="flex flex-col items-center justify-center flex-1 gap-2.5 text-center text-text-muted">
                        <div className="text-[11px] font-mono">Awaiting Council Decision...</div>
                        <div className="text-[10px] font-mono text-text-muted/60">Convene the council to see recommendations.</div>
                    </div>
                ) : (
                    <>
                        {/* Verdict */}
                        <div
                            className="rounded-xl p-5 text-center bg-bg-elevated border border-border-default shadow-sm"
                        >
                            <div className="text-[11px] font-mono mb-2 text-text-secondary font-semibold">Decision</div>
                            <div
                                className="text-3xl font-bold font-mono flex items-center justify-center gap-2 text-primary"
                            >
                                {report.decision.toUpperCase()}
                                <ChevronRight size={28} className="text-primary opacity-80" />
                            </div>
                            <div className="text-[11px] font-mono mt-2 text-text-secondary">
                                {report.regime} Market
                            </div>
                        </div>

                        {/* Conviction gauge */}
                        <ConvictionGauge pct={Math.round(report.regime_confidence * 100)} />

                        {/* Portfolio */}
                        <div>
                            <div className="text-[11px] font-semibold uppercase tracking-widest font-mono mb-3 text-text-secondary">
                                Portfolio Impact
                            </div>
                            <div className="space-y-2.5">
                                {report.portfolio.slice(0, 5).map((item: PortfolioItem) => (
                                    <div
                                        key={item.ticker}
                                        className="flex items-center justify-between p-3 rounded-xl bg-bg-elevated border border-border-default shadow-sm hover:border-border-accent transition-colors"
                                    >
                                        <div>
                                            <div className="text-sm font-mono font-bold text-text-primary mb-0.5">{item.ticker}</div>
                                            <div className="text-[10px] text-text-secondary">{item.type}</div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-[11px] font-mono font-bold text-text-primary">
                                                {item.allocation_pct.toFixed(1)}%
                                            </div>
                                            <div className="text-[10px] font-mono text-positive mt-0.5">
                                                ₹{item.monthly_investment.toLocaleString('en-IN')}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Risk metrics */}
                        {report.risk_metrics && (
                            <div className="mt-2">
                                <div className="text-[11px] font-semibold uppercase tracking-widest font-mono mb-3 text-text-secondary">
                                    Risk Metrics
                                </div>
                                <div className="space-y-2">
                                    {[
                                        { label: 'Portfolio Beta', value: report.risk_metrics.portfolio_beta?.toFixed(2) ?? '—' },
                                        { label: 'VaR (95%)', value: report.risk_metrics.var_95 != null ? formatPct(report.risk_metrics.var_95) : '—' },
                                        { label: 'Avg Correlation', value: report.risk_metrics.avg_correlation?.toFixed(2) ?? '—' },
                                    ].map(({ label, value }) => (
                                        <div key={label} className="flex justify-between items-center">
                                            <span className="text-[10px] font-mono text-text-muted">{label}</span>
                                            <span className="text-[11px] font-mono font-semibold text-text-primary">{value}</span>
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
