"""Tests for sector persistence (store.py)."""

import json
from pathlib import Path

import pytest

import protofiler.store as store


@pytest.fixture(autouse=True)
def patch_data_dir(tmp_path, monkeypatch):
    """Redirect all store I/O to a temp directory."""
    monkeypatch.setattr(store, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "_SECTORS_FILE", tmp_path / "sectors.json")


def test_load_returns_empty_when_no_file():
    assert store.load() == []


def test_add_sector_creates_sector():
    store.add_sector("Tech")
    sectors = store.load()
    assert len(sectors) == 1
    assert sectors[0].name == "Tech"
    assert sectors[0].symbols == []


def test_add_sector_idempotent():
    store.add_sector("Tech")
    store.add_sector("Tech")
    assert len(store.load()) == 1


def test_assign_symbol_to_existing_sector():
    store.add_sector("Tech")
    store.assign_symbol("Tech", "AAPL")
    sectors = store.load()
    assert "AAPL" in sectors[0].symbols


def test_assign_symbol_creates_sector_if_missing():
    store.assign_symbol("Energy", "XOM")
    sectors = store.load()
    assert any(s.name == "Energy" and "XOM" in s.symbols for s in sectors)


def test_assign_symbol_normalises_to_uppercase():
    store.assign_symbol("Tech", "aapl")
    sectors = store.load()
    assert "AAPL" in sectors[0].symbols


def test_unassign_symbol():
    store.assign_symbol("Tech", "AAPL")
    store.assign_symbol("Tech", "MSFT")
    store.unassign_symbol("AAPL")
    sectors = store.load()
    assert "AAPL" not in sectors[0].symbols
    assert "MSFT" in sectors[0].symbols


def test_remove_sector():
    store.add_sector("Tech")
    store.add_sector("Energy")
    store.remove_sector("Tech")
    sectors = store.load()
    assert all(s.name != "Tech" for s in sectors)
    assert any(s.name == "Energy" for s in sectors)


def test_save_and_load_roundtrip():
    store.assign_symbol("Tech", "AAPL")
    store.assign_symbol("Tech", "MSFT")
    store.assign_symbol("Energy", "XOM")
    sectors = store.load()
    by_name = {s.name: s.symbols for s in sectors}
    assert sorted(by_name["Tech"]) == ["AAPL", "MSFT"]
    assert by_name["Energy"] == ["XOM"]
