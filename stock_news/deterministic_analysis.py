from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from stock_news.news import simple_sentiment

EXPOSURE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "energy": ("oil", "gas", "petroleum", "energy", "drilling", "offshore", "lpg"),
    "defense": ("defense", "defence", "aerospace", "military", "weapons", "missile"),
    "airlines": ("airlines", "airways", "aviation", "air transport", "travel"),
    "shipping": ("shipping", "marine", "tanker", "containers", "freight", "port"),
    "reits": ("reit", "realty", "properties", "property", "real estate"),
    "banks": ("bank", "bancorp", "banco", "banking"),
    "insurance": ("insurance", "assurance", "life holding", "insurer"),
    "semiconductors": ("semiconductor", "semicon", "chip", "memory", "micro"),
    "software": ("software", "cloud", "data", "analytics", "saas", "platform"),
    "utilities": ("utility", "power", "electric", "water", "grid"),
    "metals": ("mining", "minerals", "gold", "silver", "copper", "steel", "ore"),
    "industrials": ("industrial", "construction", "machinery", "engineering", "manufacturing"),
    "consumer": ("consumer", "retail", "food", "grocery", "seafood", "apparel", "beverage"),
}

SECTOR_EXPOSURE_MAP: dict[str, tuple[str, ...]] = {
    "energy": ("energy",),
    "oil & gas": ("energy",),
    "financial services": ("banks", "insurance"),
    "financial": ("banks", "insurance"),
    "real estate": ("reits",),
    "technology": ("software",),
    "industrials": ("industrials",),
    "basic materials": ("metals",),
    "materials": ("metals",),
    "utilities": ("utilities",),
    "consumer cyclical": ("consumer",),
    "consumer defensive": ("consumer",),
    "consumer staples": ("consumer",),
    "healthcare": (),
}

MARKET_THEME_RULES: list[dict[str, Any]] = [
    {
        "id": "middle_east_conflict",
        "label": "Middle East conflict / defense tailwind",
        "keywords": ("iran", "israel", "war", "missile", "strike", "hezbollah", "airstrike", "ceasefire"),
        "supports": ("defense",),
        "hurts": ("airlines", "consumer", "reits", "industrials"),
    },
    {
        "id": "oil_supply_shock",
        "label": "Oil supply shock / energy tailwind",
        "keywords": (
            "hormuz",
            "crude",
            "oil prices",
            "oil supply",
            "pipeline",
            "refinery",
            "supertanker",
            "tanker",
            "opec",
            "barrels per day",
        ),
        "supports": ("energy", "shipping"),
        "hurts": ("airlines", "consumer", "industrials"),
    },
    {
        "id": "shipping_disruption",
        "label": "Shipping disruption / freight stress",
        "keywords": ("red sea", "shipping disruption", "freight rates", "container rates", "supply chain", "ports"),
        "supports": ("shipping", "energy"),
        "hurts": ("consumer", "industrials", "airlines"),
    },
    {
        "id": "rates_higher",
        "label": "Higher yields / hawkish rates",
        "keywords": ("treasury yields rise", "hawkish", "hot inflation", "rates higher", "bond yields jump", "fed pushes back"),
        "supports": ("banks", "insurance"),
        "hurts": ("reits", "utilities", "software"),
    },
    {
        "id": "rates_lower",
        "label": "Lower yields / dovish rates",
        "keywords": ("rate cut", "dovish", "cooling inflation", "yields fall", "bond yields slide", "fed easing"),
        "supports": ("reits", "utilities", "software", "consumer"),
        "hurts": ("banks", "insurance"),
    },
    {
        "id": "defense_spending",
        "label": "Defense spending tailwind",
        "keywords": ("defense spending", "military aid", "arms order", "nato spending", "weapons demand"),
        "supports": ("defense",),
        "hurts": (),
    },
    {
        "id": "semiconductor_upcycle",
        "label": "Semiconductor / AI demand tailwind",
        "keywords": ("ai demand", "data center demand", "chip demand", "memory pricing", "semiconductor sales", "gpu demand"),
        "supports": ("semiconductors", "software"),
        "hurts": (),
    },
    {
        "id": "commodity_strength",
        "label": "Commodity price strength",
        "keywords": ("gold prices", "copper prices", "iron ore", "metals rally", "commodity rally"),
        "supports": ("energy", "metals"),
        "hurts": ("consumer", "industrials"),
    },
]


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _date_label(value: Any) -> str | None:
    dt = _parse_datetime(value)
    if dt is None:
        text = str(value or "").strip()
        return text[:10] if text else None
    return dt.date().isoformat()


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    normalized_text = re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).strip()
    if not normalized_text:
        return False
    padded_text = f" {normalized_text} "
    for needle in needles:
        normalized_needle = re.sub(r"[^a-z0-9]+", " ", str(needle or "").lower()).strip()
        if normalized_needle and f" {normalized_needle} " in padded_text:
            return True
    return False


