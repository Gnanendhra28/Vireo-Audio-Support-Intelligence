"""Unit tests for data loading, validation, and preprocessing modules."""

from pathlib import Path
import pytest
import pandas as pd

from src.data.loader import DataLoader
from src.data.validation import DataValidator
from src.data.preprocessing import DataPreprocessor


@pytest.fixture(scope="module")
def data_dir():
    """Resolve data/raw directory."""
    return Path(__file__).resolve().parent.parent / "data" / "raw"


@pytest.fixture(scope="module")
def datasets(data_dir):
    """Load all datasets once for the test module."""
    loader = DataLoader(raw_data_dir=data_dir)
    return loader.load_all()


def test_datasets_exist_and_load(datasets):
    """Verify all five core datasets are present and non-empty."""
    expected_keys = ["tickets", "agents", "orders", "customers", "products"]
    for key in expected_keys:
        assert key in datasets, f"Missing expected dataset {key}"
        assert not datasets[key].empty, f"Dataset {key} is empty"


def test_primary_key_uniqueness(datasets):
    """Verify primary keys have zero duplicates across all tables."""
    pk_checks = [
        ("tickets", "ticket_id"),
        ("agents", "agent_id"),
        ("orders", "order_id"),
        ("customers", "customer_id"),
        ("products", "sku"),
    ]
    for ds_name, pk_col in pk_checks:
        res = DataValidator.check_primary_keys(datasets[ds_name], pk_col)
        assert res["is_valid"], f"Primary key violation in {ds_name}.{pk_col}: {res}"


def test_foreign_key_referential_integrity(datasets):
    """Verify referential integrity between tickets and dimensional tables."""
    # tickets -> customers
    res_cust = DataValidator.check_foreign_key(
        datasets["tickets"], "customer_id", datasets["customers"], "customer_id"
    )
    assert res_cust["is_valid"], f"Orphan customer_ids: {res_cust}"

    # tickets -> products
    res_prod = DataValidator.check_foreign_key(
        datasets["tickets"], "product_sku", datasets["products"], "sku"
    )
    assert res_prod["is_valid"], f"Orphan product_skus: {res_prod}"

    # tickets -> agents
    res_agent = DataValidator.check_foreign_key(
        datasets["tickets"], "agent_id", datasets["agents"], "agent_id"
    )
    assert res_agent["is_valid"], f"Orphan agent_ids: {res_agent}"


def test_legacy_timestamp_correction(datasets):
    """Verify that applying +05:30:00 to legacy_fd eliminates negative handle times."""
    tickets = datasets["tickets"]
    # Check that raw legacy tickets have negative handle times
    raw_anomalies = DataValidator.check_timestamp_anomalies(tickets)
    assert raw_anomalies["resolved_before_response"] > 0, "Expected raw legacy tickets to have anomalies"

    # Preprocess and verify anomalies disappear
    corrected = DataPreprocessor.apply_legacy_timestamp_correction(tickets)
    res = DataPreprocessor.compute_workload_metrics(corrected)

    # With +5h30m offset, handle_time_hrs must be >= 0 for all resolved tickets
    resolved_tickets = res[res["resolved_dt"].notna()]
    negative_handle = (resolved_tickets["handle_time_hrs"] < 0).sum()
    assert negative_handle == 0, f"Found {negative_handle} negative handle times after correction"


def test_fallback_order_join(datasets):
    """Verify fallback join matches tickets with blank order_id."""
    tickets = datasets["tickets"]
    orders = datasets["orders"]

    null_order_count = tickets["order_id"].isna().sum()
    assert null_order_count > 0, "Expected some tickets to have blank order_id"

    enriched = DataPreprocessor.enrich_fallback_orders(tickets, orders)
    # Effective order_id must cover all records where customer and sku match
    assert enriched["effective_order_id"].isna().sum() == 0


def test_pii_masking():
    """Verify that text masking truncates and cleans long strings."""
    long_msg = "A" * 200
    masked = DataValidator.mask_pii(long_msg)
    assert len(masked) <= 120
    assert masked.endswith("...")
