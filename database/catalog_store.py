"""
Persistent Catalog Store
========================
Manages user-added and PDF-imported products in a JSON file so they
survive server restarts.  Also syncs new rows into the in-memory
OEM DataFrame used by the /catalog endpoint.

File location: database/db_products/user_catalog.json

Thread-safe via a reentrant lock.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_CATALOG_DIR = Path(__file__).parent / "db_products"
_CATALOG_FILE = _CATALOG_DIR / "user_catalog.json"
_lock = RLock()


def _ensure_dir():
    _CATALOG_DIR.mkdir(parents=True, exist_ok=True)


# ── Low-level helpers ────────────────────────────────────────────────

def _load() -> List[Dict[str, Any]]:
    """Load the persisted catalog list from disk."""
    if not _CATALOG_FILE.exists():
        return []
    try:
        with open(_CATALOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as exc:
        logger.error(f"Failed to read {_CATALOG_FILE}: {exc}")
        return []


def _save(products: List[Dict[str, Any]]):
    """Write the full catalog list to disk (atomic-ish)."""
    _ensure_dir()
    tmp = str(_CATALOG_FILE) + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(products, f, indent=2, ensure_ascii=False, default=str)
        # Atomic rename (Windows: works if target doesn't exist or same volume)
        if os.path.exists(str(_CATALOG_FILE)):
            os.replace(tmp, str(_CATALOG_FILE))
        else:
            os.rename(tmp, str(_CATALOG_FILE))
        logger.debug(f"Catalog persisted — {len(products)} products")
    except Exception as exc:
        logger.error(f"Failed to persist catalog: {exc}")
        if os.path.exists(tmp):
            os.unlink(tmp)


# ── Public API ───────────────────────────────────────────────────────

def load_user_products() -> List[Dict[str, Any]]:
    """Return all persisted user/imported products (thread-safe)."""
    with _lock:
        return _load()


def add_product(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a single product to the persistent catalog.
    Generates product_code and added_at if not present.
    Returns the product dict (with generated fields).
    """
    if not product.get("product_code"):
        product["product_code"] = f"USR-{uuid.uuid4().hex[:8].upper()}"
    if not product.get("added_at"):
        product["added_at"] = datetime.now().isoformat()
    if not product.get("source"):
        product["source"] = "User Added"

    with _lock:
        catalog = _load()
        catalog.append(product)
        _save(catalog)

    logger.info(f"Product added: {product.get('name')} ({product['product_code']})")
    return product


def add_products_bulk(products: List[Dict[str, Any]], source: str = "PDF Import") -> List[Dict[str, Any]]:
    """
    Add multiple products at once (from PDF import).
    Returns the list with generated codes.
    """
    now = datetime.now().isoformat()
    for p in products:
        if not p.get("product_code"):
            p["product_code"] = f"IMP-{uuid.uuid4().hex[:8].upper()}"
        if not p.get("added_at"):
            p["added_at"] = now
        if not p.get("source"):
            p["source"] = source

    with _lock:
        catalog = _load()
        catalog.extend(products)
        _save(catalog)

    logger.info(f"Bulk-added {len(products)} products (source={source})")
    return products


def delete_product(product_code: str) -> bool:
    """Delete a product by its code. Returns True if found and removed."""
    with _lock:
        catalog = _load()
        before = len(catalog)
        catalog = [p for p in catalog if p.get("product_code") != product_code]
        if len(catalog) < before:
            _save(catalog)
            logger.info(f"Deleted product {product_code}")
            return True
    return False


def clear_imported() -> int:
    """Remove all imported products (source == 'PDF Import'). Returns count removed."""
    with _lock:
        catalog = _load()
        before = len(catalog)
        catalog = [p for p in catalog if p.get("source") != "PDF Import"]
        removed = before - len(catalog)
        _save(catalog)
    logger.info(f"Cleared {removed} imported products")
    return removed


def get_count() -> int:
    """Total user / imported products."""
    with _lock:
        return len(_load())


def get_import_history() -> List[Dict[str, Any]]:
    """Group imports by added_at timestamp and source for history view."""
    with _lock:
        catalog = _load()

    # Group by source + date
    groups: Dict[str, Dict[str, Any]] = {}
    for p in catalog:
        key = f"{p.get('source', 'unknown')}|{p.get('added_at', '')[:19]}"
        if key not in groups:
            groups[key] = {
                "source": p.get("source", "unknown"),
                "imported_at": p.get("added_at"),
                "count": 0,
                "products": [],
            }
        groups[key]["count"] += 1
        groups[key]["products"].append(p.get("name", "Unnamed"))

    return sorted(groups.values(), key=lambda g: g["imported_at"] or "", reverse=True)


# ── DataFrame sync helper ────────────────────────────────────────────

def sync_to_dataframe(product_db, products: Optional[List[Dict[str, Any]]] = None):
    """
    Inject user/imported products into the OEMProductDatabase DataFrame
    so they appear in /catalog searches and RFP matching.
    """
    try:
        import pandas as pd
    except ImportError:
        return

    if product_db is None or product_db.products_df is None:
        return

    if products is None:
        products = load_user_products()

    if not products:
        return

    new_rows = []
    for p in products:
        new_rows.append({
            "Product_Name": p.get("name", "Unnamed"),
            "Product_Code": p.get("product_code", ""),
            "OEM": p.get("oem", "Imported"),
            "Source": p.get("source", "User Added"),
            "Product_Category": p.get("category", "Cables & Wires"),
            "Price_Per_Meter_INR": p.get("price_per_meter"),
            "Voltage_Rating": p.get("voltage_rating"),
            "Conductor_Size_sqmm": p.get("conductor_size"),
            "No_of_Cores": p.get("cores"),
            "Insulation_Type": p.get("insulation"),
            "Conductor_Material": p.get("conductor_material"),
            "Standard": p.get("standard"),
        })

    product_db.products_df = pd.concat(
        [product_db.products_df, pd.DataFrame(new_rows)], ignore_index=True
    )
    logger.info(f"Synced {len(new_rows)} user products → OEM DataFrame (total: {len(product_db.products_df)})")
