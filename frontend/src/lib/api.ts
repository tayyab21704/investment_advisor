// ─── Investment Council — Typed API Client ────────────────────────────────────

import type {
    IndexDetail, MarketIndices, MoverDetail, TopMovers,
    SectorData, SearchResponse, StockDetail, ChartResponse,
    MarketStatus, HealthResponse, CouncilProfile, CouncilReport,
} from './types';

const BASE_URL =
    (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000');

// ─── Generic fetcher ──────────────────────────────────────────────────────────
/** Extracts a human-readable message from a FastAPI error body (detail may be a dict). */
function extractDetail(err: unknown, status: number): string {
    if (typeof err !== 'object' || err === null) return `HTTP ${status}`;
    const detail = (err as Record<string, unknown>).detail;
    if (!detail) return `HTTP ${status}`;
    if (typeof detail === 'string') return detail;
    if (typeof detail === 'object') {
        const d = detail as Record<string, unknown>;
        return (d.error as string) ?? JSON.stringify(detail);
    }
    return String(detail);
}

async function get<T>(path: string): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, { cache: 'no-store' });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(extractDetail(err, res.status));
    }
    return res.json();
}

async function post<T, B>(path: string, body: B): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        cache: 'no-store',
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'API error' }));
        throw new Error(extractDetail(err, res.status));
    }
    return res.json();
}


// ─── Endpoint Functions ──────────────────────────────────────────────────────

export async function fetchHealth(): Promise<HealthResponse | null> {
    try { return await get<HealthResponse>('/api/health'); }
    catch (e) { console.error('[api] fetchHealth', e); return null; }
}

export async function fetchMarketStatus(): Promise<MarketStatus | null> {
    try { return await get<MarketStatus>('/api/market-status'); }
    catch (e) { console.error('[api] fetchMarketStatus', e); return null; }
}

export async function fetchMarketIndices(): Promise<IndexDetail[]> {
    try {
        const data = await get<MarketIndices>('/api/market-indices');
        return Object.values(data);
    } catch (e) { console.error('[api] fetchMarketIndices', e); return []; }
}

export async function fetchTopMovers(): Promise<TopMovers> {
    try { return await get<TopMovers>('/api/top-movers'); }
    catch (e) { console.error('[api] fetchTopMovers', e); return { gainers: [], losers: [] }; }
}

export async function fetchSectors(): Promise<SectorData[]> {
    try { return await get<SectorData[]>('/api/sectors'); }
    catch (e) { console.error('[api] fetchSectors', e); return []; }
}

export async function searchStocks(q: string): Promise<SearchResponse> {
    try {
        return await get<SearchResponse>(`/api/search?q=${encodeURIComponent(q)}`);
    } catch (e) {
        console.error('[api] searchStocks', e);
        return { results: [], query: q, total: 0 };
    }
}

export async function fetchStockDetail(symbol: string): Promise<StockDetail | null> {
    try { return await get<StockDetail>(`/api/stock/${symbol.toUpperCase()}`); }
    catch (e) { console.error('[api] fetchStockDetail', e); return null; }
}

export async function fetchChartData(symbol: string, timeframe: string): Promise<ChartResponse | null> {
    try {
        return await get<ChartResponse>(`/api/chart/${encodeURIComponent(symbol)}?timeframe=${timeframe}`);
    } catch (e) {
        console.error('[api] fetchChartData', e);
        return null;
    }
}

export async function runCouncilAnalysis(profile: CouncilProfile): Promise<CouncilReport | null> {
    try { return await post<CouncilReport, CouncilProfile>('/api/council/analyze', profile); }
    catch (e) { console.error('[api] runCouncilAnalysis', e); return null; }
}

// Legacy export for backwards compat with any existing code
export const api = {
    getMarketIndices: fetchMarketIndices,
    getTopMovers: fetchTopMovers,
    searchStocks: (q: string) => searchStocks(q),
    getStockDetail: fetchStockDetail,
    analyzePortfolio: runCouncilAnalysis,
};

export type { IndexDetail, MoverDetail, SectorData, MarketStatus, StockDetail, CouncilReport };
