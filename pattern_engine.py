"""
PATTERN ENGINE - MAJOR SWING + CONFIRMATION
============================================

Standalone engine for OHLC market data.

Design:
    OHLC
      -> major swing detection
      -> pattern structure detection
      -> breakout / candle-close confirmation
      -> quality score
      -> standardized results

Patterns:
    Double Top / Bottom
    Triple Top / Bottom
    Head & Shoulders / Inverse
    Ascending / Descending / Symmetrical Triangle
    Rising / Falling Wedge
    Rectangle
    Bull / Bear Flag
    Bull / Bear Pennant
    Cup & Handle
    Rounding Bottom
    Channel
    Diamond

No look-ahead is used for confirmation: the last closed candle is used.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import math

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

@dataclass
class EngineConfig:
    pivot_left: int = 3
    pivot_right: int = 3
    min_swings: int = 5
    max_swings: int = 18

    # Swing significance
    min_swing_pct: float = 0.004

    # Pattern tolerances
    level_tolerance: float = 0.025
    tight_level_tolerance: float = 0.018
    neckline_tolerance: float = 0.035

    # Confirmation
    breakout_buffer: float = 0.001
    min_confidence: int = 60

    # Avoid treating tiny ranges as patterns
    min_pattern_range_pct: float = 0.01


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _safe_float(x) -> Optional[float]:
    try:
        value = float(x)
        return value if math.isfinite(value) else None
    except Exception:
        return None


def _norm_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    mapping = {str(c).lower().strip(): c for c in out.columns}

    aliases = {
        "open": ["open", "o"],
        "high": ["high", "h"],
        "low": ["low", "l"],
        "close": ["close", "c"],
        "volume": ["volume", "vol"],
    }

    rename = {}
    for target, names in aliases.items():
        for name in names:
            if name in mapping:
                rename[mapping[name]] = target
                break

    out = out.rename(columns=rename)

    required = {"high", "low", "close"}
    missing = required - set(out.columns)
    if missing:
        raise ValueError(f"Missing OHLC columns: {sorted(missing)}")

    for c in ["high", "low", "close"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    if "open" not in out:
        out["open"] = out["close"].shift(1)

    if "volume" not in out:
        out["volume"] = np.nan

    return out.dropna(subset=["high", "low", "close"]).reset_index(drop=True)


def _pct(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1e-12)


def _same_level(a: float, b: float, tolerance: float) -> bool:
    return _pct(a, b) <= tolerance


def _line_value(p1: Tuple[int, float], p2: Tuple[int, float], x: int) -> float:
    i1, y1 = p1
    i2, y2 = p2
    if i2 == i1:
        return float(y1)
    return float(y1 + (y2 - y1) * ((x - i1) / (i2 - i1)))


def _slope(p1: Tuple[int, float], p2: Tuple[int, float]) -> float:
    if p2[0] == p1[0]:
        return 0.0
    return (p2[1] - p1[1]) / (p2[0] - p1[0])


# ---------------------------------------------------------------------
# Major Swing Scanner
# ---------------------------------------------------------------------

def find_major_swings(
    df: pd.DataFrame,
    config: EngineConfig,
) -> List[Dict]:
    """
    Detect local pivots and remove nearby/insignificant pivots.

    A pivot is only accepted when its left/right neighborhood confirms it.
    This intentionally uses closed historical candles, not future candles
    after the analysis point.
    """
    highs = df["high"].to_numpy(dtype=float)
    lows = df["low"].to_numpy(dtype=float)
    n = len(df)

    L = max(1, int(config.pivot_left))
    R = max(1, int(config.pivot_right))

    raw: List[Dict] = []

    for i in range(L, n - R):
        h = highs[i]
        l = lows[i]

        left_h = highs[i-L:i]
        right_h = highs[i+1:i+R+1]
        left_l = lows[i-L:i]
        right_l = lows[i+1:i+R+1]

        is_high = h >= np.max(left_h) and h >= np.max(right_h)
        is_low = l <= np.min(left_l) and l <= np.min(right_l)

        if is_high:
            raw.append({"index": i, "price": h, "type": "H"})
        if is_low:
            raw.append({"index": i, "price": l, "type": "L"})

    raw.sort(key=lambda x: x["index"])

    # Remove same-type nearby pivots and insignificant movement.
    filtered: List[Dict] = []
    last_price = None

    for p in raw:
        if not filtered:
            filtered.append(p)
            last_price = p["price"]
            continue

        prev = filtered[-1]

        # Same type: keep the more extreme pivot.
        if p["type"] == prev["type"]:
            if p["type"] == "H" and p["price"] >= prev["price"]:
                filtered[-1] = p
                last_price = p["price"]
            elif p["type"] == "L" and p["price"] <= prev["price"]:
                filtered[-1] = p
                last_price = p["price"]
            continue

        move = abs(p["price"] - prev["price"]) / max(abs(prev["price"]), 1e-12)
        if move >= config.min_swing_pct:
            filtered.append(p)
            last_price = p["price"]

    # Alternation cleanup.
    clean: List[Dict] = []
    for p in filtered:
        if not clean:
            clean.append(p)
            continue

        if p["type"] == clean[-1]["type"]:
            if p["type"] == "H":
                if p["price"] > clean[-1]["price"]:
                    clean[-1] = p
            else:
                if p["price"] < clean[-1]["price"]:
                    clean[-1] = p
        else:
            clean.append(p)

    return clean[-config.max_swings:]


# ---------------------------------------------------------------------
# Result format
# ---------------------------------------------------------------------

def _result(
    pattern: str,
    status: str,
    direction: str,
    confidence: int,
    *,
    swings=None,
    neckline=None,
    resistance=None,
    support=None,
    entry=None,
    stop_loss=None,
    target=None,
    invalidation=None,
    reason="",
) -> Dict:
    return {
        "pattern": pattern,
        "status": status,
        "direction": direction,
        "confidence": int(max(0, min(100, confidence))),
        "swings": swings or [],
        "neckline": neckline,
        "resistance": resistance,
        "support": support,
        "entry": entry,
        "stop_loss": stop_loss,
        "target": target,
        "invalidation": invalidation,
        "reason": reason,
    }


def _confirmed_breakout(
    close: float,
    level: float,
    direction: str,
    buffer: float,
) -> bool:
    if direction == "BULLISH":
        return close > level * (1 + buffer)
    return close < level * (1 - buffer)


def _trade_levels(
    direction: str,
    entry: float,
    reference: float,
    target_distance: float,
) -> Tuple[float, float]:
    if direction == "BULLISH":
        stop = min(reference, entry - target_distance * 0.35)
        target = entry + target_distance
    else:
        stop = max(reference, entry + target_distance * 0.35)
        target = entry - target_distance
    return stop, target


# ---------------------------------------------------------------------
# Individual detectors
# ---------------------------------------------------------------------

def detect_double_top(sw: List[Dict], close: float, cfg: EngineConfig):
    if len(sw) < 3:
        return None
    s = sw[-3:]
    if [x["type"] for x in s] != ["H", "L", "H"]:
        return None

    h1, valley, h2 = s
    if not _same_level(h1["price"], h2["price"], cfg.tight_level_tolerance):
        return None
    if valley["price"] >= min(h1["price"], h2["price"]) * (1 - cfg.min_pattern_range_pct):
        return None

    neckline = valley["price"]
    rng = max(h1["price"], h2["price"]) - neckline
    confirmed = _confirmed_breakout(close, neckline, "BEARISH", cfg.breakout_buffer)
    conf = 78 if confirmed else 66

    if confirmed:
        sl, tp = _trade_levels("BEARISH", close, max(h1["price"], h2["price"]), rng)
        return _result(
            "Double Top", "CONFIRMED", "BEARISH", conf,
            swings=s, neckline=neckline, entry=close,
            stop_loss=sl, target=tp, invalidation=max(h1["price"], h2["price"]),
            reason="Two major highs are near the same level and the neckline has closed below.",
        )

    return _result(
        "Double Top", "FORMING", "BEARISH", conf,
        swings=s, neckline=neckline,
        invalidation=max(h1["price"], h2["price"]),
        reason="Structure is present; waiting for a candle close below the neckline.",
    )


def detect_double_bottom(sw: List[Dict], close: float, cfg: EngineConfig):
    if len(sw) < 3:
        return None
    s = sw[-3:]
    if [x["type"] for x in s] != ["L", "H", "L"]:
        return None

    l1, peak, l2 = s
    if not _same_level(l1["price"], l2["price"], cfg.tight_level_tolerance):
        return None
    if peak["price"] <= max(l1["price"], l2["price"]) * (1 + cfg.min_pattern_range_pct):
        return None

    neckline = peak["price"]
    rng = neckline - min(l1["price"], l2["price"])
    confirmed = _confirmed_breakout(close, neckline, "BULLISH", cfg.breakout_buffer)
    conf = 78 if confirmed else 66

    if confirmed:
        sl, tp = _trade_levels("BULLISH", close, min(l1["price"], l2["price"]), rng)
        return _result(
            "Double Bottom", "CONFIRMED", "BULLISH", conf,
            swings=s, neckline=neckline, entry=close,
            stop_loss=sl, target=tp, invalidation=min(l1["price"], l2["price"]),
            reason="Two major lows are near the same level and the neckline has closed above.",
        )

    return _result(
        "Double Bottom", "FORMING", "BULLISH", conf,
        swings=s, neckline=neckline,
        invalidation=min(l1["price"], l2["price"]),
        reason="Structure is present; waiting for a candle close above the neckline.",
    )


def detect_triple_top_bottom(sw: List[Dict], close: float, cfg: EngineConfig):
    if len(sw) < 5:
        return None
    s = sw[-5:]
    types = [x["type"] for x in s]

    if types == ["H", "L", "H", "L", "H"]:
        highs = [s[0]["price"], s[2]["price"], s[4]["price"]]
        lows = [s[1]["price"], s[3]["price"]]
        if max(highs) - min(highs) <= np.mean(highs) * cfg.level_tolerance:
            neckline = min(lows)
            rng = np.mean(highs) - neckline
            confirmed = _confirmed_breakout(close, neckline, "BEARISH", cfg.breakout_buffer)
            return _result(
                "Triple Top",
                "CONFIRMED" if confirmed else "FORMING",
                "BEARISH",
                82 if confirmed else 67,
                swings=s, neckline=neckline,
                entry=close if confirmed else None,
                stop_loss=(close + rng * .35) if confirmed else None,
                target=(close - rng) if confirmed else None,
                invalidation=max(highs),
                reason="Three major highs cluster at a similar resistance level.",
            )

    if types == ["L", "H", "L", "H", "L"]:
        lows = [s[0]["price"], s[2]["price"], s[4]["price"]]
        highs = [s[1]["price"], s[3]["price"]]
        if max(lows) - min(lows) <= np.mean(lows) * cfg.level_tolerance:
            neckline = max(highs)
            rng = neckline - np.mean(lows)
            confirmed = _confirmed_breakout(close, neckline, "BULLISH", cfg.breakout_buffer)
            return _result(
                "Triple Bottom",
                "CONFIRMED" if confirmed else "FORMING",
                "BULLISH",
                82 if confirmed else 67,
                swings=s, neckline=neckline,
                entry=close if confirmed else None,
                stop_loss=(close - rng * .35) if confirmed else None,
                target=(close + rng) if confirmed else None,
                invalidation=min(lows),
                reason="Three major lows cluster at a similar support level.",
            )

    return None


def detect_head_shoulders(sw: List[Dict], close: float, cfg: EngineConfig):
    if len(sw) < 5:
        return None
    s = sw[-5:]
    if [x["type"] for x in s] != ["H", "L", "H", "L", "H"]:
        return None

    ls, nl1, head, nl2, rs = s

    head_is_higher = head["price"] > ls["price"] and head["price"] > rs["price"]
    shoulders_similar = _same_level(
        ls["price"], rs["price"], cfg.level_tolerance
    )
    if not (head_is_higher and shoulders_similar):
        return None

    neckline = (nl1["price"] + nl2["price"]) / 2
    confirmed = _confirmed_breakout(close, neckline, "BEARISH", cfg.breakout_buffer)
    rng = head["price"] - neckline

    return _result(
        "Head & Shoulders",
        "CONFIRMED" if confirmed else "FORMING",
        "BEARISH",
        86 if confirmed else 72,
        swings=s, neckline=neckline,
        entry=close if confirmed else None,
        stop_loss=(head["price"]) if confirmed else None,
        target=(close - rng) if confirmed else None,
        invalidation=head["price"],
        reason="Head is above both shoulders and the neckline is used for confirmation.",
    )


def detect_inverse_head_shoulders(sw: List[Dict], close: float, cfg: EngineConfig):
    if len(sw) < 5:
        return None
    s = sw[-5:]
    if [x["type"] for x in s] != ["L", "H", "L", "H", "L"]:
        return None

    ls, nl1, head, nl2, rs = s

    head_is_lower = head["price"] < ls["price"] and head["price"] < rs["price"]
    shoulders_similar = _same_level(
        ls["price"], rs["price"], cfg.level_tolerance
    )
    if not (head_is_lower and shoulders_similar):
        return None

    neckline = (nl1["price"] + nl2["price"]) / 2
    confirmed = _confirmed_breakout(close, neckline, "BULLISH", cfg.breakout_buffer)
    rng = neckline - head["price"]

    return _result(
        "Inverse Head & Shoulders",
        "CONFIRMED" if confirmed else "FORMING",
        "BULLISH",
        86 if confirmed else 72,
        swings=s, neckline=neckline,
        entry=close if confirmed else None,
        stop_loss=head["price"] if confirmed else None,
        target=(close + rng) if confirmed else None,
        invalidation=head["price"],
        reason="Head is below both shoulders and the neckline is used for confirmation.",
    )


def detect_triangles(sw: List[Dict], close: float, cfg: EngineConfig):
    if len(sw) < 6:
        return None

    s = sw[-6:]
    highs = [x for x in s if x["type"] == "H"]
    lows = [x for x in s if x["type"] == "L"]

    if len(highs) < 3 or len(lows) < 3:
        return None

    hs = _slope((highs[0]["index"], highs[0]["price"]),
                (highs[-1]["index"], highs[-1]["price"]))
    ls = _slope((lows[0]["index"], lows[0]["price"]),
                (lows[-1]["index"], lows[-1]["price"]))

    last_h = highs[-1]["price"]
    last_l = lows[-1]["price"]

    # Flat resistance + rising lows.
    h_flat = abs(hs) <= np.mean([x["price"] for x in highs]) * 0.0025
    l_up = ls > 0

    if h_flat and l_up:
        resistance = np.mean([x["price"] for x in highs])
        confirmed = _confirmed_breakout(close, resistance, "BULLISH", cfg.breakout_buffer)
        return _result(
            "Ascending Triangle",
            "CONFIRMED" if confirmed else "FORMING",
            "BULLISH",
            82 if confirmed else 68,
            swings=s, resistance=resistance,
            entry=close if confirmed else None,
            reason="Flat resistance with rising major lows.",
        )

    # Flat support + falling highs.
    l_flat = abs(ls) <= np.mean([x["price"] for x in lows]) * 0.0025
    h_down = hs < 0

    if l_flat and h_down:
        support = np.mean([x["price"] for x in lows])
        confirmed = _confirmed_breakout(close, support, "BEARISH", cfg.breakout_buffer)
        return _result(
            "Descending Triangle",
            "CONFIRMED" if confirmed else "FORMING",
            "BEARISH",
            82 if confirmed else 68,
            swings=s, support=support,
            entry=close if confirmed else None,
            reason="Flat support with falling major highs.",
        )

    # Converging highs/lows.
    if hs < 0 and ls > 0:
        upper = _line_value(
            (highs[0]["index"], highs[0]["price"]),
            (highs[-1]["index"], highs[-1]["price"]),
            len(s) + highs[-1]["index"] - s[0]["index"],
        )
        lower = _line_value(
            (lows[0]["index"], lows[0]["price"]),
            (lows[-1]["index"], lows[-1]["price"]),
            len(s) + lows[-1]["index"] - s[0]["index"],
        )

        if lower < close < upper:
            return _result(
                "Symmetrical Triangle",
                "FORMING",
                "NEUTRAL",
                65,
                swings=s, resistance=upper, support=lower,
                reason="Major highs are falling while major lows are rising.",
            )

    return None


def detect_wedges(sw: List[Dict], close: float, cfg: EngineConfig):
    if len(sw) < 6:
        return None

    s = sw[-6:]
    highs = [x for x in s if x["type"] == "H"]
    lows = [x for x in s if x["type"] == "L"]

    if len(highs) < 3 or len(lows) < 3:
        return None

    hs = _slope((highs[0]["index"], highs[0]["price"]),
                (highs[-1]["index"], highs[-1]["price"]))
    ls = _slope((lows[0]["index"], lows[0]["price"]),
                (lows[-1]["index"], lows[-1]["price"]))

    avg = np.mean([x["price"] for x in s])

    if hs > 0 and ls > 0 and ls > hs * 0.75:
        support = _line_value(
            (lows[0]["index"], lows[0]["price"]),
            (lows[-1]["index"], lows[-1]["price"]),
            len(s) + lows[-1]["index"] - s[0]["index"],
        )
        confirmed = _confirmed_breakout(close, support, "BEARISH", cfg.breakout_buffer)
        return _result(
            "Rising Wedge",
            "CONFIRMED" if confirmed else "FORMING",
            "BEARISH",
            80 if confirmed else 64,
            swings=s, support=support,
            entry=close if confirmed else None,
            reason="Both boundaries rise and converge; downside break confirms.",
        )

    if hs < 0 and ls < 0 and hs < ls * 0.75:
        resistance = _line_value(
            (highs[0]["index"], highs[0]["price"]),
            (highs[-1]["index"], highs[-1]["price"]),
            len(s) + highs[-1]["index"] - s[0]["index"],
        )
        confirmed = _confirmed_breakout(close, resistance, "BULLISH", cfg.breakout_buffer)
        return _result(
            "Falling Wedge",
            "CONFIRMED" if confirmed else "FORMING",
            "BULLISH",
            80 if confirmed else 64,
            swings=s, resistance=resistance,
            entry=close if confirmed else None,
            reason="Both boundaries fall and converge; upside break confirms.",
        )

    return None


def detect_rectangle(sw: List[Dict], close: float, cfg: EngineConfig):
    if len(sw) < 6:
        return None

    s = sw[-6:]
    highs = [x["price"] for x in s if x["type"] == "H"]
    lows = [x["price"] for x in s if x["type"] == "L"]

    if len(highs) < 3 or len(lows) < 3:
        return None

    resistance = np.mean(highs)
    support = np.mean(lows)

    if resistance <= support:
        return None

    if (
        max(highs) - min(highs) <= resistance * cfg.level_tolerance
        and max(lows) - min(lows) <= support * cfg.level_tolerance
    ):
        up = _confirmed_breakout(close, resistance, "BULLISH", cfg.breakout_buffer)
        down = _confirmed_breakout(close, support, "BEARISH", cfg.breakou
