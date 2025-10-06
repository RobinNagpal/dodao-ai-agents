import json
import traceback
from typing import Optional
import yfinance as yf


def _ok(body: dict, status: int = 200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }


def _err(message: str, status: int = 400, extra: Optional[dict] = None):
    payload = {"error": message}
    if extra:
        payload.update(extra)
    return _ok(payload, status)


def _get_symbol_from_event(event: dict) -> Optional[str]:
    # 1) Query string (?symbol=AAPL or ?ticker=AAPL)
    qsp = event.get("queryStringParameters") or {}
    sym = qsp.get("symbol") or qsp.get("ticker")
    if sym:
        return sym.strip().upper()

    # 2) Optional JSON body (POST)
    body = event.get("body", None)
    if body is None:
        return None
    if isinstance(body, (bytes, bytearray)):
        body = body.decode("utf-8", errors="ignore")

    body_str = str(body).strip()
    if not body_str or body_str[0] not in ("{", "["):
        return None

    try:
        data = json.loads(body_str)
        sym = (data.get("symbol") or data.get("ticker"))
        if sym:
            return sym.strip().upper()
    except Exception:
        return None

    return None


def _safe_get_info(t: yf.Ticker) -> dict:
    try:
        info = t.get_info()
        return info if isinstance(info, dict) else {}
    except Exception as e:
        print("WARN get_info failed:", repr(e))
        return {}


def _safe_history_close(t: yf.Ticker) -> Optional[float]:
    try:
        hist = t.history(period="1d")
        if hist is not None and not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception as e:
        print("WARN history failed:", repr(e))
    return None


def _safe_ttm_income_stmt(t: yf.Ticker):
    try:
        df = t.ttm_income_stmt
        if df is not None and hasattr(df, "empty") and not df.empty:
            return df
    except Exception as e:
        print("WARN ttm_income_stmt failed:", repr(e))
    return None


def _build_stock_payload(symbol: str) -> dict:
    t = yf.Ticker(symbol)

    info = _safe_get_info(t)
    last_close = _safe_history_close(t)

    # TTM income statement
    ttm = _safe_ttm_income_stmt(t)
    total_revenue = None
    net_income = None
    if ttm is not None:
        try:
            if "Total Revenue" in ttm.index:
                total_revenue = float(ttm.loc["Total Revenue"].dropna().iloc[0])
            if "Net Income" in ttm.index:
                net_income = float(ttm.loc["Net Income"].dropna().iloc[0])
        except Exception as e:
            print("WARN parsing TTM failed:", repr(e))

    net_profit_margin = None
    if total_revenue and total_revenue != 0 and net_income is not None:
        net_profit_margin = net_income / total_revenue

    # Build response (prefer info; fall back to last_close for price)
    data = {
        "symbol": getattr(t, "ticker", symbol),
        "currency": info.get("currency"),
        "price": info.get("regularMarketPrice", last_close),
        "dayHigh": info.get("dayHigh"),
        "dayLow": info.get("dayLow"),
        "yearHigh": info.get("fiftyTwoWeekHigh"),
        "yearLow": info.get("fiftyTwoWeekLow"),
        "marketCap": info.get("marketCap"),
        "epsDilutedTTM": info.get("epsTrailingTwelveMonths"),
        "pe": info.get("trailingPE"),
        "avgVolume3M": info.get("averageDailyVolume3Month"),
        "dayVolume": info.get("volume"),
        "dividendYield": info.get("dividendYield"),
        "annualDividend": info.get("dividendRate"),
        "totalRevenue": total_revenue,
        "netIncome": net_income,
        "netProfitMargin": net_profit_margin,
    }

    # If Yahoo really returned nothing useful, keep your previous behavior
    if not info and last_close is None:
        return {"symbol": symbol, "error": "Invalid symbol or no data", "data": None}

    return data


def lambda_handler(event, context):
    # Some proxies send OPTIONS
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return _ok({"status": "ok"}, 200)

    try:
        symbol = _get_symbol_from_event(event)
        if not symbol:
            return _err("Missing 'symbol' (use /stock?symbol=AAPL or JSON body).", 400)

        payload = _build_stock_payload(symbol)
        return _ok(payload, 200)

    except Exception as e:
        print("FATAL:", traceback.format_exc())
        return _err("Internal server error", 500, {"exception": str(e)})