def _pick_primary_source_row(item: dict[str, Any]) -> dict[str, Any]:
    rows = item.get("source_rows", []) or []
    if rows:
        return rows[0]
    return {}


def _format_num(value: Any, *, digits: int = 2) -> str:
    num = _float_or_none(value)
    if num is None:
        return "n/a"
    return f"{num:.{digits}f}"


def _add_point(target: list[dict[str, Any]], point: str, confidence: str) -> None:
    normalized = point.strip()
    if not normalized:
        return
    if any(existing.get("point") == normalized for existing in target):
        return
    target.append({"point": normalized, "confidence": confidence})


def _article_point(article: dict[str, Any], *, prefix: str | None = None) -> str:
    headline = str(article.get("headline") or "Untitled article").strip().rstrip(".")
    date = article.get("date") or "recent"
    if prefix:
        return f"{date}: {prefix}: {headline}."
    return f"{date}: {headline}."


def _classify_article(article: dict[str, Any]) -> dict[str, Any]:
    headline = str(article.get("headline") or "").strip()
    summary = str(article.get("summary") or "").strip()
    text = f"{headline} {summary}".lower()
    sentiment = float(article.get("sentiment") or simple_sentiment(text))

    positive_tags: set[str] = set()
    negative_tags: set[str] = set()
    catalyst_tags: set[str] = set()

    if _contains_any(
        text,
        (
            "private placement",
            "public offering",
            "secondary offering",
            "registered direct",
            "at-the-market",
            "share sale",
            "sold shares",
            "equity offering",
        ),
    ):
        negative_tags.add("dilution")
        catalyst_tags.add("capital_markets")

    if _contains_any(
        text,
        (
            "late form 10-q",
            "late filing",
            "deficiency notice",
            "non-compliance",
            "delisting",
            "notice regarding late",
        ),
    ):
        negative_tags.add("filing")

    if _contains_any(text, ("lawsuit", "probe", "investigation", "fraud", "sec inquiry")):
        negative_tags.add("legal")

    if _contains_any(
        text,
        (
            "miss",
            "missed",
            "warning",
            "guidance cut",
            "cuts guidance",
            "lowered guidance",
            "decline",
            "fell",
            "drop",
            "slump",
            "underperform",
            "downgrade",
        ),
    ):
        negative_tags.add("weakness")

    if _contains_any(
        text,
        (
            "contract",
            "agreement",
            "partnership",
            "order",
            "award",
            "selected",
            "customer",
            "expands with",
        ),
    ):
        positive_tags.add("commercial")
        catalyst_tags.add("commercial_followthrough")

    if _contains_any(
        text,
        (
            "launch",
            "introduces",
            "introduced",
            "unveils",
            "demonstrates",
            "approval",
            "approved",
            "product",
            "platform",
            "rollout",
        ),
    ):
        positive_tags.add("product")
        catalyst_tags.add("product_followthrough")

    if _contains_any(text, ("acquire", "acquires", "acquisition", "merger", "disposition", "asset sale", "buyback", "repurchase")):
        positive_tags.add("capital_allocation")
        catalyst_tags.add("portfolio_followthrough")

    if _contains_any(text, ("upgrade", "raises target", "price target", "outperform", "buy rating")):
        positive_tags.add("sell_side")

    if _contains_any(
        text,
        (
            "earnings release date",
            "conference call",
            "annual general meeting",
            "agm",
            "investor day",
            "results",
            "earnings",
            "registration statement",
        ),
    ):
        catalyst_tags.add("scheduled_event")

    if sentiment >= 0.04:
        positive_tags.add("positive_tone")
    elif sentiment <= -0.04:
        negative_tags.add("negative_tone")

    if positive_tags and negative_tags:
        kind = "mixed"
    elif positive_tags:
        kind = "positive"
    elif negative_tags:
        kind = "negative"
    else:
        kind = "neutral"

    return {
        "date": _date_label(article.get("datetime_utc")),
        "headline": headline,
        "summary": summary,
        "url": article.get("url"),
        "source": article.get("source"),
        "provider": article.get("provider"),
        "sentiment": sentiment,
        "positive_tags": sorted(positive_tags),
        "negative_tags": sorted(negative_tags),
        "catalyst_tags": sorted(catalyst_tags),
        "kind": kind,
    }


