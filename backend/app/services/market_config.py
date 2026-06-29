"""
Market configuration — minimum stock purchase units per market.

Each market has different conventions for minimum tradable lots:
  US     : 1 share (no lot restrictions)
  HK     : lot_size varies per stock (default 100); e.g. HSBC=400, Tencent=100
  CN     : 100 shares (round lot for A-shares)
  JP     : 100 shares (standard lot for TSE)
  CRYPTO : varies per symbol (BTC=0.0001, ETH=0.001, stablecoins=1, most others=1)
"""

from decimal import Decimal, ROUND_DOWN
import math

# ── Default lot sizes per market ──────────────────────────────

DEFAULT_LOT_SIZE: dict[str, int] = {
    "US": 1,
    "HK": 100,
    "CN": 100,
    "JP": 100,
    "CRYPTO": 1,  # per-token default; overridden below for specific symbols
}

# ── Known stock-specific lot sizes (Hong Kong) ────────────────
# Keyed by symbol suffix or exact symbol (uppercase).
# Sources: HKEX listing rules, broker feeds.

HK_LOT_OVERRIDES: dict[str, int] = {
    # Major HK stocks with non-standard lot sizes
    "00005": 400,  # HSBC Holdings
    "00011": 100,  # Hang Seng Bank
    "00001": 500,  # CK Hutchison
    "00002": 500,  # CLP Holdings
    "00003": 1000, # Hong Kong and China Gas
    "00006": 500,  # Power Assets
    "00012": 1000, # Henderson Land
    "00016": 500,  # SHK Properties
    "00027": 500,  # Galaxy Entertainment
    "00066": 500,  # MTR Corporation
    "00083": 500,  # Sino Land
    "00101": 500,  # Hang Lung Properties
    "00241": 1000, # Alibaba Health
    "00267": 1000, # CITIC
    "00288": 1000, # WH Group
    "00388": 100,  # HKEX (its own lot)
    "00700": 100,  # Tencent
    "00823": 500,  # Link REIT
    "00941": 500,  # China Mobile
    "01299": 100,  # AIA Group
    "01810": 200,  # Xiaomi
    "02018": 100,  # AAC Tech
    "02020": 100,  # ANTA Sports
    "02318": 500,  # Ping An
    "02382": 100,  # Sunny Optical
    "02388": 500,  # BOC Hong Kong
    "02628": 1000, # China Life
    "02903": 100,  # HSBC - various line items
    "03690": 100,  # Meituan
    "03888": 500,  # Kingsoft
    "03988": 1000, # Bank of China
    "06160": 100,  # BeiGene (HK listing)
    "09618": 100,  # JD.com (HK listing)
    "09626": 100,  # NetEase (HK listing)
    "09888": 100,  # Baidu (HK listing)
    "09988": 100,  # Alibaba (HK listing)
    "09999": 100,  # NetEase (HK listing)
}

# ── Cryptocurrency minimum trade sizes ────────────────────────
# These represent the minimum *tradable* unit on most exchanges

CRYPTO_MIN_UNITS: dict[str, Decimal] = {
    "BTC": Decimal("0.00001"),
    "ETH": Decimal("0.001"),
    "BNB": Decimal("0.01"),
    "SOL": Decimal("0.01"),
    "XRP": Decimal("0.1"),
    "ADA": Decimal("1"),
    "DOGE": Decimal("1"),
    "USDT": Decimal("1"),
    "USDC": Decimal("1"),
    "DAI": Decimal("1"),
    "BUSD": Decimal("1"),
    "TRX": Decimal("1"),
    "MATIC": Decimal("0.1"),
    "DOT": Decimal("0.01"),
    "AVAX": Decimal("0.01"),
    "LINK": Decimal("0.01"),
    "UNI": Decimal("0.01"),
    "ATOM": Decimal("0.01"),
    "LTC": Decimal("0.01"),
    "BCH": Decimal("0.001"),
    "XLM": Decimal("1"),
    "VET": Decimal("1"),
    "FIL": Decimal("0.01"),
    "APT": Decimal("0.01"),
    "SUI": Decimal("0.01"),
    "ARB": Decimal("0.1"),
    "OP": Decimal("0.1"),
    "NEAR": Decimal("0.1"),
}


