"""
Which offer is this city actually selling?

The Command Center's 'Start Here' tab has an Active Offer cell, and it says in
plain text: "Select one active offer in B4. Do not run seven offers at once."
The governance loop agrees — Stage 1 stops unless exactly one offer is active.

`VERIFIED 2026-08-09` proposal_engine.py ignored that cell entirely and picked a
product per prospect from the audit's `recommended_product`. Of 136 audited
Asheville prospects, only 4 would have been quoted the offer Tom actually chose;
132 were quoted a different offer at roughly half the price. The control cell
did nothing.

This module makes the sheet authoritative. It never guesses: if the active offer
cannot be matched to a known product, the caller is told to fix the sheet rather
than being handed a default.

The cached copy matters. proposal_engine runs before live_sheets_sync, so a
transient Sheets error would otherwise stop proposals entirely. A slightly stale
offer is recoverable; silently quoting the wrong price to a real business is not,
so the cache is only ever used when the live read fails, and it says so loudly.
"""

import json
import os
import re

CACHE_FILE = "active_offer_{tenant}.json"
START_HERE = "Start Here"
OFFER_LABEL = "active offer"


def _normalize(text):
    return re.sub(r"[^a-z0-9 ]+", " ", str(text or "").lower()).strip()


def _squash(text):
    return re.sub(r"\s+", " ", _normalize(text))


def read_from_sheet(tenant, spreadsheet_id, client=None):
    """Return {'name': str, 'price': int|None} straight from Start Here."""
    if client is None:
        import agency_auth

        client = agency_auth.sheets_client(verbose=False)

    worksheet = client.open_by_key(spreadsheet_id).worksheet(START_HERE)
    rows = worksheet.get_all_values()

    name, price = "", None
    for row in rows:
        if not row:
            continue
        label = _squash(row[0])
        value = row[1].strip() if len(row) > 1 else ""
        if label == OFFER_LABEL and value:
            name = value
        elif label == "launch price" and value:
            digits = re.sub(r"[^0-9]", "", value)
            if digits:
                price = int(digits)
    if not name:
        raise ValueError(
            f"'{START_HERE}' has no Active Offer value for {tenant}. "
            "Put one offer name in the Active Offer row."
        )
    return {"name": name, "price": price}


def match_product(offer_name, price, products):
    """
    Map the sheet's offer text to a product id, or return None.

    Deliberately ordered from most to least certain, and deliberately refuses to
    fall back to a default. Quoting the wrong offer is worse than quoting none.
    """
    target = _squash(offer_name)
    if not target:
        return None

    # 1. The offer text is exactly a product name.
    for pid, product in products.items():
        if _squash(product["name"]) == target:
            return pid

    # 2. The product's description appears in the offer text, or vice versa.
    #    Catches "AI-Assisted Promotional Content Pack" -> "promotional content pack".
    for pid, product in products.items():
        desc = _squash(product.get("desc", ""))
        if desc and (desc in target or target in desc):
            return pid

    # 3. One product name is contained in the other.
    for pid, product in products.items():
        name = _squash(product["name"])
        if name and (name in target or target in name):
            return pid

    # 4. Price, but only when it identifies a single product.
    if price is not None:
        candidates = [pid for pid, p in products.items() if p.get("total") == price]
        if len(candidates) == 1:
            return candidates[0]

    return None


def _cache_path(tenant):
    return CACHE_FILE.format(tenant=tenant)


def save_cache(tenant, payload):
    try:
        with open(_cache_path(tenant), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
    except OSError:
        pass


def load_cache(tenant):
    try:
        with open(_cache_path(tenant), "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def resolve(tenant, spreadsheet_id, products, client=None):
    """
    Return (product_id, product, note).

    Raises ValueError when the active offer cannot be determined or matched, so
    the caller stops rather than quoting a default nobody selected.
    """
    note = ""
    try:
        offer = read_from_sheet(tenant, spreadsheet_id, client=client)
        save_cache(tenant, offer)
    except Exception as exc:
        cached = load_cache(tenant)
        if not cached:
            raise ValueError(
                f"Could not read the active offer for {tenant} ({exc}) and no cached "
                "value exists. Refusing to guess which offer to sell."
            )
        offer = cached
        note = f"USING CACHED OFFER — live read failed ({exc})"

    product_id = match_product(offer["name"], offer.get("price"), products)
    if not product_id:
        known = ", ".join(p["name"] for p in products.values())
        priced = f" at ${offer['price']}" if offer.get("price") else ""
        raise ValueError(
            f"The active offer for {tenant} is '{offer['name']}'{priced}, which does "
            f"not match any known product. Rename it in 'Start Here' to one of: "
            f"{known} — or add the product to proposal_engine.PRODUCTS."
        )

    product = products[product_id]
    if offer.get("price") and offer["price"] != product["total"]:
        note = (note + " | " if note else "") + (
            f"PRICE MISMATCH — the sheet says ${offer['price']} but "
            f"'{product['name']}' is ${product['total']}. Using ${product['total']}."
        )
    return product_id, product, note
