"""
List of popular S&P 500 and tech stocks for analysis.

This module contains a curated list of 100 popular stocks
commonly used for market analysis and portfolio building.
"""

# S&P 500 Tech Giants and Mega-Cap Stocks
MEGA_CAP = [
    'AAPL',  # Apple
    'MSFT',  # Microsoft
    'GOOGL', # Alphabet (Google)
    'AMZN',  # Amazon
    'NVDA',  # NVIDIA
    'META',  # Meta Platforms
    'TSLA',  # Tesla
    'BRK.B', # Berkshire Hathaway
]

# Large Tech Companies
LARGE_TECH = [
    'NFLX',  # Netflix
    'ADBE',  # Adobe
    'INTC',  # Intel
    'AMD',   # Advanced Micro Devices
    'QCOM',  # Qualcomm
    'CRM',   # Salesforce
    'INTU',  # Intuit
    'SNPS',  # Synopsys
    'CDNS',  # Cadence Design
    'WDAY',  # Workday
    'CRWD',  # CrowdStrike
    'NOW',   # ServiceNow
]

# Financial Services
FINANCE = [
    'JPM',   # JPMorgan Chase
    'BAC',   # Bank of America
    'WFC',   # Wells Fargo
    'GS',    # Goldman Sachs
    'MS',    # Morgan Stanley
    'BLK',   # BlackRock
    'AMP',   # Ameriprise Financial
    'MKL',   # Markel Group
    'CME',   # CME Group
    'SCHW',  # Charles Schwab
]

# Healthcare & Biotech
HEALTHCARE = [
    'JNJ',   # Johnson & Johnson
    'UNH',   # UnitedHealth Group
    'PFE',   # Pfizer
    'ABBV',  # AbbVie
    'MRK',   # Merck
    'LLY',   # Eli Lilly
    'AMGN',  # Amgen
    'TMO',   # Thermo Fisher
    'GILD',  # Gilead Sciences
    'ISRG',  # Intuitive Surgical
    'DXCM',  # DexCom
    'VEEV',  # Veeva Systems
]

# Industrial & Manufacturing
INDUSTRIAL = [
    'BA',    # Boeing
    'CAT',   # Caterpillar
    'DE',    # Deere & Company
    'GE',    # General Electric
    'HON',   # Honeywell
    'ITT',   # ITT Inc
    'LMT',   # Lockheed Martin
    'RTX',   # Raytheon Technologies
]

# Consumer & Retail
CONSUMER = [
    'WMT',   # Walmart
    'TM',    # Toyota
    'HD',    # The Home Depot
    'MCD',   # McDonald's
    'NKE',   # Nike
    'SBUX',  # Starbucks
    'COST',  # Costco
    'LOW',   # Lowe's
    'TJX',   # TJX Companies
    'ULTA',  # Ulta Beauty
]

# Energy & Utilities
ENERGY = [
    'XOM',   # Exxon Mobil
    'CVX',   # Chevron
    'COP',   # ConocoPhillips
    'SLB',   # Schlumberger
    'MPC',   # Marathon Petroleum
    'PSX',   # Phillips 66
    'NEE',   # NextEra Energy
    'DUK',   # Duke Energy
    'SO',    # Southern Company
]

# Communications & Media
COMMUNICATIONS = [
    'T',     # AT&T
    'VZ',    # Verizon
    'CMCSA', # Comcast
    'DISH',  # DISH Network
    'DIS',   # Walt Disney
    'PARA',  # Paramount Global
    'FOX',   # Fox Corporation
]

# Other Sectors
OTHER = [
    'PG',    # Procter & Gamble
    'KO',    # The Coca-Cola Company
    'PEP',   # PepsiCo
    'AXP',   # American Express
    'V',     # Visa
    'MA',    # Mastercard
    'SPGI',  # S&P Global
    'MMC',   # Marsh & McLennan
    'CB',    # Chubb Limited
    'BDX',   # Becton, Dickinson
    'ABT',   # Abbott Laboratories
    'CTLT',  # Catalent (if available)
]

# S&P 500 Mid-Cap Representative
MIDCAP = [
    'PCTY',  # Paylocity
    'SSNC',  # SS&C Technologies
    'VRSN',  # VeriSign
    'OKTA',  # Okta
    'DDOG',  # Datadog
]

# All stocks combined (approximately 100)
ALL_STOCKS = (
    MEGA_CAP + LARGE_TECH + FINANCE + HEALTHCARE + INDUSTRIAL +
    CONSUMER + ENERGY + COMMUNICATIONS + OTHER + MIDCAP
)

# Remove duplicates and sort
ALL_STOCKS = sorted(list(set(ALL_STOCKS)))

# Ensure we have approximately 100
if len(ALL_STOCKS) > 100:
    ALL_STOCKS = ALL_STOCKS[:100]

# Dictionary for easy access by category
STOCK_CATEGORIES = {
    'mega_cap': MEGA_CAP,
    'large_tech': LARGE_TECH,
    'finance': FINANCE,
    'healthcare': HEALTHCARE,
    'industrial': INDUSTRIAL,
    'consumer': CONSUMER,
    'energy': ENERGY,
    'communications': COMMUNICATIONS,
    'other': OTHER,
    'midcap': MIDCAP,
}


def get_stocks_by_category(category: str) -> list:
    """Get stocks from a specific category."""
    return STOCK_CATEGORIES.get(category, [])


def get_all_stocks() -> list:
    """Get all stocks."""
    return ALL_STOCKS


def get_stock_count() -> int:
    """Get total number of stocks."""
    return len(ALL_STOCKS)


# Print summary
if __name__ == "__main__":
    print(f"Total stocks: {get_stock_count()}")
    print(f"Categories: {', '.join(STOCK_CATEGORIES.keys())}")
    print(f"\nAll stocks: {', '.join(ALL_STOCKS)}")
