"""
PATTERN ENGINE - CURRENT ACTIVE PATTERN ONLY
============================================

Purpose
-------
This engine does NOT scan the whole chart and keep old patterns alive.

Rules:
1. Only the latest major-swing structure is considered.
2. Old/completed patterns are ignored.
3. A pattern whose entry/breakout has already been passed is not returned
   as an ACTIVE opportunity.
4. If several patterns are currently possible, they are ranked by quality.
5. get_best_pattern() returns the strongest CURRENT opportunity.
6. No forced pattern: geometry must pass strict structure tests.
7. The returned dictionaries keep the existing app interface:
   name, direction, quality, status, reason, entry, tp1, tp2, sl, points.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import math
import numpy as np
import pandas as pd


# -----------------------------
# SETTINGS
# -----------------------------
RECENT_SWINGS = 8
ENTRY_TOLERANCE = 0.0025       # 0.25%
LEVEL_TOLERANCE = 0.012        # 1.2%
DOUBLE_TOLERANCE = 0.018       # 1.8%
TRIPLE_TOLERANCE = 0.022       # 2.2%
SHOULDER_TOLERANCE = 0.035     # 3.5%
MIN_PATTERN_SCORE = 58
MAX_RETURNED = 5


# -----------------------------
# HELPERS
# -----------------------------
def _num(x: Any) -> Optional[float]:
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None


def _norm_name(name: Any) -> str:
    return str(name or "").strip().lower().replace("_", " ").replace("-", " ")


def _swing_type(s: Any) -> Optional[str]:
    if not isinstance(s, dict):
        return None

    raw = (
        s.get("type")
        or s.get("kind")
        or s.get("structure")
        or s.get("label")
        or s.get("point_type")
    )
    if raw is None:
        return None

    n = _norm_name(raw)

    if "high" in n or n in {"hh", "lh"}:
        return "high"
    if "low" in n or n in {"hl", "ll"}:
        return "low"
    return None


def _swing_index(s: Any, fallback: int) -> int:
    if isinstance(s, dict):
        for k in ("index", "idx", "bar", "position"):
            if k in s:
                try:
                    return int(s[k])
                except Exception:
                    pass
    return fallback


def _swing_price(s: Any) -> Optional[float]:
    if not isinstance(s, dict):
        return None
    for k in ("price", "value", "high", "low", "close"):
        v = _num(s.get(k))
        if v is not None:
            return v
    return None


def _extract_swings(df: pd.DataFrame) -> List[Dict[str, Any]]:
    raw = df.attrs.get("major_swings", [])

    if isinstance(raw, pd.DataFrame):
        records = raw.to_dict("records")
    elif isinstance(raw, (list, tuple)):
        records = list(raw)
    else:
        records = []

    out = []
    for i, s in enumerate(records):
        price = _swing_price(s)
        typ = _swing_type(s)
        if price is None or typ is None:
            continue

        out.append({
            "type": typ,
            "price": price,
            "index": _swing_index(s, i),
        })

    out.sort(key=lambda x: x["index"])
    return out


def _point(name: str, s: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": name,
        "index": int(s["index"]),
        "price": float(s["price"]),
        "type": s["type"],
    }


def _last_close(df: pd.DataFrame) -> float:
    return float(df["close"].iloc[-1])


def _atr(df: pd.DataFrame) -> float:
    if len(df) < 15:
        return float(df["close"].iloc[-1]) * 0.01

    h = df["high"].astype(float)
    l = df["low"].astype(float)
    c = df["close"].astype(float)
    prev = c.shift(1)

    tr = pd.concat([
        h - l,
        (h - prev).abs(),
        (l - prev).abs(),
    ], axis=1).max(axis=1)

    a = tr.rolling(14).mean().iloc[-1]
    if pd.isna(a) or a <= 0:
        return float(c.iloc[-1]) * 0.01
    return float(a)


def _levels(df: pd.DataFrame) -> Dict[str, float]:
    close = _last_close(df)
    atr = _atr(df)

    recent = df.tail(80)
    high = float(recent["high"].max())
    low = float(recent["low"].min())

    return {
        "close": close,
        "atr": atr,
        "high": high,
        "low": low,
    }


def _entry_passed(direction: str, close: float, entry: float) -> bool:
    tol = max(abs(entry) * ENTRY_TOLERANCE, 1e-12)

    if direction == "BUY":
        return close >= entry + tol
    return close <= entry - tol


def _near_entry(direction: str, close: float, entry: float) -> bool:
    tol = max(abs(entry) * LEVEL_TOLERANCE, 1e-12)

    if direction == "BUY":
        return close <= entry + tol
    return close >= entry - tol


def _quality(base: float, geometry: float, recency: float, context: float) -> int:
    score = 0.45 * base + 0.25 * geometry + 0.15 * recency + 0.15 * context
    return int(max(0, min(100, round(score))))


def _context_score(df: pd.DataFrame, direction: str) -> float:
    if len(df) < 50:
        return 50.0

    close = df["close"].astype(float)
    ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    ema200 = close.ewm(span=200, adjust=False).mean().iloc[-1]
    last = close.iloc[-1]

    if direction == "BUY":
        if last > ema50 > ema200:
            return 100.0
        if last > ema50:
            return 75.0
        return 50.0

    if last < ema50 < ema200:
        return 100.0
    if last < ema50:
        return 75.0
    return 50.0


def _recency_score(swings: List[Dict[str, Any]], used: List[Dict[str, Any]]) -> float:
    if not swings or not used:
        return 50.0

    last_idx = swings[-1]["index"]
    pattern_last = max(p["index"] for p in used)
    distance = max(0, last_idx - pattern_last)

    if distance <= 1:
        return 100.0
    if distance <= 3:
        return 85.0
    if distance <= 6:
        return 70.0
    return 50.0


def _candidate(
    name: str,
    direction: str,
    quality: int,
    status: str,
    reason: str,
    entry: float,
    tp1: float,
    tp2: float,
    sl: float,
    points: List[Dict[str, Any]],
    used: List[Dict[str, Any]],
) -> Dict[str, Any]:

    return {
        "name": name,
        "direction": direction,
        "quality": int(quality),
        "status": status,
        "reason": reason,
        "entry": float(entry),
        "tp1": float(tp1),
        "tp2": float(tp2),
        "sl": float(sl),
        "points": points,
        "_used_indices": [p["index"] for p in used],
    }


# -----------------------------
# DOUBLE TOP / BOTTOM
# -----------------------------
def _double(sw: List[Dict[str, Any]], df: pd.DataFrame) -> List[Dict[str, Any]]:
    if len(sw) < 3:
        return []

    a, b, c = sw[-3], sw[-2], sw[-1]
    out = []
    lv = _levels(df)

    # Double Top: High - Low - High
    if [a["type"], b["type"], c["type"]] == ["high", "low", "high"]:
        similarity = abs(a["price"] - c["price"]) / max(a["price"], c["price"])
        if similarity <= DOUBLE_TOLERANCE:
            entry = b["price"]
            close = lv["close"]

            # Once price has already broken below neckline, this setup is gone.
            if not _entry_passed("SELL", close, entry):
                height = max(0.0, ((a["price"] + c["price"]) / 2) - entry)
                tp1 = entry - height * 0.65
                tp2 = entry - height
                sl = max(a["price"], c["price"]) + lv["atr"] * 0.35

                geometry = max(0.0, 100.0 - similarity * 1000.0)
                status = "READY" if _near_entry("SELL", close, entry) else "FORMING"
                q = _quality(86, geometry, _recency_score(sw, [a, b, c]),
                             _context_score(df, "SELL"))

                if q >= MIN_PATTERN_SCORE:
                    out.append(_candidate(
                        "Double Top", "SELL", q, status,
                        "Two major highs are aligned and the neckline is still active.",
                        entry, tp1, tp2, sl,
                        [_point("TOP 1", a), _point("NECKLINE", b), _point("TOP 2", c)],
                        [a, b, c],
                    ))

    # Double Bottom: Low - High - Low
    if [a["type"], b["type"], c["type"]] == ["low", "high", "low"]:
        similarity = abs(a["price"] - c["price"]) / max(a["price"], c["price"])
        if similarity <= DOUBLE_TOLERANCE:
            entry = b["price"]
            close = lv["close"]

            if not _entry_passed("BUY", close, entry):
                height = max(0.0, entry - ((a["price"] + c["price"]) / 2))
                tp1 = entry + height * 0.65
                tp2 = entry + height
                sl = min(a["price"], c["price"]) - lv["atr"] * 0.35

                geometry = max(0.0, 100.0 - similarity * 1000.0)
                status = "READY" if _near_entry("BUY", close, entry) else "FORMING"
                q = _quality(86, geometry, _recency_score(sw, [a, b, c]),
                             _context_score(df, "BUY"))

                if q >= MIN_PATTERN_SCORE:
                    out.append(_candidate(
                        "Double Bottom", "BUY", q, status,
                        "Two major lows are aligned and the neckline is still active.",
                        entry, tp1, tp2, sl,
                        [_point("BOTTOM 1", a), _point("NECKLINE", b), _point("BOTTOM 2", c)],
                        [a, b, c],
                    ))

    return out


# -----------------------------
# TRIPLE TOP / BOTTOM
# -----------------------------
def _triple(sw: List[Dict[str, Any]], df: pd.DataFrame) -> List[Dict[str, Any]]:
    if len(sw) < 5:
        return []

    a, b, c, d, e = sw[-5:]
    out = []
    lv = _levels(df)

    if [x["type"] for x in (a, b, c, d, e)] == ["high", "low", "high", "low", "high"]:
        highs = [a["price"], c["price"], e["price"]]
        mean = sum(highs) / 3
        spread = max(highs) - min(highs)

        if spread / mean <= TRIPLE_TOLERANCE:
            entry = min(b["price"], d["price"])
            close = lv["close"]

            if not _entry_passed("SELL", close, entry):
                height = mean - entry
                tp1 = entry - height * 0.65
                tp2 = entry - height
                sl = max(highs) + lv["atr"] * 0.35
                geometry = max(0.0, 100.0 - (spread / mean) * 900.0)
                status = "READY" if _near_entry("SELL", close, entry) else "FORMING"
                q = _quality(94, geometry, _recency_score(sw, [a, b, c, d, e]),
                             _context_score(df, "SELL"))

                if q >= MIN_PATTERN_SCORE:
                    out.append(_candidate(
                        "Triple Top", "SELL", q, status,
                        "Three major highs are aligned; the support neckline remains unbroken.",
                        entry, tp1, tp2, sl,
                        [_point("TOP 1", a), _point("NECKLINE 1", b),
                         _point("TOP 2", c), _point("NECKLINE 2", d),
                         _point("TOP 3", e)],
                        [a, b, c, d, e],
                    ))

    if [x["type"] for x in (a, b, c, d, e)] == ["low", "high", "low", "high", "low"]:
        lows = [a["price"], c["price"], e["price"]]
        mean = sum(lows) / 3
        spread = max(lows) - min(lows)

        if spread / mean <= TRIPLE_TOLERANCE:
            entry = max(b["price"], d["price"])
            close = lv["close"]

            if not _entry_passed("BUY", close, entry):
                height = entry - mean
                tp1 = entry + height * 0.65
                tp2 = entry + height
                sl = min(lows) - lv["atr"] * 0.35
                geometry = max(0.0, 100.0 - (spread / mean) * 900.0)
                status = "READY" if _near_entry("BUY", close, entry) else "FORMING"
                q = _quality(94, geometry, _recency_score(sw, [a, b, c, d, e]),
                             _context_score(df, "BUY"))

                if q >= MIN_PATTERN_SCORE:
                    out.append(_candidate(
                        "Triple Bottom", "BUY", q, status,
                        "Three major lows are aligned; the resistance neckline remains unbroken.",
                        entry, tp1, tp2, sl,
                        [_point("BOTTOM 1", a), _point("NECKLINE 1", b),
                         _point("BOTTOM 2", c), _point("NECKLINE 2", d),
                         _point("BOTTOM 3", e)],
                        [a, b, c, d, e],
                    ))

    return out


# -----------------------------
# HEAD & SHOULDERS
# -----------------------------
def _head_shoulders(sw: List[Dict[str, Any]], df: pd.DataFrame) -> List[Dict[str, Any]]:
    if len(sw) < 5:
        return []

    a, b, c, d, e = sw[-5:]
    out = []
    lv = _levels(df)

    # H&S: high-low-high-low-high
    if [x["type"] for x in (a, b, c, d, e)] == ["high", "low", "high", "low", "high"]:
        shoulder_avg = (a["price"] + e["price"]) / 2
        head = c["price"]

        if head > shoulder_avg * 1.015:
            shoulder_diff = abs(a["price"] - e["price"]) / shoulder_avg
            neck = (b["price"] + d["price"]) / 2

            if shoulder_diff <= SHOULDER_TOLERANCE:
                close = lv["close"]

                if not _entry_passed("SELL", close, neck):
                    height = head - neck
                    tp1 = neck - height * 0.65
                    tp2 = neck - height
                    sl = max(a["price"], e["price"]) + lv["atr"] * 0.35

                    geometry = max(
                        0.0,
                        100.0
                        - shoulder_diff * 1000.0
                        + min(20.0, (head / shoulder_avg - 1.0) * 500.0)
                    )
                    status = "READY" if _near_entry("SELL", close, neck) else "FORMING"
                    q = _quality(
                        97, geometry,
                        _recency_score(sw, [a, b, c, d, e]),
                        _context_score(df, "SELL")
                    )

                    if q >= MIN_PATTERN_SCORE:
                        out.append(_candidate(
                            "Head & Shoulders", "SELL", q, status,
                            "Left shoulder, higher head and right shoulder are structurally valid; neckline is still active.",
                            neck, tp1, tp2, sl,
                            [_point("LEFT SHOULDER", a), _point("NECKLINE 1", b),
                             _point("HEAD", c), _point("NECKLINE 2", d),
                             _point("RIGHT SHOULDER", e)],
                            [a, b, c, d, e],
                        ))

    # Inverse H&S: low-high-low-high-low
    if [x["type"] for x in (a, b, c, d, e)] == ["low", "high", "low", "high", "low"]:
        shoulder_avg = (a["price"] + e["price"]) / 2
        head = c["price"]

        if head < shoulder_avg * 0.985:
            shoulder_diff = abs(a["price"] - e["price"]) / max(abs(shoulder_avg), 1e-12)
            neck = (b["price"] + d["price"]) / 2

            if shoulder_diff <= SHOULDER_TOLERANCE:
                close = lv["close"]

                if not _entry_passed("BUY", close, neck):
                    height = neck - head
                    tp1 = neck + height * 0.65
                    tp2 = neck + height
                    sl = min(a["price"], e["price"]) - lv["atr"] * 0.35

                    geometry = max(
                        0.0,
                        100.0
                        - shoulder_diff * 1000.0
                        + min(20.0, (1.0 - head / shoulder_avg) * 500.0)
                    )
                    status = "READY" if _near_entry("BUY", close, neck) else "FORMING"
                    q = _quality(
                        97, geometry,
                        _recency_score(sw, [a, b, c, d, e]),
                        _context_score(df, "BUY")
                    )

                    if q >= MIN_PATTERN_SCORE:
                        out.append(_candidate(
                            "Inverse Head & Shoulders", "BUY", q, status,
                            "Left shoulder, lower head and right shoulder are structurally valid; neckline is still active.",
                            neck, tp1, tp2, sl,
                            [_point("LEFT SHOULDER", a), _point("NECKLINE 1", b),
                             _point("HEAD", c), _point("NECKLINE 2", d),
                             _point("RIGHT SHOULDER", e)],
                            [a, b, c, d, e],
                        ))

    return out


# -----------------------------
# TRIANGLES
# -----------------------------
def _triangles(sw: List[Dict[str, Any]], df: pd.DataFrame) -> List[Dict[str, Any]]:
    if len(sw) < 5:
        return []

    a, b, c, d, e = sw[-5:]
    out = []
    lv = _levels(df)

    if [x["type"] for x in (a, b, c, d, e)] != ["high", "low", "high", "low", "high"]:
        return out

    # Need descending highs and rising lows from the alternating structure.
    highs = [a["price"], c["price"], e["price"]]
    lows = [b["price"], d["price"]]

    descending_highs = highs[0] > highs[1] and highs[1] >= highs[2]
    rising_lows = lows[0] < lows[1]

    if descending_highs and rising_lows:
        # Symmetrical/contracting triangle.
        close = lv["close"]
        upper = highs[-1]
        lower = lows[-1]

        # Direction is not guessed from the old chart. Entry is the active
        # boundary that has NOT already been broken.
        upper_break = close > upper * (1 + ENTRY_TOLERANCE)
        lower_break = close < lower * (1 - ENTRY_TOLERANCE)

        if not upper_break and not lower_break:
            entry = upper
            height = max(upper - lower, lv["atr"])
            tp1 = upper + height * 0.65
            tp2 = upper + height
            sl = lower - lv["atr"] * 0.35

            compression = (upper - lower) / max(abs(upper), 1e-12)
            geometry = max(0.0, min(100.0, 100.0 - compression * 350.0))
            status = "READY" if _near_entry("BUY", close, entry) else "FORMING"
            q = _quality(78, geometry, _recency_score(sw, [a, b, c, d, e]),
                         _context_score(df, "BUY"))

            if q >= MIN_PATTERN_SCORE:
                out.append(_candidate(
                    "Symmetrical Triangle", "BUY", q, status,
                    "Contracting highs and rising lows are forming; upside entry is still active.",
                    entry, tp1, tp2, sl,
                    [_point("HIGH 1", a), _point("LOW 1", b),
                     _point("HIGH 2", c), _point("LOW 2", d),
                     _point("HIGH 3", e)],
                    [a, b, c, d, e],
                ))

    return out


# -----------------------------
# PUBLIC API
# -----------------------------
def _deduplicate(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Keep the strongest candidate when two detectors describe essentially
    the same last-swing structure.
    """
    result = []
    seen = set()

    priority = {
        "Head & Shoulders": 5,
        "Inverse Head & Shoulders": 5,
        "Triple Top": 4,
        "Triple Bottom": 4,
        "Double Top": 3,
        "Double Bottom": 3,
        "Symmetrical Triangle": 2,
    }

    candidates = sorted(
        candidates,
        key=lambda x: (x["quality"], priority.get(x["name"], 0)),
        reverse=True,
    )

    for p in candidates:
        key = tuple(p.get("_used_indices", []))
        if key in seen:
            continue

        # Same final swing range + same direction = likely duplicate geometry.
        overlap = False
        for old in result:
            old_idx = set(old.get("_used_indices", []))
            new_idx = set(p.get("_used_indices", []))
            if old_idx and new_idx:
                common = len(old_idx & new_idx)
                union = len(old_idx | new_idx)
                if union and common / union >= 0.75 and old["direction"] == p["direction"]:
                    overl
