"""
STOCK_UNIVERSE
Master metadata list for the top ~80 NSE stocks (NIFTY 100 subset).
Keyed by NSE symbol (WITHOUT the .NS suffix).
Used by:
  - /api/search    — name / sector lookup
  - /api/sectors   — sector grouping
  - /api/top-movers — sector label enrichment
"""

STOCK_UNIVERSE: dict[str, dict] = {
    # ── IT ──────────────────────────────────────────────────────────────
    "TCS":        {"name": "Tata Consultancy Services", "sector": "IT", "industry": "IT Services"},
    "INFY":       {"name": "Infosys",                   "sector": "IT", "industry": "IT Services"},
    "WIPRO":      {"name": "Wipro",                     "sector": "IT", "industry": "IT Services"},
    "HCLTECH":    {"name": "HCL Technologies",          "sector": "IT", "industry": "IT Services"},
    "TECHM":      {"name": "Tech Mahindra",             "sector": "IT", "industry": "IT Services"},
    "LTI":        {"name": "LTI Mindtree",              "sector": "IT", "industry": "IT Services"},
    "MPHASIS":    {"name": "Mphasis",                   "sector": "IT", "industry": "IT Services"},
    "PERSISTENT": {"name": "Persistent Systems",        "sector": "IT", "industry": "IT Services"},

    # ── Banking ─────────────────────────────────────────────────────────
    "HDFCBANK":   {"name": "HDFC Bank",                 "sector": "Banking", "industry": "Private Banks"},
    "ICICIBANK":  {"name": "ICICI Bank",                "sector": "Banking", "industry": "Private Banks"},
    "SBIN":       {"name": "State Bank of India",       "sector": "Banking", "industry": "Public Sector Banks"},
    "KOTAKBANK":  {"name": "Kotak Mahindra Bank",       "sector": "Banking", "industry": "Private Banks"},
    "AXISBANK":   {"name": "Axis Bank",                 "sector": "Banking", "industry": "Private Banks"},
    "INDUSINDBK": {"name": "IndusInd Bank",             "sector": "Banking", "industry": "Private Banks"},
    "BANKBARODA": {"name": "Bank of Baroda",            "sector": "Banking", "industry": "Public Sector Banks"},
    "PNB":        {"name": "Punjab National Bank",      "sector": "Banking", "industry": "Public Sector Banks"},
    "FEDERALBNK": {"name": "Federal Bank",              "sector": "Banking", "industry": "Private Banks"},

    # ── Auto ────────────────────────────────────────────────────────────
    "MARUTI":     {"name": "Maruti Suzuki",             "sector": "Auto", "industry": "Passenger Vehicles"},
    "TATAMOTORS": {"name": "Tata Motors",               "sector": "Auto", "industry": "Commercial Vehicles"},
    "M&M":        {"name": "Mahindra & Mahindra",       "sector": "Auto", "industry": "Passenger Vehicles"},
    "BAJAJ-AUTO": {"name": "Bajaj Auto",                "sector": "Auto", "industry": "Two Wheelers"},
    "EICHERMOT":  {"name": "Eicher Motors",             "sector": "Auto", "industry": "Two Wheelers"},
    "HEROMOTOCO": {"name": "Hero MotoCorp",             "sector": "Auto", "industry": "Two Wheelers"},
    "BOSCH":      {"name": "Bosch",                     "sector": "Auto", "industry": "Auto Components"},
    "MOTHERSON":  {"name": "Samvardhana Motherson",     "sector": "Auto", "industry": "Auto Components"},

    # ── Pharma ──────────────────────────────────────────────────────────
    "SUNPHARMA":  {"name": "Sun Pharmaceutical",        "sector": "Pharma", "industry": "Pharmaceuticals"},
    "DIVISLAB":   {"name": "Divi's Laboratories",       "sector": "Pharma", "industry": "Pharmaceuticals"},
    "CIPLA":      {"name": "Cipla",                     "sector": "Pharma", "industry": "Pharmaceuticals"},
    "DRREDDY":    {"name": "Dr. Reddy's Laboratories",  "sector": "Pharma", "industry": "Pharmaceuticals"},
    "APOLLOHOSP": {"name": "Apollo Hospitals",          "sector": "Pharma", "industry": "Healthcare Services"},
    "LUPIN":      {"name": "Lupin",                     "sector": "Pharma", "industry": "Pharmaceuticals"},
    "BIOCON":     {"name": "Biocon",                    "sector": "Pharma", "industry": "Biotechnology"},
    "TORNTPHARM": {"name": "Torrent Pharmaceuticals",   "sector": "Pharma", "industry": "Pharmaceuticals"},

    # ── Energy ──────────────────────────────────────────────────────────
    "RELIANCE":   {"name": "Reliance Industries",       "sector": "Energy", "industry": "Integrated Oil & Gas"},
    "ONGC":       {"name": "Oil & Natural Gas Corp",    "sector": "Energy", "industry": "Oil & Gas Exploration"},
    "NTPC":       {"name": "NTPC",                      "sector": "Energy", "industry": "Power Generation"},
    "POWERGRID":  {"name": "Power Grid Corp",           "sector": "Energy", "industry": "Power Transmission"},
    "COALINDIA":  {"name": "Coal India",                "sector": "Energy", "industry": "Coal Mining"},
    "BPCL":       {"name": "BPCL",                      "sector": "Energy", "industry": "Petroleum Refining"},
    "IOC":        {"name": "Indian Oil Corporation",    "sector": "Energy", "industry": "Petroleum Refining"},
    "ADANIGREEN": {"name": "Adani Green Energy",        "sector": "Energy", "industry": "Renewable Energy"},

    # ── FMCG ────────────────────────────────────────────────────────────
    "HINDUNILVR": {"name": "Hindustan Unilever",        "sector": "FMCG", "industry": "Personal Products"},
    "ITC":        {"name": "ITC",                       "sector": "FMCG", "industry": "Tobacco & FMCG"},
    "NESTLEIND":  {"name": "Nestle India",              "sector": "FMCG", "industry": "Food Products"},
    "BRITANNIA":  {"name": "Britannia Industries",      "sector": "FMCG", "industry": "Food Products"},
    "DABUR":      {"name": "Dabur India",               "sector": "FMCG", "industry": "Personal Products"},
    "MARICO":     {"name": "Marico",                    "sector": "FMCG", "industry": "Personal Products"},
    "COLPAL":     {"name": "Colgate-Palmolive India",   "sector": "FMCG", "industry": "Personal Products"},
    "GODREJCP":   {"name": "Godrej Consumer Products",  "sector": "FMCG", "industry": "Personal Products"},

    # ── Metals ──────────────────────────────────────────────────────────
    "TATASTEEL":  {"name": "Tata Steel",                "sector": "Metals", "industry": "Steel"},
    "JSWSTEEL":   {"name": "JSW Steel",                 "sector": "Metals", "industry": "Steel"},
    "HINDALCO":   {"name": "Hindalco Industries",       "sector": "Metals", "industry": "Aluminium"},
    "VEDL":       {"name": "Vedanta",                   "sector": "Metals", "industry": "Diversified Metals"},
    "SAIL":       {"name": "Steel Authority of India",  "sector": "Metals", "industry": "Steel"},
    "NMDC":       {"name": "NMDC",                      "sector": "Metals", "industry": "Iron Ore Mining"},
    "NATIONALUM": {"name": "National Aluminium Co",     "sector": "Metals", "industry": "Aluminium"},

    # ── Realty ──────────────────────────────────────────────────────────
    "DLF":        {"name": "DLF",                       "sector": "Realty", "industry": "Real Estate"},
    "GODREJPROP": {"name": "Godrej Properties",         "sector": "Realty", "industry": "Real Estate"},
    "OBEROIRLTY": {"name": "Oberoi Realty",             "sector": "Realty", "industry": "Real Estate"},
    "PRESTIGE":   {"name": "Prestige Estates",          "sector": "Realty", "industry": "Real Estate"},
    "BRIGADE":    {"name": "Brigade Enterprises",       "sector": "Realty", "industry": "Real Estate"},
    "PHOENIXLTD": {"name": "Phoenix Mills",             "sector": "Realty", "industry": "Real Estate"},

    # ── Financial Services / NBFC ────────────────────────────────────────
    "BAJFINANCE": {"name": "Bajaj Finance",             "sector": "Financial Services", "industry": "Consumer Finance"},
    "BAJAJFINSV": {"name": "Bajaj Finserv",             "sector": "Financial Services", "industry": "Financial Conglomerate"},
    "HDFCLIFE":   {"name": "HDFC Life Insurance",       "sector": "Financial Services", "industry": "Life Insurance"},
    "SBILIFE":    {"name": "SBI Life Insurance",        "sector": "Financial Services", "industry": "Life Insurance"},
    "ICICIPRULI": {"name": "ICICI Pru Life Insurance",  "sector": "Financial Services", "industry": "Life Insurance"},
    "MUTHOOTFIN": {"name": "Muthoot Finance",           "sector": "Financial Services", "industry": "Gold Loan NBFC"},

    # ── Telecom ─────────────────────────────────────────────────────────
    "BHARTIARTL": {"name": "Bharti Airtel",             "sector": "Telecom", "industry": "Telecom Services"},
    "INDUSTOWER": {"name": "Indus Towers",              "sector": "Telecom", "industry": "Tower Infrastructure"},

    # ── Infrastructure & Conglomerates ──────────────────────────────────
    "LT":         {"name": "Larsen & Toubro",           "sector": "Infrastructure", "industry": "Engineering & Construction"},
    "ULTRACEMCO": {"name": "UltraTech Cement",          "sector": "Infrastructure", "industry": "Cement"},
    "GRASIM":     {"name": "Grasim Industries",         "sector": "Infrastructure", "industry": "Diversified"},
    "ADANIPORTS": {"name": "Adani Ports & SEZ",         "sector": "Infrastructure", "industry": "Ports"},
    "ASIANPAINT": {"name": "Asian Paints",              "sector": "Infrastructure", "industry": "Paints"},
    "TITAN":      {"name": "Titan Company",             "sector": "Consumer", "industry": "Jewellery & Watches"},
    "DMART":      {"name": "Avenue Supermarts (DMart)", "sector": "Consumer", "industry": "Retail"},
    "TATACONSUM": {"name": "Tata Consumer Products",    "sector": "FMCG", "industry": "Food & Beverages"},
    "PIDILITIND": {"name": "Pidilite Industries",       "sector": "Consumer", "industry": "Adhesives"},
}

# ─── SECTOR → TICKERS MAPPING (mirrors the spec exactly) ───────────────────
SECTOR_CONSTITUENTS: dict[str, list[str]] = {
    "IT":      ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM"],
    "Banking": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK"],
    "Auto":    ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "EICHERMOT"],
    "Pharma":  ["SUNPHARMA", "DIVISLAB", "CIPLA", "DRREDDY", "APOLLOHOSP"],
    "Energy":  ["RELIANCE", "ONGC", "NTPC", "POWERGRID", "COALINDIA"],
    "FMCG":    ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR"],
    "Metals":  ["TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "SAIL"],
    "Realty":  ["DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "BRIGADE"],
}

def search_universe(query: str, max_results: int = 8) -> list[dict]:
    """
    Case-insensitive substring search across symbol and company name.
    Returns a list of dicts with symbol + metadata, up to max_results.
    """
    q = query.upper().strip()
    results = []
    for symbol, meta in STOCK_UNIVERSE.items():
        if q in symbol.upper() or q in meta["name"].upper():
            results.append({"symbol": symbol, **meta})
        if len(results) >= max_results:
            break
    return results