def _infer_company_exposures(item: dict[str, Any], company_profile: dict[str, Any]) -> list[str]:
    tokens = " ".join(
        [
            str(item.get("company_name") or ""),
            str(company_profile.get("sector") or ""),
            str(company_profile.get("industry") or ""),
            str(company_profile.get("long_name") or ""),
            str(company_profile.get("short_name") or ""),
        ]
    ).lower()
    exposures: set[str] = set()

    sector = str(company_profile.get("sector") or "").strip().lower()
    for sector_key, mapped in SECTOR_EXPOSURE_MAP.items():
        if sector_key and sector_key in sector:
            exposures.update(mapped)

    for exposure, keywords in EXPOSURE_KEYWORDS.items():
        if _contains_any(tokens, keywords):
            exposures.add(exposure)

    return sorted(exposures)


def _classify_market_article(article: dict[str, Any], company_exposures: list[str]) -> dict[str, Any]:
    classified = _classify_article(article)
    text = f"{classified.get('headline', '')} {classified.get('summary', '')}".lower()

    matched_effects: list[dict[str, Any]] = []
    exposure_set = set(company_exposures)
    for rule in MARKET_THEME_RULES:
        if not _contains_any(text, tuple(rule["keywords"])):
            continue
        supportive_hits = sorted(exposure_set.intersection(rule["supports"]))
        adverse_hits = sorted(exposure_set.intersection(rule["hurts"]))
        if not supportive_hits and not adverse_hits:
            continue
        matched_effects.append(
            {
                "theme_id": rule["id"],
                "label": rule["label"],
                "supportive_exposures": supportive_hits,
                "adverse_exposures": adverse_hits,
                "direction": "supportive" if supportive_hits and not adverse_hits else "adverse" if adverse_hits and not supportive_hits else "mixed",
            }
        )

    classified["matched_effects"] = matched_effects
    return classified


