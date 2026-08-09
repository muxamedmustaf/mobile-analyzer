# ============================================================
# MOBILE ANALYZER
# SIGNAL_ENGINE.PY
# PATTERN + STRUCTURE + EMA + RSI + ATR + BOS/CHOCH
# ============================================================

import math


# ============================================================
# HELPERS
# ============================================================

def _num(value, default=None):
    try:
        if value is None:
            return default

        value = float(value)

        if not math.isfinite(value):
            return default

        return value

    except Exception:
        return default


def _last_value(df, column):
    if df is None or df.empty or column not in df.columns:
        return None

    return _num(df[column].iloc[-1])


def _previous_value(df, column):
    if df is None or len(df) < 2 or column not in df.columns:
        return None

    return _num(df[column].iloc[-2])


def _is_bullish_pattern(pattern):
    return (
        pattern is not None
        and pattern.get("direction") == "BULLISH"
    )


def _is_bearish_pattern(pattern):
    return (
        pattern is not None
        and pattern.get("direction") == "BEARISH"
    )


# ============================================================
# EMA CONDITIONS
# ============================================================

def _ema_bullish(df):
    close = _last_value(df, "close")
    ema50 = _last_value(df, "EMA50")
    ema200 = _last_value(df, "EMA200")

    if None in (close, ema50, ema200):
        return False

    return (
        close > ema50
        and ema50 > ema200
    )


def _ema_bearish(df):
    close = _last_value(df, "close")
    ema50 = _last_value(df, "EMA50")
    ema200 = _last_value(df, "EMA200")

    if None in (close, ema50, ema200):
        return False

    return (
        close < ema50
        and ema50 < ema200
    )


# ============================================================
# EMA 15 BREAK / CLOSE CONFIRMATION
# ============================================================

def _ema15_bullish_cross(df):
    if df is None or len(df) < 2:
        return False

    close = _last_value(df, "close")
    previous_close = _previous_value(df, "close")

    ema15 = _last_value(df, "EMA15")
    previous_ema15 = _previous_value(df, "EMA15")

    if None in (
        close,
        previous_close,
        ema15,
        previous_ema15,
    ):
        return False

    return (
        previous_close <= previous_ema15
        and close > ema15
    )


def _ema15_bearish_cross(df):
    if df is None or len(df) < 2:
        return False

    close = _last_value(df, "close")
    previous_close = _previous_value(df, "close")

    ema15 = _last_value(df, "EMA15")
    previous_ema15 = _previous_value(df, "EMA15")

    if None in (
        close,
        previous_close,
        ema15,
        previous_ema15,
    ):
        return False

    return (
        previous_close >= previous_ema15
        and close < ema15
    )


# ============================================================
# RSI
# ============================================================

def _rsi_neutral(df):
    rsi = _last_value(df, "RSI")

    if rsi is None:
        return False

    return 30 < rsi < 70


def _rsi_bullish(df):
    rsi = _last_value(df, "RSI")

    if rsi is None:
        return False

    return 50 < rsi < 70


def _rsi_bearish(df):
    rsi = _last_value(df, "RSI")

    if rsi is None:
        return False

    return 30 < rsi < 50


# ============================================================
# MOMENTUM
# ============================================================

def _bullish_momentum(df):
    close = _last_value(df, "close")
    previous_close = _previous_value(df, "close")

    if None in (close, previous_close):
        return False

    return close > previous_close


def _bearish_momentum(df):
    close = _last_value(df, "close")
    previous_close = _previous_value(df, "close")

    if None in (close, previous_close):
        return False

    return close < previous_close


# ============================================================
# BOS / CHOCH
# ============================================================

def _has_bullish_structure(bos, choch):
    values = {
        str(bos).upper() if bos is not None else "",
        str(choch).upper() if choch is not None else "",
    }

    return any(
        value in {
            "BULLISH",
            "BULLISH BOS",
            "BULLISH CHOCH",
            "BOS BULLISH",
            "CHOCH BULLISH",
            "UP",
        }
        for value in values
    )


def _has_bearish_structure(bos, choch):
    values = {
        str(bos).upper() if bos is not None else "",
        str(choch).upper() if choch is not None else "",
    }

    return any(
        value in {
            "BEARISH",
            "BEARISH BOS",
            "BEARISH CHOCH",
            "BOS BEARISH",
            "CHOCH BEARISH",
            "DOWN",
        }
        for value in values
    )


# ============================================================
# TARGETS / STOP
# ============================================================

