from __future__ import annotations

import hashlib
import json
import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import yfinance as yf

MARKET_RSS_FEEDS: dict[str, str] = {
    "google_business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "google_world": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en",
    "marketwatch_topstories": "https://feeds.marketwatch.com/marketwatch/topstories/",
}

POS_WORDS = {
    "beat",
    "beats",
    "growth",
    "strong",
    "upgrade",
    "upgrades",
    "record",
    "surge",
    "gain",
    "gains",
    "profit",
    "profits",
    "bullish",
    "buy",
    "outperform",
    "raise",
    "raised",
    "positive",
}
NEG_WORDS = {
    "miss",
    "misses",
    "weak",
    "downgrade",
    "downgrades",
    "drop",
    "falls",
    "loss",
    "losses",
    "lawsuit",
    "probe",
    "warn",
    "warning",
    "cut",
    "cuts",
    "negative",
    "bearish",
    "underperform",
    "slump",
}


def simple_sentiment(text: str) -> float:
    tokens = [token.strip(".,:;!?()[]{}\"'`).-_ ").lower() for token in str(text).split()]
    tokens = [token for token in tokens if token]
    if not tokens:
        return 0.0
    pos = sum(1 for token in tokens if token in POS_WORDS)
    neg = sum(1 for token in tokens if token in NEG_WORDS)
    return (pos - neg) / max(len(tokens), 1)


def _load_api_key(api_key_path: Path | None = None) -> str:
    env = os.getenv("FINNHUB_API_KEY")
    if env:
        return env.strip()

    if api_key_path and api_key_path.exists():
        key = api_key_path.read_text(encoding="utf-8").strip()
        if key:
            return key

    raise FileNotFoundError("Missing Finnhub API key. Set FINNHUB_API_KEY or create a local secrets file.")


def finnhub_fetch(symbol: str, start: str, end: str, api_key: str) -> list[dict]:
    url = "https://finnhub.io/api/v1/company-news"
    response = requests.get(url, params={"symbol": symbol, "from": start, "to": end, "token": api_key}, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, list) else []


def yfinance_fetch_news(symbol: str) -> list[dict]:
    ticker = yf.Ticker(symbol)
    items = getattr(ticker, "news", None)
    if not items or not isinstance(items, list):
        return []
    return items


def yfinance_fetch_profile(symbol: str) -> dict[str, Any]:
    ticker = yf.Ticker(symbol)
    info = getattr(ticker, "info", None) or {}
    if not isinstance(info, dict):
        info = {}
    return {
        "symbol": symbol,
        "short_name": info.get("shortName"),
        "long_name": info.get("longName"),
        "sector": info.get("sector") or info.get("sectorDisp"),
        "industry": info.get("industry") or info.get("industryDisp"),
        "quote_type": info.get("quoteType"),
        "exchange": info.get("exchange"),
        "country": info.get("country"),
    }


def rss_fetch_news(feed_name: str, url: str) -> list[dict[str, Any]]:
    response = requests.get(url, timeout=30, headers={"User-Agent": "stock-news/0.1"})
    response.raise_for_status()

    root = ET.fromstring(response.content)
    entries: list[dict[str, Any]] = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        if not title:
            continue
        entries.append(
            {
                "headline": title,
                "summary": description,
                "url": link,
                "source": feed_name,
                "provider": "rss",
                "published_at": published,
            }
        )
    return entries


