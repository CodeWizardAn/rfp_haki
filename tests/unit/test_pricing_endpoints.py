"""
Tests for Commodity Pricing & Landed Cost REST endpoints
"""
import pytest
from fastapi.testclient import TestClient
from api.rest_api import app

client = TestClient(app)


def test_get_commodity_rates():
    response = client.get("/api/v1/pricing/commodity-rates")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["currency"] == "INR"
    assert "rates" in data
    rates = data["rates"]
    assert rates["copper_inr_per_kg"] > 0
    assert rates["aluminium_inr_per_kg"] > 0
    assert rates["steel_strip_inr_per_kg"] > 0


def test_estimate_landed_cost():
    payload = {
        "conductor_size_sqmm": 16.0,
        "no_of_cores": 4,
        "conductor_material": "copper",
        "insulation": "XLPE",
        "is_armoured": True,
        "quantity_meters": 1000.0,
        "freight_distance_km": 200.0,
        "margin_percent": 10.0,
        "gst_percent": 18.0
    }
    response = client.post("/api/v1/pricing/landed-cost-estimate", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    data = res["data"]
    assert data["quantity_meters"] == 1000.0
    assert "totals" in data
    totals = data["totals"]
    assert totals["final_landed_total"] > totals["ex_factory_total"]
    assert totals["gst_amount"] > 0
    assert totals["freight"] > 0
    assert totals["margin_amount"] > 0