def _build_levels(
    df,
    direction,
    pattern=None,
):
    close = _last_value(df, "close")
    atr = _last_value(df, "ATR")

    if close is None:
        return {
            "entry": None,
            "tp1": None,
            "tp2": None,
            "sl": None,
        }

    # Pattern levels have priority when available.
    if pattern is not None:
        pattern_entry = _num(pattern.get("entry"))
        pattern_tp1 = _num(pattern.get("tp1"))
        pattern_tp2 = _num(pattern.get("tp2"))
        pattern_sl = _num(pattern.get("sl"))

        if (
            pattern_entry is not None
            and pattern_tp1 is not None
            and pattern_tp2 is not None
            and pattern_sl is not None
        ):
            return {
                "entry": pattern_entry,
                "tp1": pattern_tp1,
                "tp2": pattern_tp2,
                "sl": pattern_sl,
            }

    if atr is None or atr <= 0:
        # Safe fallback when ATR is unavailable.
        atr = abs(close) * 0.01

    if direction == "BUY":
        return {
            "entry": close,
            "tp1": close + atr * 1.5,
            "tp2": close + atr * 3.0,
            "sl": close - atr * 1.0,
        }

    if direction == "SELL":
        return {
            "entry": close,
            "tp1": close - atr * 1.5,
            "tp2": close - atr * 3.0,
            "sl": close + atr * 1.0,
        }

    return {
        "entry": None,
        "tp1": None,
        "tp2": None,
        "sl": None,
    }


# ============================================================
# MAIN SIGNAL ENGINE
# ============================================================