def update_news_history(
    symbols: list[str],
    *,
    headlines_dir: Path,
    sentiment_dir: Path,
    api_key_path: Path | None = None,
    provider: str = "auto",
    overlap_days: int = 2,
    min_fetch_minutes: int = 5,
    sleep_s: float = 0.05,
) -> dict[str, Any]:
    provider = str(provider).strip().lower()
    if provider not in {"auto", "finnhub", "yfinance"}:
        provider = "auto"

    api_key: str | None = None
    if provider in {"auto", "finnhub"}:
        try:
            api_key = _load_api_key(api_key_path)
        except FileNotFoundError:
            if provider == "finnhub":
                raise
            api_key = None

    headlines_dir.mkdir(parents=True, exist_ok=True)
    sentiment_dir.mkdir(parents=True, exist_ok=True)

    now = pd.Timestamp.now(tz="UTC")
    today = now.date().isoformat()

    out_root = headlines_dir.parent
    state_path = out_root / ".news_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
        state = state if isinstance(state, dict) else {}
    except Exception:
        state = {}

    cooldown = pd.Timedelta(minutes=int(max(0, min_fetch_minutes)))
    rows: list[dict[str, Any]] = []

    for idx, symbol in enumerate(symbols, start=1):
        safe_symbol = str(symbol).replace("/", "_")
        headlines_path = headlines_dir / f"{safe_symbol}.parquet"
        sentiment_path = sentiment_dir / f"{safe_symbol}.parquet"

        state_item = state.get(symbol)
        if headlines_path.exists() and sentiment_path.exists() and isinstance(state_item, dict):
            try:
                last_fetch = pd.to_datetime(state_item.get("last_fetch_utc"), utc=True)
            except Exception:
                last_fetch = pd.NaT
            if pd.notna(last_fetch) and (now - last_fetch) < cooldown:
                rows.append(
                    {
                        "symbol": symbol,
                        "provider": "cooldown",
                        "ok": True,
                        "from": None,
                        "to": today,
                        "n_raw": 0,
                        "n_articles": 0,
                        "n_days_total": None,
                        "error": "",
                        "skipped": True,
                        "message": "cooldown_skip",
                    }
                )
                continue

        from_date = (now.normalize() - pd.Timedelta(days=30)).date().isoformat()
        if headlines_path.exists():
            try:
                old_headlines = pd.read_parquet(headlines_path, columns=["datetime_utc"])
                if not old_headlines.empty:
                    max_dt = pd.to_datetime(old_headlines["datetime_utc"], utc=True, errors="coerce").dropna().max()
                    if pd.notna(max_dt):
                        if max_dt.date().isoformat() == today:
                            from_date = today
                        else:
                            from_date = (max_dt.normalize() - pd.Timedelta(days=int(overlap_days))).date().isoformat()
            except Exception:
                pass

        used_provider = "yfinance" if (provider == "yfinance" or api_key is None) else "finnhub"
        error = ""
        news_items: list[dict[str, Any]] = []

        if used_provider == "finnhub":
            try:
                news_items = finnhub_fetch(symbol, from_date, today, api_key or "")
            except Exception as exc:
                error = f"finnhub:{type(exc).__name__}:{exc}"
                if provider == "auto":
                    try:
                        news_items = yfinance_fetch_news(symbol)
                        used_provider = "yfinance"
                        error = ""
                    except Exception as fallback_exc:
                        error = error + f" | yfinance:{type(fallback_exc).__name__}:{fallback_exc}"
                        news_items = []
        else:
            try:
                news_items = yfinance_fetch_news(symbol)
            except Exception as exc:
                error = f"yfinance:{type(exc).__name__}:{exc}"
                news_items = []

        records: list[dict[str, Any]] = []
        min_dt = pd.Timestamp(from_date, tz="UTC")
        if used_provider == "finnhub":
            for item in news_items:
                ts = item.get("datetime")
                if ts is None:
                    continue
                dt = pd.to_datetime(int(ts), unit="s", utc=True)
                if dt < min_dt:
                    continue
                headline = str(item.get("headline", "") or "")
                summary = str(item.get("summary", "") or "")
                url = str(item.get("url", "") or "")
                signature = f"{symbol}|{int(ts)}|{headline}|{url}"
                records.append(
                    {
                        "symbol": symbol,
                        "datetime_utc": dt,
                        "date": dt.normalize(),
                        "headline": headline,
                        "summary": summary,
                        "url": url,
                        "source": str(item.get("source", "finnhub") or "finnhub"),
                        "provider": "finnhub",
                        "sentiment": simple_sentiment(f"{headline} {summary}"),
                        "id_hash": hashlib.sha1(signature.encode("utf-8")).hexdigest(),
                    }
                )
        else:
            for item in news_items:
                ts = item.get("providerPublishTime")
                if ts is None:
                    continue
                dt = pd.to_datetime(int(ts), unit="s", utc=True)
                if dt < min_dt:
                    continue
                headline = str(item.get("title", "") or "")
                url = str(item.get("link", "") or "")
                publisher = str(item.get("publisher", "yfinance") or "yfinance")
                signature = f"{symbol}|{int(ts)}|{headline}|{url}"
                records.append(
                    {
                        "symbol": symbol,
                        "datetime_utc": dt,
                        "date": dt.normalize(),
                        "headline": headline,
                        "summary": "",
                        "url": url,
                        "source": publisher,
                        "provider": "yfinance",
                        "sentiment": simple_sentiment(headline),
                        "id_hash": hashlib.sha1(signature.encode("utf-8")).hexdigest(),
                    }
                )

        new_headlines = pd.DataFrame(records)
        state[symbol] = {"last_fetch_utc": now.isoformat(), "provider": used_provider}

        if new_headlines.empty:
            if headlines_path.exists() and sentiment_path.exists():
                rows.append(
                    {
                        "symbol": symbol,
                        "provider": used_provider,
                        "ok": error == "",
                        "from": from_date,
                        "to": today,
                        "n_raw": 0,
                        "n_articles": 0,
                        "n_days_total": None,
                        "error": error,
                        "skipped": True,
                        "message": "no_new_articles",
                    }
                )
                time.sleep(max(0.0, float(sleep_s)))
                continue

            empty_headlines = pd.DataFrame(
                columns=[
                    "symbol",
                    "datetime_utc",
                    "date",
                    "headline",
                    "summary",
                    "url",
                    "source",
                    "provider",
                    "sentiment",
                    "id_hash",
                ]
            )
            empty_sentiment = pd.DataFrame(columns=["symbol", "date", "sentiment_mean", "n_articles"])
            if not headlines_path.exists():
                empty_headlines.to_parquet(headlines_path, index=False)
            if not sentiment_path.exists():
                empty_sentiment.to_parquet(sentiment_path, index=False)
            rows.append(
                {
                    "symbol": symbol,
                    "provider": used_provider,
                    "ok": error == "",
                    "from": from_date,
                    "to": today,
                    "n_raw": 0,
                    "n_articles": 0,
                    "n_days_total": 0,
                    "error": error,
                    "skipped": False,
                    "message": "bootstrapped_empty",
                }
            )
            time.sleep(max(0.0, float(sleep_s)))
            continue

        try:
            old_headlines = pd.read_parquet(headlines_path) if headlines_path.exists() else pd.DataFrame()
        except Exception:
            old_headlines = pd.DataFrame()

        headlines = pd.concat([old_headlines, new_headlines], ignore_index=True)
        headlines["datetime_utc"] = pd.to_datetime(headlines["datetime_utc"], utc=True, errors="coerce")
        headlines["date"] = pd.to_datetime(headlines["date"], utc=True, errors="coerce").dt.normalize()
        headlines = headlines.dropna(subset=["datetime_utc", "date"]).drop_duplicates(subset=["id_hash"], keep="last")
        headlines = headlines.sort_values("datetime_utc")

        appended = int(len(headlines) - len(old_headlines)) if len(old_headlines) else int(len(headlines))
        if appended > 0 or not headlines_path.exists():
            headlines.to_parquet(headlines_path, index=False)

        affected_dates = pd.to_datetime(new_headlines["date"], utc=True, errors="coerce").dropna().dt.normalize().unique()
        need_sentiment = appended > 0 or not sentiment_path.exists()
        if need_sentiment:
            try:
                old_daily = pd.read_parquet(sentiment_path) if sentiment_path.exists() else pd.DataFrame()
            except Exception:
                old_daily = pd.DataFrame()

            subset = headlines[headlines["date"].isin(affected_dates)] if len(affected_dates) else headlines
            daily_new = subset.groupby("date", as_index=False).agg(
                sentiment_mean=("sentiment", "mean"),
                n_articles=("id_hash", "count"),
            )
            daily_new["symbol"] = symbol
            daily_new = daily_new[["symbol", "date", "sentiment_mean", "n_articles"]]

            if not old_daily.empty and "date" in old_daily.columns:
                old_daily["date"] = pd.to_datetime(old_daily["date"], utc=True, errors="coerce").dt.normalize()
                old_daily = old_daily.dropna(subset=["date"])
                daily = old_daily[~old_daily["date"].isin(affected_dates)]
                daily = pd.concat([daily, daily_new], ignore_index=True)
            else:
                daily = daily_new
            daily = daily.sort_values("date")
            daily.to_parquet(sentiment_path, index=False)
            n_days_total = int(len(daily))
        else:
            n_days_total = None

        rows.append(
            {
                "symbol": symbol,
                "provider": used_provider,
                "ok": error == "",
                "from": from_date,
                "to": today,
                "n_raw": int(len(new_headlines)),
                "n_articles": int(max(appended, 0)),
                "n_days_total": n_days_total,
                "error": error,
                "skipped": appended == 0,
                "message": f"articles_appended={appended}",
            }
        )
        if idx % 25 == 0:
            print(f"news {idx}/{len(symbols)}")
        time.sleep(max(0.0, float(sleep_s)))

    coverage = pd.DataFrame(rows)
    stamp = pd.Timestamp.utcnow().strftime("%Y%m%dT%H%M%SZ")
    coverage.to_csv(out_root / "news_update_coverage_latest.csv", index=False)
    coverage.to_csv(out_root / f"news_update_coverage_{stamp}.csv", index=False)

    try:
        state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    except Exception:
        pass

    summary = {
        "ok": bool(coverage["ok"].all()) if len(coverage) else True,
        "symbols_total": int(len(coverage)),
        "symbols_ok": int(coverage["ok"].sum()) if len(coverage) else 0,
        "symbols_failed": int((~coverage["ok"]).sum()) if len(coverage) else 0,
        "providers": coverage["provider"].value_counts().to_dict() if len(coverage) else {},
    }
    (out_root / "news_update_summary_latest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


def load_news_context(
    symbol: str,
    *,
    headlines_dir: Path,
    sentiment_dir: Path,
    market_headlines_path: Path | None = None,
    market_sentiment_path: Path | None = None,
    profiles_dir: Path | None = None,
    max_articles: int = 15,
) -> dict[str, Any]:
    safe_symbol = str(symbol).replace("/", "_")
    headlines_path = headlines_dir / f"{safe_symbol}.parquet"
    sentiment_path = sentiment_dir / f"{safe_symbol}.parquet"

    articles: list[dict[str, Any]] = []
    sentiment_summary: list[dict[str, Any]] = []
    market_articles: list[dict[str, Any]] = []
    market_sentiment_summary: list[dict[str, Any]] = []
    company_profile: dict[str, Any] = {}

    if headlines_path.exists():
        headlines = pd.read_parquet(headlines_path)
        if not headlines.empty:
            headlines["datetime_utc"] = pd.to_datetime(headlines["datetime_utc"], utc=True, errors="coerce")
            headlines = headlines.dropna(subset=["datetime_utc"]).sort_values("datetime_utc", ascending=False)
            sample = headlines.head(int(max_articles))
            articles = [
                {
                    "datetime_utc": row["datetime_utc"].isoformat() if pd.notna(row["datetime_utc"]) else None,
                    "headline": row.get("headline"),
                    "summary": row.get("summary"),
                    "url": row.get("url"),
                    "source": row.get("source"),
                    "provider": row.get("provider"),
                    "sentiment": row.get("sentiment"),
                }
                for _, row in sample.iterrows()
            ]

    if sentiment_path.exists():
        daily = pd.read_parquet(sentiment_path)
        if not daily.empty:
            daily["date"] = pd.to_datetime(daily["date"], utc=True, errors="coerce")
            daily = daily.dropna(subset=["date"]).sort_values("date", ascending=False).head(10)
            sentiment_summary = [
                {
                    "date": row["date"].date().isoformat() if pd.notna(row["date"]) else None,
                    "sentiment_mean": row.get("sentiment_mean"),
                    "n_articles": row.get("n_articles"),
                }
                for _, row in daily.iterrows()
            ]

    if market_headlines_path and market_headlines_path.exists():
        market = pd.read_parquet(market_headlines_path)
        if not market.empty:
            market["datetime_utc"] = pd.to_datetime(market["datetime_utc"], utc=True, errors="coerce")
            market = market.dropna(subset=["datetime_utc"]).sort_values("datetime_utc", ascending=False)
            sample = market.head(max(int(max_articles), 20))
            market_articles = [
                {
                    "datetime_utc": row["datetime_utc"].isoformat() if pd.notna(row["datetime_utc"]) else None,
                    "headline": row.get("headline"),
                    "summary": row.get("summary"),
                    "url": row.get("url"),
                    "source": row.get("source"),
                    "provider": row.get("provider"),
                    "sentiment": row.get("sentiment"),
                }
                for _, row in sample.iterrows()
            ]

    if market_sentiment_path and market_sentiment_path.exists():
        daily = pd.read_parquet(market_sentiment_path)
        if not daily.empty:
            daily["date"] = pd.to_datetime(daily["date"], utc=True, errors="coerce")
            daily = daily.dropna(subset=["date"]).sort_values("date", ascending=False).head(10)
            market_sentiment_summary = [
                {
                    "date": row["date"].date().isoformat() if pd.notna(row["date"]) else None,
                    "sentiment_mean": row.get("sentiment_mean"),
                    "n_articles": row.get("n_articles"),
                }
                for _, row in daily.iterrows()
            ]

    if profiles_dir:
        profile_path = profiles_dir / f"{safe_symbol}.json"
        if profile_path.exists():
            try:
                payload = json.loads(profile_path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    company_profile = payload
            except Exception:
                company_profile = {}

    return {
        "symbol": symbol,
        "articles": articles,
        "daily_sentiment": sentiment_summary,
        "market_articles": market_articles,
        "market_daily_sentiment": market_sentiment_summary,
        "company_profile": company_profile,
    }


def update_market_news_history(
    *,
    headlines_path: Path,
    sentiment_path: Path,
    min_fetch_minutes: int = 30,
    sleep_s: float = 0.05,
) -> dict[str, Any]:
    headlines_path.parent.mkdir(parents=True, exist_ok=True)
    sentiment_path.parent.mkdir(parents=True, exist_ok=True)

    state_path = headlines_path.parent / ".market_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
        state = state if isinstance(state, dict) else {}
    except Exception:
        state = {}

    now = pd.Timestamp.now(tz="UTC")
    cooldown = pd.Timedelta(minutes=int(max(0, min_fetch_minutes)))
    try:
        last_fetch = pd.to_datetime(state.get("last_fetch_utc"), utc=True)
    except Exception:
        last_fetch = pd.NaT

    if headlines_path.exists() and sentiment_path.exists() and pd.notna(last_fetch) and (now - last_fetch) < cooldown:
        return {
            "ok": True,
            "provider": "rss",
            "feeds_total": len(MARKET_RSS_FEEDS),
            "articles_appended": 0,
            "skipped": True,
            "message": "cooldown_skip",
        }

    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for feed_name, url in MARKET_RSS_FEEDS.items():
        try:
            items = rss_fetch_news(feed_name, url)
        except Exception as exc:
            errors.append(f"{feed_name}:{type(exc).__name__}:{exc}")
            items = []
        for item in items:
            dt = pd.to_datetime(item.get("published_at"), utc=True, errors="coerce")
            if pd.isna(dt):
                continue
            headline = str(item.get("headline", "") or "")
            summary = str(item.get("summary", "") or "")
            link = str(item.get("url", "") or "")
            signature = f"{feed_name}|{dt.isoformat()}|{headline}|{link}"
            rows.append(
                {
                    "symbol": "_market",
                    "datetime_utc": dt,
                    "date": dt.normalize(),
                    "headline": headline,
                    "summary": summary,
                    "url": link,
                    "source": str(item.get("source") or feed_name),
                    "provider": "rss",
                    "sentiment": simple_sentiment(f"{headline} {summary}"),
                    "id_hash": hashlib.sha1(signature.encode("utf-8")).hexdigest(),
                }
            )
        time.sleep(max(0.0, float(sleep_s)))

    new_headlines = pd.DataFrame(rows)
    try:
        old_headlines = pd.read_parquet(headlines_path) if headlines_path.exists() else pd.DataFrame()
    except Exception:
        old_headlines = pd.DataFrame()

    if not new_headlines.empty:
        headlines = pd.concat([old_headlines, new_headlines], ignore_index=True)
        headlines["datetime_utc"] = pd.to_datetime(headlines["datetime_utc"], utc=True, errors="coerce")
        headlines["date"] = pd.to_datetime(headlines["date"], utc=True, errors="coerce").dt.normalize()
        headlines = headlines.dropna(subset=["datetime_utc", "date"]).drop_duplicates(subset=["id_hash"], keep="last")
        headlines = headlines.sort_values("datetime_utc")
        appended = int(len(headlines) - len(old_headlines)) if len(old_headlines) else int(len(headlines))
        headlines.to_parquet(headlines_path, index=False)

        daily = headlines.groupby("date", as_index=False).agg(
            sentiment_mean=("sentiment", "mean"),
            n_articles=("id_hash", "count"),
        )
        daily.to_parquet(sentiment_path, index=False)
    else:
        appended = 0
        if not headlines_path.exists():
            pd.DataFrame(
                columns=["symbol", "datetime_utc", "date", "headline", "summary", "url", "source", "provider", "sentiment", "id_hash"]
            ).to_parquet(headlines_path, index=False)
        if not sentiment_path.exists():
            pd.DataFrame(columns=["date", "sentiment_mean", "n_articles"]).to_parquet(sentiment_path, index=False)

    try:
        state_path.write_text(json.dumps({"last_fetch_utc": now.isoformat()}, indent=2, sort_keys=True), encoding="utf-8")
    except Exception:
        pass

    return {
        "ok": len(errors) < len(MARKET_RSS_FEEDS),
        "provider": "rss",
        "feeds_total": len(MARKET_RSS_FEEDS),
        "articles_appended": appended,
        "skipped": False,
        "errors": errors,
    }


def update_company_profiles(
    symbols: list[str],
    *,
    profiles_dir: Path,
    min_refresh_hours: int = 24 * 7,
    sleep_s: float = 0.05,
) -> dict[str, Any]:
    profiles_dir.mkdir(parents=True, exist_ok=True)
    now = pd.Timestamp.now(tz="UTC")
    cooldown = pd.Timedelta(hours=int(max(1, min_refresh_hours)))

    fetched = 0
    skipped = 0
    errors = 0
    for symbol in symbols:
        safe_symbol = str(symbol).replace("/", "_")
        profile_path = profiles_dir / f"{safe_symbol}.json"
        if profile_path.exists():
            try:
                payload = json.loads(profile_path.read_text(encoding="utf-8"))
                fetched_at = pd.to_datetime(payload.get("fetched_at_utc"), utc=True, errors="coerce")
            except Exception:
                fetched_at = pd.NaT
            if pd.notna(fetched_at) and (now - fetched_at) < cooldown:
                skipped += 1
                continue
        try:
            profile = yfinance_fetch_profile(symbol)
            payload = {
                **profile,
                "symbol": symbol,
                "provider": "yfinance",
                "fetched_at_utc": now.isoformat(),
            }
            profile_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
            fetched += 1
        except Exception as exc:
            payload = {
                "symbol": symbol,
                "provider": "yfinance",
                "fetched_at_utc": now.isoformat(),
                "error": f"{type(exc).__name__}:{exc}",
            }
            profile_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
            errors += 1
        time.sleep(max(0.0, float(sleep_s)))

    return {
        "ok": True,
        "symbols_total": len(symbols),
        "profiles_fetched": fetched,
        "profiles_skipped": skipped,
        "profiles_errors": errors,
    }