def build_evidence_snapshot(item: dict[str, Any], news_context: dict[str, Any]) -> dict[str, Any]:
    metrics = item.get("metrics", {}) or {}
    primary_row = _pick_primary_source_row(item)

    close = _float_or_none(metrics.get("close") if metrics.get("close") is not None else primary_row.get("close"))
    hh20_prev = _float_or_none(metrics.get("hh20_prev") if metrics.get("hh20_prev") is not None else primary_row.get("hh20_prev"))
    vol_anom = _float_or_none(metrics.get("vol_anom") if metrics.get("vol_anom") is not None else primary_row.get("vol_anom"))
    atr14 = _float_or_none(metrics.get("atr14") if metrics.get("atr14") is not None else primary_row.get("atr14"))
    ema20 = _float_or_none(primary_row.get("ema20"))
    ema50 = _float_or_none(primary_row.get("ema50"))
    ema200 = _float_or_none(primary_row.get("ema200"))

    classified_articles = [_classify_article(article) for article in news_context.get("articles", []) or []]
    positive_articles = [article for article in classified_articles if article["positive_tags"]]
    negative_articles = [article for article in classified_articles if article["negative_tags"]]
    catalyst_articles = [article for article in classified_articles if article["catalyst_tags"]]

    daily_sentiment = news_context.get("daily_sentiment", []) or []
    recent_means = [
        float(entry.get("sentiment_mean"))
        for entry in daily_sentiment[:3]
        if entry.get("sentiment_mean") is not None
    ]
    prior_means = [
        float(entry.get("sentiment_mean"))
        for entry in daily_sentiment[3:6]
        if entry.get("sentiment_mean") is not None
    ]
    recent_sentiment_mean = sum(recent_means) / len(recent_means) if recent_means else None
    prior_sentiment_mean = sum(prior_means) / len(prior_means) if prior_means else None
    sentiment_delta = None
    if recent_sentiment_mean is not None and prior_sentiment_mean is not None:
        sentiment_delta = recent_sentiment_mean - prior_sentiment_mean

    company_profile = news_context.get("company_profile", {}) or {}
    company_exposures = _infer_company_exposures(item, company_profile)
    classified_market_articles = [
        _classify_market_article(article, company_exposures)
        for article in news_context.get("market_articles", []) or []
    ]
    market_effects = [
        effect
        for article in classified_market_articles
        for effect in article.get("matched_effects", [])
    ]
    supportive_market_articles = [
        article
        for article in classified_market_articles
        if any(effect["direction"] in {"supportive", "mixed"} and effect["supportive_exposures"] for effect in article.get("matched_effects", []))
    ]
    adverse_market_articles = [
        article
        for article in classified_market_articles
        if any(effect["direction"] in {"adverse", "mixed"} and effect["adverse_exposures"] for effect in article.get("matched_effects", []))
    ]

    technical = {
        "close": close,
        "hh20_prev": hh20_prev,
        "vol_anom": vol_anom,
        "atr14": atr14,
        "ema20": ema20,
        "ema50": ema50,
        "ema200": ema200,
        "entry_ready": bool(item.get("entry_ready")),
        "selection_bucket": item.get("selection_bucket"),
        "close_vs_hh20_pct": ((close - hh20_prev) / hh20_prev * 100.0) if close is not None and hh20_prev not in {None, 0.0} else None,
        "close_vs_ema20_pct": ((close - ema20) / ema20 * 100.0) if close is not None and ema20 not in {None, 0.0} else None,
        "close_vs_ema50_pct": ((close - ema50) / ema50 * 100.0) if close is not None and ema50 not in {None, 0.0} else None,
        "close_vs_ema200_pct": ((close - ema200) / ema200 * 100.0) if close is not None and ema200 not in {None, 0.0} else None,
    }

    return {
        "technical": technical,
        "news": {
            "article_count": len(classified_articles),
            "positive_signal_count": len(positive_articles),
            "negative_signal_count": len(negative_articles),
            "catalyst_signal_count": len(catalyst_articles),
            "classified_articles": classified_articles,
        },
        "sentiment": {
            "recent_mean": recent_sentiment_mean,
            "prior_mean": prior_sentiment_mean,
            "delta": sentiment_delta,
            "days_sampled": len(daily_sentiment),
        },
        "market": {
            "article_count": len(classified_market_articles),
            "classified_articles": classified_market_articles,
            "supportive_effect_count": len(supportive_market_articles),
            "adverse_effect_count": len(adverse_market_articles),
            "company_profile": {
                "sector": company_profile.get("sector"),
                "industry": company_profile.get("industry"),
                "provider": company_profile.get("provider"),
            },
            "company_exposures": company_exposures,
            "matched_effects": market_effects,
        },
    }


