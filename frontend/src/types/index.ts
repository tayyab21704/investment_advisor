// === MARKET ===
export interface IndexData {
    value: number;
    change: number;
    change_pct: number;
}
export interface MarketIndices {
    '^NSEI': IndexData;
    '^BSESN': IndexData;
    '^NSEBANK': IndexData;
}

// === STOCK ===
export interface ChartPoint {
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}
export interface StockData {
    symbol: string;
    name: string;
    price: number;
    change: number;
    change_pct: number;
    open: number | null;
    high: number | null;
    low: number | null;
    prev_close: number | null;
    volume: number | null;
    market_cap: number | null;
    pe_ratio: number | null;
    roe: number | null;
    eps: number | null;
    week_52_high: number | null;
    week_52_low: number | null;
    debt_equity: number | null;
    dividend_yield: number | null;
    sector: string;
    industry: string;
    description: string;
    chart: ChartPoint[];
}

// === MOVERS ===
export interface Mover {
    symbol: string;
    price: number;
    change_pct: number;
}
export interface TopMovers {
    gainers: Mover[];
    losers: Mover[];
}

// === SEARCH ===
export interface SearchResult {
    symbol: string;
    company_name: string;
    sector: string;
    market_cap_category: string;
}

// === COUNCIL ===
export type Regime = 'RISK_ON' | 'RISK_OFF' | 'NEUTRAL';
export type Decision = 'APPROVE' | 'REJECT';

export interface PortfolioAsset {
    ticker: string;
    company_name?: string;
    allocation_pct: number;
    monthly_amount_inr: number;
    reasoning?: string;
}
export interface RiskMetrics {
    portfolio_beta: number | null;
    volatility: number | null;
    var_95: number | null;
    avg_correlation: number | null;
}
export interface CouncilReport {
    regime: Regime;
    regime_confidence: number;
    decision: Decision;
    reasoning: string;
    portfolio: PortfolioAsset[];
    risk_metrics: RiskMetrics;
    debate_rounds: number;
    safe_harbor_activated: boolean;
}

// === PORTFOLIO ===
export interface Holding {
    id: number;
    symbol: string;
    company_name: string;
    quantity: number;
    avg_buy_price: number;
    buy_date: string;
    current_price?: number;
    current_value?: number;
    pnl?: number;
    pnl_pct?: number;
}
