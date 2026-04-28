from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import Any

import httpx

from tax_engine.ingestion.store import STORE

USD_STABLE_QUOTES = {"USD", "USDT", "USDC", "BUSD", "FDUSD", "TUSD"}
_DECIMAL_ZERO = Decimal("0")


@dataclass(slots=True)
class FxResolveResult:
    rate_date: str
    source_rate_date: str
    rate: Decimal
    source: str
    from_cache: bool


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return _DECIMAL_ZERO
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return _DECIMAL_ZERO


def _parse_date(raw: str) -> date | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    if len(text) >= 10:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _extract_event_date(payload: dict[str, Any]) -> str:
    for key in ("timestamp_utc", "timestamp", "date", "time"):
        raw = payload.get(key)
        if raw is None:
            continue
        parsed = _parse_date(str(raw))
        if parsed is not None:
            return parsed.isoformat()
    return datetime.now(UTC).date().isoformat()


class FallbackFxResolver:
    def __init__(self, timeout_seconds: int = 15, fallback_rate: Decimal | str | None = None) -> None:
        self.timeout_seconds = max(3, min(int(timeout_seconds), 60))
        parsed_fallback = Decimal("0") if fallback_rate is None else _to_decimal(fallback_rate)
        self.fallback_rate = parsed_fallback if parsed_fallback > 0 else None

    def get_usd_to_eur_rate(self, rate_date: str) -> FxResolveResult | None:
        # Cache zuerst nutzen, um externe Limits und Latenz zu minimieren.
        cached = STORE.get_fx_rate(rate_date=rate_date, base_ccy="USD", quote_ccy="EUR")
        if cached is not None:
            rate = _to_decimal(cached.get("rate"))
            if rate > 0:
                return FxResolveResult(
                    rate_date=str(cached["rate_date"]),
                    source_rate_date=str(cached.get("source_rate_date") or cached["rate_date"]),
                    rate=rate,
                    source=str(cached.get("source") or "cache"),
                    from_cache=True,
                )

        frankfurter = self._fetch_frankfurter(rate_date=rate_date)
        if frankfurter is not None:
            STORE.upsert_fx_rate(
                rate_date=rate_date,
                base_ccy="USD",
                quote_ccy="EUR",
                rate=frankfurter.rate.to_eng_string(),
                source=frankfurter.source,
                source_rate_date=frankfurter.source_rate_date,
            )
            return frankfurter

        ecb = self._fetch_ecb_csv(rate_date=rate_date)
        if ecb is not None:
            STORE.upsert_fx_rate(
                rate_date=rate_date,
                base_ccy="USD",
                quote_ccy="EUR",
                rate=ecb.rate.to_eng_string(),
                source=ecb.source,
                source_rate_date=ecb.source_rate_date,
            )
            return ecb

        if self.fallback_rate is not None:
            return FxResolveResult(
                rate_date=rate_date,
                source_rate_date=rate_date,
                rate=self.fallback_rate,
                source="runtime_setting",
                from_cache=False,
            )

        return None

    def enrich_events_with_fx(self, raw_events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        transformed: list[dict[str, Any]] = []
        converted_count = 0
        unresolved: list[dict[str, str]] = []
        rate_cache: dict[str, FxResolveResult | None] = {}

        for event in raw_events:
            payload = event.get("payload", {})
            if not isinstance(payload, dict):
                transformed.append(event)
                continue

            event_id = str(event.get("unique_event_id", "")).strip()
            event_date = _extract_event_date(payload)
            fx_row = rate_cache.get(event_date)
            if fx_row is None and event_date not in rate_cache:
                fx_row = self.get_usd_to_eur_rate(event_date)
                rate_cache[event_date] = fx_row
            else:
                fx_row = rate_cache.get(event_date)

            payload_copy = dict(payload)
            changed = False

            if fx_row is not None:
                rate = fx_row.rate
                if self._apply_price_conversion(payload_copy, rate):
                    changed = True
                if self._apply_fee_conversion(payload_copy, rate):
                    changed = True
                if self._apply_amount_conversions(payload_copy, rate):
                    changed = True
                if changed:
                    converted_count += 1

                payload_copy["fx_rate_usd_eur"] = rate.to_eng_string()
                payload_copy["fx_rate_date"] = fx_row.source_rate_date
                payload_copy["fx_rate_source"] = fx_row.source
                changed = True
            elif self._requires_usd_to_eur(payload_copy):
                unresolved.append(
                    {
                        "source_event_id": event_id,
                        "rate_date": event_date,
                        "reason": "usd_to_eur_rate_missing",
                    }
                )

            if changed:
                updated = dict(event)
                updated["payload"] = payload_copy
                transformed.append(updated)
            else:
                transformed.append(event)

        return transformed, {
            "converted_event_count": converted_count,
            "unresolved_count": len(unresolved),
            "unresolved_events": unresolved[:500],
        }

    def _fetch_frankfurter(self, rate_date: str) -> FxResolveResult | None:
        url = f"https://api.frankfurter.dev/v1/{rate_date}"
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(url, params={"base": "USD", "symbols": "EUR"})
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return None

        rates = payload.get("rates") if isinstance(payload, dict) else {}
        rate = _to_decimal((rates or {}).get("EUR"))
        if rate <= 0:
            return None
        source_date = str(payload.get("date") or rate_date)
        return FxResolveResult(
            rate_date=rate_date,
            source_rate_date=source_date,
            rate=rate,
            source="frankfurter",
            from_cache=False,
        )

    def _fetch_ecb_csv(self, rate_date: str) -> FxResolveResult | None:
        # ECB liefert EUR-basierte Referenzwerte (1 EUR = X USD). Für USD->EUR invertieren wir.
        url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.csv"
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(url)
                response.raise_for_status()
                csv_text = response.text
        except Exception:
            return None

        reader = csv.DictReader(StringIO(csv_text))
        target_date = _parse_date(rate_date)
        best_date: date | None = None
        usd_per_eur = _DECIMAL_ZERO
        for row in reader:
            row_date = _parse_date(str(row.get("Date", "")))
            if row_date is None or target_date is None or row_date > target_date:
                continue
            candidate = _to_decimal(row.get("USD"))
            if candidate <= 0:
                continue
            if best_date is None or row_date > best_date:
                best_date = row_date
                usd_per_eur = candidate

        if best_date is None or usd_per_eur <= 0:
            return None
        rate = Decimal("1") / usd_per_eur
        return FxResolveResult(
            rate_date=rate_date,
            source_rate_date=best_date.isoformat(),
            rate=rate,
            source="ecb_csv",
            from_cache=False,
        )

    @staticmethod
    def _apply_price_conversion(payload: dict[str, Any], rate: Decimal) -> bool:
        price_eur = _to_decimal(payload.get("price_eur"))
        if price_eur > 0:
            return False

        lookup = _normalize_lookup_table(payload)
        quote_asset = _lookup_field_str(lookup, ("quote_asset", "quote", "quotecurrency", "tradequote", "basequote", "market"))
        price_usd = _to_decimal(_lookup_field(lookup, ("price_usd", "priceusd", "usd_price", "usdprice", "execution_price_usd")))
        if price_usd <= 0:
            if quote_asset in USD_STABLE_QUOTES:
                price_usd = _to_decimal(payload.get("price"))
        if price_usd <= 0:
            return False

        payload["price_eur"] = (price_usd * rate).to_eng_string()
        return True

    @staticmethod
    def _apply_fee_conversion(payload: dict[str, Any], rate: Decimal) -> bool:
        fee_eur = _to_decimal(payload.get("fee_eur"))
        if fee_eur > 0:
            return False

        lookup = _normalize_lookup_table(payload)
        fee_asset = _lookup_field_str(lookup, ("fee_asset", "feecoin", "feecurrency", "commission_asset"))
        fee_usd = _to_decimal(_lookup_field(lookup, ("fee_usd", "feeusd", "commission_usd", "commissionusd")))
        if fee_usd <= 0:
            if fee_asset in USD_STABLE_QUOTES:
                fee_usd = _to_decimal(payload.get("fee"))
        if fee_usd <= 0:
            return False

        payload["fee_eur"] = (fee_usd * rate).to_eng_string()
        return True

    @staticmethod
    def _apply_amount_conversions(payload: dict[str, Any], rate: Decimal) -> bool:
        changed = False
        field_pairs = (
            ("amount_usd", "amount_eur"),
            ("value_usd", "value_eur"),
            ("income_usd", "income_eur"),
            ("proceeds_usd", "proceeds_eur"),
            ("pnl_usd", "pnl_eur"),
            ("collateral_usd", "collateral_eur"),
            ("funding_usd", "funding_eur"),
            ("commission_usd", "commission_eur"),
        )
        lookup = _normalize_lookup_table(payload)
        extended_pairs = tuple(
            (source, target)
            for source, target in (
                *field_pairs,
                ("raw_amount_usd", "amount_eur"),
                ("raw_value_usd", "value_eur"),
                ("raw_income_usd", "income_eur"),
                ("raw_proceeds_usd", "proceeds_eur"),
                ("raw_pnl_usd", "pnl_eur"),
                ("raw_collateral_usd", "collateral_eur"),
                ("raw_funding_usd", "funding_eur"),
            )
        )
        for source_key, target_key in extended_pairs:
            target = _to_decimal(payload.get(target_key))
            if target > 0:
                continue
            source = _to_decimal(_lookup_field(lookup, (source_key, source_key.replace("raw_", ""))))
            if source <= 0:
                continue
            payload[target_key] = (source * rate).to_eng_string()
            changed = True
        return changed

    @staticmethod
    def _requires_usd_to_eur(payload: dict[str, Any]) -> bool:
        lookup = _normalize_lookup_table(payload)
        quote_asset = _lookup_field_str(lookup, ("quote_asset", "quote", "quotecurrency", "basequote"))

        if _to_decimal(payload.get("price_eur")) <= 0:
            if _to_decimal(_lookup_field(lookup, ("price_usd", "priceusd", "usd_price", "usdprice", "execution_price_usd"))) > 0:
                return True
            if quote_asset in USD_STABLE_QUOTES and _to_decimal(_lookup_field(lookup, ("price", "execution_price", "spot_price", "rate"))) > 0:
                return True

        if _to_decimal(payload.get("fee_eur")) <= 0:
            if _to_decimal(_lookup_field(lookup, ("fee_usd", "feeusd", "commission_usd", "commissionusd"))) > 0:
                return True
            if _lookup_field_str(lookup, ("fee_asset", "feecoin", "feecurrency", "commission_asset")) in USD_STABLE_QUOTES and _to_decimal(_lookup_field(lookup, ("fee", "commission", "txn_fee"))) > 0:
                return True

        amount_targets = (
            "amount_usd",
            "value_usd",
            "income_usd",
            "proceeds_usd",
            "pnl_usd",
            "collateral_usd",
            "funding_usd",
            "commission_usd",
            "raw_amount_usd",
            "raw_value_usd",
            "raw_income_usd",
            "raw_proceeds_usd",
            "raw_pnl_usd",
            "raw_collateral_usd",
            "raw_funding_usd",
            "raw_commission_usd",
        )
        for source in amount_targets:
            target = source.replace("raw_", "").replace("_usd", "_eur")
            if _to_decimal(_lookup_field(lookup, (source,))) > 0 and _to_decimal(payload.get(target)) <= 0:
                return True

        # Backwards-kompatibel alte Logik:
        if _to_decimal(payload.get("price_eur")) <= 0:
            quote = str(payload.get("quote_asset", "")).upper().strip()
            if quote in USD_STABLE_QUOTES and _to_decimal(payload.get("price")) > 0:
                return True
            if _to_decimal(payload.get("price_usd")) > 0:
                return True

        if _to_decimal(payload.get("fee_eur")) <= 0:
            fee_asset = str(payload.get("fee_asset", "")).upper().strip()
            if fee_asset in USD_STABLE_QUOTES and _to_decimal(payload.get("fee")) > 0:
                return True
            if _to_decimal(payload.get("fee_usd")) > 0:
                return True

        for key in (
            "amount_usd",
            "value_usd",
            "income_usd",
            "proceeds_usd",
            "pnl_usd",
            "collateral_usd",
            "funding_usd",
            "commission_usd",
        ):
            if _to_decimal(payload.get(key)) > 0:
                target = key.replace("_usd", "_eur")
                if _to_decimal(payload.get(target)) <= 0:
                    return True
        return False


def _normalize_lookup_table(payload: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            continue
        normalized[_normalize_field_key(key)] = value

    raw_row = payload.get("raw_row")
    if isinstance(raw_row, dict):
        for key, value in raw_row.items():
            if not isinstance(key, str):
                continue
            normalized[f"raw:{_normalize_field_key(key)}"] = value
    return normalized


def _normalize_field_key(value: str) -> str:
    return value.strip().lower().replace(" ", "").replace("_", "")


def _lookup_field(lookup: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for alias in aliases:
        normalized = _normalize_field_key(alias)
        candidate = lookup.get(normalized)
        if candidate is not None:
            return candidate
        raw_candidate = lookup.get(f"raw:{normalized}")
        if raw_candidate is not None:
            return raw_candidate
    return None


def _lookup_field_str(lookup: dict[str, Any], aliases: tuple[str, ...]) -> str:
    for alias in aliases:
        val = _lookup_field(lookup, (alias,))
        if val is not None and str(val).strip():
            return str(val).strip().upper()
    return ""