def get_lot_size(market: str, symbol: str, default: int | None = None) -> int:
    """
    Return the minimum lot size (whole integer shares) for a given (market, symbol).

    For US/CN/JP markets, this is typically a fixed integer.
    For HK market, we look up known overrides; falling back to the default (100).
    For CRYPTO, the lot size is *always* 1 because crypto fractions are handled
    separately via ``get_crypto_min_unit()``.

    Parameters
    ----------
    market : str
        One of US, HK, CN, JP, CRYPTO (case-insensitive).
    symbol : str
        Stock symbol (used for HK overrides).
    default : int or None
        Fallback when market is unknown. If None, uses DEFAULT_LOT_SIZE.

    Returns
    -------
    int
        Minimum integer share quantity for a round lot.
    """
    market = market.upper().strip()

    if market == "CRYPTO":
        return 1  # crypto uses fractional units, not integer lots

    if market == "HK":
        # Strip exchange suffix (e.g. "00005.HK" → "00005")
        base_symbol = symbol.upper().strip()
        for suffix in (".HK", ".T", " HK"):
            if base_symbol.endswith(suffix):
                base_symbol = base_symbol[: -len(suffix)]

        if base_symbol in HK_LOT_OVERRIDES:
            return HK_LOT_OVERRIDES[base_symbol]

    if market in DEFAULT_LOT_SIZE:
        return DEFAULT_LOT_SIZE[market]

    if default is not None:
        return int(default)

    return 1  # safest fallback


def get_crypto_min_unit(symbol: str) -> Decimal:
    """
    Return the minimum tradable unit for a cryptocurrency symbol.

    This is the smallest *fractional* unit that can be traded (e.g. 0.0001 BTC).
    For integer-lot crypto (most tokens), this returns Decimal(1).

    Parameters
    ----------
    symbol : str
        Cryptocurrency symbol (e.g. "BTC", "ETH").

    Returns
    -------
    Decimal
        Minimum trade increment.
    """
    sym = symbol.upper().strip()
    return CRYPTO_MIN_UNITS.get(sym, Decimal("1"))


def round_to_lot(qty_float: Decimal, lot_size: int, round_down: bool = True) -> Decimal:
    """
    Round a share quantity to a valid whole lot.

    Parameters
    ----------
    qty_float : Decimal
        The calculated (possibly fractional) share quantity.
    lot_size : int
        The minimum lot size for this instrument (1, 100, 400, etc.).
    round_down : bool
        If True (default), floor to nearest lot (for buys where we can't
        exceed capital). If False, ceil to nearest lot (for sells where
        we must sell whole lots).

    Returns
    -------
    Decimal
        ``qty_float`` rounded to the nearest integer multiple of ``lot_size``.
    """
    if lot_size <= 1:
        # No lot restrictions; return integer floor for buys, ceil for sells
        if round_down:
            return Decimal(str(int(qty_float)))
        else:
            # Round up for sells
            return Decimal(str(int(qty_float))) if qty_float == int(qty_float) else Decimal(str(int(qty_float) + 1))

    lots = qty_float / Decimal(str(lot_size))
    if round_down:
        lots = int(lots)  # floor
    else:
        lots = math.ceil(float(lots))  # ceil — sell must clear the position
    return Decimal(str(int(lots * lot_size)))


def get_min_units(market: str, symbol: str) -> Decimal:
    """
    Return the minimum purchasable unit expressed as a Decimal.

    For integer-lot markets (US, HK, CN, JP) this is an integer equal to
    the lot size. For crypto this is the fractional minimum unit
    (e.g. 0.00001 for BTC).
    """
    market = market.upper().strip()
    if market == "CRYPTO":
        return get_crypto_min_unit(symbol)
    return Decimal(str(get_lot_size(market, symbol)))