def generate_signal(
    df,
    patterns=None,
    trend=None,
    bos=None,
    choch=None,
):
    """
    Generate BUY / SELL / WAIT.

    IMPORTANT:
        A chart pattern alone NEVER creates a trade signal.

    BUY requires:
        1. Bullish pattern
        2. Pattern CONFIRMED
        3. BULLISH market trend
        4. Close > EMA50 > EMA200
        5. RSI between 50 and 70
        6. Bullish momentum
        7. Close above EMA15

    SELL requires the mirrored bearish conditions.

    EMA15 cross is treated as a confirmation bonus rather
    than a mandatory condition because a confirmed pattern
    can remain valid after the initial EMA15 cross candle.
    """

    if df is None or df.empty:
        return {
            "signal": "WAIT",
            "direction": "NEUTRAL",
            "quality": 0,
            "reason": "No market data.",
            "conditions": [],
            "entry": None,
            "tp1": None,
            "tp2": None,
            "sl": None,
            "pattern": None,
        }

    if patterns is None:
        patterns = []

    # --------------------------------------------------------
    # Choose strongest confirmed pattern
    # --------------------------------------------------------

    confirmed = [
        p
        for p in patterns
        if str(p.get("status", "")).upper()
        == "CONFIRMED"
    ]

    confirmed.sort(
        key=lambda p: _num(
            p.get("quality"),
            0,
        ),
        reverse=True,
    )

    pattern = (
        confirmed[0]
        if confirmed
        else None
    )

    close = _last_value(df, "close")

    # --------------------------------------------------------
    # Common conditions
    # --------------------------------------------------------

    trend_name = (
        str(trend).upper()
        if trend is not None
        else ""
    )

    bullish_pattern = _is_bullish_pattern(pattern)
    bearish_pattern = _is_bearish_pattern(pattern)

    bullish_trend = (
        trend_name == "BULLISH"
    )

    bearish_trend = (
        trend_name == "BEARISH"
    )

    ema_bullish = _ema_bullish(df)
    ema_bearish = _ema_bearish(df)

    rsi_neutral = _rsi_neutral(df)
    rsi_bullish = _rsi_bullish(df)
    rsi_bearish = _rsi_bearish(df)

    bullish_momentum = _bullish_momentum(df)
    bearish_momentum = _bearish_momentum(df)

    bullish_ema15_cross = _ema15_bullish_cross(df)
    bearish_ema15_cross = _ema15_bearish_cross(df)

    bullish_ema15_close = False
    bearish_ema15_close = False

    ema15 = _last_value(df, "EMA15")

    if (
        close is not None
        and ema15 is not None
    ):
        bullish_ema15_close = close > ema15
        bearish_ema15_close = close < ema15

    bullish_structure = _has_bullish_structure(
        bos,
        choch,
    )

    bearish_structure = _has_bearish_structure(
        bos,
        choch,
    )

    # --------------------------------------------------------
    # BUY conditions
    # --------------------------------------------------------

    buy_conditions = [
        (
            "Confirmed bullish pattern",
            bullish_pattern,
        ),
        (
            "Bullish market trend",
            bullish_trend,
        ),
        (
            "Price > EMA50 > EMA200",
            ema_bullish,
        ),
        (
            "RSI 50-70",
            rsi_bullish,
        ),
        (
            "Bullish momentum",
            bullish_momentum,
        ),
        (
            "Close > EMA15",
            bullish_ema15_close,
        ),
    ]

    buy_passed = sum(
        bool(condition)
        for _, condition in buy_conditions
    )

    # --------------------------------------------------------
    # SELL conditions
    # --------------------------------------------------------

    sell_conditions = [
        (
            "Confirmed bearish pattern",
            bearish_pattern,
        ),
        (
            "Bearish market trend",
            bearish_trend,
        ),
        (
            "Price < EMA50 < EMA200",
            ema_bearish,
        ),
        (
            "RSI 30-50",
            rsi_bearish,
        ),
        (
            "Bearish momentum",
            bearish_momentum,
        ),
        (
            "Close < EMA15",
            bearish_ema15_close,
        ),
    ]

    sell_passed = sum(
        bool(condition)
        for _, condition in sell_conditions
    )

    # --------------------------------------------------------
    # Structure confirmation is additional evidence.
    # It is not enough by itself to trigger a trade.
    # --------------------------------------------------------

    buy_structure_bonus = (
        bullish_structure
        or bullish_ema15_cross
    )

    sell_structure_bonus = (
        bearish_structure
        or bearish_ema15_cross
    )

    # --------------------------------------------------------
    # Final decision
    # --------------------------------------------------------

    # Strong signal requires ALL six core conditions.
    if buy_passed == len(buy_conditions):

        quality = 80

        if bullish_structure:
            quality += 7

        if bullish_ema15_cross:
            quality += 5

        if pattern is not None:
            quality += min(
                8,
                int(
                    _num(
                        pattern.get("quality"),
                        0,
                    ) / 12
                ),
            )

        quality = min(100, quality)

        levels = _build_levels(
            df,
            "BUY",
            pattern,
        )

        return {
            "signal": "BUY",
            "direction": "BULLISH",
            "quality": quality,
            "reason": (
                "Confirmed bullish pattern + bullish "
                "market structure + EMA alignment + "
                "RSI + momentum + EMA15 confirmation."
            ),
            "conditions": buy_conditions,
            "structure_confirmation": buy_structure_bonus,
            "entry": levels["entry"],
            "tp1": levels["tp1"],
            "tp2": levels["tp2"],
            "sl": levels["sl"],
            "pattern": pattern,
        }

    if sell_passed == len(sell_conditions):

        quality = 80

        if bearish_structure:
            quality += 7

        if bearish_ema15_cross:
            quality += 5

        if pattern is not None:
            quality += min(
                8,
                int(
                    _num(
                        pattern.get("quality"),
                        0,
                    ) / 12
                ),
            )

        quality = min(100, quality)

        levels = _build_levels(
            df,
            "SELL",
            pattern,
        )

        return {
            "signal": "SELL",
            "direction": "BEARISH",
            "quality": quality,
            "reason": (
                "Confirmed bearish pattern + bearish "
                "market structure + EMA alignment + "
                "RSI + momentum + EMA15 confirmation."
            ),
            "conditions": sell_conditions,
            "structure_confirmation": sell_structure_bonus,
            "entry": levels["entry"],
            "tp1": levels["tp1"],
            "tp2": levels["tp2"],
            "sl": levels["sl"],
            "pattern": pattern,
        }

    # --------------------------------------------------------
    # WAIT
    # --------------------------------------------------------

    if bullish_pattern and buy_passed >= 3:
        wait_reason = (
            "Bullish setup ayaa jira, laakiin "
            "dhammaan shuruudaha BUY weli ma buuxsamaan."
        )

    elif bearish_pattern and sell_passed >= 3:
        wait_reason = (
            "Bearish setup ayaa jira, laakiin "
            "dhammaan shuruudaha SELL weli ma buuxsamaan."
        )

    elif patterns:
        wait_reason = (
            "Pattern waa la helay, laakiin pattern "
            "keligiis trade signal ma aha."
        )

    else:
        wait_reason = (
            "Pattern confirmed ah iyo conditions "
            "dhammeystiran lama helin."
        )

    return {
        "signal": "WAIT",
        "direction": (
            "BULLISH"
            if buy_passed > sell_passed
            else "BEARISH"
            if sell_passed > buy_passed
            else "NEUTRAL"
        ),
        "quality": max(
            buy_passed,
            sell_passed,
        ) * 10,
        "reason": wait_reason,
        "conditions": (
            buy_conditions
            if buy_passed >= sell_passed
            else sell_conditions
        ),
        "structure_confirmation": (
            buy_structure_bonus
            if buy_passed >= sell_passed
            else sell_structure_bonus
        ),
        "entry": None,
        "tp1": None,
        "tp2": None,
        "sl": None,
        "pattern": pattern,
    }


# ============================================================
# SIMPLE ALIAS
# ============================================================

def analyze_signal(
    df,
    patterns=None,
    trend=None,
    bos=None,
    choch=None,
):
    """Alias for projects that prefer analyze_signal()."""

    return generate_signal(
        df=df,
        patterns=patterns,
        trend=trend,
        bos=bos,
        choch=choch,
  )
      