def _build_scorecard(item: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    technical = evidence["technical"]
    news = evidence["news"]
    sentiment = evidence["sentiment"]
    market = evidence["market"]

    score = 40
    components: list[dict[str, Any]] = [{"label": "Base breakout score", "points": 40}]

    if technical["entry_ready"]:
        score += 10
        components.append({"label": "Feed marks the setup as ENTRY_READY", "points": 10})
    elif item.get("selection_bucket") == "candidate":
        score -= 4
        components.append({"label": "Name is still a candidate, not confirmed ENTRY_READY", "points": -4})

    close_vs_hh20 = technical.get("close_vs_hh20_pct")
    if close_vs_hh20 is not None:
        if close_vs_hh20 >= 2.0:
            score += 10
            components.append({"label": "Price is decisively above the 20-day high trigger", "points": 10, "value": round(close_vs_hh20, 2)})
        elif close_vs_hh20 >= 0:
            score += 7
            components.append({"label": "Price is holding above the 20-day high trigger", "points": 7, "value": round(close_vs_hh20, 2)})
        else:
            score -= 8
            components.append({"label": "Price is still below the 20-day high trigger", "points": -8, "value": round(close_vs_hh20, 2)})

    vol_anom = technical.get("vol_anom")
    if vol_anom is not None:
        if vol_anom >= 3.0:
            score += 9
            components.append({"label": "Volume confirmation is very strong", "points": 9, "value": round(vol_anom, 2)})
        elif vol_anom >= 2.0:
            score += 6
            components.append({"label": "Volume confirmation is supportive", "points": 6, "value": round(vol_anom, 2)})
        elif vol_anom < 1.0:
            score -= 4
            components.append({"label": "Volume confirmation is weak", "points": -4, "value": round(vol_anom, 2)})

    for label, key in [
        ("Price is above EMA20", "close_vs_ema20_pct"),
        ("Price is above EMA50", "close_vs_ema50_pct"),
        ("Price is above EMA200", "close_vs_ema200_pct"),
    ]:
        value = technical.get(key)
        if value is None:
            continue
        if value > 0:
            score += 3
            components.append({"label": label, "points": 3, "value": round(value, 2)})
        else:
            score -= 3
            components.append({"label": label.replace("above", "below"), "points": -3, "value": round(value, 2)})

    positive_count = int(news.get("positive_signal_count") or 0)
    negative_count = int(news.get("negative_signal_count") or 0)
    if positive_count:
        points = min(positive_count * 2, 8)
        score += points
        components.append({"label": "Constructive local news signals", "points": points, "value": positive_count})
    if negative_count:
        points = min(negative_count * 2, 10)
        score -= points
        components.append({"label": "Adverse local news signals", "points": -points, "value": negative_count})

    article_tags = news.get("classified_articles", [])
    if any("dilution" in article["negative_tags"] for article in article_tags):
        score -= 6
        components.append({"label": "Dilution or share-supply overhang detected", "points": -6})
    if any("filing" in article["negative_tags"] for article in article_tags):
        score -= 5
        components.append({"label": "Filing or compliance headline detected", "points": -5})
    if any("legal" in article["negative_tags"] for article in article_tags):
        score -= 5
        components.append({"label": "Legal or investigation headline detected", "points": -5})

    supportive_market = int(market.get("supportive_effect_count") or 0)
    adverse_market = int(market.get("adverse_effect_count") or 0)
    if supportive_market:
        points = min(supportive_market * 2, 6)
        score += points
        components.append({"label": "Supportive market / sector theme overlay", "points": points, "value": supportive_market})
    if adverse_market:
        points = min(adverse_market * 2, 6)
        score -= points
        components.append({"label": "Adverse market / sector theme overlay", "points": -points, "value": adverse_market})

    sentiment_delta = sentiment.get("delta")
    if sentiment_delta is not None:
        if sentiment_delta >= 0.03:
            score += 3
            components.append({"label": "Headline sentiment is improving", "points": 3, "value": round(sentiment_delta, 3)})
        elif sentiment_delta <= -0.03:
            score -= 3
            components.append({"label": "Headline sentiment is deteriorating", "points": -3, "value": round(sentiment_delta, 3)})

    score = max(0, min(100, score))
    confidence = "low"
    if technical.get("close") is not None and technical.get("hh20_prev") is not None:
        confidence = "medium"
    market_matched = int(market.get("supportive_effect_count", 0) or 0) + int(market.get("adverse_effect_count", 0) or 0)
    if (news.get("article_count", 0) >= 5 or market_matched >= 3) and len(components) >= 5:
        confidence = "high"
    elif news.get("article_count", 0) <= 1 and market_matched == 0 and len(components) <= 4:
        confidence = "low"

    if score >= 75:
        label = "constructive_bullish"
    elif score >= 60:
        label = "constructive_watch"
    elif score >= 45:
        label = "mixed_watch"
    elif score >= 30:
        label = "fragile_watch"
    else:
        label = "avoid"

    return {
        "score_0_to_100": score,
        "confidence": confidence,
        "label": label,
        "components": components,
    }


def _build_sources(item: dict[str, Any], evidence: dict[str, Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    seen: set[str] = set()

    primary_row = _pick_primary_source_row(item)
    source_url = str(primary_row.get("_source_url") or "").strip()
    table_title = str(primary_row.get("_table_title") or "Breakout feed").strip()
    if source_url:
        key = f"feed:{source_url}"
        if key not in seen:
            sources.append(
                {
                    "title": f"Feed snapshot: {table_title}",
                    "url": source_url,
                    "publisher": "stock.sdc-fried.de",
                    "published_at": primary_row.get("_source_feed_date"),
                }
            )
            seen.add(key)

    for article in evidence["news"].get("classified_articles", []):
        url = str(article.get("url") or "").strip()
        if not url or url in seen:
            continue
        sources.append(
            {
                "title": article.get("headline") or url,
                "url": url,
                "publisher": article.get("source"),
                "published_at": article.get("date"),
            }
        )
        seen.add(url)
        if len(sources) >= 8:
            return sources

    for article in evidence["market"].get("classified_articles", []):
        if not article.get("matched_effects"):
            continue
        url = str(article.get("url") or "").strip()
        if not url or url in seen:
            continue
        sources.append(
            {
                "title": article.get("headline") or url,
                "url": url,
                "publisher": article.get("source"),
                "published_at": article.get("date"),
            }
        )
        seen.add(url)
        if len(sources) >= 8:
            return sources
    return sources


def generate_python_report(
    item: dict[str, Any],
    news_context: dict[str, Any],
    *,
    analysis_date: str | None = None,
) -> dict[str, Any]:
    analysis_date = analysis_date or datetime.now(timezone.utc).date().isoformat()
    evidence = build_evidence_snapshot(item, news_context)
    scorecard = _build_scorecard(item, evidence)

    technical = evidence["technical"]
    news = evidence["news"]
    sentiment = evidence["sentiment"]
    market = evidence["market"]
    classified_articles = news.get("classified_articles", [])
    positive_articles = [article for article in classified_articles if article["positive_tags"]]
    negative_articles = [article for article in classified_articles if article["negative_tags"]]
    catalyst_articles = [article for article in classified_articles if article["catalyst_tags"]]
    market_articles = market.get("classified_articles", [])

    recent_weakness: list[dict[str, Any]] = []
    recovery_signals: list[dict[str, Any]] = []
    catalysts: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []

    for article in negative_articles[:3]:
        _add_point(recent_weakness, _article_point(article), "medium")

    adverse_market_articles = [article for article in market_articles if any(effect["adverse_exposures"] for effect in article.get("matched_effects", []))]
    supportive_market_articles = [article for article in market_articles if any(effect["supportive_exposures"] for effect in article.get("matched_effects", []))]

    for article in adverse_market_articles[:2]:
        labels = ", ".join(effect["label"] for effect in article.get("matched_effects", []) if effect["adverse_exposures"])
        _add_point(recent_weakness, _article_point(article, prefix=f"Broader market headwind for this exposure set ({labels})"), "medium")

    if not recent_weakness:
        _add_point(
            recent_weakness,
            "No clearly negative stock-specific or market-overlay headline was captured in the local cache, so recent weakness may have been driven more by market tape than by a fresh identifiable shock.",
            "low",
        )

    close_vs_hh20 = technical.get("close_vs_hh20_pct")
    if close_vs_hh20 is not None:
        if close_vs_hh20 >= 0:
            _add_point(
                recovery_signals,
                f"Price is holding above the prior 20-day high ({_format_num(technical.get('hh20_prev'))}), a basic breakout confirmation signal.",
                "high",
            )
        else:
            _add_point(
                risks,
                f"Price is still below the prior 20-day high ({_format_num(technical.get('hh20_prev'))}), so the breakout remains unconfirmed.",
                "high",
            )

    vol_anom = technical.get("vol_anom")
    if vol_anom is not None:
        if vol_anom >= 2.0:
            _add_point(recovery_signals, f"Volume anomaly is strong at {_format_num(vol_anom)}, which supports the move.", "high")
        elif vol_anom < 1.0:
            _add_point(risks, f"Volume anomaly is only {_format_num(vol_anom)}, which weakens confirmation.", "medium")

    ema_alignment = [
        label
        for label, key in [("EMA20", "close_vs_ema20_pct"), ("EMA50", "close_vs_ema50_pct"), ("EMA200", "close_vs_ema200_pct")]
        if technical.get(key) is not None and technical.get(key) > 0
    ]
    if ema_alignment:
        _add_point(recovery_signals, f"Price is above {', '.join(ema_alignment)}, which keeps the medium-term trend supportive.", "medium")

    if item.get("entry_ready"):
        _add_point(recovery_signals, "The feed already classifies the name as ENTRY_READY rather than a lower-conviction candidate.", "high")
    else:
        _add_point(risks, "The name is still only a candidate in the source feed, so the setup is not fully confirmed yet.", "medium")

    for article in positive_articles[:3]:
        _add_point(recovery_signals, _article_point(article), "medium")

    for article in supportive_market_articles[:2]:
        labels = ", ".join(effect["label"] for effect in article.get("matched_effects", []) if effect["supportive_exposures"])
        _add_point(recovery_signals, _article_point(article, prefix=f"Supportive market tailwind for this exposure set ({labels})"), "medium")

    if sentiment.get("delta") is not None and sentiment["delta"] >= 0.03:
        _add_point(recovery_signals, "Headline sentiment has improved versus the prior few cached sessions.", "low")

    for article in catalyst_articles[:3]:
        _add_point(catalysts, _article_point(article), "medium")

    if not catalysts:
        if technical.get("hh20_prev") is not None:
            _add_point(
                catalysts,
                f"The next 1 to 4 weeks matter most around whether price can keep holding above {_format_num(technical.get('hh20_prev'))} and attract follow-through volume.",
                "medium",
            )
        else:
            _add_point(catalysts, "The next meaningful catalyst is whichever company update can confirm that the recent move has fundamental follow-through.", "low")

    if supportive_market_articles[:1]:
        labels = ", ".join(effect["label"] for effect in supportive_market_articles[0].get("matched_effects", []) if effect["supportive_exposures"])
        _add_point(catalysts, _article_point(supportive_market_articles[0], prefix=f"Market theme to monitor ({labels})"), "low")

    if technical.get("hh20_prev") is not None:
        _add_point(
            risks,
            f"A close back below {_format_num(technical.get('hh20_prev'))} would weaken or invalidate the current breakout picture.",
            "high",
        )

    for article in negative_articles[:2]:
        if "dilution" in article["negative_tags"]:
            _add_point(risks, f"Dilution or share-supply risk remains relevant: {_article_point(article)}", "high")
        elif "filing" in article["negative_tags"]:
            _add_point(risks, f"Filing or compliance risk remains relevant: {_article_point(article)}", "high")
        elif "legal" in article["negative_tags"]:
            _add_point(risks, f"Legal or investigation risk remains relevant: {_article_point(article)}", "high")
        else:
            _add_point(risks, f"Recent adverse headline could still cap follow-through: {_article_point(article)}", "medium")

    for article in adverse_market_articles[:2]:
        labels = ", ".join(effect["label"] for effect in article.get("matched_effects", []) if effect["adverse_exposures"])
        _add_point(risks, f"Broader market headwind remains relevant ({labels}): {_article_point(article)}", "medium")

    sources = _build_sources(item, evidence)
    positive_count = int(news.get("positive_signal_count") or 0)
    negative_count = int(news.get("negative_signal_count") or 0)
    article_count = int(news.get("article_count") or 0)
    market_supportive = int(market.get("supportive_effect_count") or 0)
    market_adverse = int(market.get("adverse_effect_count") or 0)

    if positive_count + market_supportive >= negative_count + market_adverse + 2:
        news_support_stance = "supportive"
    elif negative_count + market_adverse >= positive_count + market_supportive + 2:
        news_support_stance = "conflicting"
    else:
        news_support_stance = "mixed"

    summary = (
        f"{item.get('symbol')} scores {scorecard['score_0_to_100']}/100 as a {scorecard['label']} setup. "
        f"The score is driven mainly by the technical breakout picture"
        f"{' and ENTRY_READY status' if item.get('entry_ready') else ''}"
        f", with {positive_count} constructive versus {negative_count} adverse stock-specific signals"
        f" and a market overlay of {market_supportive} supportive versus {market_adverse} adverse matched macro effects."
    )

    if not article_count and not market.get("article_count"):
        summary += " Local symbol and market news coverage is thin, so the stance leans heavily on the feed and price/volume evidence."

    thesis = (
        "The setup is actionable only while the breakout level continues to hold and recent constructive signals, including the broader market overlay when relevant, keep getting follow-through."
        if scorecard["score_0_to_100"] >= 60
        else "The setup is still mixed and needs cleaner confirmation from price action, stock-specific flow, or a more favorable market overlay before it becomes a stronger breakout candidate."
    )

    report = {
        "symbol": item.get("symbol"),
        "company_name": item.get("company_name"),
        "analysis_date": analysis_date,
        "analysis_mode": "python",
        "summary": summary,
        "recent_weakness": recent_weakness[:4],
        "recovery_signals": recovery_signals[:5],
        "catalysts": catalysts[:4],
        "risks": risks[:5],
        "news_support": {
            "stance": news_support_stance,
            "explanation": (
                f"Python classified {article_count} stock-specific articles into {positive_count} constructive, "
                f"{negative_count} adverse, and {int(news.get('catalyst_signal_count') or 0)} catalyst-tagged signals. "
                f"It also matched {market_supportive} supportive and {market_adverse} adverse market-theme effects against this name's inferred sector exposures."
            ),
        },
        "breakout_stance": {
            "label": scorecard["label"],
            "score_0_to_100": scorecard["score_0_to_100"],
            "confidence": scorecard["confidence"],
            "thesis": thesis,
        },
        "sources": sources,
        "analysis_error": None,
        "scorecard": scorecard,
        "evidence": evidence,
        "market_overlay": {
            "sector": market["company_profile"].get("sector"),
            "industry": market["company_profile"].get("industry"),
            "exposures": market.get("company_exposures", []),
            "supportive_effects": market_supportive,
            "adverse_effects": market_adverse,
        },
    }
    return report
