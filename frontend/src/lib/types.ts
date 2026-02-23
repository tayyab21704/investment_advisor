// ─── Investment Council — API Type Definitions ────────────────────────────────

export interface ChartCandle {
    timestamp: string;
    open: number | null;
    high: number | null;
    low: number | null;
    close: number | null;
    volume: number;
}

export interface ChartResponse {
    symbol: string;
    timeframe: string;
    candles: ChartCandle[];
}

export interface IndexDetail {
    symbol: string;
    name: string;
    value: number;
    current_price: number;
    change: number;
    change_pct: number;
    day_high: number | null;
    day_low: number | null;
    year_high: number | null;
    year_low: number | null;
    sparkline: number[];
    market_regime: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    regime_confidence: number;
}

export type MarketIndices = Record<string, IndexDetail>;

export interface MoverDetail {
    symbol: string;
    name: string | null;
    price: number;
    current_price: number;
    change: number;
    change_pct: number;
    volume: number;
    avg_volume: number;
    volume_surge: boolean;
    sector: string | null;
    sparkline: number[];
}

export interface TopMovers {
    gainers: MoverDetail[];
    losers: MoverDetail[];
}

export interface SectorData {
    sector_name: string;
    change_pct: number;
    performance_1w: number;
    performance_1m: number;
    top_performer: string | null;
    worst_performer: string | null;
    market_cap_cr: number;
}

export interface SearchResult {
    symbol: string;
    name: string;
    sector: string | null;
    industry: string | null;
    current_price: number | null;
    change_pct: number | null;
    market_cap_cr: number | null;
}

export interface SearchResponse {
    results: SearchResult[];
    query: string;
    total: number;
}

export interface StockDetail {
    symbol: string;
    name: string;
    sector: string | null;
    industry: string | null;
    price: number;
    current_price: number;
    change: number;
    change_pct: number;
    open: number | null;
    day_high: number | null;
    day_low: number | null;
    prev_close: number | null;
    year_high: number | null;
    year_low: number | null;
    volume: number;
    avg_volume: number;
    market_cap_cr: number | null;
    pe_ratio: number | null;
    pb_ratio: number | null;
    dividend_yield: number | null;
    eps: number | null;
    roe: number | null;
    debt_to_equity: number | null;
    revenue_cr: number | null;
    profit_cr: number | null;
    chart_1d: ChartCandle[];
    chart_1w: ChartCandle[];
    chart_1m: ChartCandle[];
    chart_1y: ChartCandle[];
    chart_5y: ChartCandle[];
    chart: Array<{ time: string; open: number; high: number; low: number; close: number; volume: number }>;
    sma_20: number | null;
    sma_50: number | null;
    sma_200: number | null;
    rsi_14: number | null;
    above_sma_50: boolean | null;
    above_sma_200: boolean | null;
    regime: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    regime_confidence: number;
    description: string | null;
}

export interface MarketStatus {
    is_open: boolean;
    current_time_ist: string;
    session: 'pre_market' | 'open' | 'post_market' | 'closed';
    next_open: string;
}

export interface HealthResponse {
    status: string;
    timestamp: string;
}

export interface CouncilProfile {
    risk_appetite: 'Conservative' | 'Moderate' | 'Aggressive';
    actual_risk_capacity: number;
    monthly_surplus: number;
    monthly_income?: number;
    monthly_debt?: number;
}

export interface PortfolioItem {
    ticker: string;
    name: string;
    monthly_investment: number;
    allocation_pct: number;
    type: string;
    reasoning: string;
}

export interface CouncilReport {
    regime: string;
    regime_confidence: number;
    decision: string;
    reasoning: string;
    portfolio: PortfolioItem[];
    risk_metrics: {
        portfolio_beta: number | null;
        volatility: number | null;
        var_95: number | null;
        avg_correlation: number | null;
    };
    debate_rounds: number;
    safe_harbor_activated: boolean;
}
